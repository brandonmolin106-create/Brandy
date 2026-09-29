"""Full soundtrack for "The Fish in the Cup": voice FX, score, ambience, SFX, mix + master.

usage: python soundtrack.py WORK OUT.wav
Everything except Brandon's voice is synthesized here (no samples, no licensed music).
"""
import math
import sys

import numpy as np
import soundfile as sf
from pedalboard import (Chorus, Compressor, Gain, HighpassFilter, HighShelfFilter, LowpassFilter, PeakFilter,
                        Pedalboard, Reverb)
from scipy import signal

import sfx as S
from audio_post import (curve, duck, echo_throws, envelope, load_vocal, master, octave_double, reverb_send,
                        vocal_chain)
from sfx import SR, secs

DUR = 365.0
N = secs(DUR)


def bus():
    return np.zeros((N + secs(8), 2), np.float32)


def place(b, x, t, gain=1.0, pan=None):
    """Mix stereo (or mono) x into bus b at time t (seconds)."""
    if x.ndim == 1:
        x = np.stack([x, x], -1)
    if pan is not None:
        m = x.mean(1)
        x = S.pan(m, pan) * 1.2
    s0 = secs(t)
    if s0 < 0:
        x = x[-s0:]
        s0 = 0
    s1 = min(len(b), s0 + len(x))
    if s1 > s0:
        b[s0:s1] += x[: s1 - s0] * gain


def db(x):
    return 10 ** (x / 20.0)


# ------------------------------------------------------------------ voice

def voice_layers(work):
    v = load_vocal(f'{work}/sep/htdemucs_ft/audio_src/vocals.wav')
    v = vocal_chain(v)
    v = np.concatenate([v, np.zeros(max(0, N - len(v)), np.float32)])[:N]
    n = len(v)
    dry = np.stack([v, v], -1)

    # emotion-driven reverb sends: (time, send) keyframes per space
    hall = curve([(0, 0.10), (7.6, 0.12), (8.4, 0.3), (9.5, 0.16), (40, 0.14), (53.4, 0.16), (58.5, 0.14), (60.5, 0.24),
                  (71.2, 0.3), (75.5, 0.32), (75.8, 0.06), (77.0, 0.14), (87.0, 0.08), (89.4, 0.14), (104.8, 0.2),
                  (118.0, 0.28), (127.5, 0.36), (129.0, 0.2), (138.5, 0.26), (144.4, 0.3), (144.6, 0.07), (178.5, 0.08),
                  (181.0, 0.22), (202.5, 0.24), (206.3, 0.12), (221.0, 0.16), (228.6, 0.24), (238.4, 0.34),
                  (238.9, 0.04), (241.5, 0.14), (242.5, 0.3), (268.3, 0.34), (298.7, 0.38), (322.0, 0.42),
                  (329.0, 0.1), (345.0, 0.14), (354.5, 0.3), (357.5, 0.34)], n)
    cath = curve([(0, 0.0), (58.5, 0.0), (60.0, 0.08), (75.5, 0.12), (76.0, 0.0), (91.8, 0.0), (92.0, 0.5), (92.8, 0.0),
                  (96.8, 0.0), (97.0, 0.55), (97.8, 0.0), (127.4, 0.0), (127.8, 0.4), (128.6, 0.05), (142.5, 0.1),
                  (144.3, 0.35), (144.7, 0.0), (188.5, 0.0), (188.7, 0.55), (189.3, 0.0), (196.2, 0.0), (196.35, 0.55),
                  (197.0, 0.0), (202.0, 0.0), (202.15, 0.55), (202.8, 0.0), (203.3, 0.0), (203.5, 0.5), (204.0, 0.05),
                  (205.3, 0.05), (205.5, 0.8), (206.2, 0.0), (219.3, 0.0), (219.5, 0.5), (220.2, 0.0), (227.0, 0.1),
                  (227.8, 0.45), (228.4, 0.1), (237.4, 0.2), (238.0, 0.7), (238.7, 0.0), (266.0, 0.2), (268.2, 0.5),
                  (268.6, 0.1), (298.7, 0.2), (311.0, 0.3), (327.0, 0.55), (328.9, 0.0), (356.5, 0.2), (357.3, 0.6),
                  (358.0, 0.0)], n, smooth=0.03)
    wet = reverb_send(v, hall, 'hall', pre_delay=0.03, hp=220, tail=6.0)[:len(dry)] * 0.9
    wet2 = reverb_send(v, cath, 'cathedral', pre_delay=0.05, hp=300, tail=8.0)[:len(dry)] * 1.0

    throws = [(8.10, 8.62, 0.55, 1), (10.9, 11.4, 0.3, -1), (43.2, 43.7, 0.35, 1), (53.15, 53.6, 0.4, -1),
              (56.8, 57.4, 0.35, 1), (70.95, 71.5, 0.4, -1), (74.95, 75.5, 0.5, 1), (86.45, 87.0, 0.35, -1),
              (91.9, 92.35, 0.6, 1), (96.9, 97.3, 0.6, -1), (127.7, 128.3, 0.55, 1), (144.1, 144.6, 0.6, -1),
              (157.75, 158.3, 0.45, 1), (174.5, 175.0, 0.4, -1), (188.6, 189.0, 0.6, 1), (196.25, 196.7, 0.6, -1),
              (202.05, 202.5, 0.6, 1), (203.4, 203.9, 0.55, -1), (205.4, 205.95, 0.8, 1), (210.7, 211.2, 0.4, -1),
              (219.4, 219.9, 0.55, 1), (227.7, 228.2, 0.45, -1), (237.95, 238.6, 0.75, 1), (248.0, 248.5, 0.45, -1),
              (251.3, 251.8, 0.35, 1), (266.15, 266.6, 0.4, -1), (268.0, 268.5, 0.6, 1), (286.5, 287.0, 0.45, -1),
              (299.45, 300.0, 0.4, 1), (303.3, 303.7, 0.5, -1), (304.5, 304.95, 0.5, 1), (306.35, 306.8, 0.5, -1),
              (307.75, 308.2, 0.5, 1), (308.95, 309.4, 0.5, -1), (310.65, 311.1, 0.55, 1), (315.1, 315.6, 0.45, -1),
              (327.25, 327.8, 0.55, 1), (328.3, 328.9, 0.6, -1), (344.8, 345.4, 0.45, 1), (357.15, 357.8, 0.7, -1)]
    ech = echo_throws(v, throws, bpm_delay=0.43, feedback=0.5, tail=6.0)[:len(dry)] * 0.75

    gate = curve([(0, 0), (203.3, 0), (203.4, 1), (204.0, 1), (204.1, 0), (205.3, 0), (205.4, 1), (206.0, 1), (206.1, 0),
                  (217.8, 0), (217.85, 1), (219.9, 1), (220.0, 0), (225.7, 0), (225.75, 1), (227.9, 1), (228.0, 0),
                  (237.5, 0), (237.55, 1), (238.4, 1), (238.5, 0), (267.2, 0), (267.25, 1), (268.2, 1), (268.3, 0)], n,
                 smooth=0.02)
    octv = octave_double(v, gate, amount=0.35)
    octs = np.stack([octv, octv], -1)

    L = min(len(dry), len(wet), len(wet2), len(ech))
    vox = dry[:L] + wet[:L] + wet2[:L] + ech[:L] + octs[:L]
    return v, vox


