"""Procedural worlds and effects for the v2 cut.

Environments: nebula void, ocean (true reflections, waves, glitter, echo ripples),
mountain ranges (aerial perspective, valley fog, rim light from the logo), storm
(clouds, rain, branching lightning), haunted forest (fractal trees, mist, fireflies).
Effects: lightning, energy arcs, metal shards, embers, lens-flare ghosts, light leaks,
shockwave distortion with chromatic fringing.

All sizes are authored at 4K and scaled by `sc`.
"""
import math

import cv2
import numpy as np

from render import ev

GOLD = np.array([0.95, 0.76, 0.42], np.float32)
GOLD_HOT = np.array([1.0, 0.92, 0.74], np.float32)
BOLT = np.array([0.80, 0.86, 1.0], np.float32)


def fractal(h, w, rng, octaves=6, base=3, persistence=0.55):
    out = np.zeros((h, w), np.float32)
    amp = 1.0
    for o in range(octaves):
        gh = base * 2 ** o + 2
        gw = int(gh * w / h) + 2
        n = rng.normal(0, 1, (gh, gw)).astype(np.float32)
        out += cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC) * amp
        amp *= persistence
    out -= out.min()
    return out / max(out.max(), 1e-6)


def noise1d(n, rng, octaves=((3, 1.0), (7, 0.5), (17, 0.25), (41, 0.12), (97, 0.06), (230, 0.03))):
    x = np.zeros(n, np.float32)
    for f, a in octaves:
        pts = rng.normal(0, 1, int(f) + 4).astype(np.float32)
        x += cv2.resize(pts[None, :], (n, 1), interpolation=cv2.INTER_CUBIC)[0] * a
    return x


def displace_path(n, rng, rough=0.55, amp=0.12):
    """Midpoint displacement: perpendicular offsets along a unit segment (n = 2^k + 1)."""
    off = np.zeros(n, np.float32)
    step = n - 1
    a = amp
    while step > 1:
        half = step // 2
        for i in range(half, n - 1, step):
            off[i] = 0.5 * (off[i - half] + off[i + half]) + rng.normal(0, a)
        step = half
        a *= rough
    return off


