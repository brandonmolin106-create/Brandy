#!/usr/bin/env python3
"""Build every upload for "Nothing Becomes Everything": three audio packs (voice, SFX, music) with a
manifest of play regions, optional zone videos, and the loading screens.

    WORK=<tiktok work dir> FFMPEG=<ffmpeg> python3 tools/make_media.py [--videos]

Needs the TikTok pipeline outputs in $WORK: clips/, transcripts/, assets/, fonts/, mv/timeline.json,
mv/lines/*.wav, and mv/score_noduck.wav (score.py run with DUCK_DB=0 SCORE_OUT=...score_noduck.wav).
Writes into ../upload/. Everything audible is Brandon's own voice or generated in code.
"""
import json, os, re, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'echoes-yt-compiler'))
sys.path.insert(0, os.path.join(REPO, 'echoes-yt-compiler', 'music_video'))
from compile import WORK, FF, load_words, find, gamma_for  # noqa: E402
import timeline as TLM  # noqa: E402
import thriller_audio as TA  # noqa: E402

SR = 48000
UP = os.path.join(HERE, '..', 'upload')
MV = os.path.join(WORK, 'mv')
rng = np.random.default_rng(2026)

# id -> index in mv/timeline.json "lines" (and mv/lines/NN.wav), plus the caption text shown in game
LINES = [
    ('time_1', 'time', 0, "Time is already eating us. Each second is a small bite."),
    ('time_2', 'time', 1, "You are not watching time go by. Time is watching you disappear while it eats you."),
    ('time_3', 'time', 2, "Even while you are watching this, it is already taking the next second."),
    ('hole_1', 'hole', 3, "Putting yourself down is like jumping into a hole and asking yourself, why can't I see the sky?"),
    ('hole_2', 'hole', 4, "Every time you say \"I can't do it, I'm not good,\" it's another hand of dirt."),
    ('hole_3', 'hole', 5, "The funny thing is, the ground never pulled you down. Your thoughts kept digging."),
    ('hole_4', 'hole', 6, "The sky never disappeared. The sky never went away. You just stopped looking up. The light never left."),
    ('glass_1', 'glass', 7, "It can also feel like you are in a glass box, and every word goes in like water slowly rising."),
    ('glass_2', 'glass', 8, "But the box is made in your mind, and the water is what you keep holding onto."),
    ('glass_3', 'glass', 9, "What they say is what they say. It is not who you are."),
    ('road_1', 'road', 10, "Your feet being tired does not mean the road is over. It means you walked far."),
    ('road_2', 'road', 11, "Your mind feels heavy does not mean you are broken. It means that you are carried a lot."),
    ('road_3', 'road', 12, "The truth is, you didn't hit a wall. You just met something small and gave it a big name."),
    ('chains_1', 'chains', 13, "If you never walk, you will stay in the same place. If you never run, you will never see how far you could have gone."),
    ('chains_2', 'chains', 14, "Never let your mind lock you in a place your body could have left."),
    ('chains_3', 'chains', 15, "So move right now. Don't stay the same, or \"I can't\" will become your name."),
    ('chains_4', 'chains', 16, "If you stop, it all stops. If you keep going, you keep on growing."),
    ('everything_1', 'everything', 17, "One day you will look back and realize you were walking the whole time. You just didn't see it yet."),
    ('everything_2', 'everything', 18, "Keep on going, even when it feels like nothing, because one day that nothing becomes everything."),
    ('glass_4', 'glass', 19, "Not everything that tries reaching for you needs to stay in you."),
]
# extra lines cut straight from his own-sound clips: (id, zone, clip, in phrase, out phrase, fixes, caption)
EXTRA = [
    ('hole_step', 'hole', '7670114078936829191', 'one better thought is one step higher', 'one step higher',
     [['better sort', 'better thought']], "One better thought is one step higher."),
    ('hole_move', 'hole', '7670114078936829191', 'You was never made to look at dirt', 'you were made to move', [],
     "You were never made to look at dirt. You were made to move."),
    ('everything_3', 'everything', '7627840728298769682', "You don't have to be great today", 'You just have to not stop', [],
     "You don't have to be great today. You don't have to be the best. You just have to not stop."),
    ('hub_welcome', 'hub', '7550285407464787218', 'just a friendly reminder', 'you are amazing', [],
     "Just a friendly reminder that you are amazing."),
]
# zone videos (optional uploads, 2,000 Robux each on Roblox): clip, in phrase, out phrase (None = to the end)
VIDEOS = {
    'hub': ('7560378479389248775', 'So I thought it would be a great idea', 'Just throw it out'),
    'time': ('7678001520788426002', 'one day we will all be gone. Time is already eating us', 'you move with it instead of against it'),
    'hole': ('7670114078936829191', 'I just want to say, putting yourself down', None),
    'glass': ('7636394268810087687', 'I just want to say, people say things', None),
    'road': ('7628636840991493383', 'listen to this. Sometimes you say', None),
    'chains': ('7629348688833318152', 'If you can walk, then you can move forward', None),
    'everything': ('7627840728298769682', 'listen closely', None),
}


