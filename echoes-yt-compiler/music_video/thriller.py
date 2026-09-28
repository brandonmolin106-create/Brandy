#!/usr/bin/env python3
"""Thriller cut of the music video: title cards on black, key-word eye close-ups, glitch and flash hits
synced to the sound design, film subtitles in the letterbox bar, and a harder mix.

    WORK=<work dir> FFMPEG=<ffmpeg> python3 music_video/thriller.py

Run timeline.py, score.py and thriller_audio.py first. Writes
$WORK/mv/brandon_molina_nothing_becomes_everything_THRILLER.mp4.
"""
import json, os, re, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import visuals as V  # noqa: E402

MV = V.MV
FPS, W, IH, PW = V.FPS, V.W, V.IH, V.PW
GRADE = {'intro': 'thr_bw', 'time': 'thr_bw', 'hole': 'thr_bleach', 'glass': 'thr_cold', 'road': 'thr_bleach',
         'riser': 'thr_red', 'chains': 'thr_red', 'everything': 'thr_sepia', 'outro': 'thr_bw'}
# teaser cards: each is a line Brandon says later in that section
CARD = {'hole': 'YOUR THOUGHTS\\NKEPT DIGGING', 'glass': 'THE BOX IS MADE\\NIN YOUR MIND',
        'road': 'IT MEANS\\NYOU WALKED FAR', 'everything': 'YOU WERE WALKING\\NTHE WHOLE TIME'}


# punctuation the transcript dropped (same word count on both sides, so timings stay aligned)
PUNCT = [('walk you will stay', 'walk, you will stay'), ('same place if you never run you', 'same place. If you never run, you'),
         ('could have gone', 'could have gone.'), ('body could have left', 'body could have left.'),
         ('right now don\'t stay the same or', 'right now, don\'t stay the same, or'), ('become your name', 'become your name.')]


def punctuate(words):
    words = [dict(w) for w in words]
    toks = [w['text'] for w in words]
    for old, new in PUNCT:
        o, n = old.split(), new.split()
        for i in range(len(toks) - len(o) + 1):
            if [t.lower() for t in toks[i:i + len(o)]] == [t.lower() for t in o]:
                for j, t in enumerate(n):
                    toks[i + j] = words[i + j]['text'] = t
    return words


def subtitle_cards(lines, max_row=42):
    """Film subtitles: at most two balanced rows, split at sentence ends, then commas, then length."""
    cards = []
    for l in lines:
        cur = []
        words = punctuate(l['words'])
        cards.append(None)                                     # marks a new spoken line (sentence start)
        for k, w in enumerate(words):
            cur.append(w)
            text = ' '.join(x['text'] for x in cur)
            last = k == len(words) - 1
            rest = len(' '.join(x['text'] for x in words[k + 1:]))
            if last or rest > 14 and ((re.search(r'[.?!]$', w['text']) and len(text) > 18) or
                                      (w['text'].endswith(',') and len(text) > 48) or len(text) > 2 * max_row - 8):
                cards.append([cur[0]['start'] - 0.05, cur[-1]['end'] + 0.35, text])
                cur = []
    starts, flat, fresh = [], [], True
    for c in cards:
        if c is None:
            fresh = True
            continue
        starts.append(fresh or bool(re.search(r'[.?!]$', flat[-1][2])) if flat else True)
        flat.append(c)
        fresh = False
    for a, b in zip(flat, flat[1:]):
        a[1] = min(a[1], b[0] - 0.03)
    out = []
    for (a, b, text), cap in zip(flat, starts):
        text = (text[0].upper() + text[1:]) if cap else text
        if len(text) > max_row:                                # balance two rows at the space nearest the middle
            mid = len(text) // 2
            cut = min((i for i, c in enumerate(text) if c == ' '), key=lambda i: abs(i - mid))
            text = text[:cut] + '\\N' + text[cut + 1:]
        out.append((a, b, V.esc(text)))
    return out


