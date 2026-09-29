"""Procedural sound design + score instruments (all synthesized, royalty free).

Everything returns float32 stereo arrays shaped (n, 2) at SR.
"""
import math

import numba as nb
import numpy as np
from pedalboard import Chorus, Distortion, HighpassFilter, LowpassFilter, Pedalboard, Reverb
from scipy import signal

SR = 48000
_rng = np.random.default_rng(11)


def secs(n):
    return int(round(n * SR))


def rng(seed=None):
    return np.random.default_rng(seed) if seed is not None else _rng


# ------------------------------------------------------------------ helpers

@nb.njit(cache=True, fastmath=True)
def svf(x, cutoff, q, mode):
    """TPT state-variable filter with per-sample cutoff (Hz). mode 0=lp 1=bp 2=hp."""
    n = x.shape[0]
    y = np.empty(n, np.float32)
    ic1 = 0.0
    ic2 = 0.0
    k = 1.0 / q
    for i in range(n):
        fc = cutoff[i]
        if fc < 10.0:
            fc = 10.0
        if fc > 0.45 * 48000.0:
            fc = 0.45 * 48000.0
        g = math.tan(math.pi * fc / 48000.0)
        a1 = 1.0 / (1.0 + g * (g + k))
        a2 = g * a1
        a3 = g * a2
        v3 = x[i] - ic2
        v1 = a1 * ic1 + a2 * v3
        v2 = ic2 + a2 * ic1 + a3 * v3
        ic1 = 2.0 * v1 - ic1
        ic2 = 2.0 * v2 - ic2
        if mode == 0:
            y[i] = v2
        elif mode == 1:
            y[i] = v1 * k
        else:
            y[i] = x[i] - k * v1 - v2
    return y


def sweep(n, a, b, curve='exp'):
    t = np.linspace(0, 1, n, dtype=np.float32)
    if curve == 'exp':
        return (a * (b / a) ** t).astype(np.float32)
    return (a + (b - a) * t).astype(np.float32)


def pan(mono, p):
    """Constant-power pan. p in [-1, 1] (scalar or per-sample array)."""
    p = np.clip(np.asarray(p, np.float32), -1, 1)
    ang = (p + 1) * (math.pi / 4)
    return np.stack([mono * np.cos(ang), mono * np.sin(ang)], -1).astype(np.float32)


def widen(mono, width=1.0, seed=None):
    """Decorrelated stereo from mono using two short random-phase allpass chains."""
    r = rng(seed)
    out = []
    for _ in range(2):
        y = mono.copy()
        for _k in range(3):
            d = int(r.integers(40, 400))
            g = 0.5
            b = np.zeros(d + 1, np.float32); b[0] = -g; b[-1] = 1
            a = np.zeros(d + 1, np.float32); a[0] = 1; a[-1] = -g
            y = signal.lfilter(b, a, y).astype(np.float32)
        out.append(y)
    mid = mono
    L = mid * (1 - width * 0.5) + out[0] * width * 0.5
    R = mid * (1 - width * 0.5) + out[1] * width * 0.5
    return np.stack([L, R], -1).astype(np.float32)


def fx(x, *plugins):
    board = Pedalboard(list(plugins))
    y = board(np.ascontiguousarray(x.T), SR)
    return np.ascontiguousarray(y.T).astype(np.float32)


def tail(x, seconds):
    return np.concatenate([x, np.zeros((secs(seconds), x.shape[1]), np.float32)])


def verb(x, room=0.8, wet=0.35, dry=1.0, damping=0.5, width=1.0, pad=2.5):
    return fx(tail(x, pad), Reverb(room_size=room, wet_level=wet, dry_level=dry, damping=damping, width=width))


def norm(x, peak=0.9):
    m = float(np.max(np.abs(x))) + 1e-9
    return (x * (peak / m)).astype(np.float32)


def env_ar(n, a, r, curve=3.0):
    """Attack/release envelope over n samples, a/r as fractions or seconds (<1 => fraction)."""
    t = np.linspace(0, 1, n, dtype=np.float32)
    na = a if a > 1 else a * n
    e = np.ones(n, np.float32)
    ia = int(max(1, na))
    e[:ia] = (np.linspace(0, 1, ia) ** 2)
    ir = int(max(1, r if r > 1 else r * n))
    e[-ir:] *= np.exp(-curve * np.linspace(0, 1, ir)) * np.linspace(1, 0, ir) ** 0.5
    return e


