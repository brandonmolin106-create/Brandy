"""Procedural 3D particle scenery for Echoes in the Dark.

Every element precomputes its particles once and returns (pos, col, size)
arrays for a given time. Colours are linear HDR radiance; a particle's
screen flux is col * r_px^2, so sizes are chosen per element to land in
a sensible pixel range for the shots they're used in.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from noise3 import curl, fbm, ridged

PALETTES = {
    # deep space: indigo -> violet -> magenta -> gold
    'cosmic': [(0.02, 0.03, 0.12), (0.18, 0.06, 0.45), (0.65, 0.12, 0.55), (1.0, 0.55, 0.25), (1.0, 0.9, 0.6)],
    'ice': [(0.01, 0.03, 0.08), (0.05, 0.2, 0.45), (0.2, 0.6, 0.9), (0.7, 0.9, 1.0)],
    'ember': [(0.05, 0.01, 0.0), (0.45, 0.06, 0.02), (1.0, 0.35, 0.05), (1.0, 0.8, 0.35)],
    'dawn': [(0.05, 0.03, 0.1), (0.5, 0.15, 0.3), (1.0, 0.45, 0.25), (1.0, 0.8, 0.5), (1.0, 0.97, 0.85)],
    'teal': [(0.0, 0.03, 0.05), (0.0, 0.2, 0.3), (0.1, 0.6, 0.65), (0.6, 1.0, 0.9)],
    'blood': [(0.03, 0.0, 0.01), (0.3, 0.0, 0.05), (0.9, 0.1, 0.15), (1.0, 0.5, 0.4)],
}


def palette(name, x):
    stops = np.array(PALETTES[name], np.float32)
    x = np.clip(np.asarray(x, np.float32), 0, 1) * (len(stops) - 1)
    i = np.minimum(x.astype(int), len(stops) - 2)
    f = (x - i)[..., None]
    return stops[i] * (1 - f) + stops[i + 1] * f


def _cat(*parts):
    parts = [p for p in parts if p is not None and len(p[0])]
    if not parts:
        z = np.zeros((0, 3), np.float32)
        return z, z, np.zeros(0, np.float32)
    return (np.concatenate([p[0] for p in parts]).astype(np.float32),
            np.concatenate([p[1] for p in parts]).astype(np.float32),
            np.concatenate([p[2] for p in parts]).astype(np.float32))


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float32)


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float32)


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float32)


STAR_COLORS = np.array([(0.62, 0.72, 1.0), (0.8, 0.86, 1.0), (1.0, 1.0, 1.0), (1.0, 0.92, 0.78), (1.0, 0.78, 0.55)],
                       np.float32)


class Starfield:
    """Stars on a thick shell around the origin, sized to stay ~sub-pixel."""

    def __init__(self, n=140000, r0=60, r1=400, seed=1, px_k=0.00013, bright=1.0, milky=0.45):
        rng = np.random.default_rng(seed)
        d = rng.normal(size=(n, 3))
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        # a milky-way band: concentrate part of the stars near a tilted plane
        nb_ = int(n * milky)
        band_n = np.array([0.25, 0.9, 0.35]); band_n /= np.linalg.norm(band_n)
        dd = d[:nb_]
        dd -= np.outer(dd @ band_n, band_n) * rng.uniform(0.85, 1.0, (nb_, 1))
        d[:nb_] = dd / np.linalg.norm(dd, axis=1, keepdims=True)
        r = rng.uniform(r0, r1, (n, 1))
        self.pos = (d * r).astype(np.float32)
        mag = rng.pareto(2.2, n) + 1.0
        b = np.clip(mag, 1, 40) * bright * 1.6
        c = STAR_COLORS[rng.integers(0, len(STAR_COLORS), n)]
        self.col = (c * b[:, None]).astype(np.float32)
        self.size = (r[:, 0] * px_k * rng.uniform(0.7, 1.4, n)).astype(np.float32)
        self.tw = rng.uniform(0, 6.28, n).astype(np.float32)
        self.tws = rng.uniform(0.5, 3.0, n).astype(np.float32)

    def at(self, t, twinkle=0.25, gain=1.0, center=(0, 0, 0)):
        f = 1.0 + twinkle * np.sin(self.tw + t * self.tws)
        return self.pos + np.asarray(center, np.float32), self.col * (f * gain)[:, None], self.size


class Nebula:
    """Soft volumetric gas (big blurred particles) + embedded sparkles."""

    def __init__(self, center=(0, 0, -80), extent=(90, 60, 50), n=45000, seed=2, pal='cosmic', thresh=0.08,
                 gas_size=1.6, bright=0.05, sparkles=15000):
        rng = np.random.default_rng(seed)
        m = n * 6
        p = rng.uniform(-1, 1, (m, 3)).astype(np.float32)
        p = p[(p ** 2).sum(1) < 1]
        dens = fbm(p * 1.6 + seed * 3.1, 5)
        shape = 1 - (p ** 2).sum(1)
        v = dens + 0.35 * shape - 0.25
        keep = v > thresh
        p, v = p[keep], v[keep]
        if len(p) > n:
            idx = rng.choice(len(p), n, replace=False)
            p, v = p[idx], v[idx]
        hue = np.clip(fbm(p * 1.1 + 40.0, 3) * 1.4 + 0.5, 0, 1)
        w = np.clip((v - thresh) / (v.max() - thresh + 1e-6), 0, 1)
        col = palette(pal, 0.25 + 0.75 * hue * (0.4 + 0.6 * w)) * (bright * (0.3 + 1.2 * w))[:, None]
        ext = np.array(extent, np.float32)
        self.base = p * ext
        self.center = np.array(center, np.float32)
        self.col = col.astype(np.float32)
        self.size = (gas_size * (0.6 + 0.8 * rng.random(len(p)))).astype(np.float32)
        # sparkles: small bright stars sitting in the dense parts
        if sparkles:
            q = p[rng.choice(len(p), sparkles)] + rng.normal(0, 0.04, (sparkles, 3)).astype(np.float32)
            self.sp_pos = q * ext
            hue2 = np.clip(fbm(q * 1.1 + 40.0, 3) * 1.4 + 0.5, 0, 1)
            self.sp_col = (palette(pal, 0.55 + 0.45 * hue2) * rng.pareto(2.0, sparkles)[:, None] * 1.5 + 0.4
                           ).astype(np.float32)
            self.sp_size = np.full(sparkles, 0.02, np.float32) * rng.uniform(0.6, 1.5, sparkles).astype(np.float32)
        else:
            self.sp_pos = np.zeros((0, 3), np.float32)
            self.sp_col = np.zeros((0, 3), np.float32)
            self.sp_size = np.zeros(0, np.float32)

    def at(self, t, spin=0.004, gain=1.0, sparkle_gain=1.0):
        R = rot_y(t * spin)
        p = self.base @ R.T + self.center
        sp = self.sp_pos @ R.T + self.center
        return _cat((p, self.col * gain, self.size), (sp, self.sp_col * sparkle_gain, self.sp_size))


class Dust:
    """Floating motes around a moving centre; close ones become bokeh."""

    def __init__(self, n=5000, box=(6, 8, 10), seed=3, color=(1.0, 0.8, 0.55), bright=0.9, size=0.004):
        rng = np.random.default_rng(seed)
        self.box = np.array(box, np.float32)
        self.base = (rng.random((n, 3)) - 0.5).astype(np.float32) * self.box
        self.vel = rng.normal(0, 0.03, (n, 3)).astype(np.float32)
        self.vel[:, 1] += 0.015
        self.ph = rng.uniform(0, 6.28, n).astype(np.float32)
        c = np.array(color, np.float32)
        self.col = (c * (rng.pareto(2.5, n)[:, None] * 0.6 + 0.4) * bright).astype(np.float32)
        self.size = (size * rng.uniform(0.5, 1.8, n)).astype(np.float32)

    def at(self, t, center=(0, 0, 0), gain=1.0, wind=(0, 0, 0), cam_pos=None, near=0.5):
        p = self.base + (self.vel + np.asarray(wind, np.float32)) * t
        p[:, 0] += 0.08 * np.sin(self.ph + t * 0.4)
        p[:, 1] += 0.06 * np.sin(self.ph * 1.3 + t * 0.3)
        c = np.asarray(center, np.float32)
        p = ((p - c + self.box / 2) % self.box) - self.box / 2 + c
        flick = 0.75 + 0.25 * np.sin(self.ph * 2 + t * 1.7)
        g = flick * gain
        if cam_pos is not None:
            d = np.linalg.norm(p - np.asarray(cam_pos, np.float32), axis=1)
            f = np.clip((d - near) / near, 0, 1)
            g = g * f * f
        return p, self.col * g[:, None], self.size


class ParticleText:
    """A word made of particles, standing in 3D, that can assemble / scatter."""

    def __init__(self, text, height=1.0, density=0.9, seed=4, font='/opt/fonts/Montserrat.ttf', weight='Black',
                 color=(1.0, 0.75, 0.35), depth=0.12):
        rng = np.random.default_rng(seed)
        fs = 220
        f = ImageFont.truetype(font, fs)
        try:
            f.set_variation_by_name(weight)
        except Exception:
            pass
        l, t_, r, b = f.getbbox(text)
        img = Image.new('L', (r - l + 40, b - t_ + 40), 0)
        ImageDraw.Draw(img).text((20 - l, 20 - t_), text, font=f, fill=255)
        a = np.asarray(img, np.float32) / 255
        ys, xs = np.nonzero(a > 0.4)
        k = int(len(xs) * density)
        idx = rng.choice(len(xs), k)
        x = xs[idx] + rng.random(k)
        y = ys[idx] + rng.random(k)
        sc = height / (b - t_)
        self.base = np.stack([(x - a.shape[1] / 2) * sc, -(y - a.shape[0] / 2) * sc,
                              rng.normal(0, depth * height * 0.15, k)], -1).astype(np.float32)
        self.scatter = (rng.normal(size=(k, 3)) * np.array([3, 2, 3]) * height).astype(np.float32)
        self.col = (np.array(color, np.float32) * rng.uniform(0.6, 1.4, (k, 1))).astype(np.float32)
        self.size = np.full(k, sc * 0.9, np.float32)
        self.ph = rng.uniform(0, 1, k).astype(np.float32)
        self.width = a.shape[1] * sc

    def at(self, t, form=1.0, center=(0, 0, 0), R=None, gain=1.0, jitter=0.0):
        """form: 0 = fully scattered, 1 = fully assembled (per-particle staggered)."""
        f = np.clip(form * 1.6 - self.ph * 0.6, 0, 1)
        f = f * f * (3 - 2 * f)
        p = self.base * f[:, None] + (self.base + self.scatter) * (1 - f[:, None])
        if jitter:
            p = p + np.sin(self.ph[:, None] * 50 + t * 3 + np.array([0, 1.7, 3.1])) * jitter
        if R is not None:
            p = p @ R.T
        p = p + np.asarray(center, np.float32)
        return p, self.col * (gain * (0.3 + 0.7 * f))[:, None], self.size


class Galaxy:
    def __init__(self, n=260000, radius=60.0, arms=3, seed=5, twist=3.2, thickness=1.6):
        rng = np.random.default_rng(seed)
        nb_ = int(n * 0.18)
        na = n - nb_
        r = radius * (rng.random(na) ** 1.6) + 1.0
        arm = rng.integers(0, arms, na)
        th = np.log(r) * twist + arm * (2 * np.pi / arms) + rng.normal(0, 0.28, na) * (1.2 - r / radius)
        spread = rng.normal(0, 1, (na, 2)) * (0.06 * r[:, None] + 0.6)
        x = r * np.cos(th) + spread[:, 0]
        z = r * np.sin(th) + spread[:, 1]
        y = rng.normal(0, thickness * np.exp(-r / radius * 1.5), na)
        bulge = rng.normal(0, radius * 0.08, (nb_, 3)) * np.array([1, 0.55, 1])
        self.base = np.concatenate([np.stack([x, y, z], -1), bulge]).astype(np.float32)
        rr = np.linalg.norm(self.base[:, [0, 2]], axis=1)
        self.r = rr.astype(np.float32)
        self.th0 = np.arctan2(self.base[:, 2], self.base[:, 0]).astype(np.float32)
        core = np.exp(-rr / (radius * 0.12))
        colw = np.array([1.0, 0.85, 0.6])
        colb = np.array([0.55, 0.7, 1.0])
        mix = np.clip(core * 1.5, 0, 1)[:, None]
        c = colw * mix + colb * (1 - mix)
        pink = rng.random(len(rr)) < 0.03
        c[pink] = np.array([1.0, 0.35, 0.6])
        b = (0.4 + 1.1 * core + rng.pareto(3, len(rr)) * 0.5)
        b[pink] *= 2.0
        self.col = (c * b[:, None] * 0.9).astype(np.float32)
        self.size = (0.05 + 0.1 * rng.random(len(rr))).astype(np.float32)

    def at(self, t, center=(0, 0, 0), tilt=0.45, spin=0.05, gain=1.0, R=None):
        om = spin / np.sqrt(np.maximum(self.r, 1.0) / 10.0)
        th = self.th0 + om * t
        p = np.stack([self.r * np.cos(th), self.base[:, 1], self.r * np.sin(th)], -1)
        M = rot_x(tilt) if R is None else R
        p = p @ M.T + np.asarray(center, np.float32)
        return p.astype(np.float32), self.col * gain, self.size
