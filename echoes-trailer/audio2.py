"""Echoes in the Dark v2 - brutal thriller score, sound design and narration (6:00).

Built on the synth kit in audio.py plus heavier trailer weapons: layered impact
stacks, opening-filter braams, Shepard-tone risers, tremolo and screeching strings,
glitch stabs on stutter cuts, thunder for every strike, weather beds per world,
electric crackle, metal debris, card slams synced to the narrator's words.

  python3 audio2.py   -> out2/soundtrack_raw.wav (48 kHz stereo float)
"""
import os

import numpy as np
import soundfile as sf
from scipy.signal import butter, resample_poly, sosfilt

import audio as K
import timeline2 as T
from audio import (NOTE, SR, Bus, bell, braam, choir, echo, env_adsr, glide_sine, heartbeat, make_ir, noise_swell,
                   pad, pan_st, pluck, reverb, saw, sos_bp, sos_hp, sos_lp, staccato, sub_hit, taiko, tick, tt,
                   whoosh)

HERE = os.path.dirname(os.path.abspath(__file__))
N = int(T.DURATION * SR) + SR
K.N = N
rng = np.random.default_rng(77)
BEAT = 0.5          # 120 bpm
BAR = 4 * BEAT
GRID = T.BOOM       # the formation score locks to the boom


class Bus32(Bus):
    """Same as audio.Bus but float32, so the 6-minute mix fits next to the renderer."""

    def __init__(self):
        self.x = np.zeros((2, N), np.float32)


# ----------------------------------------------------------------------------- new weapons
def tv_lowpass(x, fc_at, block=256, order=2):
    """Time-varying low-pass (block-wise biquads with carried state)."""
    y = np.zeros_like(x)
    zi = None
    for i in range(0, len(x), block):
        fc = float(np.clip(fc_at(i / SR), 40, SR * 0.45))
        sos = butter(order, fc, "low", fs=SR, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        y[i:i + block], zi = sosfilt(sos, x[i:i + block], zi=zi)
    return y


def braam2(root, dur=5.0, bright=1.0, notes=None, drive=2.2):
    """Inception-style brass: detuned saw stack, filter slams open then closes, driven."""
    notes = notes or [root, root * 2, root * 3, root * 4 * 2 ** (3 / 12), root * 6]
    x = sum(saw(f, dur, (-14, -6, 3, 11)) * (1.0 if i < 2 else 0.7) for i, f in enumerate(notes))
    x = np.tanh(x * drive)
    fc = lambda s: 180 + 2600 * bright * np.exp(-s / (dur * 0.28)) * min(1.0, s / 0.06)
    y = tv_lowpass(x, fc, 256, 2)
    y = tv_lowpass(y, fc, 256, 2)
    e = env_adsr(len(y), 0.02, 0.5, 0.6, dur * 0.5)
    sub = sub_hit(dur, 70, root * 0.99, 2.0) * 0.9
    return np.tanh((y * e * 1.3 + sub) * 1.2)


def hit_stack(size=1.0, dur=5.0):
    """Trailer impact: transient crack + metal clang + 808 boom + sub drop + taiko +
    gated snare slam + crash, glued with saturation."""
    t = tt(dur)
    crack = sosfilt(sos_hp(1800, 2), rng.normal(0, 1, len(t))) * np.exp(-t / 0.012) * 0.9
    metal = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * a * np.exp(-t * d)
                for f, a, d in ((97, 0.7, 1.2), (181, 0.6, 2.0), (283, 0.5, 2.6), (457, 0.4, 3.5), (731, 0.3, 4.5),
                                (1187, 0.2, 6.0), (1931, 0.12, 8.0)))
    boom = np.sin(2 * np.pi * np.cumsum(38 + 30 * np.exp(-t / 0.05)) / SR) * np.exp(-t / (0.9 + 0.6 * size))
    sub = sub_hit(dur, 110 + 30 * size, 27, 3.0)
    tom = np.pad(taiko(min(dur, 2.0), 90, 45), (0, max(0, len(t) - int(min(dur, 2.0) * SR))))[:len(t)]
    body = sosfilt(sos_lp(700, 2), rng.normal(0, 1, len(t))) * np.exp(-t / 0.25) * 0.6
    snare = (sosfilt(sos_bp(900, 7000), rng.normal(0, 1, len(t))) * (t < 0.32) * np.exp(-t / 0.2) * 0.7
             + np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.06) * 0.5)
    crash = sosfilt(sos_hp(4500, 2), rng.normal(0, 1, len(t))) * np.exp(-t / 1.4) * 0.22
    x = crack + metal * 0.4 + boom * 1.2 * size + sub * 1.0 * size + tom * 0.8 + body + snare * 0.8 + crash
    return np.tanh(x * 1.35)


def reverse_swell(dur=1.2):
    """Reversed reverb-like swell that sucks into a hit."""
    t = tt(dur)
    n = sosfilt(sos_bp(300, 7000), rng.normal(0, 1, len(t)))
    return n * (t / dur) ** 3


