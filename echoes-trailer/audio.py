"""Echoes in the Dark - 6:00 trailer score, sound design and narration mix.

Everything is synthesised here (no samples): drones, heartbeat, ticking-clock
ostinato, taiko hits, brass "braams", choir pad, risers, whooshes and echo pings,
all locked to timeline.py. The narration lines in assets/voice/ are EQ'd, echoed
and ducked over the score.

  python3 audio.py            -> out/soundtrack.wav (48 kHz stereo)
"""
import os

import numpy as np
import soundfile as sf
from scipy.signal import butter, oaconvolve, resample_poly, sosfilt

import timeline as T

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
N = int(T.DURATION * SR) + SR
rng = np.random.default_rng(1234)

BPM = 100.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
GRID0 = 97.0  # the formation score is on a grid starting here

# note frequencies
NOTE = {n: 440.0 * 2 ** ((i - 57) / 12) for i, n in enumerate(
    [f"{p}{o}" for o in range(0, 8) for p in ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]])}
NOTE["Bb1"], NOTE["Bb2"], NOTE["Bb3"] = NOTE["A#1"], NOTE["A#2"], NOTE["A#3"]

CHORDS = [  # i - VI - iv - V  in D minor
    ("D1", ["D3", "F3", "A3"]),
    ("Bb1", ["Bb2", "D3", "F3"]),
    ("G1", ["G2", "Bb2", "D3"]),
    ("A1", ["A2", "C#3", "E3"]),
]


# ----------------------------------------------------------------------------- utils
def sos_lp(fc, order=4):
    return butter(order, min(fc, SR * 0.45), "low", fs=SR, output="sos")


def sos_hp(fc, order=2):
    return butter(order, fc, "high", fs=SR, output="sos")


def sos_bp(lo, hi, order=2):
    return butter(order, [lo, min(hi, SR * 0.45)], "band", fs=SR, output="sos")


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def env_adsr(n, a, d, s, r, sus_len=None):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    sus = max(0, n - a - d - r) if sus_len is None else int(sus_len * SR)
    e = np.concatenate([np.linspace(0, 1, max(a, 1)), np.linspace(1, s, max(d, 1)),
                        np.full(sus, s), np.linspace(s, 0, max(r, 1))])
    if len(e) < n:
        e = np.pad(e, (0, n - len(e)))
    return e[:n]


def saw(freq, dur, detune_cents=(0,), phase_rand=True):
    t = tt(dur)
    out = np.zeros_like(t)
    for c in detune_cents:
        f = freq * 2 ** (c / 1200)
        ph = rng.uniform(0, 1) if phase_rand else 0
        out += 2 * ((f * t + ph) % 1.0) - 1
    return out / len(detune_cents)


def glide_sine(f0, f1, dur, curve=3.0):
    t = tt(dur)
    u = t / max(dur, 1e-9)
    f = f1 + (f0 - f1) * np.exp(-curve * u)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def pan_st(x, pan=0.0, width=0.0):
    """Mono -> stereo with equal-power pan; width adds a small Haas offset."""
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    st = np.stack([x * l, x * r])
    if width > 0:
        d = int(width * 0.012 * SR)
        st[1] = np.concatenate([np.zeros(d), st[1][:-d]]) if d > 0 else st[1]
    return st * np.sqrt(2)


class Bus:
    def __init__(self):
        self.x = np.zeros((2, N), np.float64)

    def add(self, t0, sig, gain=1.0, pan=0.0, width=0.0):
        if sig.ndim == 1:
            sig = pan_st(sig, pan, width)
        i0 = int(t0 * SR)
        if i0 >= N:
            return
        if i0 < 0:
            sig = sig[:, -i0:]
            i0 = 0
        n = min(sig.shape[1], N - i0)
        self.x[:, i0:i0 + n] += sig[:, :n] * gain


def echo(sig, delay, fb, n=4, pingpong=True):
    """Tape-style echo: the studio's signature."""
    if sig.ndim == 1:
        sig = pan_st(sig)
    d = int(delay * SR)
    out = np.zeros((2, sig.shape[1] + d * n))
    out[:, :sig.shape[1]] += sig
    lp = sos_lp(4500, 2)
    tap = sig.copy()
    for k in range(1, n + 1):
        tap = sosfilt(lp, tap, axis=1) * fb
        if pingpong:
            tap = tap[::-1]
        out[:, k * d:k * d + tap.shape[1]] += tap
    return out


