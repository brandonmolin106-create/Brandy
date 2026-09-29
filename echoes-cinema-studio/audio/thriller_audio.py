"""Thriller soundtrack for the realistic cut: Brandon's voice bus + a new dark score + hit-synced sound design.

usage: python thriller_audio.py WORK OUT.wav
  WORK/audio/mix_voice.wav = the processed voice bus (vocal chain + emotion reverb) from the first cut.
Everything else is synthesized here - no samples, no licensed music.
"""
import math
import os
import sys

import numpy as np
import soundfile as sf
from pedalboard import Distortion, HighpassFilter, LowpassFilter, Reverb
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'echoes-particle-studio'))
import sfx as S  # noqa: E402
from audio_post import curve, duck, master  # noqa: E402
from sfx import SR, secs  # noqa: E402

DUR = 365.0
N = secs(DUR)


def bus():
    return np.zeros((N + secs(10), 2), np.float32)


def db(x):
    return 10 ** (x / 20.0)


def place(b, x, t, gain=1.0):
    if x.ndim == 1:
        x = np.stack([x, x], -1)
    s0 = secs(t)
    if s0 < 0:
        x = x[-s0:]
        s0 = 0
    s1 = min(len(b), s0 + len(x))
    if s1 > s0:
        b[s0:s1] += x[: s1 - s0] * gain


# ------------------------------------------------------------------ instruments
def saw(freq, n, detune=0.0, seed=0):
    rng = np.random.default_rng(seed)
    ph = (np.arange(n, dtype=np.float64) * freq * (1 + detune) / SR + rng.random()) % 1.0
    return (2 * ph - 1).astype(np.float32)


def drone_bed():
    """Continuous low D-minor drone whose filter/level follow the story's tension."""
    n = N
    t = np.arange(n, dtype=np.float32) / SR
    tension = curve([(0, 0.2), (7.0, 0.6), (8.7, 0.1), (19.5, 0.35), (27.9, 0.45), (42.1, 0.9), (53.5, 0.6),
                     (58.9, 0.35), (71.4, 0.25), (77.1, 0.6), (89.4, 0.7), (97.7, 0.3), (105.1, 0.5), (113.9, 0.8),
                     (118.2, 0.35), (129.2, 0.45), (149.1, 0.65), (163.6, 0.5), (181.4, 0.8), (205.5, 1.0),
                     (206.5, 0.55), (217.9, 1.0), (221.2, 0.5), (227.1, 0.9), (228.7, 0.4), (239.1, 0.2),
                     (242.8, 0.6), (268.3, 0.35), (280.6, 0.7), (287.1, 0.3), (298.8, 0.05), (302.3, 0.2),
                     (311.6, 0.15), (322.4, 0.02), (329.1, 0.35), (345.7, 0.6), (357.2, 1.0), (357.3, 0.05),
                     (365, 0.0)], n, smooth=0.6)
    level = curve([(0, 0.0), (0.5, 0.6), (298.8, 0.6), (301.3, 0.0), (302.3, 0.35), (322.4, 0.1), (327, 0.0),
                   (329.1, 0.5), (357.2, 0.9), (357.3, 0.0), (358.0, 0.25), (365, 0.0)], n, smooth=0.25)
    out = np.zeros((n, 2), np.float32)
    for k, (f, amp) in enumerate(((36.71, 1.0), (55.0, 0.55), (73.42, 0.45), (87.31, 0.3), (110.0, 0.18))):
        for ch in (0, 1):
            x = saw(f, n, detune=(0.003 if ch else -0.003) * (k + 1), seed=k * 2 + ch)
            wob = 1 + 0.25 * np.sin(2 * np.pi * (0.05 + 0.013 * k) * t + k + ch)
            out[:, ch] += x * amp * wob
    cutoff = (90 + 900 * tension ** 1.6).astype(np.float32)
    for ch in (0, 1):
        out[:, ch] = S.svf(out[:, ch].astype(np.float32), cutoff, np.float32(0.9), 0)
    rum = S.noise(n, 'brown', seed=4)
    rum = S.svf(rum[:, 0].astype(np.float32) if rum.ndim == 2 else rum.astype(np.float32),
                np.full(n, 70, np.float32), np.float32(0.7), 0)
    out += rum[:, None] * 0.6 * (0.3 + tension[:, None])
    out *= (level * (0.5 + 0.6 * tension))[:, None]
    return (out / (np.abs(out).max() + 1e-6) * 0.7).astype(np.float32)


