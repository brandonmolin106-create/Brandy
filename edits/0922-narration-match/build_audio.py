"""Build the narration, music bed and sound design for "0922 narration-match".

Reads the seven narration WAVs in work/narr, re-times every line (tighter
pauses, deliberate holds on the big moments), puts the per-line voice
effects on, synthesises the score and sound design, and writes:

  out/narration_fx.wav   voice + its effects (the VO track for CapCut)
  out/score_sfx.wav      music + sound design (second audio track)
  out/full_mix.wav       both together, mastered to -14 LUFS
  out/timeline.json      where every line and cue landed (video uses it)
  out/captions.srt       captions for CapCut's "Import captions"
"""
import json
import math
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from pedalboard import (Chorus, Compressor, Gain, HighpassFilter, HighShelfFilter, LowpassFilter,
                        LowShelfFilter, Pedalboard, PeakFilter, PitchShift)
from scipy import ndimage, signal

import edl

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
SR = 48000
rng = np.random.default_rng(922)


def sec(t):
    return int(round(t * SR))


def sos(kind, freq, order=2):
    return signal.butter(order, freq, btype=kind, fs=SR, output="sos")


def fade(x, fin=0.008, fout=0.008):
    x = x.copy()
    a, b = min(sec(fin), len(x) // 2), min(sec(fout), len(x) // 2)
    if a:
        x[..., :a] *= np.linspace(0, 1, a, dtype=np.float32)
    if b:
        x[..., -b:] *= np.linspace(1, 0, b, dtype=np.float32)
    return x


def add(buf, x, start):
    """Mix x into buf at sample `start`, clipping to the buffer."""
    n = x.shape[-1]
    a, b = max(start, 0), min(start + n, buf.shape[-1])
    if b > a:
        buf[..., a:b] += x[..., a - start:b - start]


# ---------------------------------------------------------------- narration

def load_parts():
    parts = {}
    for p in edl.NARRATION_PARTS:
        x, sr = sf.read(ROOT / "work/narr" / f"part{p}.wav", dtype="float32", always_2d=True)
        g = math.gcd(SR, sr)
        parts[p] = signal.resample_poly(x.mean(axis=1), SR // g, sr // g).astype(np.float32)
    return parts


def voiced_edges(x, t0, t1, thresh_db=-45):
    """First and last time (s) in [t0, t1] where the voice is above thresh."""
    seg = x[sec(t0):sec(t1)]
    hop = sec(0.01)
    rms = np.sqrt(np.convolve(seg ** 2, np.ones(hop) / hop, mode="same") + 1e-12)
    loud = np.nonzero(20 * np.log10(rms) > thresh_db)[0]
    if not len(loud):
        return t0, t1
    return t0 + loud[0] / SR, t0 + loud[-1] / SR


def load_chunks(parts):
    raw = {c["id"]: c for c in json.load(open(ROOT / "data/chunks.json"))}
    chunks = {}
    for cid, c in raw.items():
        if cid in edl.SPLITS:
            t = edl.SPLITS[cid]
            x = parts[c["part"]]
            a_vs, a_ve = voiced_edges(x, c["vs"], t)
            b_vs, b_ve = voiced_edges(x, t, c["ve"])
            chunks[f"{cid}a"] = dict(c, e=t, vs=a_vs, ve=a_ve)
            chunks[f"{cid}b"] = dict(c, s=t, vs=b_vs, ve=b_ve)
        else:
            chunks[cid] = c
    used = [cid for line in edl.LINES for cid in line[0]]
    assert len(used) == len(set(used)), "a chunk is used twice"
    expected = {k for k in chunks if (k if isinstance(k, int) else int(k[:-1])) not in edl.DROP}
    missing = expected - set(used)
    assert not missing, f"narration chunks not placed on the timeline: {sorted(map(str, missing))}"
    return chunks


def gap_rule(orig):
    """Pauses inside a line: keep short ones, squeeze the long TTS gaps."""
    return orig if orig <= 0.8 else min(0.8 + 0.4 * (orig - 0.8), 1.5)


def build_timeline(chunks):
    t = edl.PREROLL
    lines, places = [], []
    for li, (cids, text, fx, pause) in enumerate(edl.LINES):
        start = None
        for k, cid in enumerate(cids):
            c = chunks[cid]
            if k:
                t += gap_rule(c["vs"] - chunks[cids[k - 1]]["ve"])
            places.append(dict(line=li, chunk=str(cid), t=t, c=c))
            start = t if start is None else start
            t += c["ve"] - c["vs"]
        lines.append(dict(i=li, start=round(start, 3), end=round(t, 3), text=text, fx=fx))
        t += edl.TAIL if pause is None else pause
    return lines, places, t


# ------------------------------------------------------------ reverb / fx

def make_ir(rt60, length, predelay=0.015, dark=0.5, seed=0):
    r = np.random.default_rng(seed)
    n, pd = sec(length), sec(predelay)
    t = np.arange(n) / SR
    out = np.zeros((2, n + pd), np.float32)
    for ch in range(2):
        noise = r.standard_normal(n)
        lo = signal.sosfilt(sos("lowpass", 500), noise) * np.exp(-6.91 * t / (rt60 * 1.15))
        mid = signal.sosfilt(sos("bandpass", [500, 4000]), noise) * np.exp(-6.91 * t / rt60)
        hi_rt = max(rt60 * (1 - dark) * 0.8, 0.08)
        hi = signal.sosfilt(sos("highpass", 4000), noise) * np.exp(-6.91 * t / hi_rt) * (1 - 0.6 * dark)
        ir = lo + mid + hi
        for k in range(8):  # early reflections
            ir[sec(r.uniform(0.006, 0.07))] += r.uniform(0.4, 1.2) * r.choice([-1, 1]) * ir.std() * 6
        ir[:sec(0.004)] *= np.linspace(0, 1, sec(0.004))
        out[ch, pd:] = ir
    return out / np.sqrt((out ** 2).sum() / 2)


IRS = {
    "room": make_ir(0.7, 1.2, 0.008, 0.4, 1),
    "hall": make_ir(2.4, 3.5, 0.02, 0.55, 2),
    "cath": make_ir(4.6, 6.0, 0.035, 0.7, 3),
    "space": make_ir(8.0, 10.0, 0.05, 0.85, 4),
}


def convolve(bus, ir, n_out):
    """Mono bus -> stereo reverb return, trimmed to n_out samples."""
    return np.stack([signal.oaconvolve(bus, ir[ch])[:n_out] for ch in range(2)]).astype(np.float32)


def echo(x, delay=0.36, fb=0.5, taps=7):
    """Ping-pong echo that darkens with every repeat (stereo, wet only)."""
    d = sec(delay)
    out = np.zeros((2, len(x) + d * taps), np.float32)
    y = x.astype(np.float32)
    for k in range(1, taps + 1):
        y = signal.sosfilt(sos("lowpass", 3800 - 350 * k, 1), y) * fb
        y = signal.sosfilt(sos("highpass", 280, 1), y).astype(np.float32)
        ch = k % 2
        out[ch, k * d:k * d + len(y)] += y
        out[1 - ch, k * d:k * d + len(y)] += 0.3 * y
    return out


def reverse_swell(seg, ir, keep_before=3.0, keep_after=0.2):
    """Reverse reverb: a rise that sucks up into the first word.

    Returns (stereo audio, samples of lead-in before the word)."""
    h = ir.shape[1]
    wet = np.stack([signal.oaconvolve(seg[::-1], ir[ch]) for ch in range(2)])[:, ::-1]
    a, b = max(h - 1 - sec(keep_before), 0), h - 1 + sec(keep_after)
    wet = wet[:, a:b].astype(np.float32)
    wet = fade(wet, fin=keep_before * 0.6, fout=keep_after)
    return wet, (h - 1) - a


BASE = Pedalboard([
    HighpassFilter(cutoff_frequency_hz=80),
    LowShelfFilter(cutoff_frequency_hz=180, gain_db=1.5, q=0.7),
    PeakFilter(cutoff_frequency_hz=380, gain_db=-2.0, q=1.1),
    PeakFilter(cutoff_frequency_hz=3000, gain_db=2.0, q=0.9),
    HighShelfFilter(cutoff_frequency_hz=8000, gain_db=1.5, q=0.7),
    Compressor(threshold_db=-24, ratio=3.0, attack_ms=6, release_ms=140),
])
PROX = Pedalboard([LowShelfFilter(cutoff_frequency_hz=150, gain_db=2.5, q=0.7)])
MEMORY = Pedalboard([
    HighpassFilter(cutoff_frequency_hz=450), LowpassFilter(cutoff_frequency_hz=3200),
    Chorus(rate_hz=0.6, depth=0.18, centre_delay_ms=9, feedback=0.1, mix=0.4), Gain(gain_db=-1.0),
])
GHOST = Pedalboard([PitchShift(semitones=-5), LowpassFilter(cutoff_frequency_hz=2200)])
DOUBLES = [Pedalboard([PitchShift(semitones=s)]) for s in (0.18, -0.18)]


def fx_board(board, x):
    return board(x[None, :], SR)[0].astype(np.float32)


def build_voice(parts, lines, places, n):
    dry = np.zeros(n, np.float32)
    layers = np.zeros((2, n), np.float32)
    buses = {k: np.zeros(n, np.float32) for k in IRS}
    pre, post = 0.25, 0.45
    for ln in lines:
        preset = edl.VOICE_FX[ln["fx"]]
        mine = [p for p in places if p["line"] == ln["i"]]
        t0 = ln["start"] - pre
        buf = np.zeros(sec(ln["end"] - t0 + post), np.float32)
        for p in mine:
            c, x = p["c"], parts[p["c"]["part"]]
            seg = fade(x[sec(c["s"]):sec(c["e"])], 0.01, 0.02)
            add(buf, seg, sec(p["t"] - (c["vs"] - c["s"]) - t0))
        v = fx_board(BASE, buf)
        if preset.get("prox"):
            v = fx_board(PROX, v)
        if preset.get("memory"):
            v = fx_board(MEMORY, v)
        at = sec(t0)
        add(dry, v, at)
        for bus in ("room", "hall", "cath"):
            if preset.get(bus):
                add(buses[bus], v * preset[bus], at)
        voice_len = ln["end"] - ln["start"]
        if preset.get("throw") or preset.get("tail"):
            # the last word: final ~0.7 s of voice
            a = sec(pre + voice_len - min(0.7, voice_len))
            last = fade(v[a:sec(pre + voice_len + 0.15)], 0.06, 0.06)
            if preset.get("throw"):
                e = echo(last) * preset["throw"]
                add(layers, e, at + a)
                add(buses["hall"], e.mean(axis=0) * 0.5, at + a)
            if preset.get("tail"):
                add(buses["space"], last * preset["tail"], at + a)
        if preset.get("swell"):
            first = fade(v[sec(pre):sec(pre + min(1.1, voice_len))], 0.005, 0.05)
            sw, lead = reverse_swell(first, IRS["cath"])
            add(layers, sw * preset["swell"] * 2.2, at + sec(pre) - lead)
        if preset.get("ghost"):
            g = fx_board(GHOST, v) * preset["ghost"]
            add(layers, np.stack([g, g]), at + sec(0.012))
            add(buses["cath"], g * 0.6, at)
        if preset.get("chorus"):
            for k, board in enumerate(DOUBLES):
                d = fx_board(board, v) * 0.38
                pan = np.array([[0.85], [0.35]]) if k == 0 else np.array([[0.35], [0.85]])
                add(layers, pan * d[None, :], at + sec(0.022 + 0.013 * k))
            add(buses["hall"], v * 0.1, at)
    rets = sum(convolve(buses[k], IRS[k], n) for k in IRS)
    return np.stack([dry, dry]) + layers + rets, dry


# ----------------------------------------------------------------- music

CHORDS = {
    "Am": [45, 52, 57, 60, 64], "Fmaj7": [41, 48, 52, 57, 60], "F": [41, 48, 53, 57, 60],
    "C": [48, 55, 60, 64, 67], "G": [43, 50, 55, 59, 62], "Em": [40, 47, 52, 55, 59],
    "Dm": [38, 45, 50, 53, 57], "A": [45, 52, 57, 61, 64], "D": [38, 45, 50, 54, 57],
    "Am_low": [33, 40, 45], "dark": [33, 40, 45, 51, 52],
}


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def saw(f, n, phase0):
    ph = (phase0 + f * np.arange(n) / SR) % 1.0
    return (2 * ph - 1).astype(np.float32)


def pad_segment(notes, intensity, n):
    t = np.arange(n) / SR
    out = np.zeros((2, n), np.float32)
    for j, m in enumerate(notes):
        f = hz(m)
        lfo = 1 + 0.18 * np.sin(2 * np.pi * rng.uniform(0.04, 0.11) * t + rng.uniform(0, 6.28))
        for k, cents in enumerate((-7, 0, 7)):
            v = saw(f * 2 ** (cents / 1200), n, rng.uniform()) * lfo
            pan = (0.2, 0.5, 0.8)[k]
            out[0] += v * (1 - pan)
            out[1] += v * pan
    cutoff = 300 + 1100 * intensity
    out = signal.sosfilt(sos("lowpass", cutoff, 4), out).astype(np.float32)
    # sub: root an octave down
    sub = 0.9 * np.sin(2 * np.pi * hz(min(notes) - 12) * t).astype(np.float32)
    return out / len(notes) + sub[None, :] * 0.5


def pluck(f, dur=2.6, vel=1.0):
    n = sec(dur)
    t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for k in range(1, 9):
        x += (vel / k ** 1.3) * np.sin(2 * np.pi * f * k * (1 + 0.0004 * k * k) * t) * np.exp(-t * (1.1 + 0.9 * k))
    return fade(x, 0.003, 0.2)


def bell(f, dur=4.5):
    n = sec(dur)
    t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for r, a, d in zip((1, 2.0, 2.76, 5.40, 8.93), (1, .55, .4, .22, .1), (3.0, 2.2, 1.6, .9, .5)):
        x += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d)
    return fade(x, 0.002, 0.3)


MUSIC_EQ = Pedalboard([
    PeakFilter(cutoff_frequency_hz=650, gain_db=-4.0, q=0.8),
    PeakFilter(cutoff_frequency_hz=2500, gain_db=-3.0, q=0.8),
])


def build_music(lines, n):
    pad = np.zeros((2, n), np.float32)
    plucks = np.zeros((2, n), np.float32)
    starts = [max(lines[li]["start"] - 1.0, 0) for li, *_ in edl.MUSIC]
    ends = starts[1:] + [n / SR]
    xf = 2.5
    for (li, chord, inten, arp), a, b in zip(edl.MUSIC, starts, ends):
        a0, b0 = max(a - xf / 2, 0), min(b + xf / 2, n / SR)
        seg = pad_segment(CHORDS[chord], inten, sec(b0 - a0)) * inten
        seg = fade(seg, xf if a > 0 else 3.0, xf)
        add(pad, seg, sec(a0))
        if arp:
            tones = sorted(CHORDS[chord])[-4:]
            tones = [m + 12 for m in tones]
            step = 60 / 72 / 2
            for k, tt in enumerate(np.arange(a, b, step)):
                m = tones[(0, 2, 3, 2, 1, 3)[k % 6]]
                p = pluck(hz(m), vel=rng.uniform(0.6, 1.0)) * inten
                pan = 0.5 + 0.25 * (-1) ** k
                add(plucks, np.stack([p * (1 - pan), p * pan]), sec(tt))
    # air: slow-moving filtered noise
    air = signal.sosfilt(sos("bandpass", [900, 5200]), rng.standard_normal((2, n))).astype(np.float32)
    air *= (0.5 + 0.5 * np.sin(2 * np.pi * 0.025 * np.arange(n) / SR))[None, :] * 0.05
    music = pad * 0.8 + plucks * 0.5 + air
    wet = convolve(music.mean(axis=0), IRS["space"], n) * 0.9 + convolve(plucks.mean(axis=0), IRS["hall"], n) * 0.6
    music = music + wet
    # carve room for the voice (her body/formants live around 400 Hz-3 kHz)
    music = MUSIC_EQ(music.astype(np.float32), SR)
    # drop-outs (the held breath before the emotional center)
    gain = np.ones(n, np.float32)
    for a_li, b_li in edl.MUSIC_DROPOUTS:
        a, b = lines[a_li]["end"] + 0.25, lines[b_li]["start"] - 0.1
        fo = sec(0.6)
        gain[sec(a):sec(a) + fo] *= np.linspace(1, 0, fo)
        gain[sec(a) + fo:sec(b)] = 0
        fi = sec(1.5)
        gain[sec(b):sec(b) + fi] *= np.linspace(0, 1, fi)
    # hard stop with the picture
    end = sec(lines[-1]["end"] + 0.25)
    gain[end:] = 0
    return music * gain[None, :]


# ---------------------------------------------------------- sound design

def sfx_impact(big=True):
    n = sec(4.0)
    t = np.arange(n) / SR
    f = 38 + (110 if big else 70) * np.exp(-t / 0.18)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (1.0 if big else 0.7))
    x = sub.astype(np.float32)
    if big:
        burst = signal.sosfilt(sos("lowpass", 900), rng.standard_normal(n)) * np.exp(-t / 0.1) * 0.6
        x += burst.astype(np.float32)
    return fade(x * (1.0 if big else 0.55), 0.002, 0.3)


