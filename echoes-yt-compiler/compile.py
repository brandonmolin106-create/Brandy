#!/usr/bin/env python3
"""Echoes in the Dark: turn TikTok speeches into one long-form YouTube video.

    WORK=<work dir> FFMPEG=<ffmpeg binary> python3 compile.py plan.json

The work dir holds clips/<id>.mp4, transcripts/<id>.json (faster-whisper with word
timestamps), assets/ (from make_assets.py) and fonts/. Output lands in <work>/out/.

Per segment: 16:9 frame with the vertical clip centred over a blurred copy of itself,
exposure lift for dark clips, punch-in zooms on alternate sentences, word-highlight
captions and a chapter title. Segments are concatenated losslessly, then the voice is
mixed with a ducked music bed and whooshes and normalised to -14 LUFS in two passes.
"""
import difflib, json, math, os, re, subprocess, sys, wave
from concurrent.futures import ThreadPoolExecutor
import numpy as np

WORK = os.path.abspath(os.environ.get('WORK', '.'))
FF = os.environ.get('FFMPEG', 'ffmpeg')
JOBS = int(os.environ.get('JOBS', '2'))
FPS, SR, W, H = 30, 48000, 1920, 1080
FG_W, FG_X = 608, (1920 - 608) // 2
ACCENT = '&H00F0E13A&'            # ASS colours are &HAABBGGRR -> cyan #3AE1F0
X264 = ['-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-pix_fmt', 'yuv420p',
        '-profile:v', 'high', '-r', str(FPS), '-g', str(FPS * 2), '-threads', '2']
OUT = os.path.join(WORK, 'out')
SEG = os.path.join(OUT, 'seg')


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"ffmpeg failed: {' '.join(cmd)}\n{p.stderr[-3000:]}")
    return p.stderr


def frames(d):
    return int(round(d * FPS))


# ---------------------------------------------------------------- transcripts
def norm(s):
    return re.sub(r"[^a-z0-9']", '', s.lower())


def load_words(vid, fixes=()):
    t = json.load(open(os.path.join(WORK, 'transcripts', f'{vid}.json')))
    words = [dict(start=w['start'], end=w['end'], text=w['word'].strip(), seg=i)
             for i, s in enumerate(t['segments']) for w in s['words'] if w['word'].strip()]
    for bad, good in fixes:                                  # fix mishearings, re-time evenly
        b = bad.split()
        i = 0
        while i <= len(words) - len(b):
            if [norm(w['text']) for w in words[i:i + len(b)]] == [norm(x) for x in b]:
                span = words[i:i + len(b)]
                trail = re.sub(r"^.*?([.,!?]*)$", r"\1", span[-1]['text'])
                g = good.split()
                t0, t1 = span[0]['start'], span[-1]['end']
                new = [dict(start=t0 + (t1 - t0) * k / len(g), end=t0 + (t1 - t0) * (k + 1) / len(g),
                            text=x, seg=span[0]['seg']) for k, x in enumerate(g)]
                if not re.search(r'[.,!?]$', new[-1]['text']):
                    new[-1]['text'] += trail
                words[i:i + len(b)] = new
                i += len(g)
            else:
                i += 1
    return words, t['duration']


def find(words, phrase, after=0.0):
    """Index range of the best fuzzy match for `phrase` starting at or after `after` seconds."""
    target = [norm(x) for x in phrase.split()]
    toks = [norm(w['text']) for w in words]
    best, best_i = 0.0, None
    for i in range(len(words) - len(target) + 1):
        if words[i]['start'] < after - 0.01:
            continue
        r = difflib.SequenceMatcher(None, ' '.join(toks[i:i + len(target)]), ' '.join(target)).ratio()
        if r > best:
            best, best_i = r, i
    if best < 0.75:
        sys.exit(f'phrase not found ({best:.2f}): {phrase!r}')
    return best_i, best_i + len(target) - 1