# ------------------------------------------------------------------ score

D3, F3, A3, D4, F4, A4 = 50, 53, 57, 62, 65, 69
CH = {
    'Dm': [38, 50, 57, 62, 65], 'Bb': [34, 46, 53, 58, 62], 'F': [41, 53, 57, 60, 65], 'C': [36, 48, 55, 60, 64],
    'Gm': [43, 50, 55, 58, 62], 'A': [45, 52, 57, 61, 64], 'Asus': [45, 52, 57, 62, 64], 'Dsus2': [38, 50, 57, 62, 64],
    'D': [38, 50, 57, 62, 66], 'Gm6': [43, 50, 55, 58, 64], 'Bbmaj7': [34, 46, 53, 57, 62], 'Fadd9': [41, 53, 57, 60, 67],
}


def score(voice):
    mus = bus()
    # chord plan: (t0, t1, chord, brightness, gain)
    plan = [
        (0.0, 8.6, 'Dsus2', 0.25, 0.7), (8.6, 19.3, 'Dm', 0.3, 0.8), (19.3, 27.6, 'Fadd9', 0.45, 0.9), (27.6, 34.0, 'Bb', 0.3, 0.8),
        (34.0, 40.0, 'Gm', 0.3, 0.8), (40.0, 48.0, 'Dm', 0.35, 0.85), (48.0, 53.4, 'C', 0.4, 0.9), (53.4, 58.6, 'Dm', 0.3, 0.8),
        (60.5, 71.4, 'Gm6', 0.18, 0.7), (71.4, 77.0, 'Dm', 0.15, 0.6), (77.0, 87.1, 'Gm', 0.2, 0.7),
        (87.1, 92.0, 'Bb', 0.3, 0.8), (92.0, 97.0, 'F', 0.4, 0.85), (97.0, 104.8, 'C', 0.45, 0.9),
        (104.8, 113.1, 'Bbmaj7', 0.45, 0.9), (113.1, 118.0, 'F', 0.55, 1.0), (118.0, 128.9, 'Fadd9', 0.65, 1.1),
        (128.9, 138.4, 'Dm', 0.2, 0.7), (138.4, 144.5, 'Gm6', 0.2, 0.7), (144.5, 157.0, 'Dm', 0.18, 0.65),
        (158.2, 163.5, 'Bb', 0.2, 0.65), (163.5, 178.6, 'Gm', 0.22, 0.7),
        (178.6, 189.1, 'Dm', 0.4, 0.85), (189.1, 196.8, 'F', 0.5, 0.95), (196.8, 202.7, 'C', 0.5, 0.95),
        (202.7, 206.4, 'Dm', 0.5, 1.0), (206.4, 217.7, 'Bb', 0.45, 0.9), (217.7, 221.0, 'F', 0.7, 1.1),
        (221.0, 225.6, 'Gm', 0.4, 0.9), (225.6, 228.6, 'Bb', 0.6, 1.0), (228.6, 233.4, 'F', 0.6, 1.05),
        (233.4, 238.9, 'D', 0.65, 1.1),
        (240.7, 254.0, 'Dsus2', 0.3, 0.8), (254.0, 268.3, 'Asus', 0.25, 0.7), (268.3, 280.5, 'Dsus2', 0.4, 0.9),
        (280.5, 287.0, 'Fadd9', 0.5, 0.95), (287.0, 298.7, 'Bbmaj7', 0.35, 0.8), (298.7, 311.4, 'Dsus2', 0.15, 0.55),
        (311.4, 323.3, 'Asus', 0.1, 0.4),
        (330.5, 338.5, 'Dm', 0.2, 0.6), (338.5, 345.5, 'Bbmaj7', 0.25, 0.65), (345.5, 350.5, 'Gm', 0.25, 0.65),
        (350.5, 354.9, 'Asus', 0.3, 0.7), (354.9, 365.0, 'D', 0.55, 1.0),
    ]
    for (a, b, ch, br, g) in plan:
        notes = CH[ch][1:]
        p = S.pad(notes, dur=b - a + 3.0, bright=br, attack=min(2.5, (b - a) / 2), release=3.0, seed=int(a))
        place(mus, p, a - 0.5, gain=0.5 * g)
        # sub root
        root = S.midi(CH[ch][0])
        n = secs(b - a + 2.5)
        tt = np.arange(n, dtype=np.float32) / SR
        sub = np.sin(2 * np.pi * root * tt) * np.minimum(1, tt / 1.5) * np.minimum(1, (n - np.arange(n)) / secs(2.0))
        place(mus, sub.astype(np.float32), a - 0.3, gain=0.18 * g)

    # the Echoes motif on felt piano (A4 D5 F5 E5 . D5) at key moments
    motif = [(0.0, 69, 0.55), (0.62, 74, 0.6), (1.24, 77, 0.65), (1.86, 76, 0.6), (3.1, 74, 0.5)]
    for t0 in (9.0, 13.2, 29.0, 98.0, 129.4, 146.8, 241.0, 331.0, 346.0, 358.0):
        for (dt, m, vel) in motif:
            place(mus, S.felt_piano(m, dur=4.5, vel=vel), t0 + dt, gain=0.55)
            place(mus, S.felt_piano(m - 12, dur=4.0, vel=vel * 0.5), t0 + dt, gain=0.25)
    # sparse piano notes in the reflective sections
    rng = np.random.default_rng(3)
    for (a, b, pool) in ((60.5, 77.0, [62, 65, 69, 67]), (128.9, 144.0, [62, 69, 65, 70]), (163.5, 178.0, [62, 65, 67, 70]),
                         (254.0, 267.0, [69, 76, 74, 71]), (298.7, 322.0, [74, 69, 76])):
        t = a
        while t < b:
            m = int(rng.choice(pool))
            place(mus, S.felt_piano(m, dur=5.0, vel=0.35 + 0.2 * rng.random()), t, gain=0.4)
            t += rng.uniform(2.2, 3.8)

    # strings swells and choir at the emotional peaks
    for (a, b, ch, g) in ((92.0, 104.8, 'F', 0.5), (113.1, 128.9, 'Fadd9', 0.7), (189.1, 202.7, 'F', 0.55),
                          (217.7, 221.5, 'F', 0.8), (225.6, 238.9, 'D', 0.9), (280.5, 298.7, 'Fadd9', 0.45),
                          (354.9, 365.0, 'D', 0.85)):
        st = S.strings(CH[ch][1:4], dur=b - a + 2.0, seed=int(a), bright=0.6)
        place(mus, st, a, gain=0.55 * g)
    for (a, b, ch, g, vw) in ((104.8, 113.1, 'Bbmaj7', 0.4, 'oo'), (118.0, 128.9, 'Fadd9', 0.6, 'ah'),
                              (227.0, 238.9, 'D', 0.7, 'ah'), (242.5, 268.3, 'Dsus2', 0.35, 'oo'),
                              (268.3, 298.7, 'Dsus2', 0.4, 'oo'), (354.9, 365.0, 'D', 0.6, 'ah')):
        place(mus, S.choir(CH[ch][1:4], dur=b - a + 2.0, seed=int(a) + 1, vowel=vw), a, gain=0.5 * g)

    # heartbeat / pulse building into "just go for it"
    place(mus, S.heartbeat(bpm=64, beats=11), 206.6, gain=0.45)
    place(mus, S.heartbeat(bpm=78, beats=4), 214.2, gain=0.55)
    place(mus, S.heartbeat(bpm=58, beats=6), 77.2, gain=0.3)

    # tape stop at "Hold up" (238.9 -> 239.2): slow the whole music bus down to a halt
    a, b = secs(238.55), secs(239.15)
    seg = mus[a - secs(0.6):b + secs(0.6)].copy()
    L = b - a
    speed = np.linspace(1.0, 0.0, L) ** 1.4
    ph = np.cumsum(speed)
    src = np.clip(ph + secs(0.6), 0, len(seg) - 1)
    for c in range(2):
        mus[a:b, c] = np.interp(src, np.arange(len(seg)), seg[:, c]) * np.linspace(1, 0.2, L)
    mus[b:secs(240.6)] *= 0.0

    # music space
    mus = S.fx(mus, HighpassFilter(cutoff_frequency_hz=35), Reverb(room_size=0.85, wet_level=0.35, dry_level=0.8,
                                                                  damping=0.4, width=1.0))
    return mus


