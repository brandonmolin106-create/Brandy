"""Echoes in the Dark - v2 (6:00): faster cuts, whole worlds, a stack of effects.

  python3 render2.py --stills 5,40,90,120,160,230,250,290,341 --scale 0.25
  python3 render2.py --start 0 --end 1080 --out out2/seg/seg00.mp4
"""
import argparse
import math
import os
import subprocess
import time

import cv2
import numexpr as ne
import numpy as np

import render as R
import importlib
from render import (DUST8, GOLD, GOLD8, GOLD_HOT, INK, LOGO_GOLD, PAPER, PLATINUM, SILVER, WARM_WHITE,
                    apply_G, draw_dot, ease_io, ease_out, ease_out_expo, ev, lerp, make_G, pulse, smooth, span,
                    warp_region, warp_sprite)
from scenery import Scenery

T = importlib.import_module(os.environ.get("TRAILER_TIMELINE", "timeline2"))

HERE = os.path.dirname(os.path.abspath(__file__))
V4_PLACES = ("desert", "badlands", "canyon", "city", "skyline", "icecave", "ruins", "falls", "dolomites",
             "snowfield", "deadwood", "starsea", "pillars")
SCENIC = ("ocean", "mountain", "storm", "forest", "aurora", "volcano") + V4_PLACES
PLATE_OF = {"void": "space", "ocean": "ocean", "mountain": "mount", "storm": "storm", "forest": "forest",
            "aurora": "aurora", "volcano": "volcano", **{p: p for p in V4_PLACES}}
WATER = ("ocean", "skyline", "starsea")                       # the logo reflects in these
STRIKE_ENVS = ("storm", "volcano", "city", "skyline", "badlands", "desert", "canyon")
RAIN = ("storm", "city", "badlands")
SNOW_ENVS = ("aurora", "snowfield", "icecave", "falls", "dolomites")
FIREFLY_ENVS = ("forest", "ruins", "deadwood")
DUST_ENVS = ("desert", "canyon")


def plate_expo(env, t, sub):
    if sub:
        return 0.8
    if env == "void":
        e = 0.22 + 0.2 * smooth(span(t, T.SPARK - 1, T.SPARK + 3))
        if t > T.COLLAPSE[1]:
            e *= 0.8
        return e * smooth(span(t, 6.5, 9.0)) if t < 10 else e
    return {"ocean": 0.85, "mountain": 0.6, "storm": 0.72, "forest": 0.62, "aurora": 0.8, "volcano": 0.8,
            "canyon": 0.9, "city": 0.85, "deadwood": 0.75, "pillars": 0.9}.get(env, 0.8)
EMB_BORDER = (-4000.0, 1.5, 0.0, 0.0)


# ----------------------------------------------------------------------------- story clock
def growth2(t):
    if t < T.GROW[0]:
        return -0.05
    u = span(t, *T.GROW)
    return lerp(-0.004, 1.04, 0.8 * u ** 0.9 + 0.2 * (0.5 - 0.5 * math.cos(math.pi * u)))


_FS = np.linspace(T.GROW[0], T.GROW[1], 6000)
_FV = np.array([growth2(x) for x in _FS])


def growth_time2(d):
    return np.interp(d, _FV, _FS).astype(np.float32)


def star_int2(t, sub):
    if sub:
        return 1.3
    if t >= T.SLAM:
        return 1.0 + 1.2 * pulse(t, T.SLAM, 0.3)
    if t < T.SPARK:
        return 0.0
    ign = ease_out_expo(span(t, T.SPARK, T.SPARK + 0.6))
    beat = sum(pulse(t, r, 0.35) for r in T.RINGS if r <= t) * 0.35
    beat += sum(pulse(t, r, 0.5) for r in T.GROW_RINGS if r <= t) * 0.25
    out = 1 - smooth(span(t, T.STAR_OUT, T.STAR_OUT + 0.35))
    flash = 1.8 * pulse(t, T.SPARK, 0.25)
    hold = 1 - 0.55 * smooth(span(t, T.SILENCE[0], T.SILENCE[0] + 0.3)) * (t < T.COMPLETE)
    return (ign * (1.0 + beat) + flash) * out * hold


def star_scale2(t, sub):
    if sub or t >= T.SLAM:
        return 1.0
    if t < T.SPARK:
        return 0.0
    u = span(t, T.SPARK, T.SPARK + 1.1)
    over = 1 + 0.35 * math.sin(u * math.pi) * (1 - u)
    return ease_out(u) * over * (1 + 0.04 * math.sin(t * 2.1))


RINGS_ALL = ([(r, 0, 1.0) for r in T.RINGS] + [(r, 0, 0.8) for r in T.GROW_RINGS]
             + [(r, 1, 1.3) for r in T.LATE_RINGS])


def ring_list2(t):
    out = []
    for r0, big, amp0 in RINGS_ALL:
        for dt, amp in ((0, 1.0), (0.22, 0.45), (0.44, 0.2)):
            age = t - r0 - dt
            if 0 <= age < 3.5:
                out.append((age, amp * amp0, big))
    return out


def ring_radius(age, big):
    return (1600 if big else 1150) * (1 - math.exp(-age * 1.1)) + 420 * age


def emblem_vis(t, sub):
    if sub:
        return 1.0
    if t >= T.SLAM:
        return 1.0
    return 1 - smooth(span(t, T.COLLAPSE[1] + 0.3, T.STAR_OUT - 1.5))


def words_alpha(t):
    if t >= T.SLAM:
        return 1.0
    return 1 - smooth(span(t, T.COLLAPSE[1] - 0.6, T.COLLAPSE[1] + 1.2))


def strike_list(t, shot):
    if shot.env not in STRIKE_ENVS:
        return []
    out = []
    for j, (ts, kind) in enumerate(T.STRIKES):
        age = t - ts
        if 0 <= age < 0.5:
            out.append((j, age, kind))
    return out


