#!/usr/bin/env python3
"""Stage 1 of the cinematic music video: pick the voice lines, lay them on a bar grid,
render the processed voice stems and write timeline.json for the score and visuals.

    WORK=<work dir> FFMPEG=<ffmpeg> python3 music_video/timeline.py
"""
import json, os, subprocess, sys, wave
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from compile import WORK, FF, load_words, find  # noqa: E402

SR, BPM = 48000, 70
BAR = 4 * 60 / BPM
OUT = os.path.join(WORK, 'mv')
TIME, HOLE, ROCK, CHAINS, GROW, GLASS = ('7678001520788426002', '7670114078936829191', '7628636840991493383',
                                         '7629348688833318152', '7627840728298769682', '7636394268810087687')
FIXES = {HOLE: [['swords kept digging', 'thoughts kept digging']], CHAINS: [["you're on swords", 'your own thoughts']]}

# section: (lead-in bars before the first line, gap between lines, tail bars after the last line, lines)
# line: (clip, in phrase, out phrase, key words to highlight, echo-throw the last word?)
SECTIONS = [
    ('intro', 5, 0, 0, []),
    ('time', 0, 1.1, 1, [
        (TIME, 'Time is already eating us', 'each second is a small bite', ['EATING', 'BITE'], False),
        (TIME, 'you are not watching time go by', 'while it eats you', ['WATCHING', 'DISAPPEAR'], False),
        (TIME, 'Even while you are watching this', 'taking the next second', ['NEXT', 'SECOND'], True)]),
    ('hole', 1, 1.0, 0, [
        (HOLE, 'putting yourself down is like jumping into a hole', "why can't I see the sky", ['HOLE', 'SKY'], False),
        (HOLE, "Every time you say, I can't do it", 'another hand of dirt', ["CAN'T", 'DIRT'], False),
        (HOLE, 'The funny thing is, the ground never pulled you down', 'thoughts kept digging', ['THOUGHTS', 'DIGGING'], True),
        (HOLE, 'The sky never disappeared', 'the light never left', ['LOOKING', 'UP', 'LIGHT'], False)]),
    ('glass', 1, 1.0, 0, [
        (GLASS, 'It can also feel like you are in a glass box', 'like water slowly rising', ['GLASS', 'BOX', 'WATER'], False),
        (GLASS, 'But the box is made in your mind', 'what you keep holding onto', ['MIND', 'HOLDING'], False),
        (GLASS, 'What they say is what they say', 'It is not who you are', ['NOT', 'WHO', 'YOU', 'ARE'], True)]),
    ('road', 1, 1.0, 0, [
        (ROCK, 'Your feet being tired does not mean the road is over', 'It means you walked far', ['ROAD', 'FAR'], False),
        (ROCK, 'Your mind feels heavy does not mean you are broken', 'you are carried a lot', ['BROKEN', 'CARRIED'], False),
        (ROCK, "the truth is, you didn't hit a wall", 'gave it a big name', ['WALL', 'BIG', 'NAME'], True)]),
    ('riser', 2, 0, 0, []),
    ('chains', 1, 0.8, 4, [
        (CHAINS, 'if you never walk you will stay in the same place', 'how far you could have gone', ['WALK', 'RUN', 'FAR'], False),
        (CHAINS, 'never let your mind lock you in a place', 'your body could have left', ['MIND', 'LOCK', 'LEFT'], False),
        (CHAINS, 'So move right now', 'will become your name', ['MOVE', 'RIGHT', 'NOW', 'NAME'], True),
        (GROW, 'If you stop, it all stops', 'you keep on growing', ['STOP', 'GROWING'], False)]),
    ('everything', 1, 1.6, 0, [
        (GROW, 'One day you will look back and realize', "you just didn't see it yet", ['WALKING', 'WHOLE', 'TIME'], False),
        (GROW, 'Keep on going, even when it feels like nothing', 'nothing becomes everything', ['NOTHING', 'EVERYTHING'], True),
        (GLASS, 'Not everything that tries reaching for you', 'needs to stay in you', ['STAY'], False)]),
    ('outro', 5, 0, 0, []),
]


def bars_up(t):
    return np.ceil(t / BAR - 1e-6) * BAR