def sfx_riser(dur=3.0):
    n = sec(dur)
    t = np.arange(n) / SR
    env = (t / dur) ** 3
    noise = signal.sosfilt(sos("highpass", 1800), rng.standard_normal((2, n))) * env * 0.5
    tone = signal.chirp(t, 220, dur, 1400, method="logarithmic") * (t / dur) ** 2 * 0.12
    return fade((noise + tone[None, :]).astype(np.float32), 0.05, 0.01)


def sfx_rumble(dur=3.2):
    n = sec(dur)
    t = np.arange(n) / SR
    x = signal.sosfilt(sos("lowpass", 110, 4), np.cumsum(rng.standard_normal(n)) * 0.02)
    x = x / (np.abs(x).max() + 1e-9) * np.sin(np.pi * t / dur) ** 2
    return x.astype(np.float32) * 0.8


def sfx_step():
    n = sec(0.6)
    t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * (55 + 30 * np.exp(-t / 0.05)) * t) * np.exp(-t / 0.09)
    crunch = signal.sosfilt(sos("bandpass", [250, 1600]), rng.standard_normal(n)) * np.exp(-t / 0.035) * 0.25
    return fade((thump + crunch).astype(np.float32) * 0.6, 0.001, 0.05)


def sfx_whoosh(dur=1.0):
    n = sec(dur)
    t = np.arange(n) / SR
    env = np.sin(np.pi * t / dur) ** 3
    x = signal.sosfilt(sos("bandpass", [400, 3500]), rng.standard_normal(n)) * env * 0.35
    pan = t / dur
    return np.stack([x * (1 - pan), x * pan]).astype(np.float32)


