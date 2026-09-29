"""Particle avatar: retargets Brandon's real facial performance onto the bust.

Performance landmarks (from capture.py) are similarity-aligned to a neutral
shape built from the performance itself; the residual is the expression.
That expression is mapped into the bust's landmark frame and drives the
bust particles through face-mesh barycentrics. Head rotation / lean come
from the alignment. A mouth-interior particle set (dark cavity + teeth)
fills the lips when the jaw opens.
"""
import math

import numba as nb
import numpy as np
from scipy.ndimage import gaussian_filter1d

from noise3 import curl, fbm

STABLE = [10, 151, 9, 8, 168, 6, 197, 195, 5, 4, 1, 33, 133, 362, 263, 234, 454, 127, 356, 109, 338, 67, 297]
INNER_UP = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308]
INNER_LO = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308]
MOUTH_LM = sorted(set([0, 13, 14, 17, 37, 39, 40, 61, 78, 80, 81, 82, 84, 87, 88, 91, 95, 146, 178, 181, 185,
                       191, 267, 269, 270, 291, 308, 310, 311, 312, 314, 317, 318, 321, 324, 375, 402, 405,
                       409, 415]))
IRIS = [468, 473]


def umeyama(src, dst):
    """Similarity (s, R, t) minimising |s R src + t - dst|^2."""
    mu_s, mu_d = src.mean(0), dst.mean(0)
    a, b = src - mu_s, dst - mu_d
    cov = b.T @ a / len(src)
    U, S, Vt = np.linalg.svd(cov)
    D = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        D[2, 2] = -1
    R = U @ D @ Vt
    var = (a ** 2).sum() / len(src)
    s = np.trace(np.diag(S) @ D) / var
    t = mu_d - s * R @ mu_s
    return s, R, t


def rot_to_vec(R):
    ang = math.acos(max(-1.0, min(1.0, (np.trace(R) - 1) / 2)))
    if ang < 1e-8:
        return np.zeros(3)
    v = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / (2 * math.sin(ang))
    return v * ang


def vec_to_rot(v):
    ang = np.linalg.norm(v)
    if ang < 1e-9:
        return np.eye(3)
    k = v / ang
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K


F = np.diag([1.0, -1.0, -1.0])  # image (x right, y down, z away) -> world (x right, y up, z toward cam)


@nb.njit(parallel=True, fastmath=True, cache=True)
def _pose_kernel(base, tri_v, bary, off, inside, idw_i, idw_w, idw_fall, head_w, hairw, seedp, phase,
                 L, E, R, piv, lean, swx, swy, t, energy, breath, shimmer, glow, col_in, pos_out, col_out,
                 normal, rnd, aura_frac, aura_amt):
    n = base.shape[0]
    for i in nb.prange(n):
        if inside[i]:
            a = tri_v[i, 0]
            b = tri_v[i, 1]
            c = tri_v[i, 2]
            w0 = bary[i, 0]
            w1 = bary[i, 1]
            w2 = bary[i, 2]
            px = L[a, 0] * w0 + L[b, 0] * w1 + L[c, 0] * w2 + off[i, 0]
            py = L[a, 1] * w0 + L[b, 1] * w1 + L[c, 1] * w2 + off[i, 1]
            pz = L[a, 2] * w0 + L[b, 2] * w1 + L[c, 2] * w2 + off[i, 2]
        else:
            dx = 0.0
            dy = 0.0
            dz = 0.0
            for k in range(idw_i.shape[1]):
                j = idw_i[i, k]
                ww = idw_w[i, k]
                dx += E[j, 0] * ww
                dy += E[j, 1] * ww
                dz += E[j, 2] * ww
            f = idw_fall[i]
            px = base[i, 0] + dx * f
            py = base[i, 1] + dy * f
            pz = base[i, 2] + dz * f
        if rnd[i] < aura_frac:
            ph2 = phase[i] * 3.7 + t * (0.35 + rnd[i] * 4.0)
            lift = 0.5 + 0.5 * math.sin(ph2)
            lift = lift * lift * lift * lift * aura_amt * (0.6 + energy)
            px += normal[i, 0] * lift + math.sin(ph2 * 1.3) * lift * 0.3
            py += normal[i, 1] * lift + lift * 0.4
            pz += normal[i, 2] * lift
        hw = head_w[i]
        # breathing on the body
        py += (1.0 - hw) * breath * (1.0 + py * 2.0)
        hf = hairw[i]
        if hf > 0.0:
            sx = seedp[i, 0]
            sy = seedp[i, 1]
            px += (math.sin(sx * 6.1 + t * 1.3) * math.sin(sy * 4.7 - t * 0.9)) * 0.0025 * hf * (0.4 + energy)
            py += math.sin(sy * 7.3 + t * 1.1 + sx * 3.0) * 0.0015 * hf * (0.4 + energy)
        # rigid head
        qx = px - piv[0]
        qy = py - piv[1]
        qz = pz - piv[2]
        rx = R[0, 0] * qx + R[0, 1] * qy + R[0, 2] * qz + piv[0] + swx
        ry = R[1, 0] * qx + R[1, 1] * qy + R[1, 2] * qz + piv[1] + swy
        rz = R[2, 0] * qx + R[2, 1] * qy + R[2, 2] * qz + piv[2] + lean
        pos_out[i, 0] = px + hw * (rx - px)
        pos_out[i, 1] = py + hw * (ry - py)
        pos_out[i, 2] = pz + hw * (rz - pz)
        s = (1.0 + shimmer * math.sin(phase[i] + t * (2.0 + 3.0 * energy))) * (1.0 + glow * energy)
        col_out[i, 0] = col_in[i, 0] * s
        col_out[i, 1] = col_in[i, 1] * s
        col_out[i, 2] = col_in[i, 2] * s


