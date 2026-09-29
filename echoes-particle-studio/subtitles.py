"""Animated word-by-word subtitles (pop-in, keyword emphasis, glow).

Phrases come from the word-timed transcript. Each word pops in when it is
spoken (scale overshoot + fade), keywords get a gold gradient and bigger
type, and the whole phrase lifts and fades out when the next one starts.
"""
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = '/opt/fonts/Montserrat.ttf'


def _font(size, weight='ExtraBold'):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def ease_out_back(x, s=1.9):
    x = min(max(x, 0.0), 1.0) - 1.0
    return 1.0 + (s + 1) * x ** 3 + s * x ** 2


class WordSprite:
    def __init__(self, text, size, key=False, color=(255, 255, 255)):
        self.text = text
        f = _font(size, 'Black' if key else 'ExtraBold')
        l, t, r, b = f.getbbox(text)
        pad = int(size * 0.5)
        w, h = r - l + pad * 2, int(size * 1.35) + pad * 2
        self.pad = pad
        base = Image.new('L', (w, h), 0)
        ImageDraw.Draw(base).text((pad - l, pad + int(size * 0.08)), text, font=f, fill=255)
        a = np.asarray(base, np.float32) / 255.0
        # fill colour: white, or gold gradient for keywords
        yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        if key:
            top = np.array([255, 236, 170], np.float32)
            bot = np.array([255, 170, 60], np.float32)
            fill = top * (1 - yy[..., None]) + bot * yy[..., None]
            fill = np.broadcast_to(fill, (h, w, 3))
            glow_c = np.array([255, 150, 40], np.float32)
        else:
            fill = np.broadcast_to(np.array(color, np.float32), (h, w, 3))
            glow_c = np.array([120, 170, 255], np.float32)
        # outline / shadow for legibility on bright frames
        sh = cv2.GaussianBlur(cv2.dilate(a, np.ones((5, 5), np.uint8)), (0, 0), size * 0.06)
        glow = cv2.GaussianBlur(a, (0, 0), size * 0.28)
        self.rgb = fill.copy()
        self.a = a
        self.sh = np.clip(sh * 0.85, 0, 1)
        self.glow = np.clip(glow * 1.25, 0, 1)
        self.glow_c = glow_c
        self.w, self.h = w, h
        self.adv = (r - l)


def _blend(frame, x0, y0, rgb, a):
    H, W = frame.shape[:2]
    h, w = a.shape
    fx0, fy0 = max(0, x0), max(0, y0)
    fx1, fy1 = min(W, x0 + w), min(H, y0 + h)
    if fx1 <= fx0 or fy1 <= fy0:
        return
    sx0, sy0 = fx0 - x0, fy0 - y0
    aa = a[sy0:sy0 + fy1 - fy0, sx0:sx0 + fx1 - fx0][..., None]
    src = rgb[sy0:sy0 + fy1 - fy0, sx0:sx0 + fx1 - fx0] if rgb.ndim == 3 else rgb
    dst = frame[fy0:fy1, fx0:fx1].astype(np.float32)
    frame[fy0:fy1, fx0:fx1] = np.clip(dst * (1 - aa) + src * aa, 0, 255).astype(np.uint8)


def _add(frame, x0, y0, rgb_c, a):
    H, W = frame.shape[:2]
    h, w = a.shape
    fx0, fy0 = max(0, x0), max(0, y0)
    fx1, fy1 = min(W, x0 + w), min(H, y0 + h)
    if fx1 <= fx0 or fy1 <= fy0:
        return
    sx0, sy0 = fx0 - x0, fy0 - y0
    aa = a[sy0:sy0 + fy1 - fy0, sx0:sx0 + fx1 - fx0][..., None]
    dst = frame[fy0:fy1, fx0:fx1].astype(np.float32)
    frame[fy0:fy1, fx0:fx1] = np.clip(dst + rgb_c * aa, 0, 255).astype(np.uint8)


