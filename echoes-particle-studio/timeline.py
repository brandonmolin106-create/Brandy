"""The edit: every shot of "The Fish in the Cup", synced to Brandon's words.

Each shot is a function (t, ctx) -> Frame. Times are seconds on the speech
timeline (word timestamps from the proofread transcript).
"""
import math

import numpy as np

import render_core as rc
from director import Frame, shake_offset
from elements import Dust, Galaxy, Nebula, ParticleText, Starfield, _cat, palette, rot_x, rot_y, rot_z
from elements2 import (Cup, Fish, Ocean, Person, Planet, Sun, Terrain, Tree, burst, circle_path, frame_from_dir,
                       light_beam, ring_ticks, ss, trail_ring)


# ------------------------------------------------------------------ helpers

def clamp01(x):
    return min(max(x, 0.0), 1.0)


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def smoother(x):
    x = clamp01(x)
    return x * x * x * (x * (x * 6 - 15) + 10)


def ramp(t, a, b):
    return smooth((t - a) / (b - a)) if b > a else float(t >= a)


def pulse(t, t0, attack=0.05, decay=0.6):
    if t < t0 - attack:
        return 0.0
    if t < t0:
        return (t - t0 + attack) / attack
    return math.exp(-(t - t0) / decay)


def kf(t, keys, ease=smoother):
    """Keyframes [(t, value)] with eased interpolation; values may be tuples."""
    if t <= keys[0][0]:
        return np.asarray(keys[0][1], np.float64)
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return np.asarray(v0, np.float64) * (1 - u) + np.asarray(v1, np.float64) * u
    return np.asarray(keys[-1][1], np.float64)


def orbit(center, dist, yaw, pitch):
    c = np.asarray(center, np.float64)
    return c + dist * np.array([math.sin(yaw) * math.cos(pitch), math.sin(pitch), math.cos(yaw) * math.cos(pitch)])


def cam(eye, target, fov=36.0, focus=None, dof=0.0, roll=0.0, shake=0.0, t=0.0, seed=0.0):
    eye = np.asarray(eye, np.float64)
    target = np.asarray(target, np.float64)
    if shake > 0:
        dx, dy, dr = shake_offset(t, shake, seed)
        d = np.linalg.norm(target - eye)
        eye = eye + np.array([dx, dy, 0.0]) * d * 0.02
        target = target + np.array([dx, dy, 0.0]) * d * 0.02
        roll += dr
    return rc.Camera(eye, target, fov=fov, focus=focus, dof=dof, roll=roll)


def merge(*parts):
    return _cat(*[p for p in parts if p is not None])


def screen_of(c, p):
    xy, z = c.project(np.array([p], np.float64))
    return (float(xy[0][0]), float(xy[0][1])), float(z[0])


# ------------------------------------------------------------------ assets

class Assets:
    def __init__(self):
        self.stars = Starfield(bright=0.7)
        self.stars_dense = Starfield(n=200000, seed=9, bright=0.3, milky=0.7)
        self.neb_cosmic = Nebula(center=(0, 8, -160), extent=(170, 110, 70), bright=0.0010, thresh=0.12, pal='cosmic')
        self.neb_ice = Nebula(center=(-20, 10, -170), extent=(160, 100, 70), bright=0.0010, thresh=0.1, pal='ice', seed=12)
        self.neb_dawn = Nebula(center=(0, 20, -180), extent=(200, 110, 80), bright=0.0007, thresh=0.12, pal='dawn', seed=14)
        self.neb_ember = Nebula(center=(0, 10, -150), extent=(160, 100, 70), bright=0.0006, thresh=0.14, pal='ember', seed=16)
        self.dust = Dust(n=4000, box=(3, 4, 4), size=0.0015, bright=0.6)
        self.dust_big = Dust(n=6000, box=(40, 20, 60), size=0.02, bright=0.5, seed=7)
        self.fish = Fish()
        self.cup = Cup()
        self.ocean = Ocean()
        self.terrain = Terrain()
        self.person = Person()
        self.sun = Sun()
        self.tree = Tree()
        self.planet = Planet()
        self.galaxy = Galaxy()
        self.galaxy2 = Galaxy(n=120000, radius=40, arms=2, seed=8, twist=2.6)
        self.txt = {}

    def text(self, s, height=1.0, color=(1.0, 0.75, 0.35), font='/opt/fonts/Montserrat.ttf', weight='Black', seed=4,
             density=0.9):
        k = (s, height, color, font, weight)
        if k not in self.txt:
            self.txt[k] = ParticleText(s, height=height, color=color, font=font, weight=weight, seed=seed,
                                       density=density)
        return self.txt[k]


RED = (1.0, 0.18, 0.12)
GOLD = (1.0, 0.72, 0.3)

# standard avatar spec


def AV(look='starlight', gain=1.6, pos=(0, 0, 0), scale=1.0, yaw=0.0, dissolve=0.0, lift=0.25, spread=0.12,
       keep=0.5, point=0.6, aura=0.012, aura_frac=0.05, glints=1.0, shimmer=0.12, voice_glow=0.35, **kw):
    d = dict(look=look, gain=gain, pos=pos, scale=scale, yaw=yaw, dissolve=dissolve, lift=lift, spread=spread,
             keep=keep, point=point, aura=aura, aura_frac=aura_frac, glints=glints, shimmer=shimmer,
             voice_glow=voice_glow)
    d.update(kw)
    return d


def face_cam(t, dist=0.62, yaw=0.0, pitch=0.02, ty=-0.07, fov=36.0, shake=0.0, dof=5.0, center=(0, 0, 0), roll=0.0):
    c = np.asarray(center, np.float64) + np.array([0, ty, 0])
    eye = orbit(c, dist, yaw, pitch)
    return cam(eye, c, fov=fov, focus=dist, dof=dof, shake=shake, t=t, roll=roll)


# ------------------------------------------------------------------ shots

