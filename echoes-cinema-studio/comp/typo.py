"""Thriller typography: slam titles, counters, typewriter lines, red-keyword captions, brand + end card."""
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'echoes-particle-studio'))
import subtitles as SUB  # noqa: E402

W, H = 1080, 1920
ANTON = '/opt/fonts/Anton.ttf'
MONT = '/opt/fonts/Montserrat.ttf'
CINZEL = '/opt/fonts/Cinzel.ttf'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'


def font(path, size, var=None):
    f = ImageFont.truetype(path, size)
    if var:
        try:
            f.set_variation_by_name(var)
        except Exception:
            pass
    return f


def text_mask(text, fnt, tracking=0):
    """Alpha mask (float32) of a single line, with optional letter tracking."""
    if tracking == 0:
        l, t, r, b = fnt.getbbox(text)
        pad = int(fnt.size * 0.3)
        img = Image.new('L', (r - l + 2 * pad, b - t + 2 * pad), 0)
        ImageDraw.Draw(img).text((pad - l, pad - t), text, font=fnt, fill=255)
        return np.asarray(img, np.float32) / 255
    widths = [fnt.getlength(c) for c in text]
    total = sum(widths) + tracking * (len(text) - 1)
    l, t, r, b = fnt.getbbox(text)
    pad = int(fnt.size * 0.3)
    img = Image.new('L', (int(total) + 2 * pad, b - t + 2 * pad), 0)
    d = ImageDraw.Draw(img)
    x = pad
    for c, w in zip(text, widths):
        d.text((x, pad - t), c, font=fnt, fill=255)
        x += w + tracking
    return np.asarray(img, np.float32) / 255


def paste(frame, mask, cx, cy, color, alpha=1.0, glow=None, glow_sigma=18, shadow=0.6):
    """Composite a mask at centre (cx, cy) onto float frame."""
    h, w = mask.shape
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    fx0, fy0, fx1, fy1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if fx1 <= fx0 or fy1 <= fy0 or alpha <= 0.005:
        return
    m = mask[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0][..., None] * alpha
    reg = frame[fy0:fy1, fx0:fx1]
    if shadow > 0:
        sh = cv2.GaussianBlur(mask, (0, 0), max(2, mask.shape[0] * 0.03))[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0]
        reg *= (1 - shadow * np.clip(sh * 1.4, 0, 1) * alpha)[..., None]
    if glow is not None:
        g = cv2.GaussianBlur(mask, (0, 0), glow_sigma)[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0][..., None]
        reg += g * np.array(glow, np.float32) * alpha
    reg[:] = reg * (1 - m) + np.array(color, np.float32) * m


class Slam:
    """A word that hits the screen: overshoot scale-in, RGB split on impact, holds, glitches out."""
    STYLES = {
        'red': dict(font=ANTON, size=300, color=(0.92, 0.06, 0.05), glow=(0.9, 0.05, 0.02), track=6),
        'white': dict(font=ANTON, size=280, color=(0.97, 0.97, 0.95), glow=(0.5, 0.6, 0.8), track=6),
        'gold': dict(font=ANTON, size=260, color=(1.0, 0.82, 0.5), glow=(1.0, 0.5, 0.1), track=8),
        'whisper': dict(font=ANTON, size=150, color=(0.8, 0.08, 0.06), glow=(0.6, 0.02, 0.0), track=10),
        'small': dict(font=ANTON, size=150, color=(0.85, 0.87, 0.9), glow=(0.25, 0.3, 0.4), track=16),
        'number': dict(font=ANTON, size=190, color=(0.96, 0.96, 0.98), glow=(0.4, 0.55, 0.9), track=4),
        'giant': dict(font=ANTON, size=420, color=(0.97, 0.97, 0.95), glow=(0.6, 0.1, 0.05), track=4),
    }

    def __init__(self, t0, t1, text, style='red', y=None, wrap=None):
        self.t0, self.t1, self.text, self.style = t0, t1, text, style
        st = self.STYLES[style]
        size = st['size']
        f = font(st['font'], size)
        lines = wrap or [text]
        masks = [text_mask(ln, f, st['track']) for ln in lines]
        # fit width
        mw = max(m.shape[1] for m in masks)
        if mw > W * 0.9:
            k = W * 0.9 / mw
            f = font(st['font'], int(size * k))
            masks = [text_mask(ln, f, int(st['track'] * k)) for ln in lines]
        hh = sum(m.shape[0] for m in masks) - int(f.size * 0.4) * (len(masks) - 1)
        ww = max(m.shape[1] for m in masks)
        canvas = np.zeros((hh, ww), np.float32)
        y0 = 0
        for m in masks:
            x0 = (ww - m.shape[1]) // 2
            canvas[y0:y0 + m.shape[0], x0:x0 + m.shape[1]] = np.maximum(canvas[y0:y0 + m.shape[0], x0:x0 + m.shape[1]], m)
            y0 += m.shape[0] - int(f.size * 0.4)
        self.mask = canvas
        self.color, self.glow = st['color'], st['glow']
        self.y = y if y is not None else H * 0.47

    def active(self, t):
        return self.t0 - 0.02 <= t <= self.t1 + 0.12

    def draw(self, frame, t):
        if not self.active(t):
            return
        k = (t - self.t0) / 0.14
        if k < 1:
            sc = 1.28 - 0.28 * (1 - (1 - max(k, 0)) ** 3) + 0.04 * math.sin(max(k, 0) * math.pi)
            a = min(1, max(k, 0) * 2.5)
        else:
            sc = 1.0 + 0.015 * (t - self.t0)          # slow creep
            a = 1.0
        out = (t - self.t1) / 0.12
        if out > 0:
            a *= max(0.0, 1 - out)
            sc *= 1 + 0.08 * out
        m = self.mask
        if abs(sc - 1) > 0.003:
            m = cv2.resize(m, (max(2, int(m.shape[1] * sc)), max(2, int(m.shape[0] * sc))), interpolation=cv2.INTER_LINEAR)
        split = max(0.0, 1 - k) * 22 if k < 1 else (6 if out > 0 else 0)
        if split > 0.5:
            paste(frame, m, W / 2 - split, self.y, (0.9, 0.0, 0.0), a * 0.5, shadow=0)
            paste(frame, m, W / 2 + split, self.y, (0.0, 0.4, 0.9), a * 0.5, shadow=0)
        paste(frame, m, W / 2, self.y, self.color, a, glow=self.glow, glow_sigma=m.shape[0] * 0.12)


