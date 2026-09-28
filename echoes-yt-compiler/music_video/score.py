#!/usr/bin/env python3
"""Stage 2 of the cinematic music video: synthesise the suspense score from numpy/scipy alone.

    WORK=<work dir> python3 music_video/score.py

Reads $WORK/mv/timeline.json (70 BPM, 4/4, section and spoken-line times) and writes
$WORK/mv/score.wav (48 kHz stereo 16-bit, exactly `total` seconds, about -18 LUFS, true peak
under -1 dBTP, ducked ~5 dB under every spoken line) and $WORK/mv/score_spectrogram.png.
There are no samples or presets: every sound is an oscillator, filtered noise or a generated
impulse response, so the score is copyright-free.

D minor, A4 = 440 Hz equal temperament.
  intro       sub drone D1+D2, clock tick-tock, sparse felt piano, fading in from silence
  time        + dark low string pad on Dm, reverse swells into every bar line
  hole        + heartbeat, strings Dm | Bb | F | C, quieter clock
  glass       music under a low-pass rising 600 Hz -> 2.5 kHz, water, glass harmonica
  road        8th pulse, opening strings, taiko downbeats, 16th pluck ostinato, snare roll
  riser       noise sweep, rising tone, accelerating ticks, then the suck-back silence
  chains      impact + braam, taiko groove, braams every 2 bars, full strings, ostinato
  everything  drums out: warm pad + piano motif, Bb | F | C | Dm | Bb | F | C | D
  outro       pad + piano, the clock returns and stops, final boom, tail to silence
"""
import json
import os
import time
import wave

import numpy as np
from scipy.fft import irfft, rfft, rfftfreq
from scipy.signal import butter, fftconvolve, lfilter, resample_poly, sosfilt, sosfiltfilt

WORK = os.path.abspath(os.environ.get('WORK', '.'))
MV = os.path.join(WORK, 'mv')
TL = json.load(open(os.path.join(MV, 'timeline.json')))
SR, BAR = TL['sr'], TL['bar']
BEAT = BAR / 4
TOTAL = TL['total']
N = int(round(TOTAL * SR))
SEC = {s['name']: s for s in TL['sections']}
BAR0 = {s['name']: int(round(s['start'] / BAR)) for s in TL['sections']}
DROP_BAR = int(round(TL['drop'] / BAR))
TARGET_LUFS, CEILING_DBTP, DUCK_DB = -18.0, -1.5, -9.0


def T(bar, beat=0.0):
    """Seconds at a bar (0-based from the top of the track) plus beats."""
    return bar * BAR + beat * BEAT


def ns(sec):
    return int(round(sec * SR))


def db(x):
    return 10.0 ** (np.asarray(x) / 20.0)


def hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


_PC = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6,
       'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}


def mid(names):
    """'D2 A2 F#3' -> [38, 45, 54] (MIDI, C4 = 60)."""
    return [_PC[s[:-1]] + 12 * (int(s[-1]) + 1) for s in names.split()]


# ------------------------------------------------------------------------------ harmony
CHART = (['-'] * 5 + ['Dm'] * 6                                   # intro (drone only), time
         + 'Dm Bb F C Dm Bb F C Dm Bb'.split()                     # hole
         + 'Dm Dm Bb Bb F F C'.split()                             # glass: two bars per chord
         + 'Dm Bb F C Dm Bb F C Bb'.split()                        # road
         + ['C', 'C']                                              # riser: VI -> VII -> i at the drop
         + 'Dm Bb F C Dm Bb F C Dm Bb F C Dm Asus|A'.split()       # chains, ends on the dominant
         + 'Bb F C Dm Bb F C D'.split()                            # everything: V -> VI, ends in D major
         + 'D D Gm/D D D'.split())                                 # outro
assert len(CHART) == sum(s['bars'] for s in TL['sections']), 'chord chart does not match the timeline'

STR = {'Dm': ('D2 D3', 'A3 D4 F4', 'A4'), 'Bb': ('Bb1 Bb2', 'Bb3 D4 F4', 'Bb4'),     # low, mid, top line
       'F': ('F2 F3', 'A3 C4 F4', 'A4'), 'C': ('C2 C3', 'G3 C4 E4', 'G4'),
       'Asus': ('A1 A2', 'A3 D4 E4', 'D5'), 'A': ('A1 A2', 'A3 C#4 E4', 'C#5')}
OSTINATO = {'Dm': 'D4 A4 F4 A4', 'Bb': 'D4 Bb4 F4 Bb4', 'F': 'C4 A4 F4 A4', 'C': 'C4 G4 E4 G4',
            'Asus': 'D4 A4 E4 A4', 'A': 'C#4 A4 E4 A4'}
PAD = {'Bb': 'Bb1 F3 Bb3 D4', 'F': 'F2 F3 A3 C4', 'C': 'C2 E3 G3 C4', 'Dm': 'D2 F3 A3 D4',
       'D': 'D2 F#3 A3 D4', 'Gm/D': 'D2 G3 Bb3 D4'}
LEFT_HAND = {'Bb': 'Bb2 F3 Bb3 F3', 'F': 'F2 C3 F3 C3', 'C': 'C3 G3 C4 G3', 'Dm': 'D3 A3 D4 A3',
             'D': 'D3 A3 D4 A3'}
ROOT = {'Dm': 'D2', 'Bb': 'Bb1', 'F': 'F2', 'C': 'C2', 'Asus': 'A1', 'A': 'A1'}


def chord_events(b0, b1, merge=True):
    """(start s, length s, chord) for bars b0..b1-1; 'X|Y' splits a bar at beat 3; repeats merge."""
    ev = []
    for b in range(b0, b1):
        parts = CHART[b].split('|')
        for k, ch in enumerate(parts):
            t0, d = T(b, 4 * k / len(parts)), BAR / len(parts)
            if merge and ev and ev[-1][2] == ch:
                ev[-1] = (ev[-1][0], ev[-1][1] + d, ch)
            else:
                ev.append((t0, d, ch))
    return ev


# ------------------------------------------------------------------------------ dsp helpers
def fade(n):
    """Raised cosine 0 -> 1 over n samples."""
    return 0.5 - 0.5 * np.cos(np.pi * (np.arange(n) + 0.5) / max(n, 1))


def rise(t, t0, t1):
    """Raised cosine 0 -> 1 as t goes from t0 to t1 (seconds, array)."""
    return 0.5 - 0.5 * np.cos(np.pi * np.clip((np.asarray(t) - t0) / (t1 - t0), 0, 1))


def asr(n, attack, release):
    """Raised-cosine attack, flat sustain, raised-cosine release over the last `release` s."""
    e = np.ones(n)
    a = min(n, ns(attack))
    e[:a] = fade(a)
    r = min(n - a, ns(release))
    if r > 0:
        e[n - r:] *= fade(r)[::-1]
    return e


def perc(n, tau, attack=0.001):
    """Short raised-cosine attack, exponential decay, 4 ms fade to true zero."""
    return np.exp(-np.arange(n) / (tau * SR)) * asr(n, attack, 0.004)


def pan_st(x, pan=0.0):
    """Mono -> stereo, constant-power pan law normalised to unity at centre."""
    th = (np.clip(pan, -1, 1) + 1) * np.pi / 4
    return np.stack([x * np.cos(th), x * np.sin(th)], 1) * np.sqrt(2)


def _sos(kind, f, order=2):
    return butter(order, f, kind, fs=SR, output='sos')


def lowpass(x, f, order=2):
    return sosfilt(_sos('low', f, order), x, axis=0)


def highpass(x, f, order=2):
    return sosfilt(_sos('high', f, order), x, axis=0)


def bandpass(x, lo, hi, order=2):
    return sosfilt(_sos('band', [lo, hi], order), x, axis=0)


def peaking(f0, gain_db, q):
    """RBJ peaking-EQ biquad as one sos row."""
    a_ = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / SR
    al = np.sin(w) / (2 * q)
    b = np.array([1 + al * a_, -2 * np.cos(w), 1 - al * a_])
    a = np.array([1 + al / a_, -2 * np.cos(w), 1 - al / a_])
    return np.concatenate([b / a[0], a / a[0]])[None, :]


def sweep_lowpass(x, fc, top=16000.0, order=2):
    """Time-varying low-pass (fc: Hz per sample). Crossfades a half-octave bank of zero-phase
    Butterworth low-passes: zero phase lets neighbouring outputs blend without comb filtering, and
    fc >= top passes the signal untouched, so a filtered stretch splices back seamlessly."""
    fc = np.minimum(np.broadcast_to(np.asarray(fc, float), (len(x),)), top)
    nb = int(np.ceil(2 * np.log2(top / max(float(fc.min()), 20.0)))) + 1
    pos = np.clip(nb - 1 + 2 * np.log2(fc / top), 0, nb - 1)
    out = np.zeros(x.shape)
    pad = ns(0.05)
    for i in range(nb):
        w = np.clip(1 - np.abs(pos - i), 0, 1)
        on = np.flatnonzero(w)
        if not on.size:
            continue
        a, b = max(0, on[0] - pad), min(len(x), on[-1] + 1 + pad)
        seg = x[a:b] if i == nb - 1 else sosfiltfilt(_sos('low', top * 2 ** (-(nb - 1 - i) / 2), order),
                                                      x[a:b], axis=0)
        out[a:b] += (w[a:b, None] if x.ndim == 2 else w[a:b]) * seg
    return out


_TAB, TAB_LEN = {}, 8192


