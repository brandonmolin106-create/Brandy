#!/usr/bin/env python3
"""Echoes 8-Bit SFX engine — procedurally synthesises the whole pack.

    python generate_sfx.py --out ../product/wav            # regenerate the shipped set
    python generate_sfx.py --out ./mine --seed 42          # roll your own variations

Pure numpy + stdlib. 44.1 kHz, 16-bit mono WAV. Every sound is deterministic for a
given seed, so the shipped pack is reproducible and your custom rolls are repeatable.
"""
import argparse
import csv
import math
import os
import wave

import numpy as np

SR = 44100
rng = np.random.default_rng(0)

# ---------------------------------------------------------------- primitives

def t(dur):
    return np.arange(int(SR * dur)) / SR


def env(n, a=0.005, d=0.05, s=0.6, r=0.1, hold=0.0):
    """ADSR as a sample array of length n."""
    a_n, d_n, r_n, h_n = (int(x * SR) for x in (a, d, r, hold))
    s_n = max(n - a_n - d_n - r_n - h_n, 0)
    parts = [
        np.linspace(0, 1, a_n, endpoint=False),
        np.linspace(1, s, d_n, endpoint=False),
        np.full(h_n, s),
        np.full(s_n, s),
        np.linspace(s, 0, r_n),
    ]
    e = np.concatenate(parts)[:n]
    if len(e) < n:
        e = np.pad(e, (0, n - len(e)))
    return e


def osc(freq, dur, kind="square", duty=0.5, sweep=0.0, vib=0.0, vib_rate=6.0):
    """freq may be a scalar or an array (per-sample Hz). sweep = semitones over dur."""
    tt = t(dur)
    n = len(tt)
    f = np.full(n, float(freq)) if np.isscalar(freq) else np.asarray(freq, dtype=float)
    if sweep:
        f = f * 2 ** (np.linspace(0, sweep, n) / 12)
    if vib:
        f = f * 2 ** (vib * np.sin(2 * np.pi * vib_rate * tt) / 12)
    phase = np.cumsum(f) / SR
    ph = phase % 1.0
    if kind == "square":
        return np.where(ph < duty, 1.0, -1.0)
    if kind == "triangle":
        return 2 * np.abs(2 * ph - 1) - 1
    if kind == "saw":
        return 2 * ph - 1
    if kind == "sine":
        return np.sin(2 * np.pi * phase)
    raise ValueError(kind)


def noise(dur, color="white"):
    n = int(SR * dur)
    w = rng.uniform(-1, 1, n)
    if color == "white":
        return w
    # brown-ish: leaky integrator
    out = np.empty(n)
    acc = 0.0
    k = 0.02 if color == "brown" else 0.2
    for i in range(n):
        acc = (1 - k) * acc + k * w[i]
        out[i] = acc
    return out / (np.max(np.abs(out)) + 1e-9)


def lowpass(x, cutoff):
    rc = 1 / (2 * math.pi * cutoff)
    dt = 1 / SR
    alpha = dt / (rc + dt)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alpha * (v - acc)
        y[i] = acc
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def crush(x, bits=6, rate_div=1):
    q = 2 ** (bits - 1)
    y = np.round(x * q) / q
    if rate_div > 1:
        y = np.repeat(y[::rate_div], rate_div)[: len(x)]
    return y