def make_ir(dur=4.2, decay=1.25, bright_decay=0.45, predelay=0.025, seed=9):
    r = np.random.default_rng(seed)
    t = tt(dur)
    ir = np.zeros((2, len(t)))
    for c in range(2):
        n = r.normal(0, 1, len(t))
        lo = sosfilt(sos_lp(2500, 2), n) * np.exp(-t / decay)
        hi = sosfilt(sos_hp(2500, 2), n) * np.exp(-t / bright_decay)
        ir[c] = lo + hi * 0.6
    ir *= np.clip(t / 0.01, 0, 1)
    pd = int(predelay * SR)
    ir = np.concatenate([np.zeros((2, pd)), ir], 1)
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def reverb(x, ir):
    out = np.zeros_like(x)
    for c in range(2):
        out[c] = oaconvolve(x[c], ir[c], mode="full")[:x.shape[1]]
    return out


# ----------------------------------------------------------------------------- instruments
def drone(freqs, dur, fc=900, detune=(-9, -3, 4, 10)):
    x = sum(saw(f, dur, detune) for f in freqs) / len(freqs)
    return sosfilt(sos_lp(fc, 4), x)


def sub_hit(dur=3.0, f0=110, f1=32, drive=2.5):
    t = tt(dur)
    x = glide_sine(f0, f1, dur, curve=6) * np.exp(-t / (dur * 0.35))
    return np.tanh(x * drive) / np.tanh(drive)


def taiko(dur=1.6, f0=95, f1=52):
    t = tt(dur)
    body = glide_sine(f0, f1, dur, 18) * np.exp(-t / 0.28)
    skin = sosfilt(sos_bp(120, 900), rng.normal(0, 1, len(t))) * np.exp(-t / 0.05) * 0.6
    return np.tanh((body + skin) * 1.8)


def braam(root, dur=4.5, bright=1.0, notes=None):
    notes = notes or [root, root * 2, root * 3, root * 4.0 * 2 ** (3 / 12)]
    t = tt(dur)
    x = sum(saw(f, dur, (-12, -4, 5, 13)) for f in notes)
    x = np.tanh(x * 1.6)
    # filter opening: crossfade dark -> bright -> dark
    dark = sosfilt(sos_lp(350, 4), x)
    lit = sosfilt(sos_lp(1900 * bright, 4), x)
    o = np.clip(t / 0.18, 0, 1) * np.exp(-t / (dur * 0.35))
    y = dark * (1 - o) + lit * o
    e = env_adsr(len(t), 0.03, 0.4, 0.55, dur * 0.55)
    return y * e + sub_hit(dur, 70, root * 0.98, 2.0) * 0.8


def pluck(freq, dur=2.4, bright=0.6):
    t = tt(dur)
    x = sum(np.sin(2 * np.pi * freq * k * t) * np.exp(-t * (1.6 + k * 1.3)) / k ** (1.3 - bright * 0.5)
            for k in range(1, 7))
    return x * np.clip(t / 0.003, 0, 1) * 0.5


def bell(freq, dur=4.0):
    t = tt(dur)
    parts = [(1.0, 1.0, 1.4), (2.76, 0.5, 2.2), (5.4, 0.25, 3.5), (8.93, 0.12, 5.0)]
    return sum(np.sin(2 * np.pi * freq * r * t) * a * np.exp(-t * d) for r, a, d in parts) * 0.5


def tick(hi=True):
    t = tt(0.06)
    f = 5200 if hi else 3600
    return np.sin(2 * np.pi * f * t) * np.exp(-t / 0.006) + \
        sosfilt(sos_bp(2500, 9000), rng.normal(0, 1, len(t))) * np.exp(-t / 0.004) * 0.5


def staccato(freq, dur=0.22):
    x = saw(freq, dur, (-7, 6)) + saw(freq * 2, dur, (0,)) * 0.3
    x = sosfilt(sos_lp(1100, 4), x)
    return x * env_adsr(len(x), 0.005, 0.08, 0.35, 0.09)