def wavetable(shape, kmax):
    """One cycle of a band-limited waveform with harmonics 1..kmax (built by inverse FFT)."""
    key = (shape, kmax)
    if key not in _TAB:
        k = np.arange(1, kmax + 1)
        amp = {'saw': 1.0 / k,
               'soft': 1.0 / k ** 1.7,
               'fifths': np.where(np.isin(k, [1, 2, 3, 4, 6, 8, 12, 16, 24, 32]), 1.0 / k, 0.0),
               'tri': np.where(k % 2 == 1, (-1.0) ** ((k - 1) // 2) / k ** 2, 0.0)}[shape]
        spec = np.zeros(TAB_LEN // 2 + 1, complex)
        spec[1:kmax + 1] = -0.5j * TAB_LEN * amp
        tab = irfft(spec, TAB_LEN)
        _TAB[key] = np.append(tab, tab[0]) / np.abs(tab).max()
    return _TAB[key]


def osc(shape, f, n=None, phase=0.0):
    """Wavetable oscillator, harmonics kept under ~17 kHz for the highest frequency played (no
    aliasing); f in Hz, scalar or per-sample array; phase in cycles."""
    f = np.full(n, float(f)) if np.isscalar(f) else np.asarray(f, float)
    tab = wavetable(shape, int(np.clip(17000.0 / f.max(), 1, TAB_LEN // 2 - 1)))
    ph = np.cumsum(f / SR) + phase
    x = (ph - np.floor(ph)) * TAB_LEN
    i = x.astype(np.int64)
    return tab[i] + (x - i) * (tab[i + 1] - tab[i])


def shaped_noise(n, shape, seed, nfft=2048):
    """Stereo noise whose spectrum follows shape(freqs[F], times[T]) -> magnitude[F, T]: random-phase
    frames, Hann-windowed 4x overlap-add, normalised to unit RMS."""
    hop = nfft // 4
    nfr = n // hop + 6
    mag = shape(rfftfreq(nfft, 1 / SR), (np.arange(nfr) - 2) * hop / SR)
    win = np.hanning(nfft + 1)[:-1]
    rng = np.random.default_rng(seed)
    out = np.zeros((n, 2))
    for c in range(2):
        fr = irfft(mag * np.exp(2j * np.pi * rng.random(mag.shape)), nfft, axis=0) * win[:, None]
        y = np.zeros((nfr + 3) * hop)
        for k in range(4):
            y[k * hop:(k + nfr) * hop] += fr[k * hop:(k + 1) * hop].T.ravel()
        out[:, c] = y[4 * hop:4 * hop + n]
    return out / np.sqrt(np.mean(out ** 2))


def accel_times(t0, t1, r0, r1):
    """Event times in [t0, t1) whose rate rises exponentially from r0 to r1 per second."""
    k = np.log(r1 / r0) / (t1 - t0)
    count = r0 * np.expm1(k * (t1 - t0)) / k
    return t0 + np.log1p(np.arange(int(count)) * k / r0) / k


def make_ir(rt60, seconds, predelay, seed):
    """Stereo reverb impulse response: decorrelated noise in four bands, each decaying at its own
    rate (highs die faster), a soft diffuse onset and a pre-delay; unit energy per channel."""
    n = ns(seconds)
    t = np.arange(n) / SR
    nz = np.random.default_rng(seed).standard_normal((n, 2))
    ir = np.zeros((n, 2))
    for lo, hi, k in ((80, 500, 1.1), (500, 2000, 1.0), (2000, 6000, 0.7), (6000, 15000, 0.45)):
        ir += bandpass(nz, lo, hi) * np.exp(-6.908 * t / (rt60 * k))[:, None]
    ir *= ((1 - np.exp(-t / 0.012)) * asr(n, 0.0, 0.08))[:, None]
    ir = np.vstack([np.zeros((ns(predelay), 2)), ir])
    return (ir / np.sqrt((ir ** 2).sum(0))).astype(np.float32)


IRS = {}


def build_irs():
    IRS['room'] = make_ir(0.7, 0.9, 0.004, 31)
    IRS['hall'] = make_ir(3.0, 3.6, 0.022, 32)
    IRS['long'] = make_ir(6.5, 7.6, 0.035, 33)


def reverb(send, ir):
    """Convolve a send bus with an IR over its active span; the return is high-passed at 150 Hz so
    the low end stays dry, tight and mono."""
    act = np.flatnonzero(np.abs(send).max(1) > 1e-9)
    out = np.zeros(send.shape, np.float32)
    if act.size:
        a, b = act[0], act[-1] + 1
        wet = fftconvolve(send[a:b], ir, axes=0)[:len(send) - a]
        out[a:a + len(wet)] = highpass(wet, 150)
    return out


# ------------------------------------------------------------------------------ instruments
def drone(length):
    """Sub drone: a D1 sine plus a D2 wave built from octaves and fifths only (so it sits under minor
    and major chords alike), three voices a few cents apart, through a slowly breathing low-pass."""
    n = ns(length)
    t = np.arange(n) / SR
    body = np.zeros((n, 2))
    for k, (cents, pan) in enumerate(((-3, -0.4), (0, 0.0), (3, 0.4))):
        body += pan_st(osc('fifths', hz(38) * 2 ** (cents / 1200), n, phase=k / 3), pan)
    fc = 240 * 2 ** (0.85 * np.sin(2 * np.pi * t / 9.6) + 0.3 * np.sin(2 * np.pi * t / 25.7 + 1.3))
    body = sweep_lowpass(body, fc, top=4000)
    x = 0.6 * body / np.abs(body).max() + 0.22 * pan_st(np.sin(2 * np.pi * hz(26) * t))
    return x * (1 + 0.1 * np.sin(2 * np.pi * t / 6.86 + 0.5))[:, None]


def clock(kind, seed, pitch=1.0):
    """Escapement click: damped metal modes plus a tiny noise burst; 'tick' is bright, 'tock' is
    lower and duller. pitch scales the modes (the riser's ticks climb)."""
    rng = np.random.default_rng(seed)
    n = ns(0.12)
    t = np.arange(n) / SR
    modes = {'tick': ((3150, .011, 1.0), (4720, .007, .55), (6940, .0045, .3), (2240, .017, .2)),
             'tock': ((1790, .015, 1.0), (2680, .010, .5), (4010, .006, .2), (940, .026, .32))}[kind]
    x = np.zeros(n)
    for f, tau, a in modes:
        f = min(f * pitch * (1 + 0.01 * rng.standard_normal()), 15000)
        x += a * np.exp(-t / tau) * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
    burst = highpass(rng.standard_normal(n), 1500) * np.exp(-t / 0.0012)
    if kind == 'tock':
        burst = lowpass(burst, 3500)
    x = (x + 0.7 * burst / np.abs(burst).max()) * asr(n, 0.0003, 0.004)
    return x / np.abs(x).max()


def heartbeat(seed):
    """'Lub-dub': two low thumps 0.18 s apart with a falling pitch, the second softer and shorter,
    with a touch of 2nd/3rd harmonic so small speakers can hear it."""
    n = ns(0.6)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for t0, f_hi, f_lo, tau, amp in ((0.0, 75, 45, 0.07, 1.0), (0.18, 88, 54, 0.05, 0.7)):
        tt = np.clip(t - t0, 0, None)
        ph = 2 * np.pi * np.cumsum(f_lo + (f_hi - f_lo) * np.exp(-tt / 0.03)) / SR
        on = (t >= t0) * np.exp(-tt / tau) * np.minimum(1, tt / 0.005)
        x += amp * on * (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph))
    thud = lowpass(np.random.default_rng(seed).standard_normal(n), 120)
    x += 0.25 * thud / np.abs(thud).max() * np.exp(-t / 0.05)
    x *= asr(n, 0.001, 0.02)
    return x / np.abs(x).max()


_PIANO = {}


def piano(m, dur=5.0, vel=0.45):
    """Soft 'felt' piano: two strings a cent apart, each a stiff-string series of inharmonic partials
    with a hammer-position comb and a two-stage decay (prompt sound + aftersound); felt thump on the
    attack, damper after `dur`."""
    key = (m, round(dur, 2), round(vel, 2))
    if key in _PIANO:
        return _PIANO[key]
    rng = np.random.default_rng(m * 7 + int(vel * 100))
    f0 = hz(m)
    inharm = 2.5e-4 * 2 ** ((m - 60) / 24)
    tau1 = 2.6 * 2 ** (-(m - 60) / 20)
    n = ns(dur + 1.2)
    t = np.arange(n) / SR
    damper = np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.22))
    x = np.zeros((n, 2))
    for k in range(1, 25):
        fk = k * f0 * np.sqrt(1 + inharm * k * k)
        if fk > 9000:
            break
        ak = np.exp(-(k - 1) / (2.5 + 7 * vel)) / k ** 0.9 * abs(np.sin(np.pi * k / 8.3))
        if ak < 2e-3:
            continue
        tk = tau1 / (1 + 0.45 * (k - 1))
        ln = min(n, ns(tk * 9) + 1)
        tt = t[:ln]
        env = ak * (0.68 * np.exp(-tt / (0.16 * tk)) + 0.32 * np.exp(-tt / tk)) * damper[:ln]
        s1 = np.sin(2 * np.pi * fk * 2 ** (-0.6 / 1200) * tt + rng.uniform(0, 2 * np.pi))
        s2 = np.sin(2 * np.pi * fk * 2 ** (0.7 / 1200) * tt + rng.uniform(0, 2 * np.pi))
        x[:ln, 0] += env * (0.62 * s1 + 0.38 * s2)
        x[:ln, 1] += env * (0.38 * s1 + 0.62 * s2)
    th = ns(0.05)
    thump = lowpass(rng.standard_normal(th), 500 + 2500 * vel) * np.exp(-t[:th] / 0.006)
    x[:th] += 0.25 * (thump / np.abs(thump).max())[:, None] * np.abs(x).max()
    x *= asr(n, 0.0025 - 0.0015 * vel, 0.01)[:, None]
    _PIANO[key] = x / np.abs(x).max() * vel
    return _PIANO[key]


def ensemble(m, length, voices=4, detune=8.0, vib=6.0, shape='saw', width=0.6, seed=0):
    """A section note: detuned band-limited oscillators, each with its own delayed vibrato and slow
    pitch drift, spread across the stereo field (raw, no envelope)."""
    rng = np.random.default_rng(seed)
    n = ns(length)
    ctl = np.arange(0, n + 64, 32)
    tc = ctl / SR
    knots = np.arange(0, tc[-1] + 0.5, 0.5)
    out = np.zeros((n, 2))
    for v in range(voices):
        sp = 2 * v / (voices - 1) - 1 if voices > 1 else 0.0
        vib_c = (vib * rng.uniform(0.7, 1.2) * np.clip(tc / 1.2, 0, 1)
                 * np.sin(2 * np.pi * rng.uniform(4.7, 5.9) * tc + rng.uniform(0, 2 * np.pi)))
        drift = np.interp(tc, knots, rng.normal(0, 1.5, len(knots)))
        cents = detune * sp + rng.normal(0, 0.15 * detune) + vib_c + drift
        f = hz(m) * 2 ** (np.interp(np.arange(n), ctl, cents) / 1200)
        out += pan_st(osc(shape, f, phase=rng.random()), width * sp)
    return out / np.sqrt(voices)


LAYER = {'low': dict(voices=3, detune=6.0, vib=4.0, width=0.35),     # celli / basses
         'mid': dict(voices=4, detune=8.0, vib=6.0, width=0.6),      # violas / 2nd violins
         'top': dict(voices=5, detune=9.0, vib=7.0, width=0.8),      # 1st violins
         'high': dict(voices=5, detune=10.0, vib=8.0, width=0.9)}    # violins an octave up


def pad_voice(m, length, seed):
    """Warm pad voice: soft-saw and triangle ensembles, barely any vibrato."""
    return (0.75 * ensemble(m, length, voices=3, detune=7, vib=1.5, shape='soft', width=0.8, seed=seed)
            + 0.5 * ensemble(m, length, voices=2, detune=4, vib=1.0, shape='tri', width=0.5, seed=seed + 1))


def glass_note(m, length, seed):
    """Glass harmonica: near-pure sine partials 1-3, two layers 3 cents apart (slow shimmer), a light
    rubbing tremolo and a soft attack."""
    rng = np.random.default_rng(seed)
    n = ns(length + 1.4)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for cents in (-1.5, 1.5):
        f = hz(m) * 2 ** (cents / 1200)
        for k, a in ((1, 1.0), (2, 0.16), (3, 0.05)):
            x += a * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
    x *= 1 + 0.05 * np.sin(2 * np.pi * rng.uniform(4.5, 6.0) * t)
    return x * asr(n, 0.35, 1.4) / 2.4


def water(length, seed):
    """Water rising in a glass box: noise band-limited around a slowly wandering centre (LFOs), a
    bubbling level, getting brighter and louder over the section."""
    def shape(f, t):
        p = np.clip(t / length, 0, 1)
        lfo = 0.65 * np.sin(2 * np.pi * t / 7.3) + 0.25 * np.sin(2 * np.pi * t / 2.9 + 1)
        fc = (330 + 420 * p) * 2 ** lfo
        f = np.maximum(f, 1.0)[:, None]
        return (np.exp(-0.5 * (np.log2(f / fc[None, :]) / 0.7) ** 2)
                + 0.2 * np.exp(-0.5 * (np.log2(f / 110) / 0.9) ** 2))
    n = ns(length)
    x = shaped_noise(n, shape, seed)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed + 1)
    knots = np.arange(0, length + 0.3, 0.1)
    gurgle = lowpass(np.interp(t, knots, rng.standard_normal(len(knots))), 5.0)
    swell = 0.8 + 0.2 * np.sin(2 * np.pi * 0.14 * t)
    am = swell * np.clip(1 + 0.35 * gurgle / gurgle.std(), 0.3, 1.8)
    return x * (am * (0.45 + 0.55 * t / length))[:, None]


def bubble(f0, d):
    """One bubble: a sine chirping upward with a fast decay."""
    n = ns(4 * d)
    t = np.arange(n) / SR
    chirp = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.8 * t / d)) / SR)
    return chirp * np.exp(-t / d) * asr(n, 0.001, 0.004)


