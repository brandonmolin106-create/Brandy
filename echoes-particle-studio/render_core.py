"""Echoes in the Dark - CPU particle renderer.

Everything on screen is a particle: an emissive disc with a world-space
radius and an HDR colour. Particles are projected through a thin-lens
camera, their blur (size + depth-of-field circle of confusion) picks a
level in a blur pyramid, they get splatted additively (bilinear) into that
level, and the pyramid is collapsed back into one HDR image. Post FX
(bloom, god rays, ACES tonemap, grade, chromatic aberration, vignette,
grain) turn it into an 8-bit frame.
"""
import math

import cv2
import numba as nb
import numpy as np

cv2.setNumThreads(int(__import__("os").environ.get("OMP_NUM_THREADS", "4")))

W, H = 1080, 1920
NT = nb.config.NUMBA_NUM_THREADS

# Blur pyramid: level k lives at 1/2^(k-1) resolution (levels 0 and 1 are
# full res) and is blurred with sigma 1 at its own scale, so its effective
# full-res sigma is LEVEL_SIGMA[k]. Level 0 is not blurred (crisp dots).
N_LEVELS = 7
LEVEL_SIGMA = np.array([0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0], np.float32)
LEVEL_SCALE = [1, 1, 2, 4, 8, 16, 32]
LEVEL_DIMS = [(int(math.ceil(H / s)), int(math.ceil(W / s))) for s in LEVEL_SCALE]
_offs = [0]
for (h, w) in LEVEL_DIMS:
    _offs.append(_offs[-1] + h * w * 3)
LEVEL_OFFS = np.array(_offs, np.int64)
LEVEL_HW = np.array(LEVEL_DIMS, np.int64)
BUF_LEN = int(_offs[-1])


def normalize(v):
    v = np.asarray(v, np.float64)
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


class Camera:
    """Look-at camera with roll, vertical FOV (degrees) and thin-lens DOF.

    dof is the blur radius in pixels an object at infinity gets when the
    lens is focused at `focus` (0 disables depth of field).
    """

    def __init__(self, eye, target, up=(0.0, 1.0, 0.0), fov=40.0, roll=0.0,
                 focus=None, dof=0.0, shift=(0.0, 0.0)):
        self.eye = np.asarray(eye, np.float64)
        self.target = np.asarray(target, np.float64)
        self.up = np.asarray(up, np.float64)
        self.fov = float(fov)
        self.roll = float(roll)
        self.focus = float(focus) if focus is not None else float(np.linalg.norm(self.target - self.eye))
        self.dof = float(dof)
        self.shift = shift

    def basis(self):
        f = normalize(self.target - self.eye)
        r = normalize(np.cross(f, self.up))
        u = np.cross(r, f)
        if self.roll:
            c, s = math.cos(self.roll), math.sin(self.roll)
            r, u = r * c + u * s, -r * s + u * c
        return r, u, f

    @property
    def focal_px(self):
        return (H * 0.5) / math.tan(math.radians(self.fov) * 0.5)

    def params(self):
        r, u, f = self.basis()
        p = np.zeros(20, np.float32)
        p[0:3] = self.eye
        p[3:6] = r
        p[6:9] = u
        p[9:12] = f
        p[12] = self.focal_px
        p[13] = W * 0.5 + self.shift[0]
        p[14] = H * 0.5 + self.shift[1]
        p[15] = self.focus
        p[16] = self.dof
        return p

    def project(self, pts):
        """Project world points (N,3) -> screen xy (N,2), depth (N,)."""
        r, u, f = self.basis()
        d = np.asarray(pts, np.float64) - self.eye
        z = d @ f
        x = d @ r
        y = d @ u
        zz = np.maximum(z, 1e-6)
        fp = self.focal_px
        sx = W * 0.5 + self.shift[0] + x / zz * fp
        sy = H * 0.5 + self.shift[1] - y / zz * fp
        return np.stack([sx, sy], -1), z