def pad(notes, dur, fc=2200, att=2.5, rel=3.0):
    x = sum(saw(NOTE[n], dur, (-14, -6, 0, 7, 15)) for n in notes) / len(notes)
    x = sosfilt(sos_lp(fc, 4), x)
    return x * env_adsr(len(x), att, 0.5, 0.9, rel)


def choir(notes, dur, att=0.4, rel=6.0):
    x = sum(saw(NOTE[n], dur, (-10, -3, 4, 11)) for n in notes) / len(notes)
    # "ahh" vowel: two formants
    y = sosfilt(sos_bp(650, 1000), x) * 1.0 + sosfilt(sos_bp(1000, 1400), x) * 0.6 + sosfilt(sos_lp(400, 2), x) * 0.4
    vib = 1 + 0.03 * np.sin(2 * np.pi * 5.1 * tt(dur))
    return y * vib * env_adsr(len(y), att, 1.0, 0.8, rel)


def noise_swell(dur, lo=300, hi=6000, rise=True):
    t = tt(dur)
    n = rng.normal(0, 1, len(t))
    a = sosfilt(sos_bp(lo, lo * 3), n)
    b = sosfilt(sos_bp(hi / 3, hi), n)
    u = t / dur if rise else 1 - t / dur
    return (a * (1 - u) + b * u) * (u ** 2.2)


def riser(dur, f0=90, f1=900):
    t = tt(dur)
    u = t / dur
    f = f0 * (f1 / f0) ** (u ** 1.6)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    return (tone * 0.5 + noise_swell(dur, 400, 9000) * 0.8) * u ** 2


def whoosh(dur=1.6, rev=False):
    t = tt(dur)
    n = rng.normal(0, 1, len(t))
    x = sosfilt(sos_bp(500, 5000), n) * np.sin(np.pi * t / dur) ** 2
    return x[::-1] if rev else x


def heartbeat(g=1.0):
    lub = sub_hit(0.35, 75, 42, 3.0)
    dub = sub_hit(0.3, 70, 40, 3.0) * 0.7
    out = np.zeros(int(0.7 * SR))
    out[:len(lub)] += lub
    i = int(0.26 * SR)
    out[i:i + len(dub)] += dub
    return out * g