def reverse_swell(ms, length, seed):
    """Reverse-reverb swell: a soft chord burst drenched in the long hall, reversed so that it rushes
    into the next downbeat and stops right on it."""
    rng = np.random.default_rng(seed)
    n = ns(0.5)
    t = np.arange(n) / SR
    burst = sum(np.sin(2 * np.pi * hz(m) * t + rng.uniform(0, 2 * np.pi)) for m in ms) * np.exp(-t / 0.12)
    burst = burst + 0.3 * bandpass(rng.standard_normal(n), 300, 6000) * np.exp(-t / 0.05)
    pd = ns(0.035)                                    # skip the IR pre-delay so the swell ends on the beat
    wet = fftconvolve(pan_st(burst * asr(n, 0.002, 0.01)), IRS['long'], axes=0)[pd:pd + ns(length)]
    x = wet[::-1] * asr(len(wet), 0.3, 0.006)[:, None]
    return x / np.abs(x).max()


_PLUCK = {}


def pluck(m, vel=1.0):
    """Spiccato-like pluck for the 16th ostinato: slightly stretched harmonics with a bright attack
    (the higher ones die within a few tens of ms) and a short pick/bow transient."""
    key = (m, round(vel, 2))
    if key not in _PLUCK:
        rng = np.random.default_rng(m)
        n = ns(0.6)
        t = np.arange(n) / SR
        x = np.zeros(n)
        for k in range(1, 30):
            fk = k * hz(m) * np.sqrt(1 + 3e-4 * k * k)
            if fk > 11000:
                break
            x += (np.exp(-(k - 1) / (6 + 6 * vel)) / k ** 0.8 * np.exp(-t * (1 + 0.6 * (k - 1)) / 0.15)
                  * np.sin(2 * np.pi * fk * t + rng.uniform(0, 2 * np.pi)))
        pick = bandpass(rng.standard_normal(n), 2000, 8000) * np.exp(-t / 0.004)
        x = (x + 0.3 * vel * pick / np.abs(pick).max()) * asr(n, 0.0008, 0.004)
        _PLUCK[key] = x / np.abs(x).max() * vel
    return _PLUCK[key]


def pulse_note(m, cutoff, length):
    """One road-pulse note: saw + sine sub on the chord root, short decay, low-passed."""
    n = ns(length + 0.06)
    x = 0.55 * osc('saw', hz(m), n) + 0.8 * np.sin(2 * np.pi * hz(m) * np.arange(n) / SR)
    return lowpass(x, cutoff) * perc(n, 0.13, attack=0.003)


def taiko(size, hard, seed):
    """Taiko-like drum: pitch-dropping membrane modes, stick slap and skin noise, lightly saturated.
    size 'big' (odaiko), 'mid' or 'small' (shime); hard selects the louder velocity layer."""
    f_hi, f_lo, tau, length = {'big': (120, 58, 0.42, 2.0), 'mid': (235, 150, 0.2, 1.0),
                               'small': (500, 380, 0.07, 0.4)}[size]
    rng = np.random.default_rng(seed)
    f_hi *= 1 + 0.02 * rng.standard_normal()
    f_lo *= 1 + 0.02 * rng.standard_normal()
    n = ns(length)
    t = np.arange(n) / SR
    glide = np.cumsum(f_lo + (f_hi - f_lo) * np.exp(-t / 0.045)) / SR
    x = np.zeros(n)
    for ratio, a, tr in ((1.0, 1.0, 1.0), (1.59, 0.35, 0.45), (2.14, 0.18, 0.3), (2.65, 0.1, 0.2)):
        x += a * np.sin(2 * np.pi * ratio * glide) * np.exp(-t / (tau * tr))
    stick = bandpass(rng.standard_normal(n), 600, 5000) * np.exp(-t / 0.007)
    skin = lowpass(rng.standard_normal(n), 1100) * np.exp(-t / 0.035)
    x += (0.55 if hard else 0.25) * stick / np.abs(stick).max() + 0.35 * skin / np.abs(skin).max()
    x = np.tanh((3.0 if hard else 1.3) * x / np.abs(x).max()) * asr(n, 0.0005, 0.01)
    return x / np.abs(x).max()


def snare(seed):
    """Snare stroke for the roll: bright wire noise plus a short drum body."""
    rng = np.random.default_rng(seed)
    n = ns(0.3)
    t = np.arange(n) / SR
    wires = bandpass(rng.standard_normal(n), 1800, 9500)
    body = (np.sin(2 * np.pi * 188 * t) + 0.5 * np.sin(2 * np.pi * 332 * t)) * np.exp(-t / 0.03)
    x = (0.8 * wires / np.abs(wires).max() * np.exp(-t / 0.06) + 0.45 * body) * asr(n, 0.0004, 0.01)
    return x / np.abs(x).max()


def riser_noise(length, seed):
    """Noise whose band sweeps from ~250 Hz to ~11 kHz while its level climbs ~30 dB."""
    def shape(f, t):
        p = np.clip(t / length, 0, 1)[None, :]
        fc = 250 * (11000 / 250) ** (p ** 1.4)
        return np.exp(-0.5 * (np.log2(np.maximum(f, 1.0)[:, None] / fc) / (1.3 - 0.4 * p)) ** 2)
    x = shaped_noise(ns(length), shape, seed)
    p = np.arange(len(x)) / len(x)
    return x * db(-30 * (1 - p) ** 1.6)[:, None]