@nb.njit(parallel=True, fastmath=True, cache=True)
def _splat(pos, col, size, cam, bufs, offs, hw, level_sigma, rmin, znear, fog_d, fog_c, max_sig):
    n = pos.shape[0]
    nt = bufs.shape[0]
    ex, ey, ez = cam[0], cam[1], cam[2]
    rx, ry, rz = cam[3], cam[4], cam[5]
    ux, uy, uz = cam[6], cam[7], cam[8]
    fx, fy, fz = cam[9], cam[10], cam[11]
    focal = cam[12]
    cx = cam[13]
    cy = cam[14]
    focus = cam[15]
    dofk = cam[16]
    fw = np.float32(W)
    fh = np.float32(H)
    nl = level_sigma.shape[0]
    chunk = (n + nt - 1) // nt
    for t in nb.prange(nt):
        i0 = t * chunk
        i1 = min(n, i0 + chunk)
        for i in range(i0, i1):
            dx = pos[i, 0] - ex
            dy = pos[i, 1] - ey
            dz = pos[i, 2] - ez
            zc = dx * fx + dy * fy + dz * fz
            if zc < znear:
                continue
            inv = focal / zc
            sx = cx + (dx * rx + dy * ry + dz * rz) * inv
            sy = cy - (dx * ux + dy * uy + dz * uz) * inv
            if sx < -200.0 or sx > fw + 200.0 or sy < -200.0 or sy > fh + 200.0:
                continue
            rpx = size[i] * inv
            coc = 0.0
            if dofk > 0.0:
                coc = dofk * abs(1.0 - focus / zc)
            sig = math.sqrt(0.25 * rpx * rpx + 0.25 * coc * coc)
            if sig > max_sig:
                sig = max_sig
            re = rpx if rpx > rmin else rmin
            flux = re * re
            # near-plane fade so particles don't pop when the camera flies through
            if zc < znear * 4.0:
                flux *= (zc - znear) / (znear * 3.0)
            tr = 1.0
            if fog_d > 0.0:
                tr = math.exp(-fog_d * zc)
            # atmospheric perspective: far particles fade and take on the fog hue (at their own luminance)
            lum = (0.2126 * col[i, 0] + 0.7152 * col[i, 1] + 0.0722 * col[i, 2]) * (1.0 - tr) * 0.5
            c0 = (col[i, 0] * tr + fog_c[0] * lum) * flux
            c1 = (col[i, 1] * tr + fog_c[1] * lum) * flux
            c2 = (col[i, 2] * tr + fog_c[2] * lum) * flux
            # pick blur level (log interpolation between neighbours)
            k = 0
            tt = 0.0
            if sig <= level_sigma[0]:
                k = 0
                tt = 0.0
            elif sig >= level_sigma[nl - 1]:
                k = nl - 1
                tt = 0.0
            else:
                k = 0
                while k < nl - 1 and level_sigma[k + 1] <= sig:
                    k += 1
                tt = math.log(sig / level_sigma[k]) / math.log(level_sigma[k + 1] / level_sigma[k])
            for side in range(2):
                if side == 0:
                    lv = k
                    wgt = 1.0 - tt
                else:
                    lv = k + 1
                    wgt = tt
                if wgt <= 1e-4 or lv >= nl:
                    continue
                lh = hw[lv, 0]
                lw = hw[lv, 1]
                xs = (sx + 0.5) * lw / fw - 0.5
                ys = (sy + 0.5) * lh / fh - 0.5
                x0 = int(math.floor(xs))
                y0 = int(math.floor(ys))
                ax = xs - x0
                ay = ys - y0
                base = offs[lv]
                for jy in range(2):
                    yy = y0 + jy
                    if yy < 0 or yy >= lh:
                        continue
                    wy = ay if jy == 1 else 1.0 - ay
                    for jx in range(2):
                        xx = x0 + jx
                        if xx < 0 or xx >= lw:
                            continue
                        wx = ax if jx == 1 else 1.0 - ax
                        w_ = wx * wy * wgt
                        o = base + (yy * lw + xx) * 3
                        bufs[t, o] += c0 * w_
                        bufs[t, o + 1] += c1 * w_
                        bufs[t, o + 2] += c2 * w_


