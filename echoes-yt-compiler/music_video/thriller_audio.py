#!/usr/bin/env python3
"""Thriller cut, audio side: dramatic voice FX, a synthesised SFX layer and a score muffled by the drop.

    WORK=<work dir> FFMPEG=<ffmpeg> python3 music_video/thriller_audio.py

Reads $WORK/mv/timeline.json, mv/lines/*.wav and mv/score.wav (from timeline.py / score.py).
Writes mv/thriller_voice.wav, mv/thriller_score.wav, mv/thriller_sfx.wav and mv/thriller_cues.json
(the hit / glitch / flash times the visuals sync to). Every sound is generated here, nothing sampled.
"""
import json, os, subprocess, sys, wave
import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

WORK = os.path.abspath(os.environ.get('WORK', '.'))
FF = os.environ.get('FFMPEG', 'ffmpeg')
MV = os.path.join(WORK, 'mv')
SR = 48000
rng = np.random.default_rng(1313)


# ---------------------------------------------------------------- io / dsp helpers
def read(path):
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32768
        return x.reshape(-1, w.getnchannels())


def write(path, x):
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


def filt(x, kind, f, order=2):
    return sosfilt(butter(order, f, kind, fs=SR, output='sos'), x, axis=0)


def st(x, width=0.0):
    """Mono -> stereo, optionally decorrelated by a few ms."""
    if x.ndim == 2:
        return x
    if not width:
        return np.stack([x, x], 1)
    d = int(width * SR)
    return np.stack([x, np.concatenate([np.zeros(d), x[:-d]])], 1)


def ir(seconds, lo=150, hi=7000, seed=0):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    x = r.standard_normal((n, 2)) * np.exp(-t / (seconds / 6.5))[:, None]
    x = filt(x, 'band', [lo, hi])
    return x / np.sqrt((x ** 2).sum(0))


def verb(x, seconds=2.5, wet=0.4, **kw):
    x = st(x)
    return x * (1 - wet) + fftconvolve(x, ir(seconds, **kw), axes=0)[:len(x)] * wet


def pad_to(x, seconds):
    n = int(seconds * SR)
    return np.concatenate([x, np.zeros((n - len(x), x.shape[1]))]) if len(x) < n else x


def norm(x, peak):
    m = np.abs(x).max()
    return x * (peak / m) if m else x


def fade(x, a=0.004, b=0.01):
    n = len(x)
    e = np.ones(n)
    na, nb = int(a * SR), int(b * SR)
    e[:na] = np.linspace(0, 1, na)
    e[n - nb:] = np.linspace(1, 0, nb)
    return x * (e[:, None] if x.ndim == 2 else e)


# ---------------------------------------------------------------- sound effects
def hit(size=1.0):
    """Trailer hit: dropping sub, inharmonic metal, a crack, and a long dark tail."""
    n = int(4.5 * SR)
    t = np.arange(n) / SR
    f = 31 + 52 * np.exp(-t * 7)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.0)
    metal = sum(a * np.sin(2 * np.pi * fr * t + rng.uniform(0, 6.3)) * np.exp(-t * dk)
                for fr, dk, a in [(181, 4, .5), (347, 6, .42), (612, 8, .3), (1133, 11, .22), (2271, 16, .14), (3517, 24, .09)])
    crack = filt(rng.standard_normal(n) * np.exp(-t * 40), 'high', 1400)
    x = st(sub, 0) + st(0.33 * metal, 0.004) + st(0.45 * crack, 0.002)
    x = x * 0.75 + fftconvolve(x, ir(3.8, 80, 5000, 7), axes=0)[:n] * 0.55
    return norm(fade(x, 0.001, 0.2), 0.95 * size)


def reverse_swell(dur=1.8, bright=1.0):
    """A reversed reverb tail that sucks up into the next hit."""
    n = int(dur * SR)
    burst = filt(rng.standard_normal(int(0.25 * SR)) * np.exp(-np.arange(int(0.25 * SR)) / SR * 18), 'band', [200, 6000 * bright])
    tail = fftconvolve(st(burst), ir(dur, 150, 8000, 3), axes=0)[:n]
    x = tail[::-1] * np.linspace(0, 1, n)[:, None] ** 2
    return norm(fade(x, 0.02, 0.003), 0.6)


