"""Extract Brandon's source video as 1080x1920 frames for the tape shots.

The TikTok source has a burned-in caption box at the top and black bands at the bottom that move over time,
so every frame is re-framed to the live picture: top fixed under the caption box, bottom tracks the content edge
(median-smoothed so the reframe never jitters).
usage: python face_frames.py SRC.mp4 OUTDIR
"""
import os
import subprocess
import sys

import cv2
import numpy as np

SW, SH = 720, 1280
TOP = 215


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         stdout=subprocess.PIPE)
    n = SW * SH * 3
    frames, bottoms, tops = [], [], []
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        f = np.frombuffer(b, np.uint8).reshape(SH, SW, 3)
        live = f.max(axis=(1, 2)) > 14
        rows = np.where(live)[0]
        bottoms.append(rows.max() if len(rows) else SH - 1)
        # black gap under the burned-in caption box -> start below it
        gap = np.where(~live[TOP:420])[0]
        tops.append(TOP + gap.max() + 1 if len(gap) else TOP)
        frames.append(cv2.imencode('.png', f)[1])      # keep lossless until the crop is known
    bt = np.array(bottoms, np.float32)
    k = 9
    pad = np.pad(bt, k, mode='edge')
    sm = np.array([np.median(pad[i:i + 2 * k + 1]) for i in range(len(bt))])
    sm = np.clip(sm - 6, 1040, 1118)
    tp = np.array(tops, np.float32)
    pad = np.pad(tp, k, mode='edge')
    tsm = np.array([np.max(pad[i:i + 2 * k + 1]) for i in range(len(tp))]) + 4
    for i, (enc, bot, top) in enumerate(zip(frames, sm, tsm)):
        f = cv2.imdecode(enc, cv2.IMREAD_COLOR)
        top = int(top)
        h = int(bot - top)
        w = int(round(h * 9 / 16))
        x0 = (SW - w) // 2
        crop = f[top:top + h, x0:x0 + w]
        img = cv2.resize(crop, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
        cv2.imwrite(f'{out}/f_{i + 1:05d}.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 93])
    print(len(frames), 'frames; crop height range', sm.min(), sm.max())


if __name__ == '__main__':
    main()