# ------------------------------------------------------------------ ambience + sfx

def sfx_track():
    fx = bus()
    amb = bus()

    def a_(x, t, g=1.0, pan=None):
        place(amb, x, t, g, pan)

    def f_(x, t, g=1.0, pan=None):
        place(fx, x, t, g, pan)

    # space drone bed (whole piece, varying)
    n = N
    tt = np.arange(n, dtype=np.float32) / SR
    drone = (np.sin(2 * np.pi * 36.7 * tt) * 0.5 + np.sin(2 * np.pi * 55.0 * tt + 1) * 0.3).astype(np.float32)
    drone *= (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * tt)).astype(np.float32)
    lvl = curve([(0, 0.5), (8, 0.35), (58.6, 0.5), (77, 0.35), (104.8, 0.2), (129, 0.4), (178, 0.3), (238.9, 0.0),
                 (240.7, 0.5), (298.7, 0.35), (323, 0.15), (327.2, 0.0), (329.2, 0.0), (331, 0.3), (365, 0.3)], n)
    a_(np.stack([drone * lvl, drone * lvl], -1), 0.0, 0.25)
    # cosmic wind in the space sections
    for (a, b, g) in ((0, 12, 0.25), (242.5, 300, 0.3), (329, 365, 0.2)):
        a_(S.wind(b - a, seed=int(a), bright=600), a, g)
    # water inside the cup: muffled bubbles
    for (a, b) in ((11.7, 19.3), (27.6, 58.6), (58.6, 71.4), (77.0, 87.1), (89.4, 113.0)):
        nb_ = secs(b - a)
        bub = np.zeros(nb_, np.float32)
        rng = np.random.default_rng(int(a))
        for _ in range(int((b - a) * 2.5)):
            s0 = int(rng.integers(0, nb_ - secs(0.2)))
            L = secs(rng.uniform(0.03, 0.09))
            f0 = rng.uniform(300, 900)
            x = np.arange(L) / SR
            bub[s0:s0 + L] += np.sin(2 * np.pi * (f0 + 2000 * x) * x) * np.exp(-x / 0.02) * rng.uniform(0.2, 1)
        bub = S.svf(bub, np.full(nb_, 1400, np.float32), 0.7, 0)
        room = S.svf(S.noise(nb_, 'brown', int(a)), np.full(nb_, 220, np.float32), 0.7, 0) * 0.5
        x = S.widen((bub * 0.5 + room).astype(np.float32), 0.6, int(a)) * S.env_ar(nb_, 0.1, 0.1)[:, None]
        a_(x, a, 0.25)
    # ocean
    for (a, b, g) in ((19.3, 27.6, 0.55), (113.0, 128.9, 0.7), (128.9, 144.5, 0.45), (178.6, 196.8, 0.6)):
        a_(S.ocean(b - a, period=7.0, seed=int(a)), a, g)
        a_(S.wind(b - a, seed=int(a) + 5, bright=1100), a, g * 0.35)
    # tree hill wind + leaves
    a_(S.wind(6.2, seed=196, bright=1600), 196.8, 0.35)
    a_(S.rain(6.0, seed=197, intensity=0.25), 196.8, 0.12)
    # people: crowd murmur (formant-filtered noise) + footsteps
    nmur = secs(10.1)
    mur = np.zeros(nmur, np.float32)
    rng = np.random.default_rng(77)
    for _ in range(26):
        s0 = int(rng.integers(0, nmur - secs(1.2)))
        L = secs(rng.uniform(0.4, 1.1))
        src = S.noise(L, 'pink') * S.env_ar(L, 0.2, 0.3)
        f1 = rng.uniform(400, 900)
        y = S.svf(src, np.full(L, f1, np.float32), 5.0, 1) + S.svf(src, np.full(L, f1 * 2.4, np.float32), 6.0, 1) * 0.5
        mur[s0:s0 + L] += y * rng.uniform(0.3, 1.0)
    a_(S.widen(S.svf(mur, np.full(nmur, 1500, np.float32), 0.7, 0), 1.0, 3), 77.0, 0.6)
    for k in range(18):
        f_(S.fx(np.stack([S.heartbeat(bpm=200, beats=1)[:, 0]] * 2, -1), LowpassFilter(cutoff_frequency_hz=180)),
           77.4 + k * 0.55, 0.22, pan=math.sin(k * 0.7) * 0.6)
    # crowd shot / river of time
    a_(S.wind(3.0, seed=149, bright=500), 148.9, 0.3)
    nr = secs(8.0)
    river = S.svf(S.noise(nr, 'pink', 315), np.full(nr, 900, np.float32), 1.0, 1)
    pan_ = np.sin(np.linspace(0, 6, nr)).astype(np.float32) * 0.7
    a_(S.pan(river * S.env_ar(nr, 0.3, 0.4), pan_), 315.2, 0.25)

    # ---------------- SFX cues
    f_(S.sub_drop(2.5, 70, 25), 0.0, 0.5)
    f_(S.shimmer(2.2, seed=1), 0.1, 0.35)
    f_(S.reverse_swell(1.2, seed=2), 7.5, 0.35)
    f_(S.whoosh(1.4, -0.6, 0.6, seed=3), 8.4, 0.45)
    f_(S.shimmer(1.8, seed=4, fmin=1800, fmax=6000), 8.9, 0.35)
    f_(S.whoosh(1.0, 0.5, -0.5, seed=5), 11.3, 0.25)
    # glass forms: crystal tones rising
    for k, m in enumerate([81, 84, 88, 91, 93]):
        n2 = secs(3.0)
        x = np.arange(n2) / SR
        tone = np.sin(2 * np.pi * S.midi(m) * x) * np.exp(-x / 1.2) * np.minimum(1, x / 0.01)
        f_(tone.astype(np.float32), 15.2 + k * 0.55, 0.12, pan=(k - 2) * 0.3)
    f_(S.whoosh(0.9, -0.3, 0.8, seed=6, fpk=4000), 18.9, 0.45)
    for k, tw in enumerate((22.25, 23.11, 23.83)):
        f_(S.whoosh(0.8, -0.4 + 0.4 * k, 0.4, seed=10 + k, f0=150, fpk=1500, f1=300), tw - 0.35, 0.35)
    f_(S.whoosh(0.9, 0.7, -0.4, seed=13), 27.2, 0.45)

    def glass_hit(t, g=1.0, p=0.0):
        f_(S.impact(size=0.5, tone=70, seed=int(t), metal=0.9, tail_s=2.0), t, 0.45 * g, pan=p)
        n2 = secs(2.5)
        x = np.arange(n2) / SR
        ring = sum(np.sin(2 * np.pi * f * x + k) * np.exp(-x / d) / (k + 1)
                   for k, (f, d) in enumerate([(1320, 1.4), (2090, 1.0), (3170, 0.7), (4410, 0.5)]))
        f_(S.verb(S.pan(ring.astype(np.float32), p), room=0.5, wet=0.3), t, 0.2 * g)

    glass_hit(41.88, 1.0, 0.3)
    f_(S.sub_drop(1.5, 60, 30), 42.9, 0.3)
    glass_hit(46.80, 1.0, -0.3)
    # day after day...: clock accelerating
    t = 48.0
    per = 0.6
    k = 0
    while t < 53.4:
        f_(S.tick(k % 2 == 1), t, 0.35, pan=0.3 if k % 2 else -0.3)
        t += per
        per = max(0.07, per * 0.9)
        k += 1
    for tw in (48.3, 50.1, 52.4):
        f_(S.whoosh(1.1, -0.8, 0.8, seed=int(tw * 10), fpk=2500), tw - 0.3, 0.3)
    # the same circles: swirling pan synced with the fish orbit (omega 4.5 rad/s)
    ns = secs(5.2)
    x = np.arange(ns) / SR
    swirl = S.svf(S.noise(ns, 'pink', 53), (900 + 500 * np.sin(4.5 * x)).astype(np.float32), 2.0, 1)
    f_(S.pan(swirl * S.env_ar(ns, 0.2, 0.3), np.sin(4.5 * x + 3.14)), 53.4, 0.18)
    # something happens
    f_(S.sub_drop(2.8, 55, 22), 59.5, 0.55)
    f_(S.reverse_swell(1.4, freqs=(73.4, 110.0, 146.8), seed=60), 58.3, 0.3)
    n2 = secs(3.0)
    x = np.arange(n2) / SR
    down = np.sin(2 * np.pi * np.cumsum(880 * np.exp(-x / 1.2)) / SR) * np.exp(-x / 1.5) * 0.3
    f_(S.verb(S.pan(down.astype(np.float32), 0.0), room=0.8, wet=0.5), 60.6, 0.25)
    # barrier glow: glassy sustained tone
    n2 = secs(2.4)
    x = np.arange(n2) / SR
    bar = (np.sin(2 * np.pi * 1760 * x) + np.sin(2 * np.pi * 1763 * x)) * S.env_ar(n2, 0.4, 0.4) * 0.2
    f_(S.pan(bar.astype(np.float32), 0.0), 69.4, 0.2)
    f_(S.reverse_swell(1.2, seed=71), 70.4, 0.3)
    f_(S.sub_drop(1.8, 50, 25), 75.85, 0.45)
    f_(S.whoosh(1.0, 0.5, -0.5, seed=77), 76.6, 0.3)
    # judgments appear: dark glitch stabs
    for tw in (81.48, 84.18, 86.36):
        f_(S.glitch(0.5, seed=int(tw)), tw - 0.05, 0.4)
        f_(S.reverse_swell(0.8, freqs=(69.3, 103.8, 138.6), seed=int(tw) + 1), tw - 0.8, 0.25)
    f_(S.whoosh(0.8, -0.5, 0.5, seed=87), 86.8, 0.3)
    # NO. NO.
    for tw, p in ((91.96, 0.2), (96.94, -0.2)):
        f_(S.impact(size=1.2, tone=42, seed=int(tw), metal=0.5), tw - 0.01, 0.8, pan=p)
        f_(S.shimmer(2.0, seed=int(tw) + 2, fmin=2500, fmax=9000), tw, 0.3)
        f_(S.riser(1.5, f0=200, f1=3000, seed=int(tw) + 3, tonal=False), tw - 1.5, 0.25)
    # beam + lift + into the ocean
    f_(S.shimmer(3.0, seed=105, fmin=1500, fmax=6000), 105.2, 0.4)
    f_(S.riser(4.4, f0=150, f1=5000, seed=108), 108.6, 0.45)
    f_(S.wind(4.5, seed=109, bright=2200) * np.linspace(0.2, 1.0, secs(4.5), dtype=np.float32)[:, None], 108.6, 0.4)
    f_(S.whoosh(1.8, 0.6, -0.2, seed=113, fpk=1800, f1=200), 113.1, 0.5)
    land = 114.86
    f_(S.impact(size=1.0, tone=45, seed=114, metal=0.2), land, 0.6)
    ns = secs(2.5)
    spl = S.svf(S.noise(ns, 'white', 115), np.full(ns, 2500, np.float32), 0.6, 0) * np.exp(-np.arange(ns) / SR / 0.35)
    f_(S.widen(spl.astype(np.float32), 1.0, 115), land, 0.45)
    # glass shatter tinkles
    rng = np.random.default_rng(116)
    for _ in range(40):
        tt0 = land + rng.uniform(0.0, 1.6) ** 2
        n2 = secs(0.4)
        x = np.arange(n2) / SR
        f0 = rng.uniform(2500, 7000)
        tk = np.sin(2 * np.pi * f0 * x) * np.exp(-x / 0.05) * rng.uniform(0.2, 1)
        f_(tk.astype(np.float32), tt0, 0.12, pan=rng.uniform(-0.8, 0.8))
    for k, tw in enumerate((119.52, 120.28, 120.96, 121.64)):
        f_(S.impact(size=0.7, tone=38, seed=119 + k, metal=0.0, tail_s=2.5), tw, 0.35)
        f_(S.whoosh(1.2, -0.2, 0.2, seed=130 + k, f0=200, fpk=3000, f1=600), tw - 0.2, 0.3)
    f_(S.riser(2.2, f0=300, f1=6000, seed=126, tonal=True), 125.6, 0.35)
    f_(S.impact(size=0.9, tone=50, seed=127, metal=0.2), 127.76, 0.5)
    f_(S.shimmer(3.0, seed=128, fmin=2000, fmax=9000), 127.5, 0.5)
    f_(S.reverse_swell(1.0, seed=137), 136.9, 0.25)
    for k, m in enumerate([76, 79, 83]):
        n2 = secs(3.0)
        x = np.arange(n2) / SR
        tone = (np.sin(2 * np.pi * S.midi(m) * x) + 0.5 * np.sin(2 * np.pi * S.midi(m) * 1.004 * x)) * S.env_ar(n2, 0.5, 0.4)
        f_(tone.astype(np.float32), 141.3 + k * 0.3, 0.08, pan=(k - 1) * 0.5)
        f_(tone.astype(np.float32), 144.5 + k * 0.4, 0.08, pan=(1 - k) * 0.5)
    f_(S.whoosh(1.2, -0.6, 0.6, seed=148), 148.4, 0.3)
    n2 = secs(1.5)
    x = np.arange(n2) / SR
    f_(S.pan((np.sin(2 * np.pi * 3520 * x) * np.exp(-x / 0.4) * 0.3).astype(np.float32), 0.2), 161.7, 0.25)
    f_(S.reverse_swell(1.8, freqs=(69.3, 103.8, 138.6), seed=169), 168.4, 0.25)
    f_(S.glitch(0.4, seed=176), 176.6, 0.25)
    # ocean small -> NO: wave roar crescendo + crash
    ns = secs(4.0)
    roar = S.svf(S.noise(ns, 'pink', 185), np.linspace(300, 3000, ns).astype(np.float32), 0.7, 0) * np.linspace(0, 1, ns) ** 2
    f_(S.widen(roar.astype(np.float32), 1.0, 185), 184.7, 0.5)
    f_(S.impact(size=1.5, tone=36, seed=188, metal=0.1), 188.64, 0.85)
    ns = secs(3.0)
    crash = S.svf(S.noise(ns, 'white', 189), np.full(ns, 1800, np.float32), 0.6, 0) * np.exp(-np.arange(ns) / SR / 0.8)
    f_(S.widen(crash.astype(np.float32), 1.0, 189), 188.64, 0.5)
    # sun: warm drone crescendo + riser + flare
    f_(S.riser(3.4, f0=120, f1=4000, seed=192), 192.9, 0.35)
    f_(S.braam(3.5, root=36.71, seed=196), 196.29, 0.55)
    f_(S.impact(size=1.2, tone=48, seed=196, metal=0.3), 196.29, 0.5)
    # tree grows: creaks + riser + bloom
    for k in range(5):
        ns = secs(0.6)
        cr = S.svf(S.noise(ns, 'pink', 200 + k), np.full(ns, 350 + 80 * k, np.float32), 8.0, 1) * S.env_ar(ns, 0.2, 0.3)
        f_(S.pan(cr.astype(np.float32), -0.4 + 0.2 * k), 200.3 + k * 0.3, 0.3)
    f_(S.riser(1.8, f0=300, f1=5000, seed=201), 200.3, 0.3)
    f_(S.impact(size=1.1, tone=52, seed=202, metal=0.3), 202.11, 0.6)
    f_(S.shimmer(3.0, seed=202, fmin=1500, fmax=7000), 202.1, 0.5)
    # WHY? WHY?
    f_(S.braam(2.5, root=36.71, seed=203), 203.47, 0.45)
    f_(S.braam(4.0, root=36.71, seed=205), 205.45, 0.75)
    f_(S.sub_drop(2.5, 70, 22), 205.45, 0.6)
    f_(S.impact(size=1.6, tone=40, seed=205, metal=0.3), 205.45, 0.6)
    # four words: four pings
    for k, tw in enumerate((212.07, 212.59, 213.29, 213.81)):
        n2 = secs(1.5)
        x = np.arange(n2) / SR
        f_(S.pan((np.sin(2 * np.pi * S.midi(74 + [0, 3, 7, 10][k]) * x) * np.exp(-x / 0.5) * 0.4).astype(np.float32),
                 -0.45 + 0.3 * k), tw, 0.25)
    f_(S.riser(1.6, f0=200, f1=6000, seed=216), 216.3, 0.5)
    for k, tw in enumerate((217.88, 218.44, 218.92, 219.42)):
        f_(S.impact(size=1.3 + 0.1 * k, tone=44 - k * 2, seed=217 + k, metal=0.4), tw - 0.01, 0.8, pan=(k - 1.5) * 0.2)
    f_(S.braam(4.0, root=43.65, seed=219), 219.42, 0.5)
    # dome forms, shatters: bigger than that
    for k, m in enumerate([79, 83, 86, 91]):
        n2 = secs(2.0)
        x = np.arange(n2) / SR
        f_(S.pan((np.sin(2 * np.pi * S.midi(m) * x) * S.env_ar(n2, 0.3, 0.5) * 0.25).astype(np.float32), (k - 1.5) * 0.3),
           223.8 + k * 0.35, 0.2)
    f_(S.riser(1.5, f0=300, f1=7000, seed=225), 225.64, 0.45)
    f_(S.impact(size=1.4, tone=46, seed=227, metal=0.9), 227.14, 0.8)
    rng = np.random.default_rng(227)
    for _ in range(70):
        tt0 = 227.14 + rng.uniform(0.0, 1.8) ** 2
        n2 = secs(0.5)
        x = np.arange(n2) / SR
        tk = np.sin(2 * np.pi * rng.uniform(2500, 8000) * x) * np.exp(-x / 0.06) * rng.uniform(0.2, 1)
        f_(tk.astype(np.float32), tt0, 0.15, pan=rng.uniform(-0.9, 0.9))
    f_(S.shimmer(4.0, seed=229, fmin=1500, fmax=8000), 228.6, 0.3)
    f_(S.riser(3.0, f0=150, f1=3000, seed=235, pulse=False), 234.6, 0.25)
    # hold up: rewind
    rw = S.whoosh(0.7, 0.6, -0.6, seed=239, f0=4000, fpk=1500, f1=300)[::-1].copy()
    f_(rw, 238.75, 0.5)
    f_(S.glitch(0.3, seed=239), 239.0, 0.3)
    f_(S.shimmer(1.6, seed=241), 240.7, 0.35)
    # nine million years: time-lapse ticking accelerating + ashes
    t = 242.8
    per = 0.3
    k = 0
    while t < 247.5:
        f_(S.tick(k % 2 == 1), t, 0.18, pan=0.4 if k % 2 else -0.4)
        t += per
        per = max(0.05, per * 0.93)
        k += 1
    f_(S.fire(3.0, seed=247), 247.4, 0.12)
    f_(S.reverse_swell(1.6, freqs=(73.4, 110.0), seed=247), 246.0, 0.3)
    f_(S.reverse_swell(1.6, freqs=(69.3, 103.8), seed=250), 249.3, 0.3)
    f_(S.sub_drop(3.0, 45, 20), 267.28, 0.55)
    # cosmic zoom: warps and number fly-bys
    for tw in (272.98, 273.9):
        f_(S.whoosh(1.2, -0.3, 0.3, seed=int(tw * 10), f0=120, fpk=2000, f1=150), tw - 0.4, 0.5)
        f_(S.impact(size=0.8, tone=34, seed=int(tw), metal=0.0, tail_s=3.0), tw, 0.35)
    for k, tw in enumerate((280.68, 281.62, 282.88, 283.94, 284.90, 285.84)):
        p0 = -0.9 if k % 2 else 0.9
        f_(S.whoosh(1.4, p0, -p0, seed=280 + k, f0=300, fpk=3500 + 300 * k, f1=250), tw - 0.5, 0.45)
    # gone list: each item shimmers in and exhales away
    for (a, g) in ((302.32, 303.34), (303.9, 304.56), (305.14, 306.42), (306.96, 307.8), (308.34, 309.0), (309.5, 310.7)):
        f_(S.shimmer(0.9, seed=int(a * 10), fmin=2500, fmax=7000, density=20), a - 0.15, 0.15)
        f_(S.reverse_swell(0.6, freqs=(146.8, 220.0), seed=int(g * 10)), g - 0.55, 0.2)
        f_(S.whoosh(1.4, 0.0, 0.3, seed=int(g * 10) + 1, f0=600, fpk=2500, f1=200), g, 0.25)
    for k in range(4):
        n2 = secs(3.0)
        x = np.arange(n2) / SR
        dn = np.sin(2 * np.pi * np.cumsum((440 - 60 * k) * np.exp(-x / 2.0)) / SR) * np.exp(-x / 1.4) * 0.2
        f_(S.pan(dn.astype(np.float32), (k - 1.5) * 0.4), 311.6 + k * 0.8, 0.2)
    # final: the face re-forms, the small moment, the pull back
    f_(S.shimmer(2.5, seed=329), 329.1, 0.35)
    f_(S.sub_drop(2.0, 60, 30), 329.1, 0.3)
    for tw in (350.2, 350.54):
        f_(S.tick(tw > 350.3), tw, 0.25)
    n2 = secs(1.6)
    x = np.arange(n2) / SR
    ping = (np.sin(2 * np.pi * 1244.5 * x) + np.sin(2 * np.pi * 1318.5 * x)) * np.exp(-x / 0.5) * 0.2
    f_(S.pan(ping.astype(np.float32), 0.3), 352.0, 0.25)
    f_(S.riser(3.0, f0=150, f1=4000, seed=354, pulse=False), 352.2, 0.3)
    f_(S.whoosh(3.0, 0.0, 0.0, seed=355, f0=100, fpk=900, f1=80), 354.9, 0.5)
    f_(S.impact(size=1.2, tone=37, seed=357, metal=0.2, tail_s=5.0), 357.4, 0.45)
    f_(S.shimmer(5.0, seed=358), 357.4, 0.4)
    return amb, fx