class Scenery:
    def __init__(self, W, H, sc, seed=21):
        self.W, self.H, self.sc = W, H, sc
        rng = np.random.default_rng(seed)
        qw, qh = W // 4, H // 4
        self.qw, self.qh = qw, qh

        # --- starfield (3 parallax layers)
        self.stars = []
        for n, par, b0, b1, r0, r1 in [(2600, 0.06, 0.10, 0.45, 0.45, 0.9), (1100, 0.16, 0.2, 0.7, 0.6, 1.3),
                                        (280, 0.32, 0.45, 1.0, 1.0, 2.2)]:
            cols = np.array([[1, 1, 1], [0.75, 0.85, 1.0], [1.0, 0.85, 0.6]], np.float32)
            self.stars.append(dict(
                x=rng.uniform(-0.3, 1.3, n).astype(np.float32), y=rng.uniform(0, 1, n).astype(np.float32),
                b=(rng.uniform(b0, b1, n) ** 1.5).astype(np.float32), r=rng.uniform(r0, r1, n).astype(np.float32),
                ph=rng.uniform(0, 6.283, n).astype(np.float32), fr=rng.uniform(0.5, 3.0, n).astype(np.float32),
                col=cols[rng.choice(3, n, p=[0.6, 0.28, 0.12])], par=par))

        # --- nebula + storm clouds (quarter res, oversized for drifting)
        nh, nw = int(qh * 1.6), int(qw * 1.6)
        d1 = fractal(nh, nw, rng, 8, 2, 0.58)
        fil = (1 - np.abs(2 * fractal(nh, nw, rng, 7, 3, 0.6) - 1)) ** 5        # glowing filaments
        lanes = (1 - np.abs(2 * fractal(nh, nw, rng, 6, 2, 0.6) - 1)) ** 7      # dark dust lanes
        region = np.clip(fractal(nh, nw, rng, 3, 1) * 1.8 - 0.45, 0, 1)
        dens = (np.clip(d1 * 1.35 - 0.3, 0, 1) ** 1.5 * 0.75 + fil * 0.55) * region
        dens *= 1 - 0.85 * lanes
        c1 = fractal(nh, nw, rng, 4, 2)[..., None]
        c2 = fractal(nh, nw, rng, 4, 2)[..., None]
        purple = np.array([0.26, 0.12, 0.46], np.float32)
        teal = np.array([0.05, 0.30, 0.40], np.float32)
        rose = np.array([0.46, 0.12, 0.26], np.float32)
        gold = np.array([0.62, 0.42, 0.16], np.float32)
        col = purple * (1 - c1) + teal * c1
        col = col * (1 - c2 * 0.5) + rose * (c2 * 0.5)
        neb = col * dens[..., None] + gold * (np.clip(dens - 0.62, 0, 1) * 2.2)[..., None]
        self.nebula = neb.astype(np.float32)
        cl = fractal(nh, nw, rng, 7, 2)
        self.clouds = (np.clip((cl - 0.35) * 1.8, 0, 1) ** 1.3).astype(np.float32)

        # --- shared full-res detail texture (rock / water micro detail)
        self.tex = cv2.resize(fractal(H // 2, W // 2, rng, 8, 6, 0.6), (W, H)).astype(np.float32) - 0.5
        gx = cv2.Sobel(self.tex, cv2.CV_32F, 1, 0, ksize=5)
        self.tex_gx = (gx / (np.abs(gx).std() * 3 + 1e-6)).astype(np.float32)

        # --- mountain ridges (normalised 0..1 profiles, 1.8x screen width)
        Wl = int(W * 1.8)
        self.ridges = []
        for i in range(4):
            p = noise1d(Wl, rng)
            p = (p - p.min()) / (p.max() - p.min())
            p = 1 - np.abs(p * 2 - 1)                       # ridged: sharp peaks
            p = p ** (1.3 - 0.15 * i)
            self.ridges.append(p.astype(np.float32))
        self.ridge_par = [0.12, 0.3, 0.55, 0.9]
        self.ridge_off = [-0.03, 0.03, 0.09, 0.16]
        self.ridge_amp = [0.20, 0.17, 0.14, 0.11]
        self.ridge_col = [np.array(c, np.float32) for c in
                          ([0.060, 0.066, 0.090], [0.036, 0.041, 0.058], [0.020, 0.023, 0.033], [0.007, 0.008, 0.012])]

        # --- forest layers (dead trees in mist), 2x screen width
        self.trees = []
        self.tree_par = [0.25, 0.55, 0.95]
        self.tree_col = [np.array(c, np.float32) for c in
                         ([0.050, 0.055, 0.072], [0.024, 0.027, 0.038], [0.006, 0.007, 0.010])]
        for i, (ntree, height, thick, ground) in enumerate([(55, 0.20, 5, 0.0), (30, 0.30, 11, 0.05),
                                                            (13, 0.48, 24, 0.13)]):
            m = np.zeros((H, 2 * W), np.uint8)
            gl = noise1d(2 * W, rng, ((5, 1.0), (19, 0.3), (80, 0.1)))
            gl = (gl - gl.mean()) / (gl.std() + 1e-6) * 0.012 * H
            for k in range(ntree):
                x = rng.uniform(0, 2 * W)
                gy = H * (0.78 + ground) + gl[int(x) % (2 * W)]
                self._tree(m, x, gy, height * H * rng.uniform(0.7, 1.2) * 0.42, math.pi / 2 + rng.normal(0, 0.06),
                           thick * sc * rng.uniform(0.7, 1.3), 9, rng)
            pts = np.stack([np.arange(0, 2 * W, 4), H * (0.78 + ground) + gl[::4] + 0.01 * H], 1)
            pts = np.concatenate([pts, [[2 * W, H], [0, H]]]).astype(np.int32)
            cv2.fillPoly(m, [pts], 255, cv2.LINE_AA)
            self.trees.append(m)

        # --- rain, fireflies, embers
        self.rain = dict(x=rng.uniform(0, 1, 1800).astype(np.float32), y=rng.uniform(0, 1, 1800).astype(np.float32),
                         v=rng.uniform(0.8, 1.2, 1800).astype(np.float32), a=rng.uniform(0.25, 0.6, 1800).astype(np.float32),
                         l=rng.uniform(0.7, 1.3, 1800).astype(np.float32))
        self.flies = dict(x=rng.uniform(0, 1, 70).astype(np.float32), y=rng.uniform(0.5, 0.95, 70).astype(np.float32),
                          ph=rng.uniform(0, 6.283, 70).astype(np.float32), f=rng.uniform(0.3, 0.9, 70).astype(np.float32))
        self.embers = dict(x=rng.uniform(0, 1, 520).astype(np.float32), y=rng.uniform(0, 1.3, 520).astype(np.float32),
                           v=rng.uniform(0.03, 0.12, 520).astype(np.float32), ph=rng.uniform(0, 6.283, 520).astype(np.float32),
                           s=rng.uniform(0.6, 2.2, 520).astype(np.float32))

    def _tree(self, m, x, y, length, ang, thick, depth, rng):
        if depth == 0 or length < 3:
            return
        x2 = x + length * math.cos(ang)
        y2 = y - length * math.sin(ang)
        cv2.line(m, (int(x * 16), int(y * 16)), (int(x2 * 16), int(y2 * 16)), 255,
                 max(1, int(round(thick))), cv2.LINE_AA, 4)
        n = 2 if rng.uniform() < 0.8 else 3
        for i in range(n):
            spread = rng.uniform(0.25, 0.75) * (1 if i % 2 == 0 else -1)
            self._tree(m, x2, y2, length * rng.uniform(0.62, 0.82), ang + spread + rng.normal(0, 0.12),
                       thick * 0.66, depth - 1, rng)

    # ------------------------------------------------------------------ sky
    def sky(self, env, t, pan, hy, flash):
        """Quarter-res sky light (nebula, horizon glow, clouds)."""
        qw, qh = self.qw, self.qh
        q = np.zeros((qh, qw, 3), np.float32)
        nh, nw = self.nebula.shape[:2]
        ox = int(np.clip(nw * 0.18 + pan * 0.02 * self.sc + t * 0.8 * self.sc, 0, nw - qw))
        oy = int(np.clip(nh * 0.2 + t * 0.3 * self.sc, 0, nh - qh))
        if env == "void":
            q += self.nebula[oy:oy + qh, ox:ox + qw] * 0.45
        elif env in ("ocean", "mountain", "forest", "storm"):
            yq = (np.arange(qh, dtype=np.float32) * 4 + 2)[:, None]
            g = np.exp(-np.maximum(hy - yq, 0) / (0.22 * self.H)) * (yq < hy)
            hc = {"ocean": [0.06, 0.07, 0.12], "mountain": [0.05, 0.045, 0.075], "forest": [0.055, 0.075, 0.085],
                  "storm": [0.03, 0.035, 0.05]}[env]
            q += g[..., None] * np.array(hc, np.float32)
            if env != "storm":
                q += self.nebula[oy:oy + qh, ox:ox + qw] * (0.13 if env != "forest" else 0.05)
        if env == "storm":
            cl = self.clouds[oy:oy + qh, ox:ox + qw]
            yq = (np.arange(qh, dtype=np.float32) * 4)[:, None]
            band = np.clip(1.2 - yq / (hy + 1), 0, 1)
            lit = 0.05 + 1.6 * flash
            q += (cl * band * lit)[..., None] * np.array([0.55, 0.6, 0.72], np.float32)
        return q

    def storm_clouds(self, t, pan, hy, flash):
        """Storm clouds only (quarter res), lit from inside by lightning."""
        qw, qh = self.qw, self.qh
        nh, nw = self.clouds.shape[:2]
        ox = int(np.clip(nw * 0.18 + pan * 0.03 * self.sc + t * 3.0 * self.sc, 0, nw - qw))
        oy = int(np.clip(nh * 0.2, 0, nh - qh))
        cl = self.clouds[oy:oy + qh, ox:ox + qw]
        yq = (np.arange(qh, dtype=np.float32) * 4)[:, None]
        band = np.clip(1.25 - yq / ((hy if hy is not None else self.H * 0.7) + 1), 0, 1) ** 1.2
        lit = 0.05 + 0.6 * flash
        return (cl * band * lit)[..., None] * np.array([0.5, 0.55, 0.66], np.float32)

    def ocean_plate(self, img, base, t, hy, sx, star_int, lay, rings):
        """Real sea from the photo: gently animate it, then add the logo's reflection
        (everything brighter than the photo above the horizon), rippled by waves."""
        W, H, sc = self.W, self.H, self.sc
        y0 = int(math.ceil(hy))
        if y0 >= H or y0 < 2:
            return
        v = dict(ys=np.arange(y0, H, dtype=np.float32)[:, None], xs=np.arange(W, dtype=np.float32)[None, :],
                 hy=np.float32(hy), Hh=np.float32(H - hy), W2=np.float32(W / 2), Wf=np.float32(W),
                 t=np.float32(t), sc=np.float32(sc))
        v["d"] = ev("(ys-hy)/Hh", v)
        v["X"] = ev("(xs-W2)/Wf/(d+0.03)", v)
        v["Z"] = ev("1/(d+0.03)", v)
        v["p1"] = ev("X*6.0 + Z*1.9 + t*1.1", v)
        v["p2"] = ev("X*-3.1 + Z*3.3 + t*1.6 + 1.3", v)
        v["p3"] = ev("X*11.0 + Z*5.2 - t*2.1", v)
        # light above the horizon = image minus the photo
        light = np.maximum(img[:y0] - base[:y0], 0)
        mapy = ev("hy - (ys-hy) + (sin(p1)*0.5 + sin(p2)*0.35 + sin(p3)*0.15)*(3 + 80*d)*sc*2", v)
        mapx = ev("xs + cos(p2)*(2 + 30*d)*sc*2 + ys*0", v)
        np.clip(mapy, 0, y0 - 1, out=mapy)
        refl = cv2.remap(light, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        # the photo's own water breathes a little
        wy = ev("ys + (sin(p1)*0.6 + sin(p3)*0.4)*(1 + 5*d)*sc*2", v)
        wx = ev("xs + cos(p2)*(1 + 8*d)*sc*2 + ys*0", v)
        np.clip(wy, y0, H - 1, out=wy)
        water = cv2.remap(img, wx, wy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        w = dict(wt=water, r=refl, d=v["d"][..., None], tx=self.tex[y0:, :, None],
                 tint=np.array([0.8, 0.88, 1.0], np.float32)[None, None, :],
                 sx=np.float32(sx), xs=v["xs"][..., None], L=np.float32(min(1.5, star_int)), Wd=np.float32(W),
                 gold=GOLD[None, None, :])
        w["sp"] = (ev("(sin(p1*3.1)*sin(p2*2.3)+1)*0.5", v) ** 6)[..., None]
        img[y0:] = ev("wt + r*tint*(0.35 + 0.65*(1-d)**2)*(1 + tx*0.5)"
                      " + exp(-((xs-sx)/(Wd*0.015 + Wd*0.22*d))**2)*(0.02 + 0.08*(1-d))*L*(0.4 + 1.6*sp)*gold", w)
        rng = np.random.default_rng(int(t * 24) + 17)
        n = int(300 * min(1.0, star_int))
        if n > 0:
            dd = rng.uniform(0.0, 1.0, n) ** 1.6
            gx = sx + rng.normal(0, 1, n) * (18 + 520 * dd) * sc
            gy = hy + dd * (H - hy)
            gb = rng.uniform(0.2, 1.0, n) ** 3 * min(1.0, star_int)
            for x, y, b, d0 in zip(gx, gy, gb, dd):
                if 0 <= x < W and y0 <= y < H:
                    c = GOLD_HOT * 255 * b
                    cv2.circle(lay, (int(x * 16), int(y * 16)), max(1, int((1 + 2.5 * d0) * sc * 2 * 8)),
                               (float(c[0]), float(c[1]), float(c[2])), -1, cv2.LINE_AA, 4)
        if rings:
            h = H - y0
            wl = np.zeros((h, W, 3), np.uint8)
            cy = (hy + 0.42 * (H - hy)) - y0
            for rr, al in rings:
                c = GOLD * 255 * al
                ax = (int(rr * 16), int(rr * 0.13 * 16))
                cv2.ellipse(wl, (int(sx * 16), int(cy * 16)), ax, 0, 0, 360,
                            (float(c[0]), float(c[1]), float(c[2])), max(1, int(3 * sc)), cv2.LINE_AA, 4)
            lay[y0:] = cv2.add(lay[y0:], wl)

    def draw_stars(self, img, t, pan, hy, amt):
        if amt <= 0.01:
            return
        W, H, sc = self.W, self.H, self.sc
        ymax = int(min(H, hy if hy is not None else H))
        if ymax <= 0:
            return
        lay = np.zeros((ymax, W, 3), np.uint8)
        for L in self.stars:
            x = L["x"] * W + pan * L["par"] * sc
            y = L["y"] * H
            tw = 0.7 + 0.3 * np.sin(L["ph"] + t * L["fr"])
            b = L["b"] * tw * amt
            vis = np.where((x > -4) & (x < W + 4) & (y < ymax - 1) & (b > 0.02))[0]
            for i in vis:
                c = L["col"][i] * min(255.0, b[i] * 255)
                cv2.circle(lay, (int(x[i] * 16), int(y[i] * 16)), max(1, int(L["r"][i] * sc * 2 * 16 * 0.5)),
                           (float(c[0]), float(c[1]), float(c[2])), -1, cv2.LINE_AA, 4)
        img[:ymax] += lay.astype(np.float32) * np.float32(1 / 255)

    # ------------------------------------------------------------------ terrain
    def mountains(self, img, t, pan, hy, light, flash, occ):
        """Four ridge layers with aerial perspective, valley fog and rim light.
        light = (lx, ly, strength, colour)."""
        W, H, sc = self.W, self.H, self.sc
        lx, ly, Ls, Lc = light
        xs = np.arange(W, dtype=np.float32)
        for i in range(4):
            p = self.ridges[i]
            off = 0.4 * W + pan * self.ridge_par[i] * sc
            ridge = hy + self.ridge_off[i] * H - self.ridge_amp[i] * H * np.interp(xs + off, np.arange(len(p)), p)
            ridge = ridge.astype(np.float32)
            y0 = max(0, int(ridge.min()) - 2)
            if y0 >= H:
                continue
            h = H - y0
            mk = np.zeros((h, W), np.uint8)
            pts = np.stack([xs[::2], ridge[::2] - y0], 1)
            pts = np.concatenate([pts, [[W, ridge[-1] - y0], [W, h + 2], [0, h + 2]]])
            cv2.fillPoly(mk, [(pts * 4).astype(np.int32)], 255, cv2.LINE_AA, 2)
            m = mk.astype(np.float32)[..., None] * np.float32(1 / 255)
            depth = i / 3.0
            v = dict(img=img[y0:], m=m, yy=np.arange(y0, H, dtype=np.float32)[:, None, None],
                     rg=ridge[None, :, None], xx=xs[None, :, None], lx=np.float32(lx),
                     rw=np.float32((5 + 9 * depth) * sc * 2), fd=np.float32((0.12 + 0.1 * depth) * H),
                     sw=np.float32(W * 0.42), L=np.float32(Ls), F=np.float32(flash),
                     base=self.ridge_col[i][None, None, :], fogc=(np.array([0.07, 0.075, 0.095], np.float32)
                                                                  * (1.3 - depth))[None, None, :],
                     rimc=(Lc * (0.75 - 0.45 * depth))[None, None, :], flc=np.array([0.5, 0.55, 0.7], np.float32)[None, None, :],
                     tx=self.tex[y0:, :, None], dk=np.float32(0.35 + 0.25 * depth),
                     gxx=self.tex_gx[y0:, :, None], ls=np.float32(1.0 if lx < W / 2 else -1.0))
            img[y0:] = ev("img*(1-m) + m*(base*(1 + tx*dk) + fogc*where((yy-rg)/fd > 1, 1, (yy-rg)/fd)"
                          " + (rimc*L + flc*F)*exp(-(yy-rg)/rw)*exp(-((xx-lx)/sw)**2)"
                          " + (rimc*L*0.35 + flc*F*0.5)*where(gxx*ls > 0, gxx*ls, 0)*exp(-(yy-rg)/(rw*9))*exp(-((xx-lx)/(sw*1.6))**2)"
                          " + flc*F*0.08)", v)
            np.maximum(occ[y0:], mk, out=occ[y0:])

    def forest(self, img, t, pan, hy, flash, occ):
        W, H, sc = self.W, self.H, self.sc
        shift = hy - 0.8 * H
        for i, m2 in enumerate(self.trees):
            off = int(0.5 * W + pan * self.tree_par[i] * sc) % W
            mk = m2[:, off:off + W]
            if shift != 0:
                M = np.float32([[1, 0, 0], [0, 1, shift]])
                mk = cv2.warpAffine(mk, M, (W, H))
            rows = np.where(mk.max(1) > 0)[0]
            if len(rows) == 0:
                continue
            y0 = int(rows[0])
            m = mk[y0:].astype(np.float32)[..., None] * np.float32(1 / 255)
            depth = i / 2.0
            v = dict(img=img[y0:], m=m, yy=np.arange(y0, H, dtype=np.float32)[:, None, None], hy=np.float32(hy),
                     base=self.tree_col[i][None, None, :], mist=(np.array([0.07, 0.08, 0.09], np.float32)
                                                                 * (1.1 - 0.6 * depth))[None, None, :],
                     md=np.float32(0.16 * H), F=np.float32(flash), flc=np.array([0.4, 0.45, 0.55], np.float32)[None, None, :],
                     tx=self.tex[y0:, :, None])
            img[y0:] = ev("img*(1-m) + m*(base*(1+tx*0.5) + mist*exp(-abs(yy-hy)/md) + flc*F*0.05)", v)
            np.maximum(occ[y0:], mk[y0:], out=occ[y0:])

    # ------------------------------------------------------------------ water
    def ocean(self, img, t, hy, sx, star_int, lay, rings):
        W, H, sc = self.W, self.H, self.sc
        y0 = int(math.ceil(hy))
        if y0 >= H:
            return
        h = H - y0
        v = dict(ys=np.arange(y0, H, dtype=np.float32)[:, None], xs=np.arange(W, dtype=np.float32)[None, :],
                 hy=np.float32(hy), Hh=np.float32(H - hy), W2=np.float32(W / 2), Wf=np.float32(W),
                 t=np.float32(t), sc=np.float32(sc))
        v["d"] = ev("(ys-hy)/Hh", v)
        v["X"] = ev("(xs-W2)/Wf/(d+0.03)", v)
        v["Z"] = ev("1/(d+0.03)", v)
        v["p1"] = ev("X*6.0 + Z*1.9 + t*1.1", v)
        v["p2"] = ev("X*-3.1 + Z*3.3 + t*1.6 + 1.3", v)
        v["p3"] = ev("X*11.0 + Z*5.2 - t*2.1", v)
        mapy = ev("hy - (ys-hy) + (sin(p1)*0.5 + sin(p2)*0.35 + sin(p3)*0.15)*(3 + 80*d)*sc*2", v)
        mapx = ev("xs + cos(p2)*(2 + 30*d)*sc*2 + ys*0", v)
        np.clip(mapy, 0, max(0, y0 - 1), out=mapy)
        refl = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        w = dict(r=refl, d=v["d"][..., None], tx=self.tex[y0:, :, None],
                 tint=np.array([0.72, 0.85, 1.0], np.float32)[None, None, :],
                 base=np.array([0.004, 0.006, 0.011], np.float32)[None, None, :])
        w["sx"] = np.float32(sx)
        w["xs"] = v["xs"][..., None]
        w["L"] = np.float32(min(1.5, star_int))
        w["sp"] = (ev("(sin(p1*3.1)*sin(p2*2.3)+1)*0.5", v) ** 6)[..., None]
        w["Wd"] = np.float32(W)
        img[y0:] = ev("r*tint*(0.35 + 0.75*(1-d)**2)*(1 + tx*0.5) + base*(1 + tx)"
                      " + exp(-((xs-sx)/(Wd*0.015 + Wd*0.22*d))**2)*(0.03 + 0.10*(1-d))*L*(0.4 + 1.6*sp)*gold", dict(w, gold=GOLD[None, None, :]))
        # the horizon line catches the light
        hl = max(1, int(3 * sc))
        img[max(0, y0 - hl):y0 + hl] *= np.float32(0.85)
        img[max(0, y0 - hl):y0 + hl] += np.float32([0.05, 0.06, 0.09]) * np.float32(1 + min(1.5, star_int))
        # glitter path under the light + echo ripples running across the water
        rng = np.random.default_rng(int(t * 24) + 17)
        n = int(300 * min(1.0, star_int))
        if n > 0:
            dd = rng.uniform(0.0, 1.0, n) ** 1.6
            gx = sx + rng.normal(0, 1, n) * (18 + 520 * dd) * sc
            gy = hy + dd * (H - hy)
            gb = rng.uniform(0.2, 1.0, n) ** 3 * min(1.0, star_int)
            for x, y, b, d0 in zip(gx, gy, gb, dd):
                if 0 <= x < W and y0 <= y < H:
                    c = GOLD_HOT * 255 * b
                    cv2.circle(lay, (int(x * 16), int(y * 16)), max(1, int((1 + 2.5 * d0) * sc * 2 * 8)),
                               (float(c[0]), float(c[1]), float(c[2])), -1, cv2.LINE_AA, 4)
        if rings:
            wl = np.zeros((h, W, 3), np.uint8)
            cy = (hy + 0.42 * (H - hy)) - y0
            for rr, al in rings:
                c = GOLD * 255 * al
                ax = (int(rr * 16), int(rr * 0.13 * 16))
                cv2.ellipse(wl, (int(sx * 16), int(cy * 16)), ax, 0, 0, 360,
                            (float(c[0]), float(c[1]), float(c[2])), max(1, int(3 * sc)), cv2.LINE_AA, 4)
            lay[y0:] = cv2.add(lay[y0:], wl)

    # ------------------------------------------------------------------ particles
    def draw_rain(self, lay, t, amt):
        W, H, sc = self.W, self.H, self.sc
        R = self.rain
        vx, vy = -320.0 * sc, 2700.0 * sc
        x = (R["x"] * (W + 400) + t * vx * R["v"]) % (W + 400) - 200
        y = (R["y"] * (H + 400) + t * vy * R["v"]) % (H + 400) - 200
        L = 0.018 * R["l"]
        for i in range(len(x)):
            c = np.array([0.55, 0.62, 0.75]) * 255 * R["a"][i] * amt
            cv2.line(lay, (int(x[i] * 16), int(y[i] * 16)),
                     (int((x[i] - vx * L[i]) * 16), int((y[i] - vy * L[i]) * 16)),
                     (float(c[0]), float(c[1]), float(c[2])), max(1, int(sc * 2)), cv2.LINE_AA, 4)

    def draw_fireflies(self, lay, gq, t, amt):
        W, H, sc = self.W, self.H, self.sc
        F = self.flies
        x = F["x"] * W + 70 * sc * np.sin(t * F["f"] + F["ph"])
        y = F["y"] * H + 40 * sc * np.sin(t * F["f"] * 1.3 + F["ph"] * 2)
        b = np.maximum(0, np.sin(t * F["f"] * 2.2 + F["ph"])) ** 3 * amt
        for i in range(len(x)):
            if b[i] < 0.02:
                continue
            c = np.array([0.98, 0.92, 0.55]) * 255 * b[i]
            cv2.circle(lay, (int(x[i] * 16), int(y[i] * 16)), max(1, int(2.2 * sc * 16)),
                       (float(c[0]), float(c[1]), float(c[2])), -1, cv2.LINE_AA, 4)
            cv2.circle(gq, (int(x[i] / 4 * 16), int(y[i] / 4 * 16)), int(1.4 * 16),
                       (float(0.16 * b[i]), float(0.15 * b[i]), float(0.06 * b[i])), -1, cv2.LINE_AA, 4)

    def draw_embers(self, lay, gq, t, amt, rise=True):
        W, H, sc = self.W, self.H, self.sc
 
        E = self.embers
        n_on = int(len(E["x"]) * min(1.0, amt))
        y = (E["y"] * H - (t * E["v"] * H if rise else -t * E["v"] * H * 0.6)) % (1.3 * H) - 0.15 * H
        x = E["x"] * W + 50 * sc * np.sin(t * 0.7 + E["ph"])
        b = (0.5 + 0.5 * np.sin(t * 5.0 * E["v"] * 10 + E["ph"])) * amt
        for i in range(n_on):
            if b[i] < 0.03 or not (0 <= x[i] < W and 0 <= y[i] < H):
                continue
            c = np.array([1.0, 0.62, 0.22]) * 255 * b[i]
            cv2.circle(lay, (int(x[i] * 16), int(y[i] * 16)), max(1, int(E["s"][i] * sc * 2 * 16 * 0.35)),
                       (float(c[0]), float(c[1]), float(c[2])), -1, cv2.LINE_AA, 4)
            if E["s"][i] > 1.6:
                cv2.circle(gq, (int(x[i] / 4 * 16), int(y[i] / 4 * 16)), int(1.2 * 16),
                           (float(0.10 * b[i]), float(0.055 * b[i]), float(0.015 * b[i])), -1, cv2.LINE_AA, 4)

    # ------------------------------------------------------------------ lightning & arcs
    def bolt_paths(self, j, p0, p1, branches=True):
        rng = np.random.default_rng(900 + j)
        n = 129
        off = displace_path(n, rng, 0.58, 0.13)
        p0, p1 = np.array(p0, np.float32), np.array(p1, np.float32)
        d = p1 - p0
        L = float(np.hypot(*d)) + 1e-6
        nrm = np.array([-d[1], d[0]], np.float32) / L
        u = np.linspace(0, 1, n, dtype=np.float32)[:, None]
        main = p0 + d * u + nrm * (off[:, None] * L)
        paths = [(main, 1.0)]
        if branches:
            for b in range(rng.integers(3, 7)):
                k = int(rng.uniform(0.15, 0.8) * n)
                ang = math.atan2(d[1], d[0]) + rng.uniform(0.35, 0.9) * rng.choice([-1, 1])
                bl = L * rng.uniform(0.12, 0.32)
                q0 = main[k]
                q1 = q0 + np.array([math.cos(ang), math.sin(ang)], np.float32) * bl
                boff = displace_path(33, rng, 0.6, 0.15)
                bd = q1 - q0
                bn = np.array([-bd[1], bd[0]], np.float32) / (bl + 1e-6)
                bu = np.linspace(0, 1, 33, dtype=np.float32)[:, None]
                paths.append((q0 + bd * bu + bn * (boff[:, None] * bl), 0.45))
        return paths

    def draw_bolt(self, img, gq, paths, vis):
        sc = self.sc
        for pts, w in paths:
            p16 = (pts * 16).astype(np.int32)
            core = BOLT * 2.8 * vis * w
            cv2.polylines(img, [p16], False, (float(core[0]), float(core[1]), float(core[2])),
                          max(1, int(round(5 * sc * w))), cv2.LINE_AA, 4)
            q16 = (pts / 4 * 16).astype(np.int32)
            g = BOLT * 0.9 * vis * w
            cv2.polylines(gq, [q16], False, (float(g[0]), float(g[1]), float(g[2])), max(1, int(round(6 * w))),
                          cv2.LINE_AA, 4)

    @staticmethod
    def strike_vis(age):
        if age < 0 or age > 0.5:
            return 0.0
        if age < 0.06:
            return 1.0
        if age < 0.09:
            return 0.25
        if age < 0.16:
            return 0.9
        return 0.9 * math.exp(-(age - 0.16) / 0.1)

    def draw_arcs(self, img, gq, pts_screen, seed, amt):
        """Electric arcs jumping between nearby points of the logo."""
        if amt <= 0.02 or len(pts_screen) < 4:
            return
        rng = np.random.default_rng(seed)
        n = int(6 + 12 * min(1.0, amt))
        for _ in range(n):
            i = rng.integers(len(pts_screen))
            dists = np.hypot(*(pts_screen - pts_screen[i]).T)
            near = np.where((dists > 20 * self.sc) & (dists < 260 * self.sc))[0]
            if len(near) == 0:
                continue
            j = near[rng.integers(len(near))]
            p0, p1 = pts_screen[i], pts_screen[j]
            off = displace_path(17, rng, 0.6, 0.22)
            d = p1 - p0
            L = float(np.hypot(*d)) + 1e-6
            nrm = np.array([-d[1], d[0]], np.float32) / L
            u = np.linspace(0, 1, 17, dtype=np.float32)[:, None]
            path = p0 + d * u + nrm * (off[:, None] * L)
            self.draw_bolt(img, gq, [(path, 0.55 * min(1.0, amt))], 1.0)

    # ------------------------------------------------------------------ lens effects
    def flare(self, gq, sx, sy, inten):
        if inten <= 0.02:
            return
        W, H = self.W, self.H
        if not (-0.1 * W < sx < 1.1 * W and -0.1 * H < sy < 1.1 * H):
            return
        cx, cy = W / 2, H / 2
        vx, vy = cx - sx, cy - sy
        ghosts = [(0.35, 0.05, (0.10, 0.45, 0.50), "c"), (0.62, 0.028, (0.60, 0.45, 0.20), "h"),
                  (0.95, 0.085, (0.35, 0.18, 0.55), "c"), (1.28, 0.045, (0.12, 0.40, 0.45), "h"),
                  (1.62, 0.13, (0.55, 0.30, 0.12), "r"), (2.05, 0.03, (0.6, 0.6, 0.6), "c")]
        for k, r, col, kind in ghosts:
            gx, gy = (sx + vx * k) / 4, (sy + vy * k) / 4
            rr = r * H / 4
            c = tuple(float(v * 0.07 * inten) for v in col)
            if kind == "c":
                cv2.circle(gq, (int(gx * 16), int(gy * 16)), int(rr * 16), c, -1, cv2.LINE_AA, 4)
            elif kind == "h":
                hexa = np.array([[gx + rr * math.cos(a), gy + rr * math.sin(a)] for a in np.linspace(0, 2 * math.pi, 7)[:-1] + 0.3])
                cv2.fillPoly(gq, [(hexa * 16).astype(np.int32)], c, cv2.LINE_AA, 4)
            else:
                cv2.circle(gq, (int(gx * 16), int(gy * 16)), int(rr * 16), c, max(1, int(rr * 0.12)), cv2.LINE_AA, 4)
        halo = tuple(float(v * 0.05 * inten) for v in (0.9, 0.7, 0.4))
        cv2.circle(gq, (int(sx / 4 * 16), int(sy / 4 * 16)), int(0.2 * H / 4 * 16), halo, 2, cv2.LINE_AA, 4)

    def leak(self, q, u, amt):
        """A warm light leak sweeping across the frame (quarter res)."""
        if amt <= 0.01:
            return
        qh, qw = q.shape[:2]
        cx = (-0.3 + 1.6 * u) * qw
        cy = qh * (0.25 + 0.2 * math.sin(u * 3))
        yy, xx = np.mgrid[0:qh, 0:qw].astype(np.float32)
        g = np.exp(-(((xx - cx) / (0.45 * qw)) ** 2 + ((yy - cy) / (0.5 * qh)) ** 2))
        q += g[..., None] * np.array([1.0, 0.6, 0.18], np.float32) * (0.09 * amt)

    def shockwave(self, img, xx, yy, cx, cy, events, t):
        """Radial distortion ring with prismatic fringe (returns new image)."""
        act = [(t - t0, s) for t0, s in events if 0 <= t - t0 < 1.7]
        if not act:
            return img
        sc = self.sc
        v = dict(xx=xx, yy=yy, cx=np.float32(cx), cy=np.float32(cy))
        v["d"] = ev("sqrt((xx-cx)**2 + (yy-cy)**2) + 0.001", v)
        disp = np.zeros_like(v["d"])
        glow = np.zeros_like(v["d"])
        for age, s in act:
            r = np.float32(3000 * sc * age ** 0.75)
            w = np.float32((60 + 90 * age) * sc)
            k = np.float32(s * 38 * sc * (1 - age / 1.7) ** 2)
            disp += ev("k*exp(-((d-r)/w)**2)", dict(d=v["d"], r=r, w=w, k=k))
            glow += ev("exp(-((d-r)/w)**2)*g", dict(d=v["d"], r=r, w=w, g=np.float32(0.18 * s * (1 - age / 1.7))))
        out = np.empty_like(img)
        for c, f in enumerate((1.25, 1.0, 0.75)):
            w2 = dict(xx=xx, yy=yy, cx=np.float32(cx), cy=np.float32(cy), d=v["d"], p=disp, f=np.float32(f))
            mx = ev("xx - p*f*(xx-cx)/d", w2)
            my = ev("yy - p*f*(yy-cy)/d", w2)
            out[..., c] = cv2.remap(np.ascontiguousarray(img[..., c]), mx, my, cv2.INTER_LINEAR,
                                    borderMode=cv2.BORDER_REFLECT)
        out += glow[..., None] * GOLD_HOT
        return out