# ----------------------------------------------------------------------------- score
def build():
    mus = Bus()   # music (ducked under voice)
    sfx = Bus()   # sound design (lightly ducked)
    wet = Bus()   # reverb send

    def both(t0, sig, g, pan=0.0, width=0.0, send=0.3):
        mus.add(t0, sig, g, pan, width)
        wet.add(t0, sig, g * send, pan, width)

    def fx(t0, sig, g, pan=0.0, width=0.0, send=0.4):
        sfx.add(t0, sig, g, pan, width)
        wet.add(t0, sig, g * send, pan, width)

    # === Act I/II: the void & the echo (0 - 95)
    d = drone([NOTE["D1"], NOTE["A1"]], 95.0, fc=500)
    d *= np.clip(tt(95.0) / 18.0, 0, 1) ** 1.5 * (0.6 + 0.4 * np.clip((tt(95.0) - 40) / 50, 0, 1))
    both(0, d, 0.32, width=1, send=0.2)
    wind = sosfilt(sos_bp(180, 1400), rng.normal(0, 1, int(95 * SR))) * 0.05
    wind *= 0.6 + 0.4 * np.sin(2 * np.pi * tt(95) / 11.0)
    fx(0, wind * np.clip(tt(95) / 6, 0, 1), 0.6, width=1, send=0.1)
    for t0, n in [(4.0, "A4"), (12.5, "D5"), (15.5, "F4")]:
        fx(t0, echo(pluck(NOTE[n], 3.0), 0.46, 0.5, 5), 0.18)
    # spark: reverse swell into a bell + soft sub
    fx(T.SPARK - 2.0, noise_swell(2.0, 800, 10000), 0.18, width=1)
    fx(T.SPARK, echo(bell(NOTE["A5"], 5.0) + bell(NOTE["E6"], 5.0) * 0.5, 0.5, 0.45, 5), 0.30)
    fx(T.SPARK, sub_hit(3.0, 90, 34), 0.45, send=0.2)
    # heartbeat + echo ping on every ring
    for r in T.RINGS:
        late = r >= 88
        fx(r, heartbeat(1.0 if not late else 1.2), 0.55 if not late else 0.7, send=0.15)
        if not late:
            fx(r, echo(bell(NOTE["D6"], 1.5) * 0.4, 0.32, 0.35, 3), 0.07, pan=rng.uniform(-0.5, 0.5))
    # strings enter, then the ticking clock, then staccato basses
    for i, t0 in enumerate(np.arange(40.0, 95.0, 9.6)):
        root, notes = CHORDS[i % 4]
        both(t0, pad(notes, 10.5, fc=1500, att=3.0, rel=3.0), 0.10 + 0.012 * i, width=1, send=0.5)
    for k, t0 in enumerate(np.arange(60.0, 94.8, BEAT / 2)):
        g = 0.05 + 0.10 * (t0 - 60) / 35
        fx(t0, tick(k % 2 == 0), g, pan=0.25 if k % 2 else -0.25, send=0.1)
    for k, t0 in enumerate(np.arange(70.0, 94.8, BEAT / 2)):
        bar = int((t0 - 70.0) // BAR)
        root = NOTE[["D2", "D2", "A#1", "A1"][bar % 4]]
        both(t0, staccato(root), 0.12 + 0.10 * (t0 - 70) / 25, send=0.15)
    fx(86.0, riser(8.9, 60, 1400), 0.35, width=1, send=0.3)
    # BOOM
    fx(T.BOOM, braam(NOTE["D1"], 6.0), 0.60, width=1, send=0.5)
    fx(T.BOOM, taiko(), 0.8, send=0.5)
    fx(T.BOOM, sub_hit(4.0, 120, 30), 0.8, send=0.2)
    fx(T.BOOM, noise_swell(3.0, 300, 8000, rise=False), 0.3, width=1, send=0.8)

    # === Act III: the giant formation (97 - 276), sections A-E on a 100 bpm grid
    end = T.SILENCE[0]
    sections = [(97.0, 135.0, 0), (135.0, 175.0, 1), (175.0, 215.0, 2), (215.0, 250.0, 3), (250.0, end, 4)]
    n_bars = int((end - GRID0) // BAR) + 1
    for b in range(n_bars):
        tb = GRID0 + b * BAR
        if tb >= end:
            break
        sec = max(s for a0, a1, s in sections if tb >= a0)
        prog = (tb - GRID0) / (end - GRID0)
        root, notes = CHORDS[(b // 4) % 4]
        rootf = NOTE[root] * 2
        # pad every 4 bars
        if b % 4 == 0:
            up = ([n.replace("3", "4") for n in notes] if sec >= 2 else [])
            both(tb, pad(notes + up, BAR * 4 + 2.5, fc=1800 + 700 * sec, att=2.0, rel=2.5),
                 0.11 + 0.02 * sec, width=1, send=0.5)
            wd = drone([NOTE[root], NOTE[root] * 1.5], BAR * 4 + 1.0, fc=420)
            both(tb, wd * env_adsr(len(wd), 1.0, 0.5, 1.0, 1.0), 0.14 + 0.02 * sec, width=1, send=0.2)
        # staccato ostinato: 8ths, 16ths from section 1
        step = BEAT / 2 if sec == 0 else BEAT / 4
        for k in range(int(round(BAR / step))):
            t0 = tb + k * step
            if t0 >= end:
                break
            acc = 1.0 if k % (4 if step < 0.2 else 2) == 0 else 0.7
            both(t0, staccato(rootf if k % 8 != 6 else rootf * 1.2), (0.09 + 0.05 * sec) * acc, send=0.12)
        # ticking clock
        for k in range(8 if sec < 3 else 16):
            t0 = tb + k * (BAR / (8 if sec < 3 else 16))
            if t0 < end:
                fx(t0, tick(k % 2 == 0), 0.05 + 0.02 * sec, pan=0.3 if k % 2 else -0.3, send=0.08)
        # drums
        if sec >= 0 and b % 2 == 0:
            fx(tb, taiko(), 0.35 + 0.08 * sec, send=0.5)
        if sec >= 1:
            fx(tb + 2 * BEAT, taiko(1.4, 110, 60), 0.30 + 0.06 * sec, send=0.5)
        if sec >= 2:
            for k in (1.5, 3.0, 3.5):
                fx(tb + k * BEAT, taiko(1.0, 140, 80), 0.20 + 0.05 * sec, pan=rng.uniform(-0.4, 0.4), send=0.4)
        if sec >= 3:
            for k in range(8):
                fx(tb + k * BEAT / 2, taiko(0.6, 180, 100), 0.10 + 0.03 * sec, pan=0.5 if k % 2 else -0.5, send=0.3)
        # braams
        every = {0: 0, 1: 8, 2: 4, 3: 2, 4: 2}[sec]
        if every and b % every == 0:
            fx(tb, braam(NOTE[root], BAR * min(every, 2) + 1.0, bright=0.8 + 0.1 * sec), 0.22 + 0.06 * sec,
               width=1, send=0.5)
        # choir from section 3
        if sec >= 3 and b % 4 == 0:
            both(tb, choir(notes, BAR * 4 + 2.0, att=1.5, rel=2.5), 0.12 + 0.04 * (sec - 3), width=1, send=0.6)
    # growth shimmer: pentatonic glints with echo while the veins grow
    pent = ["D5", "F5", "G5", "A5", "C6", "D6", "F6"]
    for t0 in np.arange(99.0, end - 1, 1.7):
        if rng.uniform() < 0.7:
            fx(t0 + rng.uniform(0, 0.4), echo(bell(NOTE[pent[rng.integers(len(pent))]], 2.0) * 0.5, 0.36, 0.4, 3),
               0.05, pan=rng.uniform(-0.8, 0.8))
    for r in T.GROW_RINGS:
        fx(r, heartbeat(1.0), 0.45, send=0.2)
    # final build into the silence
    fx(258.0, riser(end - 258.0, 70, 2200), 0.38, width=1, send=0.3)
    for k, t0 in enumerate(np.arange(268.0, end, BEAT / 4)):
        fx(t0, taiko(0.5, 170, 95), 0.18 + 0.4 * (t0 - 268) / (end - 268), pan=0.4 if k % 2 else -0.4, send=0.3)

    # === THE HIT (276) and realistic-detail section
    c = T.COMPLETE
    fx(c, braam(NOTE["D1"], 9.0, bright=1.4, notes=[NOTE["D1"], NOTE["D2"], NOTE["A2"], NOTE["D3"], NOTE["F3"]]),
       1.15, width=1, send=0.6)
    fx(c, sub_hit(6.0, 140, 28, 3.0), 1.3, send=0.2)
    fx(c, taiko(2.0, 80, 40), 1.0, send=0.6)
    fx(c + 0.02, taiko(2.0, 100, 50), 0.7, pan=0.3, send=0.6)
    fx(c, noise_swell(5.0, 200, 10000, rise=False), 0.45, width=1, send=1.0)
    both(c, choir(["D3", "F3", "A3", "D4"], 22.0, att=0.25, rel=8.0), 0.34, width=1, send=0.7)
    both(c, pad(["D3", "A3", "D4", "F4"], 24.0, fc=2600, att=0.3, rel=8.0), 0.20, width=1, send=0.6)
    dd = drone([NOTE["D1"], NOTE["A1"]], 30.0, fc=380)
    both(c, dd * env_adsr(len(dd), 0.5, 1, 1, 8), 0.22, width=1, send=0.2)
    for s0, s1 in T.SWEEPS:
        fx(s0, whoosh(s1 - s0), 0.16, width=1, send=0.5)
    for t0 in np.arange(c + 4.0, 298.0, BEAT * 2):
        fx(t0, heartbeat(0.7), 0.30, send=0.2)

    # === the name
    both(T.LOCKUP[0] - 1, pad(["D3", "F3", "A3", "C4"], 16.0, fc=1800, att=3.0, rel=4.0), 0.30, width=1, send=0.6)
    nd = drone([NOTE["D1"], NOTE["A1"]], 32.0, fc=450)
    both(T.LOCKUP[0] - 1, nd * env_adsr(len(nd), 3.0, 1.0, 1.0, 4.0), 0.20, width=1, send=0.2)
    notes_up = ["D5", "F5", "A5", "C6", "D6", "F6", "A6", "C7", "D7", "F6", "A6", "D7", "A6", "D7", "F7"]
    n_letters = 15
    for i in range(n_letters):
        t0 = T.LETTERS[0] + (T.LETTERS[1] - T.LETTERS[0] - 0.9) * i / (n_letters - 1)
        fx(t0, echo(pluck(NOTE[notes_up[i]], 2.2, 0.8), 0.28, 0.45, 4), 0.14, pan=-0.6 + 1.2 * i / (n_letters - 1))
    fx(T.GLINT, echo(bell(NOTE["D6"], 5.0) + bell(NOTE["A6"], 5.0) * 0.5, 0.5, 0.5, 6), 0.26, width=1)
    fx(T.GLINT, sub_hit(4.0, 100, 32), 0.55, send=0.3)
    fx(T.GLINT, braam(NOTE["D1"], 7.0, bright=0.9), 0.35, width=1, send=0.6)
    both(T.TAGLINE[0], pad(["A#2", "D3", "F3", "A3"], 7.0, fc=1600), 0.26, width=1, send=0.6)
    both(T.TAGLINE[0] + 6.0, pad(["A2", "C#3", "E3", "A3"], 7.0, fc=1600), 0.28, width=1, send=0.6)
    for t0 in np.arange(T.TAGLINE[0], T.REVEAL[0] - 0.5, BEAT):
        fx(t0, tick(int((t0 - T.TAGLINE[0]) / BEAT) % 2 == 0), 0.05, send=0.1)

    # === the light: D major reveal
    r0 = T.REVEAL[0]
    fx(r0 - 2.5, noise_swell(2.5, 600, 12000), 0.35, width=1, send=0.4)
    fx(r0 - 2.5, riser(2.5, 200, 1600), 0.25, width=1)
    fx(r0, braam(NOTE["D1"], 8.0, bright=1.6, notes=[NOTE["D2"], NOTE["A2"], NOTE["D3"], NOTE["F#3"], NOTE["A3"]]),
       0.55, width=1, send=0.7)
    fx(r0, sub_hit(5.0, 120, 30), 0.7, send=0.2)
    both(r0, choir(["D4", "F#4", "A4", "D5"], 15.0, att=0.3, rel=6.0), 0.30, width=1, send=0.8)
    both(r0, pad(["D3", "F#3", "A3", "E4"], 16.0, fc=3200, att=0.2, rel=5.0), 0.20, width=1, send=0.7)
    fx(r0, echo(bell(NOTE["F#6"], 5.0), 0.5, 0.5, 5), 0.22)
    # collapse back into the dark
    fx(T.COLLAPSE[0] - 0.4, whoosh(T.COLLAPSE[1] - T.COLLAPSE[0] + 0.4, rev=True), 0.40, width=1, send=0.5)
    fx(T.COLLAPSE[0] - 0.4, noise_swell(T.COLLAPSE[1] - T.COLLAPSE[0] + 0.4, 200, 9000), 0.30, width=1)
    fx(T.COLLAPSE[1], sub_hit(4.0, 90, 30), 0.7, send=0.3)
    ld = drone([NOTE["D1"], NOTE["G#1"]], T.DURATION - T.COLLAPSE[1], fc=320)  # tritone: the dark is calling
    both(T.COLLAPSE[1], ld * env_adsr(len(ld), 2.0, 1.0, 1.0, 4.0), 0.22, width=1, send=0.3)
    for k, t0 in enumerate(np.arange(T.COLLAPSE[1] + 1.0, T.STAR_OUT - 0.3, BEAT)):
        fx(t0, tick(k % 2 == 0), 0.06, pan=0.3 if k % 2 else -0.3, send=0.15)
    fx(T.STAR_OUT, echo(bell(NOTE["D5"], 6.0), 0.55, 0.55, 7), 0.35, width=1)
    fx(T.STAR_OUT, sub_hit(5.0, 70, 26), 0.8, send=0.4)
    fx(T.STAR_OUT, heartbeat(1.0), 0.6, send=0.4)
    return mus, sfx, wet


def voice_track():
    vb = Bus()
    wet = Bus()
    hp = sos_hp(70, 2)
    for idx, t0 in T.VOICE:
        path = os.path.join(HERE, "assets", "voice", f"{idx}.wav")
        x, sr = sf.read(path, always_2d=True)
        x = x.mean(1)
        x = resample_poly(x, SR, sr) if sr != SR else x
        x = sosfilt(hp, x)
        low = sosfilt(sos_lp(160, 2), x)
        pres = sosfilt(sos_bp(2500, 5000, 2), x)
        x = x + low * 0.6 + pres * 0.35  # chest + presence, trailer-voice EQ
        env = np.sqrt(sosfilt(sos_lp(12, 1), x * x) + 1e-9)
        gain = np.minimum(1.0, (0.12 / np.maximum(env, 1e-4)) ** 0.5)  # gentle 2:1 compression
        x = x * gain
        x /= np.max(np.abs(x)) + 1e-9
        st = pan_st(x)
        if idx in (2, 7, 10, 8):  # the lines that should literally echo
            st = echo(x, 0.38, 0.38, 4)
        vb.add(t0, st, 0.62)
        wet.add(t0, st, 0.14)
    return vb, wet


def main():
    mus, sfx, wet = build()
    vb, vwet = voice_track()
    ir = make_ir()
    ir_v = make_ir(2.2, 0.6, 0.25, 0.02, seed=4)
    print("reverb...", flush=True)
    mus_wet = reverb(wet.x, ir)
    v_wet = reverb(vwet.x, ir_v)
    # adaptive sidechain: under every line the score drops exactly enough to keep the
    # narrator at least 6 dB on top (trailer-style), with smooth 0.3 s ramps
    duck = np.ones(N)
    lens = {}
    for idx, t0 in T.VOICE:
        x, sr = sf.read(os.path.join(HERE, "assets", "voice", f"{idx}.wav"))
        lens[idx] = len(x) / sr
    pre = mus.x + mus_wet * 0.55 + sfx.x
    for idx, t0 in T.VOICE:
        i0, i1 = int((t0 + 0.3) * SR), int((t0 + lens[idx]) * SR)
        vr = np.sqrt(np.mean(vb.x[:, i0:i1] ** 2)) + 1e-9
        mr = np.sqrt(np.mean(pre[:, i0:i1] ** 2)) + 1e-9
        g = min(0.8, vr / (mr * 10 ** (6.0 / 20)))
        a0, a1 = int((t0 + 0.1) * SR), int((t0 + lens[idx] + 0.4) * SR)
        duck[a0:a1] = np.minimum(duck[a0:a1], g)
    lp = sos_lp(1.2, 1)
    duck = sosfilt(lp, sosfilt(lp, duck)[::-1])[::-1]
    duck = np.minimum(duck, 1.0)
    duck_fx = duck
    # the held breath: hard-gate everything except the breath itself before the hit
    tgrid = np.arange(N) / SR
    gate = np.ones(N)
    a, b = T.SILENCE
    gate -= (1 - 0.01) * np.clip((tgrid - a) / 0.06, 0, 1) * (tgrid < b)
    music = ((mus.x + mus_wet * 0.55) * duck + sfx.x * duck_fx) * gate
    breath = Bus()
    breath.add(a - 0.05, whoosh(b - a + 0.05, rev=True), 0.3, width=1)
    mix = music + breath.x + vb.x + v_wet * 0.8
    # stats: narration vs score inside each line
    for idx, t0 in T.VOICE:
        i0, i1 = int((t0 + 0.4) * SR), int((t0 + 2.5) * SR)
        vr = np.sqrt(np.mean(vb.x[:, i0:i1] ** 2)) + 1e-9
        mr = np.sqrt(np.mean(music[:, i0:i1] ** 2)) + 1e-9
        print(f"voice {idx:2d} @ {t0:6.1f}s  voice-to-score {20 * np.log10(vr / mr):5.1f} dB", flush=True)
    mix = sosfilt(sos_hp(25, 2), mix, axis=1)
    # master: soft saturation then peak normalise
    mix = np.tanh(mix * 1.1) / 1.1
    fade_in = np.clip(np.arange(N) / (0.5 * SR), 0, 1)
    fade_out = np.clip((T.DURATION * SR - np.arange(N)) / (2.0 * SR), 0, 1)
    mix *= fade_in * fade_out
    mix = mix[:, :int(T.DURATION * SR)]
    mix /= np.max(np.abs(mix)) + 1e-9
    mix *= 10 ** (-1.0 / 20)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    sf.write(os.path.join(HERE, "out", "soundtrack_raw.wav"), mix.T.astype(np.float32), SR, subtype="FLOAT")
    print("wrote out/soundtrack_raw.wav", flush=True)


if __name__ == "__main__":
    main()