# ---------------------------------------------------------------- ASS helpers
def ass_time(t):
    t = max(0.0, t)
    return f'{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}'


ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Archivo Black,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H9A000000,0,0,0,0,100,100,1,0,1,5,3,2,120,120,205,1
Style: Big,Anton,104,&H00FFFFFF,&H00FFFFFF,&H00000000,&H9A000000,0,0,0,0,100,100,2,0,1,6,4,2,160,160,205,1
Style: ChapNo,Archivo Black,30,&H00F0E13A,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,9,0,1,0,2,7,0,0,0,1
Style: ChapTitle,Anton,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H9A000000,0,0,0,0,100,100,2,0,1,0,5,7,0,0,0,1
Style: BigNum,Anton,340,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Brand,Cinzel Decorative,30,&H00FFFFFF,&H00FFFFFF,&H00000000,&H9A000000,1,0,0,0,100,100,6,0,1,0,2,3,0,0,0,1
Style: Kicker,Cinzel Decorative,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,14,0,1,0,0,5,0,0,0,1
Style: Title,Anton,150,&H00FFFFFF,&H00FFFFFF,&H00000000,&H9A000000,0,0,0,0,100,100,3,0,1,0,6,5,0,0,0,1
Style: Sub,Archivo Black,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H9A000000,0,0,0,0,100,100,4,0,1,0,3,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ev(t0, t1, style, text, layer=0):
    return f'Dialogue: {layer},{ass_time(t0)},{ass_time(t1)},{style},,0,0,0,,{text}'


def esc(s):
    return s.replace('{', '(').replace('}', ')')


def caption_chunks(words, max_words=4, max_chars=22):
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        text = ' '.join(x['text'] for x in cur)
        if (nxt is None or len(cur) >= max_words or len(text) >= max_chars
                or re.search(r'[.,!?]$', w['text']) or nxt['start'] - w['end'] > 0.35):
            chunks.append(cur)
            cur = []
    return chunks


def caption_events(words, t0, t1, style='Cap', max_words=4, max_chars=22):
    """Word-by-word highlighted captions for words inside [t0, t1], re-timed to start at 0."""
    words = [w for w in words if w['start'] >= t0 - 0.05 and w['end'] <= t1 + 0.3]
    out, srt = [], []
    chunks = caption_chunks(words, max_words, max_chars)
    for ci, ch in enumerate(chunks):
        c_end = min(ch[-1]['end'] + 0.35, chunks[ci + 1][0]['start'] if ci + 1 < len(chunks) else t1)
        for k, w in enumerate(ch):
            a = w['start'] if k else ch[0]['start']
            b = ch[k + 1]['start'] if k + 1 < len(ch) else c_end
            parts = []
            for j, x in enumerate(ch):
                txt = esc(x['text'].upper())
                parts.append('{\\c%s\\fscx108\\fscy108}%s{\\c&H00FFFFFF&\\fscx100\\fscy100}' % (ACCENT, txt)
                             if j == k else txt)
            pop = '{\\fscx88\\fscy88\\t(0,90,\\fscx100\\fscy100)}' if k == 0 else ''
            out.append(ev(a - t0, b - t0, style, pop + ' '.join(parts), layer=5))
        srt.append((ch[0]['start'] - t0, c_end - t0, ' '.join(x['text'] for x in ch)))
    return out, srt


def wrap(title, width=11):
    lines, cur = [], ''
    for word in title.split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f'{cur} {word}'.strip()
    return lines + [cur]


def chapter_events(no, title, dur):
    e = [ev(0, dur, 'ChapNo', '{\\an7\\move(40,390,90,390,0,450)\\fad(350,0)}CHAPTER %02d' % no, 3),
         ev(0, dur, 'ChapTitle', '{\\an7\\move(40,440,90,440,60,520)\\fad(400,0)\\t(4500,5300,\\alpha&H55&)}'
            + '\\N'.join(esc(x) for x in wrap(title.upper())), 3),
         ev(0, dur, 'ChapNo', '{\\an7\\pos(90,430)\\p1\\fad(400,0)}m 0 0 l 140 0 l 140 6 l 0 6{\\p0}', 3),
         ev(0, dur, 'BigNum', '{\\an5\\pos(1592,560)\\alpha&HE8&\\fad(900,0)}%02d' % no, 1)]
    return e