def main():
    work, out = sys.argv[1], sys.argv[2]
    print('voice...', flush=True)
    v, vox = voice_layers(work)
    print('score...', flush=True)
    mus = score(v)
    print('sfx...', flush=True)
    amb, fx = sfx_track()
    L = min(len(vox), len(mus), len(amb), len(fx), N)
    vox, mus, amb, fx = vox[:L], mus[:L], amb[:L], fx[:L]
    # duck the beds under the voice
    mus = duck(mus, v[:L], depth_db=8.0)
    amb = duck(amb, v[:L], depth_db=6.0)
    mix = vox * db(0) + mus * db(-10.5) + amb * db(-9.0) + fx * db(-6.5)
    # fade in/out
    fi = secs(0.25)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    fo = secs(3.0)
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 2
    print('master...', flush=True)
    y, lufs = master(mix, target_lufs=-14.0, ceiling_db=-1.0)
    sf.write(out, y, SR, subtype='PCM_24')
    # stems for the studio
    for name, st in (('voice', vox), ('music', mus), ('ambience', amb), ('sfx', fx)):
        sf.write(out.replace('.wav', f'_{name}.wav'), (st / (np.abs(st).max() + 1e-9) * 0.9).astype(np.float32), SR,
                 subtype='PCM_24')
    print(f'done: {out}  integrated {lufs:.2f} LUFS  peak {20 * np.log10(np.abs(y).max()):.2f} dBFS', flush=True)


if __name__ == '__main__':
    main()
