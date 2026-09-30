"""Echoes in the Dark - 6:00 logo formation trailer renderer.

Every frame is rendered procedurally (numpy + numexpr + OpenCV) from the vectorised
emblem, so the logo stays razor sharp in UHD even with the camera deep inside it.

  python3 render.py --stills 30,96,150,276.3,285,310,335 --scale 0.25   # preview stills
  python3 render.py --start 0 --end 2160 --out out/seg/seg0.mp4          # frames [start, end)
"""
import argparse
import json
import math
import os
import re
import subprocess
import time

import cv2
import numexpr as ne
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import timeline as T

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "assets", "cache")
FONT = os.path.join(HERE, "assets", "Jost-300.ttf")

GOLD = np.array([0.95, 0.76, 0.42], np.float32)
GOLD_HOT = np.array([1.0, 0.92, 0.74], np.float32)
SILVER = np.array([0.80, 0.815, 0.85], np.float32)
PLATINUM = np.array([0.70, 0.715, 0.75], np.float32)
LOGO_GOLD = np.array([200, 178, 126], np.float32) / 255.0
PAPER = np.array([0.957, 0.953, 0.941], np.float32)
INK = np.array([0.065, 0.065, 0.07], np.float32)
DUST = np.array([0.85, 0.88, 0.95], np.float32)
WARM_WHITE = np.array([1.0, 0.97, 0.9], np.float32)


# ----------------------------------------------------------------------------- numexpr
_NUM = re.compile(r"(?<![\w.])(\d+\.?\d*(?:e-?\d+)?|\.\d+)(?![\w.])")
_EV_CACHE = {}


def ev(expr, d):
    """numexpr.evaluate that keeps everything float32 (plain literals would silently
    promote whole 4K frames to float64 and double the render time)."""
    hit = _EV_CACHE.get(expr)
    if hit is None:
        consts = {}

        def rep(m):
            k = f"_k{len(consts)}"
            consts[k] = np.float32(float(m.group(0)))
            return k
        hit = (_NUM.sub(rep, expr), consts)
        _EV_CACHE[expr] = hit
    e2, consts = hit
    return ne.evaluate(e2, local_dict={**d, **consts})