def brand_events(dur, brand):
    return [ev(0, dur, 'Brand', '{\\an3\\pos(1872,1044)\\alpha&H50&}%s' % esc(brand.upper()), 2)] if brand else []


def write_ass(path, events):
    with open(path, 'w') as f:
        f.write(ASS_HEAD + '\n'.join(events) + '\n')


# ---------------------------------------------------------------- rendering
def gamma_for(clip):
    """Lift dark footage toward a mean luma of ~102/255 (capped so noise stays tolerable)."""
    err = run([FF, '-hide_banner', '-i', clip, '-vf',
               'fps=1,scale=144:256,signalstats,metadata=print:key=lavfi.signalstats.YAVG', '-f', 'null', '-'])
    vals = [float(x) for x in re.findall(r'YAVG=([\d.]+)', err)]
    m = max(8.0, sum(vals) / len(vals)) / 255
    return round(min(1.7, max(1.0, math.log(m) / math.log(0.40))), 2), round(m * 255)


def zoom_expr(words, t0, t1):
    """Punch in on every other sentence (Whisper segments), so long monologues keep moving."""
    spans = {}
    for w in words:
        if t0 <= w['start'] < t1:
            s = spans.setdefault(w['seg'], [w['start'], w['end']])
            s[1] = min(t1, w['end'])
    terms = [f'between(t,{a - t0:.2f},{b - t0 + 0.15:.2f})'
             for k, (a, b) in enumerate(spans[s] for s in sorted(spans)) if k % 2 == 1 and b - a >= 1.5]
    return '+'.join(terms)


def render_clip(idx, seg):
    d = seg['dur']
    nf, ns = frames(d), int(round(d * SR))
    ass = os.path.join(SEG, f'{idx:03d}.ass')
    events = list(seg['events'])
    write_ass(ass, events)
    zx = seg['zoom']
    split = 3 if zx else 2
    flash = f",fade=t=in:st=0:d={seg['flash']}:color=white" if seg['flash'] else ',fade=t=in:st=0:d=0.12'
    v = (f"[0:v]fps={FPS},scale=576:1024:flags=lanczos,setsar=1,hqdn3d=1.5:1.5:4:4,"
         f"eq=gamma={seg['gamma']}:contrast=1.05:saturation=1.08,split={split}[s1][s2]{'[s3]' if zx else ''};"
         f"[s1]scale=320:568,crop=320:180,gblur=sigma=9,eq=brightness=-0.10:saturation=1.3,"
         f"scale={W}:{H}:flags=bicubic,vignette=angle=PI/3.2,"
         f"drawbox=x={FG_X - 6}:y=0:w={FG_W + 12}:h={H}:color=0x8A5CFF@0.55:t=6[bg];"
         f"[s2]scale={FG_W}:{H}:flags=lanczos,unsharp=5:5:0.5[fg];"
         + (f"[s3]crop=484:860:46:49,scale={FG_W}:{H}:flags=lanczos,unsharp=5:5:0.5[fz];" if zx else '')
         + f"[bg][fg]overlay={FG_X}:0[c1];"
         + (f"[c1][fz]overlay={FG_X}:0:enable='{zx}'[c2];" if zx else '[c1]null[c2];')
         + f"[c2]ass='{ass}':fontsdir='{os.path.join(WORK, 'fonts')}'{flash},"
         f"fade=t=out:st={d - 0.2:.3f}:d=0.2,tpad=stop_mode=clone:stop_duration=1,"
         f"trim=end_frame={nf},setsar=1,format=yuv420p[v]")
    a = (f"[0:a]aresample={SR},highpass=f=80,afftdn=nr=8:nf=-40,"
         f"acompressor=threshold=-21dB:ratio=3:attack=6:release=150:makeup=2,"
         f"loudnorm=I=-16:TP=-2:LRA=9,aresample={SR},aformat=sample_fmts=s16:channel_layouts=stereo,"
         f"afade=t=in:st=0:d=0.04,afade=t=out:st={d - 0.15:.3f}:d=0.15,apad,atrim=end_sample={ns}[a]")
    run([FF, '-y', '-nostats', '-loglevel', 'error', '-ss', f"{seg['in']:.3f}", '-t', f'{d + 0.5:.3f}', '-i', seg['src'],
         '-filter_complex', v + ';' + a,
         '-map', '[v]', '-an', *X264, os.path.join(SEG, f'{idx:03d}.mp4'),
         '-map', '[a]', '-c:a', 'pcm_s16le', os.path.join(SEG, f'{idx:03d}.wav')])
    return idx


