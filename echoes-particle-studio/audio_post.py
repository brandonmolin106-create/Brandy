"""Vocal chain, emotion-driven reverb/echo sends, ducking and mastering."""
import math

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from pedalboard import (Compressor, Delay, Gain, HighpassFilter, HighShelfFilter, Limiter, LowpassFilter,
                        LowShelfFilter, Pedalboard, PeakFilter, PitchShift, Reverb)
from scipy import signal

from sfx import SR, fx, secs, svf


def load_vocal(path):
    x, sr = sf.read(path, dtype='float32', always_2d=True)
    m = x.mean(1)
    if sr != SR:
        g = math.gcd(SR, sr)
        m = signal.resample_poly(m, SR // g, sr // g).astype(np.float32)
    return m


def envelope(x, attack=0.005, release=0.12):
    """Peak follower (mono)."""
    a = math.exp(-1 / (attack * SR))
    r = math.exp(-1 / (release * SR))
    y = np.abs(x).astype(np.float32)
    return _follow(y, np.float32(a), np.float32(r))


import numba as nb


@nb.njit(cache=True)
def _follow(y, a, r):
    out = np.empty_like(y)
    e = 0.0
    for i in range(y.shape[0]):
        v = y[i]
        if v > e:
            e = a * e + (1 - a) * v
        else:
            e = r * e + (1 - r) * v
        out[i] = e
    return out


def deess(x, freq=6500.0, thresh_db=-30.0, ratio=4.0):
    sos = signal.butter(4, [freq * 0.75, min(freq * 1.6, SR / 2 - 100)], 'bandpass', fs=SR, output='sos')
    band = signal.sosfilt(sos, x).astype(np.float32)
    env = envelope(band, 0.001, 0.05)
    lvl = 20 * np.log10(env + 1e-9)
    over = np.maximum(lvl - thresh_db, 0)
    red = over * (1 - 1 / ratio)
    g = 10 ** (-red / 20)
    return (x - band + band * g).astype(np.float32)


def vocal_chain(x):
    # gentle downward expander to kill residual bleed in pauses
    env = envelope(x, 0.002, 0.15)
    lvl = 20 * np.log10(env + 1e-9)
    gate_db = np.clip((lvl + 48) * 1.5, -18, 0)
    gate_db = signal.savgol_filter(gate_db, 481, 2)
    x = x * (10 ** (np.minimum(gate_db, 0) / 20)).astype(np.float32)
    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=78),
        LowShelfFilter(cutoff_frequency_hz=180, gain_db=1.0, q=0.7),
        PeakFilter(cutoff_frequency_hz=320, gain_db=-2.5, q=1.0),
        PeakFilter(cutoff_frequency_hz=3400, gain_db=2.5, q=0.9),
        HighShelfFilter(cutoff_frequency_hz=10500, gain_db=2.5, q=0.7),
        Compressor(threshold_db=-24, ratio=3.2, attack_ms=4, release_ms=90),
        Gain(gain_db=5.0),
        Compressor(threshold_db=-12, ratio=2.0, attack_ms=12, release_ms=160),
    ])
    y = board(x[None, :], SR)[0]
    y = deess(y)
    return y.astype(np.float32)


def curve(keys, n, default=0.0, smooth=0.08):
    """Piecewise-linear automation from [(t, v), ...] keyframes -> per-sample array."""
    if not keys:
        return np.full(n, default, np.float32)
    ks = sorted(keys)
    t = np.array([k[0] for k in ks]) * SR
    v = np.array([k[1] for k in ks], np.float32)
    c = np.interp(np.arange(n), t, v).astype(np.float32)
    if smooth:
        w = max(3, secs(smooth) | 1)
        c = np.convolve(c, np.ones(w, np.float32) / w, mode='same').astype(np.float32)
    return c


REVERBS = {
    'room': dict(room_size=0.35, damping=0.55, width=0.8),
    'hall': dict(room_size=0.78, damping=0.45, width=1.0),
    'cathedral': dict(room_size=0.95, damping=0.3, width=1.0),
    'plate': dict(room_size=0.6, damping=0.2, width=1.0),
}


def reverb_send(x, send, kind='hall', pre_delay=0.02, hp=250, lp=9000, tail=6.0):
    """x mono, send per-sample gain -> stereo wet (n + tail)."""
    n = len(x)
    s = np.concatenate([x * send, np.zeros(secs(tail), np.float32)])
    s = np.concatenate([np.zeros(secs(pre_delay), np.float32), s])[: n + secs(tail)]
    st = np.stack([s, s], -1)
    p = REVERBS[kind]
    return fx(st, HighpassFilter(cutoff_frequency_hz=hp), Reverb(wet_level=1.0, dry_level=0.0, **p),
              LowpassFilter(cutoff_frequency_hz=lp))