def noise(n, color='white', seed=None):
    r = rng(seed)
    w = r.standard_normal(n).astype(np.float32)
    if color == 'white':
        return w
    if color == 'pink':
        b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
        a = [1, -2.494956002, 2.017265875, -0.522189400]
        return (signal.lfilter(b, a, w) * 3.5).astype(np.float32)
    if color == 'brown':
        y = np.cumsum(w) * 0.02
        y = signal.lfilter([1, -1], [1, -0.995], y)
        return (y / (np.std(y) + 1e-9) * 0.5).astype(np.float32)
    raise ValueError(color)


# ------------------------------------------------------------------ sound effects

def whoosh(dur=1.2, p0=-0.8, p1=0.8, f0=250, fpk=2800, f1=500, peak=0.62, seed=None, air=0.6):
    n = secs(dur)
    t = np.linspace(0, 1, n, dtype=np.float32)
    cut = np.where(t < peak, f0 * (fpk / f0) ** (t / peak), fpk * (f1 / fpk) ** ((t - peak) / (1 - peak))).astype(np.float32)
    x = svf(noise(n, 'pink', seed), cut, 1.3, 1)
    lo = svf(noise(n, 'brown', None if seed is None else seed + 1), (cut * 0.12).astype(np.float32), 0.8, 0)
    amp = np.exp(-((t - peak) / 0.22) ** 2).astype(np.float32)
    mono = (x + lo * air) * amp
    st = pan(mono, p0 + (p1 - p0) * t)
    return verb(norm(st, 0.7), room=0.5, wet=0.18, pad=1.0)


def impact(size=1.0, tone=48.0, seed=None, metal=0.35, tail_s=3.5):
    n = secs(2.4 * size + 0.5)
    t = np.arange(n, dtype=np.float32) / SR
    f = tone + tone * 1.6 * np.exp(-t / 0.045)
    ph = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(ph) * np.exp(-t / (0.55 * size))
    click = svf(noise(n, 'white', seed), np.full(n, 2600, np.float32), 0.7, 0) * np.exp(-t / 0.012)
    body = svf(noise(n, 'pink', seed), np.full(n, 420, np.float32), 0.9, 0) * np.exp(-t / 0.09)
    ring = np.zeros(n, np.float32)
    for k, (fr, dec) in enumerate([(211, 0.9), (347.5, 0.7), (521, 0.5), (788, 0.35), (1102, 0.25)]):
        ring += np.sin(2 * np.pi * fr * t + k) * np.exp(-t / (dec * size)) / (k + 1)
    mono = sub * 1.0 + click * 0.5 + body * 0.9 + ring * metal * 0.25
    mono = np.tanh(mono * 1.6) / 1.2
    st = widen(mono.astype(np.float32), 0.35, seed)
    st[:, 0] += sub * 0.25
    st[:, 1] += sub * 0.25
    return verb(norm(st, 0.9), room=0.92, wet=0.32, damping=0.35, pad=tail_s)


def riser(dur=3.0, f0=180, f1=5200, pulse=True, seed=None, tonal=True):
    n = secs(dur)
    t = np.linspace(0, 1, n, dtype=np.float32)
    cut = (f0 * (f1 / f0) ** (t ** 1.3)).astype(np.float32)
    nz = svf(noise(n, 'white', seed), cut, 2.2, 1)
    mono = nz * 0.8
    if tonal:
        pitch = 90 * (8.0 ** (t ** 1.6))
        ph = 2 * np.pi * np.cumsum(pitch) / SR
        saw = sum(np.sin(ph * h + h) / h for h in range(1, 7)).astype(np.float32)
        saw2 = sum(np.sin(ph * 1.007 * h) / h for h in range(1, 7)).astype(np.float32)
        mono = mono + svf(((saw + saw2) * 0.18).astype(np.float32), cut, 0.9, 0)
    amp = (t ** 2.2).astype(np.float32)
    if pulse:
        rate = 2.0 + 22.0 * t ** 2
        lfo = 0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(rate) / SR)
        amp = amp * (0.55 + 0.45 * lfo)
    st = widen((mono * amp).astype(np.float32), 0.9, seed)
    return fx(norm(st, 0.8), Reverb(room_size=0.7, wet_level=0.25, dry_level=1.0))