def render_card(idx, seg):
    d = seg['dur']
    nf, ns = frames(d), int(round(d * SR))
    ass = os.path.join(SEG, f'{idx:03d}.ass')
    write_ass(ass, seg['events'])
    x0 = seg.get('pan_x', 60)
    v = (f"[0:v]crop={W}:{H}:x='{x0}+t*14':y='(ih-{H})/2+t*3',eq=brightness=-0.03,"
         f"ass='{ass}':fontsdir='{os.path.join(WORK, 'fonts')}',"
         f"fade=t=in:st=0:d=0.5,fade=t=out:st={d - 0.6:.3f}:d=0.6,trim=end_frame={nf},setsar=1,format=yuv420p[v]")
    run([FF, '-y', '-nostats', '-loglevel', 'error', '-loop', '1', '-framerate', str(FPS),
         '-i', os.path.join(WORK, 'assets', 'starfield.png'),
         '-f', 'lavfi', '-i', f'anullsrc=r={SR}:cl=stereo',
         '-filter_complex', v + f';[1:a]atrim=end_sample={ns},aformat=sample_fmts=s16[a]',
         '-map', '[v]', '-an', *X264, '-t', f'{d:.3f}', os.path.join(SEG, f'{idx:03d}.mp4'),
         '-map', '[a]', '-c:a', 'pcm_s16le', '-t', f'{d:.3f}', os.path.join(SEG, f'{idx:03d}.wav')])
    return idx