def build(tl, cues):
    lines, secs = tl['lines'], {s['name']: s for s in tl['sections']}
    beat, bar = 60 / tl['bpm'], tl['bar']
    subs = subtitle_cards(lines)
    shots, gam = [], {}

    def gamma(clip):
        if clip not in gam:
            gam[clip] = V.gamma_for(f'{V.WORK}/clips/{clip}.mp4')[0]
        return gam[clip]

    def add(t0, t1, **kw):
        if t1 - t0 <= 0.04:
            return
        ev = kw.pop('events', [])
        for f in cues['flashes']:                              # white flash on every hit inside the shot
            if t0 <= f < t1:
                ev.append(V.flash(f - t0, 0.14, '38'))
        for r in cues['red']:
            if t0 <= r < t1:
                ev.append(V.dlg(r - t0, r - t0 + 0.45, 'Flash', '{\\an7\\pos(0,0)\\c&H0010D0&\\alpha&H20&\\fad(0,420)'
                                '\\p1}m 0 0 l %d 0 l %d %d l 0 %d{\\p0}' % (W, W, IH, IH), 9))
        sb = [V.dlg(max(a, t0) - t0, min(b, t1) - t0, 'Sub', text, 1) for a, b, text in subs if a < t1 and b > t0]
        gl = [(max(t, t0) - t0, min(t + d, t1) - t0) for t, d in cues['glitches'] if t < t1 and t + d > t0]
        shots.append(dict(t0=t0, dur=t1 - t0, events=ev, subs=sb, glitch=gl, grain=8,
                          dust=kw.pop('dust', 0.35), **kw))

    def clip_shot(section, t0, t1, clip, src, kind='portrait', slow=1.0, **kw):
        kw.setdefault('grade', GRADE[section])
        if kind == 'portrait':
            kw.setdefault('x', W // 2 - PW // 2)
            kw.setdefault('bg_bright', -0.42)
        add(t0, t1, kind=kind, clip=clip, src=src, gamma=gamma(clip), slow=slow, eye=V.eye_line(clip, src + 1), **kw)

    def title_card(section, t0, t1, text, size=110):
        ev = [V.dlg(0.05, t1 - t0, 'Title', '{\\an5\\pos(960,402)\\fs%d\\fsp14\\blur1.5\\fad(60,380)'
                    '\\t(0,%d,\\fscx104\\fscy104)}%s' % (size, int((t1 - t0) * 1000), text), 2)]
        add(t0, t1, kind='space', grade=GRADE[section], events=ev, bright=-0.62, pan_v=6, dust=0.25)

    def key_windows(l, t0):
        wins = []
        for key in l['keys']:
            for w in l['words']:
                if w['text'].upper().strip('.,!?') == key:
                    a, b = w['start'] - 0.08 - t0, w['end'] + 0.32 - t0
                    if all(b < x or a > y + 0.9 for x, y in wins):
                        wins.append((a, b))
                    break
        return sorted(wins)[:2]

    by_sec = {n: [l for l in lines if l['section'] == n] for n in secs}
    last_chain = max(l['end'] for l in by_sec['chains'])
    montage = np.ceil((last_chain + 0.6) / bar) * bar            # same grid thriller_audio.py puts the hits on
    for name, s in secs.items():
        ls, t = by_sec[name], s['start']
        if name == 'intro':
            ev = [V.dlg(1.2, 9.0, 'Kicker', '{\\an5\\pos(960,300)\\fad(1400,900)}BRANDON MOLINA', 2),
                  V.dlg(3.0, 9.4, 'Title', '{\\an5\\pos(960,450)\\fs96\\fad(40,1000)}NOTHING BECOMES\\NEVERYTHING', 2)]
            add(t, t + 9.43, kind='space', grade='thr_bw', events=ev, fin=2.5, pan_v=6, bright=-0.35)
            clip_shot(name, t + 9.43, s['end'], by_sec['time'][0]['clip'], 3.0, slow=0.5)
            continue
        if name == 'riser':                                     # accelerating eye cuts, red flashes, then black
            src_clip = by_sec['chains'][0]['clip']
            for k, nb in enumerate([2, 2, 1, 1, 0.5, 0.5, 0.5, 0.5]):
                a, t = t, min(s['end'] - 0.35, t + nb * beat)
                clip_shot(name, a, t, src_clip, 10 + k * 3.1, kind='ecu', shake=k > 3,
                          events=[V.dlg(0, 0.08, 'Flash', '{\\an7\\pos(0,0)\\c&H0010D0&\\alpha&H40&\\p1}'
                                        'm 0 0 l %d 0 l %d %d l 0 %d{\\p0}' % (W, W, IH, IH), 9)])
            add(t, s['end'], kind='space', grade='thr_bw', bright=-0.95, dust=0.0)
            continue
        if name == 'outro':
            stop = tl['total'] - 2 * bar - t
            final = cues['hits'][-1] - t
            ev = [V.dlg(0.8, stop, 'Title', '{\\an5\\pos(960,402)\\fs96\\fad(1500,900)}NOTHING BECOMES\\NEVERYTHING', 2),
                  V.dlg(final, s['end'] - t - 0.2, 'Kicker', '{\\an5\\pos(960,402)\\fs46\\fad(30,1800)}BRANDON MOLINA', 2)]
            add(t, s['end'], kind='space', grade='thr_bw', events=ev, fout=2.5, pan_v=5, bright=-0.4)
            continue
        if ls and ls[0]['start'] - t > 0.3:                     # the bar before the first line
            if name == 'chains':
                ev = [V.dlg(0, ls[0]['start'] - t, 'Slam', '{\\an5\\pos(960,402)\\fscx140\\fscy140'
                                                     '\\t(0,140,\\fscx100\\fscy100)\\fad(0,300)}MOVE.', 5)]
                clip_shot(name, t, ls[0]['start'], ls[0]['clip'], max(0.0, ls[0]['src_in'] - 3.5), kind='ecu',
                          shake=True, events=ev)
            else:
                title_card(name, t, ls[0]['start'], CARD[name])
        for k, l in enumerate(ls):
            nxt = ls[k + 1]['start'] if k + 1 < len(ls) else None
            a = l['start']
            b = nxt if nxt else (montage if name == 'chains' else min(s['end'], l['end'] + 0.9))
            clip_shot(name, a, b, l['clip'], l['src_in'], ecu_win=key_windows(l, a),
                      shake=name == 'chains', glow=name == 'everything', leak=0.18 if name == 'everything' else 0)
            t = b
        if t < s['end'] - 0.04:
            if name == 'chains':                                # post-drop montage, a slam on every bar
                words, k = ['WALK.', 'RUN.', 'MOVE.', 'GROW.'], 0
                src_clip, alt = by_sec['chains'][0]['clip'], by_sec['road'][0]['clip']
                while t < s['end'] - 0.04:
                    a, t = t, min(s['end'], t + 2 * beat)
                    ev = []
                    if k % 2 == 0:
                        ev.append(V.dlg(0, 2 * beat * 2, 'Slam', '{\\an5\\pos(960,402)\\fscx135\\fscy135'
                                        '\\t(0,150,\\fscx100\\fscy100)\\fad(0,250)}%s' % words[(k // 2) % 4], 5))
                    clip_shot(name, a, t, src_clip if k % 3 else alt, 20 + k * 2.3, kind='ecu', shake=True, events=ev)
                    k += 1
            elif name == 'everything':
                add(t, s['end'], kind='space', grade='thr_sepia', pan_v=8, bright=-0.3, leak=0.2)
            else:
                clip_shot(name, t, s['end'], ls[-1]['clip'], ls[-1]['src_out'] + 0.5, kind='ecu', slow=0.5)
    return shots


def mix(tl, video, out):
    V.run([V.FF, '-y', '-nostats', '-loglevel', 'error', '-i', f'{MV}/thriller_voice.wav', '-i', f'{MV}/voice_dry.wav',
           '-i', f'{MV}/thriller_score.wav', '-i', f'{MV}/thriller_sfx.wav', '-filter_complex',
           '[1:a]asplit=2[k1][k2];'
           '[2:a][k1]sidechaincompress=threshold=0.025:ratio=4:attack=20:release=450[sc];'
           '[3:a][k2]sidechaincompress=threshold=0.03:ratio=2:attack=10:release=300[fx];'
           "[0:a][sc][fx]amix=inputs=3:normalize=0:weights='1 0.85 0.7',"
           f"alimiter=limit=0.89:attack=4:release=90:level=disabled,atrim=0:{tl['total']:.3f}[m]",
           '-map', '[m]', '-c:a', 'pcm_f32le', f'{MV}/thriller_premix.wav'])
    st = V.run([V.FF, '-hide_banner', '-i', f'{MV}/thriller_premix.wav', '-af',
                'loudnorm=I=-14:TP=-1.5:LRA=14:print_format=json', '-f', 'null', '-'])
    m = json.loads(st[st.rindex('{'):st.rindex('}') + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=14:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    V.run([V.FF, '-y', '-nostats', '-loglevel', 'error', '-i', video, '-i', f'{MV}/thriller_premix.wav',
           '-af', f'{ln},aresample=48000', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-bsf:v',
           'h264_metadata=sample_aspect_ratio=1/1', '-c:a', 'aac', '-b:a', '256k', '-shortest',
           '-movflags', '+faststart', out])


def main():
    tl = json.load(open(f'{MV}/timeline.json'))
    cues = json.load(open(f'{MV}/thriller_cues.json'))
    V.SH = os.path.join(MV, 'shots_thriller')
    os.makedirs(V.SH, exist_ok=True)
    V.make_layers()
    shots = build(tl, cues)
    for s in shots:
        s['nf'] = int(round((s['t0'] + s['dur']) * FPS)) - int(round(s['t0'] * FPS))
    print(f"{len(shots)} shots, {sum(s['nf'] for s in shots) / FPS:.2f}s (timeline {tl['total']:.2f}s)", flush=True)
    for i, s in enumerate(shots):
        print(f"  {i:03d} {s['t0']:7.2f} {s['kind']:8} {s['grade']:10} {s['nf']:4d}f ecu={len(s.get('ecu_win', []))}"
              f" subs={len(s['subs'])} glitch={len(s['glitch'])}", flush=True)
    only = os.environ.get('ONLY')
    todo = [i for i in range(len(shots)) if (only is None or str(i) in only.split(','))
            and (only or not os.path.exists(f'{V.SH}/{i:03d}.mp4'))]
    with ThreadPoolExecutor(int(os.environ.get('JOBS', '3'))) as pool:
        for i in pool.map(lambda i: V.render(i, shots[i]), todo):
            print(f"  shot {i:03d} {shots[i]['kind']:8} {shots[i]['dur']:5.2f}s", flush=True)
    if only:
        return
    with open(f'{MV}/shots_thriller.txt', 'w') as f:
        f.writelines(f"file '{V.SH}/{i:03d}.mp4'\n" for i in range(len(shots)))
    V.run([V.FF, '-y', '-nostats', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{MV}/shots_thriller.txt',
           '-c', 'copy', f'{MV}/thriller_video_only.mp4'])
    out = f'{MV}/brandon_molina_nothing_becomes_everything_THRILLER.mp4'
    mix(tl, f'{MV}/thriller_video_only.mp4', out)
    print('done:', out)


if __name__ == '__main__':
    main()