def riser_tone(length):
    """Tone gliding three octaves (D2 -> D5) with a vibrato that widens and speeds up, plus an
    octave-up layer fading in; band-limited additive synthesis."""
    n = ns(length)
    t = np.arange(n) / SR
    p = t / length
    semis = 36 * p ** 1.3 + (0.15 + 0.5 * p) * np.sin(2 * np.pi * (5 + 3 * p) * t)
    ph = 2 * np.pi * np.cumsum(hz(38) * 2 ** (semis / 12)) / SR
    x = sum(np.sin(k * ph) / k ** 1.2 for k in range(1, 9))
    x += 0.5 * p * sum(np.sin(2 * k * ph) / k ** 1.2 for k in range(1, 5))
    return pan_st(x / np.abs(x).max() * db(-24 * (1 - p) ** 1.5) * asr(n, 0.3, 0.02))


def braam(root, length=3.8, seed=0):
    """Trailer 'braam': seven detuned saws on each of root, +12 and +19 (D1/D2/A2 for D), sagging
    ~40 cents, soft-saturated, through a low-pass closing from ~3.5 kHz to ~170 Hz."""
    rng = np.random.default_rng(seed)
    n = ns(length)
    t = np.arange(n) / SR
    sag = -40 * (1 - np.exp(-t / 1.1))
    x = np.zeros((n, 2))
    for m, lvl in ((root, 0.7), (root + 12, 1.0), (root + 19, 0.55)):
        for v in range(7):
            sp = v / 3 - 1
            f = hz(m) * 2 ** ((16 * sp + rng.normal(0, 2) + sag) / 1200)
            x += lvl * pan_st(osc('saw', f, phase=rng.random()), 0.6 * sp)
    x = np.tanh(2.5 * x / (3 * np.sqrt(np.mean(x ** 2))))
    x = sweep_lowpass(x, 170 * (3500 / 170) ** np.exp(-t / 0.9))
    x *= (asr(n, 0.03, 0.9) * (0.45 + 0.55 * np.exp(-t / 1.3)))[:, None]
    return x / np.abs(x).max()


def impact(seed=1):
    """Drop impact: a sub boom falling to D1, a body thud, a bright noise crash, a metallic 'chain'
    clang (inharmonic free-bar partials on D3) and a transient click."""
    rng = np.random.default_rng(seed)
    n = ns(5.5)
    t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(hz(26) + (105 - hz(26)) * np.exp(-t / 0.09)) / SR
    boom_ = (np.sin(ph) + 0.3 * np.sin(2 * ph) * np.exp(-t / 0.4)) * np.exp(-t / 1.3)
    thud = np.sin(2 * np.pi * np.cumsum(55 + 70 * np.exp(-t / 0.03)) / SR) * np.exp(-t / 0.14)
    bar_modes = ((1, 1, 1.4), (2.76, .6, 1.0), (5.40, .45, .7), (8.93, .3, .5), (13.34, .2, .35))
    clang = sum(a * np.sin(2 * np.pi * hz(50) * r * t + rng.uniform(0, 6.3)) * np.exp(-t / tau)
                for r, a, tau in bar_modes)
    click = highpass(rng.standard_normal(n), 1500) * np.exp(-t / 0.0025)
    crash_ = highpass(rng.standard_normal((n, 2)), 380)
    crash_ *= (0.75 * np.exp(-t / 0.28) + 0.25 * np.exp(-t / 1.7))[:, None]
    sheen = bandpass(rng.standard_normal((n, 2)), 5000, 13000) * np.exp(-t / 1.2)[:, None]
    x = (pan_st(boom_ + 0.7 * thud + 0.08 * clang + 0.3 * click / np.abs(click).max())
         + 0.35 * crash_ / np.abs(crash_).max() + 0.12 * sheen / np.abs(sheen).max())
    x *= asr(n, 0.0008, 0.3)[:, None]
    return x / np.abs(x).max()


def crash(seed, length=4.0):
    """Cymbal-like noise crash: bright stereo noise, fast body decay and a long shimmering tail."""
    rng = np.random.default_rng(seed)
    n = ns(length)
    t = np.arange(n) / SR
    body = highpass(rng.standard_normal((n, 2)), 400)
    body *= (0.7 * np.exp(-t / 0.35) + 0.3 * np.exp(-t / 1.6))[:, None]
    sheen = bandpass(rng.standard_normal((n, 2)), 5000, 14000) * np.exp(-t / 1.3)[:, None]
    x = (body + 0.5 * sheen) * asr(n, 0.001, 0.3)[:, None]
    return x / np.abs(x).max()


def boom(length=6.5, seed=4):
    """Low boom tuned to D1: a sine falling from ~75 Hz with a slow decay over a dark rumble."""
    n = ns(length)
    t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(hz(26) + (75 - hz(26)) * np.exp(-t / 0.15)) / SR
    x = np.sin(ph) * np.exp(-t / 2.0) + 0.3 * np.sin(2 * ph) * np.exp(-t / 0.7)
    rumble = lowpass(np.random.default_rng(seed).standard_normal(n), 140)
    x += 0.3 * rumble / np.abs(rumble).max() * np.exp(-t / 0.9)
    x *= asr(n, 0.004, 1.0)
    return x / np.abs(x).max()


# ------------------------------------------------------------------------------ mixer
class Mix:
    """Two render parts: 'A' (everything before the drop, cut together with its reverb tails for the
    suck-back silence) and 'B' (from the drop on). Each part has groups ('music'; 'glass' sits outside
    the glass-box low-pass) with a dry bus and room/hall/long reverb sends."""

    def __init__(self, split_s):
        self.split = ns(split_s)
        self.span = {'A': (0, self.split), 'B': (self.split, N)}
        self.bus, self.meter = {}, {}

    def _buf(self, key):
        if key not in self.bus:
            a, b = self.span[key[0]]
            self.bus[key] = np.zeros((b - a, 2), np.float32)
        return self.bus[key]

    def add(self, group, t, sig, gain_db=0.0, pan=0.0, track='?', **sends):
        sig = np.asarray(sig, float)
        sig = pan_st(sig, pan) if sig.ndim == 1 else sig * [min(1.0, 1 - pan), min(1.0, 1 + pan)]
        sig = sig * db(gain_db)
        i = ns(t)
        part = 'A' if i < self.split else 'B'
        a, b = self.span[part]
        j0, j1 = i - a, i - a + len(sig)
        s0 = max(0, -j0)
        j0, j1 = max(j0, 0), min(j1, b - a)
        if j1 <= j0:
            return
        seg = sig[s0:s0 + j1 - j0]
        self._buf((part, group, 'dry'))[j0:j1] += seg
        for name, amt in sends.items():
            if amt:
                self._buf((part, group, name))[j0:j1] += amt * seg
        for s in TL['sections']:                         # per-track level meter (dry)
            lo, hi = max(ns(s['start']) - a, j0), min(ns(s['end']) - a, j1)
            if hi > lo:
                e = float(np.square(seg[lo - j0:hi - j0]).sum())
                self.meter[(track, s['name'])] = self.meter.get((track, s['name']), 0.0) + e

    def render(self, part, group):
        a, b = self.span[part]
        out = self.bus.pop((part, group, 'dry'), np.zeros((b - a, 2), np.float32))
        for name in ('room', 'hall', 'long'):
            send = self.bus.pop((part, group, name), None)
            if send is not None:
                out += reverb(send, IRS[name])
        return out


# ------------------------------------------------------------------------------ tracks
def track_drone(mix):
    """Sub drone from silence (11 s fade-in) through the glass box; fades as the road pulse takes over."""
    end = T(BAR0['road'] + 2.5)
    x = drone(end)
    t = np.arange(len(x)) / SR
    g = rise(t, 0, 11.0) * (1 - rise(t, T(BAR0['road']), end))       # in from silence, out under the road
    g *= db(-3 * rise(t, T(BAR0['hole']), T(BAR0['hole'] + 2)))       # steps back once the hole strings enter
    mix.add('music', 0.0, x * g[:, None], gain_db=-17.5, track='drone')


def track_clock(mix):
    """Tick on beats 1/3, tock on 2/4: present in the intro, quieter under the heartbeat, muffled in
    the glass box; back softly in the outro, where it stops two bars before the end."""
    snd = {k: [clock(k, 11 * i + (0 if k == 'tick' else 5)) for i in range(4)] for k in ('tick', 'tock')}
    for name, lvl in (('intro', -19), ('time', -20), ('hole', -26), ('glass', -26), ('road', -30), ('outro', -25)):
        b0, nbar = BAR0[name], SEC[name]['bars'] - (2 if name == 'outro' else 0)
        for i in range(nbar * 4):
            kind = 'tick' if i % 2 == 0 else 'tock'
            g = lvl - (2.5 if kind == 'tock' else 0.0)
            if name == 'intro':
                g -= 20 * (1 - min(1.0, i / 10))
            if name == 'outro':
                g -= 8 * (1 - min(1.0, i / 4))
            mix.add('music', T(b0, i), snd[kind][i % 4], gain_db=g, pan=0.2 if kind == 'tick' else -0.2,
                    track='clock', room=0.3, hall=0.08)