def shepard(dur, base=40.0, n_oct=7, speed0=0.08, speed1=0.35):
    """Shepard-Risset glissando: feels like it rises forever."""
    t = tt(dur)
    u = t / dur
    speed = speed0 + (speed1 - speed0) * u ** 2
    pos0 = np.cumsum(speed) / SR
    out = np.zeros_like(t)
    for k in range(n_oct):
        pos = (k + pos0) % n_oct
        f = base * 2 ** pos
        amp = np.exp(-((pos - n_oct / 2) / (n_oct / 4.5)) ** 2)
        ph = 2 * np.pi * np.cumsum(f) / SR
        out += amp * (np.sin(ph) + 0.35 * np.sin(2 * ph))
    return out / n_oct * 2 * (0.25 + 0.75 * u ** 1.5)


def tremolo(notes, dur, rate=14.0, fc=3200, att=2.0, rel=2.0):
    x = sum(saw(NOTE[n], dur, (-12, -4, 5, 12)) for n in notes) / len(notes)
    x = sosfilt(sos_lp(fc, 4), x)
    trem = (0.55 + 0.45 * np.sin(2 * np.pi * rate * tt(dur))) ** 2
    return x * trem * env_adsr(len(x), att, 0.5, 0.95, rel)


def screech(dur, notes=("D6", "D#6", "A5", "G#5")):
    t = tt(dur)
    x = np.zeros_like(t)
    for n in notes:
        vib = 1 + 0.012 * np.sin(2 * np.pi * (5.5 + rng.uniform(-0.5, 0.5)) * t + rng.uniform(0, 6))
        ph = 2 * np.pi * np.cumsum(NOTE[n] * vib * (1 + 0.03 * (t / dur) ** 2)) / SR
        x += (2 * ((ph / (2 * np.pi)) % 1) - 1)
    x = sosfilt(sos_bp(900, 6000), x / len(notes))
    return x * (t / dur) ** 2


def stab(root=NOTE["D3"], dur=0.45, gain=1.0):
    notes = [root, root * 2 ** (3 / 12), root * 2 ** (7 / 12), root * 2, root / 2]
    x = sum(saw(f, dur, (-9, 8)) for f in notes)
    x = tv_lowpass(np.tanh(x * 2.0), lambda s: 5000 * np.exp(-s / 0.08) + 500, 128, 2)
    e = env_adsr(len(x), 0.003, 0.12, 0.35, 0.2)
    click = sosfilt(sos_hp(2500, 2), rng.normal(0, 1, len(x))) * np.exp(-tt(dur) / 0.01)
    return (x * e + click * 0.6 + sub_hit(dur, 90, 40) * 0.8) * gain


def glitch(dur=0.35):
    """Digital stutter: a grain repeated with shrinking period + pitch jumps."""
    t = tt(dur)
    out = np.zeros_like(t)
    g = int(0.028 * SR)
    grain = sosfilt(sos_bp(400, 6000), rng.normal(0, 1, g)) * np.hanning(g)
    pos = 0
    k = 0
    while pos + g < len(t):
        f = 300 * 2 ** rng.integers(0, 5)
        blip = np.sin(2 * np.pi * f * np.arange(g) / SR) * np.hanning(g) * 0.6
        out[pos:pos + g] += grain + blip
        pos += max(int(g * (0.9 - 0.06 * k)), int(0.012 * SR))
        k += 1
    return out * 0.7


def thunder(dur=6.0, dist=0.5):
    t = tt(dur)
    crack = sosfilt(sos_hp(900, 2), rng.normal(0, 1, len(t))) * np.exp(-t / (0.05 + 0.1 * dist)) * (1.2 - dist)
    brown = np.cumsum(rng.normal(0, 1, len(t)))
    brown = sosfilt(sos_hp(20, 1), brown)
    brown /= np.abs(brown).max() + 1e-9
    rumble = sosfilt(sos_lp(160 + 200 * (1 - dist), 2), brown)
    mod = np.clip(np.interp(t, np.linspace(0, dur, 40), rng.uniform(0.2, 1.0, 40)), 0, 1)
    rumble = rumble * mod * np.exp(-t / (1.6 + 2.0 * dist)) * np.clip(t / 0.08, 0, 1)
    return np.tanh((crack * 0.8 + rumble * 3.0) * 1.2)


def rain_bed(dur):
    t = tt(dur)
    hiss = sosfilt(sos_bp(900, 9000), rng.normal(0, 1, len(t))) * 0.35
    drops = np.zeros_like(t)
    idx = rng.integers(0, len(t), int(dur * 900))
    drops[idx] = rng.uniform(-1, 1, len(idx))
    drops = sosfilt(sos_bp(1500, 8000), drops) * 1.5
    return hiss + drops


def ocean_bed(dur):
    t = tt(dur)
    n = rng.normal(0, 1, len(t))
    swell = (0.5 + 0.5 * np.sin(2 * np.pi * t / 7.3 + 1)) ** 2 * 0.8 + 0.2
    low = sosfilt(sos_lp(600, 2), n) * swell
    foam = sosfilt(sos_bp(2500, 9000), n) * swell ** 3 * 0.25
    return low + foam