def sfx_heartbeat(beats=4, gap=0.92):
    n = sec(beats * gap + 1)
    x = np.zeros(n, np.float32)
    tt = np.arange(sec(0.5)) / SR
    thump = np.sin(2 * np.pi * 48 * tt) * np.exp(-tt / 0.09)
    for b in range(beats):
        v = 0.8 * (1 - 0.15 * b)
        add(x, (thump * v).astype(np.float32), sec(b * gap))
        add(x, (thump * v * 0.6).astype(np.float32), sec(b * gap + 0.28))
    return x


CHIME_NOTES = iter([88, 85, 81])  # E6, C#6, A5 -- smile, tear, fall


def build_sfx(lines, n):
    dry = np.zeros((2, n), np.float32)
    send = np.zeros(n, np.float32)
    cues = []
    for kind, li, where, off in edl.CUES:
        t = lines[li][where] + off
        cues.append(dict(kind=kind, line=li, t=round(t, 3)))
        if kind == "impact":
            x = sfx_impact(True)
            add(dry, np.stack([x, x]), sec(t))
            add(send, x * 0.5, sec(t))
        elif kind == "softboom":
            x = sfx_impact(False)
            add(dry, np.stack([x, x]), sec(t))
            add(send, x * 0.4, sec(t))
        elif kind == "riser":
            x = sfx_riser()
            add(dry, x * 0.7, sec(t) - x.shape[1])
            add(send, x.mean(axis=0) * 0.5, sec(t) - x.shape[1])
        elif kind == "rumble":
            x = sfx_rumble()
            add(dry, np.stack([x, x]), sec(t - 1.2))
        elif kind == "step":
            x = sfx_step()
            add(dry, np.stack([x, x]), sec(t))
            add(send, x * 0.3, sec(t))
        elif kind == "whoosh":
            x = sfx_whoosh()
            add(dry, x * 0.8, sec(t - 0.5))
        elif kind == "heartbeat":
            x = sfx_heartbeat()
            add(dry, np.stack([x, x]), sec(t))
        elif kind == "chime":
            x = bell(hz(next(CHIME_NOTES))) * 0.35
            add(dry, np.stack([x, x]), sec(t))
            add(send, x * 0.9, sec(t))
        # glow / glitch are picture-only accents (build_video.py)
    return dry + convolve(send, IRS["cath"], n), cues