def arp(notes, step, kind="square", duty=0.5, repeats=1):
    seq = []
    for _ in range(repeats):
        for nfreq in notes:
            seq.append(osc(nfreq, step, kind, duty) * env(int(SR * step), 0.002, 0.02, 0.8, 0.02))
    return np.concatenate(seq)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def finish(x, gain=0.9):
    x = np.asarray(x, dtype=float)
    peak = np.max(np.abs(x)) + 1e-9
    x = x / peak * gain
    fade = min(int(0.004 * SR), len(x) // 4)
    if fade > 0:
        x[:fade] *= np.linspace(0, 1, fade)
        x[-fade:] *= np.linspace(1, 0, fade)
    return x


def write_wav(path, x):
    data = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


# ---------------------------------------------------------------- recipes
# Each recipe takes a variation index i and returns a float array.

def r_jump(i):
    base = 220 + 40 * i
    d = 0.18 + 0.02 * (i % 3)
    x = osc(base, d, "square", 0.5 - 0.05 * (i % 3), sweep=14 + i) * env(int(SR * d), 0.002, 0.05, 0.5, 0.08)
    return crush(x, 6)


def r_land(i):
    d = 0.12
    x = noise(d, "brown") * env(int(SR * d), 0.001, 0.03, 0.3, 0.06)
    x += 0.6 * osc(90 - 10 * i, d, "triangle", sweep=-12) * env(int(SR * d), 0.001, 0.04, 0.2, 0.05)
    return lowpass(x, 900 + 150 * i)


def r_coin(i):
    n0 = 76 + (i % 4) * 2
    x = np.concatenate([
        osc(midi(n0), 0.07, "square", 0.5) * env(int(SR * 0.07), 0.001, 0.02, 0.9, 0.01),
        osc(midi(n0 + 5 + (i // 4) * 2), 0.22, "square", 0.5) * env(int(SR * 0.22), 0.001, 0.05, 0.6, 0.12),
    ])
    return crush(x, 7)


def r_gem(i):
    notes = [midi(n) for n in (72 + i, 76 + i, 79 + i, 84 + i)]
    x = arp(notes, 0.045, "triangle")
    tail = osc(midi(84 + i), 0.25, "triangle", vib=0.3, vib_rate=9) * env(int(SR * 0.25), 0.001, 0.05, 0.5, 0.15)
    return np.concatenate([x, tail])


def r_powerup(i):
    d = 0.5 + 0.05 * i
    x = osc(200 + 30 * i, d, "square", 0.25, sweep=24, vib=0.6, vib_rate=14 + i) * env(int(SR * d), 0.005, 0.1, 0.8, 0.15)
    steps = arp([midi(60 + i + k) for k in (0, 4, 7, 12, 16, 19)], 0.06, "square", 0.5)
    return np.concatenate([steps, crush(x, 6)])


def r_hit(i):
    d = 0.16
    x = noise(d, "white") * env(int(SR * d), 0.001, 0.02, 0.2, 0.08)
    x += 0.8 * osc(160 + 20 * i, d, "square", 0.5, sweep=-20) * env(int(SR * d), 0.001, 0.05, 0.3, 0.06)
    return crush(lowpass(x, 2500 + 300 * i), 5)


def r_hurt(i):
    d = 0.3
    x = osc(330 - 20 * i, d, "saw", sweep=-10, vib=1.5, vib_rate=25) * env(int(SR * d), 0.002, 0.08, 0.5, 0.12)
    return crush(x, 5, 2)


def r_death(i):
    d = 0.9
    x = osc(440 - 40 * i, d, "square", 0.5, sweep=-30, vib=1.0, vib_rate=8) * env(int(SR * d), 0.002, 0.2, 0.6, 0.3)
    x += 0.3 * noise(d, "brown") * env(int(SR * d), 0.2, 0.2, 0.5, 0.3)
    return crush(x, 5, 3)


def r_explosion(i):
    d = 0.7 + 0.1 * (i % 3)
    n = int(SR * d)
    x = noise(d, "brown") * env(n, 0.002, 0.15, 0.4, 0.4)
    x += 0.5 * noise(d, "white") * env(n, 0.001, 0.05, 0.1, 0.2)
    x += 0.7 * osc(60 + 10 * i, d, "sine", sweep=-18) * env(n, 0.001, 0.1, 0.3, 0.3)
    return crush(lowpass(x, 1800 + 200 * i), 6)


def r_laser(i):
    d = 0.22
    x = osc(1200 + 150 * i, d, "square", 0.3 + 0.05 * (i % 3), sweep=-28) * env(int(SR * d), 0.001, 0.04, 0.5, 0.08)
    return crush(x, 6)


def r_shoot(i):
    d = 0.12
    x = osc(600 + 80 * i, d, "saw", sweep=-16) * env(int(SR * d), 0.001, 0.03, 0.3, 0.05)
    x += 0.5 * noise(d, "white") * env(int(SR * d), 0.001, 0.02, 0.1, 0.04)
    return crush(highpass(x, 300), 6)


def r_ui_click(i):
    d = 0.05
    x = osc(900 + 120 * i, d, "square", 0.5) * env(int(SR * d), 0.001, 0.01, 0.4, 0.03)
    return x


def r_ui_confirm(i):
    notes = [midi(72 + i * 2), midi(79 + i * 2)]
    return arp(notes, 0.07, "square", 0.5)


def r_ui_cancel(i):
    notes = [midi(72 - i), midi(65 - i)]
    return arp(notes, 0.08, "square", 0.25)


def r_ui_error(i):
    d = 0.25
    x = osc(140 + 10 * i, d, "square", 0.5, vib=0.8, vib_rate=30) * env(int(SR * d), 0.001, 0.05, 0.7, 0.08)
    return crush(x, 5)


def r_menu_move(i):
    d = 0.06
    return osc(500 + 100 * i, d, "triangle", sweep=4) * env(int(SR * d), 0.001, 0.02, 0.5, 0.03)


def r_level_up(i):
    base = 60 + 2 * i
    notes = [midi(base + k) for k in (0, 4, 7, 12, 7, 12, 16, 19, 24)]
    x = arp(notes, 0.08, "square", 0.5)
    tail = osc(midi(base + 24), 0.5, "square", 0.5, vib=0.4, vib_rate=7) * env(int(SR * 0.5), 0.001, 0.1, 0.6, 0.3)
    return np.concatenate([x, tail])


def r_win(i):
    base = 60 + 3 * i
    seq = [(0, .1), (4, .1), (7, .1), (12, .2), (7, .1), (12, .4)]
    x = np.concatenate([osc(midi(base + n), d, "square", 0.5) * env(int(SR * d), 0.002, 0.04, 0.8, 0.05) for n, d in seq])
    return x


def r_lose(i):
    base = 64 - 2 * i
    seq = [(0, .18), (-1, .18), (-2, .18), (-4, .5)]
    x = np.concatenate([osc(midi(base + n), d, "square", 0.5, vib=0.3, vib_rate=5) * env(int(SR * d), 0.002, 0.06, 0.7, 0.08) for n, d in seq])
    return crush(x, 6)


def r_door(i):
    d = 0.35
    n = int(SR * d)
    x = noise(d, "brown") * env(n, 0.01, 0.1, 0.5, 0.2)
    x = lowpass(x, 600 + 100 * i)
    x += 0.4 * osc(80 + 15 * i, d, "triangle", sweep=6) * env(n, 0.01, 0.1, 0.6, 0.2)
    return x


def r_teleport(i):
    d = 0.6
    n = int(SR * d)
    x = osc(300, d, "sine", sweep=30 if i % 2 == 0 else -30, vib=2, vib_rate=20 + 5 * i) * env(n, 0.01, 0.1, 0.7, 0.25)
    x += 0.4 * osc(450, d, "triangle", sweep=36 if i % 2 == 0 else -36) * env(n, 0.01, 0.1, 0.5, 0.25)
    return crush(x, 6)


def r_footstep(i):
    d = 0.09
    n = int(SR * d)
    x = noise(d, "brown") * env(n, 0.001, 0.02, 0.2, 0.05)
    x += 0.3 * osc(120 + 25 * i, d, "sine", sweep=-8) * env(n, 0.001, 0.02, 0.2, 0.04)
    return lowpass(x, 700 + 150 * i)


def r_splash(i):
    d = 0.4
    n = int(SR * d)
    x = noise(d, "white") * env(n, 0.002, 0.08, 0.3, 0.25)
    x = lowpass(x, 1200 + 300 * i)
    x += 0.4 * osc(220 - 20 * i, d, "sine", sweep=-14) * env(n, 0.002, 0.05, 0.2, 0.2)
    return x


def r_alarm(i):
    d = 0.8
    n = int(SR * d)
    f = 600 + 100 * i + 200 * (np.sin(2 * np.pi * (3 + i) * t(d)) > 0)
    return osc(f, d, "square", 0.5) * env(n, 0.005, 0.05, 0.8, 0.1)


def r_heartbeat(i):
    beat = osc(55 + 5 * i, 0.12, "sine", sweep=-6) * env(int(SR * 0.12), 0.002, 0.04, 0.4, 0.06)
    gap1 = np.zeros(int(SR * 0.12))
    gap2 = np.zeros(int(SR * 0.45))
    return np.concatenate([beat, gap1, 0.7 * beat, gap2])


def r_engine_loop(i):
    d = 1.0
    n = int(SR * d)
    f = 70 + 15 * i
    x = osc(f, d, "saw") * 0.6 + osc(f * 1.01, d, "square", 0.3) * 0.4
    x = lowpass(x, 400 + 80 * i)
    x += 0.15 * lowpass(noise(d, "white"), 800)
    return x * env(n, 0.0, 0.0, 1.0, 0.0)


def r_drone_loop(i):
    d = 2.0
    n = int(SR * d)
    base = midi(36 + 5 * i)
    x = osc(base, d, "triangle") * 0.5 + osc(base * 1.5, d, "sine", vib=0.2, vib_rate=0.5) * 0.3 + osc(base * 2.0, d, "triangle", vib=0.15, vib_rate=0.3) * 0.2
    return lowpass(x, 900) * env(n, 0.0, 0.0, 1.0, 0.0)


CATALOG = [
    ("jump", r_jump, 8, "Player jump, rising blip"),
    ("land", r_land, 4, "Landing thud"),
    ("coin", r_coin, 8, "Coin / pickup two-note chime"),
    ("gem", r_gem, 6, "Gem / rare pickup sparkle"),
    ("powerup", r_powerup, 6, "Power-up rising arpeggio"),
    ("hit", r_hit, 8, "Melee hit / impact"),
    ("hurt", r_hurt, 6, "Player hurt buzz"),
    ("death", r_death, 4, "Player death descending"),
    ("explosion", r_explosion, 8, "Explosion boom"),
    ("laser", r_laser, 8, "Laser zap"),
    ("shoot", r_shoot, 6, "Short gunshot / pew"),
    ("ui_click", r_ui_click, 6, "UI click"),
    ("ui_confirm", r_ui_confirm, 4, "UI confirm / accept"),
    ("ui_cancel", r_ui_cancel, 4, "UI cancel / back"),
    ("ui_error", r_ui_error, 4, "UI error buzz"),
    ("menu_move", r_menu_move, 4, "Menu cursor move"),
    ("level_up", r_level_up, 4, "Level-up fanfare"),
    ("win", r_win, 3, "Win jingle"),
    ("lose", r_lose, 3, "Lose jingle"),
    ("door", r_door, 4, "Door open / close"),
    ("teleport", r_teleport, 4, "Teleport / warp"),
    ("footstep", r_footstep, 8, "Footstep"),
    ("splash", r_splash, 4, "Water splash"),
    ("alarm", r_alarm, 3, "Alarm / siren"),
    ("heartbeat", r_heartbeat, 2, "Heartbeat (loopable)"),
    ("engine_loop", r_engine_loop, 3, "Engine hum (1s seamless loop)"),
    ("drone_loop", r_drone_loop, 4, "Ambient drone (2s seamless loop)"),
]


def main():
    global rng
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    os.makedirs(args.out, exist_ok=True)

    rows = []
    total = 0
    for name, fn, count, desc in CATALOG:
        for i in range(count):
            x = finish(fn(i))
            fname = f"{name}_{i + 1:02d}.wav"
            write_wav(os.path.join(args.out, fname), x)
            rows.append((fname, name, desc, f"{len(x) / SR:.3f}"))
            total += 1
    with open(os.path.join(args.out, "index.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "category", "description", "seconds"])
        w.writerows(rows)
    print(f"wrote {total} sounds to {args.out}")


if __name__ == "__main__":
    main()