def track_piano(mix):
    """Felt piano: one note per bar in the intro and time, the string top line in the hole, the hope
    motif with a left-hand pulse in 'everything', a few sustained notes in the outro."""
    i, tm, h, e, o = (BAR0[k] for k in ('intro', 'time', 'hole', 'everything', 'outro'))
    ev = [(i + 1, 0, 'D4', .45, 5), (i + 2, 0, 'A4', .45, 5), (i + 3, 0, 'F4', .5, 5), (i + 4, 0, 'E4', .5, 3),
          (i + 4, 2, 'C#4', .45, 1.75)]                               # damped as it resolves to D4 on 'time'
    ev += [(tm + k, 0, n, .42, 5) for k, n in enumerate('D4 F4 E4 A3 Bb3 A3'.split())]
    ev += [(h + k, 0, n, .32, 4) for k, n in enumerate('A4 Bb4 A4 G4 A4 Bb4 A4 G4 A4 Bb4'.split())]
    melody = 'D5 C5 C5 A4 G4 E4 F4 A4 D5 F5 E5 C5 D5 E5'.split()
    ev += [(e + k // 2, 2 * (k % 2), n, .5, 2.4) for k, n in enumerate(melody)] + [(e + 7, 0, 'F#5', .55, 9)]
    for k, ch in enumerate(CHART[e:e + 8]):
        ev += [(e + k, beat, n, .28, 0.9 if beat == 3 else 1.3) for beat, n in enumerate(LEFT_HAND[ch].split())]
    ev += [(o, 0, 'D4 A4', .3, 6), (o + 1, 0, 'F#4', .28, 4), (o + 1, 2, 'A4', .26, 4), (o + 2, 0, 'Bb4', .3, 3.5),
           (o + 2, 2, 'A4', .26, 4), (o + 3, 0, 'D3 A3 F#4', .34, 8)]
    for bar, beat, names, vel, dur in ev:
        for m in mid(names):
            mix.add('music', T(bar, beat), piano(m, dur, vel), gain_db=-9, pan=(m - 62) / 40,
                    track='piano', hall=0.2, long=0.45)


def track_swells(mix):
    """Reverse swells into every bar line of 'time' (the last, bigger one lands on 'hole'), and a
    bright one into the D major 'light' near the end of 'everything'."""
    for b in range(BAR0['time'] + 1, BAR0['hole'] + 1):
        big = b == BAR0['hole']
        x = reverse_swell(mid('D2 A2 D3 A3 D4' if big else 'D3 A3 D4'), 2.4 if big else 1.6, seed=b)
        mix.add('music', T(b) - len(x) / SR, x, gain_db=-22 if big else -26, track='swell', hall=0.1)
    x = reverse_swell(mid('D5 F#5 A5'), 2.6, seed=99)
    mix.add('music', T(BAR0['everything'] + 7) - len(x) / SR, x, gain_db=-28, track='swell', hall=0.2)


def track_strings(mix):
    """String section: a dark Dm pad swelling through 'time'; one chord per bar from 'hole' (two bars
    per chord in 'glass'); opening up and growing through 'road'; tremolo in the riser; the full
    section with an octave-up line in 'chains'."""
    bufs = {p: np.zeros((b - a, 2), np.float32) for p, (a, b) in mix.span.items()}
    seeds = iter(range(1000, 10 ** 6))

    def note(t0, ms, length, layer, g, attack=0.4, release=0.9, env_fn=None):
        for m in ms:
            x = ensemble(m, length + release, seed=next(seeds), **LAYER[layer])
            e = asr(len(x), attack, release) * db(g)
            if env_fn is not None:
                e = e * env_fn(np.arange(len(x)) / SR)
            i = ns(t0)
            part = 'A' if i < mix.split else 'B'
            j = i - mix.span[part][0]
            k = min(len(x), len(bufs[part]) - j)
            bufs[part][j:j + k] += x[:k] * e[:k, None]

    t0, t1 = T(BAR0['time']), T(BAR0['hole'])                         # time: dark low pad on Dm
    swell = lambda t: (0.2 + 0.8 * rise(t, 0, t1 - t0)) * (1 + 0.12 * np.sin(2 * np.pi * t / BAR - np.pi / 2))
    note(t0, mid('D2 A2'), t1 - t0, 'low', -24, 3.0, 1.2, swell)
    note(t0, mid('D3 F3'), t1 - t0, 'mid', -28, 3.0, 1.2, swell)
    breathe = lambda t: 1 + 0.15 * np.sin(np.pi * np.clip(t / BAR, 0, 1))
    for t0, d, ch in chord_events(BAR0['hole'], BAR0['glass']):       # hole: one dark chord per bar
        low, mv, _ = STR[ch]
        note(t0, mid(low), d, 'low', -25, 0.35, 0.9, breathe)
        note(t0, mid(mv), d, 'mid', -29, 0.35, 0.9, breathe)
    for t0, d, ch in chord_events(BAR0['glass'], BAR0['road']):       # glass: two bars per chord
        low, mv, _ = STR[ch]
        note(t0, mid(low), d, 'low', -25, 0.8, 1.2)
        note(t0, mid(mv), d, 'mid', -28, 0.8, 1.2)
    r0, r1 = BAR0['road'], BAR0['riser']
    for t0, d, ch in chord_events(r0, r1, merge=False):               # road: crescendo, top line joins
        p = (t0 - T(r0)) / (T(r1) - T(r0))
        low, mv, top = STR[ch]
        note(t0, mid(low), d, 'low', -25 + 5 * p, 0.3, 0.8)
        note(t0, mid(mv), d, 'mid', -29 + 6 * p, 0.3, 0.8)
        if t0 >= T(r0 + 4) - 1e-6:
            note(t0, mid(top), d, 'top', -31 + 7 * p, 0.4, 0.8)
    t0, d = T(r1), T(DROP_BAR) - T(r1)                                # riser: C chord, 32nd tremolo
    trem = lambda t: (0.6 + 0.4 * rise(t, 0, d - 0.4)) * (0.7 + 0.3 * np.cos(2 * np.pi * 8 / BEAT * t))
    note(t0, mid('C2 C3'), d, 'low', -23, 0.3, 0.3, trem)
    note(t0, mid('G3 C4 E4'), d, 'mid', -26, 0.3, 0.3, trem)
    note(t0, mid('G4'), d, 'top', -27, 0.3, 0.3, trem)
    c0, c1 = BAR0['chains'], BAR0['everything']                       # chains: the full section
    for t0, d, ch in chord_events(c0, c1, merge=False):
        low, mv, _ = STR[ch]
        note(t0, mid(low), d, 'low', -20, 0.06, 0.6)                 # (the last four bars get louder by
        note(t0, mid(mv), d, 'mid', -25.5, 0.06, 0.6)                #  losing the duck, not by a fader)
    climax = dict(zip(range(c1 - 4, c1), ('A4 C5', 'G4 E4', 'F4 A4', 'D5 C#5')))
    for b in range(c0, c1):
        if b in climax:                                               # last four bars: the big line
            for k, m in enumerate(mid(climax[b])):
                note(T(b, 2 * k), [m], BAR / 2, 'top', -20.5, 0.08, 0.5)
                note(T(b, 2 * k), [m + 12], BAR / 2, 'high', -22.5, 0.1, 0.5)
        else:                                                         # under the voice: soft, octave up
            m = mid(STR[CHART[b]][2])[0]
            note(T(b), [m], BAR, 'top', -24.5, 0.1, 0.6)
            note(T(b), [m + 12], BAR, 'high', -31.5, 0.2, 0.6)
    tA = np.arange(len(bufs['A'])) / SR                                # dark -> opening through the road
    kn = [(0, 480), (T(BAR0['time']), 480), (T(BAR0['hole']), 650), (T(BAR0['glass']), 800), (T(r0), 850),
          (T(r1), 5000), (T(DROP_BAR), 9000)]
    fc = 2 ** np.interp(tA, [k[0] for k in kn], np.log2([k[1] for k in kn]))
    a0 = ns(T(BAR0['time']) - 0.1)
    bufs['A'][a0:] = sweep_lowpass(bufs['A'][a0:], fc[a0:])
    bufs['B'] = lowpass(bufs['B'], 7000, order=2)
    mix.add('music', 0.0, bufs['A'], track='strings', hall=0.3)
    mix.add('music', T(DROP_BAR), bufs['B'], track='strings', hall=0.28)


def track_heart(mix):
    """Heartbeat on every beat from 'hole' (fading in), softer in 'glass', dissolving into the road pulse."""
    hb = [heartbeat(s) for s in range(3)]
    h0, g0, r0 = BAR0['hole'], BAR0['glass'], BAR0['road']
    for i in range((r0 + 2 - h0) * 4):
        t = T(h0, i)
        if t < T(g0):
            g = -18 - 9 * max(0.0, 1 - i / 4)
        elif t < T(r0):
            g = -22
        else:
            g = -22 - 12 * (t - T(r0)) / (2 * BAR)
        mix.add('music', t, hb[i % 3], gain_db=g, track='heart', room=0.08)


GLASS_NOTES = [(0, 0, 'A5'), (0, 2, 'D5'), (1, 0, 'F5'), (1, 2, 'E5'), (2, 0, 'D5'), (2, 2, 'F5'),
               (3, 0, 'Bb5'), (3, 2, 'A5'), (4, 0, 'C6'), (4, 2, 'A5'), (5, 0, 'F5'), (5, 2, 'E5'),
               (6, 0, 'G5'), (6, 2, 'E5')]                            # (bar in 'glass', beat, note)


def track_glass(mix):
    """The glass box: rising water, sparse bubbles and a glass-harmonica line on chord tones (all of it
    in the 'glass' group, outside the box's low-pass)."""
    g0, g1 = T(BAR0['glass']), T(BAR0['road'])
    w = water(g1 - g0 + 1.5, seed=21)
    tt = np.arange(len(w)) / SR
    w *= (rise(tt, 0, 2.5) * (1 - rise(tt, g1 - g0 - 0.2, g1 - g0 + 1.2)))[:, None]
    mix.add('glass', g0 - 0.3, w, gain_db=-31, track='water', room=0.2, hall=0.1)
    rng = np.random.default_rng(22)
    t = g0 + 0.5
    while t < g1 - 0.5:
        p = (t - g0) / (g1 - g0)
        f0 = np.exp(rng.uniform(np.log(450), np.log(1500)))
        mix.add('glass', t, bubble(f0, rng.uniform(0.02, 0.05)), gain_db=-40 + rng.normal(0, 3),
                pan=rng.uniform(-0.7, 0.7), track='water', hall=0.15)
        t += rng.exponential(1 / (1.2 + 2.8 * p))
    for k, (bar, beat, name) in enumerate(GLASS_NOTES):
        length = (4 if k == len(GLASS_NOTES) - 1 else 3) * BEAT
        mix.add('glass', T(BAR0['glass'] + bar, beat), glass_note(mid(name)[0], length, seed=k),
                gain_db=-27, pan=0.3 if k % 2 else -0.3, track='glass', hall=0.35, long=0.35)


def track_pulse(mix):
    """Road: the heartbeat turns into an 8th-note pulse on the chord roots, opening and growing; 16ths
    in the last riser bar; nothing plays into the suck-back."""
    r0, r1 = BAR0['road'], BAR0['riser']
    cache = {}
    for t0, d, ch in chord_events(r0, r1 + 2, merge=False):
        root = mid(ROOT[ch])[0]
        step = 0.25 if t0 >= T(r1 + 1) - 1e-6 else 0.5
        for k in range(int(round(d / BEAT / step))):
            t = t0 + k * step * BEAT
            if t > T(DROP_BAR) - 0.45:
                break
            p = (t - T(r0)) / (T(DROP_BAR) - T(r0))
            key = (root, int(round(4 * np.log2(260 * (1400 / 260) ** p))), step)
            if key not in cache:
                cache[key] = pulse_note(root, 2 ** (key[1] / 4), step * BEAT)
            accent = 2.5 if abs(k * step - round(k * step)) < 1e-6 else 0.0
            mix.add('music', t, cache[key], gain_db=-25 + 6 * p + accent, track='pulse', room=0.1)


def track_taiko(mix):
    """Road: a low hit on each downbeat, growing, with pickups later on; riser: quarters, then 8ths and
    16ths; chains: hits on 1, 2&, 3, 4 with a 16th fill every 4th bar and a big fill into the breakdown."""
    rng = np.random.default_rng(5)
    kit = {(s, h): [taiko(s, h, seed=100 * i + 10 * h + j) for j in range(3)]
           for i, s in enumerate(('big', 'mid', 'small')) for h in (0, 1)}

    def hit(t, size, vel, g=0.0):
        pan = {'big': 0.0, 'mid': rng.choice([-0.3, 0.3]), 'small': rng.choice([-0.45, 0.45])}[size]
        mix.add('music', t + rng.normal(0, 0.003), kit[(size, int(vel > 0.7))][rng.integers(3)],
                gain_db=-15 + g + 20 * np.log10(vel) + rng.normal(0, 0.6), pan=pan, track='taiko',
                room=0.12, hall=0.3)

    r0, r1, c0, c1 = BAR0['road'], BAR0['riser'], BAR0['chains'], BAR0['everything']
    for b in range(r0, r1):
        p = (b - r0) / (r1 - r0 - 1)
        hit(T(b), 'big', 0.7 + 0.28 * p, -4)
        if b >= r0 + 4:
            hit(T(b, 2), 'big', 0.4 + 0.3 * p, -4)
        if b >= r1 - 2:
            hit(T(b, 3), 'mid', 0.5, -4)
            hit(T(b, 3.5), 'mid', 0.65, -4)
    for bt in np.arange(0, 8, 1.0):                                   # riser build
        steps = [0.0] if bt < 4 else ([0.0, 0.5] if bt < 6 else [0.0, 0.25, 0.5, 0.75])
        for s in steps:
            t = T(r1, bt + s)
            if t < T(DROP_BAR) - 0.45:
                hit(t, 'big' if s == 0 else 'mid', 0.5 + 0.45 * (bt + s) / 8, -6)
    for i, b in enumerate(range(c0, c1)):                             # chains
        full, last = b >= c1 - 4, b == c1 - 1
        g = -2.5 if full else -3.5
        hit(T(b), 'big', 1.0, g)
        if not full:
            hit(T(b), 'mid', 0.75, g - 3)
        if last:
            beats = np.arange(1.0, 4.0, 0.25)
        else:
            hit(T(b, 1.5), 'big', 0.72, g)
            beats = np.arange(2.0, 4.0, 0.25) if i % 4 == 3 else []
            if i % 4 != 3:
                hit(T(b, 2), 'big', 0.92, g)
                hit(T(b, 3), 'big', 0.8, g)
                if full:
                    hit(T(b, 3.5), 'mid', 0.65, g)
        for j, bt in enumerate(beats):                                # 16th fill, crescendo
            hit(T(b, bt), 'big' if bt % 1 == 0 else 'mid', 0.55 + 0.45 * j / len(beats), g)
        if full:
            for bt in np.arange(0, 4, 0.5):
                hit(T(b, bt), 'small', 0.45, g - 4)


def track_ostinato(mix):
    """16th-note pluck on chord tones: fades in through the road, drives the riser and all of
    'chains' (doubled an octave up in the last four bars); silent in the suck-back."""
    b0, r1, c1 = BAR0['road'] + 1, BAR0['riser'], BAR0['everything']
    rng = np.random.default_rng(8)
    for t0, d, ch in chord_events(b0, c1, merge=False):
        cell = mid(OSTINATO[ch])
        for k in range(int(round(d / BEAT * 4))):
            t = t0 + k * BEAT / 4
            if T(DROP_BAR) - 0.45 < t < T(DROP_BAR):
                continue
            vel = (1.0 if k % 4 == 0 else 0.8 if k % 2 == 0 else 0.7) * rng.uniform(0.93, 1.0)
            vel = round(vel, 2)
            full = t >= T(c1 - 4) - 1e-6
            if t < T(DROP_BAR):                                          # fade in through the road, grow in the riser
                p = min(1.0, (t - T(b0)) / (T(r1) - T(b0)))
                g = -18 - 24 * (1 - p) ** 1.8 + 2 * max(0.0, (t - T(r1)) / (2 * BAR))
            else:
                g = -16 if full else -16.5
            m, th = cell[k % 4], t + rng.normal(0, 0.002)              # a player, not a sequencer
            mix.add('music', th, pluck(m, vel), gain_db=g, pan=0.25 if k % 2 else -0.25, track='ostinato',
                    room=0.2, hall=0.15)
            if full:
                mix.add('music', th, pluck(m + 12, vel), gain_db=g - 4, pan=-0.35 if k % 2 else 0.35,
                        track='ostinato', room=0.2, hall=0.15)


def track_snare(mix):
    """Snare-like roll: builds over the last two road bars, accelerates through the riser, cut for the
    suck-back."""
    rng = np.random.default_rng(9)
    hits = [snare(s) for s in range(6)]
    t0, t1, t2 = T(BAR0['riser'] - 2), T(BAR0['riser']), T(DROP_BAR) - 0.42
    for t in np.concatenate([np.arange(t0, t1, 1 / 14), accel_times(t1, t2, 14, 34)]):
        p = (t - t0) / (t2 - t0)
        mix.add('music', t + rng.normal(0, 0.002), hits[rng.integers(6)],
                gain_db=-61 + 34 * p ** 0.8 + rng.normal(0, 1.2), pan=rng.uniform(-0.15, 0.15),
                track='snare', room=0.25, hall=0.2)


def track_riser(mix):
    """Two-bar riser: noise sweeping up, a tone gliding D2 -> D5, ticks accelerating into a buzz; all of
    it ends 0.37 s before the drop (the suck-back)."""
    t0, t1 = T(BAR0['riser']), T(DROP_BAR) - 0.37
    mix.add('music', t0, riser_noise(t1 - t0, 3), gain_db=-27, track='riser', hall=0.3)
    mix.add('music', t0, riser_tone(t1 - t0), gain_db=-30, track='riser', hall=0.25)
    for i, t in enumerate(accel_times(t0, t1 - 0.03, 2.33, 28)):
        p = (t - t0) / (t1 - t0)
        mix.add('music', t, clock('tick' if i % 2 == 0 else 'tock', 300 + i % 8, pitch=2 ** p),
                gain_db=-30 + 8 * p, pan=0.2 if i % 2 == 0 else -0.2, track='riser', room=0.3)


def track_hits(mix):
    """The drop impact, a braam every two bars of 'chains' (on the chord root), a reverse crash and
    crash into its final four bars, a soft boom into the breakdown, and the final boom when the clock
    has stopped."""
    c0, c1 = BAR0['chains'], BAR0['everything']
    mix.add('music', T(c0), impact(1), gain_db=-8, track='impact', hall=0.35, long=0.15)
    for b in range(c0, c1, 2):
        root = mid({'Dm': 'D1', 'F': 'F1'}[CHART[b]])[0]
        g = -13 if b == c0 else (-17 if b >= c1 - 4 else -15)
        # the brass speaks a hair (12 ms) after the drums, which also keeps the peaks from stacking
        mix.add('music', T(b) + 0.012, braam(root, seed=b), gain_db=g, track='braam', hall=0.25)
    x = crash(7)
    mix.add('music', T(c1 - 4) - 1.6, x[:ns(1.6)][::-1] * asr(ns(1.6), 1.0, 0.004)[:, None], gain_db=-26,
            track='crash', hall=0.2)
    mix.add('music', T(c1 - 4), x, gain_db=-24, track='crash', hall=0.3)
    mix.add('music', T(c1), boom(6.0, 5), gain_db=-26, track='boom', hall=0.3, long=0.3)
    mix.add('music', T(len(CHART) - 2), boom(6.8, 6), gain_db=-22, track='boom', hall=0.2, long=0.45)


def track_pad(mix):
    """Warm pad for the breakdown and the outro, brightening on the final D major 'light', then fading
    with the outro."""
    e0 = BAR0['everything']
    ts = T(e0)
    buf = np.zeros((N - ns(ts), 2))
    for k, (t0, d, ch) in enumerate(chord_events(e0, len(CHART))):
        for j, m in enumerate(mid(PAD[ch])):
            env = asr(ns(d + 2.5), 2.5 if k == 0 else 1.0, 2.5) * db(-6.0 if j == 0 else 0.0)  # light bass voice
            x = pad_voice(m, d + 2.5, seed=5000 + 10 * k + 2 * j) * env[:, None]
            a = ns(t0 - ts)
            b = min(len(buf), a + len(x))
            buf[a:b] += x[:b - a]
    t = np.arange(len(buf)) / SR + ts
    kn = [(ts, 1200), (T(e0 + 7) - 0.5, 1500), (T(e0 + 7) + 1.5, 2800), (T(len(CHART) - 2), 2400), (TOTAL, 1200)]
    buf = sweep_lowpass(buf, 2 ** np.interp(t, [k[0] for k in kn], np.log2([k[1] for k in kn])))
    g = db(-5 * rise(t, T(BAR0['outro']), T(BAR0['outro'] + 1)))       # a step back for the outro...
    g *= 1 - rise(t, T(len(CHART) - 2) + 1.0, TOTAL - 0.2)            # ...then gone by the last sample
    buf *= g[:, None]
    mix.add('music', ts, buf, gain_db=-31, track='pad', hall=0.35, long=0.25)


TRACKS = [track_drone, track_clock, track_piano, track_swells, track_strings, track_heart, track_glass,
          track_pulse, track_taiko, track_ostinato, track_snare, track_riser, track_hits, track_pad]


# ------------------------------------------------------------------------------ master
def glass_box(a):
    """Inside the glass box: the pre-drop music dives under a 600 Hz low-pass that rises to 2.5 kHz by
    the end of 'glass', then opens again for the road."""
    g0, g1 = T(BAR0['glass']), T(BAR0['road'])
    i0, i1 = ns(g0 - 1.0), ns(g1 + 1.0)
    t = np.arange(i0, i1) / SR
    fc = 2 ** np.interp(t, [t[0], g0 - 0.2, g0 + 0.3, g1, g1 + 0.6, t[-1]],
                        np.log2([16000, 16000, 600, 2500, 16000, 16000]))
    a[i0:i1] = sweep_lowpass(a[i0:i1], fc)
    return a


def voice_scoop(b):
    """'chains' while the voice speaks: a broad ~4 dB dip over 1-4 kHz (zero-phase, crossfaded)."""
    ls = [ln for ln in TL['lines'] if ln['section'] == 'chains']
    t = np.arange(len(b)) / SR + T(DROP_BAR)
    g = rise(t, ls[0]['start'] - 0.3, ls[0]['start']) * (1 - rise(t, ls[-1]['end'], ls[-1]['end'] + 0.4))
    on = np.flatnonzero(g)
    i0, i1 = on[0], on[-1] + 1
    seg = b[i0:i1]
    b[i0:i1] = seg + g[i0:i1, None] * (sosfiltfilt(peaking(2200, -2.0, 0.6), seg, axis=0) - seg)
    return b


def suck_back(n):
    """Pre-drop gain: full until 0.40 s before the drop, near-silence (-40 dB, dying out) for the
    last 0.35 s."""
    d, t = T(DROP_BAR), np.arange(n) / SR
    return 1 - 0.99 * rise(t, d - 0.40, d - 0.35) - 0.01 * rise(t, d - 0.35, d)


def duck_curve(n, attack=0.15, release=0.2):
    """Score gain under the voice: DUCK_DB inside every spoken line with raised-cosine ramps."""
    m = np.zeros(n)
    for ln in TL['lines']:
        a, b, c, d = ns(ln['start'] - attack), ns(ln['start']), ns(ln['end']), ns(ln['end'] + release)
        m[a:b] = np.maximum(m[a:b], fade(b - a))
        m[b:c] = 1.0
        m[c:d] = np.maximum(m[c:d], fade(d - c)[::-1])
    return db(DUCK_DB * m)


def mono_bass(x, f=110.0):
    """Collapse everything under ~110 Hz to mono (zero-phase high-pass on the side channel)."""
    mono = x.mean(1)
    side = sosfiltfilt(_sos('high', f), (x[:, 0] - x[:, 1]) / 2)
    return np.stack([mono + side, mono - side], 1)


def master(mix):
    a = glass_box(mix.render('A', 'music'))
    a += mix.render('A', 'glass')
    a *= suck_back(len(a))[:, None].astype(np.float32)
    b = voice_scoop(mix.render('B', 'music'))
    x = np.concatenate([a, b]).astype(np.float64)
    del a, b
    x = mono_bass(highpass(x, 24))
    return x * duck_curve(len(x))[:, None]


# ------------------------------------------------------------------------------ measurement
def kweight(x):
    """BS.1770 K-weighting (48 kHz coefficients)."""
    y = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285],
                [1.0, -1.69065929318241, 0.73248077421585], x, axis=0)
    return lfilter([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], y, axis=0)


