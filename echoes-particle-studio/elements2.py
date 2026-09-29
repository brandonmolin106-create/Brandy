"""Story elements: the fish, the cup, the ocean, people, sun, tree, planet, shards, beams, rings."""
import math

import numba as nb
import numpy as np

from elements import _cat, palette, rot_x, rot_y, rot_z
from noise3 import fbm


def ss(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def frame_from_dir(d, up=(0, 1, 0), bank=0.0):
    """Rotation whose +x axis points along d (fish heading)."""
    x = np.asarray(d, np.float64)
    x /= np.linalg.norm(x) + 1e-12
    upv = np.asarray(up, np.float64)
    z = np.cross(x, upv)
    if np.linalg.norm(z) < 1e-6:
        z = np.cross(x, [0, 0, 1])
    z /= np.linalg.norm(z)
    y = np.cross(z, x)
    R = np.stack([x, y, z], 1)
    if bank:
        R = R @ rot_x(bank).astype(np.float64)
    return R.astype(np.float32)


# ------------------------------------------------------------------ FISH

class Fish:
    """Elegant goldfish/betta made of particles, local +x = forward, length ~1."""

    def __init__(self, n_body=26000, n_fin=30000, seed=21):
        rng = np.random.default_rng(seed)
        # body: ellipsoid-ish, tapering to the peduncle
        u = rng.random(n_body)
        x = 0.5 - u * 0.95  # 0.5 (snout) .. -0.45 (peduncle)
        prof = np.clip(1 - ((x - 0.08) / 0.58) ** 2, 0, 1) ** 0.55
        h = 0.2 * prof + 0.02
        w = 0.12 * prof + 0.012
        th = rng.uniform(0, 2 * np.pi, n_body)
        y = h * np.cos(th)
        z = w * np.sin(th)
        body = np.stack([x, y, z], -1)
        # lateral line + belly gradient colour
        top = np.cos(th)
        colb = palette('ember', 0.55 + 0.35 * (x + 0.5) + 0.1 * top)
        colb *= (0.55 + 0.45 * np.abs(np.sin(th)))[:, None]
        lat = np.abs(np.cos(th)) < 0.08
        colb[lat] += np.array([0.6, 0.45, 0.2])
        scales = (np.sin(x * 90) * np.sin(th * 18)) > 0.6
        colb[scales] *= 1.35
        # eyes
        ne = 600
        eye = []
        for side in (-1, 1):
            a = rng.normal(0, 1, (ne, 3))
            a /= np.linalg.norm(a, axis=1, keepdims=True)
            eye.append(a * 0.022 + np.array([0.36, 0.045, side * 0.075]))
        eye = np.concatenate(eye)
        cole = np.tile(np.array([[0.02, 0.02, 0.03]]), (len(eye), 1))
        cole[rng.random(len(eye)) < 0.12] = [2.5, 2.4, 2.2]
        # fins: tail fan, dorsal, pectorals, anal
        fins, colf, finpar = [], [], []
        # tail: rays from peduncle
        nt = int(n_fin * 0.6)
        ray = rng.integers(0, 22, nt)
        ang = (ray / 21.0 - 0.5) * 1.5 + rng.normal(0, 0.02, nt)
        r = rng.random(nt) ** 0.7 * (0.55 + 0.1 * np.cos(ang * 2))
        on_ray = rng.random(nt) < 0.45
        ang = np.where(on_ray, ang, ang + rng.uniform(-0.035, 0.035, nt))
        tx = -0.45 - r * np.cos(ang)
        ty = r * np.sin(ang)
        tz = rng.normal(0, 0.004, nt)
        fins.append(np.stack([tx, ty, tz], -1))
        c = palette('ember', 0.65 + 0.3 * r) * np.where(on_ray, 1.0, 0.35)[:, None] * (0.6 + 0.8 * r)[:, None]
        edge = r > 0.5
        c[edge] += np.array([0.9, 0.5, 0.25]) * 0.8
        colf.append(c)
        finpar.append(np.stack([r, np.full(nt, 1.0)], -1))
        # dorsal
        nd = int(n_fin * 0.18)
        dx = rng.uniform(-0.22, 0.25, nd)
        dh = (0.17 * np.sin(np.clip((dx + 0.22) / 0.47, 0, 1) * np.pi) ** 0.7) * rng.random(nd) ** 0.8
        fins.append(np.stack([dx - dh * 0.35, 0.18 * np.clip(1 - ((dx - 0.08) / 0.58) ** 2, 0, 1) ** 0.55 + 0.02 + dh,
                              rng.normal(0, 0.003, nd)], -1))
        colf.append(palette('ember', 0.7 + dh * 2) * 0.7)
        finpar.append(np.stack([dh * 3, np.full(nd, 0.5)], -1))
        # pectorals (both sides)
        npf = int(n_fin * 0.11)
        for side in (-1, 1):
            rr = rng.random(npf) ** 0.8 * 0.2
            aa = rng.uniform(-0.6, 0.6, npf)
            fins.append(np.stack([0.15 - rr * np.cos(aa) * 0.8, -0.08 - rr * 0.5, side * (0.1 + rr * np.abs(np.sin(aa)))], -1))
            colf.append(palette('ember', 0.75 + rr) * 0.55)
            finpar.append(np.stack([rr * 2.5, np.full(npf, 0.3)], -1))
        fins = np.concatenate(fins)
        colf = np.concatenate(colf)
        finpar = np.concatenate(finpar)
        self.base = np.concatenate([body, eye, fins]).astype(np.float32)
        self.col = np.concatenate([colb, cole, colf]).astype(np.float32)
        self.flex = np.concatenate([np.zeros(len(body)), np.zeros(len(eye)), finpar[:, 0]]).astype(np.float32)
        self.is_fin = np.concatenate([np.zeros(len(body)), np.zeros(len(eye)), np.ones(len(fins))]).astype(bool)
        self.size = np.concatenate([np.full(len(body), 0.0022), np.full(len(eye), 0.0016),
                                    np.full(len(fins), 0.0018)]).astype(np.float32)
        self.ph = rng.uniform(0, 6.28, len(self.base)).astype(np.float32)

    def at(self, t, pos=(0, 0, 0), heading=(1, 0, 0), scale=0.3, speed=1.0, gain=1.0, tint=None, bank=0.0,
           beat=6.0, amp=1.0, dissolve=0.0, seed_t=0.0):
        p = self.base.copy()
        x = p[:, 0]
        # travelling body wave, amplitude growing toward the tail
        A = (0.015 + 0.11 * np.clip(0.4 - x, 0, 1.2) ** 1.6) * amp
        ph = 7.0 * x - beat * t * speed
        p[:, 2] += A * np.sin(ph)
        # fins flutter with lag
        f = self.flex
        p[:, 2] += self.is_fin * f * 0.05 * np.sin(ph * 1.3 - 1.5 * f + self.ph * 0.2) * amp
        p[:, 1] += self.is_fin * f * 0.02 * np.sin(beat * 0.7 * t + f * 3 + self.ph * 0.1)
        R = frame_from_dir(heading, bank=bank)
        p = (p * scale) @ R.T + np.asarray(pos, np.float32)
        col = self.col * (gain * 0.35)
        if tint is not None:
            lum = col @ np.array([0.2126, 0.7152, 0.0722], np.float32)
            col = col * (1 - tint[3]) + lum[:, None] * np.array(tint[:3], np.float32) * tint[3]
        shimmer = 1.0 + 0.25 * np.sin(self.ph + t * 3.0)
        col = col * shimmer[:, None]
        size = self.size * scale
        if dissolve > 0:
            rnd = (self.ph / 6.28)
            a = ss((dissolve * 1.6 - rnd * 0.6))
            drift = np.stack([np.sin(self.ph * 3 + t * 0.5), 1.0 + rnd, np.cos(self.ph * 5 + t * 0.4)], -1) * scale * 2.5
            p = p + drift * a[:, None]
            col = col * (1 - a * 0.9)[:, None]
        return p.astype(np.float32), col.astype(np.float32), size.astype(np.float32)


def circle_path(t, center=(0, 0, 0), radius=0.2, omega=1.2, y_wobble=0.02, phase=0.0):
    a = omega * t + phase
    c = np.asarray(center, np.float32)
    p = c + np.array([radius * math.cos(a), y_wobble * math.sin(a * 2.3), radius * math.sin(a)], np.float32)
    d = np.array([-math.sin(a), 0.0, math.cos(a)], np.float32) * np.sign(omega)
    return p, d


def trail_ring(center, radius, t, omega, length=6.0, n=1400, y_wobble=0.02, col=(1.0, 0.55, 0.2), gain=1.0,
               phase=0.0, size=0.0025):
    """Glowing trail behind a fish moving on a circle: samples of its past positions."""
    k = np.linspace(0, 1, n, dtype=np.float32)
    tt = t - k * length
    a = omega * tt + phase
    c = np.asarray(center, np.float32)
    p = np.stack([c[0] + radius * np.cos(a), c[1] + y_wobble * np.sin(a * 2.3), c[2] + radius * np.sin(a)], -1)
    fade = (1 - k) ** 1.5
    colr = np.array(col, np.float32)[None, :] * (fade * gain)[:, None]
    return p.astype(np.float32), colr.astype(np.float32), np.full(n, size, np.float32)


# ------------------------------------------------------------------ CUP

class Cup:
    """Glass tumbler with water. Local origin at the base centre, +y up."""

    def __init__(self, rb=0.3, rt=0.37, h=0.95, n_wall=60000, n_rim=9000, n_base=12000, n_water=14000, seed=31,
                 water_level=0.72, n_shards=90):
        rng = np.random.default_rng(seed)
        self.rb, self.rt, self.h, self.wl = rb, rt, h, water_level
        # wall (outer + inner, thin)
        y = rng.random(n_wall) * h
        th = rng.uniform(0, 2 * np.pi, n_wall)
        r = rb + (rt - rb) * y / h
        inner = rng.random(n_wall) < 0.4
        r = r - inner * 0.012
        wall = np.stack([r * np.cos(th), y, r * np.sin(th)], -1)
        nrm = np.stack([np.cos(th), np.full(n_wall, -(rt - rb) / h), np.sin(th)], -1)
        # rim: torus
        th2 = rng.uniform(0, 2 * np.pi, n_rim)
        ph2 = rng.uniform(0, 2 * np.pi, n_rim)
        rim = np.stack([(rt - 0.006 + 0.008 * np.cos(ph2)) * np.cos(th2), h + 0.008 * np.sin(ph2),
                        (rt - 0.006 + 0.008 * np.cos(ph2)) * np.sin(th2)], -1)
        nrim = np.stack([np.cos(ph2) * np.cos(th2), np.sin(ph2), np.cos(ph2) * np.sin(th2)], -1)
        # thick base: disc + ring edge
        rr = np.sqrt(rng.random(n_base)) * rb
        th3 = rng.uniform(0, 2 * np.pi, n_base)
        yb = rng.random(n_base) * 0.06
        base = np.stack([rr * np.cos(th3), yb, rr * np.sin(th3)], -1)
        nbase = np.stack([np.cos(th3) * (rr / rb) ** 4, np.ones(n_base) * 0.3, np.sin(th3) * (rr / rb) ** 4], -1)
        self.glass = np.concatenate([wall, rim, base]).astype(np.float32)
        nn = np.concatenate([nrm, nrim, nbase])
        self.normal = (nn / np.linalg.norm(nn, axis=1, keepdims=True)).astype(np.float32)
        kind = np.concatenate([np.zeros(n_wall), np.ones(n_rim), np.full(n_base, 2)])
        self.kind = kind.astype(np.int8)
        self.theta = np.concatenate([th, th2, th3]).astype(np.float32)
        self.gy = self.glass[:, 1].copy()
        self.gsize = np.where(kind == 1, 0.0016, 0.0012).astype(np.float32)
        # water: surface (meniscus ring + sparse disc) and a few bubbles
        rws = rb + (rt - rb) * water_level / h - 0.014
        nsurf = n_water // 2
        rr = np.sqrt(rng.random(nsurf)) * rws
        th4 = rng.uniform(0, 2 * np.pi, nsurf)
        self.ws_r, self.ws_th = rr.astype(np.float32), th4.astype(np.float32)
        self.ws_rmax = rws
        nvol = n_water - nsurf
        yv = rng.random(nvol) * water_level
        rv = np.sqrt(rng.random(nvol)) * (rb + (rt - rb) * yv / h - 0.02)
        thv = rng.uniform(0, 2 * np.pi, nvol)
        self.wv = np.stack([rv * np.cos(thv), yv, rv * np.sin(thv)], -1).astype(np.float32)
        self.wv_ph = rng.uniform(0, 6.28, nvol).astype(np.float32)
        # shards: voronoi cells over the glass
        seeds = self.glass[rng.choice(len(self.glass), n_shards, replace=False)]
        d = ((self.glass[:, None, :] - seeds[None, :, :]) ** 2).sum(-1) if len(self.glass) * n_shards < 2e7 else None
        if d is None:
            from scipy.spatial import cKDTree
            _, lab = cKDTree(seeds).query(self.glass)
        else:
            lab = d.argmin(1)
        self.shard = lab.astype(np.int32)
        self.sh_center = np.array([self.glass[lab == k].mean(0) if (lab == k).any() else seeds[k]
                                   for k in range(n_shards)], np.float32)
        out = self.sh_center.copy()
        out[:, 1] -= h * 0.45
        out /= np.linalg.norm(out, axis=1, keepdims=True) + 1e-9
        self.sh_vel = (out * rng.uniform(0.8, 2.2, (n_shards, 1)) + rng.normal(0, 0.25, (n_shards, 3))).astype(np.float32)
        ax = rng.normal(size=(n_shards, 3))
        self.sh_axis = (ax / np.linalg.norm(ax, axis=1, keepdims=True)).astype(np.float32)
        self.sh_spin = rng.uniform(2, 9, n_shards).astype(np.float32)
        self.ph = rng.uniform(0, 6.28, len(self.glass)).astype(np.float32)

    def at(self, t, M=None, T=(0, 0, 0), scale=1.0, cam_pos=None, gain=1.0, style='glass', water=True,
           impacts=(), shatter=None, reflect=True, light_dir=(0.5, 0.6, 0.6), water_gain=1.0, tint=(0.75, 0.9, 1.0),
           water_level=None, build=1.0):
        """impacts: list of (t_hit, local_point). shatter: (t0, strength) or None. build: 0..1 draws the cup in."""
        M = np.eye(3, dtype=np.float32) if M is None else np.asarray(M, np.float32)
        T = np.asarray(T, np.float32)
        g = self.glass.copy()
        n = self.normal
        # world normals & view-dependent fresnel
        gw = (g * scale) @ M.T + T
        nw = n @ M.T
        if cam_pos is not None:
            v = np.asarray(cam_pos, np.float32) - gw
            v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-9
            ndv = np.abs((nw * v).sum(1))
        else:
            ndv = np.full(len(g), 0.5, np.float32)
        fres = (1 - ndv) ** 3
        ld = np.asarray(light_dir, np.float32)
        ld = ld / np.linalg.norm(ld)
        spec = np.exp(-((np.abs((nw * ld).sum(1)) - 0.92) / 0.05) ** 2)
        b = 0.008 + 1.1 * fres + 0.8 * spec
        b = np.where(self.kind == 1, b * 1.6 + 0.35, b)
        b = np.where(self.kind == 2, b * 0.8 + 0.08, b)
        if style == 'ghost':
            b = 0.02 + 0.9 * fres
        col = np.array(tint, np.float32)[None, :] * (b * gain)[:, None]
        # impacts: expanding bright ring over the surface
        for (th_, lp) in impacts:
            dt = t - th_
            if dt < 0 or dt > 2.5:
                continue
            d = np.linalg.norm(g - np.asarray(lp, np.float32), axis=1)
            front = dt * 0.9
            ring = np.exp(-((d - front) / 0.03) ** 2) * math.exp(-dt * 1.6) * 3.0
            flash = np.exp(-(d / 0.06) ** 2) * math.exp(-dt * 8.0) * 3.0
            col = col + (ring + flash)[:, None] * np.array([0.8, 0.9, 1.0], np.float32) * gain
        if build < 1.0:
            vis = ss((build * 1.25 - self.gy / self.h * 1.0) * 6.0) if build > 0 else np.zeros(len(g))
            front = np.exp(-((self.gy / self.h - build * 1.25 + 0.15) / 0.03) ** 2) * 4.0
            col = col * vis[:, None] + (front * (build > 0))[:, None] * np.array([1.0, 0.85, 0.6], np.float32)
        pos = g
        size = self.gsize.copy()
        if shatter is not None and t >= shatter[0]:
            dt = t - shatter[0]
            k = self.shard
            cen = self.sh_center[k]
            ax = self.sh_axis[k]
            ang = self.sh_spin[k] * dt * shatter[1]
            rel = pos - cen
            # rodrigues
            c, s_ = np.cos(ang)[:, None], np.sin(ang)[:, None]
            rel = rel * c + np.cross(ax, rel) * s_ + ax * (ax * rel).sum(1, keepdims=True) * (1 - c)
            pos = cen + rel + self.sh_vel[k] * dt * shatter[1] * (1.0 / (1.0 + 0.4 * dt))
            flash = math.exp(-dt * 3.0) * 1.2
            col = col * (1 + flash) + np.array([0.9, 0.95, 1.0], np.float32) * flash * 0.04 * gain
            col = col * max(0.0, 1.0 - dt / 3.5)
        pw = (pos * scale) @ M.T + T
        parts = [(pw, col, size * scale)]
        if water and (shatter is None or t < shatter[0]):
            wl = self.wl if water_level is None else water_level
            r, th = self.ws_r, self.ws_th
            wav = 0.006 * np.sin(r * 40 - t * 3.0) + 0.004 * np.sin(th * 3 + t * 1.3)
            ws = np.stack([r * np.cos(th), wl + wav, r * np.sin(th)], -1)
            edge = (r / self.ws_rmax) ** 12
            wc = np.array([0.25, 0.55, 0.9], np.float32)[None, :] * (0.004 + 1.2 * edge + 0.06 * (np.sin(r * 60 - t * 4) > 0.95))[:, None]
            bub = self.wv.copy()
            bub[:, 1] = (bub[:, 1] + t * 0.05 * (1 + self.wv_ph * 0.1)) % max(wl, 1e-3)
            bc = np.array([0.4, 0.7, 1.0], np.float32)[None, :] * (0.0015 + 0.25 * (np.sin(self.wv_ph + t) > 0.985))[:, None]
            wall_w = np.concatenate([ws, bub])
            wall_c = np.concatenate([wc, bc]) * water_gain * gain
            parts.append(((wall_w * scale) @ M.T + T, wall_c.astype(np.float32),
                          np.full(len(wall_w), 0.002 * scale, np.float32)))
        if reflect:
            ref = []
            for (pp, cc, sz) in parts:
                q = pp.copy()
                q[:, 1] = 2 * T[1] - q[:, 1]
                fade = np.exp(-(T[1] - q[:, 1]) / (0.35 * scale))
                ref.append((q, cc * (0.22 * fade)[:, None], sz))
            parts += ref
        return _cat(*parts)


# ------------------------------------------------------------------ OCEAN

from noise3 import GRAD, PERM, noise3


@nb.njit(parallel=True, fastmath=True, cache=True)
def _ocean2(ex, ey, ez, a0, d, th, jit, t, waves, amp, ld, base, crest, spec_c, bio_c, glitter, bio, pulses,
            perm, grad, sky, out_p, out_c, out_s, pxk):
    n = d.shape[0]
    for i in nb.prange(n):
        a = a0 + th[i]
        x = ex + d[i] * math.sin(a) + jit[i, 0] * d[i] * 0.004
        z = ez - d[i] * math.cos(a) + jit[i, 1] * d[i] * 0.004
        px = x
        pz = z
        py = 0.0
        nx = 0.0
        nyy = 1.0
        nz = 0.0
        hsum = 0.0
        for k in range(waves.shape[0]):
            dx = waves[k, 0]
            dz = waves[k, 1]
            kk = waves[k, 2]
            A = waves[k, 3] * amp
            w = waves[k, 4]
            q = waves[k, 6]
            ph = kk * (dx * x + dz * z) - w * t + waves[k, 5]
            c = math.cos(ph)
            s_ = math.sin(ph)
            px += q * A * dx * c
            pz += q * A * dz * c
            py += A * s_
            nx -= dx * kk * A * c
            nz -= dz * kk * A * c
            nyy -= q * kk * A * s_
            hsum += A
        nl = math.sqrt(nx * nx + nyy * nyy + nz * nz)
        nx /= nl
        nyy /= nl
        nz /= nl
        vx = ex - px
        vy = ey - py
        vz = ez - pz
        vl = math.sqrt(vx * vx + vy * vy + vz * vz) + 1e-6
        vx /= vl
        vy /= vl
        vz /= vl
        ndv = nx * vx + nyy * vy + nz * vz
        if ndv < 0.0:
            ndv = 0.0
        fres = 0.02 + 0.98 * (1.0 - ndv) ** 5
        hx = vx + ld[0]
        hy = vy + ld[1]
        hz = vz + ld[2]
        hl = math.sqrt(hx * hx + hy * hy + hz * hz) + 1e-6
        ndh = (nx * hx + nyy * hy + nz * hz) / hl
        if ndh < 0.0:
            ndh = 0.0
        spec = ndh ** 400 * glitter * 40.0 + ndh ** 60 * glitter * 0.6
        hc = py / (hsum + 1e-6)
        cr = hc - 0.35
        if cr < 0.0:
            cr = 0.0
        cr = cr * cr * 6.0
        sp = noise3(px * 1.7, pz * 1.7, t * 0.4, perm, grad) - 0.32
        if sp < 0.0:
            sp = 0.0
        sp = sp * sp * 70.0 * bio * (0.4 + cr * 3.0)
        pul = 0.0
        for j in range(pulses.shape[0]):
            dt = t - pulses[j, 0]
            if dt < 0.0:
                continue
            ox = pulses[j, 4]
            oz = pulses[j, 5]
            r = math.sqrt((px - ox) ** 2 + (pz - oz) ** 2)
            front = dt * pulses[j, 1]
            g = (r - front) / pulses[j, 2]
            pul += math.exp(-g * g) * math.exp(-dt * 0.4) * pulses[j, 3]
        for c3 in range(3):
            out_c[i, c3] = (base[c3] * (0.35 + sky * fres) + crest[c3] * cr + spec_c[c3] * spec +
                            bio_c[c3] * (sp + pul))
        out_p[i, 0] = px
        out_p[i, 1] = py
        out_p[i, 2] = pz
        out_s[i] = d[i] * pxk


class Ocean:
    """Camera-relative log-polar sampled ocean with Gerstner waves and analytic normals."""

    def __init__(self, n=420000, d0=0.6, dmax=1200.0, fov_deg=150.0, seed=41, steep=0.7):
        rng = np.random.default_rng(seed)
        u = rng.random(n)
        self.d = (d0 * np.exp(u * math.log(dmax / d0))).astype(np.float64)
        self.th = rng.uniform(-math.radians(fov_deg) / 2, math.radians(fov_deg) / 2, n).astype(np.float64)
        self.jit = rng.normal(0, 1, (n, 2)).astype(np.float64)
        ws = []
        for k in range(10):
            ang = math.pi * 0.5 + rng.normal(0, 0.55)
            lam = 34.0 / (1.55 ** k)
            kk = 2 * math.pi / lam
            A = lam / 34.0 * 0.55
            ws.append([math.cos(ang), -abs(math.sin(ang)), kk, A, math.sqrt(9.8 * kk), rng.uniform(0, 6.28), steep / (kk * A * 10 + 1e-6)])
        W = np.array(ws, np.float64)
        W[:, 6] = np.clip(W[:, 6], 0.0, 1.0)
        self.waves = W
        self.out_p = np.empty((n, 3), np.float32)
        self.out_c = np.empty((n, 3), np.float32)
        self.out_s = np.empty(n, np.float32)

    def at(self, t, cam=None, eye=(0, 3, 10), fwd=(0, 0, -1), amp=1.0, gain=1.0, pulses=(), light_dir=(0.0, 0.25, -1.0),
           base_col=(0.05, 0.16, 0.32), crest_col=(0.3, 0.8, 1.0), spec_col=(1.0, 0.92, 0.8), bio_col=(0.2, 0.85, 1.0),
           glitter=1.0, bio=1.0, sky=1.2, px=0.5, **_):
        if cam is not None:
            eye = cam.eye
            fwd = cam.target - cam.eye
            pxk = px / cam.focal_px
        else:
            pxk = px / 2000.0
        a0 = math.atan2(fwd[0], -fwd[2])
        ld = np.asarray(light_dir, np.float64)
        ld = ld / np.linalg.norm(ld)
        P = np.array([[p[0], p[1], p[2], p[3], p[4] if len(p) > 4 else 0.0, p[5] if len(p) > 5 else 0.0]
                      for p in pulses], np.float64).reshape(-1, 6)
        _ocean2(float(eye[0]), float(eye[1]), float(eye[2]), a0, self.d, self.th, self.jit, t, self.waves, amp, ld,
                np.asarray(base_col, np.float64), np.asarray(crest_col, np.float64), np.asarray(spec_col, np.float64),
                np.asarray(bio_col, np.float64), glitter, bio, P, PERM, GRAD, sky, self.out_p, self.out_c, self.out_s, pxk)
        return self.out_p, self.out_c * gain, self.out_s


class Terrain:
    """Log-polar sampled rolling hills (static heightfield) for the tree."""

    def __init__(self, n=300000, d0=0.5, dmax=400.0, seed=43):
        rng = np.random.default_rng(seed)
        u = rng.random(n)
        self.d = d0 * np.exp(u * math.log(dmax / d0))
        self.th = rng.uniform(-1.4, 1.4, n)
        self.ph = rng.uniform(0, 6.28, n).astype(np.float32)

    def at(self, t, cam, height=1.5, gain=1.0, col=(0.05, 0.12, 0.06), tip=(0.5, 0.9, 0.4), hill=(0, 0, 0), hill_h=1.0):
        fwd = cam.target - cam.eye
        a0 = math.atan2(fwd[0], -fwd[2])
        a = a0 + self.th
        x = cam.eye[0] + self.d * np.sin(a)
        z = cam.eye[2] - self.d * np.cos(a)
        xz = np.stack([x * 0.05, z * 0.05, np.zeros_like(x)], -1)
        h = fbm(xz, 4) * height * 4
        r2 = (x - hill[0]) ** 2 + (z - hill[2]) ** 2
        h = h + hill_h * np.exp(-r2 / 30.0) - 0.4
        p = np.stack([x, h, z], -1).astype(np.float32)
        blade = 0.5 + 0.5 * np.sin(self.ph + t * 1.2 + x * 0.3)
        c = np.array(col, np.float32)[None] * (0.6 + 0.4 * blade)[:, None] + \
            np.array(tip, np.float32)[None] * ((fbm(xz * 7 + 3.0, 2) > 0.25) * 0.4 * blade)[:, None]
        return p, (c * gain).astype(np.float32), (self.d * 0.45 / cam.focal_px).astype(np.float32)


# ------------------------------------------------------------------ PEOPLE

class Person:
    """Humanoid silhouette from capsules, surface-sampled, with a walk cycle."""
    PARTS = [  # name, a(x,y,z), b, radius, density
        ('head', (0, 1.66, 0), (0, 1.72, 0), 0.11, 1.4),
        ('neck', (0, 1.46, 0), (0, 1.58, 0), 0.05, 0.6),
        ('torso', (0, 0.98, 0), (0, 1.42, 0), 0.17, 2.4),
        ('hips', (0, 0.9, 0), (0, 1.0, 0), 0.16, 0.8),
        ('uarmL', (-0.21, 1.4, 0), (-0.24, 1.1, 0), 0.05, 0.6),
        ('larmL', (-0.24, 1.1, 0), (-0.25, 0.82, 0.02), 0.042, 0.5),
        ('uarmR', (0.21, 1.4, 0), (0.24, 1.1, 0), 0.05, 0.6),
        ('larmR', (0.24, 1.1, 0), (0.25, 0.82, 0.02), 0.042, 0.5),
        ('ulegL', (-0.09, 0.9, 0), (-0.1, 0.48, 0), 0.075, 1.0),
        ('llegL', (-0.1, 0.48, 0), (-0.1, 0.05, 0), 0.055, 0.8),
        ('ulegR', (0.09, 0.9, 0), (0.1, 0.48, 0), 0.075, 1.0),
        ('llegR', (0.1, 0.48, 0), (0.1, 0.05, 0), 0.055, 0.8),
    ]

    def __init__(self, n=16000, seed=51):
        rng = np.random.default_rng(seed)
        dens = np.array([p[4] for p in self.PARTS])
        counts = (dens / dens.sum() * n).astype(int)
        P, N, L = [], [], []
        for k, ((name, a, b, r, _), c) in enumerate(zip(self.PARTS, counts)):
            a, b = np.array(a), np.array(b)
            u = rng.random(c)
            th = rng.uniform(0, 2 * np.pi, c)
            ax = b - a
            ln = np.linalg.norm(ax)
            axn = ax / ln
            tmp = np.array([1, 0, 0]) if abs(axn[0]) < 0.9 else np.array([0, 0, 1])
            e1 = np.cross(axn, tmp); e1 /= np.linalg.norm(e1)
            e2 = np.cross(axn, e1)
            # capsule: cylinder + hemisphere caps
            capf = (2 * r) / (ln + 2 * r)
            cap = rng.random(c) < capf
            pts = a + axn * (u * ln)[:, None] + (np.cos(th)[:, None] * e1 + np.sin(th)[:, None] * e2) * r
            nrm = np.cos(th)[:, None] * e1 + np.sin(th)[:, None] * e2
            if cap.any():
                s = rng.normal(size=(cap.sum(), 3)); s /= np.linalg.norm(s, axis=1, keepdims=True)
                end = np.where(rng.random(cap.sum()) < 0.5, 0, 1)
                cen = np.where(end[:, None] == 0, a, b)
                pts[cap] = cen + s * r
                nrm[cap] = s
            P.append(pts); N.append(nrm); L.append(np.full(c, k))
        self.base = np.concatenate(P).astype(np.float32)
        self.normal = np.concatenate(N).astype(np.float32)
        self.part = np.concatenate(L).astype(np.int32)
        self.ph = rng.uniform(0, 6.28, len(self.base)).astype(np.float32)
        self.pivots = {'L': np.array([-0.09, 0.9, 0]), 'R': np.array([0.09, 0.9, 0]),
                       'aL': np.array([-0.21, 1.4, 0]), 'aR': np.array([0.21, 1.4, 0])}

    def at(self, t, pos=(0, 0, 0), yaw=0.0, scale=1.0, walk=1.0, cam_pos=None, col=(0.9, 0.2, 0.15), gain=1.0,
           rim=1.0, dissolve=0.0):
        p = self.base.copy()
        ph = t * 2 * math.pi * 0.9
        sw = 0.45 * walk
        for names, piv, sgn in ((('ulegL', 'llegL'), 'L', 1), (('ulegR', 'llegR'), 'R', -1),
                                (('uarmL', 'larmL'), 'aL', -1), (('uarmR', 'larmR'), 'aR', 1)):
            ids = [i for i, pp in enumerate(self.PARTS) if pp[0] in names]
            m = np.isin(self.part, ids)
            ang = sgn * sw * math.sin(ph) * (0.6 if piv.startswith('a') else 1.0)
            R = rot_x(ang)
            c = self.pivots[piv]
            p[m] = (p[m] - c) @ R.T + c
        p[:, 1] += 0.025 * walk * abs(math.sin(ph))
        R = rot_y(yaw)
        p = (p * scale) @ R.T + np.asarray(pos, np.float32)
        nw = self.normal @ R.T
        b = np.full(len(p), 0.12, np.float32)
        if cam_pos is not None:
            v = np.asarray(cam_pos, np.float32) - p
            v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-9
            b = 0.06 + rim * (1 - np.abs((nw * v).sum(1))) ** 2.5 * 1.4
        c = np.array(col, np.float32)[None, :] * (b * gain)[:, None]
        if dissolve > 0:
            rnd = self.ph / 6.28
            a = ss(dissolve * 1.6 - rnd * 0.6)
            p = p + np.stack([np.sin(self.ph * 3), 1.2 + rnd, np.cos(self.ph * 5)], -1) * scale * a[:, None]
            c = c * (1 - a * 0.95)[:, None]
        return p.astype(np.float32), c.astype(np.float32), np.full(len(p), 0.006 * scale, np.float32)


# ------------------------------------------------------------------ SUN

class Sun:
    def __init__(self, n=60000, n_corona=40000, seed=61):
        rng = np.random.default_rng(seed)
        s = rng.normal(size=(n, 3)); s /= np.linalg.norm(s, axis=1, keepdims=True)
        self.surf = s.astype(np.float32)
        self.gran = fbm(s * 6.0, 4).astype(np.float32)
        c = rng.normal(size=(n_corona, 3)); c /= np.linalg.norm(c, axis=1, keepdims=True)
        self.cor_dir = c.astype(np.float32)
        self.cor_r = (1.0 + rng.exponential(0.25, n_corona)).astype(np.float32)
        self.cor_ph = rng.uniform(0, 6.28, n_corona).astype(np.float32)

    def at(self, t, center=(0, 0, -50), radius=6.0, gain=1.0, flare=0.0):
        c = np.asarray(center, np.float32)
        g = self.gran + 0.15 * np.sin(self.surf[:, 0] * 9 + t * 0.8)
        sc = palette('dawn', 0.72 + 0.28 * np.clip(g * 2.2 + 0.5, 0, 1)) * 2.2
        p1 = self.surf * radius + c
        r = self.cor_r * (1.0 + 0.05 * np.sin(self.cor_ph + t * 0.7)) * (1 + flare * 0.6)
        p2 = self.cor_dir * (r * radius)[:, None] + c
        fall = np.exp(-(r - 1.0) * 3.0) * (1 + flare * 3)
        cc = palette('dawn', 0.55 + 0.4 * fall)[:, :] * (fall * 0.35)[:, None]
        return _cat((p1, sc * gain, np.full(len(p1), radius * 0.012, np.float32)),
                    (p2, cc * gain, np.full(len(p2), radius * 0.02, np.float32)))


# ------------------------------------------------------------------ TREE

class Tree:
    def __init__(self, seed=71, depth=8, n_leaf=40000):
        rng = np.random.default_rng(seed)
        segs = []  # (a, b, radius, birth, depth)

        def grow(a, d, length, radius, depth_, birth):
            b = a + d * length
            segs.append((a, b, radius, birth, depth_))
            if depth_ >= depth:
                return
            nk = 2 if depth_ < 2 else rng.integers(2, 4)
            for k in range(nk):
                ang = rng.uniform(0.35, 0.75)
                az = rng.uniform(0, 2 * np.pi)
                perp = np.cross(d, [1, 0, 0] if abs(d[0]) < 0.9 else [0, 0, 1]); perp /= np.linalg.norm(perp)
                perp2 = np.cross(d, perp)
                nd = d * math.cos(ang) + (perp * math.cos(az) + perp2 * math.sin(az)) * math.sin(ang)
                nd = nd + np.array([0, 0.25, 0])
                nd /= np.linalg.norm(nd)
                grow(b, nd, length * rng.uniform(0.62, 0.8), radius * 0.66, depth_ + 1, birth + 1.0)

        grow(np.zeros(3), np.array([0, 1.0, 0]), 1.2, 0.09, 0, 0.0)
        P, C, B, S = [], [], [], []
        for (a, b, r, birth, dp) in segs:
            ln = np.linalg.norm(b - a)
            n = int(max(30, ln * 5000 * (r / 0.09) ** 0.5))
            u = rng.random(n)
            th = rng.uniform(0, 2 * np.pi, n)
            ax = (b - a) / ln
            e1 = np.cross(ax, [1, 0, 0] if abs(ax[0]) < 0.9 else [0, 0, 1]); e1 /= np.linalg.norm(e1)
            e2 = np.cross(ax, e1)
            pts = a + ax * (u * ln)[:, None] + (np.cos(th)[:, None] * e1 + np.sin(th)[:, None] * e2) * r
            P.append(pts)
            C.append(np.tile(np.array([[0.55, 0.32, 0.18]]) * (0.4 + 0.6 * rng.random((n, 1))), (1, 1)))
            B.append(birth + u)
            S.append(np.full(n, 0.004))
        self.bark = np.concatenate(P).astype(np.float32)
        self.bark_col = np.concatenate(C).astype(np.float32)
        self.bark_birth = np.concatenate(B).astype(np.float32)
        self.max_birth = float(max(s[3] for s in segs) + 1)
        tips = np.array([s[1] for s in segs if s[4] >= depth - 1])
        tb = np.array([s[3] + 1 for s in segs if s[4] >= depth - 1])
        k = rng.integers(0, len(tips), n_leaf)
        off = rng.normal(0, 0.09, (n_leaf, 3))
        self.leaf = (tips[k] + off).astype(np.float32)
        self.leaf_birth = (tb[k] + rng.random(n_leaf) * 0.6).astype(np.float32)
        hue = rng.random(n_leaf)
        self.leaf_col = np.where(hue[:, None] < 0.7, np.array([[0.35, 0.9, 0.35]]), np.array([[1.0, 0.8, 0.3]])).astype(np.float32)
        self.leaf_col *= rng.uniform(0.5, 1.4, (n_leaf, 1)).astype(np.float32)
        self.leaf_dir = off.astype(np.float32) / 0.09
        self.ph = rng.uniform(0, 6.28, n_leaf).astype(np.float32)

    def at(self, t, grow=1.0, pos=(0, 0, 0), scale=1.0, gain=1.0, bloom=0.0, sway=0.02):
        g = grow * (self.max_birth + 0.6)
        vis = ss((g - self.bark_birth) * 3.0)
        bp = self.bark.copy()
        bp[:, 0] += sway * np.sin(t * 0.8 + bp[:, 1] * 1.5) * bp[:, 1] ** 2
        lv = ss((g - self.leaf_birth) * 2.0)
        lp = self.leaf + self.leaf_dir * (0.02 * np.sin(self.ph + t * 1.5) + bloom * 0.35)[:, None]
        lp[:, 0] += sway * np.sin(t * 0.8 + lp[:, 1] * 1.5) * lp[:, 1] ** 2
        tw = 0.7 + 0.3 * np.sin(self.ph * 2 + t * 2.0)
        lc = self.leaf_col * (lv * tw * (1 + bloom * 3.0) * 0.35)[:, None]
        # growth front glows
        front = np.exp(-((g - self.bark_birth) / 0.25) ** 2) * 3.0 * (grow < 0.999)
        bc = self.bark_col * vis[:, None] + front[:, None] * np.array([1.0, 0.8, 0.4], np.float32)
        P = np.asarray(pos, np.float32)
        return _cat((bp * scale + P, bc * gain * 0.35, np.full(len(bp), 0.002 * scale, np.float32)),
                    (lp * scale + P, lc * gain, np.full(len(lp), 0.004 * scale, np.float32)))


# ------------------------------------------------------------------ PLANET

class Planet:
    def __init__(self, n=160000, seed=81):
        rng = np.random.default_rng(seed)
        s = rng.normal(size=(n, 3)); s /= np.linalg.norm(s, axis=1, keepdims=True)
        self.s = s.astype(np.float32)
        land = fbm(s * 2.2 + 5.0, 5)
        self.land = (land > 0.05).astype(np.float32)
        self.hgt = land.astype(np.float32)
        self.city = ((rng.random(n) < 0.08) & (land > 0.08)).astype(np.float32)
        self.cloud = np.clip(fbm(s * 4.0 + 20.0, 4) * 3 - 0.2, 0, 1).astype(np.float32)
        a = rng.normal(size=(40000, 3)); a /= np.linalg.norm(a, axis=1, keepdims=True)
        self.atm = a.astype(np.float32)

    def at(self, t, center=(0, 0, 0), radius=1.0, spin=0.05, sun_dir=(1.0, 0.3, 0.5), cam_pos=None, gain=1.0):
        R = rot_y(t * spin)
        s = self.s @ R.T
        sd = np.asarray(sun_dir, np.float32); sd /= np.linalg.norm(sd)
        lit = np.clip(s @ sd, 0, 1)
        ocean = np.array([0.02, 0.08, 0.25], np.float32)
        landc = np.array([0.12, 0.25, 0.08], np.float32) + np.array([0.3, 0.2, 0.1], np.float32) * np.clip(self.hgt * 4, 0, 1)[:, None]
        base = ocean[None] * (1 - self.land[:, None]) + landc * self.land[:, None]
        base = base + self.cloud[:, None] * 0.6
        col = base * (0.03 + 1.6 * lit)[:, None]
        night = (lit < 0.05) * self.city
        col = col + night[:, None] * np.array([1.0, 0.7, 0.35], np.float32) * 1.2
        c = np.asarray(center, np.float32)
        p = s * radius + c
        atm = self.atm * radius * 1.03 + c
        ab = np.full(len(atm), 0.02, np.float32)
        if cam_pos is not None:
            v = np.asarray(cam_pos, np.float32) - atm
            v /= np.linalg.norm(v, axis=1, keepdims=True)
            ab = (1 - np.abs((self.atm * v).sum(1))) ** 4 * 1.2 * (0.2 + np.clip(self.atm @ sd + 0.3, 0, 1))
        ac = np.array([0.3, 0.6, 1.0], np.float32)[None] * ab[:, None]
        return _cat((p, col * gain, np.full(len(p), radius * 0.006, np.float32)),
                    (atm, ac * gain, np.full(len(atm), radius * 0.01, np.float32)))


# ------------------------------------------------------------------ misc

def light_beam(t, top=(0, 6, 0), bottom=(0, 0, 0), radius=0.5, n=12000, gain=1.0, seed=91, col=(1.0, 0.85, 0.55)):
    rng = np.random.default_rng(seed)
    u = rng.random(n)
    th = rng.uniform(0, 2 * np.pi, n)
    r = np.sqrt(rng.random(n)) * radius * (0.4 + 0.6 * u)
    a, b = np.asarray(top, np.float32), np.asarray(bottom, np.float32)
    uu = (u + t * 0.15 * rng.uniform(0.5, 1.5, n)) % 1.0
    p = a + (b - a) * uu[:, None]
    p[:, 0] += r * np.cos(th)
    p[:, 2] += r * np.sin(th)
    c = np.array(col, np.float32)[None] * (gain * (0.3 + 0.7 * rng.random(n)) * np.sin(np.pi * uu))[:, None]
    return p.astype(np.float32), (c * 0.6).astype(np.float32), np.full(n, 0.0025, np.float32)


def ring_ticks(t, center=(0, 0, 0), radius=1.0, n=60, spin=0.0, gain=1.0, per=60, y=0.0, sweep=None):
    pts, cols = [], []
    for k in range(n):
        a = 2 * math.pi * k / n + spin
        big = (k % 5 == 0)
        L = 0.08 if big else 0.04
        m = 18 if big else 8
        for j in range(m):
            r = radius - L * j / m
            pts.append((center[0] + r * math.cos(a), center[1] + y, center[2] + r * math.sin(a)))
            b = (1.4 if big else 0.6)
            if sweep is not None:
                da = (a - sweep) % (2 * math.pi)
                b *= 0.3 + 2.5 * math.exp(-da * 1.5)
            cols.append((b, b * 0.85, b * 0.6))
    p = np.array(pts, np.float32)
    c = np.array(cols, np.float32) * gain
    return p, c, np.full(len(p), 0.004 * radius, np.float32)


def burst(t, t0, center=(0, 0, 0), n=6000, speed=2.0, seed=0, col=(1.0, 0.8, 0.5), life=2.5, size=0.01, gain=0.35):
    """One-shot spherical particle burst (sparks)."""
    dt = t - t0
    if dt < 0 or dt > life:
        z = np.zeros((0, 3), np.float32)
        return z, z, np.zeros(0, np.float32)
    rng = np.random.default_rng(seed)
    d = rng.normal(size=(n, 3)); d /= np.linalg.norm(d, axis=1, keepdims=True)
    v = d * speed * rng.uniform(0.65, 1.0, (n, 1)) ** 0.5
    p = np.asarray(center, np.float32) + v * (1 - math.exp(-dt * 3.0)) / 3.0 * 2.5
    p[:, 1] -= 0.25 * speed * dt * dt
    f = math.exp(-dt * 3.0 / life * 2.5) * min(1.0, dt / 0.03)
    c = np.array(col, np.float32)[None] * (f * gain * rng.uniform(0.2, 1.5, (n, 1)) ** 2)
    return p.astype(np.float32), c.astype(np.float32), np.full(n, size, np.float32)
