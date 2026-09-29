"""Frame compositor: shots -> particles -> HDR layers -> post -> subtitles -> encoder."""
import math
import subprocess

import numba as nb
import numpy as np

import render_core as rc
from noise3 import curl

FPS = 30


class Frame:
    def __init__(self, cam, bg=None, fg=None, avatar=None, rays=None, grade=None, bloom=None, flash=0.0,
                 bg_dof=None, fog=0.0, fog_color=(0, 0, 0), occl=0.85, exposure=1.0, shake=0.0):
        self.cam = cam
        self.bg = bg
        self.fg = fg
        self.avatar = avatar
        self.rays = rays
        self.grade = grade or {}
        self.bloom = bloom or {}
        self.flash = flash
        self.bg_dof = bg_dof
        self.fog = fog
        self.fog_color = fog_color
        self.occl = occl
        self.exposure = exposure
        self.shake = shake


@nb.njit(parallel=True, fastmath=True, cache=True)
def _dissolve(pos, col, size, seed, amount, t, lift, spread, out_p, out_c, out_s):
    """Staggered disintegration: particles peel off (by seed threshold), drift up/out and fade."""
    n = pos.shape[0]
    for i in nb.prange(n):
        s = seed[i]
        # local amount: particles with low seed go first
        a = (amount * 1.6 - s * 0.6)
        if a < 0.0:
            a = 0.0
        if a > 1.0:
            a = 1.0
        a = a * a * (3.0 - 2.0 * a)
        ph = s * 91.7
        dx = math.sin(ph + t * 0.9) * spread + math.sin(ph * 2.3) * spread * 0.6
        dy = lift * (0.4 + s) + math.sin(ph * 1.7 + t * 0.7) * spread * 0.4
        dz = math.cos(ph * 1.3 + t * 0.8) * spread
        out_p[i, 0] = pos[i, 0] + dx * a
        out_p[i, 1] = pos[i, 1] + dy * a
        out_p[i, 2] = pos[i, 2] + dz * a
        f = 1.0 - a * 0.85
        glow = 1.0 + 2.5 * a * (1.0 - a) * 4.0 * 0.25
        out_c[i, 0] = col[i, 0] * f * glow
        out_c[i, 1] = col[i, 1] * f * glow
        out_c[i, 2] = col[i, 2] * f * glow
        out_s[i] = size[i] * (1.0 - 0.5 * a)


def dissolve(pos, col, size, seed, amount, t, lift=0.3, spread=0.15):
    if amount <= 1e-4:
        return pos, col, size
    op = np.empty_like(pos)
    oc = np.empty_like(col)
    os_ = np.empty_like(size)
    _dissolve(pos, col, size, seed, np.float32(amount), np.float32(t), np.float32(lift), np.float32(spread),
              op, oc, os_)
    return op, oc, os_


def look_at_matrix(yaw=0.0, pitch=0.0, roll=0.0):
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    Rz = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
    return (Ry @ Rx @ Rz).astype(np.float32)


def shake_offset(t, amp, seed=0.0):
    """Smooth handheld noise: (dx, dy, droll)."""
    if amp <= 0:
        return 0.0, 0.0, 0.0
    f = [0.7, 1.3, 2.9, 5.3]
    a = [1.0, 0.6, 0.25, 0.1]
    dx = sum(ai * math.sin(2 * math.pi * fi * t + 1.3 * k + seed) for k, (fi, ai) in enumerate(zip(f, a)))
    dy = sum(ai * math.sin(2 * math.pi * fi * 1.1 * t + 2.1 * k + seed * 1.7) for k, (fi, ai) in enumerate(zip(f, a)))
    dr = sum(ai * math.sin(2 * math.pi * fi * 0.8 * t + 0.7 * k + seed * 2.3) for k, (fi, ai) in enumerate(zip(f, a)))
    return dx * amp, dy * amp, dr * amp * 0.02


class Compositor:
    def __init__(self):
        self.sp = rc.Splatter()

    def layer(self, cam, parts, fog=0.0, fog_color=(0, 0, 0), max_sigma=40.0):
        if parts is None or len(parts[0]) == 0:
            return None
        pos, col, size = parts
        lv = self.sp.render(cam, pos, col, size, fog_density=fog, fog_color=fog_color, max_sigma=max_sigma)
        return rc.collapse(lv)

    def compose(self, F, avatar_parts=None, frame_idx=0):
        cam = F.cam
        bg_cam = cam
        if F.bg_dof is not None:
            bg_cam = rc.Camera(cam.eye, cam.target, cam.up, cam.fov, cam.roll, cam.focus, F.bg_dof, cam.shift)
        bg = self.layer(bg_cam, F.bg, F.fog, F.fog_color)
        hdr = bg if bg is not None else np.zeros((rc.H, rc.W, 3), np.float32)
        cov = None
        if avatar_parts is not None and len(avatar_parts[0]):
            cov = rc.coverage(cam, avatar_parts[0], avatar_parts[2])
            av = self.layer(cam, avatar_parts, max_sigma=24.0)
        if F.rays is not None and F.rays[1] > 0:
            src = hdr if cov is None else hdr * (1.0 - cov)
            thr = F.rays[2] if len(F.rays) > 2 else 0.6
            rays = rc.rays_only(src, F.rays[0], strength=F.rays[1], threshold=thr)
        else:
            rays = None
        if cov is not None:
            hdr = hdr * (1.0 - cov * F.occl) + av
        if rays is not None:
            hdr = hdr + rays
        fg = self.layer(cam, F.fg, F.fog, F.fog_color)
        if fg is not None:
            hdr = hdr + fg
        b = dict(threshold=1.0, strength=0.55)
        b.update(F.bloom)
        hdr = rc.bloom(hdr, **b)
        if F.flash > 0:
            hdr = hdr + np.float32(F.flash) * np.array([1.0, 0.95, 0.88], np.float32)
        g = dict(F.grade)
        g['exposure'] = g.get('exposure', 1.0) * F.exposure
        return rc.finish(hdr, rc.Grade(**g), frame_idx)


class Encoder:
    def __init__(self, path, fps=FPS, crf=12, preset='veryfast'):
        # near-lossless intermediate; deliverables are re-encoded by assemble.sh
        self.p = subprocess.Popen([
            'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{rc.W}x{rc.H}',
            '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-preset', preset, '-crf', str(crf),
            '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-threads', '2', '-movflags', '+faststart', path],
            stdin=subprocess.PIPE)

    def write(self, rgb):
        self.p.stdin.write(np.ascontiguousarray(rgb).tobytes())

    def close(self):
        self.p.stdin.close()
        self.p.wait()