def block_power(x, block, hop, centred=False):
    y = kweight(x)
    c = np.concatenate([[0.0], np.cumsum((y ** 2).sum(1))])
    if centred:                                       # one value per hop, window centred on it
        mid_ = np.arange(0, len(y), hop)
        lo, hi = np.clip(mid_ - block // 2, 0, len(y)), np.clip(mid_ + block // 2, 0, len(y))
        return (c[hi] - c[lo]) / np.maximum(hi - lo, 1)
    s = np.arange(0, len(y) - block + 1, hop)
    return (c[s + block] - c[s]) / block


def lufs(x):
    """BS.1770-4 integrated loudness (400 ms blocks, 75 % overlap, absolute and relative gates)."""
    z = block_power(x, ns(0.4), ns(0.1))
    z = z[z > 10 ** ((-70 + 0.691) / 10)]
    if not z.size:
        return -np.inf
    return -0.691 + 10 * np.log10(z[z > z.mean() * 0.1].mean())


def peak_env(x, up=4):
    """Per-sample peak (over channels) of the 4x-oversampled signal: a true-peak detector."""
    out = np.empty(len(x))
    step, pad = 1 << 19, 64
    for a in range(0, len(x), step):
        b = min(len(x), a + step)
        lo, hi = max(0, a - pad), min(len(x), b + pad)
        u = np.abs(resample_poly(x[lo:hi], up, 1, axis=0)).max(1)
        out[a:b] = u[(a - lo) * up:(b - lo) * up].reshape(-1, up).max(1)
    return out


def limit(x, pk, ceiling_db):
    """Look-ahead true-peak limiter. The gain reduction needed per sample is spread backwards at
    0.5 dB/ms (attack) and released at 12 dB/s, both as running maxima, so the ceiling always holds."""
    need = np.maximum(0.0, 20 * np.log10(np.maximum(pk, 1e-12)) - ceiling_db)
    if not need.any():
        return x, need
    i = np.arange(len(need))
    sa, sr = 0.5 / ns(0.001), 12.0 / SR
    att = sa * i + np.maximum.accumulate((need - sa * i)[::-1])[::-1]
    rel = np.maximum.accumulate(need + sr * i) - sr * i
    gr = np.maximum(att, rel)
    return x * db(-gr)[:, None], gr


def finalize(x):
    """Normalise to TARGET_LUFS through the limiter (iterated), then the fade in/out."""
    pk = peak_env(x)
    gain = TARGET_LUFS - lufs(x)
    for _ in range(6):
        y, gr = limit(x * db(gain), pk * db(gain), CEILING_DBTP)
        err = TARGET_LUFS - lufs(y)
        if abs(err) < 0.02:
            break
        gain += err
    y *= asr(len(y), 1.0, 4.0)[:, None]
    return y, gain, gr


def write_wav(path, x):
    """16-bit PCM with TPDF dither (none on digital silence)."""
    rng = np.random.default_rng(1)
    q = x * 32767.0
    q += (rng.random(q.shape) - rng.random(q.shape)) * (np.abs(q) > 2)
    q = np.clip(np.round(q), -32768, 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(q.tobytes())


def read_wav(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1, 2) / 32768.0


# ------------------------------------------------------------------------------ spectrogram
INK = {'surface': (26, 26, 25), 'primary': (255, 255, 255), 'secondary': (195, 194, 183),
       'muted': (137, 135, 129), 'grid': (44, 44, 42), 'axis': (56, 56, 53), 'blue': (57, 135, 229),
       'orange': (217, 89, 38), 'critical': (208, 59, 59)}
RAMP = ['#1a1a19', '#0d366b', '#104281', '#184f95', '#256abf', '#3987e5', '#6da7ec', '#9ec5f4', '#cde2fb']


def _font(size):
    from PIL import ImageFont
    try:
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)
    except OSError:
        return ImageFont.load_default(size=size)


def spectrogram_png(y, path, subtitle, lo_db=-100.0, hi_db=-25.0):
    """Log-frequency spectrogram (20 Hz-20 kHz, one-hue sequential ramp) with section boundaries, a
    lane of the spoken lines and a level lane (short-term loudness + sample peak)."""
    from PIL import Image, ImageDraw
    px, H = 10, 560
    W = int(round(len(y) / SR * px))
    L, R, TOP, GAP, STRIP, LANE, BOT = 86, 150, 78, 10, 22, 190, 50
    img = Image.new('RGB', (L + W + R, TOP + H + GAP + STRIP + GAP + LANE + BOT), INK['surface'])
    d = ImageDraw.Draw(img, 'RGBA')
    f12, f13, f16 = _font(12), _font(13), _font(17)

    mono = y.mean(1)
    nfft, hop = 8192, SR // px
    padded = np.concatenate([np.zeros(nfft // 2), mono, np.zeros(nfft)])
    frames = np.lib.stride_tricks.sliding_window_view(padded, nfft)[::hop][:W]
    win = np.hanning(nfft)
    P = np.empty((nfft // 2 + 1, W))
    for a in range(0, W, 256):
        P[:, a:a + 256] = (np.abs(rfft(frames[a:a + 256] * win, axis=1)) ** 2).T
    P /= (nfft / 4) ** 2                                  # a full-scale sine reads 0 dB
    edges = 20 * 1000 ** (np.arange(H + 1) / H) * nfft / SR
    cs = np.vstack([np.zeros((1, W)), np.cumsum(P, 0)])
    lo = np.floor(edges[:-1]).astype(int)
    hi = np.maximum(lo + 1, np.ceil(edges[1:]).astype(int))
    kc = np.sqrt(edges[:-1] * edges[1:])
    k0 = np.floor(kc).astype(int)
    fr = (kc - k0)[:, None]
    band_mean = (cs[hi] - cs[lo]) / (hi - lo)[:, None]     # rows spanning >= 3 bins: mean power
    interp = P[k0] * (1 - fr) + P[k0 + 1] * fr               # narrower rows (low end): interpolate
    sdb = 10 * np.log10(np.where((hi - lo >= 3)[:, None], band_mean, interp)[::-1] + 1e-14)
    stops = np.array([[int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in RAMP], float)
    grid = np.linspace(0, 1, len(RAMP))
    lut = np.stack([np.interp(np.linspace(0, 1, 256), grid, stops[:, c]) for c in range(3)], 1)
    idx = np.clip((sdb - lo_db) / (hi_db - lo_db) * 255, 0, 255).astype(np.uint8)
    img.paste(Image.fromarray(lut[idx].astype(np.uint8), 'RGB'), (L, TOP))

    y_s, y_v, y_l = TOP, TOP + H + GAP, TOP + H + GAP + STRIP + GAP
    for f in (20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000):
        yy = TOP + H - H * np.log(f / 20) / np.log(1000)
        d.line([(L, yy), (L + W, yy)], fill=(255, 255, 255, 34))
        d.text((L - 8, yy), f'{f // 1000}k' if f >= 1000 else str(f), font=f12, fill=INK['muted'], anchor='rm')
    d.text((14, TOP + H / 2), 'Hz', font=f12, fill=INK['muted'], anchor='lm')

    cx = L + W + 34                                       # scale legend for the ramp
    for r in range(H):
        d.line([(cx, TOP + r), (cx + 14, TOP + r)], fill=tuple(int(v) for v in lut[int(255 * (1 - r / (H - 1)))]))
    for v in range(int(hi_db), int(lo_db) - 1, -15):
        yy = TOP + H * (hi_db - v) / (hi_db - lo_db)
        d.text((cx + 20, yy), f'{v} dB', font=f12, fill=INK['muted'], anchor='lm')

    for ln in TL['lines']:                                # spoken lines
        d.rounded_rectangle([L + ln['start'] * px, y_v + 4, L + ln['end'] * px, y_v + STRIP - 4], 3,
                            fill=INK['muted'])
    d.text((L - 8, y_v + STRIP / 2), 'voice', font=f12, fill=INK['muted'], anchor='rm')

    def ly(v):                                            # level lane: -60..0 dB
        return y_l + LANE * (0 - v) / 60
    for v in (0, -12, -24, -36, -48, -60):
        d.line([(L, ly(v)), (L + W, ly(v))], fill=INK['grid'])
        d.text((L - 8, ly(v)), f'{v}', font=f12, fill=INK['muted'], anchor='rm')
    for v, label in ((TARGET_LUFS, f'{TARGET_LUFS:g} LUFS target'), (-1.0, '-1 dBTP ceiling')):
        for x0 in range(L, L + W, 12):
            d.line([(x0, ly(v)), (x0 + 6, ly(v))], fill=INK['secondary'])
        d.text((L + W + 8, ly(v)), label, font=f12, fill=INK['secondary'], anchor='lm')
    st = -0.691 + 10 * np.log10(block_power(y, ns(3.0), hop, centred=True)[:W] + 1e-12)
    ab = np.abs(y).max(1)
    ab = np.concatenate([ab, np.zeros(max(0, W * hop - len(ab)))])[:W * hop]
    pk = 20 * np.log10(ab.reshape(W, hop).max(1) + 1e-9)
    for series, col in ((pk, INK['orange']), (st, INK['blue'])):
        pts = [(L + i + 0.5, ly(float(np.clip(v, -60, 0)))) for i, v in enumerate(series)]
        d.line(pts, fill=col, width=2)
    clips = np.flatnonzero(pk > -0.01)
    for i in clips:
        d.line([(L + i, y_l), (L + i, y_l + 8)], fill=INK['critical'], width=2)
    if clips.size:
        d.text((L + clips[0] + 4, y_l + 2), 'clip', font=f12, fill=INK['critical'])
    lx = L + 12
    for label, col in (('short-term loudness, LUFS (3 s)', INK['blue']), ('sample peak, dBFS', INK['orange'])):
        d.rounded_rectangle([lx, ly(-54) - 5, lx + 18, ly(-54) + 5], 2, fill=col)
        d.text((lx + 24, ly(-54)), label, font=f12, fill=INK['secondary'], anchor='lm')
        lx += 24 + d.textlength(label, font=f12) + 24

    for s in TL['sections']:                              # section boundaries + names
        x0, x1 = L + s['start'] * px, L + s['end'] * px
        d.line([(x0, y_s - 6), (x0, y_l + LANE)], fill=(255, 255, 255, 150))
        d.text(((x0 + x1) / 2, y_s - 12), s['name'], font=f13, fill=INK['primary'], anchor='ms')
    d.line([(L + W, y_s - 6), (L + W, y_l + LANE)], fill=(255, 255, 255, 150))
    for sec in range(0, int(len(y) / SR) + 1, 10):
        x0 = L + sec * px
        d.line([(x0, y_l + LANE), (x0, y_l + LANE + 5)], fill=INK['axis'])
        if sec % 20 == 0:
            d.text((x0, y_l + LANE + 8), f'{sec // 60}:{sec % 60:02d}', font=f12, fill=INK['muted'], anchor='mt')
    d.text((L, 14), 'Score spectrogram (log frequency)', font=f16, fill=INK['primary'])
    d.text((L, 38), subtitle, font=f13, fill=INK['secondary'])
    img.save(path)


# ------------------------------------------------------------------------------ main
def main():
    t_start = time.time()
    build_irs()
    mix = Mix(T(DROP_BAR))
    for track in TRACKS:
        t0 = time.time()
        track(mix)
        print(f'  {track.__name__:16} {time.time() - t0:5.1f}s', flush=True)
    raw = master(mix)
    y, gain, gr = finalize(raw)
    assert len(y) == N and np.isfinite(y).all()
    out = os.path.join(MV, 'score.wav')
    write_wav(out, y)
    y = read_wav(out)
    tp = 20 * np.log10(peak_env(y).max())
    loud = lufs(y)
    print(f'wrote {out}: {len(y) / SR:.3f}s, {loud:.2f} LUFS, true peak {tp:.2f} dBTP, '
          f'sample peak {20 * np.log10(np.abs(y).max()):.2f} dBFS, limiter max GR {gr.max():.2f} dB, '
          f'{int((np.abs(y) >= 32767 / 32768).sum())} full-scale samples, master gain {gain:+.1f} dB '
          f'({time.time() - t_start:.0f}s)')
    hot = np.flatnonzero(gr > 1.5)
    if hot.size:
        groups = np.split(hot, np.flatnonzero(np.diff(hot) > SR // 4) + 1)
        print(f'  limiter > 1.5 dB in {len(groups)} places, the biggest: ' + ', '.join(
            f'{g[0] / SR:.2f}s ({gr[g].max():.1f} dB)' for g in sorted(groups, key=lambda g: -gr[g].max())[:8]))
    print('  section      LUFS   peak dBFS  limiter GR | dry track levels (dB RMS after master gain)')
    tracks = sorted({k[0] for k in mix.meter})
    for s in TL['sections']:
        a, b = ns(s['start']), ns(s['end'])
        lv = [(tr, 10 * np.log10(mix.meter[(tr, s['name'])] / (2 * (b - a)) + 1e-20) + gain)
              for tr in tracks if mix.meter.get((tr, s['name']), 0) > 0]
        print(f"  {s['name']:10} {lufs(y[a:b]):6.1f} {20 * np.log10(np.abs(y[a:b]).max()):7.1f} "
              f"{gr[a:b].max():9.1f} dB | " + ' '.join(f'{tr} {v:.0f}' for tr, v in sorted(lv, key=lambda kv: -kv[1])))
    png = os.path.join(MV, 'score_spectrogram.png')
    spectrogram_png(y, png, f'{os.path.basename(out)}  ·  {loud:.1f} LUFS integrated  ·  true peak {tp:.1f} dBTP'
                            f'  ·  {len(y) / SR:.3f} s  ·  D minor, 70 BPM')
    print(f'wrote {png}')


if __name__ == '__main__':
    main()
