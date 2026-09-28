#!/usr/bin/env python3
"""Stage 3 of the cinematic music video: shots, grades, kinetic type, then the final mix.

    WORK=<work dir> FFMPEG=<ffmpeg> python3 music_video/visuals.py

Reads $WORK/mv/timeline.json, voice_fx.wav, voice_dry.wav and score.wav; writes
$WORK/mv/brandon_molina_nothing_becomes_everything.mp4 (1920x1080, 24 fps, 2.39:1 letterbox).
"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from compile import WORK, FF, gamma_for, ass_time, esc  # noqa: E402

FPS, W, IH, H = 24, 1920, 804, 1080          # IH = picture height inside the 2.39:1 bars
BAR_Y = (H - IH) // 2
MV = os.path.join(WORK, 'mv')
SH = os.path.join(MV, 'shots')
LAY = os.path.join(MV, 'layers')
FONTS = os.path.join(WORK, 'fonts')
JOBS = int(os.environ.get('JOBS', '2'))
AMBER, WHITE = '&H0047B3FF&', '&H00FFFFFF&'
PW = 452                                     # portrait width at picture height (576x1024 -> 452x804)
X264 = ['-c:v', 'libx264', '-preset', 'fast', '-crf', '21', '-maxrate', '9M', '-bufsize', '18M',
        '-pix_fmt', 'yuv420p', '-r', str(FPS), '-threads', '2']

GRADE = {
    'bw': 'hue=s=0,curves=preset=strong_contrast,eq=gamma=1.05',
    'teal': 'colorbalance=rs=-0.08:gs=0.02:bs=0.10:rh=0.10:gh=0.02:bh=-0.08,curves=preset=medium_contrast,eq=saturation=0.85',
    'cold': 'colorbalance=rs=-0.14:bs=0.20:rm=-0.06:bm=0.10,eq=saturation=0.65:brightness=-0.02,curves=preset=medium_contrast',
    'warm': 'colorbalance=rs=0.08:bs=-0.10:rh=0.12:bh=-0.10,eq=saturation=1.05:gamma=1.04',
    'drop': 'colorbalance=rs=-0.06:bs=0.08:rh=0.12:bh=-0.10,curves=preset=strong_contrast,eq=saturation=1.12',
}
SECTION_GRADE = {'intro': 'bw', 'time': 'bw', 'hole': 'teal', 'glass': 'cold', 'road': 'warm',
                 'riser': 'drop', 'chains': 'drop', 'everything': 'warm', 'outro': 'bw'}
# clips with a TikTok text sticker burned into the top: px to trim off the 576x1024 frame in portrait shots
TOP_TRIM = {'7628636840991493383': 230}


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"ffmpeg failed:\n{' '.join(cmd)[:1500]}\n{p.stderr[-2500:]}")
    return p.stderr


# ---------------------------------------------------------------- overlay layers
def make_layers():
    """Bokeh dust, warm light leaks and the portrait feather mask (RGBA PNG sequences)."""
    os.makedirs(LAY, exist_ok=True)
    rng = np.random.default_rng(11)
    if not os.path.exists(f'{LAY}/mask.png'):
        m = np.ones((IH, PW), np.float32)
        ramp = 90
        m[:, :ramp] *= np.linspace(0, 1, ramp)[None, :] ** 1.5
        m[:, -ramp:] *= np.linspace(1, 0, ramp)[None, :] ** 1.5
        Image.fromarray((m * 255).astype('uint8')).save(f'{LAY}/mask.png')
    n, w, h = FPS * 8, W // 2, IH // 2
    if not os.path.exists(f'{LAY}/dust_{n - 1:03d}.png'):
        k = 70
        pos = rng.uniform([0, 0], [w, h], (k, 2))
        vel = rng.uniform([-6, -14], [6, -4], (k, 2)) / FPS
        size = rng.uniform(1.5, 7, k)
        bright = rng.uniform(40, 170, k)
        ph = rng.uniform(0, 2 * np.pi, k)
        for f in range(n):
            im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            p = (pos + vel * f) % [w, h]                         # wraps -> seamless-ish loop
            for i in range(k):
                a = bright[i] * (0.6 + 0.4 * np.sin(2 * np.pi * f / n * 2 + ph[i]))
                r = size[i]
                d.ellipse((p[i, 0] - r, p[i, 1] - r, p[i, 0] + r, p[i, 1] + r), fill=(255, 240, 220, int(a)))
            im.filter(ImageFilter.GaussianBlur(1.6)).save(f'{LAY}/dust_{f:03d}.png')
    if not os.path.exists(f'{LAY}/leak_{n - 1:03d}.png'):
        blobs = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(120, 260), rng.uniform(0, 2 * np.pi),
                  [(255, 140, 40), (255, 80, 30), (255, 200, 120)][i % 3]) for i in range(4)]
        for f in range(n):
            im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            for bx, by, r, p, col in blobs:
                t = 2 * np.pi * f / n + p
                x, y = bx + 160 * np.sin(t), by + 70 * np.cos(t * 1.3)
                a = int(90 + 60 * np.sin(t * 2))
                d.ellipse((x - r, y - r, x + r, y + r), fill=col + (a,))
            im.filter(ImageFilter.GaussianBlur(70)).save(f'{LAY}/leak_{f:03d}.png')


# ---------------------------------------------------------------- face / eye line for ECU crops
_eye = {}


def eye_line(clip, t):
    key = (clip, round(t))
    if key not in _eye:
        import cv2
        casc = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        raw = subprocess.run([FF, '-v', 'error', '-ss', f'{max(0, t - 1):.2f}', '-t', '2', '-i', f'{WORK}/clips/{clip}.mp4',
                              '-vf', 'fps=3,format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
        fr = np.frombuffer(raw, np.uint8).reshape(-1, 1024, 576)
        ys = []
        for g in fr:
            f = casc.detectMultiScale(g, 1.1, 5, minSize=(110, 110))
            if len(f):
                x, y, w_, h_ = max(f, key=lambda r: r[2] * r[3])
                ys.append(y + 0.45 * h_)
        _eye[key] = int(np.median(ys)) if ys else 430
    return _eye[key]


# ---------------------------------------------------------------- ASS
HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {IH}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Lyric,Cinzel Decorative,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,3,0,1,0,3,4,0,0,0,1
Style: Slam,Anton,230,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,6,0,1,0,6,5,0,0,0,1
Style: Title,Cinzel Decorative,86,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,16,0,1,0,0,5,0,0,0,1
Style: Kicker,Cinzel Decorative,34,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,18,0,1,0,0,5,0,0,0,1
Style: Flash,Anton,20,&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def dlg(a, b, style, text, layer=1):
    return f'Dialogue: {layer},{ass_time(a)},{ass_time(b)},{style},,0,0,0,,{text}'


def flash(t, dur=0.16, alpha='40'):
    return dlg(t, t + dur, 'Flash', '{\\an7\\pos(0,0)\\alpha&H%s&\\fad(0,%d)\\p1}m 0 0 l %d 0 l %d %d l 0 %d{\\p0}'
               % (alpha, int(dur * 1000), W, W, IH, IH), 9)


def lyric(line, t0, side):
    """Word-by-word reveal of one spoken line, key words bigger and amber, soft drift."""
    keys = set(line['keys'])
    rows, cur, n = [], [], 0
    for w in line['words']:
        wt = w['text'].upper()
        cost = len(wt) * (1.6 if wt.strip('.,!?') in keys else 1) + 1
        if cur and n + cost > 24:
            rows.append(cur)
            cur, n = [], 0
        cur.append(w)
        n += cost
    rows.append(cur)
    parts = []
    for r, row in enumerate(rows):
        seg = []
        for w in row:
            a = int((w['start'] - t0) * 1000) - 60
            wt = esc(w['text'].upper())
            big = wt.strip('.,!?') in keys
            style = '\\fnAnton\\fs92\\fsp5\\c%s' % AMBER if big else '\\fnCinzel Decorative\\fs58\\fsp3\\c%s' % WHITE
            seg.append('{%s\\alpha&HFF&\\blur7\\t(%d,%d,\\alpha&H00&\\blur0.6)}%s' % (style, a, a + 240, wt))
        parts.append(' '.join(seg))
    x0 = 150 if side == 'left' else W - 150
    an = 4 if side == 'left' else 6
    end = line['end'] - t0 + 0.5
    move = '\\move(%d,%d,%d,%d)' % (x0, IH // 2, x0 + (18 if side == 'left' else -18), IH // 2)
    return dlg(0, end, 'Lyric', '{\\an%d%s\\fad(0,450)}' % (an, move) + '\\N'.join(parts), 3)


def write_ass(path, events):
    with open(path, 'w') as f:
        f.write(HEAD + '\n'.join(events) + '\n')


# ---------------------------------------------------------------- shot rendering
def finish(grade, extra=''):
    """Common tail: grade, text, grain, vignette, letterbox."""
    return (f"{GRADE[grade]}{extra},ass='{{ass}}':fontsdir='{FONTS}',"
            f"noise=alls=5:allf=t,vignette=angle=PI/4.4,pad={W}:{H}:0:{BAR_Y}:black")


def render(i, s):
    d = s['dur']
    nf = s['nf']
    ass = os.path.join(SH, f'{i:03d}.ass')
    write_ass(ass, s['events'])
    out = os.path.join(SH, f'{i:03d}.mp4')
    grade = s['grade']
    fx = ''
    if s.get('shake'):
        fx += (f",scale={int(W * 1.05)}:{int(IH * 1.05)},crop={W}:{IH}:"
               f"x='{int(W * 0.025)}+11*sin(t*41)+6*sin(t*67)':y='{int(IH * 0.025)}+7*sin(t*53)+4*sin(t*31)',"
               "rgbashift=rh=-5:bh=5")
    if s.get('glow'):
        fx += (",format=gbrp,split[g1][g2];[g2]scale=480:201,gblur=sigma=14,scale="
               f"{W}:{IH}[g3];[g1][g3]blend=all_mode=screen:all_opacity=0.38,format=yuv420p")
    tail = finish(grade, fx).replace('{ass}', ass)
    dust = f"[{{d}}:v]scale={W}:{IH},format=rgba,colorchannelmixer=aa={s.get('dust', 0.55)}[dust];"
    leak = f"[{{l}}:v]scale={W}:{IH},format=rgba,colorchannelmixer=aa={s.get('leak', 0.0)}[leak];"
    ins, graph = [], ''
    if s['kind'] == 'space':
        ins += ['-loop', '1', '-framerate', str(FPS), '-i', f'{WORK}/assets/starfield.png']
        graph = (f"[0:v]scale={int(W * 1.2)}:-2,crop={W}:{IH}:x='{s.get('pan_x', 40)}+t*{s.get('pan_v', 12)}':"
                 f"y='(ih-{IH})/2-t*{s.get('tilt_v', 0)}',eq=brightness={s.get('bright', -0.02)}[base];")
    else:
        g = s['gamma']
        src = f'{WORK}/clips/{s["clip"]}.mp4'
        slow = s.get('slow', 1.0)
        ins += ['-ss', f"{s['src']:.3f}", '-t', f'{d / slow + 0.5:.3f}', '-i', src]
        pre = f"[0:v]setpts={1 / slow:.4f}*PTS,fps={FPS},scale=576:1024,setsar=1,hqdn3d=1.5:1.5:4:4,eq=gamma={g}"
        if slow < 1:
            pre += ",tmix=frames=3:weights='1 2 1'"
        if s['kind'] == 'portrait':
            x = s['x']
            top = TOP_TRIM.get(s['clip'], 0)
            if top:                                              # keep the 9:16 shape, zoom past the sticker
                th = 1024 - top
                tw = int(th * 576 / 1024) // 2 * 2
                pre += f",crop={tw}:{th}:{(576 - tw) // 2}:{top},scale=576:1024"
            graph = (f"{pre},split=2[a][b];"
                     f"[a]scale=240:427,crop=240:100:0:300,gblur=sigma=14,scale={W}:{IH},"
                     f"eq=brightness=-0.34:saturation=0.5[bg];"
                     f"[b]scale={PW}:{IH}:flags=lanczos,unsharp=5:5:0.4[fg0];[fg0][m]alphamerge[fg];"
                     f"[bg][fg]overlay={x}:0[base];")
        else:                                                    # ecu: eye-line band, full width
            y = max(0, min(1024 - 241, s['eye'] - 120))
            graph = f"{pre},crop=576:241:0:{y},scale={W}:{IH}:flags=lanczos,unsharp=7:7:0.8[base];"
    k = len([x for x in ins if x == '-i'])
    extra_in = []
    if s['kind'] == 'portrait':
        extra_in += ['-loop', '1', '-i', f'{LAY}/mask.png']
        graph = graph.replace('[m]', f'[{k}:v]')
        k += 1
    extra_in += ['-framerate', str(FPS), '-loop', '1', '-i', os.path.join(LAY, 'dust_%03d.png')]
    di = k
    k += 1
    graph += dust.format(d=di)
    comp = '[base][dust]overlay=0:0:format=auto[c1];'
    if s.get('leak'):
        extra_in += ['-framerate', str(FPS), '-loop', '1', '-i', os.path.join(LAY, 'leak_%03d.png')]
        graph += leak.format(l=k)
        comp += '[c1][leak]overlay=0:0:format=auto[c2];'
        last = 'c2'
    else:
        last = 'c1'
    fade = f",fade=t=in:st=0:d={s.get('fin', 0.0)}" if s.get('fin') else ''
    fade += f",fade=t=out:st={d - s['fout']:.3f}:d={s['fout']}" if s.get('fout') else ''
    graph += comp + f"[{last}]{tail}{fade},trim=end_frame={nf},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v]"
    run([FF, '-y', '-nostats', '-loglevel', 'error', *ins, *extra_in, '-filter_complex', graph,
         '-map', '[v]', '-frames:v', str(nf), *X264, out])
    return i


# ---------------------------------------------------------------- shot list
def build(tl):
    lines, secs = tl['lines'], {s['name']: s for s in tl['sections']}
    beat, bar = 60 / tl['bpm'], tl['bar']
    shots, gam = [], {}

    def g(clip):
        if clip not in gam:
            gam[clip] = gamma_for(f'{WORK}/clips/{clip}.mp4')[0]
        return gam[clip]

    def add(t0, t1, **kw):
        if t1 - t0 > 0.04:
            shots.append(dict(t0=t0, dur=t1 - t0, events=kw.pop('events', []), **kw))

    def cut(section, t0, t1, clip, src, kind='ecu', slow=0.5, **kw):
        kw.setdefault('grade', SECTION_GRADE[section])
        e = dict(eye=eye_line(clip, src + 1)) if kind == 'ecu' else {}
        add(t0, t1, kind=kind, clip=clip, src=src, gamma=g(clip), slow=slow, **e, **kw)

    first_clip = {s: next((l['clip'] for l in lines if l['section'] == s), None) for s in secs}
    by_sec = {s: [l for l in lines if l['section'] == s] for s in secs}
    side = 'left'
    for name, s in secs.items():
        ls = by_sec[name]
        t = s['start']
        if name == 'intro':
            ev = [dlg(1.2, 9.0, 'Kicker', '{\\an5\\pos(960,300)\\fad(1400,900)}BRANDON MOLINA', 2),
                  dlg(3.0, 9.4, 'Title', '{\\an5\\pos(960,420)\\blur2\\fad(1800,1000)\\t(0,6000,\\fsp24)}NOTHING BECOMES', 2),
                  dlg(3.6, 9.4, 'Title', '{\\an5\\pos(960,520)\\blur2\\fad(1800,1000)\\t(0,6000,\\fsp24)}EVERYTHING', 2)]
            add(t, t + 9.43, kind='space', grade='bw', events=ev, fin=2.5, pan_v=10, dust=0.7)
            cut(name, t + 9.43, s['end'], first_clip['time'], 3.0, kind='portrait', x=W // 2 - PW // 2,
                slow=0.5, events=[], fout=0.0, dust=0.6)
            continue
        if name == 'riser':                                     # accelerating ECU cuts, then suck-back
            lens = [2, 2, 1, 1, 0.5, 0.5, 0.5, 0.5]
            src_clip = first_clip['chains']
            for k, n_beats in enumerate(lens):
                a = t
                t = min(s['end'] - 0.35, t + n_beats * beat)
                cut(name, a, t, src_clip, 10 + k * 3.1, slow=1.0, events=[flash(0, 0.1, '70')], shake=k > 3)
            add(t, s['end'], kind='space', grade='bw', bright=-0.9, events=[], dust=0.0)
            continue
        if name == 'outro':
            ev = [dlg(0.8, 12.5, 'Title', '{\\an5\\pos(960,380)\\fad(1500,1500)}NOTHING BECOMES', 2),
                  dlg(1.4, 12.5, 'Title', '{\\an5\\pos(960,480)\\fad(1500,1500)}EVERYTHING', 2),
                  dlg(5.0, s['end'] - t - 1.0, 'Kicker', '{\\an5\\pos(960,600)\\fad(1200,1800)}BRANDON MOLINA', 2)]
            add(t, s['end'], kind='space', grade='bw', events=ev, fout=3.5, pan_v=8, tilt_v=6, leak=0.35, dust=0.8)
            continue
        # lead-in before the first line: slow-motion ECU (or space for the hope section)
        if ls and ls[0]['start'] - t > 0.3:
            if name == 'everything':
                add(t, ls[0]['start'], kind='space', grade='warm', events=[], leak=0.55, pan_v=14, tilt_v=10)
            else:
                cut(name, t, ls[0]['start'], ls[0]['clip'], max(0.0, ls[0]['src_in'] - 3.5), slow=0.5,
                    events=[flash(0, 0.3, '30')] if name == 'chains' else [], shake=name == 'chains')
        for k, l in enumerate(ls):
            nxt = ls[k + 1]['start'] if k + 1 < len(ls) else None
            a = l['start']
            b = nxt if nxt else min(s['end'], l['end'] + 0.9)
            x = W - PW - 170 if side == 'left' else 170
            ev = [lyric(l, a, side)]
            if name == 'chains':
                ev += [flash(bt - a, 0.14, '50') for bt in np.arange(s['start'], s['end'], bar) if a <= bt < b]
            cut(name, a, b, l['clip'], l['src_in'], kind='portrait', x=x, slow=1.0, events=ev,
                shake=name == 'chains', glow=name == 'everything', leak=0.3 if name in ('road', 'everything') else 0)
            side = 'right' if side == 'left' else 'left'
            t = b
        if t < s['end'] - 0.04:                                 # instrumental tail of the section
            if name == 'chains':                                # post-drop montage with word slams
                words = ['WALK.', 'RUN.', 'MOVE.', 'GROW.']
                src_clip = first_clip['chains']
                k = 0
                while t < s['end'] - 0.04:
                    a = t
                    t = min(s['end'], t + 2 * beat)
                    ev = [flash(0, 0.12, '40')]
                    if k % 2 == 0:
                        ev.append(dlg(0, 2 * beat * 2, 'Slam', '{\\an5\\pos(960,402)\\fscx130\\fscy130'
                                      '\\t(0,160,\\fscx100\\fscy100)\\fad(0,250)}%s' % words[(k // 2) % 4], 5))
                    cut(name, a, t, src_clip if k % 3 else first_clip['road'], 20 + k * 2.3, slow=1.0,
                        events=ev, shake=True)
                    k += 1
            elif name == 'everything':
                add(t, s['end'], kind='space', grade='warm', events=[], pan_v=12, leak=0.3)
            else:                                               # slow-motion eyes as a breath between sections
                cut(name, t, s['end'], ls[-1]['clip'], ls[-1]['src_out'] + 0.5, slow=0.5, events=[])
    return shots


# ---------------------------------------------------------------- mix
def mix(tl, video, out):
    run([FF, '-y', '-nostats', '-loglevel', 'error', '-i', f'{MV}/voice_fx.wav', '-i', f'{MV}/voice_dry.wav',
         '-i', f'{MV}/score.wav', '-filter_complex',
         '[2:a][1:a]sidechaincompress=threshold=0.04:ratio=2.5:attack=30:release=500[sc];'
         f"[0:a][sc]amix=inputs=2:normalize=0,atrim=0:{tl['total']:.3f}[m]",
         '-map', '[m]', '-c:a', 'pcm_s16le', f'{MV}/premix.wav'])
    st = run([FF, '-hide_banner', '-i', f'{MV}/premix.wav', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json',
              '-f', 'null', '-'])
    m = json.loads(st[st.rindex('{'):st.rindex('}') + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    run([FF, '-y', '-nostats', '-loglevel', 'error', '-i', video, '-i', f'{MV}/premix.wav', '-af', f'{ln},aresample=48000',
         '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest',
         '-movflags', '+faststart', out])


def main():
    tl = json.load(open(f'{MV}/timeline.json'))
    os.makedirs(SH, exist_ok=True)
    make_layers()
    shots = build(tl)
    for s in shots:                                               # frame-exact tiling, no A/V drift
        s['nf'] = int(round((s['t0'] + s['dur']) * FPS)) - int(round(s['t0'] * FPS))
    total = sum(s['nf'] for s in shots) / FPS
    print(f'{len(shots)} shots, {total:.2f}s (timeline {tl["total"]:.2f}s)', flush=True)
    for i, s in enumerate(shots):
        print(f"  {i:03d} {s['t0']:7.2f} {s['kind']:8} {s['nf']:4d}f {s.get('clip', '')[-5:]}", flush=True)
    only = os.environ.get('ONLY')
    todo = [i for i in range(len(shots)) if (only is None or str(i) in only.split(','))
            and (only or not os.path.exists(f'{SH}/{i:03d}.mp4'))]
    with ThreadPoolExecutor(JOBS) as pool:
        for i in pool.map(lambda i: render(i, shots[i]), todo):
            print(f"  shot {i:03d} {shots[i]['kind']:8} {shots[i]['dur']:5.2f}s", flush=True)
    if only:
        return
    with open(f'{MV}/shots.txt', 'w') as f:
        f.writelines(f"file '{SH}/{i:03d}.mp4'\n" for i in range(len(shots)))
    run([FF, '-y', '-nostats', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{MV}/shots.txt',
         '-c', 'copy', f'{MV}/video_only.mp4'])
    if os.path.exists(f'{MV}/score.wav'):
        out = f'{MV}/brandon_molina_nothing_becomes_everything.mp4'
        mix(tl, f'{MV}/video_only.mp4', out)
        print('done:', out)
    else:
        print('video done; score.wav missing, run the mix again once it exists')


if __name__ == '__main__':
    main()