def shepard(dur, cycle=11.0, voices=8, fmin=28.0):
    """Shepard-Risset glissando: a tone that seems to rise forever, swelling in."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(voices):
        p = (k / voices + t / cycle) % 1.0
        f = fmin * 2 ** (p * voices)
        amp = 0.5 - 0.5 * np.cos(2 * np.pi * p)
        out += amp * np.sin(2 * np.pi * np.cumsum(f) / SR + k)
    out *= np.linspace(0.05, 1, n) ** 1.6
    return norm(fade(st(out, 0.006), 0.3, 0.01), 0.45)


def heartbeat(t0, t1, bpm0, bpm1, level=0.8):
    """Beats whose tempo slides from bpm0 to bpm1; returns (start_sample, audio) pieces."""
    pieces, t = [], t0
    lub_n = int(0.35 * SR)
    tt = np.arange(lub_n) / SR
    lub = np.sin(2 * np.pi * np.cumsum(58 - 18 * tt / 0.35) / SR) * np.exp(-tt * 16)
    dub = np.sin(2 * np.pi * np.cumsum(66 - 16 * tt / 0.35) / SR) * np.exp(-tt * 20) * 0.6
    while t < t1:
        frac = (t - t0) / max(1e-6, t1 - t0)
        bpm = bpm0 + (bpm1 - bpm0) * frac
        gap = min(0.22, 60 / bpm * 0.3)
        beat = np.zeros(lub_n + int(gap * SR))
        beat[:lub_n] += lub
        beat[int(gap * SR):int(gap * SR) + lub_n] += dub
        pieces.append((t, st(filt(beat, 'low', 180) * level)))
        t += 60 / bpm
    return pieces


def breath(kind='in', dur=None):
    dur = dur or (0.85 if kind == 'in' else 1.3)
    n = int(dur * SR)
    t = np.arange(n) / SR
    band = [850, 2800] if kind == 'in' else [450, 1900]
    x = filt(rng.standard_normal(n), 'band', band, 3)
    e = (t / dur) ** 1.8 * (1 - np.clip((t - dur * 0.9) / (dur * 0.1), 0, 1)) if kind == 'in' \
        else np.clip(t / 0.08, 0, 1) * (1 - t / dur) ** 1.4
    return norm(fade(st(x * e, 0.0008), 0.01, 0.02), 0.35)


def glass_shatter():
    n = int(2.2 * SR)
    t = np.arange(n) / SR
    x = np.zeros((n, 2))
    x += st(filt(rng.standard_normal(n) * np.exp(-t * 55), 'high', 2500) * 0.8)
    x += st(np.sin(2 * np.pi * 95 * t) * np.exp(-t * 14) * 0.6)
    for _ in range(70):                                         # shards: bright pings, dense then scattering
        s = int(min(1.6, rng.exponential(0.25)) * SR)
        f = rng.uniform(2300, 9500)
        m = int(rng.uniform(0.03, 0.28) * SR)
        tt = np.arange(m) / SR
        ping = np.sin(2 * np.pi * f * tt) * np.exp(-tt / rng.uniform(0.01, 0.07)) * rng.uniform(0.1, 0.4)
        pan = rng.uniform(0, 1)
        e = min(n, s + m)
        x[s:e, 0] += ping[:e - s] * (1 - pan)
        x[s:e, 1] += ping[:e - s] * pan
    x += st(filt(rng.standard_normal(n) * np.exp(-t * 6), 'high', 4000) * 0.12, 0.003)
    return norm(verb(x, 1.6, 0.3, lo=600, hi=12000, seed=5), 0.75)


def dirt():
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    grit = filt(rng.standard_normal(n), 'band', [160, 1700], 3)
    grains = np.repeat(rng.uniform(0.2, 1.0, n // 240 + 1), 240)[:n]
    e = np.clip(t / 0.03, 0, 1) * np.exp(-t * 7)
    thud = np.sin(2 * np.pi * np.cumsum(90 - 40 * t) / SR) * np.exp(-t * 18)
    return norm(fade(st(grit * grains * e + thud * 0.7, 0.002), 0.002, 0.03), 0.6)


def chains(dur=1.5):
    n = int((dur + 0.4) * SR)
    x = np.zeros((n, 2))
    k = int(dur * 34)
    times = np.sort(np.concatenate([rng.uniform(0, dur, k // 2), rng.normal(dur * 0.25, 0.12, k - k // 2).clip(0, dur)]))
    for s0 in times:
        f = rng.uniform(900, 2600)
        m = int(rng.uniform(0.04, 0.14) * SR)
        tt = np.arange(m) / SR
        clink = sum(a * np.sin(2 * np.pi * f * r * tt) for r, a in [(1, 1), (2.76, .5), (5.4, .25)]) * np.exp(-tt * rng.uniform(30, 70))
        pan = rng.uniform(0.2, 0.8)
        s = int(s0 * SR)
        e = min(n, s + m)
        x[s:e, 0] += clink[:e - s] * (1 - pan) * rng.uniform(0.3, 1)
        x[s:e, 1] += clink[:e - s] * pan * rng.uniform(0.3, 1)
    return norm(verb(x, 1.3, 0.25, lo=400, hi=9000, seed=9), 0.55)


def tinnitus(dur=3.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * 4700 * t) + 0.5 * np.sin(2 * np.pi * 4723 * t)) * np.exp(-t * 1.1)
    return fade(st(x * 0.06), 0.005, 0.2)


def bowed_metal(dur=3.0, f0=460):
    """Eerie bowed-cymbal drone: jittery inharmonic partials with a slow swell."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    jit = filt(rng.standard_normal(n), 'low', 6) * 40
    x = sum(a * np.sin(2 * np.pi * np.cumsum(f0 * r * (1 + 0.002 * jit)) / SR)
            for r, a in [(1, 1), (2.31, .6), (3.73, .4), (5.12, .25)])
    x *= np.sin(np.pi * t / dur) ** 1.5 * (0.7 + 0.3 * filt(rng.standard_normal(n), 'low', 3) * 8).clip(0, 1.4)
    return norm(verb(st(x, 0.005), 2.5, 0.45, seed=11), 0.22)