def reverse_swell(dur=2.0, freqs=(146.8, 220.0, 293.7, 440.0), seed=None):
    n = secs(dur)
    t = np.arange(n, dtype=np.float32) / SR
    x = np.zeros(n, np.float32)
    for f in freqs:
        x += np.sin(2 * np.pi * f * t) * np.exp(-t / 0.4)
    x += noise(n, 'pink', seed) * np.exp(-t / 0.15) * 0.3
    st = verb(widen(x, 0.8, seed), room=0.95, wet=0.9, dry=0.2, pad=0.1)[:n]
    return norm(st[::-1].copy() * np.linspace(0.2, 1, n, dtype=np.float32)[:, None] ** 2, 0.7)


def shimmer(dur=2.5, density=38, fmin=2200, fmax=9000, seed=None):
    r = rng(seed)
    n = secs(dur)
    out = np.zeros((n, 2), np.float32)
    k = int(density * dur)
    for _ in range(k):
        f = math.exp(r.uniform(math.log(fmin), math.log(fmax)))
        L = secs(r.uniform(0.08, 0.35))
        s0 = int(r.integers(0, max(1, n - L)))
        tt = np.arange(L, dtype=np.float32) / SR
        blip = np.sin(2 * np.pi * f * tt) * np.exp(-tt / (L / SR / 4)) * r.uniform(0.2, 1)
        out[s0:s0 + L] += pan(blip.astype(np.float32), r.uniform(-0.9, 0.9))
    env = env_ar(n, 0.25, 0.4)[:, None]
    return verb(norm(out * env, 0.5), room=0.9, wet=0.55, dry=0.6, pad=2.5)


def sub_drop(dur=1.8, f0=90, f1=26):
    n = secs(dur)
    t = np.arange(n, dtype=np.float32) / SR
    f = f1 + (f0 - f1) * np.exp(-t / (dur * 0.3))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (dur * 0.45))
    x = np.tanh(x * 1.4)
    return norm(np.stack([x, x], -1).astype(np.float32), 0.9)


def heartbeat(bpm=62, beats=4, seed=None):
    period = 60.0 / bpm
    n = secs(period * beats + 0.8)
    out = np.zeros(n, np.float32)
    for b in range(beats):
        for off, amp in ((0.0, 1.0), (0.26, 0.7)):
            s0 = secs(b * period + off)
            L = secs(0.35)
            tt = np.arange(L, dtype=np.float32) / SR
            thump = np.sin(2 * np.pi * (48 + 30 * np.exp(-tt / 0.03)) * tt) * np.exp(-tt / 0.09) * amp
            out[s0:s0 + L] += thump
    out = svf(out, np.full(n, 240, np.float32), 0.7, 0)
    return norm(np.stack([out, out], -1), 0.85)


def wind(dur=8.0, seed=None, bright=900.0):
    r = rng(seed)
    n = secs(dur)
    ctrl = np.interp(np.arange(n), np.linspace(0, n, 12), r.uniform(0.3, 1.0, 12)).astype(np.float32)
    ctrl = signal.savgol_filter(ctrl, 2001, 2).astype(np.float32)
    chans = []
    for c in range(2):
        cut = (bright * 0.35 + bright * ctrl * (0.8 + 0.2 * c)).astype(np.float32)
        chans.append(svf(noise(n, 'pink', None if seed is None else seed + c), cut, 1.6, 1) * (0.4 + 0.6 * ctrl))
    st = np.stack(chans, -1)
    return norm(st * env_ar(n, 0.15, 0.15)[:, None], 0.6)


def rain(dur=8.0, seed=None, intensity=1.0):
    r = rng(seed)
    n = secs(dur)
    bed = svf(noise(n, 'pink', seed), np.full(n, 3500, np.float32), 0.6, 2) * 0.25
    drops = np.zeros(n, np.float32)
    k = int(900 * dur * intensity)
    idx = r.integers(0, n - 200, k)
    amps = r.uniform(0.1, 1.0, k) ** 2
    np.add.at(drops, idx, amps)
    drops = svf(drops, np.full(n, 4200, np.float32), 1.2, 1)
    st = widen((bed + drops * 0.8).astype(np.float32), 1.0, seed)
    return norm(st * env_ar(n, 0.1, 0.1)[:, None], 0.5)


def ocean(dur=10.0, period=7.5, seed=None):
    n = secs(dur)
    t = np.arange(n, dtype=np.float32) / SR
    swell = (0.5 + 0.5 * np.sin(2 * np.pi * t / period - 1.2)) ** 3
    cut = (250 + 2600 * swell).astype(np.float32)
    chans = []
    for c in range(2):
        chans.append(svf(noise(n, 'pink', None if seed is None else seed + c), cut, 0.7, 0) * (0.15 + 0.85 * swell))
    return norm(np.stack(chans, -1) * env_ar(n, 0.1, 0.1)[:, None], 0.6)