class Shots:
    def __init__(self, A, energy):
        self.A = A
        self.energy = energy

    def e(self, t):
        i = int(t * 30)
        return float(self.energy[min(max(i, 0), len(self.energy) - 1)])

    # --- 0.00 INTRO: particles assemble into Brandon ---
    def intro(self, t, ctx):
        A = self.A
        form = 1.0 - smoother(t / 1.5)
        dis = form + 0.22 * math.sin(clamp01((t - 4.0) / 1.5) * math.pi) + 0.35 * ramp(t, 7.0, 8.6)
        yaw = float(kf(t, [(0, -0.28), (8.6, 0.12)]))
        dist = float(kf(t, [(0, 1.25), (3.0, 0.78), (8.6, 0.66)]))
        c = face_cam(t, dist=dist, yaw=yaw, pitch=0.03, shake=0.3)
        bg = merge(A.stars.at(t, gain=ramp(t, 0.0, 1.5)), A.neb_cosmic.at(t, gain=0.8 * ramp(t, 0.3, 3.0)))
        fg = A.dust.at(t, center=(0, 0, 0.2), cam_pos=c.eye, gain=0.5)
        return Frame(c, bg=bg, fg=fg, avatar=AV('starlight', dissolve=dis, lift=0.35, spread=0.25),
                     rays=((540, 560), 0.35, 0.8), bg_dof=1.5,
                     grade=dict(exposure=ramp(t, 0.0, 0.6) * 1.0 + 0.001))

    # --- 8.60 fish forms from Brandon's particles ---
    def fish_reveal(self, t, ctx):
        A = self.A
        dis = 0.35 + 0.65 * ramp(t, 8.6, 9.5)
        fdis = 1.0 - smoother((t - 8.85) / 1.05)
        c1 = face_cam(t, dist=float(kf(t, [(8.6, 0.66), (10.0, 0.9)])), yaw=0.12, pitch=0.03)
        beat = 6.0 + 10.0 * pulse(t, 10.6, 0.1, 0.4)
        fish = A.fish.at(t, pos=(0.09, -0.05, 0.0), heading=(1, 0, 0.35), scale=0.3, gain=1.0 * (1 - fdis) + 0.001,
                         dissolve=fdis, beat=beat)
        ctr = np.average(fish[0], axis=0, weights=fish[1].sum(1) + 1e-6) if t > 9.3 else np.array([0.0, -0.05, 0.0])
        ctr = ctr * ramp(t, 9.3, 10.3) + np.array([0.0, -0.05, 0.0]) * (1 - ramp(t, 9.3, 10.3))
        c = cam(orbit(ctr, float(kf(t, [(8.6, 1.35), (11.7, 1.1)])), float(kf(t, [(8.6, 0.12), (11.7, -0.25)])),
                      0.08), ctr, fov=36, dof=3.0, focus=1.2)
        av = AV('starlight', dissolve=dis, lift=0.2, spread=0.3, gain=1.6 * (1 - ramp(t, 9.4, 10.2)))
        bg = merge(A.stars.at(t), A.neb_cosmic.at(t, gain=0.2), fish)
        return Frame(c, bg=bg, avatar=av if t < 10.0 else None, bg_dof=1.0, rays=((540, 900), 0.3, 0.8))

    # --- 11.70 the fish in the void, the cup builds around it ---
    def cup_intro(self, t, ctx):
        A = self.A
        fp, fd = circle_path(t, center=(0, 0.42, 0), radius=0.15 * ramp(t, 11.7, 14.5) + 0.001, omega=1.2)
        fp = fp * ramp(t, 11.7, 12.5) + np.array([0.0, 0.42, 0.0]) * (1 - ramp(t, 11.7, 12.5))
        fish = A.fish.at(t, pos=fp, heading=fd, scale=0.22)
        build = ramp(t, 15.1, 17.9)
        eye = kf(t, [(11.7, (0.25, 0.48, 0.95)), (15.0, (0.45, 0.66, 1.8)), (19.3, (0.12, 0.95, 2.95))])
        c = cam(eye, (0, 0.42, 0), fov=36, dof=3.0, focus=float(np.linalg.norm(eye - np.array([0, 0.42, 0]))))
        cupp = A.cup.at(t, cam_pos=c.eye, build=build, water=build > 0.6, water_gain=ramp(t, 16.8, 17.8))
        bg = merge(A.stars.at(t), A.neb_ice.at(t, gain=0.18), cupp, fish,
                   trail_ring((0, 0.42, 0), 0.15, t, 1.2, length=2.0, gain=0.25 * ramp(t, 13, 15)))
        return Frame(c, bg=bg, fg=A.dust.at(t, center=(0, 0.4, 0.8), cam_pos=c.eye, gain=0.3), bg_dof=1.0)

    # --- 19.30 the ocean it could have: swim and swim and swim ---
    def ocean_glimpse(self, t, ctx):
        A = self.A
        tt = t - 19.3
        surge = sum(pulse(t, tw, 0.05, 0.5) for tw in (22.25, 23.11, 23.83))
        fx = tt * 3.0
        fpos = np.array([math.sin(tt * 0.6) * 1.5, 0.3 + 0.15 * math.sin(tt * 1.3), -fx])
        fdir = np.array([math.cos(tt * 0.6) * 0.9, 0.2 * math.cos(tt * 1.3), -3.0])
        fish = A.fish.at(t, pos=fpos, heading=fdir, scale=0.9, gain=2.5, beat=7 + 8 * surge)
        rise = ramp(t, 25.6, 27.6)
        eye = fpos + np.array([1.2 + 6 * rise, 0.9 + 14 * rise, 4.0 + 10 * rise])
        c = cam(eye, fpos + np.array([0, 0, -2.0]), fov=48, dof=2.0, focus=float(np.linalg.norm(eye - fpos)))
        pulses = [(tw, 12.0, 2.5, 1.0, float(fpos[0]), float(fpos[2])) for tw in (22.25, 23.11, 23.83)]
        oc = A.ocean.at(t, cam=c, light_dir=(0.2, 0.25, -1.0), pulses=pulses, amp=0.8, gain=1.0)
        moon = merge(A.stars.at(t, center=c.eye), A.galaxy.at(t, center=(40, 60, -300 - fx), tilt=1.1, gain=0.25))
        return Frame(c, bg=merge(moon, oc, fish), fog=0.006, fog_color=(0.3, 0.55, 1.0), bg_dof=0.5,
                     grade=dict(split_sh=(-0.02, 0.01, 0.05)))

    # --- 27.60 just a cup: it can only swim a little ---
    def cup_confined(self, t, ctx):
        A = self.A
        om = 1.5
        r = 0.15 + 0.06 * ramp(t, 34.2, 36.8)
        fp, fd = circle_path(t, center=(0, 0.42, 0), radius=r, omega=om)
        fish = A.fish.at(t, pos=fp, heading=fd, scale=0.22, beat=6 + 3 * ramp(t, 34, 36))
        yaw = float(kf(t, [(27.6, 0.4), (33.4, -0.6), (39.9, -1.4)]))
        dist = float(kf(t, [(27.6, 2.6), (31.4, 1.9), (33.4, 1.75), (37.0, 1.45), (39.9, 1.3)]))
        pitch = float(kf(t, [(27.6, 0.25), (33.4, 0.15), (39.9, 0.05)]))
        c = cam(orbit((0, 0.42, 0), dist, yaw, pitch), (0, 0.42, 0), fov=36, dof=4.0, focus=dist)
        bg = merge(A.stars.at(t), A.neb_ice.at(t, gain=0.2), A.cup.at(t, cam_pos=c.eye), fish,
                   trail_ring((0, 0.42, 0), r, t, om, length=3.5, gain=0.35))
        return Frame(c, bg=bg, fg=A.dust.at(t, center=(0, 0.4, 0.9), cam_pos=c.eye, gain=0.3), bg_dof=1.0)

    # --- 39.90 it hits glass like a wall, again and again, years after year ---
    def hits_glass(self, t, ctx):
        A = self.A
        R_in = 0.3
        hit1, hit2 = 41.88, 46.80
        # path: 39.9-41.88 dash to +x wall; bounce; 43.8 turn; 46.8 hit -x wall; then circles
        if t < hit1:
            u = smooth((t - 39.9) / (hit1 - 39.9))
            fp = np.array([-0.05 + (R_in - 0.07 + 0.05) * u ** 1.6, 0.42, 0.0]); fd = np.array([1.0, 0, 0])
        elif t < 43.8:
            u = (t - hit1) / (43.8 - hit1)
            fp = np.array([R_in - 0.07 - 0.06 * math.sin(min(u * 3, 1) * math.pi / 2), 0.42, 0.02 * u]); fd = np.array([1.0, 0, 0.1 * u])
        elif t < hit2:
            u = smooth((t - 43.8) / (hit2 - 43.8))
            ang = u * math.pi
            fp = np.array([(R_in - 0.13) * math.cos(ang), 0.42, 0.12 * math.sin(ang)])
            fd = np.array([-math.sin(ang), 0, math.cos(ang) * 0.5]) if u < 0.85 else np.array([-1.0, 0, 0])
            if u > 0.6:
                fp[0] = -(R_in - 0.07) * smooth((u - 0.6) / 0.4) + fp[0] * (1 - smooth((u - 0.6) / 0.4))
        else:
            fp, fd = circle_path(t - 46.8, center=(0, 0.42, 0), radius=0.16, omega=1.5 + 3.0 * ramp(t, 48, 53), phase=math.pi)
        fish = A.fish.at(t, pos=fp, heading=fd, scale=0.22, beat=8 + 6 * pulse(t, hit1, 0.02, 0.3) + 6 * pulse(t, hit2, 0.02, 0.3))
        impacts = [(hit1, (R_in, 0.42, 0.0)), (hit2, (-R_in, 0.42, 0.0))]
        # camera: outside glass looking at the fish approaching; then pull up to top-down time-lapse
        top = ramp(t, 48.0, 51.5)
        if t < 43.8:
            eye = np.array([1.25, 0.5, 0.45]); tgt = np.array([0.1, 0.42, 0.0])
        elif t < 48.0:
            yaw = float(kf(t, [(43.8, 1.2), (48.0, -1.3)]))
            eye = orbit((0, 0.42, 0), 1.25, yaw, 0.12); tgt = np.array([0, 0.42, 0])
        else:
            eye = orbit((0, 0.42, 0), 1.2 + 0.9 * top, -1.3 + 0.8 * top, 0.12 + 1.4 * top); tgt = np.array([0, 0.3 + 0.12 * (1 - top), 0])
        sh = 2.2 * pulse(t, hit1, 0.01, 0.35) + 2.2 * pulse(t, hit2, 0.01, 0.35)
        c = cam(eye, tgt, fov=36, dof=3.0, focus=float(np.linalg.norm(eye - tgt)), shake=sh, t=t)
        wall = 1.0 + 3.0 * pulse(t, 42.9, 0.1, 0.8)
        cupp = A.cup.at(t, cam_pos=c.eye, impacts=impacts, gain=wall)
        spin = -(t - 48.0) ** 2 * 0.35 if t > 48 else 0.0
        ticks = ring_ticks(t, center=(0, 0.0, 0), radius=0.62, spin=spin, gain=0.6 * ramp(t, 48.0, 49.0), sweep=spin * 3) if t > 47.8 else None
        trail = trail_ring((0, 0.42, 0), 0.16, t - 46.8, 1.5 + 3.0 * ramp(t, 48, 53), length=2 + 12 * ramp(t, 48, 53),
                           gain=0.5 * ramp(t, 47.0, 49.0), phase=math.pi) if t > 46.8 else None
        day = 0.5 + 0.5 * math.sin((t - 48) * (2 + 8 * ramp(t, 48, 53)) * 2) if t > 48 else 1.0
        g = dict(exposure=0.85 + 0.3 * day * ramp(t, 48, 49) + (1 - ramp(t, 48, 49)) * 0.15,
                 split_hi=(0.03 + 0.03 * day, 0.012, -0.02 - 0.03 * (1 - day)))
        fl = 0.12 * pulse(t, hit1, 0.01, 0.12) + 0.12 * pulse(t, hit2, 0.01, 0.12)
        return Frame(c, bg=merge(A.stars.at(t), A.neb_ice.at(t, gain=0.35), cupp, fish, ticks, trail), bg_dof=1.0,
                     grade=g, flash=fl)

    # --- 53.40 the same circles (top-down) ---
    def same_circles(self, t, ctx):
        A = self.A
        om = 4.5
        fp, fd = circle_path(t, center=(0, 0.42, 0), radius=0.16, omega=om)
        fish = A.fish.at(t, pos=fp, heading=fd, scale=0.22, beat=9)
        roll = (t - 53.4) * 0.15
        c = cam((0.0, 2.3, 0.001), (0, 0.4, 0), fov=36, roll=roll, dof=0)
        c.up = np.array([0.0, 0.0, -1.0])
        rings = [trail_ring((0, 0.42, 0), rr, t, om, length=1.4, gain=0.25, n=900) for rr in (0.16, 0.155, 0.165, 0.15, 0.17)]
        return Frame(c, bg=merge(A.stars.at(t), A.cup.at(t, cam_pos=c.eye, reflect=False), fish, *rings),
                     grade=dict(exposure=0.95))

    # --- 58.60 then something happens: the fish stops trying ---
    def stops_trying(self, t, ctx):
        A = self.A
        stop = ramp(t, 60.5, 63.0)
        om = 1.5 * (1 - stop) + 0.08
        fp, fd = circle_path(t, center=(0, 0.42 - 0.12 * stop, 0), radius=0.16 * (1 - 0.6 * stop), omega=om)
        cold = ramp(t, 60.8, 64.0)
        fish = A.fish.at(t, pos=fp, heading=fd, scale=0.22, beat=6 * (1 - stop) + 1.2, amp=1 - 0.6 * stop,
                         gain=1.0 - 0.45 * cold, tint=(0.35, 0.55, 1.0, 0.75 * cold))
        push = ramp(t, 65.5, 71.4)
        tgt = fp.copy()
        eye = tgt + np.array([0.55 - 0.35 * push, 0.08, 0.95 - 0.55 * push])
        c = cam(eye, tgt, fov=36, dof=6.0, focus=float(np.linalg.norm(eye - tgt)))
        barrier = 0.6 + 2.5 * ramp(t, 69.6, 71.2)
        cupp = A.cup.at(t, cam_pos=c.eye, gain=barrier, tint=(0.5, 0.7, 1.0))
        return Frame(c, bg=merge(A.stars.at(t, gain=0.7), A.neb_ice.at(t, gain=0.25), cupp, fish), bg_dof=1.0,
                     grade=dict(sat=0.85, exposure=0.95))

    # --- 71.40 inner voice: "I cannot go any more than this. Think about that." ---
    def inner_voice(self, t, ctx):
        A = self.A
        form = 1.0 - smoother((t - 71.4) / 1.2)
        push = ramp(t, 75.6, 77.0)
        c = face_cam(t, dist=0.7 - 0.2 * push, yaw=-0.18 + 0.1 * push, pitch=0.02, ty=-0.05 + 0.02 * push, dof=6)
        bg = merge(A.stars.at(t, gain=0.6), A.neb_ice.at(t, gain=0.35))
        return Frame(c, bg=bg, avatar=AV('ghost', dissolve=form * 0.9, gain=1.5, lift=0.2, spread=0.2),
                     grade=dict(sat=0.7), bg_dof=1.5, rays=((540, 520), 0.25, 0.8))

    # --- 77.00 people walk past and judge the fish ---
    def people(self, t, ctx):
        A = self.A
        fp, fd = circle_path(t, center=(0, 0.42, 0), radius=0.12, omega=0.6)
        fish = A.fish.at(t, pos=fp, heading=fd, scale=0.22, gain=0.7, tint=(0.35, 0.55, 1.0, 0.5))
        dolly = float(kf(t, [(77.0, 0.0), (87.1, 1.0)]))
        eye = np.array([0.9 - 1.8 * dolly, 0.35, 3.2])
        c = cam(eye, (0, 1.6, 0), fov=50, dof=3.0, focus=3.2)
        ppl = []
        speeds = [(-9, 0.9, -3.4, 1.0), (10, -0.8, -4.6, 0.0), (-12, 0.7, -7.0, 2.0), (12, -0.75, -3.8, 3.0)]
        for k, (x0, v, z, ph) in enumerate(speeds):
            x = x0 + v * (t - 77.0) * 1.0 * 2.2
            ppl.append(A.person.at(t * 1.1 + ph, pos=(x, 0, z), yaw=math.pi / 2 if v > 0 else -math.pi / 2, scale=2.4,
                                   cam_pos=c.eye, col=(1.0, 0.25, 0.15), gain=0.5, walk=1.0, rim=1.4))
        words = []
        for (s, t0, pos) in (('NOT VERY GOOD', 81.48, (-0.25, 3.0, -1.5)), ('CAN\'T DO ANYTHING', 84.18, (0.2, 2.35, -1.8)),
                             ('HA  HA  HA', 86.36, (0.0, 3.55, -2.6))):
            if t > t0 - 0.3:
                txt = A.text(s, height=0.13, color=RED)
                f = smooth((t - t0 + 0.3) / 0.6)
                drift = np.array(pos) + np.array([0, -0.25 * (t - t0), 0.1 * (t - t0)])
                words.append(txt.at(t, form=f, center=drift, gain=1.4, jitter=0.004))
        cupp = A.cup.at(t, cam_pos=c.eye, gain=0.8)
        return Frame(c, bg=merge(A.stars.at(t, gain=0.5), A.neb_ember.at(t, gain=0.55), cupp, fish, *ppl, *words),
                     bg_dof=1.0, grade=dict(split_sh=(0.02, -0.005, 0.0), sat=0.95, exposure=0.95))

    # --- 87.10 "Now let me ask you something." ---
    def ask(self, t, ctx):
        A = self.A
        push = ramp(t, 87.1, 89.4)
        c = face_cam(t, dist=0.8 - 0.18 * push, yaw=0.2 - 0.1 * push, dof=6)
        return Frame(c, bg=merge(A.stars.at(t), A.neb_dawn.at(t, gain=0.4)), avatar=AV('gold', gain=1.6),
                     rays=((560, 540), 0.35, 0.8), bg_dof=1.5)

    # --- 89.40 do their words make the fish smaller? NO. (x2) ---
    def words_shatter(self, t, ctx):
        A = self.A
        no1, no2 = 91.96, 96.94
        glow = 0.7 + 0.8 * ramp(t, 92.6, 96.3) + 1.2 * pulse(t, no2, 0.02, 1.2)
        fp, fd = circle_path(t, center=(0, 0.42, 0), radius=0.14, omega=1.0 + 1.2 * ramp(t, 92, 96))
        warm = ramp(t, 92.0, 96.9)
        fish = A.fish.at(t, pos=fp, heading=fd, scale=0.22, gain=glow, tint=(0.35, 0.55, 1.0, 0.5 * (1 - warm)))
        yaw = float(kf(t, [(89.4, -0.4), (97.5, 0.9)]))
        dist = float(kf(t, [(89.4, 2.9), (91.9, 2.6), (97.5, 2.0)]))
        sh = 3.0 * pulse(t, no1, 0.01, 0.4) + 3.0 * pulse(t, no2, 0.01, 0.4)
        c = cam(orbit((0, 0.7, 0), dist, yaw, 0.12), (0, 0.72, 0), fov=40, dof=3, focus=dist, shake=sh, t=t)
        parts = [A.stars.at(t), A.neb_dawn.at(t, gain=0.2 + 0.4 * warm)]
        # red judgments hover over the cup, pressing down, then shatter on each "No."
        for (s, pos, tno, tin) in (('NOT VERY GOOD', (-0.05, 1.3, 0.0), no1, 89.4), ('CAN\'T DO ANYTHING', (0.05, 1.16, 0.05), no1, 89.4),
                                   ('SMALL', (0.0, 1.18, 0.0), no2, 92.4), ('NOTHING', (0.0, 1.36, -0.05), no2, 92.4)):
            if t < tin or t > tno + 2.0:
                continue
            txt = A.text(s, height=0.06 if len(s) > 6 else 0.1, color=RED)
            press = -0.25 * ramp(t, tin, tno)
            form = smooth((t - tin) / 0.7) if t < tno else 1.0 - smooth((t - tno) / 0.25)
            parts.append(txt.at(t, form=form, center=(pos[0], pos[1] + press, pos[2]), gain=1.5, jitter=0.002,
                                R=rot_y(yaw)))
        parts.append(burst(t, no1, center=(0, 1.22, 0), n=5000, speed=2.6, seed=3, col=(1.0, 0.35, 0.2), size=0.003, gain=0.25))
        parts.append(burst(t, no2, center=(0, 0.5, 0), n=7000, speed=3.0, seed=4, col=(1.0, 0.75, 0.35), size=0.003, gain=0.25))
        impacts = [(no1, (0.0, 0.95, 0.37)), (no2, (0.0, 0.42, 0.33))]
        parts.append(A.cup.at(t, cam_pos=c.eye, impacts=impacts))
        parts.append(fish)
        fl = 0.06 * pulse(t, no1, 0.01, 0.15) + 0.08 * pulse(t, no2, 0.01, 0.2)
        return Frame(c, bg=merge(*parts), flash=fl, bg_dof=1.0,
                     grade=dict(exposure=1.0 + 0.1 * warm))

    # --- 97.50 the fish is still a fish; what it believes ---
    def still_fish(self, t, ctx):
        A = self.A
        fp, fd = circle_path(t, center=(0, 0.42, 0), radius=0.14, omega=1.6)
        fish = A.fish.at(t, pos=fp, heading=fd, scale=0.22, gain=1.6)
        u = ramp(t, 97.5, 104.8)
        c = cam(orbit((0, 0.42, 0), 1.25 + 0.9 * u, 0.9 - 1.6 * u, 0.1 + 0.25 * u), (0, 0.42, 0), fov=36, dof=4,
                focus=1.25 + 0.9 * u)
        belief = 0.7 + 1.8 * ramp(t, 102.5, 104.4)
        return Frame(c, bg=merge(A.stars.at(t), A.neb_dawn.at(t, gain=0.15), A.cup.at(t, cam_pos=c.eye, gain=belief), fish,
                                 trail_ring((0, 0.42, 0), 0.14, t, 1.6, length=2.5, gain=0.4)), bg_dof=1.0)

    # --- 104.80 someone lifts the cup up (beam of light) ---
    def lift(self, t, ctx):
        A = self.A
        rise = smoother((t - 108.6) / 4.5) * 9.0
        T = np.array([0.0, rise, 0.0])
        fp, fd = circle_path(t, center=(0, 0.42 + rise, 0), radius=0.13, omega=1.4)
        fish = A.fish.at(t, pos=fp, heading=fd, scale=0.22, gain=1.4)
        beam_on = ramp(t, 105.2, 106.6)
        eye = kf(t, [(104.8, (0.6, 0.6, 2.4)), (108.6, (0.8, 0.9, 2.8)), (113.1, (1.2, 9.6, 3.0))])
        tgt = T + np.array([0, 0.45, 0])
        c = cam(eye, tgt, fov=40, dof=2.5, focus=float(np.linalg.norm(eye - tgt)))
        streak = ramp(t, 109, 111) * (t - 109) * 3.0
        stars = A.stars_dense.at(t, center=(0, -streak * 5, 0))
        clouds = A.neb_dawn.at(t, gain=0.4 * ramp(t, 110.5, 112.5)) if t > 110.5 else None
        return Frame(c, bg=merge(stars, clouds, A.cup.at(t, T=T, cam_pos=c.eye, reflect=t < 108.6, gain=1.2), fish,
                                 light_beam(t, top=(0, 14, 0), bottom=(0, 0.0, 0), radius=0.7, gain=0.5 * beam_on)),
                     rays=((540, 200), 0.35 * beam_on, 0.8), bg_dof=1.0,
                     grade=dict(split_hi=(0.05, 0.02, -0.03)))

    # --- 113.10 places it into the big, open ocean ---
    def into_ocean(self, t, ctx):
        A = self.A
        land = 114.86
        yc = float(kf(t, [(113.1, 6.0), (land, 0.0)], ease=lambda x: 1 - (1 - clamp01(x)) ** 2))
        T = np.array([0.0, yc - 0.45, 0.0])
        fp, fd = circle_path(t, center=(0, yc, 0), radius=0.13, omega=1.4)
        fish = A.fish.at(t, pos=fp, heading=fd, scale=0.22, gain=1.6)
        pull = ramp(t, 115.6, 118.0)
        eye = np.array([1.6 + 6 * pull, 1.6 + 10 * pull, 4.5 + 16 * pull])
        c = cam(eye, (0, 0.3 + yc * 0.4, 0), fov=45, dof=1.5, focus=float(np.linalg.norm(eye)),
                shake=1.5 * pulse(t, land, 0.01, 0.5), t=t)
        sh = (land, 1.0) if t >= land else None
        cupp = A.cup.at(t, T=T, cam_pos=c.eye, shatter=sh, reflect=False, water=t < land)
        oc = A.ocean.at(t, cam=c, light_dir=(0.3, 0.3, -1.0), pulses=[(land, 5.0, 1.2, 1.2, 0.0, 0.0)], amp=0.35, gain=0.75, sky=1.0)
        splash = burst(t, land, center=(0, 0.1, 0), n=9000, speed=3.0, seed=6, col=(0.4, 0.85, 1.0), size=0.003, gain=0.2)
        return Frame(c, bg=merge(A.stars.at(t), A.galaxy.at(t, center=(60, 80, -400), tilt=1.1, gain=0.3), oc, cupp, fish,
                                 splash), fog=0.004, fog_color=(0.3, 0.55, 1.0), bg_dof=0.8,
                     flash=0.06 * pulse(t, land, 0.01, 0.2))

    # --- 118.00 the water goes on and on... the fish is free ---
    def on_and_on(self, t, ctx):
        A = self.A
        tt = t - 118.0
        speed = 6.0 + 10.0 * ramp(t, 119.0, 122.0)
        zc = -(tt * 6.0 + 10.0 * max(0, tt - 1.0) ** 2 * 0.5 * ramp(t, 119.0, 122.0))
        rise = ramp(t, 122.3, 126.0)
        eye = np.array([0.0, 1.2 + 5.0 * rise, zc + 6.0])
        tgt = np.array([0.0, 0.8 + 2.0 * rise, zc - 30])
        c = cam(eye, tgt, fov=50, dof=0.0)
        def zc_at(tq):
            q = tq - 118.0
            return -(q * 6.0 + 10.0 * max(0, q - 1.0) ** 2 * 0.5 * ramp(tq, 119.0, 122.0))
        pulses = [(tw, 30.0, 4.0, 2.5, 0.0, zc_at(tw)) for tw in (119.52, 120.28, 120.96, 121.64)]
        oc = A.ocean.at(t, cam=c, light_dir=(0.0, 0.18, -1.0), pulses=pulses, amp=0.7)
        # the leap: arc out of the water in front of the camera
        jt = (t - 126.4) / 1.8
        fish = None
        if 125.5 < t < 129.0:
            u = clamp01(jt)
            fpos = np.array([0.3, 0.2 + 1.9 * math.sin(u * math.pi), zc - 6.5 - 2.5 * u])
            fdir = np.array([0.1, 2.2 * math.cos(u * math.pi) * math.pi, -3.0])
            fish = A.fish.at(t, pos=fpos, heading=fdir, scale=1.5, gain=3.0, beat=9)
            trail = burst(t, 127.76, center=fpos, n=5000, speed=1.5, seed=9, col=(1.0, 0.75, 0.35), size=0.006)
        else:
            trail = None
        moon = A.galaxy.at(t, center=(-80, 110, zc - 500), tilt=1.2, gain=0.35)
        return Frame(c, bg=merge(A.stars.at(t), moon, oc, fish, trail), fog=0.005, fog_color=(0.3, 0.55, 1.0),
                     rays=(screen_of(c, (-80, 110, zc - 500))[0], 0.3, 0.8) if t > 126 else None,
                     grade=dict(exposure=1.0 + 0.15 * pulse(t, 127.76, 0.05, 1.0)))

    # --- 128.90 but it doesn't swim far: tiny circles in a huge ocean ---
    def still_circles(self, t, ctx):
        A = self.A
        om = 1.2
        fp, fd = circle_path(t, center=(0, 0.15, 0), radius=0.9, omega=om)
        fish = A.fish.at(t, pos=fp, heading=fd, scale=0.6, gain=2.0)
        h = float(kf(t, [(128.9, 30.0), (134.5, 16.0), (138.4, 12.0)]))
        c = cam((0.0, h, 0.01), (0, 0, 0), fov=40, roll=(t - 128.9) * 0.05)
        c.up = np.array([0.0, 0.0, -1.0])
        glow = 0.6 + 1.2 * ramp(t, 133.4, 134.6)
        oc = A.ocean.at(t, cam=c, light_dir=(0.0, 1.0, 0.2), amp=0.4, bio=1.5, glitter=0.3, gain=1.8, sky=2.0)
        ring = trail_ring((0, 0.15, 0), 0.9, t, om, length=5.0, gain=glow, n=2000, size=0.02)
        return Frame(c, bg=merge(oc, fish, ring), fog=0.002, fog_color=(0.3, 0.55, 1.0),
                     grade=dict(exposure=1.0 - 0.15 * ramp(t, 137.5, 138.4)))

    # --- 138.40 the cup is still in its mind (ghost cup) ---
    def ghost_cup(self, t, ctx):
        A = self.A
        fp, fd = circle_path(t, center=(0, 0.42, 0), radius=0.15, omega=1.2)
        fish = A.fish.at(t, pos=fp, heading=fd, scale=0.22, gain=1.4)
        eye = kf(t, [(138.4, (1.3, 1.5, 2.6)), (144.5, (0.7, 0.95, 2.1))])
        c = cam(eye, (0, 0.4, 0), fov=40, dof=2.5, focus=float(np.linalg.norm(eye - np.array([0, 0.4, 0]))))
        build = ramp(t, 141.5, 143.4)
        g = A.cup.at(t, cam_pos=c.eye, style='ghost', build=build, water=False, reflect=False, gain=3.0,
                     tint=(0.45, 0.7, 1.0))
        oc = A.ocean.at(t, cam=c, light_dir=(0.3, 0.3, -1.0), amp=0.25, gain=1.2, sky=1.3)
        return Frame(c, bg=merge(A.stars.at(t), oc, fish, g), fog=0.01, fog_color=(0.3, 0.55, 1.0), bg_dof=1.0,
                     grade=dict(sat=0.9))

    # --- 144.50 how many people live like that? (Brandon under a glass dome) ---
    def dome(self, t, ctx):
        A = self.A
        c = face_cam(t, dist=float(kf(t, [(144.5, 1.15), (148.9, 0.95)])), yaw=float(kf(t, [(144.5, 0.3), (148.9, 0.05)])),
                     pitch=0.06, ty=-0.03, dof=4)
        M = rot_x(math.pi)
        g = A.cup.at(t, M=M, T=(0, 0.215, -0.025), scale=0.39, cam_pos=c.eye, style='ghost', build=ramp(t, 144.6, 146.3),
                     water=False, reflect=False, gain=1.6, tint=(0.45, 0.7, 1.0))
        return Frame(c, bg=merge(A.stars.at(t), A.neb_ice.at(t, gain=0.35)), fg=g, avatar=AV('starlight', gain=1.5),
                     bg_dof=1.5)

    def crowd(self, t, ctx):
        A = self.A
        c = cam(kf(t, [(148.9, (-1.5, 1.7, 7.0)), (151.5, (1.5, 1.6, 6.0))]), (0, 1.3, -6), fov=45, dof=2.0, focus=7.0)
        parts = [A.stars.at(t, gain=0.6), A.neb_ice.at(t, gain=0.3)]
        rng = np.random.default_rng(3)
        for k in range(22):
            x = rng.uniform(-9, 9)
            z = -rng.uniform(0, 26)
            parts.append(A.person.at(0.0, pos=(x, 0, z), yaw=rng.uniform(-0.4, 0.4), scale=1.0, walk=0.0, cam_pos=c.eye,
                                     col=(0.35, 0.55, 1.0), gain=0.6))
            parts.append(A.cup.at(t, M=rot_x(math.pi), T=(x, 1.94, z), scale=0.28, cam_pos=c.eye, style='ghost', water=False,
                                  reflect=False, gain=1.2, tint=(0.45, 0.7, 1.0)))
        return Frame(c, bg=merge(*parts), fog=0.05, fog_color=(0.3, 0.5, 1.0), bg_dof=1.0)

    def they_can(self, t, ctx):
        A = self.A
        quiet = ramp(t, 157.3, 158.2) * (1 - ramp(t, 158.8, 160.0))
        c = face_cam(t, dist=float(kf(t, [(151.5, 0.75), (163.5, 0.6)])), yaw=float(kf(t, [(151.5, -0.25), (163.5, 0.15)])),
                     dof=6)
        g = A.cup.at(t, M=rot_x(math.pi), T=(0, 0.215, -0.025), scale=0.39, cam_pos=c.eye, style='ghost', water=False,
                     reflect=False, gain=1.2 + 2.5 * pulse(t, 161.7, 0.1, 1.0), tint=(0.45, 0.7, 1.0))
        return Frame(c, bg=merge(A.stars.at(t), A.neb_ice.at(t, gain=0.35)), fg=g,
                     avatar=AV('starlight', gain=1.6 * (1 - 0.55 * quiet), voice_glow=0.35 * (1 - quiet)), bg_dof=1.5)

    # --- 163.50 think about your life ---
    def your_life(self, t, ctx):
        A = self.A
        push = ramp(t, 163.5, 178.6)
        c = face_cam(t, dist=0.78 - 0.2 * push, yaw=0.25 - 0.4 * push, dof=6, pitch=0.03)
        parts = [A.stars.at(t), A.neb_cosmic.at(t, gain=0.5)]
        if t > 169.5:
            fade = ramp(t, 169.8, 171.4) * (1 - ramp(t, 176.0, 178.2))
            parts.append(A.person.at(t, pos=(0.9, -1.6, -3.0), yaw=-0.3, scale=1.0, walk=0.0, cam_pos=c.eye, col=RED,
                                     gain=0.9 * fade, dissolve=ramp(t, 176.0, 178.2)))
        return Frame(c, bg=merge(*parts), avatar=AV('starlight', gain=1.6), bg_dof=2.5, rays=((600, 520), 0.25, 0.8))

    # --- 178.60 the ocean is small? NO. ---
    def ocean_small(self, t, ctx):
        A = self.A
        if t < 180.9:
            c = face_cam(t, dist=0.62, yaw=-0.1, dof=6)
            return Frame(c, bg=merge(A.stars.at(t), A.neb_ice.at(t, gain=0.4)), avatar=AV('starlight', gain=1.6), bg_dof=1.5)
        no = 188.64
        swell = ramp(t, 184.9, 188.3)
        amp = 0.6 + 2.6 * swell - 2.0 * ramp(t, no + 0.3, no + 1.5)
        eye = np.array([0.0, 2.4 - 1.2 * swell, 10.0])
        c = cam(eye, (0, 2.5 + 2.0 * swell, -40), fov=52, shake=2.5 * pulse(t, no, 0.01, 0.6) + 0.4 * swell, t=t)
        oc = A.ocean.at(t, cam=c, light_dir=(0.0, 0.15, -1.0), amp=amp, pulses=[(no, 25.0, 6.0, 1.5, 0.0, -20.0)], bio=1.0 + 2 * pulse(t, no, 0.02, 1.5), gain=1.6)
        txt = A.text('SMALL', height=1.4, color=RED)
        f = smooth((t - 184.1) / 0.6) if t < no else 1 - smooth((t - no) / 0.3)
        word = txt.at(t, form=f, center=(0, 4.5 - 2.5 * swell, -18), gain=2.0, jitter=0.02) if t > 183.9 else None
        return Frame(c, bg=merge(A.stars.at(t), A.galaxy.at(t, center=(60, 90, -400), tilt=1.1, gain=0.3), oc, word),
                     fog=0.004, fog_color=(0.3, 0.55, 1.0), flash=0.12 * pulse(t, no, 0.01, 0.2))

    # --- 189.10 the sun is not bright? NO. ---
    def sun(self, t, ctx):
        A = self.A
        no = 196.29
        rise = ramp(t, 189.1, 192.0)
        sc = np.array([0.0, -4.0 + 12.0 * rise, -60.0])
        flare = pulse(t, no, 0.03, 1.4)
        intens = 0.45 + 0.3 * ramp(t, 192.6, 195.5) + 0.15 * flare
        c = cam((0, 2.0, 12.0), (0, 5.0, -40), fov=52, shake=2.0 * pulse(t, no, 0.01, 0.6), t=t)
        s = A.sun.at(t, center=sc, radius=3.2, gain=intens, flare=flare)
        oc = A.ocean.at(t, cam=c, light_dir=(sc - c.eye) / np.linalg.norm(sc - c.eye), amp=0.5, glitter=1.5 + 3 * flare,
                        base_col=(0.05, 0.05, 0.08), crest_col=(1.0, 0.6, 0.3), bio=0.2)
        txt = A.text('NOT BRIGHT', height=0.42, color=RED)
        f = smooth((t - 191.5) / 0.6) if t < no else 1 - smooth((t - no) / 0.25)
        word = txt.at(t, form=f, center=(0, 4.3, -8), gain=1.6, jitter=0.006) if t > 191.3 else None
        sxy, _ = screen_of(c, sc)
        return Frame(c, bg=merge(A.stars.at(t, gain=1 - rise * 0.6), oc, s, word), fog=0.003, fog_color=(0.05, 0.02, 0.02),
                     rays=(sxy, 0.45 + 0.9 * flare, 0.95), flash=0.03 * pulse(t, no, 0.01, 0.25), bloom=dict(threshold=2.0, strength=0.35),
                     grade=dict(split_hi=(0.06, 0.02, -0.04), exposure=1.0))

    # --- 196.80 the tree is ugly? NO. ---
    def tree(self, t, ctx):
        A = self.A
        no = 202.11
        grow = 0.55 + 0.37 * ramp(t, 200.3, 201.8) + 0.08 * ramp(t, no, no + 0.4)
        bloom = pulse(t, no, 0.02, 0.9)
        u = ramp(t, 196.8, 202.7)
        c = cam(orbit((0, 2.6, 0), 10.5 - 1.5 * u, -0.5 + 0.8 * u, 0.06), (0, 2.8, 0), fov=45,
                shake=2.0 * pulse(t, no, 0.01, 0.5), t=t, dof=1.0, focus=7.0)
        tr = A.tree.at(t, grow=grow, bloom=bloom, scale=1.5)
        txt = A.text('UGLY', height=0.55, color=RED)
        f = smooth((t - 199.4) / 0.5) if t < no else 1 - smooth((t - no) / 0.25)
        word = txt.at(t, form=f, center=(0, 4.6, 1.0), gain=1.5, jitter=0.01, R=rot_y(-0.5 + 0.8 * u)) if t > 199.2 else None
        hill = A.terrain.at(t, c, height=0.6, gain=0.22, hill=(0, 0, 0), hill_h=0.6)
        sparks = burst(t, no, center=(0, 3.8, 0), n=8000, speed=4.0, seed=12, col=(1.0, 0.85, 0.4), size=0.006, gain=0.2)
        return Frame(c, bg=merge(A.stars.at(t), A.neb_dawn.at(t, gain=0.2), hill, tr, word, sparks), fog=0.01,
                     fog_color=(0.3, 0.3, 0.5), flash=0.04 * pulse(t, no, 0.01, 0.2), bg_dof=1.0,
                     rays=((540, 700), 0.25 * bloom + 0.1, 0.9))

    # --- 202.70 then why? and I mean it. WHY? ---
    def why(self, t, ctx):
        A = self.A
        w1, w2 = 203.47, 205.45
        zoom = 0.2 * pulse(t, w1, 0.08, 0.9) + 0.28 * pulse(t, w2, 0.08, 1.2)
        c = face_cam(t, dist=0.75 - zoom, yaw=0.05, dof=7, shake=1.2 * pulse(t, w1, 0.01, 0.5) + 2.0 * pulse(t, w2, 0.01, 0.6))
        return Frame(c, bg=merge(A.stars.at(t), A.neb_ember.at(t, gain=0.18 + 0.25 * pulse(t, w2, 0.05, 1.0))), occl=0.97,
                     avatar=AV('ember', gain=1.6, voice_glow=0.5), rays=((540, 520), 0.3, 0.85), bg_dof=2,
                     flash=0.08 * pulse(t, w2, 0.01, 0.15), grade=dict(split_sh=(0.03, -0.01, -0.01)))

    # --- 206.40 why do you let it stop your life? four words ---
    def four_words(self, t, ctx):
        A = self.A
        c = face_cam(t, dist=float(kf(t, [(206.4, 0.9), (217.7, 0.62)])), yaw=float(kf(t, [(206.4, -0.3), (217.7, 0.0)])),
                     dof=6)
        bgp = [A.stars.at(t), A.neb_dawn.at(t, gain=0.35)]
        fgp = []
        cyaw = float(kf(t, [(206.4, -0.3), (217.7, 0.0)]))
        for k, (s, ph) in enumerate((('NOT VERY GOOD', 0.0), ('CAN\'T DO ANYTHING', 2.1), ('SMALL', 4.2))):
            ang = ph + (t - 206.4) * 0.5
            txt = A.text(s, height=0.026, color=RED)
            fade = ramp(t, 206.6, 208.0) * (1 - ramp(t, 216.8, 217.7))
            ctr = (0.42 * math.sin(ang), 0.06 * k - 0.04, 0.42 * math.cos(ang) - 0.06)
            part = txt.at(t, form=1.0, center=ctr, gain=1.2 * fade, R=rot_y(cyaw))
            (fgp if ctr[2] > 0 else bgp).append(part)
        for k, t0 in enumerate((212.07, 212.59, 213.29, 213.81)):
            if t > t0:
                p = np.array([(k - 1.5) * 0.07, 0.2, 0.15])
                fgp.append(burst(t, t0, center=p, n=800, speed=0.08, seed=20 + k, col=(1.0, 0.8, 0.4), size=0.0015, life=3.0))
        parts = bgp
        return Frame(c, bg=merge(*bgp), fg=merge(*fgp) if fgp else None, avatar=AV('gold', gain=1.6), bg_dof=1.5,
                     rays=((540, 520), 0.3, 0.8))

    # --- 217.70 JUST GO FOR IT ---
    def go_for_it(self, t, ctx):
        A = self.A
        hits = [217.88, 218.44, 218.92, 219.42]
        words = ['JUST', 'GO', 'FOR', 'IT']
        sh = sum(2.5 * pulse(t, h, 0.01, 0.35) for h in hits)
        c = cam((0, 0, 4.2), (0, 0, 0), fov=40, shake=sh, t=t)
        parts = [A.stars.at(t), A.neb_dawn.at(t, gain=0.35), A.dust_big.at(t, gain=0.15)]
        for k, (w, h) in enumerate(zip(words, hits)):
            if t < h - 0.12:
                continue
            txt = A.text(w, height=0.34, color=GOLD)
            y = 0.66 - k * 0.44
            z = float(kf(t, [(h - 0.12, 3.0), (h, 0.0)], ease=lambda x: 1 - (1 - clamp01(x)) ** 3))
            f = 1.0 - ramp(t, 221.2 + k * 0.2, 222.6 + k * 0.2)
            parts.append(txt.at(t, form=smooth((t - h + 0.12) / 0.12) * f + 0.001, center=(0, y, z), gain=1.1 + 1.2 * pulse(t, h, 0.01, 0.3),
                                jitter=0.003))
            parts.append(burst(t, h, center=(0, y, 0.1), n=3000, speed=2.0, seed=40 + k, col=(1.0, 0.75, 0.35), size=0.003))
        fl = sum(0.12 * pulse(t, h, 0.01, 0.1) for h in hits)
        return Frame(c, bg=merge(*parts), flash=fl, rays=((540, 900), 0.4, 0.8), grade=dict(exposure=1.05))

    # --- 221.00 four words. think about it. don't let your mind become a cup ---
    def dont_let(self, t, ctx):
        A = self.A
        c = face_cam(t, dist=float(kf(t, [(221.0, 1.0), (225.6, 0.8)])), yaw=float(kf(t, [(221.0, 0.35), (225.6, 0.1)])), dof=5)
        build = ramp(t, 223.7, 225.2)
        g = A.cup.at(t, M=rot_x(math.pi), T=(0, 0.215, -0.025), scale=0.39, cam_pos=c.eye, style='ghost', build=build,
                     water=False, reflect=False, gain=1.8, tint=(0.5, 0.75, 1.0))
        form = 1 - ramp(t, 221.0, 222.0)
        dust = A.dust.at(t, center=(0, 0, 0.1), cam_pos=c.eye, gain=0.8 * (1 - ramp(t, 222.5, 224.0)))
        return Frame(c, bg=merge(A.stars.at(t), A.neb_dawn.at(t, gain=0.4)), fg=merge(g, dust),
                     avatar=AV('gold', gain=1.6, dissolve=form * 0.6), bg_dof=1.5)

    # --- 225.60 your life is bigger than that (dome shatters) ---
    def bigger(self, t, ctx):
        A = self.A
        br = 227.14
        pull = smoother((t - br) / 1.6)
        c = face_cam(t, dist=0.8 + 1.4 * pull, yaw=0.1 - 0.3 * pull, pitch=0.05 + 0.1 * pull, dof=4, fov=36 + 10 * pull,
                     shake=2.5 * pulse(t, br, 0.01, 0.5))
        g = A.cup.at(t, M=rot_x(math.pi), T=(0, 0.215, -0.025), scale=0.39, cam_pos=c.eye, style='ghost', water=False,
                     reflect=False, gain=1.8, tint=(0.5, 0.75, 1.0), shatter=(br, 1.2))
        cosmos = merge(A.stars_dense.at(t, gain=0.3 + 0.3 * pull), A.neb_dawn.at(t, gain=0.3 + 0.2 * pull),
                       A.galaxy.at(t, center=(-25, 30, -140), tilt=0.9, gain=0.25 * pull))
        return Frame(c, bg=cosmos, fg=g, avatar=AV('gold', gain=1.7), flash=0.2 * pulse(t, br, 0.01, 0.2), bg_dof=1.0,
                     rays=((540, 520), 0.5 + 0.8 * pulse(t, br, 0.05, 1.5), 0.7))

    # --- 228.60 will you be able to say, I lived? ---
    def lived(self, t, ctx):
        A = self.A
        u = ramp(t, 228.6, 238.9)
        c = face_cam(t, dist=1.05 - 0.4 * u, yaw=-0.2 + 0.35 * u, pitch=0.08 - 0.05 * u, fov=40 - 4 * u, dof=4)
        glow = 1.6 + 0.6 * ramp(t, 237.0, 238.0)
        return Frame(c, bg=merge(A.stars.at(t, gain=0.8), A.neb_dawn.at(t, gain=0.3),
                                 A.galaxy.at(t, center=(-25, 30, -140), tilt=0.9, gain=0.2)),
                     avatar=AV('gold', gain=glow, aura=0.02, aura_frac=0.1), rays=((540, 460), 0.35, 0.8), bg_dof=1.0,
                     grade=dict(split_hi=(0.06, 0.025, -0.03), exposure=1.0 + 0.1 * ramp(t, 237.5, 238.3)))

    # --- 238.90 hold up before you go / think about that fish ---
    def hold_up(self, t, ctx):
        A = self.A
        if t < 240.7:
            c = face_cam(t, dist=0.65, yaw=0.05, dof=6, shake=1.0 * pulse(t, 239.06, 0.01, 0.4))
            return Frame(c, bg=merge(A.stars.at(t), A.neb_cosmic.at(t, gain=0.4)), avatar=AV('starlight', gain=1.6), bg_dof=1.5)
        fdis = 1 - smoother((t - 240.7) / 1.2)
        fish = A.fish.at(t, pos=(0, 0, 0), heading=(1, 0, 0.3), scale=0.3, gain=1.3, dissolve=fdis)
        c = cam(orbit((0, 0, 0), 1.2, -0.3 + (t - 240.7) * 0.1, 0.1), (0, 0, 0), fov=36, dof=3, focus=1.2)
        return Frame(c, bg=merge(A.stars.at(t), A.neb_cosmic.at(t, gain=0.4), fish), bg_dof=1.0)

    # --- 242.50 nine million years: star trails; the fish is gone ---
    def nine_million(self, t, ctx):
        A = self.A
        age = ramp(t, 242.8, 247.5)
        gone = ramp(t, 247.5, 249.0)
        fish = A.fish.at(t, pos=(0, 0, 0), heading=(1, 0, 0.3), scale=0.3, gain=1.3 * (1 - 0.6 * age),
                         tint=(0.6, 0.6, 0.7, 0.6 * age), dissolve=gone * 1.0, beat=6 - 4 * age)
        c = cam(orbit((0.02, 0, 0), 1.25 + 0.3 * age, -0.1 + 0.2 * age, 0.1), (0.02, 0, 0), fov=40, dof=3, focus=1.25)
        # star trails: rotate stars around the view axis, draw several time samples
        spin = (t - 242.5) ** 1.5 * 0.08
        trails = []
        for k in range(8):
            a = spin - k * 0.012 * (1 + 4 * ramp(t, 243, 246))
            R = rot_z(a)
            p, col, sz = A.stars.at(t)
            trails.append((p @ R.T, col * (0.6 * (1 - k / 8)), sz))
        return Frame(c, bg=merge(*trails, fish), bg_dof=0.5, grade=dict(sat=0.85))

    def person_gone(self, t, ctx):
        A = self.A
        c = cam((0.4, 1.3, 5.0), (0, 1.1, 0), fov=40, dof=2, focus=5.0)
        d = ramp(t, 250.6, 253.9)
        return Frame(c, bg=merge(A.stars.at(t, gain=0.6), A.person.at(t, pos=(0, 0, 0), yaw=0.2, scale=1.1, walk=0.0,
                                                                     cam_pos=c.eye, col=RED, gain=0.9, dissolve=d)))

    def not_remember(self, t, ctx):
        A = self.A
        u = ramp(t, 254.1, 267.0)
        gone = ramp(t, 267.3, 268.2)
        c = cam((-0.6 + 1.2 * u, 0.3, 4.6), (-0.3 + 0.6 * u, 0.1, -1.0), fov=45, dof=2, focus=5.0)
        fish = A.fish.at(t, pos=(-1.1 - 0.4 * u, 0.3, -1.0), heading=(1, 0, 0.2), scale=0.6, gain=0.8 * (1 - gone),
                         tint=(0.6, 0.7, 0.9, 0.8), dissolve=0.55 + 0.45 * gone, beat=2)
        per = A.person.at(t, pos=(1.3 + 0.4 * u, -0.9, -2.0), yaw=-0.4, scale=0.9, walk=0, cam_pos=c.eye, col=(0.8, 0.3, 0.3),
                          gain=0.7 * (1 - gone), dissolve=0.4 + 0.6 * gone)
        return Frame(c, bg=merge(A.stars.at(t, gain=0.6), A.neb_ice.at(t, gain=0.2), fish, per), bg_dof=1.0,
                     grade=dict(sat=0.7))

    # --- 268.30 keep on going: cosmic zoom out, warp jumps ---
    def time_scale(self, t, ctx):
        A = self.A
        u = ramp(t, 268.3, 280.5)
        jumps = [272.98, 273.9]
        kick = sum(pulse(t, j, 0.05, 0.5) for j in jumps)
        d = 4.0 * math.exp(u * 4.2)
        eye = np.array([0.3 * d, 0.15 * d, d])
        c = cam(eye, (0, 0, 0), fov=40 + 14 * kick, shake=1.0 * kick, t=t)
        pl = A.planet.at(t, radius=1.0, cam_pos=c.eye, spin=0.3 + 2.0 * u)
        gal = A.galaxy.at(t, center=(0, -30, -60), tilt=0.5, spin=0.05 + 0.6 * u, gain=0.2 + 0.8 * u)
        return Frame(c, bg=merge(A.stars_dense.at(t, center=eye * 0.9, gain=0.8), pl, gal,
                                 A.neb_cosmic.at(t, gain=0.4 * u)), flash=0.15 * kick)

    def numbers(self, t, ctx):
        A = self.A
        nums = [(280.68, '1,000,000'), (281.62, '9,000,000'), (282.88, '100,000,000'), (283.94, '1,000,000,000'),
                (284.90, '1,000,000,000,000'), (285.84, '+1,000,000,000,000')]
        c = cam((0, 0, 6.0), (0, 0, 0), fov=42, shake=0.4, t=t)
        parts = [A.stars_dense.at(t, center=(0, 0, 0), gain=0.5), A.galaxy.at(t, center=(0, -22, -120), tilt=0.7, spin=0.4, gain=0.35),
                 A.galaxy2.at(t, center=(40, 25, -160), tilt=1.2, spin=0.5, gain=0.3), A.neb_cosmic.at(t, gain=0.35)]
        for k, (t0, s) in enumerate(nums):
            dt = t - t0 + 0.25
            if dt < 0 or dt > 2.2:
                continue
            txt = A.text(s, height=0.22, color=(1.0, 0.8, 0.45) if k < 5 else (1.0, 0.55, 0.3), weight='ExtraBold')
            z = -14.0 + dt * 10.0
            parts.append(txt.at(t, form=smooth(dt / 0.35), center=(0.0, 0.45 - 0.05 * k, z), gain=1.4,
                                jitter=0.003))
        return Frame(c, bg=merge(*parts), bg_dof=0.0)

    def meaningless(self, t, ctx):
        A = self.A
        u = ramp(t, 287.0, 298.7)
        c = cam((0, 2.0 - 1.0 * u, 60 - 30 * u), (0, 0, -40), fov=45)
        gx = [A.galaxy.at(t, center=(-20, 5, -60), tilt=0.8, spin=0.2, gain=0.3),
              A.galaxy2.at(t, center=(30, -8, -110), tilt=1.3, spin=0.2, gain=0.3),
              A.galaxy2.at(t + 50, center=(-50, 25, -200), tilt=0.4, spin=0.2, gain=0.25)]
        return Frame(c, bg=merge(A.stars_dense.at(t, center=c.eye, gain=0.8 - 0.4 * u), A.neb_cosmic.at(t, gain=0.5 - 0.3 * u), *gx),
                     grade=dict(exposure=1.0 - 0.3 * ramp(t, 297.0, 298.7)))

    # --- 298.70 more time. more silence. the cup. gone. ... the hurt. gone. ---
    def gone_list(self, t, ctx):
        A = self.A
        c = cam((0, 0.4, 4.0), (0, 0.4, 0), fov=40, dof=1.5, focus=4.0)
        parts = [A.stars.at(t, gain=0.5 - 0.3 * ramp(t, 298.7, 302.0))]
        items = [(302.32, 303.34, 'cup'), (303.9, 304.56, 'water'), (305.14, 306.42, 'voices'), (306.96, 307.8, 'people'),
                 (308.34, 309.0, 'names'), (309.5, 310.7, 'hurt')]
        for (a, g, kind) in items:
            if t < a - 0.2 or t > g + 2.5:
                continue
            app = ramp(t, a - 0.2, a + 0.2)
            dis = ramp(t, g, g + 1.8)
            if kind == 'cup':
                parts.append(A.cup.at(t, T=(0, 0, 0), scale=0.8, cam_pos=c.eye, style='ghost', water=False, reflect=False,
                                      gain=1.6 * app * (1 - dis), tint=(0.6, 0.8, 1.0), shatter=(g, 0.25) if t > g else None))
            elif kind == 'water':
                rng = np.random.default_rng(5)
                p = rng.normal(0, 0.35, (6000, 3)).astype(np.float32) + np.array([0, 0.4, 0], np.float32)
                p[:, 1] += dis * 1.5 * rng.random(6000)
                col = np.tile(np.array([[0.3, 0.7, 1.0]], np.float32), (6000, 1)) * (0.5 * app * (1 - dis))
                parts.append((p, col, np.full(6000, 0.006, np.float32)))
            elif kind == 'voices':
                for k, s in enumerate(('NOT VERY GOOD', 'CAN\'T DO ANYTHING')):
                    txt = A.text(s, height=0.1, color=RED)
                    parts.append(txt.at(t, form=app * (1 - dis), center=(0, 0.6 - 0.25 * k, 0), gain=1.2 * (1 - dis)))
            elif kind == 'people':
                for k in range(3):
                    parts.append(A.person.at(0, pos=(-1.2 + 1.2 * k, -0.6, -1.0), yaw=0.0, scale=0.7, walk=0, cam_pos=c.eye,
                                             col=(0.7, 0.3, 0.3), gain=0.7 * app, dissolve=dis))
            elif kind == 'names':
                txt = A.text('?  ?  ?', height=0.25, color=(0.8, 0.8, 0.9))
                parts.append(txt.at(t, form=app * (1 - dis), center=(0, 0.4, 0), gain=1.2 * (1 - dis)))
            elif kind == 'hurt':
                txt = A.text('HURT', height=0.28, color=(1.0, 0.25, 0.3))
                parts.append(txt.at(t, form=app * (1 - dis), center=(0, 0.4, 0), gain=1.6 * (1 - dis), jitter=0.004))
        return Frame(c, bg=merge(*parts), bg_dof=0.5, grade=dict(sat=0.85))

    def heavy_nothing(self, t, ctx):
        A = self.A
        # 311.4 everything falls away; 315.1 river of time; 323.3 fade to nothing
        c = cam((0, 0.0, 6.0), (0, 0, 0), fov=45)
        fallp, fallc, falls = A.dust_big.at(t, gain=0.6 * (1 - ramp(t, 312.5, 315.5)))
        fallp = fallp.copy()
        fallp[:, 1] -= (t - 311.4) ** 2 * 0.3
        river_on = ramp(t, 315.3, 317.0) * (1 - ramp(t, 323.5, 327.0))
        rng = np.random.default_rng(8)
        n = 20000
        base = rng.random(n).astype(np.float32)
        x = ((base * 30 + t * 1.2) % 30) - 15
        y = np.sin(x * 0.3 + rng.random(n) * 0.5) * 0.6 + rng.normal(0, 0.25, n)
        z = rng.normal(0, 1.2, n) - 2
        river = (np.stack([x, y, z], -1).astype(np.float32),
                 (palette('ice', 0.5 + 0.5 * rng.random(n)) * (0.25 * river_on)).astype(np.float32),
                 np.full(n, 0.008, np.float32))
        stars_g = 0.5 * (1 - ramp(t, 324.0, 328.0))
        return Frame(c, bg=merge(A.stars.at(t, gain=stars_g), (fallp, fallc, falls), river),
                     grade=dict(exposure=1.0 - ramp(t, 326.5, 328.3)))

    # --- 329.00 so let me ask you something... ---
    def final_q(self, t, ctx):
        A = self.A
        form = 1 - smoother((t - 329.1) / 1.8)
        c = face_cam(t, dist=float(kf(t, [(329.0, 1.1), (338.0, 0.75), (345.5, 0.55)])),
                     yaw=float(kf(t, [(329.0, -0.3), (345.5, 0.1)])), dof=5)
        starsg = 0.2 + 0.8 * ramp(t, 338.5, 342.0)
        parts = [A.stars.at(t, gain=starsg), A.stars_dense.at(t, gain=0.6 * ramp(t, 338.5, 342.5)),
                 A.neb_cosmic.at(t, gain=0.35 * ramp(t, 330.0, 334.0))]
        fg = []
        if 331.0 < t < 339.0:
            fade = ramp(t, 331.0, 332.2) * (1 - ramp(t, 336.3, 338.5))
            ang = (t - 331) * 0.7
            fp = np.array([0.32 * math.sin(ang), 0.05, 0.32 * math.cos(ang)])
            fd = np.array([math.cos(ang), 0, -math.sin(ang)])
            fg.append(A.fish.at(t, pos=fp, heading=fd, scale=0.1, gain=0.8 * fade, dissolve=ramp(t, 336.3, 338.5)))
            fg.append(A.person.at(0, pos=(-0.3 * math.sin(ang), -0.25, -0.3 * math.cos(ang) - 0.2), yaw=0, scale=0.18,
                                  walk=0, cam_pos=c.eye, col=(0.8, 0.3, 0.3), gain=0.6 * fade, dissolve=ramp(t, 336.3, 338.5)))
        spark = np.array([[0.0, 0.0, 0.0]], np.float32)
        return Frame(c, bg=merge(*parts), fg=merge(*fg) if fg else None,
                     avatar=AV('starlight', gain=1.6, dissolve=form, lift=0.3, spread=0.3),
                     bg_dof=1.5, grade=dict(exposure=0.2 + 0.8 * ramp(t, 329.0, 330.0)))

    def final(self, t, ctx):
        A = self.A
        pull = smoother((t - 354.9) / 3.0)
        dist = 0.55 + 0.1 * ramp(t, 345.5, 354.9) + 9.0 * pull ** 2
        c = face_cam(t, dist=dist, yaw=0.1 - 0.4 * pull, pitch=0.03 + 0.25 * pull, fov=36 + 12 * pull, dof=5 * (1 - pull))
        # the small moment: a spark in front of him
        sp_on = ramp(t, 346.5, 347.5) * (1 - ramp(t, 355.0, 356.5))
        red = pulse(t, 352.0, 0.2, 0.8)
        tick = pulse(t, 350.2, 0.05, 0.4)
        spark_c = np.array([1.0 - 0.0 * red, 0.8 - 0.55 * red, 0.45 - 0.3 * red], np.float32)
        rng = np.random.default_rng(2)
        sp = rng.normal(0, 0.0025, (300, 3)).astype(np.float32) + np.array([0.075, -0.06, 0.2], np.float32)
        spark = (sp, np.tile(spark_c * (0.5 + 0.8 * tick) * sp_on, (300, 1)).astype(np.float32), np.full(300, 0.0004, np.float32))
        cosmos = merge(A.stars_dense.at(t, gain=0.35 + 0.25 * pull), A.neb_dawn.at(t, gain=0.35 + 0.25 * pull),
                       A.galaxy.at(t, center=(-25, 30, -140), tilt=0.9, gain=0.15 + 0.3 * pull))
        return Frame(c, bg=cosmos, fg=spark, avatar=AV('starlight', gain=1.6 * min(1.0, (0.7 / dist) ** 1.6),
                                                       dissolve=0.55 * pull, lift=0.5, spread=0.6), bg_dof=1.5,
                     rays=((540, 520), 0.3 + 0.4 * pull, 0.7), grade=dict(split_hi=(0.05, 0.02, -0.03)))

    def end_card(self, t, ctx):
        A = self.A
        c = cam((0, 0, 5.0), (0, 0, 0), fov=40)
        f = smoother((t - 357.6) / 2.2)
        logo = A.text('ECHOES', height=0.3, color=(1.0, 0.8, 0.5), font='/opt/fonts/Cinzel.ttf', weight='Bold')
        logo2 = A.text('IN THE DARK', height=0.11, color=(0.7, 0.8, 1.0), font='/opt/fonts/Cinzel.ttf', weight='Regular')
        out = 1 - ramp(t, 363.4, 364.9)
        return Frame(c, bg=merge(A.stars_dense.at(t, gain=0.45 * out), A.neb_cosmic.at(t, gain=0.3 * out),
                                 logo.at(t, form=f, center=(0, 0.2, 0), gain=1.3 * out, jitter=0.002),
                                 logo2.at(t, form=smoother((t - 358.4) / 2.0), center=(0, -0.08, 0), gain=1.2 * out)),
                     rays=((540, 860), 0.3 * out, 0.8), grade=dict(exposure=out + 0.001))


