"""Render "The Fish in the Cup" (Echoes in the Dark).

usage:
  python render.py WORK preview T1,T2,...  OUT.jpg     # contact sheet of single frames
  python render.py WORK chunk F0 F1 OUT.mp4            # encode frames [F0, F1)
"""
import json
import math
import sys
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import render_core as rc
from avatar import Bust, Performance
from director import FPS, Compositor, Encoder, dissolve
from subtitles import Subtitles, build_phrases
from timeline import Assets, Shots, build_timeline, key_filter, smooth
from elements import rot_y

DURATION = 365.0


class Renderer:
    def __init__(self, work):
        self.work = work
        self.bust = Bust(f'{work}/bust.npz')
        self.perf = Performance(f'{work}/perf_capture.npz', self.bust, duration=DURATION)
        self.energy = np.load(f'{work}/energy.npy')
        self.A = Assets()
        self.S = Shots(self.A, self.energy)
        self.tl = build_timeline(self.S)
        import os
        from overlay import align
        cap = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'productions/fish-in-the-cup/captions.txt')
        words = json.load(open(f'{work}/words.json'))
        self.subs = Subtitles(align(cap, words) if os.path.exists(cap) else build_phrases(key_filter(words), max_words=4))
        self.comp = Compositor()
        self._looks = {}
        self.seed = np.random.default_rng(17).random(2_000_000).astype(np.float32)
        self._brand = self._brand_sprite()

    def _brand_sprite(self):
        f = ImageFont.truetype('/opt/fonts/Cinzel.ttf', 38)
        try:
            f.set_variation_by_name('Bold')
        except Exception:
            pass
        img = Image.new('L', (700, 80), 0)
        ImageDraw.Draw(img).text((350, 40), 'ECHOES  IN  THE  DARK', font=f, fill=255, anchor='mm')
        a = np.asarray(img, np.float32) / 255
        return a

    def energy_at(self, t):
        i = int(t * FPS)
        return float(self.energy[min(max(i, 0), len(self.energy) - 1)])

    def look(self, name, gain):
        k = (name, round(gain, 3))
        if k not in self._looks:
            if len(self._looks) > 24:
                self._looks.clear()
            self._looks[k] = self.bust.look(name, gain=gain)
        return self._looks[k]

    def avatar_parts(self, spec, fi, t):
        E, R, lean, sway, jaw = self.perf.at(fi)
        e = self.energy_at(t)
        base = self.look(spec['look'], spec['gain'])
        fx = dict(keep=spec['keep'], point_size=spec['point'], aura=spec['aura'], aura_frac=spec['aura_frac'],
                  shimmer=spec['shimmer'], voice_glow=spec['voice_glow'])
        pos, col, size, hw = self.bust.pose(E, R, lean, sway, t=t, energy=e, col=base, fx=fx)
        if spec.get('glints', 1.0) > 0:
            gp, gc, gs = self.bust.eye_glints(E, R, lean, sway, bright=4.0 * spec['glints'] * (0.6 + 0.4 * e))
            pos = np.concatenate([pos, gp]); col = np.concatenate([col, gc]); size = np.concatenate([size, gs])
        if spec['dissolve'] > 1e-4:
            pos, col, size = dissolve(np.ascontiguousarray(pos), np.ascontiguousarray(col), np.ascontiguousarray(size),
                                      self.seed[:len(pos)], min(spec['dissolve'], 1.0), t, spec['lift'], spec['spread'])
        sc = spec['scale']
        if sc != 1.0 or spec['yaw'] or any(spec['pos']):
            pos = (pos * sc) @ rot_y(spec['yaw']).T + np.asarray(spec['pos'], np.float32)
            size = size * sc
        return pos.astype(np.float32), col.astype(np.float32), size.astype(np.float32)

    def shot_index(self, t):
        idx = 0
        for i, (t0, fn, tr) in enumerate(self.tl):
            if t >= t0:
                idx = i
        return idx

    def render_shot(self, i, t, fi, flash=0.0, expo=1.0):
        t0, fn, tr = self.tl[i]
        F = fn(t, {})
        F.flash += flash
        F.exposure *= expo
        av = self.avatar_parts(F.avatar, fi, t) if F.avatar else None
        return self.comp.compose(F, av, fi)

    def frame(self, fi, overlays=True):
        t = fi / FPS
        i = self.shot_index(t)
        img = None
        # transition into shot i (or into shot i+1 if we are just before its cut)
        for j in (i + 1, i):
            if j <= 0 or j >= len(self.tl):
                continue
            tc, fn, tr = self.tl[j]
            if tr is None:
                continue
            kind, d = tr
            if abs(t - tc) > d / 2:
                continue
            u = smooth((t - (tc - d / 2)) / d)
            if kind == 'cross':
                a = self.render_shot(j - 1, t, fi)
                b = self.render_shot(j, t, fi)
                img = (a.astype(np.float32) * (1 - u) + b.astype(np.float32) * u).astype(np.uint8)
            elif kind == 'flash':
                fl = 1.2 * (1 - abs(t - tc) / (d / 2)) ** 2
                img = self.render_shot(j if t >= tc else j - 1, t, fi, flash=fl)
            elif kind == 'fade':
                ex = abs(t - tc) / (d / 2)
                img = self.render_shot(j if t >= tc else j - 1, t, fi, expo=max(ex, 0.001) ** 1.5)
            break
        if img is None:
            img = self.render_shot(i, t, fi)
        if overlays:
            self.overlays(img, t)
        return img

    def overlays(self, img, t):
        # brand mark at the top during the hook
        a = smooth((t - 0.6) / 0.8) * (1 - smooth((t - 3.6) / 0.8))
        if a > 0.01:
            s = self._brand
            y0, x0 = 190, (rc.W - s.shape[1]) // 2
            reg = img[y0:y0 + s.shape[0], x0:x0 + s.shape[1]].astype(np.float32)
            glow = cv2.GaussianBlur(s, (0, 0), 6) * 0.6
            col = np.array([255, 214, 150], np.float32)
            reg = reg + (glow[..., None] * np.array([255, 150, 60], np.float32) * 0.5 * a)
            reg = reg * (1 - s[..., None] * a * 0.9) + col * s[..., None] * a * 0.9
            img[y0:y0 + s.shape[0], x0:x0 + s.shape[1]] = np.clip(reg, 0, 255).astype(np.uint8)
        if t < 357.3 and not (217.8 < t < 220.6):
            self.subs.draw(img, t)