class Performance:
    def __init__(self, perf_npz, bust, fps_out=30.0, duration=None, amp=1.15, max_yaw=0.38,
                 max_pitch=0.3, max_roll=0.35):
        d = np.load(perf_npz, allow_pickle=True)
        lm, valid, t = d['lm'].astype(np.float64), d['valid'].astype(bool), d['t'].astype(np.float64)
        names = list(d['bs_names'])
        bs = d['bs']
        self.src_t = t
        jaw = bs[:, names.index('jawOpen')]
        blink = (bs[:, names.index('eyeBlinkLeft')] + bs[:, names.index('eyeBlinkRight')]) / 2
        funnel = bs[:, names.index('mouthFunnel')] + bs[:, names.index('mouthPucker')]
        st = np.array(STABLE)

        # neutral shape: generalized procrustes over calm, closed-mouth frames
        cand = np.nonzero(valid & (jaw < np.nanpercentile(jaw[valid], 15)) & (blink < 0.35) & (funnel < 0.3))[0]
        if len(cand) < 10:
            cand = np.nonzero(valid)[0][:200]
        ref = lm[cand[0]]
        for _ in range(3):
            acc = []
            for i in cand:
                s, R, tt = umeyama(lm[i][st], ref[st])
                acc.append((s * (R @ lm[i].T)).T + tt)
            ref = np.median(np.array(acc), 0)
        self.neutral = ref

        n = len(t)
        E = np.zeros((n, 478, 3))
        rv = np.zeros((n, 3))
        sc = np.ones(n)
        tr = np.zeros((n, 2))
        for i in range(n):
            if not valid[i]:
                continue
            s, R, tt = umeyama(lm[i][st], ref[st])
            A = (s * (R @ lm[i].T)).T + tt
            E[i] = A - ref
            Rw = F @ R.T @ F  # head rotation relative to neutral, world coords
            rv[i] = rot_to_vec(Rw)
            sc[i] = 1.0 / s
            tr[i] = lm[i][st, :2].mean(0)

        # neutral(perf) -> bust landmark frame
        sb, Rb, _ = umeyama(ref[st], bust.lm_px[st])
        mpp = bust.mpp
        Eb = np.einsum('ij,nkj->nki', Rb, E) * sb
        Ew = Eb * np.array([1.0, -1.0, -1.0]) * mpp * amp

        # fill invalid frames by interpolation, then smooth
        vi = np.nonzero(valid)[0]
        def fill(arr):
            flat = arr.reshape(n, -1)
            out = np.empty_like(flat)
            for c in range(flat.shape[1]):
                out[:, c] = np.interp(np.arange(n), vi, flat[vi, c])
            return out.reshape(arr.shape)
        Ew, rv, sc, tr = fill(Ew), fill(rv), fill(sc), fill(tr)
        self.gap = np.zeros(n)
        # distance (frames) to nearest valid frame -> confidence
        idx = np.arange(n)
        nearest = np.abs(idx[:, None] - vi[None, :]).min(1) if len(vi) < 20000 else np.zeros(n)
        self.conf_src = np.clip(1.0 - (nearest - 2) / 6.0, 0, 1)

        mouth = np.zeros(478, bool)
        mouth[MOUTH_LM] = True
        Es = gaussian_filter1d(Ew, 1.3, axis=0)
        Es[:, mouth] = gaussian_filter1d(Ew[:, mouth], 0.6, axis=0)
        rv = gaussian_filter1d(rv, 1.2, axis=0)
        sc = gaussian_filter1d(sc, 2.0, axis=0)
        tr = gaussian_filter1d(tr, 2.0, axis=0)

        # clamp head rotation (the bust is 2.5D)
        rv[:, 0] = np.clip(rv[:, 0], -max_pitch, max_pitch)
        rv[:, 1] = np.clip(rv[:, 1], -max_yaw, max_yaw)
        rv[:, 2] = np.clip(rv[:, 2], -max_roll, max_roll)

        self.jaw_src = gaussian_filter1d(np.nan_to_num(np.interp(np.arange(n), vi, jaw[vi])), 0.8)
        self.fps_out = fps_out
        dur = duration if duration is not None else t[-1]
        self.n_out = int(round(dur * fps_out))
        to = np.arange(self.n_out) / fps_out

        def rs(arr):
            flat = arr.reshape(n, -1)
            out = np.empty((self.n_out, flat.shape[1]))
            for c in range(flat.shape[1]):
                out[:, c] = np.interp(to, t, flat[:, c])
            return out.reshape((self.n_out,) + arr.shape[1:])

        self.E = rs(Es).astype(np.float32)
        self.rv = rs(rv)
        self.scale = rs(sc)
        self.trans2d = rs(tr)
        self.jaw = rs(self.jaw_src)
        self.conf = rs(self.conf_src)
        # lean: bigger face in frame (smaller s) -> leaning toward camera
        base = np.median(self.scale)
        self.lean = np.clip((1.0 / self.scale * base - 1.0), -0.35, 0.35)  # >0 closer
        self.sway = (self.trans2d - np.median(self.trans2d, 0)) / (bust.face_w_px / sb)

    def at(self, i):
        i = int(min(max(i, 0), self.n_out - 1))
        return self.E[i], vec_to_rot(self.rv[i]), self.lean[i], self.sway[i], self.jaw[i]