# ----------------------------------------------------------------------------- assets
class Assets2(R.Assets):
    def __init__(self, sc):
        super().__init__(sc)
        self.sp_te = growth_time2(self.sp_d)
        cen = np.array(self.meta["front_centroid"], np.float64)
        k = np.exp(-0.5 * (np.arange(-12, 13) / 5.0) ** 2)
        k /= k.sum()
        pad = np.pad(cen, ((12, 12), (0, 0)), mode="edge")
        self.cen = np.stack([np.convolve(pad[:, i], k, "valid") for i in range(2)], 1)
        self.tips = np.array([self.axis, 260.0])
        self.s_lock = 980.0 / self.emb_h
        C = self.emb_c
        lock_total = 980 + self.emb_h * (65 + 41) / 340.0 * self.s_lock
        lock_center_y = (T.H - lock_total) / 2 + 490
        self.F_lock = np.array([C[0], C[1] + (T.H / 2 - lock_center_y) / self.s_lock])
        self.scn = Scenery(self.W, self.H, sc)
        rng = np.random.default_rng(31)
        n = 720
        idx = rng.choice(len(self.sp_xy), n, replace=False)
        self.sh_p = self.sp_xy[idx]
        d = self.sh_p - self.emb_c[None].astype(np.float32)
        d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        ang = rng.normal(0, 0.45, n)
        ca, sa = np.cos(ang), np.sin(ang)
        self.sh_dir = np.stack([d[:, 0] * ca - d[:, 1] * sa, d[:, 0] * sa + d[:, 1] * ca], 1).astype(np.float32)
        self.sh_v = rng.uniform(300, 2600, n).astype(np.float32)
        self.sh_size = rng.uniform(5, 30, n).astype(np.float32)
        self.sh_rot0 = rng.uniform(0, 6.283, n)
        self.sh_w = rng.uniform(-9, 9, n)
        self.sh_life = rng.uniform(1.8, 4.2, n)
        self.sh_ph = rng.uniform(0, 6.283, n)
        self.sh_gw = rng.uniform(6, 20, n)
        self.sh_shape = rng.uniform(0.35, 1.0, (n, 3))
        self.arc_idx = rng.choice(len(self.sp_xy), 1200, replace=False)
        self._picks = {}
        self._build_cards()
        self._load_plates()

    def _load_plates(self):
        import json
        pdir = os.path.join(HERE, "assets", "cache", "plates")
        meta = json.load(open(os.path.join(pdir, "meta.json")))
        self.plates = {}
        for name in [n for n in ("space", "ocean", "mount", "storm", "forest", "aurora", "volcano") + V4_PLACES
                     if os.path.exists(os.path.join(pdir, n + ".npz"))]:
            d = np.load(os.path.join(pdir, name + ".npz"))
            rgb = d["rgb"]
            mask = d["mask"] if "mask" in d.files else None
            if self.sc != 1.0:
                size = (int(rgb.shape[1] * self.sc), int(rgb.shape[0] * self.sc))
                rgb = cv2.resize(rgb, size, interpolation=cv2.INTER_AREA)
                if mask is not None:
                    mask = cv2.resize(mask, size, interpolation=cv2.INTER_AREA)
            m = dict(meta.get(name, {}))
            for k in list(m):
                m[k] = m[k] * self.sc
            self.plates[name] = dict(rgb=np.ascontiguousarray(rgb), mask=mask, meta=m)

    def _build_cards(self):
        from PIL import Image, ImageDraw, ImageFont
        W, H, sc = self.W, self.H, self.sc
        texts = [c[2] for c in T.CARDS] + [c[1] for c in T.WORD_CARDS]
        self.cards = {}
        rng = np.random.default_rng(8)
        for text in texts:
            cap = 250 * sc
            size = int(cap / 0.7)
            font = ImageFont.truetype(os.path.join(HERE, "assets", "Jost-500.ttf"), size)
            for _ in range(3):
                track = 0.24 * size
                adv = [font.getlength(ch) for ch in text]
                width = sum(adv) + track * (len(text) - 1)
                if width <= 0.74 * W:
                    break
                size = int(size * 0.74 * W / width)
                font = ImageFont.truetype(os.path.join(HERE, "assets", "Jost-500.ttf"), size)
            track = 0.24 * size
            adv = [font.getlength(ch) for ch in text]
            width = sum(adv) + track * (len(text) - 1)
            bb = font.getbbox("E")
            pad = int(size * 0.35)
            im = Image.new("L", (int(width + 2 * pad), int(bb[3] - bb[1] + 2 * pad)), 0)
            d = ImageDraw.Draw(im)
            x = pad
            for ch, a in zip(text, adv):
                d.text((x, pad - bb[1]), ch, font=font, fill=255)
                x += a + track
            al = np.asarray(im, np.float32) / 255.0
            h, w = al.shape
            yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
            stops = [(0.0, (0.96, 0.96, 0.99)), (0.40, (0.86, 0.84, 0.80)), (0.50, (0.80, 0.66, 0.40)),
                     (0.56, (0.98, 0.90, 0.70)), (0.80, (0.55, 0.52, 0.50)), (1.0, (0.26, 0.26, 0.30))]
            fill = np.zeros((h, w, 3), np.float32)
            for c in range(3):
                fill[..., c] = np.interp(yy, [s[0] for s in stops], [s[1][c] for s in stops])
            brushed = cv2.resize(rng.normal(0, 1, (max(2, h // 3), max(2, w // 60))).astype(np.float32), (w, h))
            fill *= (1 + 0.06 * brushed)[..., None]
            self.cards[text] = (al, fill)

    def _build_camera_path(self):
        pass

    def _build_particles(self):
        super()._build_particles()
        rng = np.random.default_rng(12)
        n = len(self.p_base)
        self.p_g0 = rng.uniform(T.GATHER[0], T.GATHER[1] - 4.0, n).astype(np.float32)
        self.p_gd = rng.uniform(2.5, 4.5, n).astype(np.float32)

    def pick(self, shot):
        if shot.seed in self._picks:
            return self._picks[shot.seed]
        f0 = growth2(shot.t0 + 0.2)
        rng = np.random.default_rng(shot.seed)
        if f0 > 1.0:
            cand = np.arange(len(self.sp_xy))
        else:
            cand = np.where((self.sp_d > f0 - 0.12) & (self.sp_d < f0 - 0.01))[0]
        if len(cand) == 0:
            p = self.front_centroid(max(f0, 0.0), -1)
        else:
            p = self.sp_xy[cand[rng.integers(len(cand))]].astype(np.float64)
        self._picks[shot.seed] = p
        return p


# ----------------------------------------------------------------------------- camera
def resolve(c, t, shot, A):
    f = c["f"]
    base = A.s_hero
    if isinstance(f, tuple):
        F = np.array(f, np.float64)
    elif f == "C":
        F = A.emb_c
    elif f == "S":
        F = A.star
    elif f == "TIP":
        F = A.tips
    elif f == "AXF":
        F = np.array([T.AXIS, A.front_centroid(max(growth2(t), 0.0) + 0.02, -1)[1]])
    elif f == "FRONT":
        F = A.front_centroid(max(growth2(t), 0.0) + 0.015, -1)
    elif f == "PICK":
        F = A.pick(shot)
    elif f == "LOCK":
        F = A.F_lock
        base = A.s_lock
    else:
        raise ValueError(f)
    return np.array(F, np.float64), c["z"] * base


def camera2(t, shot, A):
    u = span(t, shot.t0, shot.t1)
    e = {"io": ease_io, "lin": lambda x: x}.get(shot.ease, ease_io)(u)
    if shot.ease == "rush":
        e = ease_io(span(t, shot.t0, shot.t0 + 3.4))
    elif shot.ease == "lock":
        e = ease_io(span(t, *T.LOCKUP))
    F0, s0 = resolve(shot.c0, t, shot, A)
    F1, s1 = resolve(shot.c1, t, shot, A)
    F = F0 + (F1 - F0) * e
    s = math.exp(lerp(math.log(s0), math.log(s1), e))
    if shot.ease == "lock":
        s *= 1 + 0.04 * span(t, T.LOCKUP[1], shot.t1)
    s *= 1 + shot.punch * math.exp(-(t - shot.t0) / 0.3)
    g = lambda k: lerp(shot.c0[k], shot.c1[k], e)
    roll, yaw, ox, oy = g("roll"), g("yaw"), g("ox"), g("oy")
    kick = 26 * pulse(t, T.BOOM, 0.45) + 38 * pulse(t, T.COMPLETE, 0.5) + 34 * pulse(t, T.SLAM, 0.45)
    kick += sum(22 * s * math.exp(-(t - ti) / 0.25) for ti, s in T.IMPACTS if 0 <= t - ti < 1.2 and s < 1.0)
    kick += 10 * pulse(t, shot.t0, 0.2) * (shot.punch > 0)
    for j, age, kind in strike_list(t, shot):
        kick += 14 * math.exp(-age / 0.2) * (kind != "sky")
    hh = 3.2 if getattr(T, "V7", False) else 1.0
    dx = (math.sin(t * 0.37) * 5 + math.sin(t * 0.91 + 1) * 2 + math.sin(t * 2.3) * 0.8) * hh + kick * math.sin(t * 71.0)
    dy = (math.cos(t * 0.29) * 4 + math.sin(t * 0.73 + 2) * 1.5 + math.cos(t * 1.9) * 0.7) * hh + kick * math.cos(t * 57.0)
    roll += kick * 0.0005 * math.sin(t * 53.0)
    return F, s, roll, yaw, ox + dx, oy + dy, dx, dy


def build_G(A, F, s, roll, yaw, ox, oy):
    W, H, sc = A.W, A.H, A.sc
    a = s * sc
    cx, cy = W / 2 + ox * sc, H / 2 + oy * sc
    G0 = make_G(a, cx - F[0] * a, cy - F[1] * a, yaw, A.emb_c[0], A.emb_c[1])
    if abs(roll) > 1e-6:
        c, sn = math.cos(roll), math.sin(roll)
        Rm = np.array([[c, -sn, W / 2 - c * W / 2 + sn * H / 2], [sn, c, H / 2 - sn * W / 2 - c * H / 2], [0, 0, 1]])
        G0 = Rm @ G0
    return G0, a


# ----------------------------------------------------------------------------- emblem
def metal_body2(t, v, a, A, phi):
    h = ev("1 - (1 - where(E*2.2 > 1, 1, E*2.2))**2 - 0.06*eng + 0.004*N", v).astype(np.float32)
    kz = np.float32(0.125 * 40.0 * a)
    gx = cv2.Sobel(h, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(h, cv2.CV_32F, 0, 1, ksize=3)
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


def draw_emblem(img, q_extra, lt, t, A, G, a, sx, sy, f, mat, vis, boost, sub):
    W, H, sc = A.W, A.H, A.sc
    if not sub and t < T.GROW[0] + 3:
        Gq = np.diag([0.25, 0.25, 1.0]) @ G
        r = warp_sprite(A.emb, 0, 0, Gq, a / 4, A.qw, A.qh, border=EMB_BORDER)
        if r is not None:
            (qy0, qy1, qx0, qx1), fq = r
            v = dict(S=fq[..., 0], a=np.float32(a / 4), xx=A.qxx[qy0:qy1, qx0:qx1], yy=A.qyy[qy0:qy1, qx0:qx1],
                     sx=np.float32(sx / 4), sy=np.float32(sy / 4))
            Afq = ev("where(S*a+0.5 < 0, 0, where(S*a+0.5 > 1, 1, S*a+0.5))", v)
            rd = ev("sqrt((xx-sx)**2+(yy-sy)**2)", v)
            ghost = np.zeros_like(rd)
            for age, amp, big in ring_list2(t):
                ghost += ev("exp(-((rd-rr)/w)**2)*k", dict(
                    rd=rd, rr=np.float32(ring_radius(age, big) * sc / 4), w=np.float32(130 * sc / 4),
                    k=np.float32(amp * math.exp(-age / 1.8))))
            gk = np.float32(0.22 * (1 - smooth(span(t, T.GROW[0], T.GROW[0] + 3))))
            base = np.float32(0.012 * smooth(span(t, 30, 70)))
            q_extra[qy0:qy1, qx0:qx1] += ev("Af*(ghost*gk + base)", dict(Af=Afq, ghost=ghost, gk=gk, base=base))[..., None] * GOLD
    if vis <= 0.001 or (f < 0 and lt is None):
        return
    r = warp_sprite(A.emb, 0, 0, G, a, W, H, border=EMB_BORDER)
    if r is None:
        return
    roi, fld = r
    y0, y1, x0, x1 = roi
    fv = dict(S=fld[..., 0], D=fld[..., 1], E=fld[..., 2], N=fld[..., 3], a=np.float32(a), f=np.float32(f))
    fv["Af"] = ev("where(S*a+0.5 < 0, 0, where(S*a+0.5 > 1, 1, S*a+0.5))", fv)
    if lt is not None:
        R.over_color(lt, roi, fv["Af"], INK)
    if f < 0:
        return
    fv["Dw"] = ev("D + 0.0035*N", fv)
    fv["beh"] = ev("where(Dw > f, 0, where((f-Dw)/0.03 > 1, 1, (f-Dw)/0.03))", fv)
    fv["cv"] = ev("(E - (1 - beh))/0.08 + 1", fv)
    cover = ev("Af * where(Dw < f + 0.001, 1, 0) * where(cv > 1, 1, where(cv < 0, 0, cv))", fv)
    k = 0.5 if a > 1.1 else 1.0
    hh, ww = fld.shape[:2]
    if k < 1:
        fs = warp_region(A.emb, G, a, x0, y0, int(math.ceil(ww * k)), int(math.ceil(hh * k)), k, border=EMB_BORDER)
        cs = None
    else:
        fs, cs = fld, cover
    v = dict(S=fs[..., 0], D=fs[..., 1], E=fs[..., 2], N=fs[..., 3], a=np.float32(a * k), f=np.float32(f),
             t=np.float32(t))
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
    v["rib"] = ev("(0.5+0.5*cos(D*603.19))**6", v)
    cf = 1 + 2.0 * pulse(t, T.COMPLETE, 0.4) + 1.6 * pulse(t, T.SLAM, 0.4) + boost
    v["cflash"] = np.float32(cf)
    shade = ev("((0.9 + 0.1*(1-D)) * (1 - 0.30*eng) * (1 - 0.10*rib) + 0.10*exp(-E/0.10))"
               " * (1 + 0.05*N) * cflash", v)
    body = shade[..., None] * SILVER + (v["eng"] * np.float32(0.10))[..., None] * GOLD
    body = body * (1 - cool[..., None] * np.float32(0.7)) + (cool[..., None] * np.float32(0.77)) * GOLD
    if mat > 0.001:
        phi = 2.3 + 0.35 * math.sin(t * 0.21) + 0.6 * math.sin(t * 0.13)
        body = body * np.float32(1 - mat) + metal_body2(t, v, a * k, A, phi) * np.float32(mat * cf)
    glow = heat[..., None] * (GOLD_HOT * np.float32(1.7 * vis))
    pa = 0.30 * smooth(span(t, T.GROW[0] + 2, T.GROW[0] + 8)) * (1 - 0.6 * mat)
    flow = getattr(T, "V7", False) and (t >= T.GROW[0] + 2 or sub)
    if flow:
        pa = max(pa, 0.16)
    if pa > 0.001 and (f < 1.2 or flow):
        v["pa"] = np.float32(pa * vis)
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
    for ts, sv in getattr(T, "SURGES", ()):
        age = t - ts
        if 0 < age < 1.4:
            v["u"] = np.float32(age / 1.1 * 1.2 - 0.05)
            v["sk"] = np.float32(sv * vis * (1 - span(age, 1.0, 1.4)))
            v["cs"] = cs
            glow += ev("(exp(-((D-u)/0.022)**2)*3.4 + exp(-((D-u+0.07)/0.06)**2)*0.8) * (0.35+E) * cs * sk",
                       v)[..., None] * GOLD_HOT
    if k < 1:
        both = cv2.resize(np.concatenate([body, glow], 2), (ww, hh), interpolation=cv2.INTER_LINEAR)
        body, glow = both[..., :3], both[..., 3:]
    img[y0:y1, x0:x1] = ev("reg*(1-c) + c*body + glow", dict(
        reg=img[y0:y1, x0:x1], c=(cover * np.float32(vis))[..., None], body=body, glow=glow))


def draw_words(img, lt, t, A, G, a):
    W, H, sc = A.W, A.H, A.sc
    wa = words_alpha(t)
    for L in A.letters:
        if t >= T.SLAM:
            u = 1.0
            t0 = T.SLAM
        else:
            t0 = T.LETTERS[0] + (T.LETTERS[1] - T.LETTERS[0] - 0.9) * L["order"] / max(1, A.n_letters - 1)
            u = span(t, t0, t0 + 0.9)
        if u <= 0:
            continue
        al = ease_out(u) * wa
        if al <= 0.001:
            continue
        dy = (1 - ease_out(u)) * 0.25 * (A.word_bottom - A.word_top)
        r = warp_sprite(L["mips"], L["ox"], L["oy"] + dy, G, a, W, H)
        if r is None:
            continue
        roi, m = r
        if u < 1:
            kk = int((1 - u) * 14 * sc * 4) * 2 + 1
            if kk > 1:
                m = cv2.GaussianBlur(m, (kk, kk), 0)
        R.over_color(img, roi, m * np.float32(al), np.float32([0.88, 0.88, 0.90]))
        if lt is not None:
            R.over_color(lt, roi, m * np.float32(al), INK * 1.3)
        if t < T.SLAM:
            for j, delay in enumerate((0.0, 0.18, 0.36)):
                eu = span(t, t0 + delay, t0 + delay + 1.4)
                if 0 < eu < 1:
                    kz = 1 + 0.9 * ease_out(eu)
                    ea = (1 - eu) ** 2 * 0.35 / (1 + j)
                    cxs, cys = apply_G(G, L["cx"], L["cy"])
                    aa = a * kz
                    G2 = make_G(aa, cxs - L["cx"] * aa, cys - L["cy"] * aa)
                    r2 = warp_sprite(L["mips"], L["ox"], L["oy"], G2, aa, W, H)
                    if r2 is not None:
                        R.add_color(img, r2[0], r2[1] * np.float32(ea * wa), GOLD)
    tu = span(t, *T.TAGLINE)
    tag_a = smooth(tu * 4) * (1 - smooth((tu - 0.8) * 5))
    if t >= T.SLAM:
        tag_a = smooth(span(t, T.SLAM + 3.0, T.SLAM + 4.5))
    if tag_a > 0.001:
        r = warp_sprite(A.tag["mips"], A.tag["ox"], A.tag["oy"], G, a, W, H)
        if r is not None:
            R.add_color(img, r[0], r[1] * np.float32(tag_a * 1.25), GOLD)


def draw_shards(lay, gq, t, A, G, sc, t_event):
    age = t - t_event
    if age < 0 or age > 4.5:
        return
    k = 1.4
    for i in range(len(A.sh_p)):
        if age > A.sh_life[i]:
            continue
        p = apply_G(G, float(A.sh_p[i, 0]), float(A.sh_p[i, 1]))
        v = A.sh_v[i] * sc
        dist = v / k * (1 - math.exp(-k * age))
        cx = p[0] + A.sh_dir[i, 0] * dist
        cy = p[1] + A.sh_dir[i, 1] * dist + 180 * sc * age * age
        if not (-50 < cx < A.W + 50 and -50 < cy < A.H + 50):
            continue
        fade = (1 - age / A.sh_life[i]) ** 1.2
        rot = A.sh_rot0[i] + A.sh_w[i] * age
        sz = A.sh_size[i] * sc * 2
        pts = np.array([[cx + sz * A.sh_shape[i, j] * math.cos(rot + j * 2.094),
                         cy + sz * A.sh_shape[i, j] * math.sin(rot + j * 2.094)] for j in range(3)])
        glint = (0.5 + 0.5 * math.sin(age * A.sh_gw[i] + A.sh_ph[i])) ** 8
        c = (np.array([0.55, 0.56, 0.6]) * 0.6 + GOLD_HOT * glint * 1.4) * 255 * fade
        c = np.minimum(c, 255)
        cv2.fillPoly(lay, [(pts * 16).astype(np.int32)], (float(c[0]), float(c[1]), float(c[2])), cv2.LINE_AA, 4)
        vnow = v * math.exp(-k * age)
        tail = (cx - A.sh_dir[i, 0] * vnow * 0.03, cy - A.sh_dir[i, 1] * vnow * 0.03)
        cv2.line(lay, (int(cx * 16), int(cy * 16)), (int(tail[0] * 16), int(tail[1] * 16)),
                 (float(c[0] * 0.5), float(c[1] * 0.5), float(c[2] * 0.5)), max(1, int(sz * 0.3)), cv2.LINE_AA, 4)
        if glint > 0.5:
            cv2.circle(gq, (int(cx / 4 * 16), int(cy / 4 * 16)), int(3 * 16),
                       tuple(float(x) for x in GOLD_HOT * 0.5 * glint * fade), -1, cv2.LINE_AA, 4)


def draw_card(img, q_extra, t, shot, A):
    """Kinetic title card: slams in oversized, settles, drifts; chrome-gold fill with a
    light sweep; glow in the quarter-res light layer."""
    W, H, sc = A.W, A.H, A.sc
    al, fill = A.cards[shot.card]
    u = t - shot.t0
    dur = shot.t1 - shot.t0
    k = 1 + 0.16 * math.exp(-u / 0.08) + 0.035 * u / max(dur, 0.1)
    fade = 1 - smooth(span(t, shot.t1 - 0.1, shot.t1))
    h, w = al.shape
    M = np.float32([[k, 0, W / 2 - k * w / 2], [0, k, H / 2 - k * h / 2]])
    x0 = max(0, int(W / 2 - k * w / 2) - 2)
    x1 = min(W, int(W / 2 + k * w / 2) + 2)
    y0 = max(0, int(H / 2 - k * h / 2) - 2)
    y1 = min(H, int(H / 2 + k * h / 2) + 2)
    M[0, 2] -= x0
    M[1, 2] -= y0
    a2 = cv2.warpAffine(al, M, (x1 - x0, y1 - y0)) * np.float32(fade)
    f2 = cv2.warpAffine(fill, M, (x1 - x0, y1 - y0))
    su = span(u, 0.05, 0.9)
    if 0 < su < 1:
        xs = np.arange(x0, x1, dtype=np.float32)[None, :]
        ys = np.arange(y0, y1, dtype=np.float32)[:, None]
        p = lerp(x0 - 0.2 * W, x1 + 0.2 * W, ease_io(su))
        band = np.exp(-(((xs + (ys - H / 2) * 0.6) - p) / (70 * sc * 2)) ** 2)
        f2 = f2 + band[..., None] * np.float32([1.2, 1.1, 0.9])
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a2[..., None]) + f2 * a2[..., None] * np.float32(1 + 1.2 * math.exp(-u / 0.12))
    qa = cv2.resize(a2, (max(1, (x1 - x0) // 4), max(1, (y1 - y0) // 4)), interpolation=cv2.INTER_AREA)
    qa = cv2.GaussianBlur(qa, (0, 0), 6 * sc * 4)
    qy0, qx0 = y0 // 4, x0 // 4
    hq, wq = qa.shape
    hq, wq = min(hq, A.qh - qy0), min(wq, A.qw - qx0)
    q_extra[qy0:qy0 + hq, qx0:qx0 + wq] += qa[:hq, :wq, None] * GOLD * np.float32(0.35 + 1.2 * math.exp(-u / 0.15))


def streak_burst(gq, cx, cy, age, s, seed, sc):
    """Radial light streaks exploding out of an impact (quarter-res glow layer)."""
    rng = np.random.default_rng(seed)
    n = int(40 + 50 * min(1.5, s))
    fade = (1 - age / 0.6) ** 2
    for _ in range(n):
        ang = rng.uniform(0, 2 * math.pi)
        spd = rng.uniform(900, 3200) * sc * s
        r0 = (40 * sc + spd * age * 0.6) / 4
        L = rng.uniform(150, 700) * sc * s * fade / 4
        c, sn = math.cos(ang), math.sin(ang)
        p0 = (cx / 4 + c * r0, cy / 4 + sn * r0)
        p1 = (cx / 4 + c * (r0 + L), cy / 4 + sn * (r0 + L))
        k = rng.uniform(0.3, 1.0) * fade * 0.9 * min(1.5, s)
        cv2.line(gq, (int(p0[0] * 16), int(p0[1] * 16)), (int(p1[0] * 16), int(p1[1] * 16)),
                 (float(k * 1.0), float(k * 0.85), float(k * 0.6)), 1, cv2.LINE_AA, 4)


def zoom_blur(img, cx, cy, amt, A):
    """Radial zoom-blur punch, computed at quarter res and blended in."""
    small = cv2.resize(img, (A.qw, A.qh), interpolation=cv2.INTER_AREA)
    acc = np.zeros_like(small)
    wsum = 0.0
    for i in range(12):
        kk = 1 + 0.022 * i * amt
        w = 1 - i / 13
        M = np.float32([[kk, 0, cx / 4 * (1 - kk)], [0, kk, cy / 4 * (1 - kk)]])
        acc += cv2.warpAffine(small, M, (A.qw, A.qh), borderMode=cv2.BORDER_REFLECT) * np.float32(w)
        wsum += w
    up = cv2.resize(acc / np.float32(wsum), (A.W, A.H), interpolation=cv2.INTER_LINEAR)
    bm = np.float32(min(0.8, amt * 0.85))
    return img * (1 - bm) + up * bm


def glitch_slices(out, seed, amt, sc):
    """Digital tear: random horizontal bands shifted with an RGB split."""
    rng = np.random.default_rng(seed)
    H, W = out.shape[:2]
    for _ in range(int(5 + 12 * amt)):
        h = int(rng.integers(6, 90) * sc * 2)
        y0 = int(rng.integers(0, max(1, H - h)))
        dx = int(rng.integers(-240, 240) * amt * sc)
        band = out[y0:y0 + h].copy()
        for c, f in ((0, 1.0), (1, 0.45), (2, -0.35)):
            out[y0:y0 + h, :, c] = np.roll(band[..., c], int(dx * f), axis=1)


AUR_G = np.array([0.18, 1.0, 0.45], np.float32)
AUR_V = np.array([0.7, 0.2, 1.0], np.float32)


def aurora_curtain(t, A, pan, hy, u):
    """Moving aurora curtain above the ridge: folded ribbons with rays, green base, violet tops."""
    qx = A.qxx / A.qw + np.float32(pan * 0.0002)
    qy = A.qyy / A.qh
    y0 = np.float32((hy if hy is not None else 0.45 * A.H) / A.H - 0.05)
    v = dict(qx=qx, qy=qy, t=np.float32(t), y0=y0)
    v["fold"] = ev("0.12*sin(qx*5.1 + t*0.23) + 0.05*sin(qx*13.0 - t*0.41 + 1.7)", v)
    v["ray"] = ev("(0.55 + 0.45*sin(qx*170.0 + fold*40.0 + t*0.9))*(0.6 + 0.4*sin(qx*47.0 - t*0.6))", v)
    v["band"] = ev("exp(-((qy - (y0 - 0.2 + fold))/0.11)**2)", v)
    v["body"] = ev("band*ray*(0.65 + 0.35*sin(t*0.7 + qx*3.0))", v)
    v["top"] = ev("exp(-((qy - (y0 - 0.38 + fold*1.2))/0.09)**2)*ray*0.45", v)
    q = v["body"][..., None] * AUR_G + v["top"][..., None] * AUR_V
    q *= np.float32(0.16)
    return cv2.resize(q, (A.W, A.H), interpolation=cv2.INTER_LINEAR)


_BR = np.random.default_rng(4242)
NB = 900
BOMBS = dict(t0=np.sort(_BR.uniform(0, 500, NB)).astype(np.float32), vent=_BR.integers(0, 2, NB),
             vx=_BR.normal(0, 0.16, NB).astype(np.float32), vy=-_BR.uniform(0.45, 1.05, NB).astype(np.float32),
             life=_BR.uniform(1.4, 2.8, NB).astype(np.float32), sz=_BR.uniform(0.6, 2.2, NB).astype(np.float32))
VENTS = np.float32([[0.45, 0.778], [0.546, 0.763]])      # crater vents (plate fractions)
_SR = np.random.default_rng(99)
SNOW = dict(x=_SR.uniform(0, 1, 700).astype(np.float32), y=_SR.uniform(0, 1, 700).astype(np.float32),
            v=_SR.uniform(0.03, 0.12, 700).astype(np.float32), z=_SR.uniform(0, 1, 700).astype(np.float32),
            ph=_SR.uniform(0, 6.3, 700).astype(np.float32))


def draw_lava_bombs(lay, gq, t, Mp, pw, ph, H, sc):
    """Ballistic lava bombs from the two vents, drawn as motion-blurred hot streaks."""
    B = BOMBS
    age = t - B["t0"]
    idx = np.where((age > 0) & (age < B["life"]))[0]
    g = 0.55
    for i in idx:
        a = float(age[i])
        v = VENTS[B["vent"][i]]
        bx, by = v[0] * pw * Mp[0, 0] + Mp[0, 2], v[1] * ph * Mp[1, 1] + Mp[1, 2]
        pos = lambda s: (bx + B["vx"][i] * H * s, by + B["vy"][i] * H * s + 0.5 * g * H * s * s)
        x1, y1 = pos(a)
        x0, y0 = pos(max(0.0, a - 0.05))
        heat = (1 - a / B["life"][i]) ** 1.3
        heat = float(heat)
        c = (255 * heat, 150 * heat ** 1.6 + 30 * heat, 40 * heat ** 3)
        w = max(1, int(B["sz"][i] * sc * 2))
        cv2.line(lay, (int(x0 * 16), int(y0 * 16)), (int(x1 * 16), int(y1 * 16)), c, w, cv2.LINE_AA, 4)
        if B["sz"][i] > 1.2:
            cv2.circle(gq, (int(x1 / 4 * 16), int(y1 / 4 * 16)), int(1.5 * 16),
                       (0.12 * heat, 0.05 * heat, 0.01 * heat), -1, cv2.LINE_AA, 4)


def draw_snow(lay, t, W, H, sc):
    S = SNOW
    y = (S["y"] + t * S["v"]) % 1.05 - 0.025
    x = (S["x"] + 0.02 * np.sin(t * 0.8 + S["ph"]) + t * 0.015 * (0.5 + S["z"])) % 1.0
    for i in range(len(y)):
        b = float(0.25 + 0.6 * S["z"][i]) * 255
        draw_dot(lay, x[i] * W, y[i] * H, (0.6 + 2.2 * S["z"][i] ** 2) * sc * 2, b * 0.55, DUST8)


ANA_TINT = np.array([0.35, 0.6, 1.0], np.float32)
_FR = np.random.default_rng(31)
_F0 = cv2.resize(_FR.random((12, 48)).astype(np.float32), (1024, 256), interpolation=cv2.INTER_CUBIC)
_F1 = cv2.resize(_FR.random((24, 96)).astype(np.float32), (1024, 256), interpolation=cv2.INTER_CUBIC)
FOG_COL = {"desert": (0.55, 0.45, 0.38), "badlands": (0.5, 0.48, 0.5), "canyon": (0.5, 0.36, 0.3),
           "city": (0.45, 0.5, 0.6), "skyline": (0.4, 0.45, 0.6)}


def fog_layer(t, A, hy, env):
    """Two octaves of drifting mist banked around the horizon (quarter res)."""
    o0, o1 = int(t * 9) % 1024, int(t * 17) % 1024
    n = np.roll(_F0, -o0, 1) * 0.65 + np.roll(_F1, -o1, 1) * 0.35
    n = cv2.resize(n[:, :512], (A.qw, A.qh), interpolation=cv2.INTER_LINEAR)
    yc = (hy if hy is not None else 0.7 * A.H) / A.H
    prof = np.exp(-((np.arange(A.qh, dtype=np.float32) / A.qh - yc - 0.04) / 0.16) ** 2)[:, None]
    d = np.clip(n - 0.35, 0, 1) * prof * np.float32(0.16)
    return d[..., None] * np.array(FOG_COL.get(env, (0.42, 0.48, 0.58)), np.float32)


_MR = np.random.default_rng(606)
NM = 400
METEORS = dict(t0=np.sort(_MR.uniform(0, 480, NM)).astype(np.float32), x=_MR.uniform(0.05, 0.95, NM),
               y=_MR.uniform(0.03, 0.3, NM), ang=_MR.uniform(0.35, 0.75, NM) * np.where(_MR.random(NM) < 0.5, 1, -1),
               ln=_MR.uniform(0.08, 0.2, NM), dur=_MR.uniform(0.35, 0.8, NM), b=_MR.uniform(0.5, 1.0, NM))
_OR = np.random.default_rng(707)
NO = 220
ORBIT = dict(r=_OR.uniform(0.5, 1.0, NO).astype(np.float32), w=_OR.uniform(0.5, 1.4, NO) * np.where(_OR.random(NO) < 0.8, 1, -1),
             ph=_OR.uniform(0, 6.283, NO), tilt=_OR.uniform(0.18, 0.42, NO), sz=_OR.uniform(0.6, 2.0, NO))
_DIRT = {}


def lens_dirt(A):
    """Smudges, specks and a wipe streak on the 'front element' (quarter res), revealed by bright light."""
    key = (A.qw, A.qh)
    if key not in _DIRT:
        r = np.random.default_rng(88)
        d = np.zeros((A.qh, A.qw), np.float32)
        for _ in range(140):
            cx, cy, rr = r.uniform(0, A.qw), r.uniform(0, A.qh), r.uniform(1.5, 22) * A.qw / 960
            cv2.circle(d, (int(cx), int(cy)), max(1, int(rr)), float(r.uniform(0.15, 0.6)), -1, cv2.LINE_AA)
        for _ in range(6):
            x0, y0 = r.uniform(0, A.qw), r.uniform(0, A.qh)
            cv2.ellipse(d, (int(x0), int(y0)), (int(A.qw * r.uniform(0.08, 0.25)), int(A.qh * 0.02)),
                        float(r.uniform(-30, 30)), 0, 360, 0.35, -1, cv2.LINE_AA)
        _DIRT[key] = cv2.GaussianBlur(d, (0, 0), 1.6 * A.qw / 960)
    return _DIRT[key]


def draw_meteors(lay, gq, t, W, H, sc):
    M = METEORS
    age = t - M["t0"]
    for i in np.where((age > 0) & (age < M["dur"]))[0]:
        u = float(age[i] / M["dur"][i])
        L = float(M["ln"][i]) * W
        dx, dy = math.cos(float(M["ang"][i])), math.sin(abs(float(M["ang"][i])))
        dx = dx if M["ang"][i] > 0 else -dx
        hx, hy_ = float(M["x"][i]) * W + dx * L * 2 * u, float(M["y"][i]) * H + dy * L * 2 * u
        fade = math.sin(math.pi * u) * float(M["b"][i])
        for k in range(8):
            a0, a1 = k / 8, (k + 1) / 8
            v = fade * (1 - a0) ** 1.5 * 255
            cv2.line(lay, (int((hx - dx * L * a0) * 16), int((hy_ - dy * L * a0) * 16)),
                     (int((hx - dx * L * a1) * 16), int((hy_ - dy * L * a1) * 16)),
                     (v * 0.85, v * 0.92, v), max(1, int(2 * sc * (1 - a0))), cv2.LINE_AA, 4)
        cv2.circle(gq, (int(hx / 4 * 16), int(hy_ / 4 * 16)), int(2 * 16), (0.18 * fade, 0.2 * fade, 0.25 * fade),
                   -1, cv2.LINE_AA, 4)


def searchlights(t, A, hy):
    """Three sweeping searchlight beams from the city (quarter res, additive)."""
    out = np.zeros((A.qh, A.qw), np.float32)
    by = (hy if hy is not None else 0.65 * A.H) / 4
    for j, bx in enumerate((0.22, 0.5, 0.8)):
        ang = -math.pi / 2 + 0.45 * math.sin(t * (0.35 + 0.1 * j) + j * 2.1)
        dx, dy = math.cos(ang), math.sin(ang)
        v = dict(qx=A.qxx - np.float32(bx * A.qw), qy=A.qyy - np.float32(by), dx=np.float32(dx), dy=np.float32(dy),
                 w=np.float32(A.qw * 0.006), L=np.float32(A.qh * 1.2))
        out += ev("where(qx*dx+qy*dy > 0, exp(-((qx*dy-qy*dx)/(w*(1+(qx*dx+qy*dy)/(L*0.35))))**2) * exp(-(qx*dx+qy*dy)/L), 0)", v)
    return cv2.resize(out, (A.W, A.H), interpolation=cv2.INTER_LINEAR)[..., None] * np.float32([0.10, 0.11, 0.13])


_WR = np.random.default_rng(919)
NW = 700
WARP = dict(x=_WR.uniform(-1, 1, NW).astype(np.float32), y=_WR.uniform(-1, 1, NW).astype(np.float32),
            z=_WR.uniform(0, 1, NW).astype(np.float32), b=_WR.uniform(0.3, 1.0, NW).astype(np.float32))


def warp_stream(img, t, W, H, sc, amt):
    """Stars streaming past the camera: short radial streaks that lengthen as they fly by."""
    S = WARP
    z = (S["z"] - t * 0.09) % 1.0 + 0.04
    z1 = z + 0.02
    f = W * 0.09
    x0, y0 = W / 2 + S["x"] / z * f, H / 2 + S["y"] / z * f
    x1, y1 = W / 2 + S["x"] / z1 * f, H / 2 + S["y"] / z1 * f
    br = S["b"] * np.clip((1.05 - z) ** 2, 0, 1) * amt
    lay = np.zeros((H // 2, W // 2, 3), np.uint8)
    for i in np.where((br > 0.03) & (np.abs(x0 - W / 2) < W) & (np.abs(y0 - H / 2) < H))[0]:
        v = float(br[i]) * 150
        cv2.line(lay, (int(x1[i] / 2 * 16), int(y1[i] / 2 * 16)), (int(x0[i] / 2 * 16), int(y0[i] / 2 * 16)),
                 (v * 0.8, v * 0.88, v), 1, cv2.LINE_AA, 4)
    img += cv2.resize(lay, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) * np.float32(1 / 255)


# ----------------------------------------------------------------------------- frame
def render2(t, A):
    W, H, sc = A.W, A.H, A.sc
    shot = T.shot_at(t)
    if shot.stutter > 0 and t - shot.t0 < shot.stutter:
        step = 3.0 / T.FPS
        t = shot.t0 + math.floor((t - shot.t0) / step) * step
    nologo = shot.card is not None
    env = shot.env
    scn = A.scn
    sub = shot.sub
    u = span(t, shot.t0, shot.t1)
    F, s4, roll, yaw, ox, oy, shx, shy = camera2(t, shot, A)
    G, a = build_G(A, F, s4, roll, yaw, ox, oy)
    sx, sy = apply_G(G, A.star[0], A.star[1])
    hy = shot.horizon * H if env in SCENIC else None
    pan = lerp(shot.pan[0], shot.pan[1], u)
    f = 1.1 if sub else growth2(t)
    mat = 1.0 if sub else ease_io(span(t, *T.MATERIALIZE))
    vis = 0.0 if nologo else emblem_vis(t, sub)
    si = 0.0 if nologo else star_int2(t, sub)

    pname = PLATE_OF.get(env)
    base = None
    pmask = None
    if pname is not None:
        Pp = A.plates[pname]
        ph, pw = Pp["rgb"].shape[:2]
        zp = 1.0 + 0.05 * ease_io(u) + 0.04 * shot.punch * math.exp(-(t - shot.t0) / 0.3)
        if getattr(T, "V7", False):
            zp = 1.0 + 0.10 * u + 0.012 * math.sin(t * 0.9) + 0.04 * shot.punch * math.exp(-(t - shot.t0) / 0.3)
        tx = W / 2 + pan * sc * (1.3 if getattr(T, "V7", False) else 0.5) + shx * sc - zp * pw / 2
        ty = H / 2 + shy * sc - zp * ph / 2
        Mp = np.float32([[zp, 0, tx], [0, zp, ty]])
        if getattr(T, "V7", False):
            rot = math.radians(0.9 * math.sin(t * 0.21 + shot.seed) + 0.6 * (u - 0.5) * (1 if shot.seed % 2 else -1))
            cs_, sn_ = math.cos(rot) * zp, math.sin(rot) * zp
            cx0, cy0 = W / 2 + pan * sc * 1.3 + shx * sc, H / 2 + shy * sc
            Mp = np.float32([[cs_, -sn_, cx0 - cs_ * pw / 2 + sn_ * ph / 2], [sn_, cs_, cy0 - sn_ * pw / 2 - cs_ * ph / 2]])
        base = cv2.warpAffine(Pp["rgb"], Mp, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        base = base.astype(np.float32)
        base *= np.float32(plate_expo(env, t, sub) / 255.0)
        # darken the photo behind the logo so it punches out of any background
        if not nologo:
            ecs = apply_G(G, A.emb_c[0], A.emb_c[1])
            rad = min(W * 0.6, max(A.emb_h * a * 0.62, 200 * sc))
            halo = ev("1 - k*exp(-(((qx-cx)/rx)**2 + ((qy-cy)/ry)**2))", dict(
                qx=A.qxx, qy=A.qyy, cx=np.float32(ecs[0] / 4), cy=np.float32(ecs[1] / 4),
                rx=np.float32(rad * 0.85 / 4), ry=np.float32(rad / 4), k=np.float32(0.5)))
            base *= cv2.resize(halo, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
        if Pp["mask"] is not None:
            pmask = cv2.warpAffine(Pp["mask"], Mp, (W, H), flags=cv2.INTER_LINEAR)
        if env in WATER:
            hy = Pp["meta"]["horizon"] * zp + ty
        elif env in ("mountain", "storm", "aurora"):
            hy = Pp["meta"]["ridge_mean"] * zp + ty
    img = base.copy() if base is not None else A.bg.copy()
    if getattr(T, "V7", False) and env in ("black", "void") and shot.card is None and t > 7.0:
        warp_stream(img, t, W, H, sc, 1.0 if env == "black" else 0.55)
    q_extra = np.zeros((A.qh, A.qw, 3), np.float32)
    gq = np.zeros((A.qh, A.qw, 3), np.float32)
    lay = np.zeros((H, W, 3), np.uint8)
    occ = pmask

    rev_u = ease_io(span(t, *T.REVEAL))
    col_u = ease_io(span(t, *T.COLLAPSE))
    rev_r = (rev_u * (1 - col_u)) * 5200 * sc
    lt = A.paper.copy() if rev_r > 1 else None

    strikes = strike_list(t, shot)
    flashL = sum(scn.strike_vis(age) * (1.0 if kind == "sky" else 0.75) for j, age, kind in strikes)
    if sub:
        flashL *= 0.35
    boost = sum(scn.strike_vis(age) * 1.5 for j, age, kind in strikes if kind == "emblem")
    if base is not None and flashL > 0.001:
        img *= np.float32(1 + 1.1 * flashL)            # lightning lights up the whole photo

    # --- storm clouds over the photo (behind the logo and the peaks)
    if env == "storm":
        img += cv2.resize(scn.storm_clouds(t, pan, hy, flashL), (W, H), interpolation=cv2.INTER_LINEAR)
    if getattr(T, "V6", False) and env in SCENIC and env not in ("icecave", "deadwood", "forest", "city") and not nologo:
        draw_meteors(lay, gq, t, W, H, sc)
    if getattr(T, "V6", False) and env in ("city", "skyline"):
        img += searchlights(t, A, hy)
    if env == "aurora" or (getattr(T, "V6", False) and env == "snowfield"):
        cur = aurora_curtain(t, A, pan, hy, u)
        if pmask is not None:
            cur *= (1 - pmask.astype(np.float32) / 255)[..., None]
        img += cur
    if env == "volcano":
        # the eruption breathes: hot parts of the photo flicker and pulse on the beat
        fl = 1 + 0.10 * math.sin(t * 13.0) * math.sin(t * 5.3 + 1) + 0.18 * max(0.0, math.sin(t * 2.1)) ** 6
        hotm = np.clip(base.max(2, keepdims=True) * 2.5 - 0.35, 0, 1)
        img *= 1 + (np.float32(fl) - 1) * hotm

    # --- the emblem, the name
    if not nologo:
        draw_emblem(img, q_extra, lt, t, A, G, a, sx, sy, f, mat, vis, boost, sub)
        if not sub:
            draw_words(img, lt, t, A, G, a)
    elif shot.card:
        draw_card(img, q_extra, t, shot, A)

    # --- echo rings (sky) + glow
    water_rings = []
    for age, amp, big in ring_list2(t):
        if sub or nologo:
            break
        rr = ring_radius(age, big) * sc
        al = amp * math.exp(-age / (1.5 if not big else 1.8)) * (1 - span(age, 2.8, 3.5))
        vv = float(np.clip(al * 255, 0, 255))
        if vv < 2:
            continue
        th = max(1, int(round((3 if not big else 6) * sc * 2)))
        cv2.circle(lay, (int(sx * 16), int(sy * 16)), int(rr * 16), (vv * GOLD8[0], vv * GOLD8[1], vv * GOLD8[2]),
                   th, cv2.LINE_AA, 4)
        cv2.circle(gq, (int(sx * 4), int(sy * 4)), int(rr / 4 * 16), tuple(float(c * al * 0.9) for c in GOLD),
                   max(1, int(3 * sc)), cv2.LINE_AA, 4)
        water_rings.append((rr * 0.9, al))

    # --- lightning + energy arcs
    for j, age, kind in strikes:
        vs = scn.strike_vis(age)
        if vs <= 0:
            continue
        rng = np.random.default_rng(5000 + j)
        if kind == "emblem":
            cand = np.where(A.sp_d < max(f, 0.05))[0]
            p = A.sp_xy[cand[rng.integers(len(cand))]] if len(cand) else A.star
            p1 = apply_G(G, float(p[0]), float(p[1]))
            p0 = (p1[0] + rng.uniform(-0.3, 0.3) * W, -0.05 * H)
        elif kind == "ground":
            p1 = (rng.uniform(0.15, 0.85) * W, (hy if hy is not None else 0.75 * H) + 0.02 * H)
            p0 = (p1[0] + rng.uniform(-0.25, 0.25) * W, -0.05 * H)
        else:
            p0 = (rng.uniform(-0.1, 0.4) * W, rng.uniform(0.05, 0.3) * H)
            p1 = (p0[0] + rng.uniform(0.4, 0.8) * W, p0[1] + rng.uniform(-0.1, 0.15) * H)
        scn.draw_bolt(img, gq, scn.bolt_paths(j, p0, p1), vs)
    arc_amt = boost * 0.6 + 1.2 * pulse(t, T.COMPLETE, 0.8) + 1.0 * pulse(t, T.SLAM, 0.6) + (0.8 if sub else 0.0)
    if arc_amt > 0.05 and vis > 0.1 and f > 0:
        idx = A.arc_idx[A.sp_d[A.arc_idx] < f]
        if len(idx) > 8:
            hom = np.c_[A.sp_xy[idx], np.ones(len(idx), np.float32)] @ G.T
            pts = (hom[:, :2] / hom[:, 2:3]).astype(np.float32)
            scn.draw_arcs(img, gq, pts, int(t * T.FPS) // 2 + 77, arc_amt)

    # --- sparks off the growth front
    if T.GROW[0] - 0.2 < t < T.GROW[1] + 3 and not sub and vis > 0 and not nologo:
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

    # --- the star + lens flare
    Rst = A.star_r * a * star_scale2(t, sub) * 1.02
    glint = 1.6 * math.exp(-((t - T.GLINT) / 0.35) ** 2) + 1.2 * math.exp(-((t - T.SPARK - 0.25) / 0.4) ** 2)
    glint += 1.6 * math.exp(-((t - T.COMPLETE) / 0.45) ** 2) + 1.4 * math.exp(-((t - T.STAR_OUT) / 0.25) ** 2)
    glint += 1.0 * math.exp(-((t - T.BOOM) / 0.4) ** 2) + 1.4 * math.exp(-((t - T.SLAM) / 0.4) ** 2)
    R.draw_star(img, sx, sy, Rst, si, 0.35 + glint, A, q=q_extra)
    if lt is None and env != "black" and not nologo:
        scn.flare(gq, sx, sy, min(1.5, si) * (0.8 if env == "void" else 1.0))

    # --- terrain (occluders)
    ec = apply_G(G, A.emb_c[0], A.emb_c[1])
    Ls = 0.25 * si + (0.5 if (0 < f < 1.05 and t < T.COMPLETE) else 0.0) + 0.6 * mat * vis + 0.4 * sub
    light = (ec[0], ec[1], Ls, np.array([0.95, 0.72, 0.38], np.float32))
    if pmask is not None:
        rows = np.where(pmask.max(1) > 8)[0]
        if len(rows):
            y0 = int(rows[0])
            spill = ev("exp(-((qx-lx)**2+(qy-ly)**2)/(r*r))", dict(
                qx=A.qxx, qy=A.qyy, lx=np.float32(ec[0] / 4), ly=np.float32(ec[1] / 4),
                r=np.float32(A.qw * (0.45 if env != "forest" else 0.3))))
            spill = cv2.resize(spill, (W, H), interpolation=cv2.INTER_LINEAR)[y0:]
            strength = 0.92 if env == "forest" else 1.0
            v = dict(img=img[y0:], b=base[y0:], m=(pmask[y0:].astype(np.float32) * np.float32(strength / 255))[..., None],
                     sp=spill[..., None], L=np.float32(Ls * (0.45 if env == "aurora" else 0.9)), F=np.float32(flashL * 0.9),
                     warm=np.array([1.0, 0.72, 0.36], np.float32)[None, None, :],
                     cold=np.array([0.75, 0.82, 1.0], np.float32)[None, None, :])
            v["alb"] = (v["b"].mean(2, keepdims=True) * np.float32(3.0)).clip(0, 1)
            img[y0:] = ev("img*(1-m) + m*(b*(1+F) + alb*sp*L*warm + alb*F*0.5*cold)", v)
    if occ is not None:
        inv = cv2.merge([255 - occ] * 3)
        lay = cv2.multiply(lay, inv, scale=1 / 255)

    # --- foreground particles
    if env in ("black", "void") and not sub:
        p_fade = smooth(span(t, 7.0, 12.0)) * (1 - smooth(span(t, T.STAR_OUT - 1.5, T.STAR_OUT + 3)))
        if t >= T.SLAM:
            p_fade = 0.6 * smooth(span(t, T.SLAM, T.SLAM + 2)) * (1 - smooth(span(t, *T.FADE_END)))
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
            elif t < T.BOOM + 4:
                e = np.float32(ease_out_expo((t - T.BOOM) / 3.5))
                pos = star_s + (pos - star_s) * e
                bright = bright * (1 + 2.0 * (1 - e))
            bright = bright * p_fade
            rad = (0.7 + A.p_z * 1.6) * max(sc * 2, 0.5)
            visi = np.where((bright > 0.02) & (pos[:, 0] > -60) & (pos[:, 0] < W + 60)
                            & (pos[:, 1] > -60) & (pos[:, 1] < H + 60))[0]
            for i in visi:
                x, y = pos[i]
                if A.p_bokeh[i]:
                    draw_dot(lay, x, y, (10 + 18 * A.p_z[i]) * sc * 2, min(255, bright[i] * 60), DUST8)
                else:
                    draw_dot(lay, x, y, rad[i] * 0.6, min(255, bright[i] * 255), GOLD8 if A.p_gold[i] else DUST8)
    if env in RAIN:
        scn.draw_rain(lay, t, 1.0)
    if env in FIREFLY_ENVS:
        scn.draw_fireflies(lay, gq, t, 1.0)
    if env in SNOW_ENVS and env != "aurora":
        draw_snow(lay, t, W, H, sc)
    if env in DUST_ENVS:
        draw_snow(lay, t * 0.35 + 7.0, W, H, sc * 0.8)
    if getattr(T, "V7", False) and env in SCENIC and env not in DUST_ENVS + RAIN + SNOW_ENVS + FIREFLY_ENVS:
        draw_snow(lay, t * 0.25 + 3.0, W, H, sc * 0.6)
    if env == "volcano" and pname is not None:
        draw_lava_bombs(lay, gq, t, Mp, pw, ph, H, sc)
    if env == "aurora":
        draw_snow(lay, t, W, H, sc)
    if getattr(T, "V6", False) and not nologo and vis > 0.5 and (sub or T.COMPLETE <= t < T.COLLAPSE[0] or t >= T.SLAM + 1.0):
        O = ORBIT
        R0 = A.emb_h * a * 0.62
        ang = O["ph"] + O["w"] * t
        ox_ = ec[0] + np.cos(ang) * O["r"] * R0
        oy_ = ec[1] + np.sin(ang) * O["r"] * R0 * O["tilt"]
        dep = 0.35 + 0.65 * (np.sin(ang) > 0)
        for i in range(NO):
            for k in range(3):
                a2 = ang[i] - O["w"][i] * 0.035 * k
                px = ec[0] + math.cos(a2) * O["r"][i] * R0
                py = ec[1] + math.sin(a2) * O["r"][i] * R0 * O["tilt"][i]
                draw_dot(lay, px, py, O["sz"][i] * sc * 2.6 * (1 - 0.25 * k), 255 * dep[i] * vis * (1 - 0.3 * k), GOLD8)
    ember_amt = 0.9 * smooth(span(t, T.COMPLETE, T.COMPLETE + 1.5)) * (1 - smooth(span(t, T.LOCKUP[0] - 2, T.LOCKUP[0] + 2)))
    ember_amt = max(ember_amt, 0.8 * smooth(span(t, T.SLAM, T.SLAM + 1.0)) * (1 - smooth(span(t, *T.FADE_END))))
    if env == "forest":
        ember_amt = max(ember_amt, 0.25)
    if env == "volcano":
        ember_amt = max(ember_amt, 1.0)
    if ember_amt > 0.01 and lt is None:
        scn.draw_embers(lay, gq, t, ember_amt, rise=True)
    if not nologo:
        for te in (T.COMPLETE, T.SLAM):
            draw_shards(lay, gq, t, A, G, sc, te)

    # --- flashes + light leak
    k = 0.45 * pulse(t, T.BOOM, 0.5) + 0.6 * pulse(t, T.COMPLETE, 0.7) + 0.55 * pulse(t, T.SLAM, 0.6)
    if k > 0.002:
        q_extra += ev("exp(-sqrt((qx-sx)**2+(qy-sy)**2)/w*3.0)*k", dict(
            qx=A.qxx, qy=A.qyy, sx=np.float32(sx / 4), sy=np.float32(sy / 4), w=np.float32(A.qw),
            k=np.float32(k)))[..., None] * GOLD
    if shot.leak:
        scn.leak(q_extra, u, 1.0)

    # --- impact light-streak bursts
    imps = [(t - ti, s) for ti, s in T.IMPACTS if 0 <= t - ti < 0.6]
    for age, s in imps:
        if s >= 0.5 and lt is None:
            cxs, cys = (ec if not nologo else (W / 2, H / 2))
            streak_burst(gq, cxs, cys, age, s, int(s * 1000) + int((t - age) * 10), sc)

    # --- bloom + god rays
    small = cv2.resize(img, (A.qw, A.qh), interpolation=cv2.INTER_AREA)
    bright = np.maximum(small - 0.62, 0)
    b1 = cv2.GaussianBlur(bright, (0, 0), 3 * sc * 4)
    b2 = cv2.GaussianBlur(cv2.resize(bright, (A.qw // 2, A.qh // 2), interpolation=cv2.INTER_AREA), (0, 0), 8 * sc * 4)
    q = q_extra + b1 * 0.45 + cv2.resize(b2, (A.qw, A.qh)) * 0.55
    q += cv2.GaussianBlur(gq, (0, 0), 2.0 * sc * 4)
    q += cv2.GaussianBlur(bright, (0, 0), 6 * sc * 4) * np.float32([0.22, 0.06, 0.025])  # film halation
    if getattr(T, "V5", False):
        # anamorphic lens streaks: every highlight throws a long blue horizontal flare
        hot = np.maximum(small - 0.9, 0)
        ana = cv2.GaussianBlur(hot, (0, 0), sigmaX=A.qw * 0.07, sigmaY=0.7)
        q += ana * ANA_TINT * np.float32(2.4)
        if env in SCENIC:
            q += fog_layer(t, A, hy, env)
    if getattr(T, "V6", False):
        illum = cv2.GaussianBlur(cv2.resize(b2, (A.qw, A.qh)), (0, 0), A.qw * 0.03)
        q += lens_dirt(A)[..., None] * illum * np.float32(3.2) * np.float32([1.0, 0.92, 0.8])
    ray_amt = {"void": 0.55, "forest": 1.1, "mountain": 0.7, "storm": 0.45, "ocean": 0.5, "black": 0.45, "aurora": 0.6, "volcano": 0.9}.get(env, 0.65)
    ray_amt *= smooth(span(t, T.SPARK, T.SPARK + 2)) if not sub else 1.0
    if t > T.STAR_OUT and t < T.SLAM:
        ray_amt *= 1 - smooth(span(t, T.STAR_OUT, T.STAR_OUT + 0.6))
    if ray_amt > 0.01:
        rc = (sx / 4, sy / 4) if env in ("void", "black") else (ec[0] / 4, ec[1] / 4)
        rad = max(A.qw * 0.06, Rst * 2.5 / 4) if env in ("void", "black") else A.qw * 0.22
        near = ev("exp(-((qx-cx)**2+(qy-cy)**2)/(r*r))", dict(
            qx=A.qxx, qy=A.qyy, cx=np.float32(rc[0]), cy=np.float32(rc[1]), r=np.float32(rad)))
        src = np.maximum(small - 0.45, 0) * near[..., None]
        acc = np.zeros_like(src)
        for i in range(1, 14):
            kk = 1 + 0.05 * i
            M = np.float32([[kk, 0, rc[0] * (1 - kk)], [0, kk, rc[1] * (1 - kk)]])
            acc += cv2.warpAffine(src, M, (A.qw, A.qh)) * (1 - i / 14)
        q += cv2.GaussianBlur(acc, (0, 0), 1.5) * (ray_amt / 6)
    img += cv2.resize(q, (W, H), interpolation=cv2.INTER_LINEAR)

    # --- water: the logo's light reflected and rippled through the real sea
    if env in WATER:
        lay[int(hy):] = 0
        scn.ocean_plate(img, base, t, hy, sx, max(si, Ls), lay, water_rings)

    # --- light-mode blend (reveal / collapse)
    if lt is not None:
        R.draw_star(lt, sx, sy, A.star_r * a * 1.02, 1.0, 0.0, A, light=1.0)
        v = dict(xx=A.xx, yy=A.yy, sx=np.float32(sx), sy=np.float32(sy), r=np.float32(rev_r),
                 e=np.float32(70 * sc), w1=np.float32(55 * sc), w2=np.float32(260 * sc))
        v["d"] = ev("sqrt((xx-sx)**2+(yy-sy)**2)", v)
        v["m"] = ev("where((r-d)/e+0.5 > 1, 1, where((r-d)/e+0.5 < 0, 0, (r-d)/e+0.5))", v)
        wave = ev("(exp(-((d-r)/w1)**2)*1.2 + exp(-((d-r)/w2)**2)*0.35) * (1-m)", v)
        m3 = v["m"][..., None]
        img = img * (1 - m3) + lt * m3 + wave[..., None] * GOLD_HOT
        lay = (lay.astype(np.float32) * (1 - m3)).astype(np.uint8)

    # --- shockwave distortion with prismatic fringe
    sw = [(t0, s) for t0, s in T.SHOCKWAVES if (s > 0.3 or env == "storm")]
    img = scn.shockwave(img, A.xx, A.yy, sx, sy, sw, t)

    # --- zoom-blur punch radiating from the logo, and the white-hot impact frame
    zb = max([s * math.exp(-age / 0.12) for age, s in imps], default=0.0)
    if zb > 0.05 and lt is None:
        cxs, cys = (ec if not nologo else (W / 2, H / 2))
        img = zoom_blur(img, cxs, cys, zb, A)
    hot = any(s >= 0.9 and age < 1.0 / T.FPS for age, s in imps)
    if hot:
        img = img * np.float32(2.3) + np.float32(0.16)

    if getattr(T, "V6", False) and shot.punch > 0 and lt is None:
        wa = (t - shot.t0) * T.FPS
        if 0 <= wa < 2.0:
            kw = int(W * 0.07 * (1 - wa / 2.0)) | 1
            if kw > 3:
                img = cv2.blur(img, (kw, 1))

    # --- finishing
    vk = np.float32(1.0 if lt is None else 0.25)
    hold = 1 - 0.5 * smooth(span(t, T.SILENCE[0], T.SILENCE[0] + 0.4)) * (T.SILENCE[0] <= t < T.COMPLETE)
    fade = smooth(span(t, 0.0, 0.3)) * (1 - smooth(span(t, *T.FADE_END))) * hold
    cut = shot.flash * math.exp(-(t - shot.t0) / 0.07) + flashL * 0.06
    img *= (A.vignette if vk == 1 else 1 - (1 - A.vignette) * vk) * np.float32(fade)
    if cut > 0.003:
        img += np.float32(cut) * np.float32([0.95, 0.88, 0.78])
    g = cv2.resize(A.grain[int(t * T.FPS) % len(A.grain)], (W, H), interpolation=cv2.INTER_LINEAR)
    # filmic ACES curve, lifted teal blacks, warm highlights, then grain
    out = ev("(x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14)", dict(x=np.maximum(img * np.float32(1.12), 0)))
    out = ev("(where(y > 1, 1, y) + lift*(1-y)**8 + warm*y**3)*255 + g3*2.0", dict(
        y=out, lift=np.float32([0.004, 0.009, 0.014])[None, None, :], warm=np.float32([0.03, 0.005, -0.03])[None, None, :],
        g3=g[..., None]))
    out = cv2.convertScaleAbs(out)
    if fade < 1:
        lay = (lay.astype(np.float32) * fade).astype(np.uint8)
    out = cv2.add(out, lay)
    if any(s >= 1.0 and 1.0 / T.FPS <= age < 2.0 / T.FPS for age, s in imps):
        out = 255 - out                                                  # one negative frame: shock
    gl = 0.0
    if shot.stutter > 0 or shot.card:
        gl = max(gl, math.exp(-(t - shot.t0) / 0.07))
    gl = max([gl] + [s * math.exp(-age / 0.06) for age, s in imps if s >= 0.8])
    if gl > 0.08:
        glitch_slices(out, int(t * T.FPS) * 7 + 3, min(1.0, gl), sc)
    ca = (1.0 * pulse(t, T.BOOM, 0.3) + 1.4 * pulse(t, T.COMPLETE, 0.35) + 1.2 * pulse(t, T.SLAM, 0.35)
          + 0.6 * sum(math.exp(-age / 0.15) for j, age, kind in strikes) + 4 * shot.punch * pulse(t, shot.t0, 0.15)
          + (1.2 if sub else 0.0) + sum(1.6 * s * math.exp(-age / 0.18) for age, s in imps))
    if ca > 0.02:
        for c, sgn in ((0, 1), (2, -1)):
            kk = 1 + sgn * 0.006 * ca
            M = np.float32([[kk, 0, W / 2 * (1 - kk)], [0, kk, H / 2 * (1 - kk)]])
            out[..., c] = cv2.warpAffine(np.ascontiguousarray(out[..., c]), M, (W, H), borderMode=cv2.BORDER_REPLICATE)
    bar = int(A.bar * (1 - ease_io(span(t, T.LOCKUP[0] - 1, T.LOCKUP[1]))))
    if bar > 0:
        out[:bar] = 0
        out[H - bar:] = 0
    return out


# ----------------------------------------------------------------------------- main
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
    A = Assets2(args.scale)
    if args.stills:
        os.makedirs(os.path.join(HERE, "out2", "stills"), exist_ok=True)
        for s in args.stills.split(","):
            t = float(s)
            t0 = time.time()
            fr = render2(t, A)
            p = os.path.join(HERE, "out2", "stills", f"t{t:06.2f}.png")
            cv2.imwrite(p, cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
            print(p, f"{time.time() - t0:.2f}s", flush=True)
        return
    cmd = [R.ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{A.W}x{A.H}", "-r", str(T.FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "faster", "-crf", str(args.crf), "-tune", "film",
           "-maxrate", "45M", "-bufsize", "90M", "-g", str(T.FPS * 2),
           "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
           "-color_trc", "bt709", "-threads", "1", args.out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(args.start, args.end):
        fr = render2(i / T.FPS, A)
        proc.stdin.write(fr.tobytes())
        if (i - args.start) % 48 == 0:
            el = time.time() - t0
            done = i - args.start + 1
            print(f"[{args.start}-{args.end}] frame {i}  {el / done:.2f}s/f  eta {(args.end - i) * el / done / 60:.1f} min",
                  flush=True)
    proc.stdin.close()
    proc.wait()
    print("done", args.out, flush=True)


if __name__ == "__main__":
    main()