@nb.njit(parallel=True, fastmath=True, cache=True)
def _reduce(bufs, out):
    nt = bufs.shape[0]
    n = bufs.shape[1]
    step = 1 << 16
    nch = (n + step - 1) // step
    for c in nb.prange(nch):
        a = c * step
        b = min(n, a + step)
        for i in range(a, b):
            s = 0.0
            for t in range(nt):
                s += bufs[t, i]
                bufs[t, i] = 0.0
            out[i] = s


class Splatter:
    def __init__(self):
        self.bufs = np.zeros((NT, BUF_LEN), np.float32)
        self.flat = np.zeros(BUF_LEN, np.float32)
        self.zero_fog = np.zeros(3, np.float32)

    def render(self, cam, pos, col, size, rmin=0.35, znear=0.05, fog_density=0.0,
               fog_color=None, max_sigma=40.0):
        """Splat particles, return list of per-level images (views)."""
        fc = self.zero_fog if fog_color is None else np.asarray(fog_color, np.float32)
        if pos.shape[0]:
            _splat(np.ascontiguousarray(pos, np.float32), np.ascontiguousarray(col, np.float32),
                   np.ascontiguousarray(size, np.float32), cam.params(), self.bufs, LEVEL_OFFS,
                   LEVEL_HW, LEVEL_SIGMA, np.float32(rmin), np.float32(znear),
                   np.float32(fog_density), fc, np.float32(max_sigma))
        _reduce(self.bufs, self.flat)
        return [self.flat[LEVEL_OFFS[k]:LEVEL_OFFS[k + 1]].reshape(LEVEL_DIMS[k][0], LEVEL_DIMS[k][1], 3)
                for k in range(N_LEVELS)]


def collapse(levels):
    """Blur each level at its own scale and collapse the pyramid to full res."""
    acc = None
    for k in range(N_LEVELS - 1, 0, -1):
        lv = cv2.GaussianBlur(levels[k], (0, 0), 1.0)
        if acc is None:
            acc = lv
        else:
            if acc.shape[:2] != lv.shape[:2]:
                acc = cv2.resize(acc, (lv.shape[1], lv.shape[0]), interpolation=cv2.INTER_LINEAR)
            acc = acc + lv
    if acc.shape[:2] != (H, W):
        acc = cv2.resize(acc, (W, H), interpolation=cv2.INTER_LINEAR)
    return acc + levels[0]


# ------------------------------------------------------------------ post FX

def bloom(img, threshold=1.0, strength=0.6, radii=(4, 12, 32, 80), weights=(0.4, 0.3, 0.2, 0.1)):
    """Multi-scale bloom on the HDR image."""
    small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    br = np.maximum(small - threshold, 0.0)
    out = np.zeros_like(br)
    for r, w in zip(radii, weights):
        out += cv2.GaussianBlur(br, (0, 0), r / 4.0) * w
    return img + cv2.resize(out, (W, H), interpolation=cv2.INTER_LINEAR) * strength


def god_rays(img, light_xy, strength=0.5, decay=0.965, samples=28, threshold=0.6, length=0.55):
    """img + screen-space radial light shafts from light_xy (full-res px)."""
    if strength <= 0:
        return img
    return img + rays_only(img, light_xy, strength, decay, samples, threshold, length)


