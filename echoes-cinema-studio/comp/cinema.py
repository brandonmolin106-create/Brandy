"""Thriller-cut compositor: EDL -> 1080x1920 @24 fps -> H.264 chunks -> master with soundtrack.

usage:
  python cinema.py render WORK FIRST LAST OUT.mp4   # render a frame range to a chunk
  python cinema.py still WORK T OUT.png             # one frame (QA)
WORK = .../cine (renders/, face/, audio)
"""
import functools
import math
import os
import subprocess
import sys
import time

import cv2
import numpy as np

import fx
import typo
from edl import build

W, H, FPS = 1080, 1920, 24
cv2.setNumThreads(1)  # one thread per chunk process; assemble.sh runs several in parallel
FACE_FPS = 16


class Sources:
    def __init__(self, work):
        self.work = work
        self.renders = f'{work}/renders'
        self.face_dir = f'{work}/face'
        self.face_n = len([f for f in os.listdir(self.face_dir) if f.endswith('.jpg')])
        self.counts = {}

    def frames(self, name):
        """Available frame indices (slow shots are rendered on every 2nd frame and blended here)."""
        if name not in self.counts:
            d = f'{self.renders}/{name}'
            idx = sorted(int(f[len(name) + 1:-4]) for f in os.listdir(d) if f.endswith('.png')) if os.path.isdir(d) else []
            self.counts[name] = np.array(idx, np.int64)
        return self.counts[name]

    @functools.lru_cache(maxsize=24)
    def render_frame(self, name, i):
        p = f'{self.renders}/{name}/{name}_{i:04d}.png'
        im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
        if im is None:
            return np.zeros((H, W, 3), np.float32)
        im = im[..., ::-1].astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)
        if im.shape[0] != H:
            im = cv2.resize(im, (W, H), interpolation=cv2.INTER_CUBIC)
            # restore crispness lost in the 2x upscale
            bl = cv2.GaussianBlur(im, (0, 0), 1.6)
            im = np.clip(im + (im - bl) * 0.55, 0, None)
        return im

    def clip(self, name, ct, loop=False, blend=True):
        idx = self.frames(name)
        if len(idx) == 0:
            return np.zeros((H, W, 3), np.float32)
        n = int(idx[-1]) + 1
        f = ct * FPS
        f = f % n if loop else min(max(f, 0.0), n - 1)
        j = int(np.searchsorted(idx, f, side='right')) - 1
        if j < 0:
            j = 0
        i0 = int(idx[j])
        if j + 1 < len(idx):
            i1 = int(idx[j + 1])
        else:
            i1 = int(idx[0]) + n if loop else i0
        a = (f - i0) / (i1 - i0) if i1 > i0 else 0.0
        im0 = self.render_frame(name, i0)
        if not blend or a < 0.08:
            return im0.copy()
        im1 = self.render_frame(name, i1 % n)
        if a > 0.92:
            return im1.copy()
        return im0 * (1 - a) + im1 * a

    @functools.lru_cache(maxsize=8)
    def face_frame(self, idx):
        idx = min(max(idx, 1), self.face_n)
        im = cv2.imread(f'{self.face_dir}/f_{idx:05d}.jpg')
        return im[..., ::-1].astype(np.float32) / 255.0

    def face(self, t):
        """Brandon at speech time t (the voice track is his own - picture stays lip-synced)."""
        return self.face_frame(int(t * FACE_FPS) + 1).copy()


_REC = {}


def rec_overlay(img, t):
    """Camcorder OSD on the confession tape: blinking REC dot, tape counter."""
    if 'f' not in _REC:
        _REC['f'] = typo.font(typo.MONO, 38)
        _REC['rec'] = typo.text_mask('REC', _REC['f'])
    if int(t * 1.6) % 2 == 0:
        cv2.circle(img, (92, 212), 13, (0.95, 0.08, 0.06), -1, cv2.LINE_AA)
    typo.paste(img, _REC['rec'], 160, 212, (0.92, 0.92, 0.9), 0.9, shadow=0.4)
    fr = int(t * 30) % 30
    s = int(t)
    tc = f'00:{s // 60:02d}:{s % 60:02d}:{fr:02d}'
    m = typo.text_mask(tc, _REC['f'])
    typo.paste(img, m, 60 + m.shape[1] / 2, 262, (0.92, 0.92, 0.9), 0.8, shadow=0.4)


def tape_look(img, t, amount=1.0):
    """The confession tape: cold monochrome, crushed, scanlines, occasional tracking wobble."""
    x = fx.grade(img, 'tape')
    x = fx.scanlines(x, 0.07 * amount, t)
    # tracking wobble every few seconds
    ph = (t * 0.37) % 1.0
    if ph < 0.05:
        k = math.sin(ph / 0.05 * math.pi)
        x = fx.glitch(x, t, 0.35 * k * amount, seed=3)
    return x


