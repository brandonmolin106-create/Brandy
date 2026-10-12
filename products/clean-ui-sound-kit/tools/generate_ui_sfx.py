#!/usr/bin/env python3
"""Clean UI Sound Kit engine — synthesises the whole kit from code. Pure numpy + stdlib.

    python generate_ui_sfx.py --out ../product/wav          # regenerate the shipped set
    python generate_ui_sfx.py --out ./mine --seed 3         # roll your own variations

44.1 kHz, 16-bit mono WAV. Deterministic per seed. Every recipe takes a variation index so one
recipe yields several related sounds (click_01 … click_08).
"""
import argparse
import csv
import math
import os
import wave

import numpy as np

SR = 44100
rng = np.random.default_rng(0)


# ------------------------------------------------------------------ primitives
def t(dur):
    return np.arange(int(SR * dur)) / SR


def env(n, a=0.003, d=0.05, s=0.5, r=0.08, hold=0.0):
    a_n, d_n, r_n, h_n = (int(x * SR) for x in (a, d, r, hold))
    s_n = max(n - a_n - d_n - r_n - h_n, 0)
    e = np.concatenate([
        np.linspace(0, 1, a_n, endpoint=False),
        np.linspace(1, s, d_n, endpoint=False),
        np.full(h_n, s),
        np.full(s_n, s),
        np.linspace(s, 0, r_n),
    ])[:n]
    return np.pad(e, (0, max(n - len(e), 0)))


def osc(freq, dur, kind="sine", glide=0.0, vib=0.0, vib_rate=5.0):
    """glide is semitones across the sound (negative = down). freq may be an array."""
    tt = t(dur)
    n = len(tt)
    f = np.full(n, float(freq)) if np.isscalar(freq) else np.asarray(freq, float)
    if glide:
        f = f * 2 ** (np.linspace(0, glide, n) / 12)
    if vib:
        f = f * 2 ** (vib * np.sin(2 * np.pi * vib_rate * tt) / 12)
    ph = np.cumsum(f) / SR
    if kind == "sine":
        return np.sin(2 * np.pi * ph)
    if kind == "triangle":
        return 2 * np.abs(2 * (ph % 1) - 1) - 1
    if kind == "soft":  # sine with a little 2nd harmonic: warmer than pure sine
        return 0.85 * np.sin(2 * np.pi * ph) + 0.15 * np.sin(4 * np.pi * ph)
    raise ValueError(kind)


def noise(dur, color="white"):
    n = int(SR * dur)
    w = rng.uniform(-1, 1, n)
    if color == "white":
        return w
    out = np.empty(n)
    acc = 0.0
    k = 0.03 if color == "brown" else 0.25
    for i in range(n):
        acc = (1 - k) * acc + k * w[i]
        out[i] = acc
    return out / (np.max(np.abs(out)) + 1e-9)


def lowpass(x, cutoff):
    """cutoff may be a scalar or a per-sample array (for sweeps)."""
    n = len(x)
    c = np.full(n, float(cutoff)) if np.isscalar(cutoff) else np.asarray(cutoff, float)
    alpha = (1 / SR) / (1 / (2 * math.pi * c) + 1 / SR)
    y = np.empty(n)
    acc = 0.0
    for i in range(n):
        acc += alpha[i] * (x[i] - acc)
        y[i] = acc
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def delay(x, time=0.09, fb=0.3, mix=0.22, tail=0.35):
    """Simple feedback delay for a touch of room. Extends the sound by `tail` seconds."""
    n = len(x) + int(SR * tail)
    y = np.zeros(n)
    y[: len(x)] = x
    d = int(SR * time)
    for i in range(d, n):
        y[i] += fb * y[i - d]
    out = np.zeros(n)
    out[: len(x)] = x
    return (1 - mix) * out + mix * y