def rays_only(img, light_xy, strength=0.5, decay=0.965, samples=28, threshold=0.6, length=0.55):
    """Just the light-shaft layer (full res) for img's bright parts streaking from light_xy."""
    q = 4
    small = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA)
    lum = small.max(axis=2, keepdims=True)
    src = small * np.clip((lum - threshold) / max(threshold, 1e-3), 0, 4)
    lx, ly = light_xy[0] / q, light_xy[1] / q
    acc = np.zeros_like(src)
    wsum = 0.0
    w = 1.0
    for i in range(samples):
        s = 1.0 - length * i / samples
        M = np.array([[s, 0, lx * (1 - s)], [0, s, ly * (1 - s)]], np.float32)
        acc += cv2.warpAffine(src, M, (src.shape[1], src.shape[0]), flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_CONSTANT) * w
        wsum += w
        w *= decay
    acc = cv2.GaussianBlur(acc / wsum, (0, 0), 1.5)
    return cv2.resize(acc, (W, H), interpolation=cv2.INTER_LINEAR) * strength


@nb.njit(fastmath=True, cache=True, inline='always')
def _aces(v):
    if v < 0.0:
        v = 0.0
    v = (v * (2.51 * v + 0.03)) / (v * (2.43 * v + 0.59) + 0.14)
    if v > 1.0:
        v = 1.0
    return v ** (1.0 / 2.2)


@nb.njit(parallel=True, fastmath=True, cache=True)
def _finish(img, out, exposure, lift, gamma, gain, sat, split_sh, split_hi, vig, vig_pow,
            grain, grain_tex, gx, gy, contrast, ca_px):
    h, w = img.shape[0], img.shape[1]
    cxw = w * 0.5
    cyh = h * 0.5
    inv_r = 1.0 / math.sqrt(cxw * cxw + cyh * cyh)
    gh, gw = grain_tex.shape[0], grain_tex.shape[1]
    for y in nb.prange(h):
        for x in range(w):
            dxn = (x - cxw) * inv_r
            dyn = (y - cyh) * inv_r
            rr = math.sqrt(dxn * dxn + dyn * dyn)
            # chromatic aberration: sample R outward, B inward
            sh = ca_px * rr * rr
            ixr = min(max(int(x + dxn * sh + 0.5), 0), w - 1)
            iyr = min(max(int(y + dyn * sh + 0.5), 0), h - 1)
            ixb = min(max(int(x - dxn * sh + 0.5), 0), w - 1)
            iyb = min(max(int(y - dyn * sh + 0.5), 0), h - 1)
            r = _aces(img[iyr, ixr, 0] * exposure)
            g = _aces(img[y, x, 1] * exposure)
            b = _aces(img[iyb, ixb, 2] * exposure)
            lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
            ws = (1.0 - lum) * (1.0 - lum)
            wh = lum * lum
            r = r + split_sh[0] * ws + split_hi[0] * wh
            g = g + split_sh[1] * ws + split_hi[1] * wh
            b = b + split_sh[2] * ws + split_hi[2] * wh
            r = lum + (r - lum) * sat
            g = lum + (g - lum) * sat
            b = lum + (b - lum) * sat
            r = max(gain[0] * (r + lift[0] * (1.0 - r)), 0.0) ** (1.0 / gamma[0])
            g = max(gain[1] * (g + lift[1] * (1.0 - g)), 0.0) ** (1.0 / gamma[1])
            b = max(gain[2] * (b + lift[2] * (1.0 - b)), 0.0) ** (1.0 / gamma[2])
            r = 0.5 + (r - 0.5) * contrast
            g = 0.5 + (g - 0.5) * contrast
            b = 0.5 + (b - 0.5) * contrast
            vg = 1.0 - vig * rr ** vig_pow
            gn = grain_tex[(y + gy) % gh, (x + gx) % gw] * grain * (0.35 + 0.65 * (1.0 - lum))
            dt = grain_tex[(y * 7 + gy) % gh, (x * 13 + gx) % gw] * 0.5 + 0.5
            r = (r * vg + gn) * 255.0 + dt
            g = (g * vg + gn) * 255.0 + dt
            b = (b * vg + gn) * 255.0 + dt
            out[y, x, 0] = np.uint8(min(max(r, 0.0), 255.0))
            out[y, x, 1] = np.uint8(min(max(g, 0.0), 255.0))
            out[y, x, 2] = np.uint8(min(max(b, 0.0), 255.0))