class Compositor:
    def __init__(self, work):
        self.src = Sources(work)
        self.edl, self.events = build()
        self.grain = fx.Grain()
        self.vig = fx.vignette_mask(0.6)
        self.brand = typo.brand_mask()
        self.handle = typo.handle_mask()
        self.caps = self.events['captions']

    def shot_at(self, t):
        for s in self.edl:
            if s['t0'] <= t < s['t1']:
                return s
        return self.edl[-1]

    def base(self, s, t):
        src = s['src']
        lt = t - s['t0']
        if src == 'black':
            return np.zeros((H, W, 3), np.float32)
        if src == 'face':
            im = self.src.face(t + s.get('face_offset', 0.0))
            if s.get('freeze') is not None and t >= s['freeze'][0]:
                im = self.src.face(s['freeze'][0])
            im = tape_look(im, t)
            rec_overlay(im, t)
            return im
        ct = s.get('ct0', 0.0) + lt * s.get('speed', 1.0)
        im = self.src.clip(src, ct, loop=s.get('loop', False), blend=s.get('blend', True))
        return fx.grade(im, s.get('grade', 'room'))

    def frame(self, fi, shot=None):
        t = fi / FPS
        s = shot if shot is not None else self.shot_at(t)
        lt = t - s['t0']
        dur = s['t1'] - s['t0']
        img = self.base(s, t)
        # ---- per-shot scene fx
        if s.get('dim'):
            img *= s['dim']
        if s.get('timelapse'):
            day = 0.55 + 0.45 * math.sin(t * s['timelapse'] * 2 * math.pi)
            img *= day
            img = fx.blinds_sweep(img, t * s['timelapse'], 0.3)
            if s.get('age'):
                k = min(1, lt / dur)
                g = img.mean(2, keepdims=True)
                img = img * (1 - 0.6 * k) + g * 0.6 * k
        if s.get('shadows'):
            img = fx.people_shadows(img, t, s['shadows'], seed=int(s['t0']))
        if s.get('rays'):
            img = fx.god_rays(img, strength=s['rays'])
        if s.get('bell'):
            b = s['bell']
            amt = fx.smooth(lt / 0.5) if b is True else b
            img = fx.bell_jar(img, amt, t)
        if s.get('crack') is not None and t >= s['crack']:
            img = fx.cracks(img, min(1, (t - s['crack']) / 0.25), seed=7)
        if s.get('lamp_die'):
            pass
        # ---- camera: push / drift / impacts
        z0, z1 = s.get('push', (1.0, 1.0))
        zoom = z0 + (z1 - z0) * fx.smooth(lt / max(dur, 1e-3))
        dx = dy = rot = 0.0
        amp = s.get('handheld', 0.0)
        if amp:
            a, b_, r = fx.shake(t, amp, seed=s['t0'])
            dx, dy, rot = dx + a, dy + b_, rot + r
        for (ti, st) in self.events['impacts']:
            e = fx.env(t, ti, 0.01, 0.45)
            if e > 0:
                a, b_, r = fx.shake(t * 3, 26 * st * e, seed=ti)
                dx, dy, rot = dx + a, dy + b_, rot + r
                zoom *= 1 + 0.035 * st * e
        img = fx.transform(img, zoom, dx, dy, rot, flip=s.get('flip', False))
        # ---- optics
        if s['src'] != 'face':
            img = fx.halation(img, strength=s.get('halation', 0.25))
            img = fx.bloom(img, strength=s.get('bloom', 0.3))
        else:
            img = fx.bloom(img, thr=0.8, strength=0.15)
        ca = 1.5
        for (ti, st) in self.events['impacts']:
            ca += 9 * st * fx.env(t, ti, 0.01, 0.3)
        img = fx.chroma_ab(img, ca)
        # ---- transitions / flashes / glitches
        g = 0.0
        for (ti, du, st) in self.events['glitches']:
            if ti <= t < ti + du:
                g = max(g, st)
        if s['src'] == 'face' and lt < 0.12:
            g = max(g, 0.6 * (1 - lt / 0.12))
        if g > 0:
            img = fx.glitch(img, t, g, seed=int(t * 10))
        img = fx.light_leak(img, t, sum(st * fx.env(t, ti, 0.15, 0.8) for (ti, st) in self.events['leaks']))
        # ---- typography over picture
        for sl in self.events['slams']:
            sl.draw(img, t)
        for tl in self.events['types']:
            tl.draw(img, t)
        for c in self.events['counters']:
            c.draw(img, t)
        self.draw_brand(img, t)
        # ---- film finish
        img *= self.vig
        img = self.grain.apply(img, fi, 0.045 if s['src'] != 'face' else 0.07)
        lb = 0.0
        for (a0, a1) in self.events['letterbox']:
            if a0 - 0.4 <= t <= a1 + 0.4:
                lb = max(lb, min(fx.smooth((t - (a0 - 0.4)) / 0.4), fx.smooth(((a1 + 0.4) - t) / 0.4)))
        img = fx.letterbox(img, lb)
        for (ti, du, col) in self.events['flashes']:
            if ti <= t < ti + du:
                k = 1 - (t - ti) / du
                img = img * (1 - 0.85 * k) + np.array(col, np.float32) * k
        # weave
        img = fx.transform(img, 1.0, 0.6 * math.sin(fi * 1.7), 0.5 * math.cos(fi * 2.3), 0.0)
        # captions last (always legible)
        if not any(a <= t < b for a, b in self.events['no_captions']) and not any(sl.active(t) for sl in self.events['slams']):
            self.caps.draw_float(img, t)
        # fade to/from black
        for (a0, a1, direction) in self.events['fades']:
            if a0 <= t < a1:
                k = (t - a0) / (a1 - a0)
                img *= (1 - k) if direction == 'out' else k
        return np.clip(img, 0, 1)

    def draw_brand(self, img, t):
        a = fx.smooth((t - 0.65) / 0.35) * (1 - fx.smooth((t - 1.9) / 0.3))
        if a > 0.01:
            typo.paste(img, self.brand, W / 2, H * 0.22, (1.0, 0.86, 0.66), a, glow=(0.9, 0.35, 0.1), glow_sigma=14)
        e0 = self.events['end_card']
        a = fx.smooth((t - e0) / 0.8)
        if a > 0.01:
            typo.paste(img, self.brand, W / 2, H * 0.44, (1.0, 0.86, 0.66), a, glow=(0.9, 0.35, 0.1), glow_sigma=16)
            b = fx.smooth((t - e0 - 1.2) / 0.8)
            typo.paste(img, self.handle, W / 2, H * 0.52, (0.85, 0.88, 0.95), b, glow=(0.2, 0.3, 0.6), glow_sigma=10)