def pulse_track(sections, bpm=100):
    """Muted 16th-note bass ostinato (D D D F / D D C D) in the given (t0, t1, gain) sections."""
    b = bus()
    step = 60.0 / bpm / 4
    pattern = [38, 38, 38, 41, 38, 38, 36, 38]
    for (t0, t1, g, *acc) in sections:
        accel = acc[0] if acc else 1.0
        t = t0
        k = 0
        while t < t1:
            f = S.midi(pattern[k % len(pattern)])
            n = secs(0.16)
            tt = np.arange(n) / SR
            x = (np.sign(np.sin(2 * np.pi * f * tt)) * 0.5 + np.sin(2 * np.pi * f * tt)) * np.exp(-tt * 22)
            x = S.svf(x.astype(np.float32), np.full(n, 600.0, np.float32), np.float32(1.2), 0)
            acc_k = 1.0 if k % 4 == 0 else 0.7
            place(b, x * acc_k * g, t)
            prog = (t - t0) / max(1e-3, t1 - t0)
            t += step / (1 + (accel - 1) * prog)
            k += 1
    return b


def glass_knock(strength=1.0, seed=0):
    """Fish nose on glass: dull thud + short ringing glass partials."""
    rng = np.random.default_rng(seed)
    n = secs(1.2)
    t = np.arange(n) / SR
    thud = np.sin(2 * np.pi * 95 * t * (1 - 0.3 * t)) * np.exp(-t * 28)
    ring = sum(a * np.sin(2 * np.pi * f * t + rng.random()) * np.exp(-t * d)
               for f, a, d in ((2210, 0.35, 9), (3170, 0.22, 12), (4630, 0.15, 16), (6040, 0.08, 22)))
    x = (thud * 0.9 + ring) * strength
    return S.verb(np.stack([x, x * 0.96], -1).astype(np.float32), room=0.35, wet=0.18, pad=0.8)


def bubbles(dur=3.0, rate=14.0, seed=0):
    rng = np.random.default_rng(seed)
    n = secs(dur)
    out = np.zeros((n, 2), np.float32)
    k = int(dur * rate)
    for _ in range(k):
        s0 = int(rng.uniform(0, n - secs(0.08)))
        m = secs(rng.uniform(0.02, 0.07))
        t = np.arange(m) / SR
        f0 = rng.uniform(500, 1600)
        x = np.sin(2 * np.pi * f0 * t * (1 + 3 * t)) * np.exp(-t * 60)
        p = rng.uniform(-0.7, 0.7)
        out[s0:s0 + m, 0] += x * (1 - p) * 0.3
        out[s0:s0 + m, 1] += x * (1 + p) * 0.3
    return out


def splash(seed=0):
    n = secs(2.5)
    nz = S.noise(n, 'white', seed=seed)
    nz = nz[:, 0] if nz.ndim == 2 else nz
    env = np.exp(-np.arange(n) / SR * 3.5) * (1 - np.exp(-np.arange(n) / SR * 90))
    x = S.svf((nz * env).astype(np.float32), np.linspace(5000, 900, n).astype(np.float32), np.float32(0.8), 0)
    boom = S.sub_drop(1.2, 70, 30)[:n]
    y = np.stack([x, x], -1) * 0.8
    y[:len(boom)] += boom * 0.6
    return S.verb(y.astype(np.float32), room=0.7, wet=0.3, pad=1.5)


def underwater(dur, seed=0):
    """Muffled pressure: lowpassed rumble + slow swells."""
    n = secs(dur)
    nz = S.noise(n, 'brown', seed=seed)
    nz = nz[:, 0] if nz.ndim == 2 else nz
    t = np.arange(n) / SR
    cut = (180 + 90 * np.sin(2 * np.pi * 0.11 * t)).astype(np.float32)
    x = S.svf(nz.astype(np.float32), cut, np.float32(0.9), 0)
    x = x / (np.abs(x).max() + 1e-6)
    fade = np.minimum(1, np.minimum(t / 0.6, (dur - t) / 0.8))
    return (np.stack([x, np.roll(x, 900)], -1) * fade[:, None] * 0.6).astype(np.float32)


def lamp_buzz(dur, seed=0, flicker=None):
    """Mains hum of an old tungsten lamp (100 Hz + harmonics), optional on/off flicker envelope."""
    n = secs(dur)
    t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((100, 1.0), (200, 0.5), (300, 0.3), (400, 0.12)))
    x += 0.15 * S.noise(n, 'white', seed=seed) * (np.sin(2 * np.pi * 100 * t) > 0.9)
    env = np.ones(n, np.float32) if flicker is None else np.interp(t, *zip(*flicker)).astype(np.float32)
    return (np.stack([x, x], -1) * env[:, None] * 0.12).astype(np.float32)