def wind_bed(dur):
    t = tt(dur)
    n = rng.normal(0, 1, len(t))
    fc = lambda s: 380 + 260 * np.sin(2 * np.pi * s / 9.0) + 120 * np.sin(2 * np.pi * s / 3.1)
    w = tv_lowpass(n, fc, 512, 2) - tv_lowpass(n, lambda s: fc(s) * 0.45, 512, 2)
    return w * (0.6 + 0.4 * np.sin(2 * np.pi * t / 6.0)) * 2.0


def forest_bed(dur):
    t = tt(dur)
    w = wind_bed(dur) * 0.6
    creak = np.zeros_like(t)
    for _ in range(int(dur / 2.5)):
        i = rng.integers(0, len(t) - SR)
        L = int(rng.uniform(0.3, 0.9) * SR)
        f0 = rng.uniform(70, 160)
        c = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.3 * np.sin(np.linspace(0, 9, L)))) / SR)
        creak[i:i + L] += np.sign(c) * np.hanning(L) * 0.08
    creak = sosfilt(sos_bp(200, 1800), creak)
    return w + creak


def space_bed(dur):
    t = tt(dur)
    d = K.drone([NOTE["D1"], NOTE["A1"]], dur, fc=300)
    glass = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * (0.5 + 0.5 * np.sin(2 * np.pi * t / p + rng.uniform(0, 6)))
                for f, p in ((1174.7, 11), (1760, 7), (2637, 13), (3520, 5)))
    return d + glass * 0.03


def crackle(dur, density=120):
    t = tt(dur)
    out = np.zeros_like(t)
    for _ in range(int(dur * density)):
        i = rng.integers(0, len(t) - 600)
        L = rng.integers(60, 600)
        out[i:i + L] += rng.normal(0, 1, L) * np.hanning(L)
    out = sosfilt(sos_bp(1200, 9000), out)
    buzz = saw(60, dur, (0,)) * (rng.uniform(0, 1, int(dur * 40)).repeat(int(SR / 40))[:len(t)] > 0.6)
    return out * 0.6 + sosfilt(sos_lp(900, 2), buzz) * 0.25


def debris(dur=3.5, n=70):
    """Metal shards raining down: many tiny bell pings, dense then sparse."""
    out = np.zeros(int(dur * SR))
    for _ in range(n):
        at = rng.exponential(0.7)
        if at > dur - 0.6:
            continue
        b = bell(rng.uniform(1800, 5200), 0.6) * rng.uniform(0.2, 1.0) * np.exp(-at / 1.4)
        i = int(at * SR)
        out[i:i + len(b)] += b[:len(out) - i]
    return out


def card_slam(size=1.0):
    return hit_stack(0.8 * size, 3.5) + np.pad(stab(NOTE["D2"], 0.6, 0.6 * size), (0, int(2.9 * SR)))


def pulse_bass(freq, dur=0.22):
    x = saw(freq, dur, (-6, 6)) + saw(freq / 2, dur, (0,)) * 0.8
    x = tv_lowpass(x, lambda s: 200 + 1600 * np.exp(-s / 0.05), 64, 2)
    return x * env_adsr(len(x), 0.003, 0.06, 0.4, 0.08)


