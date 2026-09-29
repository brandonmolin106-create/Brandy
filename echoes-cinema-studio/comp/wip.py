"""Work-in-progress cut: finished segments + first-pass renders, black 'RENDERING' cards for the rest, real soundtrack.

usage: python wip.py WORK/cine OUTDIR
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from cinema import FPS, Compositor, segments

W, H = 1080, 1920


def card(path, label):
    img = Image.new('RGB', (W, H), (4, 4, 6))
    d = ImageDraw.Draw(img)
    f1 = ImageFont.truetype('/opt/fonts/Anton.ttf', 70)
    f2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 34)
    d.text((W / 2, H * 0.45), 'RENDERING', font=f1, fill=(200, 30, 25), anchor='mm')
    d.text((W / 2, H * 0.45 + 80), label, font=f2, fill=(150, 155, 165), anchor='mm')
    img.save(path)


def main():
    cine, out = sys.argv[1], sys.argv[2]
    os.makedirs(f'{cine}/wip', exist_ok=True)
    comp = Compositor(cine)
    lst = []
    for k, f0, f1, s in segments(comp):
        final, wip = f'{cine}/segs/seg_{k:03d}.mp4', f'{cine}/wip/seg_{k:03d}.mp4'
        if os.path.exists(final):
            lst.append(final)
            continue
        if not os.path.exists(wip):
            png = f'{cine}/wip/card_{k:03d}.png'
            card(png, s['src'].replace('_', ' ').upper())
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-r', str(FPS), '-i', png, '-frames:v',
                            str(f1 - f0), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
                            wip], check=True)
        lst.append(wip)
    with open(f'{cine}/wip/list.txt', 'w') as fh:
        for p in lst:
            fh.write(f"file '{p}'\n")
    os.makedirs(out, exist_ok=True)
    full = f'{cine}/wip/wip_full.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{cine}/wip/list.txt',
                    '-i', f'{cine}/audio/thriller_mix.wav', '-map', '0:v', '-map', '1:a',
                    '-vf', 'scale=720:1280:flags=lanczos', '-c:v', 'libx264', '-preset', 'medium', '-crf', '25',
                    '-maxrate', '1050k', '-bufsize', '2100k', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
                    '-movflags', '+faststart', '-shortest', full], check=True)
    for part, ss in ((1, 0), (2, 183)):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(ss), '-t', '183', '-i', full, '-c', 'copy',
                        '-movflags', '+faststart', f'{out}/EchoesInTheDark_Thriller_WIP_part{part}.mp4'], check=True)
    print('done', flush=True)


if __name__ == '__main__':
    main()