class Bust:
    def __init__(self, npz):
        d = np.load(npz, allow_pickle=True)
        for k in ['pos', 'col', 'size', 'cls', 'alpha', 'tri', 'bary', 'off', 'idw_i', 'idw_w', 'idw_fall',
                  'head_w', 'lm_world', 'lm_px', 'simplices', 'pivot']:
            setattr(self, k, d[k])
        self.mpp = float(d['mpp'])
        self.face_w_px = float(d['face_w_px'])
        self.n = len(self.pos)
        self.inside = self.tri >= 0
        self.tri_v = self.simplices[np.maximum(self.tri, 0)]  # (n, 3) landmark ids
        rng = np.random.default_rng(5)
        self.phase = rng.uniform(0, 2 * np.pi, self.n).astype(np.float32)
        self.rand = rng.random(self.n).astype(np.float32)
        self.rand2 = rng.random(self.n).astype(np.float32)
        # per-particle noise seed position for drift / dissolve
        self.seedp = (self.pos * 9.0 + rng.normal(0, 0.05, self.pos.shape)).astype(np.float32)
        lum = self.col @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        self.lum = lum
        self._surface_init()
        self._mouth_init(rng)
        x, y = self.pos[:, 0], self.pos[:, 1]
        x0, x1 = np.percentile(x, [0.2, 99.8])
        y0, y1 = np.percentile(y, [0.2, 99.8])

        def ss(a):
            a = np.clip(a, 0, 1)
            return a * a * (3 - 2 * a)
        fade = ss((y - y0) / ((y1 - y0) * 0.16)) * ss((x - x0) / ((x1 - x0) * 0.07)) * ss((x1 - x) / ((x1 - x0) * 0.07))
        fade *= ss((y1 - y) / ((y1 - y0) * 0.03))
        self.edge_fade = fade.astype(np.float32)

    def _surface_init(self):
        """Per-particle normal (from the depth surface) and rim factor (distance to silhouette)."""
        import cv2
        from scipy import ndimage
        g = self.mpp * 2.0
        u = np.round(self.pos[:, 0] / g).astype(int)
        v = np.round(-self.pos[:, 1] / g).astype(int)
        u0, v0 = u.min(), v.min()
        u -= u0
        v -= v0
        Hh, Ww = v.max() + 1, u.max() + 1
        zs = np.zeros((Hh, Ww), np.float32)
        cnt = np.zeros((Hh, Ww), np.float32)
        np.add.at(zs, (v, u), self.pos[:, 2])
        np.add.at(cnt, (v, u), 1)
        m = cnt > 0
        z = np.where(m, zs / np.maximum(cnt, 1), 0).astype(np.float32)
        _, inds = ndimage.distance_transform_edt(~m, return_indices=True)
        z = z[inds[0], inds[1]]
        z = cv2.GaussianBlur(z, (0, 0), 2.0)
        gy, gx = np.gradient(z, g)
        nx, ny = -gx, gy  # image v grows downward, world y up
        nz = np.ones_like(z)
        nn = np.sqrt(nx * nx + ny * ny + nz * nz)
        N = np.stack([nx / nn, ny / nn, nz / nn], -1)
        self.normal = N[v, u].astype(np.float32)
        mm = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        dist = ndimage.distance_transform_edt(mm)
        self.rim = np.exp(-dist[v, u] / 4.0).astype(np.float32)
        # hair freedom: 0 where hair meets face/skin (roots), -> 1 far from it (tips / outer edge)
        nonhair = np.zeros((Hh, Ww), bool)
        nh = self.cls != 1
        nonhair[v[nh], u[nh]] = True
        nonhair = cv2.morphologyEx(nonhair.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
        dh = ndimage.distance_transform_edt(~nonhair)
        free = np.clip((dh[v, u] - 3.0) / 25.0, 0, 1)
        self.hair_free = np.where(self.cls == 1, free * free * (3 - 2 * free), 0).astype(np.float32)

    def look(self, name='starlight', key_dir=(0.4, 0.5, 0.75), key=0.35, rim_col=(0.5, 0.75, 1.0), rim=0.6,
             gain=1.0, sat=1.0, hair_sheen=1.0):
        """Stylised base colour for the particles (likeness kept through the photo luminance/colour)."""
        c = self.col
        lum = self.lum[:, None]
        if name == 'natural':
            base = c
        elif name == 'starlight':
            base = c * 0.55 + lum * np.array([0.6, 0.78, 1.15], np.float32) * 0.7
        elif name == 'gold':
            base = c * 0.45 + lum * np.array([1.25, 0.85, 0.45], np.float32) * 0.8
        elif name == 'ember':
            base = c * 0.3 + lum * np.array([1.4, 0.45, 0.15], np.float32) * 0.9
        elif name == 'ghost':
            base = lum * np.array([0.55, 0.75, 1.0], np.float32) * 1.1
        elif name == 'teal':
            base = c * 0.35 + lum * np.array([0.35, 1.0, 0.95], np.float32) * 0.8
        else:
            base = c
        if sat != 1.0:
            l2 = base @ np.array([0.2126, 0.7152, 0.0722], np.float32)
            base = l2[:, None] + (base - l2[:, None]) * sat
        kd = np.array(key_dir, np.float32)
        kd /= np.linalg.norm(kd)
        shade = (1.0 - key) + key * np.clip(self.normal @ kd, 0, 1) * 1.6
        out = base * shade[:, None] + self.rim[:, None] * np.array(rim_col, np.float32) * rim * 0.35
        out = out * self.edge_fade[:, None]
        # hair: dark in the photo, so give strands a sheen + sparse glints so the silhouette reads
        hair = self.cls == 1
        sheen = np.array(rim_col, np.float32) * (0.05 + 0.1 * np.clip(self.normal[:, 1], 0, 1))[:, None]
        out[hair] += sheen[hair] * hair_sheen
        glint = hair & (self.rand < 0.06)
        out[glint] += np.array(rim_col, np.float32) * 0.35 * hair_sheen
        return (out * gain).astype(np.float32)

    def eye_glints(self, E, R, lean, sway, n=40, bright=6.0, seed=0):
        """Tiny bright catchlights on both irises (world-local points)."""
        c = self.iris_points(E, R, lean, sway)
        rng = np.random.default_rng(seed)
        off = rng.normal(0, 0.0007, (n, 3)).astype(np.float32)
        off[:, 2] = 0.0015
        pts = np.concatenate([c[0] + off + np.array([0.0012, 0.0012, 0], np.float32),
                              c[1] + off + np.array([0.0012, 0.0012, 0], np.float32)])
        col = np.full((2 * n, 3), bright / n * 8, np.float32) * np.array([0.9, 0.95, 1.0], np.float32)
        size = np.full(2 * n, 0.3 * self.mpp, np.float32)
        return pts, col, size

    def _mouth_init(self, rng, n=9000):
        s = rng.random(n)
        r = rng.random(n)
        self.m_s = s.astype(np.float32)
        self.m_r = r.astype(np.float32)
        col = np.zeros((n, 3), np.float32)
        teeth_up = r > 0.78
        teeth_lo = r < 0.12
        tongue = (r < 0.35) & (np.abs(s - 0.5) < 0.3)
        col[:] = [0.012, 0.004, 0.005]
        col[tongue] = [0.09, 0.03, 0.035]
        col[teeth_lo] = [0.16, 0.15, 0.14]
        col[teeth_up] = [0.42, 0.41, 0.4]
        # teeth only across the middle of the mouth
        col[(teeth_up | teeth_lo) & (np.abs(s - 0.5) > 0.36)] = [0.015, 0.006, 0.006]
        self.m_col = col
        self.m_size = np.full(n, 0.4 * self.mpp, np.float32)

    def mouth_particles(self, L):
        """Mouth cavity particles from the deformed landmark set L (478, 3)."""
        up = L[INNER_UP]
        lo = L[INNER_LO]
        s = self.m_s * (len(INNER_UP) - 1)
        i0 = np.minimum(s.astype(int), len(INNER_UP) - 2)
        f = (s - i0)[:, None]
        U = up[i0] * (1 - f) + up[i0 + 1] * f
        Lo = lo[i0] * (1 - f) + lo[i0 + 1] * f
        r = self.m_r[:, None]
        P = Lo + (U - Lo) * r
        gap = np.linalg.norm(up[5] - lo[5])
        depth = np.sin(np.pi * r[:, 0]) * np.sin(np.pi * self.m_s) * min(gap, 0.02) * 1.2
        P[:, 2] -= depth + 0.002
        vis = np.clip((gap - 0.0015) / 0.006, 0, 1)
        return P.astype(np.float32), (self.m_col * vis).astype(np.float32), self.m_size

    def pose(self, E, R, lean=0.0, sway=(0.0, 0.0), t=0.0, energy=0.0, fx=None, col=None):
        """Return (pos, col, size, head_w) of the posed avatar in bust-local coordinates.

        col: optional per-particle base colour (stylised look); defaults to the photo colour.
        """
        fx = fx or {}
        E = np.ascontiguousarray(E, np.float32)
        L = (self.lm_world + E).astype(np.float32)
        n = self.n
        if not hasattr(self, '_pos_out'):
            self._pos_out = np.empty((n, 3), np.float32)
            self._col_out = np.empty((n, 3), np.float32)
            self._hair = self.hair_free
            self._inside = self.inside.astype(np.bool_)
        base_col = self.col if col is None else col
        br = math.sin(t * 2 * math.pi * 0.23) * 0.003
        _pose_kernel(self.pos, self.tri_v, self.bary, self.off, self._inside, self.idw_i, self.idw_w, self.idw_fall,
                     self.head_w, self._hair, self.seedp, self.phase, L, E, np.ascontiguousarray(R, np.float32),
                     self.pivot.astype(np.float32), np.float32(lean * 0.12), np.float32(sway[0] * 0.02),
                     np.float32(-sway[1] * 0.012), np.float32(t), np.float32(energy), np.float32(br),
                     np.float32(fx.get('shimmer', 0.12)), np.float32(fx.get('voice_glow', 0.35)),
                     np.ascontiguousarray(base_col, np.float32), self._pos_out, self._col_out,
                     self.normal, self.rand, np.float32(fx.get('aura_frac', 0.04)), np.float32(fx.get('aura', 0.012)))
        mp_, mc, ms = self.mouth_particles(L)
        piv = self.pivot
        mrot = (mp_ - piv) @ R.T + piv
        mrot[:, 2] += lean * 0.12
        mrot[:, 0] += sway[0] * 0.02
        mrot[:, 1] -= sway[1] * 0.012
        keep = fx.get('keep', 1.0)
        if keep < 1.0:
            sel = self.rand2 < keep
            P, C, S, HW = self._pos_out[sel], self._col_out[sel], self.size[sel], self.head_w[sel]
            ps = fx.get('point_size', 0.7)
            S = S * ps
            C = C * (1.0 / (keep * ps * ps))
        else:
            P, C, S, HW = self._pos_out, self._col_out, self.size, self.head_w
        pos = np.concatenate([P, mrot.astype(np.float32)])
        colo = np.concatenate([C, mc * fx.get('mouth_gain', 1.0)])
        size = np.concatenate([S, ms])
        hw = np.concatenate([HW, np.ones(len(mp_), np.float32)])
        return pos, colo, size, hw

    def iris_points(self, E, R, lean, sway):
        L = self.lm_world + E
        p = L[IRIS]
        piv = self.pivot
        rot = (p - piv) @ R.T + piv
        rot[:, 2] += lean * 0.12 + 0.004
        rot[:, 0] += sway[0] * 0.02
        rot[:, 1] -= sway[1] * 0.012
        return rot