# ----------------------------------------------------------------------------- the score
def build():
    mus, sfx, wet = Bus32(), Bus32(), Bus32()

    def M(t0, sig, g, pan=0.0, width=0.0, send=0.3):
        mus.add(t0, sig, g, pan, width)
        wet.add(t0, sig, g * send, pan, width)

    def X(t0, sig, g, pan=0.0, width=0.0, send=0.4):
        sfx.add(t0, sig, g, pan, width)
        wet.add(t0, sig, g * send, pan, width)

    def HIT(t0, g=1.0, pre=1.2):
        X(t0 - pre, reverse_swell(pre), 0.35 * g, width=1, send=0.6)
        X(t0, hit_stack(g, 5.0), 0.9 * g, width=1, send=0.6)

    # ---- cold open
    X(0.0, sub_hit(7.0, 45, 30, 1.2) * np.clip(tt(7.0) / 4, 0, 1), 0.14, send=0.1)
    for t0 in (1.6, 3.0):
        X(t0, heartbeat(0.8), 0.45, send=0.2)
    flashes = [3.35, 4.25, 4.95, 5.45, 5.85, 6.15, 6.40, 6.60]
    for i, t0 in enumerate(flashes):
        g = [0.25, 0.3, 0.45, 0.8, 0.9, 1.0, 1.0, 1.1][i]
        X(t0, stab(NOTE["D3"] * [1, 1.06, 1, 0.94, 1, 1.12, 1, 1.19][i], 0.4, 1.0), 0.45 * g, width=1, send=0.4)
        X(t0, glitch(0.25), 0.25 * g, pan=rng.uniform(-0.5, 0.5), send=0.2)
    X(6.75, reverse_swell(0.25), 0.5, width=1)
    HIT(7.0, 0.7, pre=0.01)

    # ---- Act I
    sb = space_bed(12.0)
    M(7.0, sb * env_adsr(len(sb), 1.5, 1, 1, 2.5), 0.35, width=1, send=0.4)
    X(T.SPARK - 2.0, noise_swell(2.0, 800, 11000), 0.22, width=1)
    X(T.SPARK, echo(bell(NOTE["A5"], 5.0) + bell(NOTE["E6"], 5.0) * 0.5, 0.5, 0.5, 6), 0.3)
    HIT(T.SPARK, 0.6, pre=0.8)
    for r in T.RINGS:
        late = r >= 66.5
        X(r, heartbeat(1.0 if not late else 1.25), 0.5 if not late else 0.75, send=0.15)
        if not late:
            X(r, echo(bell(NOTE["D6"], 1.5) * 0.4, 0.32, 0.4, 4), 0.07, pan=rng.uniform(-0.6, 0.6))
    M(16.0, K.drone([NOTE["D1"], NOTE["A1"]], 57.0, fc=420) * env_adsr(int(57 * SR), 4, 1, 1, 3), 0.28, width=1, send=0.2)
    tr = tremolo(["D4", "F4", "A4"], 12.0, att=5.0, rel=1.0)
    M(19.0, tr, 0.10, width=1, send=0.5)
    # cards: EVERY SOUND / HAS AN ECHO
    for t0, t1, text in T.CARDS[:2]:
        X(t0 - 0.5, reverse_swell(0.5), 0.4, width=1)
        X(t0, card_slam(1.0), 0.8, width=1, send=0.6)
    X(T.CARDS[1][0], echo(hit_stack(0.5, 1.5), 0.42, 0.5, 5), 0.35, width=1)  # the slam itself echoes
    ob = ocean_bed(12.5)
    X(31.0, ob * env_adsr(len(ob), 0.3, 1, 1, 1.0), 0.18, width=1, send=0.1)
    X(31.0, whoosh(1.0), 0.3, width=1)
    wb = wind_bed(12.5)
    X(43.0, wb * env_adsr(len(wb), 0.3, 1, 1, 1.0), 0.12, width=1, send=0.1)
    X(43.0, whoosh(1.0), 0.3, width=1)
    M(31.0, tremolo(["D3", "A3", "D4", "F4"], 24.0, rate=12, att=6, rel=2), 0.10, width=1, send=0.5)
    # gathering: rising tension into the montage
    M(55.0, tremolo(["D5", "D#5", "A4"], 16.3, rate=16, att=8, rel=0.3), 0.08, width=1, send=0.5)
    X(55.0, shepard(16.2, 40, 7, 0.06, 0.4), 0.22, width=1, send=0.3)
    for k, t0 in enumerate(np.arange(60.0, 71.2, BEAT / 2)):
        X(t0, tick(k % 2 == 0), 0.05 + 0.12 * (t0 - 60) / 11, pan=0.3 if k % 2 else -0.3, send=0.1)
    cuts = [63.0, 65.2, 67.0, 68.5, 69.6, 70.5]
    for i, t0 in enumerate(cuts):
        X(t0, stab(NOTE["D3"] * 2 ** ((i % 3) / 12), 0.4, 1.0), 0.45, width=1, send=0.4)
        X(t0 - 0.35, whoosh(0.4, rev=True), 0.3, width=1)
    for ts, kind in T.STRIKES:
        if 60 < ts < 100 or 150 < ts < 180 or 240 < ts < 250:
            X(ts, thunder(6.0, 0.25 if kind != "sky" else 0.6), 0.55, width=1, send=0.4)
            if kind == "emblem":
                X(ts, crackle(1.2, 160), 0.25, width=1, send=0.2)
    X(71.3, screech(1.3), 0.2, width=1, send=0.6)                 # the drop before "they were wrong"
    X(72.6, card_slam(0.8), 0.6, width=1, send=0.6)
    X(74.0, reverse_swell(1.0), 0.6, width=1, send=0.4)

    # ---- BOOM
    HIT(T.BOOM, 1.3, pre=0.01)
    X(T.BOOM, braam2(NOTE["D1"], 7.0, 1.2), 0.8, width=1, send=0.6)
    X(T.BOOM, noise_swell(3.0, 300, 9000, rise=False), 0.35, width=1, send=0.8)

    # ---- Act II: the formation (120 bpm grid from the boom)
    sections = [(77.0, 84.0, "drive"), (84.0, 100.0, "storm"), (100.0, 112.0, "chase"), (112.0, 128.0, "forest"),
                (128.0, 142.0, "chase2"), (142.0, 156.0, "ocean"), (156.0, 178.0, "montage"),
                (178.0, 196.0, "epic"), (196.0, 212.0, "build"), (212.0, T.SILENCE[0], "final")]
    prog = ["D2", "D2", "A#1", "A1", "D2", "D2", "C2", "A1"]
    bar_i = 0
    t0 = 77.0
    while t0 < T.SILENCE[0] - 1e-6:
        sec = [s for a, b, s in sections if a <= t0 < b][0]
        root = NOTE[prog[bar_i % len(prog)]]
        inten = {"drive": 0.5, "storm": 0.8, "chase": 0.7, "forest": 0.45, "chase2": 0.85, "ocean": 0.75,
                 "montage": 1.0, "epic": 0.95, "build": 1.0, "final": 1.05}[sec]
        step = BEAT / 4 if sec in ("chase", "chase2", "montage", "build", "final") else BEAT / 2
        if sec == "forest":
            step = BEAT
        for k in range(int(round(BAR / step))):
            tk = t0 + k * step
            if tk >= T.SILENCE[0]:
                break
            acc = 1.0 if k % 4 == 0 else 0.7
            M(tk, pulse_bass(root * (2 if k % 8 == 6 else 1), 0.2), 0.16 * inten * acc, send=0.08)
        # drums
        X(t0, taiko(1.6, 95, 48), 0.55 * inten, send=0.5)
        if sec != "forest":
            X(t0 + 2 * BEAT, taiko(1.4, 110, 55), 0.45 * inten, send=0.5)
        if sec in ("storm", "chase2", "montage", "epic", "build", "final"):
            for kk in (1.5, 3.0, 3.5):
                X(t0 + kk * BEAT, taiko(0.9, 150, 80), 0.28 * inten, pan=rng.uniform(-0.5, 0.5), send=0.4)
        if sec in ("montage", "build", "final"):
            for kk in range(8):
                X(t0 + kk * BEAT / 2, taiko(0.5, 190, 110), 0.14 * inten, pan=0.5 if kk % 2 else -0.5, send=0.3)
        for kk in range(8):
            X(t0 + kk * BEAT / 2, tick(kk % 2 == 0), 0.05 * inten, pan=0.3 if kk % 2 else -0.3, send=0.08)
        # braams and strings
        every = {"drive": 4, "storm": 2, "chase": 4, "forest": 8, "chase2": 2, "ocean": 4, "montage": 1,
                 "epic": 2, "build": 1, "final": 1}[sec]
        if bar_i % every == 0:
            X(t0, braam2(root / 2, BAR * min(every, 2) + 1.5, 0.7 + 0.4 * inten), 0.34 * inten, width=1, send=0.5)
        if bar_i % 4 == 0:
            chord = [["D3", "F3", "A3"], ["A#2", "D3", "F3"], ["G2", "A#2", "D3"], ["A2", "C#3", "E3"]][(bar_i // 4) % 4]
            M(t0, tremolo(chord + [c.replace("3", "4") for c in chord], BAR * 4 + 1.0, rate=14, att=1.0, rel=1.0),
              0.07 + 0.05 * inten, width=1, send=0.5)
            if sec in ("epic", "montage", "build", "final", "ocean"):
                M(t0, choir(chord, BAR * 4 + 1.5, att=1.0, rel=1.5), 0.12 * inten, width=1, send=0.6)
        bar_i += 1
        t0 += BAR
    # world beds during the formation
    for a, b, env in [(84.0, 100.0, "storm"), (112.0, 128.0, "forest"), (142.0, 156.0, "ocean"), (178.0, 196.0, "wind"),
                      (240.0, 252.0, "wind"), (252.0, 264.0, "ocean")]:
        d = b - a
        bed = {"storm": rain_bed, "forest": forest_bed, "ocean": ocean_bed, "wind": wind_bed}[env](d)
        X(a, bed * env_adsr(len(bed), 0.4, 1, 1, 0.8), {"storm": 0.16, "forest": 0.2, "ocean": 0.2, "wind": 0.14}[env],
          width=1, send=0.1)
    # every cut in the formation gets a whoosh; montage cuts get stabs + glitches
    for s in T.SHOTS:
        if 75.5 < s.t0 < 224 and (s.t1 - s.t0) > 0.2:
            X(s.t0 - 0.3, whoosh(0.35, rev=True), 0.22, width=1, send=0.3)
            if s.stutter > 0:
                X(s.t0, stab(NOTE["D3"] * 2 ** (rng.integers(0, 4) / 12), 0.35, 1.0), 0.4, width=1, send=0.4)
                X(s.t0, glitch(s.stutter + 0.05), 0.3, pan=rng.uniform(-0.6, 0.6), send=0.2)
    # FASTER / LOUDER / STRONGER: slams on the words
    for i, (tw, word) in enumerate(T.WORD_CARDS):
        X(tw - 0.35, reverse_swell(0.35), 0.4, width=1)
        X(tw, card_slam(1.0 + 0.2 * i), 0.8 + 0.15 * i, width=1, send=0.6)
    for r in T.GROW_RINGS:
        X(r, heartbeat(1.0), 0.35, send=0.2)
    # the dark is not empty... a bar of screeching strings
    X(181.5, screech(5.0), 0.12, width=1, send=0.6)
    # final build: Shepard riser + roll into the silence
    X(198.0, shepard(T.SILENCE[0] - 198.0, 38, 7, 0.07, 0.6), 0.34, width=1, send=0.3)
    for k, tk in enumerate(np.arange(218.0, T.SILENCE[0], BEAT / 8)):
        X(tk, taiko(0.35, 190, 110), 0.1 + 0.45 * ((tk - 218) / (T.SILENCE[0] - 218)) ** 2,
          pan=0.4 if k % 2 else -0.4, send=0.3)
    X(214.0, K.riser(T.SILENCE[0] - 214.0, 60, 3000), 0.3, width=1, send=0.3)

    # ---- THE HIT
    c = T.COMPLETE
    HIT(c, 1.6, pre=0.01)
    X(c, braam2(NOTE["D1"], 10.0, 1.6, notes=[NOTE["D1"], NOTE["D2"], NOTE["A2"], NOTE["D3"], NOTE["F3"], NOTE["A3"]]),
      1.0, width=1, send=0.7)
    X(c, noise_swell(5.0, 200, 11000, rise=False), 0.4, width=1, send=1.0)
    X(c + 0.05, debris(4.0, 90), 0.35, width=1, send=0.5)
    X(c, crackle(2.0, 220), 0.3, width=1, send=0.3)
    M(c, choir(["D3", "F3", "A3", "D4"], 16.0, att=0.2, rel=6.0), 0.4, width=1, send=0.7)
    M(c, pad(["D3", "A3", "D4", "F4"], 16.0, fc=2800, att=0.2, rel=6.0), 0.22, width=1, send=0.6)
    for k, tk in enumerate(np.arange(c + 4.0, 240.0, BEAT * 2)):
        X(tk, taiko(1.8, 85, 42), 0.5, send=0.6)
        if k % 2 == 1:
            X(tk, braam2(NOTE["A#1"] if k % 4 == 1 else NOTE["C2"], 3.0, 0.9), 0.3, width=1, send=0.5)
    for s0, s1 in T.SWEEPS:
        X(s0, whoosh(s1 - s0), 0.16, width=1, send=0.5)
    # monuments
    HIT(240.0, 0.7, pre=0.4)
    M(240.0, choir(["A#2", "D3", "F3", "A#3"], 12.5, att=1.0, rel=2.0), 0.3, width=1, send=0.7)
    X(240.0, braam2(NOTE["A#1"], 6.0, 1.0), 0.45, width=1, send=0.6)
    HIT(252.0, 0.6, pre=0.4)
    M(252.0, choir(["F2", "A2", "C3", "F3"], 12.5, att=1.0, rel=2.0), 0.28, width=1, send=0.7)
    X(252.0, braam2(NOTE["F1"], 6.0, 1.0), 0.4, width=1, send=0.6)
    M(264.0, tremolo(["D4", "D#4", "A3"], 6.5, rate=18, att=3.0, rel=0.3), 0.1, width=1, send=0.5)
    for k, tk in enumerate(np.arange(264.0, 270.0, BEAT / 2)):
        X(tk, tick(k % 2 == 0), 0.08, send=0.1)
    X(266.0, shepard(4.0, 40, 7, 0.2, 0.6), 0.25, width=1)

    # ---- a hit on every other impact point (scene cuts, strikes on the logo, flashes)
    explicit = {7.0, T.SPARK, 27.0, 29.1, 72.6, T.BOOM, T.COMPLETE, T.GLINT, T.REVEAL[0], T.SLAM, 240.0, 252.0, 270.0}
    explicit |= {tw for tw, w in T.WORD_CARDS}
    for ti, sv in T.IMPACTS:
        if any(abs(ti - e) < 0.05 for e in explicit):
            continue
        X(ti - 0.25, reverse_swell(0.25), 0.25 * sv, width=1)
        X(ti, hit_stack(0.55 * sv + 0.2, 3.0), 0.55 * sv + 0.1, width=1, send=0.5)

    # ---- the name
    HIT(270.0, 0.6, pre=0.8)
    M(270.0, pad(["D3", "F3", "A3", "C4"], 18.0, fc=1900, att=2.5, rel=4.0), 0.3, width=1, send=0.6)
    M(270.0, K.drone([NOTE["D1"], NOTE["A1"]], 38.0, fc=420) * env_adsr(int(38 * SR), 3, 1, 1, 4), 0.25, width=1, send=0.2)
    notes_up = ["D5", "F5", "A5", "C6", "D6", "F6", "A6", "C7", "D7", "F6", "A6", "D7", "A6", "D7", "F7"]
    for i in range(15):
        tl = T.LETTERS[0] + (T.LETTERS[1] - T.LETTERS[0] - 0.9) * i / 14
        X(tl, echo(pluck(NOTE[notes_up[i]], 2.2, 0.8), 0.28, 0.45, 4), 0.15, pan=-0.6 + 1.2 * i / 14)
    X(T.GLINT, echo(bell(NOTE["D6"], 5.0) + bell(NOTE["A6"], 5.0) * 0.5, 0.5, 0.5, 6), 0.28, width=1)
    HIT(T.GLINT, 0.8, pre=0.6)
    X(T.GLINT, braam2(NOTE["D1"], 7.0, 1.1), 0.55, width=1, send=0.6)
    M(T.TAGLINE[0], pad(["A#2", "D3", "F3", "A3"], 6.5, fc=1600), 0.26, width=1, send=0.6)
    M(T.TAGLINE[0] + 6.0, pad(["A2", "C#3", "E3", "A3"], 6.0, fc=1600), 0.28, width=1, send=0.6)
    for k, tk in enumerate(np.arange(T.TAGLINE[0], 300.0, BEAT)):
        X(tk, tick(k % 2 == 0), 0.05, send=0.1)
    # "will follow you into the light": crescendo into the reveal
    M(300.0, tremolo(["D4", "F#4", "A4", "D5"], 7.2, rate=14, att=5.0, rel=0.3), 0.14, width=1, send=0.6)
    X(300.0, shepard(7.0, 50, 7, 0.1, 0.5), 0.22, width=1)
    r0 = T.REVEAL[0]
    X(r0 - 2.5, noise_swell(2.5, 600, 12000), 0.4, width=1, send=0.4)
    HIT(r0, 1.0, pre=0.01)
    X(r0, braam2(NOTE["D1"], 9.0, 1.7, notes=[NOTE["D2"], NOTE["A2"], NOTE["D3"], NOTE["F#3"], NOTE["A3"]]), 0.7,
      width=1, send=0.7)
    M(r0, choir(["D4", "F#4", "A4", "D5"], 14.0, att=0.3, rel=5.0), 0.34, width=1, send=0.8)
    M(r0, pad(["D3", "F#3", "A3", "E4"], 14.0, fc=3400, att=0.2, rel=5.0), 0.22, width=1, send=0.7)
    X(r0, echo(bell(NOTE["F#6"], 5.0), 0.5, 0.5, 5), 0.24)
    # collapse
    X(T.COLLAPSE[0] - 0.4, whoosh(T.COLLAPSE[1] - T.COLLAPSE[0] + 0.4, rev=True), 0.45, width=1, send=0.5)
    X(T.COLLAPSE[0] - 0.4, reverse_swell(T.COLLAPSE[1] - T.COLLAPSE[0] + 0.4), 0.4, width=1)
    X(T.COLLAPSE[1], sub_hit(4.0, 90, 30), 0.8, send=0.3)

    # ---- finale
    ld = K.drone([NOTE["D1"], NOTE["G#1"]], T.SLAM - T.COLLAPSE[1], fc=320)   # tritone: the dark is calling
    M(T.COLLAPSE[1], ld * env_adsr(len(ld), 2.0, 1.0, 1.0, 1.5), 0.26, width=1, send=0.3)
    for k, tk in enumerate(np.arange(T.COLLAPSE[1] + 1.0, T.STAR_OUT - 0.2, BEAT)):
        X(tk, tick(k % 2 == 0), 0.07, pan=0.3 if k % 2 else -0.3, send=0.15)
    for tk in (324.0, 326.6, 329.4, 332.4):
        X(tk, heartbeat(0.9), 0.45, send=0.3)
    X(T.STAR_OUT, echo(bell(NOTE["D5"], 6.0), 0.55, 0.55, 7), 0.35, width=1)
    X(T.STAR_OUT, sub_hit(5.0, 70, 26), 0.8, send=0.4)
    X(T.SLAM - 3.0, screech(3.0), 0.18, width=1, send=0.6)
    X(T.SLAM - 1.5, reverse_swell(1.5), 0.6, width=1, send=0.5)
    HIT(T.SLAM, 1.7, pre=0.01)
    X(T.SLAM, braam2(NOTE["D1"], 12.0, 1.7, notes=[NOTE["D1"], NOTE["D2"], NOTE["A2"], NOTE["D3"], NOTE["F3"]]),
      1.0, width=1, send=0.7)
    X(T.SLAM + 0.05, debris(4.0, 90), 0.35, width=1, send=0.5)
    M(T.SLAM, choir(["D3", "F3", "A3", "D4"], 16.0, att=0.2, rel=8.0), 0.36, width=1, send=0.7)
    fd = K.drone([NOTE["D1"], NOTE["A1"]], 20.0, fc=380)
    M(T.SLAM, fd * env_adsr(len(fd), 1.0, 1.0, 1.0, 8.0), 0.24, width=1, send=0.2)
    X(346.0, whoosh(4.0), 0.14, width=1, send=0.5)
    X(357.0, heartbeat(0.8), 0.4, send=0.5)
    return mus, sfx, wet


def voice_track():
    vb, wet = Bus32(), Bus32()
    hp = sos_hp(70, 2)
    lens = {}
    for idx, t0 in T.VOICE:
        path = os.path.join(HERE, "assets", "voice", f"{idx}.wav")
        if not os.path.exists(path):
            print("missing voice line", idx)
            continue
        x, sr = sf.read(path, always_2d=True)
        x = x.mean(1)
        x = resample_poly(x, SR, sr) if sr != SR else x
        x = sosfilt(hp, x)
        low = sosfilt(sos_lp(160, 2), x)
        pres = sosfilt(sos_bp(2500, 5000, 2), x)
        x = x + low * 0.7 + pres * 0.35
        env = np.sqrt(sosfilt(sos_lp(12, 1), x * x) + 1e-9)
        x = x * np.minimum(1.0, (0.12 / np.maximum(env, 1e-4)) ** 0.55)
        x = np.tanh(x / (np.max(np.abs(x)) + 1e-9) * 1.4) / np.tanh(1.4)       # a touch of trailer grit
        st = pan_st(x)
        if idx in (2, 7, 19, 8, 24):
            st = echo(x, 0.38, 0.38, 4)
        vb.add(t0, st, 0.62)
        wet.add(t0, st, 0.14)
        envx = np.convolve(np.abs(x), np.ones(960) / 960, "same")
        on = np.where(envx > 0.02 * np.abs(x).max())[0]
        lens[idx] = (on[-1] / SR + 0.15) if len(on) else len(x) / SR     # where the speech actually ends
    return vb, wet, lens


def main():
    mus, sfx, wet = build()
    vb, vwet, lens = voice_track()
    print("reverb...", flush=True)
    mus_wet = reverb(wet.x, make_ir(4.6, 1.4, 0.5, 0.03).astype(np.float32)).astype(np.float32)
    del wet
    v_wet = reverb(vwet.x, make_ir(2.2, 0.6, 0.25, 0.02, seed=4).astype(np.float32)).astype(np.float32)
    del vwet
    pre = mus.x
    pre += mus_wet * np.float32(0.55)
    pre += sfx.x
    del mus_wet, sfx
    duck = np.ones(N)
    for idx, t0 in T.VOICE:
        if idx not in lens:
            continue
        i0, i1 = int((t0 + 0.3) * SR), int((t0 + lens[idx]) * SR)
        vr_line = np.sqrt(np.mean(vb.x[:, i0:i1] ** 2)) + 1e-9
        # duck in half-second chunks so loud hit tails under a line get pushed down harder
        c = int(0.5 * SR)
        for j0 in range(int((t0 + 0.1) * SR), int((t0 + lens[idx] + 0.3) * SR), c):
            j1 = min(N, j0 + c)
            vr = max(np.sqrt(np.mean(vb.x[:, j0:j1] ** 2)), vr_line * 0.7) + 1e-9
            mr = np.sqrt(np.mean(pre[:, j0:j1] ** 2)) + 1e-9
            g = min(0.85, vr / (mr * 10 ** (7.0 / 20)))
            duck[j0:j1] = np.minimum(duck[j0:j1], g)
    lp = sos_lp(2.5, 1)
    duck = np.minimum(sosfilt(lp, sosfilt(lp, duck)[::-1])[::-1], 1.0).astype(np.float32)
    # never duck a mega-hit
    for ti, sv in T.IMPACTS:
        if sv >= 0.8:
            j0, j1 = int((ti - 0.03) * SR), int((ti + 0.6) * SR)
            ramp = np.clip((np.arange(j1 - j0) / SR - 0.4) / 0.2, 0, 1).astype(np.float32)
            duck[j0:j1] = np.maximum(duck[j0:j1], 1 - ramp * (1 - duck[j0:j1]))
    tg = np.arange(N) / SR
    a, b = T.SILENCE
    gate = np.ones(N, np.float32)
    for g0, g1 in T.PRE_HIT_SILENCE:
        gate *= (1 - (1 - 0.004) * np.clip((tg - g0) / 0.03, 0, 1) * (tg < g1)).astype(np.float32)
    del tg
    music = pre
    music *= duck * gate
    breath = Bus32()
    breath.add(a - 0.05, whoosh(b - a + 0.05, rev=True), 0.12, width=1)
    mix = music + breath.x + vb.x + v_wet * 0.8
    for idx, t0 in T.VOICE:
        if idx not in lens:
            continue
        i0, i1 = int((t0 + 0.4) * SR), int((t0 + min(lens[idx], 2.5)) * SR)
        vr = np.sqrt(np.mean(vb.x[:, i0:i1] ** 2)) + 1e-9
        mr = np.sqrt(np.mean(music[:, i0:i1] ** 2)) + 1e-9
        print(f"voice {idx:2d} @ {t0:6.1f}s  voice-to-score {20 * np.log10(vr / mr):5.1f} dB", flush=True)
    mix = sosfilt(sos_hp(24, 2), mix, axis=1)
    # master: glue saturation + peak limiter, then normalise to -1 dBFS
    mix = np.tanh(mix * 1.15) / 1.15
    envl = np.max(np.abs(mix), 0)
    gain = np.minimum(1.0, 0.9 / np.maximum(sosfilt(sos_lp(8, 1), envl), 1e-6))
    mix *= gain
    fade_out = np.clip((T.DURATION * SR - np.arange(N)) / (2.5 * SR), 0, 1)
    mix *= np.clip(np.arange(N) / (0.05 * SR), 0, 1) * fade_out
    mix = mix[:, :int(T.DURATION * SR)]
    mix /= np.max(np.abs(mix)) + 1e-9
    mix *= 10 ** (-1.0 / 20)
    os.makedirs(os.path.join(HERE, "out2"), exist_ok=True)
    sf.write(os.path.join(HERE, "out2", "soundtrack_raw.wav"), mix.T.astype(np.float32), SR, subtype="FLOAT")
    print("wrote out2/soundtrack_raw.wav", flush=True)


if __name__ == "__main__":
    main()