def main():
    work, mode = sys.argv[1], sys.argv[2]
    R = Renderer(work)
    if mode == 'preview':
        times = [float(x) for x in sys.argv[3].split(',')]
        out = sys.argv[4]
        tiles = []
        for tt in times:
            t0 = time.time()
            img = R.frame(int(round(tt * FPS)))
            cv2.putText(img, f'{tt:.2f}', (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 255, 0), 3)
            tiles.append(cv2.resize(img, (270, 480), interpolation=cv2.INTER_AREA))
            print(f'{tt:.2f}s rendered in {time.time() - t0:.2f}s', flush=True)
        cols = int(sys.argv[5]) if len(sys.argv) > 5 else 6
        while len(tiles) % cols:
            tiles.append(np.zeros_like(tiles[0]))
        rows = [np.concatenate(tiles[k:k + cols], 1) for k in range(0, len(tiles), cols)]
        cv2.imwrite(out, np.concatenate(rows, 0)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
    elif mode == 'chunk':
        f0, f1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
        enc = Encoder(out)
        t0 = time.time()
        for fi in range(f0, f1):
            enc.write(R.frame(fi, overlays=False))  # captions/brand are burned in by overlay.py
            if (fi - f0) % 60 == 0:
                el = time.time() - t0
                print(f'frame {fi} ({fi - f0 + 1}/{f1 - f0}) {el / (fi - f0 + 1):.2f}s/frame', flush=True)
        enc.close()
        print('done', out, f'{(time.time() - t0) / (f1 - f0):.2f}s/frame', flush=True)
    elif mode == 'still':
        tt = float(sys.argv[3])
        img = R.frame(int(round(tt * FPS)))
        cv2.imwrite(sys.argv[4], img[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])


if __name__ == '__main__':
    main()