# ----------------------------------------------------------------------------- easing
def clamp01(x):
    return min(1.0, max(0.0, x))


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_io(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_out_expo(x):
    x = clamp01(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def span(t, a, b):
    return clamp01((t - a) / (b - a))


def lerp(a, b, u):
    return a + (b - a) * u


def pulse(t, t0, decay):
    return math.exp(-(t - t0) / decay) if t >= t0 else 0.0


# ----------------------------------------------------------------------------- growth
def growth_front(t):
    u = span(t, *T.GROW)
    f = 0.7 * u + 0.3 * (0.5 - 0.5 * math.cos(math.pi * u))
    return lerp(-0.02, 1.04, f)


_F_SAMPLES = np.linspace(T.GROW[0], T.GROW[1], 6000)
_F_VALUES = np.array([growth_front(x) for x in _F_SAMPLES])


def growth_time(d):
    return np.interp(d, _F_VALUES, _F_SAMPLES).astype(np.float32)


# ----------------------------------------------------------------------------- warping
def build_mips(img, levels=4):
    mips = [(img, 1.0)]
    cur = img
    for i in range(1, levels):
        cur = cv2.resize(cur, (max(1, cur.shape[1] // 2), max(1, cur.shape[0] // 2)),
                         interpolation=cv2.INTER_AREA)
        mips.append((cur, 0.5 ** i))
    return mips


def make_G(a, bx, by, theta=0.0, cx=0.0, cy=0.0, f=6500.0):
    """Homography from mask space to screen: scale a, offset b, plus an optional
    rotation of the logo plane around the vertical axis through (cx, cy)."""
    if abs(theta) < 1e-6:
        return np.array([[a, 0, bx], [0, a, by], [0, 0, 1]], np.float64)
    s, c = math.sin(theta), math.cos(theta)
    Hm = np.array([[a * cx * s + a * f * c + bx * s, 0, a * cx * f + bx * f],
                   [a * cy * s + by * s, a * f, a * cy * f + by * f],
                   [s, 0, f]], np.float64)
    Tm = np.array([[1, 0, -cx], [0, 1, -cy], [0, 0, 1]], np.float64)
    G = Hm @ Tm
    return G / G[2, 2]


def apply_G(G, x, y):
    v = G @ np.array([x, y, 1.0])
    return v[0] / v[2], v[1] / v[2]


def warp_sprite(mips, ox, oy, G, a, W, H, pad=2, border=0):
    """Place a mask-space image (origin ox, oy) on screen through homography G.
    Returns ((Y0, Y1, X0, X1), pixels) cropped to the frame, or None."""
    img, sc = mips[0]
    for m, s in mips:
        if a / s >= 0.7:
            img, sc = m, s
    h, w = img.shape[:2]
    P = np.array([[1 / sc, 0, ox], [0, 1 / sc, oy], [0, 0, 1]], np.float64)
    M = G @ P
    pts = [M @ np.array([u, v, 1.0]) for u, v in ((0, 0), (w, 0), (0, h), (w, h))]
    xs = [p[0] / p[2] for p in pts]
    ys = [p[1] / p[2] for p in pts]
    X0 = max(0, int(math.floor(min(xs))) - pad)
    Y0 = max(0, int(math.floor(min(ys))) - pad)
    X1 = min(W, int(math.ceil(max(xs))) + pad)
    Y1 = min(H, int(math.ceil(max(ys))) + pad)
    if X1 <= X0 or Y1 <= Y0:
        return None
    M = np.array([[1, 0, -X0], [0, 1, -Y0], [0, 0, 1]], np.float64) @ M
    size = (X1 - X0, Y1 - Y0)
    if abs(M[2, 0]) < 1e-12 and abs(M[2, 1]) < 1e-12:
        out = cv2.warpAffine(img, (M[:2] / M[2, 2]).astype(np.float32), size, flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=border)
    else:
        out = cv2.warpPerspective(img, M, size, flags=cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_CONSTANT, borderValue=border)
    return (Y0, Y1, X0, X1), out


def warp_region(mips, G, a, X0, Y0, w, h, k, border=0):
    """Sample a mask-space image on a k-scaled pixel grid covering the full-res screen
    region that starts at (X0, Y0): lets surface shading run at reduced resolution."""
    img, sc = mips[0]
    for m, s in mips:
        if a * k / s >= 0.7:
            img, sc = m, s
    P = np.array([[1 / sc, 0, 0], [0, 1 / sc, 0], [0, 0, 1]], np.float64)
    Sk = np.array([[k, 0, 0.5 * k - 0.5], [0, k, 0.5 * k - 0.5], [0, 0, 1]], np.float64)
    Tr = np.array([[1, 0, -X0], [0, 1, -Y0], [0, 0, 1]], np.float64)
    M = Sk @ Tr @ G @ P
    if abs(M[2, 0]) < 1e-12 and abs(M[2, 1]) < 1e-12:
        return cv2.warpAffine(img, (M[:2] / M[2, 2]).astype(np.float32), (w, h), flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_CONSTANT, borderValue=border)
    return cv2.warpPerspective(img, M, (w, h), flags=cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_CONSTANT, borderValue=border)


# ----------------------------------------------------------------------------- assets
class Assets:
    def __init__(self, sc):
        self.sc = sc
        self.W = int(round(T.W * sc))
        self.H = int(round(T.H * sc))
        meta = json.load(open(os.path.join(CACHE, "meta.json")))
        self.meta = meta
        ld = lambda n: np.load(os.path.join(CACHE, n)).astype(np.float32)
        sdf, dist, edt, grain = ld("sdf.npy"), ld("dist.npy"), ld("edt.npy"), ld("grain.npy")
        self.emb = build_mips(np.dstack([sdf, dist, edt, grain]), 5)
        bx0, by0, bx1, by1 = meta["bbox"]
        self.emb_c = np.array([(bx0 + bx1) / 2, (by0 + by1) / 2], np.float64)
        self.emb_h = by1 - by0
        self.emb_w = bx1 - bx0
        self.axis = meta["axis"]
        self.star = np.array(meta["star"], np.float64)
        self.star_r = meta["star_radius"]
        self.s_hero = 1500.0 / self.emb_h

        # Spark emitters: points inside the strokes with their growth distance.
        ys, xs = np.where((sdf > 3) & (edt > 0.5))
        rng = np.random.default_rng(7)
        pick = rng.choice(len(xs), 30000, replace=False)
        self.sp_xy = np.stack([xs[pick], ys[pick]], 1).astype(np.float32)
        self.sp_d = dist[ys[pick], xs[pick]]
        ang = rng.uniform(0, 2 * np.pi, len(pick))
        spd = rng.uniform(15, 90, len(pick))
        self.sp_v = np.stack([np.cos(ang) * spd, np.sin(ang) * spd - 20], 1).astype(np.float32)
        self.sp_life = rng.uniform(0.6, 2.2, len(pick)).astype(np.float32)
        self.sp_size = rng.choice([1, 1, 1, 2, 2, 3], len(pick)).astype(np.float32)
        self.sp_te = growth_time(self.sp_d)

        self._build_text()
        self._build_particles()
        self._build_screen_layers()
        self._build_camera_path()

    # --- text lives in mask space so the camera moves it with the emblem
    def _build_text(self):
        bx0, by0, bx1, by1 = self.meta["bbox"]
        cap = self.emb_h * 41.0 / 340.0
        gap = self.emb_h * 65.0 / 340.0
        width = self.emb_w * 642.0 / 395.0 * 0.985
        top = by1 + gap
        size = int(cap / 0.70)
        font = ImageFont.truetype(FONT, size)
        cap_box = font.getbbox("E")
        size = int(size * cap / (cap_box[3] - cap_box[1]))
        font = ImageFont.truetype(FONT, size)
        text = "ECHOES IN THE DARK"
        adv = [font.getlength(ch) for ch in text]
        track = (width - sum(adv)) / (len(text) - 1)
        x = self.emb_c[0] - width / 2
        cap_top = font.getbbox("E")[1]
        self.letters = []
        pad = int(size * 0.3)
        order = 0
        for ch, a in zip(text, adv):
            if ch != " ":
                bb = font.getbbox(ch)
                im = Image.new("L", (int(bb[2] + pad * 2), int(size * 1.2 + pad * 2)), 0)
                ImageDraw.Draw(im).text((pad, pad), ch, font=font, fill=255)
                arr = np.asarray(im, np.float32) / 255.0
                self.letters.append(dict(mips=build_mips(arr, 5), ox=x - pad, oy=top - cap_top - pad,
                                         cx=x + a / 2, cy=top + cap / 2, order=order))
                order += 1
            x += a + track
        self.n_letters = order
        self.word_top = top
        self.word_bottom = top + cap

        tag = "STORIES  THAT  ECHO  FOREVER"
        tsize = int(size * 0.34)
        tfont = ImageFont.truetype(FONT, tsize)
        spacing = tsize * 0.42
        adv = [tfont.getlength(c) for c in tag]
        tw = sum(adv) + spacing * (len(tag) - 1)
        pad = int(tsize * 0.4)
        im = Image.new("L", (int(tw + pad * 2), int(tsize * 1.4 + pad * 2)), 0)
        d = ImageDraw.Draw(im)
        xx = pad
        for c, a in zip(tag, adv):
            d.text((xx, pad), c, font=tfont, fill=255)
            xx += a + spacing
        arr = np.asarray(im, np.float32) / 255.0
        self.tag = dict(mips=build_mips(arr, 5), ox=self.emb_c[0] - tw / 2 - pad,
                        oy=top + cap + gap * 0.62 - pad - tfont.getbbox("S")[1])

    def _build_particles(self):
        rng = np.random.default_rng(11)
        n = 3200
        self.p_base = rng.uniform([-0.05, -0.05], [1.05, 1.05], (n, 2)).astype(np.float32)
        self.p_z = (rng.uniform(0.15, 1.0, n) ** 1.6).astype(np.float32)
        self.p_v = (rng.normal(0, 1, (n, 2)) * 0.0022 + np.array([0.0009, -0.0016])).astype(np.float32)
        self.p_phase = rng.uniform(0, 2 * np.pi, n).astype(np.float32)
        self.p_tw = rng.uniform(0.4, 2.2, n).astype(np.float32)
        self.p_g0 = rng.uniform(T.GATHER[0], T.GATHER[1] - 6.0, n).astype(np.float32)
        self.p_gd = rng.uniform(3.0, 6.0, n).astype(np.float32)
        self.p_spin = (rng.uniform(1.5, 4.0, n) * rng.choice([-1, 1], n)).astype(np.float32)
        self.p_gold = rng.uniform(0, 1, n) < 0.35
        self.p_bokeh = rng.uniform(0, 1, n) < 0.06

    def _build_screen_layers(self):
        W, H = self.W, self.H
        self.yy, self.xx = np.mgrid[0:H, 0:W].astype(np.float32)
        nx = (self.xx - W / 2) / (W / 2)
        ny = (self.yy - H / 2) / (H / 2)
        r = np.sqrt(nx * nx * 0.78 + ny * ny)
        self.vignette = (1.0 - 0.42 * np.clip(r, 0, 1.6) ** 2.3).clip(0.2, 1)[..., None].astype(np.float32)
        base = np.float32([0.010, 0.011, 0.016])
        edge = np.float32([0.002, 0.002, 0.004])
        g = np.clip(r / 1.3, 0, 1)[..., None]
        self.bg = (base * (1 - g) + edge * g).astype(np.float32)
        self.paper = (PAPER * (1 - 0.06 * np.clip(r, 0, 1.5) ** 2)[..., None]).astype(np.float32)
        rng = np.random.default_rng(3)
        self.grain = [rng.normal(0, 1, (H // 2 + 1, W // 2 + 1)).astype(np.float32) for _ in range(8)]
        qw, qh = W // 4, H // 4
        self.qw, self.qh = qw, qh
        self.qyy, self.qxx = np.mgrid[0:qh, 0:qw].astype(np.float32)
        fog = np.zeros((qh * 2, qw * 2), np.float32)
        for o in range(6):
            f = 2 ** o
            n = rng.normal(0, 1, (max(2, qh * 2 // (48 // f + 1)), max(2, qw * 2 // (48 // f + 1)))).astype(np.float32)
            fog += cv2.resize(n, (qw * 2, qh * 2), interpolation=cv2.INTER_CUBIC) / (1.7 ** o)
        fog = (fog - fog.min()) / (fog.max() - fog.min())
        self.fog = (np.clip((fog - 0.45) * 2.2, 0, 1) ** 1.6).astype(np.float32)
        self.bar = int(round((T.H - T.W / 2.39) / 2 * self.sc))

    # --- the camera path is precomputed once so it can be smoothed
    def _build_camera_path(self):
        cen = np.array(self.meta["front_centroid"], np.float64)
        k = np.exp(-0.5 * (np.arange(-12, 13) / 5.0) ** 2)
        k /= k.sum()
        pad = np.pad(cen, ((12, 12), (0, 0)), mode="edge")
        self.cen = np.stack([np.convolve(pad[:, i], k, "valid") for i in range(2)], 1)
        n = int(T.DURATION * T.FPS) + 2
        ts = np.arange(n) / T.FPS
        raw = np.array([self._camera_raw(t) for t in ts])
        sm = raw.copy()
        sig = int(1.6 * T.FPS)
        kk = np.exp(-0.5 * (np.arange(-3 * sig, 3 * sig + 1) / sig) ** 2)
        kk /= kk.sum()
        for i in range(3):
            p = np.pad(raw[:, i], (3 * sig, 3 * sig), mode="edge")
            sm[:, i] = np.convolve(p, kk, "valid")
        wgt = np.array([smooth(span(t, 99.0, 102.0)) * (1 - smooth(span(t, 268.0, 272.0))) for t in ts])
        self.cam_path = raw * (1 - wgt[:, None]) + sm * wgt[:, None]

    def front_centroid(self, f, side):
        f = min(max(f, 0.0), 0.999)
        i = f * (len(self.cen) - 1)
        i0 = int(i)
        i1 = min(i0 + 1, len(self.cen) - 1)
        p = self.cen[i0] * (1 - (i - i0)) + self.cen[i1] * (i - i0)
        if side > 0:
            p = np.array([2 * self.axis - p[0], p[1]])
        return p

    def _camera_raw(self, t):
        C, star, sh = self.emb_c, self.star, self.s_hero
        if t < 95.5:
            z = 6.0
            z = lerp(z, 4.5, ease_io(span(t, 20, 45)))
            z = lerp(z, 1.35, ease_io(span(t, 45, 92)))
            z = lerp(z, 1.25, ease_io(span(t, 92, 95.5)))
            F = star + (C - star) * 0.55 * ease_io(span(t, 45, 92))
        elif t < 272.0:
            f = growth_front(t)
            left = self.front_centroid(f + 0.015, -1)
            right = self.front_centroid(f + 0.015, +1)
            side = smooth(span(t, 148, 158)) * (1 - smooth(span(t, 196, 206)))
            follow = left * (1 - side) + right * side
            w = 0.35 * smooth(span(t, 206, 215)) + 0.25 * smooth(span(t, 225, 245)) + 0.4 * smooth(span(t, 250, 270))
            follow = follow * (1 - w) + C * w
            keys = [(99.5, 5.0), (150, 3.2), (200, 2.4), (245, 1.6), (270, 1.0)]
            z = keys[0][1]
            for (t0, z0), (t1, z1) in zip(keys[:-1], keys[1:]):
                if t >= t0:
                    z = math.exp(lerp(math.log(z0), math.log(z1), ease_io(span(t, t0, t1))))
            ru = ease_io(span(t, 95.5, 99.5))  # the rush in after the boom
            pre = star + (C - star) * 0.55
            F = pre * (1 - ru) + follow * ru
            z = math.exp(lerp(math.log(1.25), math.log(z), ru))
        else:
            z = 1.0 + 0.06 * ease_io(span(t, 272, 297))
            s_lock = 980.0 / self.emb_h
            lock_total = 980 + self.emb_h * (65 + 41) / 340.0 * s_lock
            lock_center_y = (T.H - lock_total) / 2 + 490
            F_lock = np.array([C[0], C[1] + (T.H / 2 - lock_center_y) / s_lock])
            u = ease_io(span(t, *T.LOCKUP))
            z = lerp(z, s_lock / sh, u)
            F = C + (F_lock - C) * u
            z *= 1 + 0.045 * smooth(span(t, T.LOCKUP[1], T.COLLAPSE[0]))
            if t > T.COLLAPSE[0]:
                F = F + (star - F) * ease_io(span(t, T.COLLAPSE[0] + 0.4, T.COLLAPSE[1] + 1.5))
                z *= 1 + 2.4 * ease_io(span(t, T.COLLAPSE[0] + 0.6, T.DURATION))
        return [F[0], F[1], z]

    def camera(self, t):
        i = t * T.FPS
        i0 = int(min(max(i, 0), len(self.cam_path) - 2))
        u = i - i0
        fx, fy, z = self.cam_path[i0] * (1 - u) + self.cam_path[i0 + 1] * u
        s = z * self.s_hero
        # handheld drift + impact shake (screen px at 4K)
        dx = math.sin(t * 0.37) * 5 + math.sin(t * 0.91 + 1) * 2
        dy = math.cos(t * 0.29) * 4 + math.sin(t * 0.73 + 2) * 1.5
        kick = 26 * pulse(t, T.BOOM, 0.45) + 34 * pulse(t, T.COMPLETE, 0.5)
        dx += kick * math.sin(t * 71.0)
        dy += kick * math.cos(t * 57.0)
        fx += dx / s
        fy += dy / s
        theta = 0.0
        if T.ORBIT[0] < t < T.ORBIT[1]:
            u = span(t, *T.ORBIT)
            theta = 0.24 * math.sin(2 * math.pi * u) * math.sin(math.pi * u)
        return fx, fy, s, theta


# ----------------------------------------------------------------------------- drawing
def add_color(img, roi, weight, color):
    y0, y1, x0, x1 = roi
    img[y0:y1, x0:x1] += weight[..., None] * color


def over_color(img, roi, cov, color):
    y0, y1, x0, x1 = roi
    c = cov[..., None]
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - c) + c * color


RINGS_ALL = ([(r, 0, 1.0) for r in T.RINGS] + [(r, 0, 0.8) for r in T.GROW_RINGS]
             + [(r, 1, 1.3) for r in T.LATE_RINGS])


def ring_list(t):
    out = []
    for r0, big, amp0 in RINGS_ALL:
        for dt, amp in ((0, 1.0), (0.22, 0.45), (0.44, 0.2)):
            age = t - r0 - dt
            if 0 <= age < 3.5:
                out.append((age, amp * amp0, big))
    return out


def ring_radius(age, big):
    return (1600 if big else 1150) * (1 - math.exp(-age * 1.1)) + 420 * age


def star_intensity(t):
    if t < T.SPARK:
        return 0.0
    ign = ease_out_expo(span(t, T.SPARK, T.SPARK + 0.6))
    beat = sum(pulse(t, r, 0.35) for r in T.RINGS if r <= t) * 0.35
    beat += sum(pulse(t, r, 0.5) for r in T.GROW_RINGS if r <= t) * 0.25
    out = 1 - smooth(span(t, T.STAR_OUT, T.STAR_OUT + 0.35))
    flash = 1.8 * pulse(t, T.SPARK, 0.25)
    hold = 1 - 0.55 * smooth(span(t, T.SILENCE[0], T.SILENCE[0] + 0.3)) * (t < T.COMPLETE)
    return (ign * (1.0 + beat) + flash) * out * hold


def star_scale(t):
    if t < T.SPARK:
        return 0.0
    u = span(t, T.SPARK, T.SPARK + 1.1)
    over = 1 + 0.35 * math.sin(u * math.pi) * (1 - u)
    return ease_out(u) * over * (1 + 0.04 * math.sin(t * 2.1))


def draw_star(img, cx, cy, R, inten, flare, A, light=0.0, q=None):
    """Four-point star: crisp core + streaks at full res, soft glow in the quarter-res
    light layer (q) so a huge close-up star stays cheap."""
    W, H, sc = A.W, A.H, A.sc
    if inten <= 0.001 or R <= 0.2:
        return
    dark = 1 - light
    fl = np.float32(flare * dark)
    # soft glow -> quarter res
    if q is not None and dark > 0:
        hq = min(R * 7, 700 * sc) / 4 + 2
        qx0, qx1 = max(0, int(cx / 4 - hq)), min(A.qw, int(cx / 4 + hq))
        qy0, qy1 = max(0, int(cy / 4 - hq)), min(A.qh, int(cy / 4 + hq))
        if qx1 > qx0 and qy1 > qy0:
            gl = ev("(exp(-(rr/(R*1.3))**2)*0.55 + exp(-rr/(R*2.4))*0.22) * where(rr < hq, (1 - rr/hq)**2, 0) * k",
                    dict(rr=ev("sqrt((xx-cx)**2+(yy-cy)**2)", dict(xx=A.qxx[qy0:qy1, qx0:qx1], yy=A.qyy[qy0:qy1, qx0:qx1],
                                                                  cx=np.float32(cx / 4), cy=np.float32(cy / 4))),
                         R=np.float32(R / 4), hq=np.float32(hq), k=np.float32(inten * dark)))
            q[qy0:qy1, qx0:qx1] += gl[..., None] * GOLD
    # crisp core
    half = int(max(R * 1.25, 3))
    x0, x1 = max(0, int(cx - half)), min(W, int(cx + half))
    y0, y1 = max(0, int(cy - half)), min(H, int(cy + half))
    if x1 > x0 and y1 > y0:
        v = dict(xx=A.xx[y0:y1, x0:x1], yy=A.yy[y0:y1, x0:x1], cx=np.float32(cx), cy=np.float32(cy), R=np.float32(R))
        cov = ev("(1 - ((abs(xx-cx)+0.001)**0.56 + (abs(yy-cy)+0.001)**0.56)**(1/0.56)/R)*R*0.9+0.5", v)
        np.clip(cov, 0, 1, out=cov)
        core = GOLD_HOT * np.float32(min(inten, 1.6) * dark) + LOGO_GOLD * np.float32(light)
        region = img[y0:y1, x0:x1]
        region[:] = region * (1 - cov[..., None]) + cov[..., None] * core
    if fl <= 0.001:
        return
    # thin anamorphic streaks: a horizontal band and a short vertical one
    for horiz in (True, False):
        if horiz:
            bw, ln = int(max(2, R * 0.3)), int(min(W, R * 30))
            X0, X1, Y0, Y1 = max(0, int(cx - ln)), min(W, int(cx + ln)), max(0, int(cy - bw)), min(H, int(cy + bw))
        else:
            bw, ln = int(max(2, R * 0.3)), int(R * 5)
            X0, X1, Y0, Y1 = max(0, int(cx - bw)), min(W, int(cx + bw)), max(0, int(cy - ln)), min(H, int(cy + ln))
        if X1 <= X0 or Y1 <= Y0:
            continue
        v = dict(xx=A.xx[Y0:Y1, X0:X1], yy=A.yy[Y0:Y1, X0:X1], cx=np.float32(cx), cy=np.float32(cy),
                 R=np.float32(R), f=fl, i=np.float32(min(inten, 1.5)))
        if horiz:
            st = ev("(exp(-(abs(yy-cy)/(R*0.06))**2)*exp(-abs(xx-cx)/(R*1.4))*0.9*i"
                    " + exp(-((yy-cy)/(R*0.05))**2)*exp(-abs(xx-cx)/(R*22))*0.35) * f", v)
        else:
            st = ev("exp(-(abs(xx-cx)/(R*0.06))**2)*exp(-abs(yy-cy)/(R*1.1))*0.6*f*i", v)
        img[Y0:Y1, X0:X1] += st[..., None] * GOLD


GOLD8 = tuple(float(c) for c in GOLD)
DUST8 = tuple(float(c) for c in DUST)


def draw_dot(lay, x, y, r, v, col):
    cv2.circle(lay, (int(x * 16), int(y * 16)), max(1, int(r * 16)),
               (float(v * col[0]), float(v * col[1]), float(v * col[2])), -1, cv2.LINE_AA, 4)


def metal_body(t, v, a, A):
    """Realistic engraved platinum with gold inlay: bevelled normals from the stroke
    distance field, a moving key light, softbox reflections and brushed micro detail."""
    h = ev("1 - (1 - where(E*2.2 > 1, 1, E*2.2))**2 - 0.06*eng + 0.004*N", v).astype(np.float32)
    kz = np.float32(0.125 * 40.0 * a)  # slope scale: bevels read the same at any zoom
    gx = cv2.Sobel(h, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(h, cv2.CV_32F, 0, 1, ksize=3)
    phi = 2.3 + 0.35 * math.sin(t * 0.21) + 0.9 * smooth(span(t, T.ORBIT[0], T.ORBIT[1]))
    L = np.array([math.cos(phi), -math.sin(phi), 1.1])
    L /= np.linalg.norm(L)
    Hv = L + np.array([0, 0, 1.0])
    Hv /= np.linalg.norm(Hv)
    w = dict(gx=gx, gy=gy, kz=kz, E=v["E"], N=v["N"], eng=v["eng"], t=np.float32(t),
             Lx=np.float32(L[0]), Ly=np.float32(L[1]), Lz=np.float32(L[2]),
             Hx=np.float32(Hv[0]), Hy=np.float32(Hv[1]), Hz=np.float32(Hv[2]))
    w["nx"] = ev("-gx*kz", w)
    w["ny"] = ev("-gy*kz", w)
    w["inv"] = ev("1/sqrt(nx*nx+ny*ny+1)", w)
    w["diff"] = ev("where((nx*Lx+ny*Ly+Lz)*inv > 0, (nx*Lx+ny*Ly+Lz)*inv, 0)", w)
    w["spec"] = ev("where((nx*Hx+ny*Hy+Hz)*inv > 0, (nx*Hx+ny*Hy+Hz)*inv, 0)**90 * (1 + 0.35*N)", w)
    w["env"] = ev("(0.5+0.5*cos(nx*inv*7.0 + t*0.25 + 1.3))**8 * 0.9 + (0.5 - 0.5*ny*inv)*0.25", w)
    w["ao"] = ev("0.55 + 0.45*where(E*4 > 1, 1, E*4)", w)
    w["inl"] = ev("where(eng*1.1 > 1, 1, eng*1.1)", w)
    out = np.empty(gx.shape + (3,), np.float32)
    for c in range(3):
        w.update(P=np.float32(PLATINUM[c]), Gc=np.float32(GOLD[c]), GH=np.float32(GOLD_HOT[c]),
                 WW=np.float32(WARM_WHITE[c]))
        out[..., c] = ev(
            "((0.06 + 0.62*diff)*ao*(1 + 0.06*N)*P + spec*1.3*WW + env*ao*0.30*P) * (1 - inl)"
            " + inl * (Gc*(0.25 + 0.75*diff) + spec*1.1*GH) + exp(-E/0.07)*0.18*Gc", w)
    return out


# ----------------------------------------------------------------------------- frame
def render(t, A):
    W, H, sc = A.W, A.H, A.sc
    img = A.bg.copy()
    fx, fy, s4, theta = A.camera(t)
    a = s4 * sc
    bx = W / 2 - fx * a
    by = H / 2 - fy * a
    G = make_G(a, bx, by, theta, A.emb_c[0], A.emb_c[1])
    sx, sy = apply_G(G, A.star[0], A.star[1])

    q_extra = np.zeros((A.qh, A.qw, 3), np.float32)
    lay = np.zeros((H, W, 3), np.uint8)             # crisp dots/rings, added after tone mapping
    ring_q = np.zeros((A.qh, A.qw), np.float32)     # ring glow, quarter res

    rev_u = ease_io(span(t, *T.REVEAL))
    col_u = ease_io(span(t, *T.COLLAPSE))
    rev_r = (rev_u * (1 - col_u)) * 5200 * sc
    lt = A.paper.copy() if rev_r > 1 else None

    # --- fog lit by the star
    fog_amt = 0.05 * smooth(span(t, 2.0, 22.0)) * (1 - 0.6 * smooth(span(t, 300, 315)))
    fog_amt *= 1 - smooth(span(t, T.STAR_OUT - 1, T.FADE_END[1]))
    if fog_amt > 0.001:
        ox = int((t * 6.0) % A.qw)
        oy = int((t * 2.5) % A.qh)
        v = dict(qx=A.qxx, qy=A.qyy, sx=np.float32(sx / 4), sy=np.float32(sy / 4),
                 hw=np.float32(A.qw * 0.5), si=np.float32(min(1.0, star_intensity(t) + 0.1)),
                 fog=A.fog[oy:oy + A.qh, ox:ox + A.qw], amt=np.float32(fog_amt))
        lit = ev("fog * amt * (0.25 + 1.4*exp(-sqrt((qx-sx)**2+(qy-sy)**2)/hw*2.2)*si)", v)
        q_extra += lit[..., None] * np.float32([0.55, 0.62, 0.85])

    # --- emblem
    grow_f = growth_front(t)
    fade_out = 1 - smooth(span(t, T.COLLAPSE[1] + 0.3, T.STAR_OUT))
    if T.RINGS[0] - 0.1 < t < T.GROW[0] + 3:
        # sonar ghost: rings briefly light up the not-yet-formed giant emblem (soft, so
        # it lives in the quarter-res light layer)
        Gq = np.diag([0.25, 0.25, 1.0]) @ G
        r = warp_sprite(A.emb, 0, 0, Gq, a / 4, A.qw, A.qh, border=(-4000.0, 1.5, 0.0, 0.0))
        if r is not None:
            (qy0, qy1, qx0, qx1), fq = r
            v = dict(S=fq[..., 0], a=np.float32(a / 4), xx=A.qxx[qy0:qy1, qx0:qx1], yy=A.qyy[qy0:qy1, qx0:qx1],
                     sx=np.float32(sx / 4), sy=np.float32(sy / 4))
            Afq = ev("where(S*a+0.5 < 0, 0, where(S*a+0.5 > 1, 1, S*a+0.5))", v)
            rd = ev("sqrt((xx-sx)**2+(yy-sy)**2)", v)
            ghost = np.zeros_like(rd)
            for age, amp, big in ring_list(t):
                ghost += ev("exp(-((rd-rr)/w)**2)*k", dict(
                    rd=rd, rr=np.float32(ring_radius(age, big) * sc / 4), w=np.float32(130 * sc / 4),
                    k=np.float32(amp * math.exp(-age / 1.8))))
            gk = np.float32(0.22 * (1 - smooth(span(t, T.GROW[0], T.GROW[0] + 3))))
            base = np.float32(0.012 * smooth(span(t, 40, 90)))
            q_extra[qy0:qy1, qx0:qx1] += ev("Af*(ghost*gk + base)", dict(Af=Afq, ghost=ghost, gk=gk, base=base))[..., None] * GOLD

    if (t >= T.GROW[0] or lt is not None) and t < T.FADE_END[1]:
        r = warp_sprite(A.emb, 0, 0, G, a, W, H, border=(-4000.0, 1.5, 0.0, 0.0))
        if r is not None:
            roi, fld = r
            y0, y1, x0, x1 = roi
            fv = dict(S=fld[..., 0], D=fld[..., 1], E=fld[..., 2], N=fld[..., 3], a=np.float32(a),
                      f=np.float32(grow_f + 0.0), t=np.float32(t))
            fv["Af"] = ev("where(S*a+0.5 < 0, 0, where(S*a+0.5 > 1, 1, S*a+0.5))", fv)
            if lt is not None:
                over_color(lt, roi, fv["Af"], INK)
            if t >= T.GROW[0]:
                # full-res coverage keeps every edge razor sharp; a slightly wavy front
                fv["Dw"] = ev("D + 0.0035*N", fv)
                fv["beh"] = ev("where(Dw > f, 0, where((f-Dw)/0.03 > 1, 1, (f-Dw)/0.03))", fv)
                fv["cv"] = ev("(E - (1 - beh))/0.08 + 1", fv)
                cover = ev("Af * where(Dw < f + 0.001, 1, 0) * where(cv > 1, 1, where(cv < 0, 0, cv))", fv)

                # surface shading can run at half res when the camera is deep inside
                # the logo (the fields there are already magnified), then upsampled
                k = 0.5 if a > 1.1 else 1.0
                hh, ww = fld.shape[:2]
                if k < 1:
                    fs = warp_region(A.emb, G, a, x0, y0, int(math.ceil(ww * k)), int(math.ceil(hh * k)), k,
                                     border=(-4000.0, 1.5, 0.0, 0.0))
                    cs = None
                else:
                    fs, cs = fld, cover
                v = dict(S=fs[..., 0], D=fs[..., 1], E=fs[..., 2], N=fs[..., 3], a=np.float32(a * k),
                         f=np.float32(grow_f), t=np.float32(t), cover=cs)
                v["Dw"] = ev("D + 0.0035*N", v)
                v["Af"] = ev("where(S*a+0.5 < 0, 0, where(S*a+0.5 > 1, 1, S*a+0.5))", v)
                if cs is None:
                    v["beh"] = ev("where(Dw > f, 0, where((f-Dw)/0.03 > 1, 1, (f-Dw)/0.03))", v)
                    v["cv"] = ev("(E - (1 - beh))/0.08 + 1", v)
                    cs = ev("Af * where(Dw < f + 0.001, 1, 0) * where(cv > 1, 1, where(cv < 0, 0, cv))", v)
                    v["cover"] = cs
                heat = ev("where(Dw < f, exp(-(f-Dw)/0.007), 0) * Af", v)
                cool = ev("where(Dw < f, exp(-(f-Dw)/0.04), 0)", v)
                v["eng"] = ev("exp(-((E-0.80)/0.045)**2) + exp(-((E-0.40)/0.018)**2)*0.45", v)
                v["rib"] = ev("(0.5+0.5*cos(D*603.19))**6", v)  # feather barbs along each stroke
                v["cflash"] = np.float32(1 + 2.0 * pulse(t, T.COMPLETE, 0.4))
                shade = ev("((0.9 + 0.1*(1-D)) * (1 - 0.30*eng) * (1 - 0.10*rib) + 0.10*exp(-E/0.10))"
                           " * (1 + 0.05*N) * cflash", v)
                body = shade[..., None] * SILVER + (v["eng"] * np.float32(0.10))[..., None] * GOLD
                body = body * (1 - cool[..., None] * np.float32(0.7)) + (cool[..., None] * np.float32(0.77)) * GOLD
                mat = ease_io(span(t, *T.MATERIALIZE))
                if mat > 0.001:
                    body = body * np.float32(1 - mat) + metal_body(t, v, a * k, A) * np.float32(mat * float(v["cflash"]))
                glow = heat[..., None] * (GOLD_HOT * np.float32(1.7 * fade_out))
                pa = 0.30 * smooth(span(t, T.GROW[0] + 2, T.GROW[0] + 8)) * (1 - 0.6 * mat) \
                    * (1 - 0.5 * smooth(span(t, 305, 312)))
                if pa > 0.001:
                    v["pa"] = np.float32(pa * fade_out)
                    glow += ev("where(cos(6.2832*(D*9.0 - t*0.18)) > 0, cos(6.2832*(D*9.0 - t*0.18)), 0)**18"
                               " * E * cover * pa", v)[..., None] * GOLD
                for s0, s1 in T.SWEEPS:
                    su = span(t, s0, s1)
                    if 0 < su < 1:
                        ext = A.emb_h * a * 0.8
                        ys_ = (np.arange(fs.shape[0], dtype=np.float32) / k + y0)[:, None]
                        xs_ = (np.arange(fs.shape[1], dtype=np.float32) / k + x0)[None, :]
                        glow += ev("exp(-(((xx + (yy-sy)*0.55) - p)/w)**2) * cover * 0.9", dict(
                            xx=xs_, yy=ys_, sy=np.float32(sy), p=np.float32(lerp(sx - ext, sx + ext, ease_io(su))),
                            w=np.float32(max(40 * sc, A.emb_h * a * 0.045)), cover=cs))[..., None] * WARM_WHITE
                if k < 1:
                    both = cv2.resize(np.concatenate([body, glow], 2), (ww, hh), interpolation=cv2.INTER_LINEAR)
                    body, glow = both[..., :3], both[..., 3:]
                img[y0:y1, x0:x1] = ev("reg*(1-c) + c*body + glow", dict(
                    reg=img[y0:y1, x0:x1], c=(cover * np.float32(fade_out))[..., None], body=body, glow=glow))

    # --- wordmark and tagline
    word_alpha_total = 1 - smooth(span(t, T.COLLAPSE[1] - 0.6, T.COLLAPSE[1] + 1.2))
    for L in A.letters:
        t0 = T.LETTERS[0] + (T.LETTERS[1] - T.LETTERS[0] - 0.9) * L["order"] / max(1, A.n_letters - 1)
        u = span(t, t0, t0 + 0.9)
        if u <= 0:
            continue
        al = ease_out(u) * word_alpha_total
        if al <= 0.001:
            continue
        dy = (1 - ease_out(u)) * 0.25 * (A.word_bottom - A.word_top)
        r = warp_sprite(L["mips"], L["ox"], L["oy"] + dy, G, a, W, H)
        if r is None:
            continue
        roi, m = r
        if u < 1:
            k = int((1 - u) * 14 * sc * 4) * 2 + 1
            if k > 1:
                m = cv2.GaussianBlur(m, (k, k), 0)
        over_color(img, roi, m * np.float32(al), np.float32([0.88, 0.88, 0.90]))
        if lt is not None:
            over_color(lt, roi, m * np.float32(al), INK * 1.3)
        for j, delay in enumerate((0.0, 0.18, 0.36)):
            eu = span(t, t0 + delay, t0 + delay + 1.4)
            if 0 < eu < 1:
                k = 1 + 0.9 * ease_out(eu)
                ea = (1 - eu) ** 2 * 0.35 / (1 + j)
                cxs, cys = apply_G(G, L["cx"], L["cy"])
                aa = a * k
                G2 = make_G(aa, cxs - L["cx"] * aa, cys - L["cy"] * aa)
                r2 = warp_sprite(L["mips"], L["ox"], L["oy"], G2, aa, W, H)
                if r2 is not None:
                    add_color(img, r2[0], r2[1] * np.float32(ea * word_alpha_total), GOLD)

    tu = span(t, *T.TAGLINE)
    tag_a = smooth(tu * 4) * (1 - smooth((tu - 0.8) * 5))
    if tag_a > 0.001:
        r = warp_sprite(A.tag["mips"], A.tag["ox"], A.tag["oy"], G, a, W, H)
        if r is not None:
            add_color(img, r[0], r[1] * np.float32(tag_a * 1.25), GOLD)

    # --- echo rings
    for age, amp, big in ring_list(t):
        rr = ring_radius(age, big) * sc
        al = amp * math.exp(-age / (1.5 if not big else 1.8)) * (1 - span(age, 2.8, 3.5))
        vv = int(np.clip(al * 255, 0, 255))
        if vv < 2:
            continue
        th = max(1, int(round((3 if not big else 6) * sc * 2)))
        cv2.circle(lay, (int(sx * 16), int(sy * 16)), int(rr * 16), (float(vv * GOLD8[0]), float(vv * GOLD8[1]), float(vv * GOLD8[2])),
                   th, cv2.LINE_AA, 4)
        cv2.circle(ring_q, (int(sx * 4), int(sy * 4)), int(rr / 4 * 16), float(al), max(1, int(3 * sc * 4 / 4)),
                   cv2.LINE_AA, 4)

    # --- dust + bokeh
    p_fade = smooth(span(t, 1.0, 10.0)) * (1 - smooth(span(t, T.STAR_OUT - 1.5, T.FADE_END[1])))
    if p_fade > 0.001:
        base = (A.p_base + A.p_v * t) % 1.1 - 0.05
        pos = base * np.float32([W, H])
        zl = math.log(max(s4 / A.s_hero, 1e-3))
        ctr = np.float32([W / 2, H / 2])
        pos = (pos - ctr) * (1 + zl * A.p_z[:, None] * 0.45) + ctr
        bright = (0.18 + 0.16 * np.sin(A.p_phase + t * A.p_tw)) * (0.35 + 0.65 * A.p_z)
        star_s = np.float32([sx, sy])
        if t < T.BOOM:
            g = np.clip((t - A.p_g0) / A.p_gd, 0, 1)
            g = g * g * (3 - 2 * g)
            rel = pos - star_s
            ang = A.p_spin * g
            ca, sa = np.cos(ang), np.sin(ang)
            rot = np.stack([rel[:, 0] * ca - rel[:, 1] * sa, rel[:, 0] * sa + rel[:, 1] * ca], 1)
            pos = star_s + rot * ((1 - g) ** 1.3)[:, None]
            bright = bright * (1 + 2.5 * g) * (g < 0.985)
        else:
            e = np.float32(ease_out_expo((t - T.BOOM) / 3.5))
            pos = star_s + (pos - star_s) * e
            bright = bright * (1 + 2.0 * (1 - e))
        bright = bright * p_fade
        rad = (0.7 + A.p_z * 1.6) * max(sc * 2, 0.5)
        vis = np.where((bright > 0.02) & (pos[:, 0] > -60) & (pos[:, 0] < W + 60)
                       & (pos[:, 1] > -60) & (pos[:, 1] < H + 60))[0]
        for i in vis:
            x, y = pos[i]
            if A.p_bokeh[i]:
                draw_dot(lay, x, y, (10 + 18 * A.p_z[i]) * sc * 2, min(255, bright[i] * 60), DUST8)
            else:
                draw_dot(lay, x, y, rad[i] * 0.6, min(255, bright[i] * 255), GOLD8 if A.p_gold[i] else DUST8)

    # --- sparks thrown off the growth front
    if T.GROW[0] - 0.2 < t < T.GROW[1] + 3:
        age = t - A.sp_te
        idx = np.where((age > 0) & (age < A.sp_life))[0]
        if len(idx):
            ag = age[idx]
            p = A.sp_xy[idx] + A.sp_v[idx] * ag[:, None] + np.float32([0, 18]) * (ag ** 2)[:, None]
            hom = np.c_[p, np.ones(len(p), np.float32)] @ G.T
            p = hom[:, :2] / hom[:, 2:3]
            br = (1 - ag / A.sp_life[idx]) ** 1.5
            zf = 0.6 + 0.4 * min(3.0, a / sc / A.s_hero)
            szs = np.maximum(1, A.sp_size[idx] * sc * 2 * zf)
            for (x, y), b, sz in zip(p, br, szs):
                if 0 <= x < W and 0 <= y < H:
                    draw_dot(lay, x, y, sz * 0.7, min(255, 255 * b), GOLD8)


    # --- the star, on top of everything
    R = A.star_r * a * star_scale(t) * 1.02
    glint = 1.6 * math.exp(-((t - T.GLINT) / 0.35) ** 2) + 1.2 * math.exp(-((t - T.SPARK - 0.25) / 0.4) ** 2)
    glint += 1.6 * math.exp(-((t - T.COMPLETE) / 0.45) ** 2) + 1.4 * math.exp(-((t - T.STAR_OUT) / 0.25) ** 2)
    glint += 1.0 * math.exp(-((t - T.BOOM) / 0.4) ** 2)
    draw_star(img, sx, sy, R, star_intensity(t), 0.35 + glint, A, q=q_extra)

    # --- flashes
    k = 0.45 * pulse(t, T.BOOM, 0.5) + 0.55 * pulse(t, T.COMPLETE, 0.7)
    if k > 0.002:
        q_extra += ev("exp(-sqrt((qx-sx)**2+(qy-sy)**2)/w*3.0)*k", dict(
            qx=A.qxx, qy=A.qyy, sx=np.float32(sx / 4), sy=np.float32(sy / 4), w=np.float32(A.qw),
            k=np.float32(k)))[..., None] * GOLD

    # --- bloom + god rays at quarter resolution
    small = cv2.resize(img, (A.qw, A.qh), interpolation=cv2.INTER_AREA)
    bright = np.maximum(small - 0.62, 0)
    b1 = cv2.GaussianBlur(bright, (0, 0), 3 * sc * 4)
    b2 = cv2.GaussianBlur(cv2.resize(bright, (A.qw // 2, A.qh // 2), interpolation=cv2.INTER_AREA), (0, 0), 8 * sc * 4)
    q = q_extra + b1 * 0.45 + cv2.resize(b2, (A.qw, A.qh)) * 0.55
    q += cv2.GaussianBlur(ring_q, (0, 0), 2.0 * sc * 4)[..., None] * (GOLD * np.float32(0.9))
    ray_amt = 0.55 * smooth(span(t, T.SPARK, T.SPARK + 2)) * (1 - 0.7 * smooth(span(t, 296, 304)))
    ray_amt *= 1 - smooth(span(t, T.STAR_OUT, T.STAR_OUT + 0.6))
    if ray_amt > 0.01:
        cx4, cy4 = sx / 4, sy / 4
        near = ev("exp(-((qx-cx)**2+(qy-cy)**2)/(r*r))", dict(
            qx=A.qxx, qy=A.qyy, cx=np.float32(cx4), cy=np.float32(cy4), r=np.float32(max(A.qw * 0.06, R * 2.5 / 4))))
        src = np.maximum(small - 0.5, 0) * near[..., None]
        acc = np.zeros_like(src)
        for i in range(1, 12):
            kk = 1 + 0.045 * i
            M = np.float32([[kk, 0, cx4 * (1 - kk)], [0, kk, cy4 * (1 - kk)]])
            acc += cv2.warpAffine(src, M, (A.qw, A.qh)) * (1 - i / 12)
        q += cv2.GaussianBlur(acc, (0, 0), 1.5) * (ray_amt / 6)
    img += cv2.resize(q, (W, H), interpolation=cv2.INTER_LINEAR)

    # --- light-mode blend (reveal / collapse)
    if lt is not None:
        draw_star(lt, sx, sy, A.star_r * a * 1.02, 1.0, 0.0, A, light=1.0)
        v = dict(xx=A.xx, yy=A.yy, sx=np.float32(sx), sy=np.float32(sy), r=np.float32(rev_r),
                 e=np.float32(70 * sc), w1=np.float32(55 * sc), w2=np.float32(260 * sc))
        v["d"] = ev("sqrt((xx-sx)**2+(yy-sy)**2)", v)
        v["m"] = ev("where((r-d)/e+0.5 > 1, 1, where((r-d)/e+0.5 < 0, 0, (r-d)/e+0.5))", v)
        wave = ev("(exp(-((d-r)/w1)**2)*1.2 + exp(-((d-r)/w2)**2)*0.35) * (1-m)", v)
        m3 = v["m"][..., None]
        img = img * (1 - m3) + lt * m3 + wave[..., None] * GOLD_HOT
        lay = (lay.astype(np.float32) * (1 - m3)).astype(np.uint8)  # no dust on the paper

    # --- finishing
    vk = np.float32(1.0 if lt is None else 0.25)
    hold = 1 - 0.5 * smooth(span(t, T.SILENCE[0], T.SILENCE[0] + 0.4)) * (t < T.COMPLETE)
    fade = smooth(span(t, 0.0, 3.0)) * (1 - smooth(span(t, *T.FADE_END))) * hold
    g = cv2.resize(A.grain[int(t * T.FPS) % len(A.grain)], (W, H), interpolation=cv2.INTER_LINEAR)
    img *= (A.vignette if vk == 1 else 1 - (1 - A.vignette) * vk) * np.float32(fade)
    out = ev("where(img > 0.8, 0.8 + (img-0.8)/(1 + (img-0.8)/0.2), img)*255 + g3*2.0", dict(img=img, g3=g[..., None]))
    out = cv2.convertScaleAbs(out)
    if fade < 1:
        lay = (lay.astype(np.float32) * fade).astype(np.uint8)
    out = cv2.add(out, lay)
    # cinematic 2.39:1 bars that open up for the logo lockup
    bar = int(A.bar * (1 - ease_io(span(t, T.LOCKUP[0] - 1, T.LOCKUP[1]))))
    if bar > 0:
        out[:bar] = 0
        out[H - bar:] = 0
    return out


# ----------------------------------------------------------------------------- main
def ffmpeg_exe():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--stills", type=str, default="")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=int(T.DURATION * T.FPS))
    ap.add_argument("--out", type=str, default="")
    ap.add_argument("--crf", type=int, default=17)
    ap.add_argument("--threads", type=int, default=1)
    args = ap.parse_args()
    cv2.setNumThreads(args.threads)
    ne.set_num_threads(args.threads)
    A = Assets(args.scale)

    if args.stills:
        os.makedirs(os.path.join(HERE, "out", "stills"), exist_ok=True)
        for s in args.stills.split(","):
            t = float(s)
            t0 = time.time()
            fr = render(t, A)
            p = os.path.join(HERE, "out", "stills", f"t{t:06.1f}.png")
            cv2.imwrite(p, cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
            print(p, f"{time.time() - t0:.2f}s", flush=True)
        return

    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{A.W}x{A.H}", "-r", str(T.FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "faster", "-crf", str(args.crf), "-tune", "film",
           "-maxrate", "45M", "-bufsize", "90M", "-g", str(T.FPS * 2),
           "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
           "-color_trc", "bt709", "-threads", "1", args.out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(args.start, args.end):
        fr = render(i / T.FPS, A)
        proc.stdin.write(fr.tobytes())
        if (i - args.start) % 48 == 0:
            el = time.time() - t0
            done = i - args.start + 1
            print(f"[{args.start}-{args.end}] frame {i}  {el / done:.2f}s/f  eta {(args.end - i) * el / done / 60:.1f} min", flush=True)
    proc.stdin.close()
    proc.wait()
    print("done", args.out, flush=True)


if __name__ == "__main__":
    main()
