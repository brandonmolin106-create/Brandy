"""Burn captions + brand mark onto the rendered master and encode the deliverables in one pass.

usage: python overlay.py WORK CAPTIONS.txt WORDS.json OUTDIR
  reads  WORK/video_master.mp4 (render without overlays) and WORK/audio/mix.wav
  writes OUTDIR/EchoesInTheDark_FishInTheCup_MASTER.mp4 and ..._TikTok.mp4
"""
import json
import re
import subprocess
import sys
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from subtitles import Subtitles

W, H, FPS = 1080, 1920, 30
NO_CAPTIONS = [(217.8, 220.6), (357.3, 1e9)]  # 3D words replace captions / end card


def norm(tok):
    return re.sub(r"[^a-z0-9']", '', tok.lower())


def align(captions_path, words):
    """Map hand-written caption lines onto the word-timed transcript (must match word for word)."""
    lines = [ln.strip() for ln in open(captions_path) if ln.strip() and not ln.startswith('#')]
    wi = 0
    phrases = []
    for ln in lines:
        items = []
        for tok in ln.split():
            key = '*' in tok
            disp = tok.replace('*', '')
            n = norm(disp)
            if wi >= len(words) or norm(words[wi]['w']) != n:
                ctx = ' '.join(w['w'] for w in words[max(0, wi - 3):wi + 4])
                raise ValueError(f'caption "{ln}" token "{tok}" != transcript word #{wi} near: {ctx}')
            disp = disp.rstrip('.,;:')
            items.append({'w': disp, 's': words[wi]['s'], 'e': words[wi]['e'], 'key': key})
            wi += 1
        phrases.append({'start': items[0]['s'], 'end': items[-1]['e'], 'words': items})
    if wi != len(words):
        raise ValueError(f'captions cover {wi} of {len(words)} words')
    return phrases


def brand_sprite():
    f = ImageFont.truetype('/opt/fonts/Cinzel.ttf', 38)
    try:
        f.set_variation_by_name('Bold')
    except Exception:
        pass
    img = Image.new('L', (700, 80), 0)
    ImageDraw.Draw(img).text((350, 40), 'ECHOES  IN  THE  DARK', font=f, fill=255, anchor='mm')
    return np.asarray(img, np.float32) / 255


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def draw_brand(img, s, t):
    a = smooth((t - 0.6) / 0.8) * (1 - smooth((t - 3.6) / 0.8))
    if a <= 0.01:
        return
    y0, x0 = 190, (W - s.shape[1]) // 2
    reg = img[y0:y0 + s.shape[0], x0:x0 + s.shape[1]].astype(np.float32)
    glow = cv2.GaussianBlur(s, (0, 0), 6) * 0.6
    reg = reg + glow[..., None] * np.array([255, 150, 60], np.float32) * 0.5 * a
    reg = reg * (1 - s[..., None] * a * 0.9) + np.array([255, 214, 150], np.float32) * s[..., None] * a * 0.9
    img[y0:y0 + s.shape[0], x0:x0 + s.shape[1]] = np.clip(reg, 0, 255).astype(np.uint8)


def main():
    work, cap_path, words_path, outdir = sys.argv[1:5]
    words = json.load(open(words_path))
    phrases = align(cap_path, words)
    print(f'{len(phrases)} caption lines aligned to {len(words)} words', flush=True)
    if len(sys.argv) > 5 and sys.argv[5] == 'check':
        return
    subs = Subtitles(phrases)
    brand = brand_sprite()
    src = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', f'{work}/video_master.mp4', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           stdout=subprocess.PIPE, bufsize=W * H * 3 * 2)
    common = ['-c:a', 'aac', '-ar', '48000', '-movflags', '+faststart', '-shortest']
    enc = subprocess.Popen([
        'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
        '-i', f'{work}/audio/mix.wav',
        '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-profile:v', 'high',
        '-pix_fmt', 'yuv420p', '-b:a', '320k', *common, f'{outdir}/EchoesInTheDark_FishInTheCup_MASTER.mp4',
        '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-maxrate', '12M',
        '-bufsize', '24M', '-profile:v', 'high', '-level', '4.2', '-pix_fmt', 'yuv420p', '-g', '60', '-b:a', '256k',
        *common, f'{outdir}/EchoesInTheDark_FishInTheCup_TikTok.mp4'], stdin=subprocess.PIPE)
    n = W * H * 3
    fi = 0
    t0 = time.time()
    while True:
        buf = src.stdout.read(n)
        if len(buf) < n:
            break
        img = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
        t = fi / FPS
        draw_brand(img, brand, t)
        if not any(a < t < b for a, b in NO_CAPTIONS):
            subs.draw(img, t)
        enc.stdin.write(img.tobytes())
        fi += 1
        if fi % 900 == 0:
            print(f'{fi} frames ({fi / FPS:.0f}s) {(time.time() - t0) / fi * 1000:.0f} ms/frame', flush=True)
    enc.stdin.close()
    enc.wait()
    src.wait()
    print('done', fi, 'frames', flush=True)


if __name__ == '__main__':
    main()