def fire(dur=8.0, seed=None):
    r = rng(seed)
    n = secs(dur)
    rumble = svf(noise(n, 'brown', seed), np.full(n, 180, np.float32), 0.7, 0) * 0.6
    pops = np.zeros(n, np.float32)
    k = int(14 * dur)
    for _ in range(k):
        s0 = int(r.integers(0, n - 4000))
        L = int(r.integers(200, 3000))
        tt = np.arange(L, dtype=np.float32)
        pops[s0:s0 + L] += r.standard_normal(L).astype(np.float32) * np.exp(-tt / (L / 5)) * r.uniform(0.2, 1.0)
    pops = svf(pops, np.full(n, 2400, np.float32), 0.8, 1)
    st = widen((rumble + pops).astype(np.float32), 0.8, seed)
    return norm(st * env_ar(n, 0.1, 0.1)[:, None], 0.55)


def tick(tock=False):
    n = secs(0.12)
    t = np.arange(n, dtype=np.float32) / SR
    f = 1900 if not tock else 1450
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.012) + noise(n, 'white') * np.exp(-t / 0.002) * 0.6
    x = svf(x.astype(np.float32), np.full(n, 3200, np.float32), 1.5, 1)
    return norm(np.stack([x, x], -1), 0.6)


def clock(dur=4.0, bpm=60):
    n = secs(dur)
    out = np.zeros((n, 2), np.float32)
    per = 60.0 / bpm
    k = 0
    while k * per < dur - 0.2:
        s = tick(k % 2 == 1)
        s0 = secs(k * per)
        out[s0:s0 + len(s)] += s
        k += 1
    return verb(out, room=0.6, wet=0.25, pad=1.0)


def glitch(dur=0.6, seed=None):
    r = rng(seed)
    n = secs(dur)
    base = noise(secs(0.05), 'white', seed)
    out = np.zeros(n, np.float32)
    pos = 0
    while pos < n:
        L = int(r.integers(300, 3000))
        f = r.uniform(200, 4000)
        tt = np.arange(L, dtype=np.float32) / SR
        seg = np.sign(np.sin(2 * np.pi * f * tt)) * 0.3 + np.resize(base, L) * 0.3
        seg *= r.uniform(0.2, 1)
        out[pos:pos + L] += seg[: max(0, min(L, n - pos))]
        pos += L + int(r.integers(0, 1500))
    return norm(pan(out, float(r.uniform(-0.5, 0.5))) * env_ar(n, 0.01, 0.2)[:, None], 0.4)


def braam(dur=4.0, root=36.71, seed=None):
    """Huge low brass 'braam' for the heaviest moments."""
    n = secs(dur)
    t = np.arange(n, dtype=np.float32) / SR
    x = np.zeros(n, np.float32)
    for mul, amp in ((1, 1.0), (1.5, 0.6), (2, 0.8), (3, 0.3)):
        for det in (-0.004, 0.0, 0.005):
            f = root * mul * (1 + det)
            ph = 2 * np.pi * f * t
            x += sum(np.sin(ph * h) / h for h in range(1, 12)).astype(np.float32) * amp * 0.2
    cut = (120 + 1800 * (1 - np.exp(-t / 0.25)) * np.exp(-t / (dur * 0.6))).astype(np.float32)
    y = svf(x, cut, 0.9, 0)
    y = np.tanh(y * 2.5)
    y *= env_ar(n, 0.04, 0.5)
    st = widen(y.astype(np.float32), 0.5, seed)
    return verb(norm(st, 0.9), room=0.95, wet=0.4, damping=0.4, pad=3.0)


# ------------------------------------------------------------------ instruments for the score