def note(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def tone(freq, dur, kind="soft", a=0.003, d=0.05, s=0.5, r=0.08, glide=0.0, vib=0.0, vib_rate=5.0, gain=1.0):
    x = osc(freq, dur, kind, glide, vib, vib_rate)
    return gain * x * env(len(x), a, d, s, r)


def seq(parts, gap=0.0):
    out = []
    for p in parts:
        out.append(p)
        if gap:
            out.append(np.zeros(int(SR * gap)))
    return np.concatenate(out)


def finish(x, gain=0.85):
    x = np.asarray(x, float)
    x = x / (np.max(np.abs(x)) + 1e-9) * gain
    fade = min(int(0.003 * SR), len(x) // 4)
    if fade:
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


# ------------------------------------------------------------------ recipes
def r_click(i):
    x = tone(1800 + 150 * i, 0.04, "sine", 0.001, 0.015, 0.2, 0.02, glide=-3)
    x[: int(SR * 0.004)] += 0.4 * noise(0.004)
    return x


def r_tap(i):
    return lowpass(tone(900 + 80 * i, 0.055, "triangle", 0.002, 0.02, 0.3, 0.03, glide=-2), 3200)


def r_hover(i):
    return tone(1200 + 100 * i, 0.06, "sine", 0.004, 0.02, 0.3, 0.03, glide=2, gain=0.6)


def r_toggle_on(i):
    f = 560 + 40 * i
    return seq([tone(f, 0.05, "soft", 0.002, 0.02, 0.4, 0.02), tone(f * 1.5, 0.09, "soft", 0.002, 0.03, 0.4, 0.05)])


def r_toggle_off(i):
    f = 560 + 40 * i
    return seq([tone(f * 1.5, 0.05, "soft", 0.002, 0.02, 0.4, 0.02), tone(f, 0.09, "soft", 0.002, 0.03, 0.4, 0.05)])


def r_switch(i):
    x = seq([r_click(i), tone(380 + 30 * i, 0.07, "triangle", 0.002, 0.03, 0.3, 0.03)])
    return lowpass(x, 4000)


def r_success(i):
    base = 72 + (i % 3) * 2
    notes = [base, base + 4, base + 7] if i < 3 else [base, base + 7, base + 12]
    x = seq([tone(note(n), 0.09, "soft", 0.003, 0.04, 0.5, 0.05) for n in notes])
    x = np.concatenate([x, tone(note(notes[-1]), 0.25, "soft", 0.003, 0.08, 0.4, 0.15, vib=0.15, vib_rate=6)])
    return delay(x, 0.11, 0.3, 0.2)


def r_error(i):
    f = note(64 - i)
    a = tone(f, 0.13, "triangle", 0.003, 0.05, 0.5, 0.05) + 0.4 * tone(f * 1.01, 0.13, "triangle", 0.003, 0.05, 0.5, 0.05)
    b = tone(f * 0.84, 0.2, "triangle", 0.003, 0.06, 0.5, 0.1) + 0.4 * tone(f * 0.85, 0.2, "triangle", 0.003, 0.06, 0.5, 0.1)
    return lowpass(seq([a, b]), 2500)


def r_warning(i):
    f = note(69 + i)
    p = tone(f, 0.11, "triangle", 0.003, 0.04, 0.6, 0.04)
    return lowpass(seq([p, p], gap=0.07), 3000)


def r_notification(i):
    base = 76 + (i % 4)
    iv = [4, 7, 12, 5][i % 4]
    x = seq([tone(note(base), 0.12, "soft", 0.003, 0.05, 0.5, 0.06),
             tone(note(base + iv), 0.3, "soft", 0.003, 0.08, 0.4, 0.2)])
    return delay(x, 0.12, 0.35, 0.25, 0.4)


def r_message_sent(i):
    x = tone(500 + 40 * i, 0.16, "soft", 0.003, 0.05, 0.5, 0.06, glide=12)
    return seq([x, r_pop(i % 6) * 0.6])


def r_message_received(i):
    x = tone(1000 + 50 * i, 0.14, "soft", 0.003, 0.05, 0.5, 0.06, glide=-6)
    return delay(seq([x, tone(note(76 + i), 0.18, "soft", 0.003, 0.06, 0.4, 0.1)]), 0.1, 0.25, 0.18, 0.25)


def r_pop(i):
    return tone(320 + 30 * i, 0.07, "sine", 0.001, 0.03, 0.2, 0.03, glide=-12)


def r_swipe(i):
    d = 0.18 + 0.02 * i
    n = int(SR * d)
    sweep = np.linspace(500, 4000 + 500 * i, n) if i % 2 == 0 else np.linspace(4000, 500, n)
    return lowpass(noise(d), sweep) * env(n, 0.01, 0.05, 0.6, 0.08)


def r_whoosh(i):
    d = 0.35
    n = int(SR * d)
    sweep = np.concatenate([np.linspace(300, 3000, n // 2), np.linspace(3000, 300, n - n // 2)])
    x = highpass(lowpass(noise(d, "brown"), sweep), 150 + 50 * i)
    return x * env(n, 0.05, 0.1, 0.7, 0.15)


def r_lock(i):
    return lowpass(seq([r_tap(i), tone(220 - 15 * i, 0.09, "triangle", 0.002, 0.04, 0.3, 0.04)]), 2500)


def r_unlock(i):
    return lowpass(seq([tone(220 - 15 * i, 0.07, "triangle", 0.002, 0.03, 0.3, 0.03), r_tap(i), tone(880, 0.08, "soft", 0.002, 0.03, 0.3, 0.04)]), 3500)


def r_typing_tick(i):
    x = tone(2500 + 200 * i, 0.018, "sine", 0.001, 0.008, 0.2, 0.008)
    x[: int(SR * 0.003)] += 0.5 * noise(0.003)
    return x


def r_scroll_tick(i):
    return tone(3000 + 250 * i, 0.014, "sine", 0.001, 0.006, 0.2, 0.006, gain=0.7)


def r_delete(i):
    x = tone(800 - 40 * i, 0.22, "triangle", 0.003, 0.06, 0.5, 0.1, glide=-20)
    puff = lowpass(noise(0.08), 1500) * env(int(SR * 0.08), 0.002, 0.03, 0.2, 0.04)
    x[: len(puff)] += 0.5 * puff
    return lowpass(x, 2800)


def r_undo(i):
    return tone(300 + 30 * i, 0.16, "soft", 0.003, 0.05, 0.5, 0.06, glide=12)


def r_achievement(i):
    base = 72 + 2 * i
    x = seq([tone(note(base + k), 0.075, "soft", 0.003, 0.03, 0.6, 0.03) for k in (0, 4, 7, 12)])
    x = np.concatenate([x, tone(note(base + 12), 0.4, "soft", 0.003, 0.1, 0.4, 0.25, vib=0.2, vib_rate=6)])
    return delay(x, 0.12, 0.35, 0.25, 0.45)


def r_level_complete(i):
    base = 67 + 2 * i
    mel = [(0, .1), (4, .1), (7, .1), (12, .18), (7, .08), (12, .4)]
    x = seq([tone(note(base + n), d, "soft", 0.003, 0.04, 0.6, 0.05) for n, d in mel])
    return delay(x, 0.13, 0.3, 0.22, 0.45)


def r_countdown_tick(i):
    return tone(1000 + 100 * i, 0.05, "sine", 0.001, 0.02, 0.3, 0.02)


def r_loading_loop(i):
    d = 1.0
    n = int(SR * d)
    f = note(69 + 5 * i)
    pulses = (np.sin(2 * np.pi * 4 * t(d)) > 0.6).astype(float)
    pulses = lowpass(pulses, 60)
    return osc(f, d, "soft") * pulses * 0.8 + 0.1 * osc(f / 2, d, "sine")


def r_ambient_pad_loop(i):
    d = 2.0
    base = note(48 + 5 * i)
    x = (osc(base, d, "soft") * 0.4 + osc(base * 1.5, d, "sine", vib=0.1, vib_rate=0.5) * 0.3
         + osc(base * 2.0 * 1.003, d, "sine", vib=0.08, vib_rate=0.3) * 0.2 + osc(base * 2.5, d, "sine") * 0.1)
    return lowpass(x, 1200)


CATALOG = [
    ("click", r_click, 8, "Button click, crisp"),
    ("tap", r_tap, 6, "Soft tap"),
    ("hover", r_hover, 4, "Hover / focus, quiet"),
    ("toggle_on", r_toggle_on, 4, "Toggle on (rising)"),
    ("toggle_off", r_toggle_off, 4, "Toggle off (falling)"),
    ("switch", r_switch, 4, "Physical-feel switch"),
    ("success", r_success, 6, "Success / confirm chime"),
    ("error", r_error, 6, "Error, soft two-note"),
    ("warning", r_warning, 4, "Warning double-beep"),
    ("notification", r_notification, 8, "Notification two-note"),
    ("message_sent", r_message_sent, 4, "Message sent swoosh-pop"),
    ("message_received", r_message_received, 4, "Message received"),
    ("pop", r_pop, 6, "Bubble pop"),
    ("swipe", r_swipe, 4, "Swipe / page transition"),
    ("whoosh", r_whoosh, 4, "Whoosh / modal open"),
    ("lock", r_lock, 3, "Lock"),
    ("unlock", r_unlock, 3, "Unlock"),
    ("typing_tick", r_typing_tick, 4, "Keyboard / typing tick"),
    ("scroll_tick", r_scroll_tick, 4, "Scroll / picker tick"),
    ("delete", r_delete, 4, "Delete / trash"),
    ("undo", r_undo, 3, "Undo / restore"),
    ("achievement", r_achievement, 4, "Achievement / reward"),
    ("level_complete", r_level_complete, 3, "Level complete / task done"),
    ("countdown_tick", r_countdown_tick, 3, "Countdown / timer tick"),
    ("loading_loop", r_loading_loop, 3, "Loading pulse (1 s seamless loop)"),
    ("ambient_pad_loop", r_ambient_pad_loop, 3, "Ambient pad (2 s seamless loop)"),
]


def main():
    global rng
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    os.makedirs(args.out, exist_ok=True)
    rows, total = [], 0
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