# ---------------------------------------------------------------- audio helpers
def read(path):
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float64) / 32768
        return x.reshape(-1, w.getnchannels())


def write(path, x):
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


def silence(sec):
    return np.zeros((int(sec * SR), 2))


def lufs(x):
    tmp = os.path.join(UP, '_lufs.wav')
    write(tmp, x)
    err = subprocess.run([FF, '-hide_banner', '-nostats', '-i', tmp, '-af', 'ebur128', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    os.remove(tmp)
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', err)[-1])


def to_lufs(x, target, ceiling=0.89):
    y = x * 10 ** ((target - lufs(x)) / 20)
    peak = np.abs(y).max()
    if peak > ceiling:                                          # soft-knee limit only the overs
        y = np.sign(y) * np.where(np.abs(y) > ceiling * 0.8,
                                  ceiling * 0.8 + (ceiling * 0.2) * np.tanh((np.abs(y) - ceiling * 0.8) / (ceiling * 0.2)),
                                  np.abs(y))
    return y


def ogg(wav, out, q):
    subprocess.run([FF, '-y', '-loglevel', 'error', '-i', wav, '-c:a', 'libvorbis', '-q:a', str(q), out], check=True)
    os.remove(wav)


def pack(items, gap, lead=0.3):
    """Concatenate (name, audio) with silence between; returns audio and {name: (start, end)}."""
    parts, regions, t = [silence(lead)], {}, lead
    for name, x in items:
        regions[name] = (round(t, 3), round(t + len(x) / SR, 3))
        parts += [x, silence(gap)]
        t += len(x) / SR + gap
    return np.concatenate(parts), regions


# ---------------------------------------------------------------- voice pack
def voice_pack():
    tl = json.load(open(os.path.join(MV, 'timeline.json')))
    items, meta = [], {}
    for lid, zone, idx, text in LINES:
        assert tl['lines'][idx]['section'] in (zone, 'everything'), (lid, tl['lines'][idx]['section'])
        items.append((lid, read(os.path.join(MV, 'lines', f'{idx:02d}.wav'))))
        meta[lid] = (zone, text)
    for lid, zone, clip, a, b, fixes, text in EXTRA:
        words, _ = load_words(clip, fixes)
        i0 = find(words, a)[0]
        i1 = find(words, b, after=words[i0]['start'])[1]
        tmp = os.path.join(UP, f'_{lid}.wav')
        items.append((lid, TLM.process(clip, words[i0]['start'] - 0.08, words[i1]['end'] + 0.3, tmp).astype(np.float64)))
        os.remove(tmp)
        meta[lid] = (zone, text)
    order = ['hub_welcome'] + [x[0] for x in LINES if x[1] == 'time'] + \
            [i for z in ('hole', 'glass', 'road', 'chains', 'everything') for i, _ in items if meta[i][0] == z]
    items = sorted(items, key=lambda it: order.index(it[0]))
    room = TA.ir(0.9, 200, 7000, 4)
    items = [(n, x + TA.fftconvolve(x, room, axes=0)[:len(x)] * 0.06) for n, x in items]
    audio, regions = pack(items, gap=0.6)
    audio = to_lufs(audio, -16.0)
    write(os.path.join(UP, '_voice.wav'), audio)
    ogg(os.path.join(UP, '_voice.wav'), os.path.join(UP, 'voice_pack.ogg'), 5)
    lines = [dict(id=n, zone=meta[n][0], start=regions[n][0], end=regions[n][1], text=meta[n][1]) for n, _ in items]
    return dict(file='voice_pack.ogg', duration=round(len(audio) / SR, 3), lines=lines)


# ---------------------------------------------------------------- sfx pack
def tone(freqs, dur, decays, amps, vib=0.0):
    t = np.arange(int(dur * SR)) / SR
    x = sum(a * np.sin(2 * np.pi * f * t * (1 + vib * np.sin(2 * np.pi * 5.5 * t)) + rng.uniform(0, 6.3)) * np.exp(-t * d)
            for f, d, a in zip(freqs, decays, amps))
    return x


def chime(f0=880.0, dur=1.6):
    x = tone([f0, f0 * 2.0, f0 * 2.76, f0 * 5.4], dur, [2.6, 3.6, 5, 8], [1, .45, .3, .15])
    for k, r in enumerate((2.0, 2.5, 3.0)):                     # a little sparkle on top
        s = int(k * 0.06 * SR)
        x[s:] += tone([f0 * r], dur, [9], [0.25])[:len(x) - s]
    return TA.norm(TA.verb(TA.st(x, 0.003), 1.2, 0.22, lo=400, hi=12000, seed=3), 0.6)


def bell(f0=196.0, dur=4.5):
    rel = [(0.5, 0.6, 1.0), (1.0, 0.9, 1.3), (1.19, 0.5, 1.8), (1.5, 0.35, 2.2), (2.0, 0.4, 2.6), (2.52, 0.2, 3.4), (3.0, 0.15, 4.2)]
    x = tone([f0 * r for r, _, _ in rel], dur, [d for _, _, d in rel], [a for _, a, _ in rel])
    x += TA.filt(rng.standard_normal(len(x)) * np.exp(-np.arange(len(x)) / SR * 60), 'band', [800, 5000]) * 0.3
    return TA.norm(TA.verb(TA.st(x, 0.004), 3.0, 0.35, seed=8), 0.8)


def ui_click():
    t = np.arange(int(0.12 * SR)) / SR
    x = np.sin(2 * np.pi * 1650 * t) * np.exp(-t * 90) + TA.filt(rng.standard_normal(len(t)) * np.exp(-t * 400), 'high', 3000) * 0.4
    return TA.fade(TA.st(TA.norm(x, 0.4)), 0.001, 0.01)


def portal():
    dur = 2.2
    t = np.arange(int(dur * SR)) / SR
    x = np.zeros(len(t))
    for f in (700, 930, 1180, 1560, 1870, 2400):
        f_t = f * (1 + 0.22 * t / dur) * (1 + 0.006 * np.sin(2 * np.pi * rng.uniform(5, 7) * t))
        x += np.sin(2 * np.pi * np.cumsum(f_t) / SR) * rng.uniform(0.4, 1)
    x *= np.sin(np.pi * t / dur) ** 1.2
    return TA.norm(TA.verb(TA.st(x, 0.006), 2.0, 0.45, lo=500, hi=12000, seed=12), 0.45)


def step_rise():
    dur = 1.0
    t = np.arange(int(dur * SR)) / SR
    grind = TA.filt(np.cumsum(rng.standard_normal(len(t))), 'band', [40, 260], 3)
    grind = grind / np.abs(grind).max() * np.clip(t / 0.7, 0, 1) ** 1.3 * (t < 0.75)
    x = TA.st(grind * 0.8)
    thud = TA.dirt()
    s = int(0.72 * SR)
    x[s:s + len(thud)] += thud[:len(x) - s] * 0.9
    return TA.norm(TA.fade(x, 0.02, 0.05), 0.7)


def water_drain():
    dur = 1.8
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    blk = 960
    noise = rng.standard_normal(n)
    for s in range(0, n, blk):                                  # band-pass sweeping down: a draining gurgle
        fc = 2400 * (1 - s / n) ** 1.5 + 180
        x[s:s + blk] = TA.filt(noise[s:s + blk], 'band', [fc * 0.6, fc * 1.4])
    x *= np.sin(np.pi * t / dur) ** 0.8 * 0.6
    for _ in range(26):                                         # bubbles: tiny upward chirps
        s = int(rng.uniform(0, dur - 0.1) * SR)
        m = int(0.045 * SR)
        tt = np.arange(m) / SR
        f = rng.uniform(300, 900) * (1 + 6 * tt)
        x[s:s + m] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 60) * rng.uniform(0.2, 0.5)
    return TA.norm(TA.verb(TA.st(x, 0.002), 1.0, 0.2, seed=13), 0.55)


def clock_tick():
    x = np.zeros((int(0.9 * SR), 2))
    for at, f in ((0.0, 3200), (60 / 70, 1900)):
        t = np.arange(int(0.05 * SR)) / SR
        c = np.sin(2 * np.pi * f * t) * np.exp(-t * 180) + TA.filt(rng.standard_normal(len(t)) * np.exp(-t * 500), 'high', 2500) * 0.5
        s = int(at * SR)
        e = min(len(x), s + len(c))
        x[s:e] += TA.st(c)[:e - s]
    return TA.norm(TA.verb(x, 0.8, 0.2, seed=14), 0.5)


def sfx_pack():
    def after(a, b, at):
        out = np.zeros((max(len(a), int(at * SR) + len(b)), 2))
        out[:len(a)] += a
        out[int(at * SR):int(at * SR) + len(b)] += b
        return out
    hb = TA.heartbeat(0.0, 0.5, 70, 70, 0.9)[0][1]
    d5, fs5, a5 = 587.33, 739.99, 880.0
    chord = after(after(chime(d5, 2.4), chime(fs5, 2.3), 0.08), chime(a5, 2.2), 0.16)
    items = [
        ('collect', chime(1046.5)), ('step_rise', step_rise()), ('glass_shatter', TA.glass_shatter()),
        ('water_drain', water_drain()), ('chains_break', after(TA.chains(1.1), TA.hit(0.55), 0.05)),
        ('wall_shrink', after(TA.reverse_swell(1.3), TA.hit(0.35), 1.3)), ('zone_complete', after(TA.hit(0.45), chord, 0.0)),
        ('clock_tick', clock_tick()), ('heartbeat', hb), ('whoosh', read(os.path.join(WORK, 'assets', 'whoosh.wav'))),
        ('portal', portal()), ('ui_click', ui_click()), ('finale_boom', TA.hit(1.0)), ('bell', bell()),
    ]
    items = [(n, TA.norm(x, 0.7) if np.abs(x).max() > 0.7 else x) for n, x in items]
    audio, regions = pack(items, gap=0.35)
    write(os.path.join(UP, '_sfx.wav'), audio)
    ogg(os.path.join(UP, '_sfx.wav'), os.path.join(UP, 'sfx_pack.ogg'), 5)
    return dict(file='sfx_pack.ogg', duration=round(len(audio) / SR, 3),
                sounds={n: dict(start=a, end=b) for n, (a, b) in regions.items()})


# ---------------------------------------------------------------- music pack
def music_pack():
    tl = json.load(open(os.path.join(MV, 'timeline.json')))
    sec = {s['name']: (s['start'], s['end']) for s in tl['sections']}
    bar = tl['bar']
    score = read(os.path.join(MV, 'score_noduck.wav'))
    pad = read(os.path.join(WORK, 'assets', 'pad_loop.wav'))

    def loop(a, b, xf=0.4):
        """Section [a, b) whose last xf seconds blend into the audio just before a -> seamless wrap."""
        s, e, n = int(a * SR), int(b * SR), int(xf * SR)
        seg = score[s:e].copy()
        w = np.sin(np.linspace(0, np.pi / 2, n))[:, None]
        seg[-n:] = seg[-n:] * np.cos(np.linspace(0, np.pi / 2, n))[:, None] + score[s - n:s] * w
        return seg
    tracks = [
        ('hub', to_lufs(pad, -20.0), True),
        ('time', to_lufs(loop(*sec['time']), -20.0), True),
        ('hole', to_lufs(loop(*sec['hole']), -20.0), True),
        ('glass', to_lufs(loop(*sec['glass']), -20.0), True),
        ('road', to_lufs(loop(sec['road'][0], sec['road'][0] + 7 * bar), -20.0), True),
        ('chains', to_lufs(loop(sec['chains'][0] + bar, sec['chains'][1]), -18.5), True),
        ('everything', to_lufs(loop(*sec['everything']), -20.0), True),
        ('finale', to_lufs(score[int(sec['everything'][0] * SR):], -19.0), False),
    ]
    audio, regions = pack([(n, x) for n, x, _ in tracks], gap=1.0, lead=0.5)
    write(os.path.join(UP, '_music.wav'), audio)
    ogg(os.path.join(UP, '_music.wav'), os.path.join(UP, 'music_pack.ogg'), 4)
    return dict(file='music_pack.ogg', duration=round(len(audio) / SR, 3),
                tracks={n: dict(start=regions[n][0], end=regions[n][1], loop=lp) for n, _, lp in tracks})


# ---------------------------------------------------------------- zone videos (optional)
def videos():
    os.makedirs(os.path.join(UP, 'videos'), exist_ok=True)
    out = {}
    for zone, (clip, a, b) in VIDEOS.items():
        words, dur = load_words(clip, [])
        t0 = max(0.0, words[find(words, a)[0]]['start'] - 0.15)
        t1 = words[find(words, b, after=t0)[1]]['end'] + 0.5 if b else min(dur, words[-1]['end'] + 0.7)
        d = min(t1 - t0, 299.0)
        g = gamma_for(os.path.join(WORK, 'clips', f'{clip}.mp4'))[0]
        name = f'video_{zone}.mp4'
        subprocess.run([FF, '-y', '-loglevel', 'error', '-ss', f'{t0:.3f}', '-t', f'{d:.3f}',
                        '-i', os.path.join(WORK, 'clips', f'{clip}.mp4'),
                        '-vf', f'scale=576:1024,setsar=1,hqdn3d=1.5:1.5:4:4,eq=gamma={g}:contrast=1.04,'
                               f'fade=t=in:st=0:d=0.3,fade=t=out:st={d - 0.4:.3f}:d=0.4,format=yuv420p',
                        '-af', f'highpass=f=80,afftdn=nr=8:nf=-40,loudnorm=I=-16:TP=-1.5:LRA=9,aresample=48000,'
                               f'afade=t=in:st=0:d=0.2,afade=t=out:st={d - 0.4:.3f}:d=0.4',
                        '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-c:a', 'aac', '-b:a', '128k',
                        '-movflags', '+faststart', os.path.join(UP, 'videos', name)], check=True)
        out[zone] = f'videos/{name}'
        print(f'  video {zone:10} {d:6.1f}s  gamma {g}')
    return out


# ---------------------------------------------------------------- loading screens
def loading_screens():
    fonts = os.path.join(WORK, 'fonts')
    W, H = 1920, 1080
    bg = Image.open(os.path.join(WORK, 'assets', 'starfield.png')).convert('RGB')
    bg = bg.resize((W, int(bg.height * W / bg.width))).crop((0, 0, W, H))
    bg = Image.eval(bg, lambda v: int(v * 0.72))
    title = ImageFont.truetype(os.path.join(fonts, 'CinzelDecorative-Black.ttf'), 104)
    sub = ImageFont.truetype(os.path.join(fonts, 'ArchivoBlack-Regular.ttf'), 30)
    mono = ImageFont.truetype(os.path.join(fonts, 'CinzelDecorative-Black.ttf'), 190)

    def glow_ring(img, cx, cy, r, col=(80, 210, 230)):
        g = Image.new('L', img.size, 0)
        ImageDraw.Draw(g).ellipse((cx - r - 18, cy - r - 18, cx + r + 18, cy + r + 18), outline=255, width=14)
        g = g.filter(ImageFilter.GaussianBlur(16))
        img.paste(Image.new('RGB', img.size, col), (0, 0), g)
        ImageDraw.Draw(img).ellipse((cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6), outline=col, width=4)

    def text(img, y, s, font, fill=(245, 245, 245), spacing=0):
        d = ImageDraw.Draw(img)
        chars = list(s)
        widths = [d.textlength(c, font=font) for c in chars]
        total = sum(widths) + spacing * (len(chars) - 1)
        x = (W - total) / 2
        shadow = Image.new('L', img.size, 0)
        sd = ImageDraw.Draw(shadow)
        xx = x
        for c, w in zip(chars, widths):
            sd.text((xx, y + 6), c, font=font, fill=255)
            xx += w + spacing
        img.paste((0, 0, 0), (0, 0), shadow.filter(ImageFilter.GaussianBlur(9)))
        for c, w in zip(chars, widths):
            d.text((x, y), c, font=font, fill=fill)
            x += w + spacing

    for variant in ('photo', 'no_photo'):
        img = bg.copy()
        cx, cy, r = W // 2, 330, 150
        glow_ring(img, cx, cy, r)
        avatar = os.path.join(WORK, '..', 'roblox_work', 'avatar.jpg')
        if variant == 'photo' and os.path.exists(avatar):
            a = Image.open(avatar).convert('RGB').resize((2 * r, 2 * r), Image.LANCZOS)
            m = Image.new('L', (2 * r, 2 * r), 0)
            ImageDraw.Draw(m).ellipse((0, 0, 2 * r, 2 * r), fill=255)
            img.paste(a, (cx - r, cy - r), m)
        else:
            d = ImageDraw.Draw(img)
            w = d.textlength('B', font=mono)
            d.text((cx - w / 2, cy - 128), 'B', font=mono, fill=(235, 250, 255))
        text(img, 560, 'NOTHING BECOMES', title, spacing=6)
        text(img, 690, 'EVERYTHING', title, fill=(120, 225, 238), spacing=10)
        text(img, 860, 'A GAME BY BRANDON', sub, fill=(200, 205, 215), spacing=14)
        img.save(os.path.join(UP, 'loading_screen.png' if variant == 'photo' else 'loading_screen_no_photo.png'), optimize=True)


def main():
    os.makedirs(UP, exist_ok=True)
    man = dict(voice=voice_pack(), sfx=sfx_pack(), music=music_pack())
    print(f"voice pack {man['voice']['duration']:.1f}s ({len(man['voice']['lines'])} lines), "
          f"sfx pack {man['sfx']['duration']:.1f}s, music pack {man['music']['duration']:.1f}s")
    man['videos'] = videos() if '--videos' in sys.argv else {z: f'videos/video_{z}.mp4' for z in VIDEOS}
    loading_screens()
    json.dump(man, open(os.path.join(UP, 'audio_manifest.json'), 'w'), indent=1)
    print('wrote', os.path.join(UP, 'audio_manifest.json'))


if __name__ == '__main__':
    main()