def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def felt_piano(m, dur=4.0, vel=0.7, seed=None):
    f = midi(m)
    n = secs(dur)
    t = np.arange(n, dtype=np.float32) / SR
    B = 0.00012
    x = np.zeros(n, np.float32)
    bright = 0.6 + 0.8 * vel
    for k in range(1, 16):
        fk = f * k * math.sqrt(1 + B * k * k)
        if fk > 12000:
            break
        amp = (1.0 / k ** (1.9 - 0.5 * bright)) * (1 + 0.2 * math.sin(k * 1.7))
        tau = (2.4 * dur / 4.0) / (1 + 0.45 * k) * (220 / max(f, 60)) ** 0.25
        x += (np.sin(2 * np.pi * fk * t + k * 0.3) * np.exp(-t / tau) * amp).astype(np.float32)
    ham = svf(noise(n, 'pink', seed), np.full(n, 900, np.float32), 0.7, 0) * np.exp(-t / 0.018) * 0.35
    x = x + ham
    x *= np.minimum(1, t / 0.006)
    x *= np.minimum(1, (n - np.arange(n)) / secs(0.3))
    x = svf(x.astype(np.float32), np.full(n, 1600 + 2200 * vel, np.float32), 0.6, 0)
    return (pan(x, 0.0) * vel).astype(np.float32)


def pad(notes, dur=8.0, bright=0.5, seed=None, attack=2.0, release=2.5, detune=0.006):
    n = secs(dur)
    t = np.arange(n, dtype=np.float32) / SR
    out = np.zeros((n, 2), np.float32)
    r = rng(seed)
    for m in notes:
        f = midi(m)
        for c in range(2):
            x = np.zeros(n, np.float32)
            for v in range(3):
                d = 1 + detune * (v - 1) + r.uniform(-0.001, 0.001)
                ph = 2 * np.pi * f * d * t + r.uniform(0, 6.28)
                x += sum(np.sin(ph * h) / h for h in range(1, 9)).astype(np.float32)
            lfo = 0.5 + 0.5 * np.sin(2 * np.pi * (0.07 + 0.03 * c) * t + r.uniform(0, 6))
            cut = (300 + 2200 * bright * (0.6 + 0.4 * lfo)).astype(np.float32)
            out[:, c] += svf(x * 0.08, cut, 0.8, 0)
    e = np.ones(n, np.float32)
    na, nr = secs(min(attack, dur / 2)), secs(min(release, dur / 2))
    e[:na] = np.linspace(0, 1, na) ** 1.5
    e[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    return (out * e[:, None] / max(1, len(notes)) ** 0.5).astype(np.float32)


def choir(notes, dur=6.0, seed=None, vowel='ah'):
    """Formant-filtered saw ensemble with vibrato, a soft 'aah' choir."""
    formants = {'ah': [(800, 1.0, 80), (1150, 0.5, 90), (2900, 0.25, 120)],
                'oo': [(350, 1.0, 60), (600, 0.4, 60), (2700, 0.1, 100)]}[vowel]
    n = secs(dur)
    t = np.arange(n, dtype=np.float32) / SR
    r = rng(seed)
    out = np.zeros((n, 2), np.float32)
    for m in notes:
        for voice in range(4):
            f = midi(m) * (1 + r.uniform(-0.004, 0.004))
            vib = 1 + 0.006 * np.sin(2 * np.pi * r.uniform(4.5, 5.8) * t + r.uniform(0, 6))
            ph = 2 * np.pi * np.cumsum(f * vib) / SR
            src = sum(np.sin(ph * h) / h for h in range(1, 30) if f * h < 9000).astype(np.float32)
            y = np.zeros(n, np.float32)
            for (fc, g, bw) in formants:
                y += svf(src, np.full(n, fc, np.float32), fc / bw, 1) * g
            out += pan(y * 0.05, r.uniform(-0.7, 0.7))
    e = env_ar(n, 0.35, 0.35)
    return (out * e[:, None] / max(1, len(notes)) ** 0.5).astype(np.float32)


def strings(notes, dur=6.0, seed=None, bright=0.5):
    n = secs(dur)
    t = np.arange(n, dtype=np.float32) / SR
    r = rng(seed)
    out = np.zeros((n, 2), np.float32)
    for m in notes:
        for voice in range(5):
            f = midi(m) * (1 + r.uniform(-0.003, 0.003))
            vib = 1 + 0.004 * np.sin(2 * np.pi * r.uniform(4.8, 6.0) * t + r.uniform(0, 6))
            ph = 2 * np.pi * np.cumsum(f * vib) / SR
            src = sum(np.sin(ph * h) / h for h in range(1, 20) if f * h < 10000).astype(np.float32)
            env = env_ar(n, 0.4, 0.3)
            cut = (400 + 3000 * bright * env).astype(np.float32)
            out += pan(svf(src, cut, 0.7, 0) * 0.05, r.uniform(-0.8, 0.8))
    return (out / max(1, len(notes)) ** 0.5).astype(np.float32)