def encode_cmd(path, crf=14):
    return ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
            '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf), '-pix_fmt', 'yuv420p', '-threads', '2',
            path]


def segments(comp):
    out = []
    for k, s in enumerate(comp.edl):
        f0, f1 = int(round(s['t0'] * FPS)), int(round(s['t1'] * FPS))
        if f1 > f0:
            out.append((k, f0, f1, s))
    return out


def ready(comp, s):
    """A render source counts once its directory carries a .ready marker (set after QA)."""
    return s['src'] in ('face', 'black') or os.path.exists(f"{comp.src.renders}/{s['src']}/.ready")


def render_segments(comp, outdir, part=0, parts=1, crf=14):
    os.makedirs(outdir, exist_ok=True)
    for k, f0, f1, s in segments(comp):
        if k % parts != part:
            continue
        path = f'{outdir}/seg_{k:03d}.mp4'
        if os.path.exists(path) and os.path.getsize(path) > 0:
            continue
        if not ready(comp, s):
            continue
        tmp = path + '.part.mp4'
        p = subprocess.Popen(encode_cmd(tmp, crf), stdin=subprocess.PIPE)
        t0 = time.time()
        for fi in range(f0, f1):
            p.stdin.write((comp.frame(fi, shot=s) * 255 + 0.5).astype(np.uint8).tobytes())
        p.stdin.close()
        p.wait()
        os.replace(tmp, path)
        print(f"seg {k:03d} {s['src']:>16} {s['t0']:7.2f}-{s['t1']:7.2f}  {(time.time() - t0) / (f1 - f0):.2f}s/frame",
              flush=True)


def main():
    mode = sys.argv[1]
    work = sys.argv[2]
    comp = Compositor(work)
    if mode == 'segs':
        outdir = sys.argv[3]
        part, parts = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (0, 1)
        render_segments(comp, outdir, part, parts)
        missing = [k for k, f0, f1, s in segments(comp) if not os.path.exists(f'{outdir}/seg_{k:03d}.mp4')]
        print('segments missing:', len(missing), flush=True)
        return
    if mode == 'concat':
        outdir, dst = sys.argv[3], sys.argv[4]
        with open(f'{outdir}/list.txt', 'w') as fh:
            for k, f0, f1, s in segments(comp):
                fh.write(f"file '{outdir}/seg_{k:03d}.mp4'\n")
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{outdir}/list.txt',
                        '-c', 'copy', dst], check=True)
        return
    if mode == 'still':
        t = float(sys.argv[3])
        img = comp.frame(int(round(t * FPS)))
        cv2.imwrite(sys.argv[4], (img[..., ::-1] * 255).astype(np.uint8))
        return
    first, last, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    p = subprocess.Popen(encode_cmd(out), stdin=subprocess.PIPE)
    t0 = time.time()
    for fi in range(first, last):
        img = comp.frame(fi)
        p.stdin.write((img * 255 + 0.5).astype(np.uint8).tobytes())
        if (fi - first) % 240 == 0:
            el = time.time() - t0
            print(f'{out}: frame {fi} ({fi / FPS:.1f}s) {el / max(1, fi - first + 1):.2f}s/frame', flush=True)
    p.stdin.close()
    p.wait()
    print('done', out, flush=True)


if __name__ == '__main__':
    main()