class TypeLine:
    """Monospace typewriter line (case-file / timestamp style)."""

    def __init__(self, t0, t1, text, y, size=44, cps=22, color=(0.85, 0.88, 0.9), cursor=True):
        self.t0, self.t1, self.text, self.y, self.cps = t0, t1, text, y, cps
        self.f = font(MONO, size)
        self.color = color
        self.cursor = cursor
        self.cache = {}

    def draw(self, frame, t):
        if t < self.t0 or t > self.t1 + 0.3:
            return
        n = min(len(self.text), int((t - self.t0) * self.cps) + 1)
        s = self.text[:n]
        if self.cursor and int(t * 3) % 2 == 0 and t < self.t1:
            s = s + '_'
        if s not in self.cache:
            self.cache[s] = text_mask(s, self.f)
        a = 1.0 if t <= self.t1 else max(0, 1 - (t - self.t1) / 0.3)
        m = self.cache[s]
        paste(frame, m, W / 2 + (m.shape[1] - text_mask(self.text + '_', self.f).shape[1]) / 2, self.y, self.color, a,
              shadow=0.5)


class Counter:
    """Years counter that runs up to a value."""

    def __init__(self, t0, t1, v0, v1, suffix='', y=H * 0.47, style='number'):
        self.t0, self.t1, self.v0, self.v1, self.suffix, self.y = t0, t1, v0, v1, suffix, y
        st = Slam.STYLES[style]
        self.f = font(st['font'], st['size'])
        self.small = font(ANTON, 70)
        self.color, self.glow = st['color'], st['glow']

    def draw(self, frame, t):
        if t < self.t0 - 0.05 or t > self.t1 + 0.3:
            return
        k = min(1, max(0, (t - self.t0) / max(0.01, (self.t1 - self.t0) * 0.85)))
        k = 1 - (1 - k) ** 3
        v = int(self.v0 + (self.v1 - self.v0) * k)
        s = f'{v:,}'
        m = text_mask(s, self.f, 4)
        if m.shape[1] > W * 0.92:
            m = cv2.resize(m, (int(W * 0.92), int(m.shape[0] * W * 0.92 / m.shape[1])))
        a = min(1, (t - self.t0 + 0.05) / 0.1) * (1 if t <= self.t1 else max(0, 1 - (t - self.t1) / 0.3))
        paste(frame, m, W / 2, self.y, self.color, a, glow=self.glow, glow_sigma=16)
        if self.suffix:
            ms = text_mask(self.suffix, self.small, 18)
            paste(frame, ms, W / 2, self.y + m.shape[0] * 0.62, (0.75, 0.78, 0.82), a, shadow=0.4)


# ------------------------------------------------------------------ captions (white, red keywords)
class ThrillerSprite(SUB.WordSprite):
    def __init__(self, text, size, key=False, color=(255, 255, 255)):
        super().__init__(text, size, key, color)
        if key:
            h, w = self.a.shape
            yy = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
            top = np.array([255, 70, 60], np.float32)
            bot = np.array([200, 10, 10], np.float32)
            self.rgb = np.broadcast_to(top * (1 - yy) + bot * yy, (h, w, 3)).copy()
            self.glow_c = np.array([255, 20, 10], np.float32)
        else:
            self.glow_c = np.array([90, 110, 140], np.float32)


class Captions(SUB.Subtitles):
    def sprite(self, text, key):
        k = (text, key)
        if k not in self._cache:
            self._cache[k] = ThrillerSprite(text, int(self.size * (1.18 if key else 1.0)), key)
        return self._cache[k]

    def draw_float(self, frame, t):
        """Draw onto a float frame (0..1) via a uint8 round trip of just the caption band."""
        y0, y1 = int(self.cy - 260), int(self.cy + 260)
        band = np.clip(frame[y0:y1] * 255, 0, 255).astype(np.uint8)
        before = band.copy()
        tmp = np.zeros((H, W, 3), np.uint8)
        tmp[y0:y1] = band
        self.draw(tmp, t)
        after = tmp[y0:y1]
        changed = np.any(after != before, axis=2, keepdims=True)
        frame[y0:y1] = np.where(changed, after.astype(np.float32) / 255, frame[y0:y1])


def brand_mask():
    return text_mask('ECHOES  IN  THE  DARK', font(CINZEL, 54, 'Bold'), 4)


def handle_mask(text='@brandonmolina651'):
    return text_mask(text, font(MONT, 46, 'SemiBold'))