# ---------------------------------------------------------------- output

def limit(x, ceiling_db=-2.0, lookahead=0.004, release=0.08):
    """Transparent look-ahead peak limiter (gain only moves when a peak
    would cross the ceiling)."""
    c = 10 ** (ceiling_db / 20)
    need = np.minimum(1.0, c / (np.abs(x).max(axis=0) + 1e-12))
    la = sec(lookahead)
    att = 1 - ndimage.minimum_filter1d(need, 2 * la + 1)
    a = np.exp(-1 / (release * SR))
    att = np.maximum(att, signal.lfilter([1 - a], [1, -a], att))
    att = ndimage.uniform_filter1d(att, la)
    att = np.maximum(att, 1 - need)
    return (x * (1 - att)[None, :]).astype(np.float32)


def lufs(x):
    return pyln.Meter(SR).integrated_loudness(x.T.astype(np.float64))


def at_lufs(x, target):
    return x * 10 ** ((target - lufs(x)) / 20)


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def wrap(text, width=42):
    rows, row = [], ""
    for w in text.split():
        if row and len(row) + 1 + len(w) > width:
            rows.append(row)
            row = w
        else:
            row = f"{row} {w}".strip()
    return rows + [row]


def write_srt(lines, path):
    events = []
    for k, ln in enumerate(lines):
        nxt = lines[k + 1]["start"] if k + 1 < len(lines) else ln["end"] + 2.5
        a, b = ln["start"] - 0.05, min(ln["end"] + 0.6, nxt - 0.08)
        rows = wrap(ln["text"])
        blocks = [rows[i:i + 2] for i in range(0, len(rows), 2)]
        total = sum(len(" ".join(bl)) for bl in blocks)
        t = a
        for bl in blocks:
            d = (b - a) * len(" ".join(bl)) / total
            events.append((t, t + d, "\n".join(bl)))
            t += d
    with open(path, "w") as f:
        for i, (a, b, txt) in enumerate(events, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n\n")


def main():
    OUT.mkdir(exist_ok=True)
    parts = load_parts()
    chunks = load_chunks(parts)
    lines, places, total = build_timeline(chunks)
    n = sec(total)
    print(f"timeline {total:.1f}s ({len(lines)} lines)")

    voice, dry = build_voice(parts, lines, places, n)
    music = build_music(lines, n)
    sfx, cues = build_sfx(lines, n)

    voice = at_lufs(voice, -16.0)
    music = at_lufs(music, -27.5)
    # duck the music under the voice (fast-ish attack, slow release)
    env = np.abs(dry)
    env = signal.sosfilt(sos("lowpass", 3, 1), env)
    env = env / (np.percentile(env, 99) + 1e-9)
    duck = 1 - 0.45 * np.clip(env, 0, 1)
    music *= duck[None, :].astype(np.float32)
    sfx *= 10 ** (-6 / 20) / (np.abs(sfx).max() + 1e-9)

    bed = music + sfx
    mix = voice + bed
    g = 10 ** ((-14.0 - lufs(mix)) / 20)
    master, voice_st, bed_st = limit(mix * g), limit(voice * g), limit(bed * g)
    for name, x in (("full_mix", master), ("narration_fx", voice_st), ("score_sfx", bed_st)):
        sf.write(OUT / f"{name}.wav", x.T, SR, subtype="PCM_24")
        print(f"{name}.wav  {lufs(x):.1f} LUFS  peak {20 * np.log10(np.abs(x).max()):.1f} dBFS")

    chunk_starts = {p["chunk"]: round(p["t"], 3) for p in places}
    json.dump(dict(duration=round(total, 3), lines=lines, cues=cues, chunk_starts=chunk_starts),
              open(OUT / "timeline.json", "w"), indent=1)
    write_srt(lines, OUT / "captions.srt")


if __name__ == "__main__":
    main()