class Grade:
    def __init__(self, exposure=1.0, lift=(0.0, 0.0, 0.0), gamma=(1.0, 1.0, 1.0), gain=(1.0, 1.0, 1.0),
                 sat=1.05, split_sh=(-0.01, 0.005, 0.03), split_hi=(0.03, 0.012, -0.02), vignette=0.35,
                 vig_pow=2.2, grain=0.018, contrast=1.04, ca=2.0):
        self.exposure = exposure
        self.lift = np.array(lift, np.float32)
        self.gamma = np.array(gamma, np.float32)
        self.gain = np.array(gain, np.float32)
        self.sat = sat
        self.split_sh = np.array(split_sh, np.float32)
        self.split_hi = np.array(split_hi, np.float32)
        self.vignette = vignette
        self.vig_pow = vig_pow
        self.grain = grain
        self.contrast = contrast
        self.ca = ca


_rng = np.random.default_rng(7)
GRAIN_TEX = (_rng.standard_normal((512, 512)).astype(np.float32) * 0.5)
GRAIN_TEX = cv2.GaussianBlur(GRAIN_TEX, (0, 0), 0.6) * 1.6


def finish(img, grade, frame_idx=0, out=None):
    if out is None:
        out = np.empty((H, W, 3), np.uint8)
    gx = (frame_idx * 173) % 512
    gy = (frame_idx * 311) % 512
    _finish(np.ascontiguousarray(img, np.float32), out, np.float32(grade.exposure), grade.lift,
            grade.gamma, grade.gain, np.float32(grade.sat), grade.split_sh, grade.split_hi,
            np.float32(grade.vignette), np.float32(grade.vig_pow), np.float32(grade.grain),
            GRAIN_TEX, gx, gy, np.float32(grade.contrast), np.float32(grade.ca))
    return out


@nb.njit(parallel=True, fastmath=True, cache=True)
def _coverage(pos, size, cam, out, q):
    """Particle coverage (sum of screen disc areas) on a 1/q grid, per-row parallel via chunks."""
    n = pos.shape[0]
    ex, ey, ez = cam[0], cam[1], cam[2]
    rx, ry, rz = cam[3], cam[4], cam[5]
    ux, uy, uz = cam[6], cam[7], cam[8]
    fx, fy, fz = cam[9], cam[10], cam[11]
    focal = cam[12]
    cx = cam[13]
    cy = cam[14]
    h, w = out.shape[1], out.shape[2]
    nt = out.shape[0]
    chunk = (n + nt - 1) // nt
    for t in nb.prange(nt):
        for i in range(t * chunk, min(n, (t + 1) * chunk)):
            dx = pos[i, 0] - ex
            dy = pos[i, 1] - ey
            dz = pos[i, 2] - ez
            zc = dx * fx + dy * fy + dz * fz
            if zc < 0.01:
                continue
            inv = focal / zc
            sx = (cx + (dx * rx + dy * ry + dz * rz) * inv) / q
            sy = (cy - (dx * ux + dy * uy + dz * uz) * inv) / q
            xi = int(sx)
            yi = int(sy)
            if xi < 0 or yi < 0 or xi >= w or yi >= h:
                continue
            out[t, yi, xi] += 1.0


def coverage(cam, pos, size, q=4, blur=1.5, k=1.6):
    """Soft silhouette of a particle set: 1 - exp(-k * particles-per-cell) on a 1/q grid."""
    hq, wq = H // q, W // q
    buf = np.zeros((NT, hq, wq), np.float32)
    _coverage(np.ascontiguousarray(pos, np.float32), np.ascontiguousarray(size, np.float32), cam.params(), buf, q)
    m = buf.sum(0)
    m = cv2.GaussianBlur(m, (0, 0), 1.0)
    m = 1.0 - np.exp(-m * k)
    m = cv2.GaussianBlur(m, (0, 0), blur)
    return cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