class Subtitles:
    def __init__(self, phrases, cx=520, cy=1330, size=70, max_w=860, line_gap=1.12):
        """phrases: list of dicts {start, end, words: [{w, s, e, key}]}"""
        self.phrases = phrases
        self.cx, self.cy, self.size, self.max_w = cx, cy, size, max_w
        self.line_gap = line_gap
        self._cache = {}
        self._layout = {}

    def sprite(self, text, key):
        k = (text, key)
        if k not in self._cache:
            self._cache[k] = WordSprite(text, int(self.size * (1.18 if key else 1.0)), key)
        return self._cache[k]

    def layout(self, pi):
        if pi in self._layout:
            return self._layout[pi]
        ph = self.phrases[pi]
        sprites = [self.sprite(w['w'], w.get('key', False)) for w in ph['words']]
        space = self.size * 0.28
        lines, cur, cw = [], [], 0
        for i, s in enumerate(sprites):
            add = s.adv + (space if cur else 0)
            if cur and cw + add > self.max_w:
                lines.append(cur)
                cur, cw = [], 0
                add = s.adv
            cur.append(i)
            cw += add
        if cur:
            lines.append(cur)
        pos = {}
        lh = self.size * self.line_gap * 1.15
        y0 = self.cy - (len(lines) - 1) * lh / 2
        for li, line in enumerate(lines):
            tw = sum(sprites[i].adv for i in line) + space * (len(line) - 1)
            x = self.cx - tw / 2
            for i in line:
                pos[i] = (x + sprites[i].adv / 2, y0 + li * lh)
                x += sprites[i].adv + space
        self._layout[pi] = (sprites, pos)
        return self._layout[pi]

    def draw(self, frame, t, style=None):
        style = style or {}
        for pi, ph in enumerate(self.phrases):
            if t < ph['start'] - 0.05 or t > ph['end'] + 0.35:
                continue
            nxt = self.phrases[pi + 1]['start'] if pi + 1 < len(self.phrases) else 1e9
            out_t = min(ph['end'] + 0.35, nxt)
            fade_out = 1.0 - min(max((t - (out_t - 0.18)) / 0.18, 0.0), 1.0)
            lift = (1.0 - fade_out) * 18
            sprites, pos = self.layout(pi)
            for i, (w, s) in enumerate(zip(ph['words'], sprites)):
                dt = t - w['s'] + 0.04
                if dt < 0:
                    continue
                k = min(dt / 0.16, 1.0)
                sc = 0.55 + 0.45 * ease_out_back(k)
                speaking = w['s'] - 0.04 <= t <= w['e'] + 0.05
                if w.get('key'):
                    sc *= 1.0 + 0.06 * math.exp(-dt * 3.0)
                alpha = min(dt / 0.08, 1.0) * fade_out
                x, y = pos[i]
                self._draw_word(frame, s, x, y - lift + (1 - k) * 22, sc, alpha, speaking, w.get('key', False))

    def _draw_word(self, frame, s, x, y, sc, alpha, speaking, key):
        if alpha <= 0.01:
            return
        if abs(sc - 1.0) > 0.01:
            w2, h2 = max(2, int(s.w * sc)), max(2, int(s.h * sc))
            a = cv2.resize(s.a, (w2, h2), interpolation=cv2.INTER_LINEAR)
            sh = cv2.resize(s.sh, (w2, h2), interpolation=cv2.INTER_LINEAR)
            gl = cv2.resize(s.glow, (w2, h2), interpolation=cv2.INTER_LINEAR)
            rgb = cv2.resize(s.rgb, (w2, h2), interpolation=cv2.INTER_LINEAR)
        else:
            a, sh, gl, rgb = s.a, s.sh, s.glow, s.rgb
        h2, w2 = a.shape
        x0 = int(round(x - w2 / 2))
        y0 = int(round(y - h2 / 2))
        gstr = (0.75 if speaking else 0.35) * (1.4 if key else 1.0)
        _blend(frame, x0, y0 + 3, np.zeros(3, np.float32), sh * alpha * 0.8)
        _add(frame, x0, y0, s.glow_c * gstr, gl * alpha)
        dim = 1.0 if (speaking or key) else 0.9
        _blend(frame, x0, y0, rgb * dim, a * alpha)


def build_phrases(words, keywords=(), max_words=4, max_gap=0.45, max_dur=2.6):
    """Group word dicts {w, s, e} into on-screen phrases, breaking at pauses/punctuation."""
    kw = {k.lower() for k in keywords}
    phrases, cur = [], []
    for i, w in enumerate(words):
        txt = w['w'].strip()
        if not txt:
            continue
        clean = txt.strip('.,!?;:"\'').lower()
        item = {'w': txt.upper().strip(), 's': w['s'], 'e': w['e'], 'key': w.get('key', clean in kw)}
        if cur:
            gap = w['s'] - cur[-1]['e']
            if gap > max_gap or len(cur) >= max_words or (w['e'] - cur[0]['s']) > max_dur:
                phrases.append(cur)
                cur = []
        cur.append(item)
        if txt[-1] in '.!?,;:' and len(cur) >= 2:
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    out = []
    for p in phrases:
        for it in p:
            it['w'] = it['w'].rstrip(',;:')
        out.append({'start': p[0]['s'], 'end': p[-1]['e'], 'words': p})
    return out