def build_timeline(S):
    """(t_start, shot_fn, transition_in) in order; shot runs until the next start."""
    return [
        (0.00, S.intro, None),
        (8.60, S.fish_reveal, None),
        (11.70, S.cup_intro, ('cross', 0.5)),
        (19.30, S.ocean_glimpse, ('flash', 0.4)),
        (27.60, S.cup_confined, ('flash', 0.4)),
        (39.90, S.hits_glass, ('cross', 0.4)),
        (53.40, S.same_circles, ('cross', 0.5)),
        (58.60, S.stops_trying, ('fade', 0.6)),
        (71.40, S.inner_voice, ('cross', 0.8)),
        (77.00, S.people, ('fade', 0.5)),
        (87.10, S.ask, ('cross', 0.3)),
        (89.40, S.words_shatter, ('cross', 0.3)),
        (97.50, S.still_fish, ('cross', 0.5)),
        (104.80, S.lift, ('cross', 0.6)),
        (113.10, S.into_ocean, ('cross', 0.5)),
        (118.00, S.on_and_on, ('flash', 0.4)),
        (128.90, S.still_circles, ('fade', 0.6)),
        (138.40, S.ghost_cup, ('cross', 0.6)),
        (144.50, S.dome, ('cross', 0.6)),
        (148.90, S.crowd, ('cross', 0.5)),
        (151.50, S.they_can, ('cross', 0.5)),
        (163.50, S.your_life, ('cross', 0.6)),
        (178.60, S.ocean_small, ('cross', 0.4)),
        (189.10, S.sun, ('flash', 0.3)),
        (196.80, S.tree, ('flash', 0.3)),
        (202.70, S.why, ('flash', 0.25)),
        (206.40, S.four_words, ('cross', 0.5)),
        (217.70, S.go_for_it, ('cross', 0.2)),
        (221.00, S.dont_let, ('cross', 0.6)),
        (225.60, S.bigger, None),
        (228.60, S.lived, ('cross', 0.6)),
        (238.90, S.hold_up, ('flash', 0.3)),
        (242.50, S.nine_million, ('cross', 0.5)),
        (249.20, S.person_gone, ('cross', 0.8)),
        (254.10, S.not_remember, ('cross', 0.8)),
        (268.30, S.time_scale, ('fade', 0.5)),
        (280.50, S.numbers, ('flash', 0.3)),
        (287.00, S.meaningless, ('cross', 0.8)),
        (298.70, S.gone_list, ('cross', 1.0)),
        (311.40, S.heavy_nothing, ('cross', 0.8)),
        (329.00, S.final_q, None),
        (345.50, S.final, None),
        (357.40, S.end_card, ('cross', 0.8)),
    ]