def echo_throws(x, throws, bpm_delay=0.42, feedback=0.48, tail=5.0):
    """throws: list of (t_start, t_end, gain, pan_dir). Ping-pong filtered echoes of those words."""
    n = len(x)
    L = np.zeros(n + secs(tail), np.float32)
    R = np.zeros(n + secs(tail), np.float32)
    for (t0, t1, g, direction) in throws:
        a, b = secs(t0), secs(t1)
        seg = x[a:b].copy()
        if len(seg) < 10:
            continue
        fade = min(len(seg) // 4, secs(0.02))
        seg[:fade] *= np.linspace(0, 1, fade)
        seg[-fade:] *= np.linspace(1, 0, fade)
        sos = signal.butter(2, [500, 4500], 'bandpass', fs=SR, output='sos')
        seg = signal.sosfilt(sos, seg).astype(np.float32)
        d = secs(bpm_delay)
        amp = g
        k = 1
        side = direction
        while amp > 0.02 and a + k * d < len(L):
            s0 = a + k * d
            s1 = min(len(L), s0 + len(seg))
            chunk = seg[: s1 - s0] * amp
            if side > 0:
                R[s0:s1] += chunk
                L[s0:s1] += chunk * 0.35
            else:
                L[s0:s1] += chunk
                R[s0:s1] += chunk * 0.35
            side = -side
            amp *= feedback
            seg = signal.sosfilt(signal.butter(1, 3000, 'lowpass', fs=SR, output='sos'), seg).astype(np.float32)
            k += 1
    st = np.stack([L, R], -1)
    return fx(st, Reverb(room_size=0.7, wet_level=0.35, dry_level=1.0, width=1.0))


def octave_double(x, gate, semis=-12, amount=0.28):
    """Low octave shadow under the voice on the heaviest lines (gate: per-sample 0..1)."""
    y = Pedalboard([PitchShift(semitones=semis), LowpassFilter(cutoff_frequency_hz=1400)])(x[None, :], SR)[0]
    return (y * gate * amount).astype(np.float32)


def duck(bed, key, depth_db=7.0, attack=0.03, release=0.35):
    env = envelope(key, attack, release)
    lvl = np.clip(env / (np.percentile(env[env > 1e-4], 80) + 1e-9), 0, 1)
    g = 10 ** (-depth_db * lvl / 20)
    n = min(len(bed), len(g))
    out = bed.copy()
    out[:n] *= g[:n, None]
    return out


@nb.njit(cache=True)
def _lookahead_gain(greq, D, release):
    """Backward sliding min over D+1 samples, moving average over D, then slow release."""
    n = greq.shape[0]
    g1 = np.empty(n, np.float32)
    dq = np.empty(n, np.int64)
    head = 0
    tail = 0
    for i in range(n):
        while tail > head and greq[dq[tail - 1]] >= greq[i]:
            tail -= 1
        dq[tail] = i
        tail += 1
        while dq[head] < i - D:
            head += 1
        g1[i] = greq[dq[head]]
    g2 = np.empty(n, np.float32)
    acc = 0.0
    for i in range(n):
        acc += g1[i]
        if i >= D:
            acc -= g1[i - D]
            g2[i] = acc / D
        else:
            g2[i] = acc / (i + 1)
    out = np.empty(n, np.float32)
    y = 1.0
    for i in range(n):
        v = g2[i]
        if v < y:
            y = v
        else:
            y = y + (v - y) * release
        out[i] = y
    return out


def limit(x, ceiling_db=-1.5, lookahead_ms=5.0, release_ms=120.0):
    """Brickwall lookahead limiter (no makeup gain). x: (n, 2)."""
    c = 10 ** (ceiling_db / 20)
    D = max(1, int(SR * lookahead_ms / 1000))
    pk = np.abs(x).max(1)
    greq = np.minimum(1.0, c / np.maximum(pk, 1e-9)).astype(np.float32)
    g = _lookahead_gain(greq, D, np.float32(1 - math.exp(-1 / (release_ms / 1000 * SR))))
    xd = np.concatenate([np.zeros((D, 2), np.float32), x[:-D]])
    y = xd * g[:, None]
    return np.clip(y, -c, c).astype(np.float32), D


def master(mix, target_lufs=-14.0, ceiling_db=-1.0):
    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=24),
        Compressor(threshold_db=-18, ratio=1.8, attack_ms=25, release_ms=250),
    ])
    y = fx(mix, *board)
    meter = pyln.Meter(SR)
    g = 0.0
    for _ in range(3):
        loud = meter.integrated_loudness(y * (10 ** (g / 20)))
        g += target_lufs - loud
        lim, D = limit(y * (10 ** (g / 20)), ceiling_db - 0.5)
        got = meter.integrated_loudness(lim)
        g += (target_lufs - got) * 0.9
    lim, D = limit(y * (10 ** (g / 20)), ceiling_db - 0.5)
    lim = lim[D:]
    return lim.astype(np.float32), meter.integrated_loudness(lim)