def process(clip, t0, t1, path):
    subprocess.run([FF, '-y', '-loglevel', 'error', '-ss', f'{t0:.3f}', '-t', f'{t1 - t0:.3f}',
                    '-i', os.path.join(WORK, 'clips', f'{clip}.mp4'), '-af',
                    'highpass=f=90,afftdn=nr=12:nf=-38,equalizer=f=300:t=q:w=1.2:g=-2,'
                    'equalizer=f=3200:t=q:w=1.0:g=3,deesser=i=0.4,'
                    'acompressor=threshold=-20dB:ratio=4:attack=5:release=120:makeup=3,'
                    f'loudnorm=I=-17:TP=-2:LRA=7,aresample={SR},'
                    f'afade=t=in:st=0:d=0.03,afade=t=out:st={t1 - t0 - 0.12:.3f}:d=0.12',
                    '-ac', '2', '-c:a', 'pcm_s16le', path], check=True)
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32).reshape(-1, 2) / 32768


def write(path, x):
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


def hall(seconds=2.8):
    rng = np.random.default_rng(3)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t / (seconds / 6.5))[:, None]
    ir = sosfilt(butter(2, [200, 5500], 'band', fs=SR, output='sos'), ir, axis=0)
    ir = np.concatenate([np.zeros((int(0.025 * SR), 2)), ir])
    return ir / np.sqrt((ir ** 2).sum(0))


def main():
    os.makedirs(os.path.join(OUT, 'lines'), exist_ok=True)
    t, sections, lines, rendered = 0.0, [], [], []
    for name, lead, gap, tail, items in SECTIONS:
        start = t
        t += lead * BAR
        for k, (clip, a, b, keys, throw) in enumerate(items):
            words, _ = load_words(clip, FIXES.get(clip, []))
            i0 = find(words, a)[0]
            i1 = find(words, b, after=words[i0]['start'])[1]
            s0, s1 = words[i0]['start'] - 0.08, words[i1]['end'] + 0.3
            path = os.path.join(OUT, 'lines', f'{len(lines):02d}.wav')
            audio = process(clip, s0, s1, path)
            lw = [dict(start=round(w['start'] - s0 + t, 3), end=round(w['end'] - s0 + t, 3), text=w['text'])
                  for w in words[i0:i1 + 1]]
            lines.append(dict(section=name, clip=clip, src_in=round(s0, 3), src_out=round(s1, 3),
                              start=round(t, 3), end=round(t + len(audio) / SR, 3), keys=keys, throw=throw,
                              text=' '.join(w['text'] for w in lw), words=lw))
            rendered.append((t, audio, throw, lw))
            t += len(audio) / SR + (gap if k < len(items) - 1 else 0)
        if items:
            t = bars_up(t + 0.6) + tail * BAR
        sections.append(dict(name=name, start=round(start, 3), end=round(t, 3), bars=round((t - start) / BAR)))
    total = t
    n = int(total * SR) + SR
    dry = np.zeros((n, 2), np.float32)
    throws = np.zeros((n, 2), np.float32)
    beat = 60 / BPM
    for t0, audio, throw, lw in rendered:
        a = int(t0 * SR)
        dry[a:a + len(audio)] += audio
        if throw:                                               # echo the last word on the beat grid
            w0 = int((lw[-1]['start'] - t0) * SR)
            word = audio[w0:] * np.linspace(1, 0.6, len(audio) - w0)[:, None]
            for r in range(1, 4):
                s = a + w0 + int(r * beat / 2 * SR)
                e = min(n, s + len(word))
                throws[s:e] += word[:e - s] * (0.42 ** r)
    throws = sosfilt(butter(2, [300, 3500], 'band', fs=SR, output='sos'), throws, axis=0)
    ir = hall()
    wet = fftconvolve(dry * 0.9 + throws, ir, axes=0)[:n] * 0.16 + fftconvolve(throws, ir, axes=0)[:n] * 0.35
    write(os.path.join(OUT, 'voice_dry.wav'), dry)
    write(os.path.join(OUT, 'voice_fx.wav'), dry + throws * 0.6 + wet)
    drop = next(s['start'] for s in sections if s['name'] == 'chains')
    json.dump(dict(sr=SR, bpm=BPM, bar=BAR, total=round(total, 3), drop=drop, sections=sections, lines=lines),
              open(os.path.join(OUT, 'timeline.json'), 'w'), indent=1)
    print(f'total {total:.1f}s ({total / BAR:.0f} bars); drop at {drop:.2f}s')
    for s in sections:
        print(f"  {s['name']:10} {s['start']:7.2f} -> {s['end']:7.2f}  ({s['bars']} bars)")


if __name__ == '__main__':
    main()