# ---------------------------------------------------------------- planning
def build(plan):
    segs, chapter_no, gammas = [], 0, {}
    for item in plan['segments']:
        if item['type'] == 'card':
            d = item['dur']
            L = item['lines']
            if item['kind'] == 'title':
                ev_ = [ev(0.2, d, 'Kicker', '{\\an5\\pos(960,372)\\fad(700,300)\\alpha&H20&}%s' % esc(L['kicker'].upper()), 2),
                       ev(0.9, d, 'Title', '{\\an5\\pos(960,540)\\blur14\\1c%s\\3c%s\\bord8\\alpha&H70&\\fad(250,300)}%s'
                          % (ACCENT, ACCENT, esc(L['title'])), 1),
                       ev(0.9, d, 'Title', '{\\an5\\pos(960,540)\\fscx122\\fscy122\\t(0,450,\\fscx100\\fscy100)'
                          '\\fad(250,300)}%s' % esc(L['title']), 2),
                       ev(1.6, d, 'Sub', '{\\an5\\pos(960,672)\\fad(500,300)}%s' % esc(L['sub'].upper()), 2)]
            else:
                ev_ = [ev(0.3, d, 'Title', '{\\an5\\pos(960,190)\\fscx70\\fscy70\\fad(500,500)}%s' % esc(L['title']), 2),
                       ev(1.0, d, 'Sub', '{\\an5\\pos(960,300)\\fad(500,500)}%s' % esc(L['sub'].upper()), 2),
                       ev(1.6, d, 'Kicker', '{\\an5\\pos(960,960)\\fad(600,500)\\alpha&H30&}%s' % esc(L['foot']), 2)]
            segs.append(dict(kind='card', dur=d, events=ev_, pan_x=item.get('pan_x', 60),
                             label=item.get('label', item['kind']), sfx=item.get('sfx')))
            continue
        vid = item['clip']
        src = os.path.join(WORK, 'clips', f'{vid}.mp4')
        words, clip_dur = load_words(vid, item.get('fixes', []))
        t0 = words[find(words, item['in'])[0]]['start'] - 0.12 if item.get('in') else 0.0
        t1 = (words[find(words, item['out'], after=t0)[1]]['end'] + 0.45) if item.get('out') \
            else min(clip_dur, words[-1]['end'] + 0.6)
        t0 = max(0.0, t0)
        d = frames(t1 - t0) / FPS
        if vid not in gammas:
            gammas[vid] = gamma_for(src)
        events, srt = [], []
        style = item.get('style', 'cap')
        if item.get('captions', True):
            if style == 'big':
                events, srt = caption_events(words, t0, t0 + d, 'Big', max_words=7, max_chars=34)
            else:
                events, srt = caption_events(words, t0, t0 + d)
        chapter = item.get('chapter')
        if chapter:
            chapter_no += 1
            events += chapter_events(chapter_no, chapter, d)
        if style != 'big':
            events += brand_events(d, plan.get('brand', ''))
        segs.append(dict(kind='clip', src=src, vid=vid, **{'in': t0}, dur=d, events=events, srt=srt,
                         zoom=zoom_expr(words, t0, t0 + d) if item.get('zoom', True) else '',
                         gamma=gammas[vid][0], flash=item.get('flash', 0.3 if chapter else 0),
                         chapter=chapter, chapter_no=chapter_no if chapter else None,
                         label=chapter or item.get('label', vid), sfx=item.get('sfx', 'whoosh' if chapter else None)))
    return segs, gammas


# ---------------------------------------------------------------- audio
def read_wav(path):
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32768
        return x.reshape(-1, w.getnchannels())


def write_wav(path, x):
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


def music_and_sfx(segs, total):
    """Music bed (loud on cards, low under speech) plus whooshes/booms at the cuts."""
    n = int(round(total * SR))
    pad = read_wav(os.path.join(WORK, 'assets', 'pad_loop.wav'))
    sfx = {k: read_wav(os.path.join(WORK, 'assets', f'{k}.wav')) for k in ('whoosh', 'boom')}
    pts, t = [], 0.0
    for s in segs:
        g = 0.85 if s['kind'] == 'card' else 0.24
        pts += [(t, g), (t + s['dur'], g)]
        t += s['dur']
    pts[-1] = (total, 0.0)
    pts.insert(-1, (total - 3.0, 0.85))                         # fade the bed out over the last 3 s
    bt, bg = zip(*pts)
    ct = np.arange(0, total + 0.01, 0.01)                        # 100 Hz gain envelope, 0.6 s ramps
    cg = np.convolve(np.pad(np.interp(ct, bt, bg), 30, mode='edge'), np.ones(61) / 61, 'valid')
    out = np.zeros((n, 2), np.float32)
    step = SR * 10
    for a in range(0, n, step):
        b = min(n, a + step)
        idx = np.arange(a, b)
        out[a:b] = pad[idx % len(pad)] * np.interp(idx / SR, ct, cg).astype(np.float32)[:, None]
    t = 0.0
    for s in segs:
        kind = s.get('sfx')
        if kind:
            clip = sfx[kind]
            at = int(max(0.0, t - (0.41 if kind == 'whoosh' else -0.1)) * SR)
            e = min(n, at + len(clip))
            out[at:e] += clip[:e - at] * (0.55 if kind == 'whoosh' else 0.9)
        t += s['dur']
    write_wav(os.path.join(OUT, 'bed_sfx.wav'), out)