def click(seed=0):
    n = secs(0.06)
    nz = S.noise(n, 'white', seed=seed)
    x = nz * np.exp(-np.arange(n) / SR * 120)
    return np.stack([x, x], -1).astype(np.float32) * 0.5


def glass_shatter(seed=0):
    rng = np.random.default_rng(seed)
    n = secs(3.0)
    out = np.zeros((n, 2), np.float32)
    for _ in range(160):
        s0 = int(abs(rng.normal(0, secs(0.35))))
        if s0 >= n - secs(0.2):
            continue
        m = secs(rng.uniform(0.05, 0.25))
        t = np.arange(m) / SR
        f = rng.uniform(2500, 9000)
        x = np.sin(2 * np.pi * f * t) * np.exp(-t * rng.uniform(15, 40)) * rng.uniform(0.1, 0.4)
        p = rng.uniform(-0.9, 0.9)
        out[s0:s0 + m, 0] += x * (1 - p)
        out[s0:s0 + m, 1] += x * (1 + p)
    nz = S.noise(secs(0.4), 'white', seed=seed + 1) * np.exp(-np.arange(secs(0.4)) / SR * 14)
    out[:len(nz)] += np.stack([nz, nz], -1) * 0.6
    return S.verb(out, room=0.8, wet=0.35, pad=2.0)


def tape_stop(dur=0.45):
    n = secs(dur)
    t = np.arange(n) / SR
    f = 220 * (1 - t / dur) ** 2 + 20
    ph = np.cumsum(2 * np.pi * f / SR)
    x = (np.sign(np.sin(ph)) * 0.3 + np.sin(ph * 2) * 0.3) * (1 - t / dur)
    return np.stack([x, x], -1).astype(np.float32)


def footsteps(t0, t1, pace=0.55, seed=0):
    """Muffled footsteps of people walking past outside the room."""
    b = []
    rng = np.random.default_rng(seed)
    t = t0
    while t < t1:
        n = secs(0.25)
        tt = np.arange(n) / SR
        x = np.sin(2 * np.pi * rng.uniform(55, 75) * tt) * np.exp(-tt * 30) + \
            0.3 * S.noise(n, 'brown', seed=int(t * 100)) * np.exp(-tt * 40)
        b.append((t, np.stack([x, x], -1).astype(np.float32)))
        t += pace * rng.uniform(0.9, 1.1)
    return b