def thunder(dur=6.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    brown = filt(np.cumsum(rng.standard_normal(n)), 'high', 20)
    brown = filt(brown / np.abs(brown).max(), 'low', 190, 3)
    e = sum(rng.uniform(0.4, 1) * np.exp(-((t - c) / w) ** 2) for c, w in
            [(rng.uniform(0.3, 1.2), 0.5), (rng.uniform(1.4, 2.6), 0.9), (rng.uniform(2.8, 4.5), 1.3)])
    return norm(fade(st(brown * e, 0.01), 0.3, 0.8), 0.5)


def glitch(dur=0.16):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sq = np.sign(np.sin(2 * np.pi * rng.uniform(70, 320) * t))
    gate = np.repeat(rng.integers(0, 2, n // 700 + 1), 700)[:n]
    crush = np.round(rng.standard_normal(n) * 3) / 3
    return fade(st((sq * 0.5 + crush * 0.3) * gate * 0.35, 0.001), 0.002, 0.004)


def clunk():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 150 * t) * np.exp(-t * 30) + filt(rng.standard_normal(n) * np.exp(-t * 90), 'band', [900, 4000]) * 0.5
    return norm(verb(st(x), 0.9, 0.3, seed=2), 0.6)


# ---------------------------------------------------------------- voice FX
def pitch_down(x, semis=-5):
    """Duration-preserving pitch shift through ffmpeg (asetrate + atempo)."""
    ratio = 2 ** (semis / 12)
    src, dst = os.path.join(MV, '_ps_in.wav'), os.path.join(MV, '_ps_out.wav')
    write(src, x)
    subprocess.run([FF, '-y', '-loglevel', 'error', '-i', src, '-af',
                    f'asetrate={int(SR * ratio)},aresample={SR},atempo={1 / ratio:.5f}', dst], check=True)
    y = read(dst)
    return pad_to(y, len(x) / SR)[:len(x)]


def main():
    tl = json.load(open(os.path.join(MV, 'timeline.json')))
    total, beat, drop = tl['total'], 60 / tl['bpm'], tl['drop']
    secs = {s['name']: s for s in tl['sections']}
    lines = tl['lines']
    n = int(total * SR)
    voice = np.zeros((n, 2))
    sfx = np.zeros((n, 2))
    cues = dict(hits=[], glitches=[], flashes=[], red=[drop], shatter=None)

    def put(buf, t, x, gain=1.0):
        s = int(round(t * SR))
        if s >= n:
            return
        if s < 0:
            x, s = x[-s:], 0
        e = min(n, s + len(x))
        buf[s:e] += x[:e - s] * gain

    def line_with(fragment):
        return next(i for i, l in enumerate(lines) if fragment.lower() in l['text'].lower())

    def word_time(li, text, end=False):
        li = line_with(li) if isinstance(li, str) else li
        for w in lines[li]['words']:
            if w['text'].upper().strip('.,!?') == text:
                return w['end'] if end else w['start']
        return None

    # --- voice: dry lines, reverse-reverb pre-verbs into each section, a low double on the darkest lines
    first_of_section = {}
    for i, l in enumerate(lines):
        first_of_section.setdefault(l['section'], i)
    demon = {line_with(f) for f in ('watching you disappear', 'thoughts kept digging', 'will become your name')}
    dark_ir = ir(3.4, 120, 5000, 21)
    for i, l in enumerate(lines):
        x = read(os.path.join(MV, 'lines', f'{i:02d}.wav'))
        put(voice, l['start'], x)
        if first_of_section.get(l['section']) == i and l['section'] != 'chains':
            head = x[:int(0.6 * SR)]
            wet = fftconvolve(head, dark_ir, axes=0)[::-1]
            put(voice, l['start'] - len(wet) / SR + 0.05, norm(wet, 0.25))
        if i in demon:
            put(voice, l['start'], filt(pitch_down(x, -5), 'low', 2600), 0.33)
        if l.get('throw'):                                       # echo the last word, darker, on the beat grid
            w = l['words'][-1]
            a = int((w['start'] - l['start']) * SR)
            word = x[a:] * np.linspace(1, 0.5, len(x) - a)[:, None]
            for r in range(1, 5):
                put(voice, w['start'] + r * beat / 2, filt(word, 'band', [250, 3000]), 0.45 ** r)
    voice = voice + fftconvolve(voice, dark_ir, axes=0)[:n] * 0.17

    # --- sound design
    def hit_at(t, size=1.0, swell=True, flash=True):
        if swell:
            put(sfx, t - 1.8, reverse_swell(1.8), 0.8 * size)
        put(sfx, t, hit(size))
        cues['hits'].append(round(t, 3))
        if flash:
            cues['flashes'].append(round(t, 3))

    put(sfx, 0.6, thunder(7.0), 0.9)
    put(sfx, 5.5, bowed_metal(6.0, 440), 1.0)
    hit_at(3.0, 0.55, swell=False)
    put(sfx, 15.9, breath('in'), 0.9)
    hit_at(secs['time']['start'], 0.8)
    t = word_time('watching you disappear', 'DISAPPEAR')
    if t:
        put(sfx, t, glitch(0.22), 0.9)
        cues['glitches'].append([round(t, 3), 0.25])
    t = word_time('taking the next second', 'SECOND')
    if t:
        for k in range(3):
            put(sfx, t + k * 0.09, glitch(0.06), 0.7)
        cues['glitches'].append([round(t, 3), 0.3])
    for name in ('hole', 'glass', 'road', 'everything'):
        hit_at(secs[name]['start'], 0.75 if name != 'everything' else 0.5)
    for li, word in (('hand of dirt', 'DIRT'), ('kept digging', 'DIGGING')):
        t = word_time(li, word)
        if t:
            put(sfx, t, dirt(), 0.8)
            put(sfx, t + beat / 2, dirt(), 0.5)
            put(sfx, t + beat, dirt(), 0.3)
    t = word_time('stopped looking up', 'UP')
    if t:
        put(sfx, t - 0.2, reverse_swell(1.2, bright=1.5), 0.35)
    t = word_time('in a glass box', 'BOX')
    if t:
        put(sfx, t + 0.05, glass_shatter(), 0.95)
        cues['shatter'] = round(t + 0.05, 3)
        cues['flashes'].append(round(t + 0.05, 3))
        cues['glitches'].append([round(t + 0.05, 3), 0.2])
    t = word_time('not who you are', 'ARE', end=True)
    if t:
        put(sfx, t + 0.1, bowed_metal(3.5, 380), 1.0)
    # the riser: a Shepard tone climbing forever + a heartbeat racing, then silence, an inhale, the drop
    r0, r1 = secs['road']['end'] - 2 * tl['bar'], secs['riser']['end']
    put(sfx, r0, shepard(r1 - r0 - 0.35), 1.0)
    for s0, beatx in heartbeat(secs['riser']['start'] - tl['bar'], r1 - 0.45, 72, 150, 0.9):
        put(sfx, s0, beatx)
    put(sfx, r1 - 0.62, breath('in', 0.6), 1.1)
    put(sfx, drop, hit(1.25))
    put(sfx, drop + 0.02, chains(1.6), 0.9)
    put(sfx, drop + 0.15, tinnitus(3.4), 1.0)
    cues['hits'].append(round(drop, 3))
    cues['glitches'].append([round(drop, 3), 0.35])
    for li, word in (('lock you in', 'LOCK'), ('will become your name', 'NAME')):
        t = word_time(li, word)
        if t:
            put(sfx, t, chains(1.1) if word == 'LOCK' else hit(0.7), 0.8)
            if word == 'NAME':
                cues['hits'].append(round(t, 3))
                cues['flashes'].append(round(t, 3))
    last_chain = max(l['end'] for l in lines if l['section'] == 'chains')
    bt = np.ceil((last_chain + 0.6) / tl['bar']) * tl['bar']      # post-drop montage: a hit on every slam
    k = 0
    while bt < secs['chains']['end'] - 0.05:
        put(sfx, bt, hit(0.6 if k % 2 == 0 else 0.35))
        cues['hits'].append(round(bt, 3))
        cues['glitches'].append([round(bt, 3), 0.12])
        bt += 2 * beat
        k += 1
    for s0, beatx in heartbeat(secs['everything']['start'] + 0.5, secs['everything']['end'] - 2, 78, 52, 0.35):
        put(sfx, s0, beatx)
    e3 = lines[-1]
    put(sfx, e3['end'] + 0.3, breath('out'), 0.8)
    put(sfx, secs['outro']['start'] + 1.0, thunder(8.0), 0.6)
    clock_stop = total - 2 * tl['bar']
    put(sfx, clock_stop, clunk(), 0.7)
    hit_at(clock_stop + 2.2, 0.9, swell=True)

    # --- score: the drop hits full-range, then goes muffled ("shell shock") and opens back up
    score = read(os.path.join(MV, 'score.wav'))[:n]
    score = pad_to(score, total)[:n]
    muff = filt(score, 'low', 380, 4)
    tt = np.arange(n) / SR
    m = np.interp(tt, [0, drop + 0.12, drop + 0.3, drop + 1.4, drop + 3.2, total], [0, 0, 1, 1, 0, 0])
    score = score * (1 - m[:, None]) + muff * m[:, None] * 1.25
    write(os.path.join(MV, 'thriller_voice.wav'), norm(voice, 0.9))
    write(os.path.join(MV, 'thriller_score.wav'), score)
    write(os.path.join(MV, 'thriller_sfx.wav'), norm(sfx, 0.95))
    cues['hits'] = sorted(set(cues['hits']))
    cues['flashes'] = sorted(set(cues['flashes']))
    json.dump(cues, open(os.path.join(MV, 'thriller_cues.json'), 'w'), indent=1)
    for f in ('_ps_in.wav', '_ps_out.wav'):
        if os.path.exists(os.path.join(MV, f)):
            os.remove(os.path.join(MV, f))
    print(f"thriller audio: {len(cues['hits'])} hits, {len(cues['glitches'])} glitches, shatter at {cues['shatter']}")


if __name__ == '__main__':
    main()