def main():
    plan = json.load(open(sys.argv[1]))
    os.makedirs(SEG, exist_ok=True)
    segs, gammas = build(plan)
    total = sum(s['dur'] for s in segs)
    print(f'{len(segs)} segments, {total / 60:.1f} min; gamma per clip: '
          + ', '.join(f'..{k[-5:]}:{g}(Y{y})' for k, (g, y) in gammas.items()), flush=True)
    for i, s in enumerate(segs):
        print(f"  {i:03d} {s['label'][:30]:30} in={s.get('in', 0):6.2f} dur={s['dur']:6.2f}", flush=True)
    only = os.environ.get('ONLY')
    todo = [i for i in range(len(segs)) if only is None or str(i) in only.split(',')]
    if os.environ.get('RESUME'):                                 # keep segments already rendered
        todo = [i for i in todo if not all(os.path.exists(os.path.join(SEG, f'{i:03d}.{x}')) for x in ('mp4', 'wav'))]
    with ThreadPoolExecutor(JOBS) as pool:
        for i in pool.map(lambda i: (render_clip if segs[i]['kind'] == 'clip' else render_card)(i, segs[i]), todo):
            print(f'  rendered {i:03d} {segs[i]["label"]} ({segs[i]["dur"]:.1f}s)', flush=True)
    if only:
        return
    with open(os.path.join(OUT, 'v.txt'), 'w') as fv, open(os.path.join(OUT, 'a.txt'), 'w') as fa:
        for i in range(len(segs)):
            fv.write(f"file '{SEG}/{i:03d}.mp4'\n")
            fa.write(f"file '{SEG}/{i:03d}.wav'\n")
    run([FF, '-y', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/v.txt', '-c', 'copy', f'{OUT}/body_video.mp4'])
    run([FF, '-y', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/a.txt', '-c', 'copy', f'{OUT}/body_voice.wav'])
    music_and_sfx(segs, total)
    mix = (f"[0:a]asplit=2[v1][v2];[1:a][v2]sidechaincompress=threshold=0.03:ratio=3:attack=25:release=600[bd];"
           f"[v1][bd]amix=inputs=2:normalize=0[m]")
    run([FF, '-y', '-i', f'{OUT}/body_voice.wav', '-i', f'{OUT}/bed_sfx.wav', '-filter_complex', mix,
         '-map', '[m]', '-c:a', 'pcm_s16le', f'{OUT}/premix.wav'])
    stats = run([FF, '-hide_banner', '-i', f'{OUT}/premix.wav', '-af',
                 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'])
    m = json.loads(stats[stats.rindex('{'):stats.rindex('}') + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    run([FF, '-y', '-i', f'{OUT}/body_video.mp4', '-i', f'{OUT}/premix.wav', '-af', f'{ln},aresample={SR}',
         '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart',
         '-metadata', f"title={plan['title']}", f'{OUT}/{plan["output"]}'])
    # YouTube chapters + an SRT of the corrected captions (optional CC upload)
    t, chap, srt = 0.0, [], []
    for s in segs:
        if s.get('chapter'):
            chap.append((t, f"{s['chapter_no']:02d}. {s['chapter'].title()}"))
        elif s['kind'] == 'card' and s['label'] == 'outro':
            chap.append((t, 'Outro'))
        for a, b, txt in s.get('srt', []):
            srt.append((t + max(0, a), t + min(s['dur'], b), txt))
        t += s['dur']
    fmt = lambda x: f'{int(x // 60)}:{int(x % 60):02d}'
    with open(f'{OUT}/chapters.txt', 'w') as f:
        f.write('0:00 Intro\n' + ''.join(f'{fmt(a)} {b}\n' for a, b in chap))
    st = lambda x: f'{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(x * 1000 % 1000):03d}'
    with open(f'{OUT}/captions.srt', 'w') as f:
        f.write(''.join(f'{i}\n{st(a)} --> {st(b)}\n{txt}\n\n' for i, (a, b, txt) in enumerate(srt, 1)))
    print(f'done: {OUT}/{plan["output"]}  ({total / 60:.1f} min)')


if __name__ == '__main__':
    main()