# ------------------------------------------------------------------ build
def build(work):
    voice, sr = sf.read(f'{work}/audio/mix_voice.wav', dtype='float32', always_2d=True)
    assert sr == SR
    vox = np.zeros((N + secs(10), 2), np.float32)
    vox[:min(len(voice), len(vox))] = voice[:len(vox)]

    mus, fxb, amb = bus(), bus(), bus()
    # ---- drone bed
    d = drone_bed()
    mus[:N] += d * 0.9
    # ---- pulse ostinato sections (t0, t1, gain, accel)
    mus += pulse_track([(27.9, 39.9, 0.18), (39.9, 53.5, 0.32, 1.6), (53.5, 58.9, 0.2), (77.1, 91.9, 0.3),
                        (149.1, 156.8, 0.28), (158.8, 175.6, 0.22), (206.5, 217.8, 0.34, 1.8),
                        (242.8, 247.5, 0.3, 2.0), (329.1, 357.1, 0.26, 1.5)])
    # ---- heartbeat
    for t0, bpm, beats, g in ((58.9, 60, 12, 0.7), (71.4, 50, 5, 0.6), (131.4, 64, 13, 0.4), (163.6, 66, 12, 0.45),
                              (254.2, 52, 12, 0.5), (329.1, 58, 16, 0.5), (345.7, 72, 13, 0.6)):
        place(mus, S.heartbeat(bpm=bpm, beats=beats, seed=int(t0)), t0, g)
    # ---- ticking clocks (time passing)
    place(fxb, S.clock(5.3, 120), 48.2, 0.5)
    place(fxb, S.clock(4.7, 190), 242.84, 0.55)
    place(fxb, S.clock(12.0, 60), 268.3, 0.35)
    place(fxb, S.clock(3.5, 60), 298.8, 0.3)
    # ---- piano motif (D minor add9, sparse) + hope chords
    motif = [(62, 0.0), (69, 0.75), (76, 1.5), (77, 2.25), (74, 3.0)]
    for t0, g in ((8.9, 0.35), (97.7, 0.4), (101.4, 0.35), (129.3, 0.25), (228.8, 0.4), (233.3, 0.35),
                  (331.0, 0.3), (336.4, 0.3), (345.8, 0.35), (350.6, 0.35)):
        for m, dt in motif:
            place(mus, S.felt_piano(m, dur=3.5, vel=0.8, seed=m + int(t0)), t0 + dt, g)
    place(mus, S.strings([50, 57, 62, 66, 69], dur=10.5, seed=3, bright=0.6), 228.7, 0.35)   # D major lift: I lived?
    place(mus, S.choir([62, 66, 69, 74], dur=7.0, seed=5), 231.0, 0.22)
    place(mus, S.pad([50, 57, 65, 69], dur=10.0, bright=0.4, seed=9), 118.2, 0.3)            # the open ocean
    place(mus, S.strings([50, 57, 62, 66], dur=4.0, seed=4, bright=0.7), 127.6, 0.3)          # free
    place(mus, S.pad([38, 45, 50], dur=8.0, bright=0.2, seed=2), 357.3, 0.45)                 # end card
    place(mus, S.felt_piano(38, dur=6.0, vel=0.9, seed=1), 357.4, 0.5)

    # ---- hits: (t, braam?, impact size)
    hits = [(7.10, True, 1.0), (42.12, True, 1.2), (43.28, False, 0.6), (47.08, False, 1.0), (52.44, False, 0.7),
            (61.17, False, 0.4), (75.88, False, 0.6), (91.96, True, 1.2), (96.94, True, 1.2), (127.76, False, 0.8),
            (137.88, False, 0.6), (188.64, True, 1.3), (196.29, True, 1.3), (202.11, True, 1.3), (203.47, False, 0.9),
            (205.45, True, 1.5), (217.88, False, 0.8), (218.44, False, 0.8), (218.92, False, 0.9), (219.42, True, 1.6),
            (227.14, False, 1.3), (248.04, False, 0.6), (280.68, False, 0.7), (281.62, False, 0.8),
            (282.88, False, 0.9), (283.94, False, 1.0), (284.90, True, 1.2), (286.30, True, 1.4),
            (303.34, False, 0.9), (304.56, False, 0.9), (306.42, False, 0.9), (307.80, False, 0.9), (309.00, False, 0.9),
            (310.70, True, 1.1), (327.31, False, 0.5), (357.21, True, 1.8)]
    for t, br, size in hits:
        place(fxb, S.impact(size=size, seed=int(t * 10)), t, 0.55 * size)
        place(fxb, S.sub_drop(1.6), t, 0.35 * size)
        if br:
            place(mus, S.braam(dur=4.0, seed=int(t)), t - 0.02, 0.5)
    # glass hits + water
    place(fxb, glass_knock(1.0, 1), 42.12, 0.8)
    place(fxb, glass_knock(0.8, 2), 47.08, 0.7)
    place(fxb, bubbles(2.0, 10, 3), 42.2, 0.4)
    place(fxb, bubbles(4.3, 20, 4), 113.94, 0.6)
    place(fxb, splash(5), 113.94, 0.8)
    place(fxb, bubbles(3.0, 8, 6), 122.3, 0.3)
    # risers into the big moments
    for t_end, dur in ((19.5, 3.0), (42.12, 2.2), (113.94, 4.5), (181.44, 2.5), (217.88, 6.0), (227.14, 3.0),
                       (280.6, 4.0), (357.21, 6.5)):
        r = S.riser(dur=dur, seed=int(t_end))
        place(fxb, r, t_end - dur, 0.35)
    # whooshes on the hard cuts into new worlds
    for t in (8.82, 19.5, 27.88, 105.12, 108.26, 118.18, 149.08, 181.44, 189.18, 196.87, 228.74, 242.84, 268.3, 331.03):
        place(fxb, S.whoosh(dur=0.9, seed=int(t * 7)), t - 0.45, 0.35)
    # reverse swells into each 'Gone.'
    for t in (303.34, 304.56, 306.42, 307.80, 309.00, 310.70):
        place(fxb, S.reverse_swell(0.5, seed=int(t)), t - 0.5, 0.35)
    # glitches on cuts into the tape
    for t in (2.0, 18.2, 33.42, 58.9, 65.5, 75.8, 87.3, 92.58, 129.22, 137.88, 144.54, 153.52, 158.8, 163.64, 170.22,
              178.72, 202.81, 211.53, 221.18, 233.34, 239.06, 305.14, 329.07, 342.0):
        place(fxb, S.glitch(0.35, seed=int(t * 3)), t, 0.25)
    place(fxb, tape_stop(), 239.06, 0.5)
    place(fxb, glass_shatter(7), 227.0, 0.8)
    # lamp: stutter on at the top, dies at 'Both are gone' and in the long fade to nothing
    place(amb, lamp_buzz(8.7, 1, [(0, 0), (0.55, 0), (0.6, 1), (0.66, 0.1), (0.75, 0), (0.95, 0), (1.0, 0.7),
                                   (1.05, 0.2), (1.12, 1), (8.6, 1), (8.7, 0)]), 0.0, 0.5)
    for t in (0.6, 1.0, 1.12, 268.08, 312.5, 316.0, 321.8):
        place(fxb, click(int(t * 10)), t, 0.5)
    place(amb, lamp_buzz(11.0, 2, [(0, 1), (10.8, 0.1), (11.0, 0)]), 311.56, 0.35)
    place(amb, lamp_buzz(5.0, 3, [(0, 0), (0.1, 1), (4.9, 1), (5.0, 0)]), 149.08, 0.5)    # fluorescent tube
    # footsteps of the people walking past
    for t, x in footsteps(77.1, 87.3, seed=1) + footsteps(175.66, 178.7, seed=2) + footsteps(206.49, 211.5, seed=3):
        place(fxb, x, t, 0.35)
    # ambiences
    rain = S.rain(DUR, seed=3)
    rain_lv = curve([(0, 0.0), (0.6, 0.3), (19.5, 0.3), (19.6, 0.0), (27.8, 0.0), (27.9, 0.3), (113.9, 0.3), (114.0, 0.0),
                     (149.0, 0.0), (163.6, 0.2), (181.4, 0.2), (181.5, 0.0), (206.4, 0.0), (206.5, 0.25), (217.8, 0.25),
                     (217.9, 0.0), (242.8, 0.0), (242.9, 0.25), (268.3, 0.25), (268.4, 0.0), (329.0, 0.0),
                     (331.0, 0.25), (357.2, 0.25), (357.3, 0.0)], len(rain), smooth=0.2)
    amb[:len(rain)] += rain * rain_lv[:, None]
    for t0, t1 in ((19.5, 27.88), (113.94, 129.22), (131.44, 137.88), (138.68, 144.54)):
        place(amb, underwater(t1 - t0, seed=int(t0)), t0, 0.7)
    place(amb, S.wind(7.4, seed=5, bright=500), 181.3, 0.6)
    place(amb, S.ocean(7.4, period=5.0, seed=6), 181.3, 0.8)
    place(amb, S.wind(5.4, seed=7, bright=1200), 196.8, 0.5)
    place(amb, S.shimmer(4.0, seed=8), 189.2, 0.4)
    place(amb, S.shimmer(3.0, seed=9), 71.4, 0.3)
    place(amb, S.shimmer(6.0, seed=10), 268.3, 0.25)

    # ---- silence where the story asks for it
    gate = curve([(0, 1), (157.7, 1), (157.82, 0.08), (158.7, 0.08), (158.8, 1), (239.06, 1), (239.1, 0.0),
                  (239.4, 0.0), (239.5, 1), (301.3, 1), (301.4, 0.0), (302.2, 0.0), (302.3, 1), (322.4, 1), (322.5, 0.15),
                  (329.0, 0.15), (329.1, 1), (344.8, 1), (344.9, 0.1), (345.6, 0.1), (345.7, 1), (357.22, 1),
                  (357.25, 0.0), (357.35, 0.0), (357.4, 1)], len(mus), smooth=0.02)
    mus *= gate[:, None]
    amb *= gate[:, None]

    # ---- mix
    key = vox.mean(1)
    mus = duck(mus, key, depth_db=5.0)
    amb = duck(amb, key, depth_db=4.0)
    fxb_d = duck(fxb, key, depth_db=2.5)
    mix = vox * db(0) + mus * db(-9.5) + fxb_d * db(-7.0) + amb * db(-13.0)
    return mix[:N], dict(voice=vox[:N], music=mus[:N], sfx=fxb[:N], ambience=amb[:N])


def main():
    work, out = sys.argv[1], sys.argv[2]
    mix, stems = build(work)
    final, lufs = master(mix, target_lufs=-14.0, ceiling_db=-1.0)
    final = final[:N]
    sf.write(out, final, SR, subtype='PCM_24')
    peak = 20 * np.log10(np.abs(final).max() + 1e-9)
    print(f'{out}: {len(final) / SR:.2f}s  {lufs:.2f} LUFS  peak {peak:.2f} dBFS', flush=True)
    base = out.rsplit('.', 1)[0]
    for k, v in stems.items():
        sf.write(f'{base}_{k}.wav', v, SR, subtype='PCM_24')


if __name__ == '__main__':
    main()