KEYWORDS = ['fish', 'cup', 'ocean', 'free', 'mind', 'smaller', 'born', 'believes', 'sun', 'shining', 'tree', 'growing',
            'why', 'why?', 'just', 'go', 'for', 'it', 'bigger', 'lived', 'gone', 'nothing', 'million', 'billion',
            'trillion', 'time', 'silence', 'moment', 'opinion', 'biggest', 'life', 'no', 'wall', 'glass', 'stops',
            'quiet', 'think', 'hurt', 'never', 'forgets', 'listen', 'heavy', 'years']


def key_filter(words):
    """Only highlight keywords where they carry meaning (e.g. 'just go for it', not every 'just')."""
    out = []
    for i, w in enumerate(words):
        c = w['w'].strip('.,!?;:"\'').lower()
        k = c in KEYWORDS
        if c in ('just', 'go', 'for', 'it'):
            k = 217.5 < w['s'] < 219.8
        if c == 'fish':
            k = w['s'] < 12.0 or 97 < w['s'] < 100 or 126 < w['s'] < 128
        if c in ('time', 'years', 'life'):
            k = c == 'life' and w['s'] > 225 or c == 'time' and w['s'] > 296 or c == 'years' and 242 < w['s'] < 245
        if c == 'no':
            k = True
        w = dict(w)
        w['key'] = k
        out.append(w)
    return out
