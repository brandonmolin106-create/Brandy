"""Image FX for the thriller cut (numpy/OpenCV, float32 RGB in [0, 1+], 1080x1920)."""
import math

import cv2
import numpy as np

W, H = 1080, 1920


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def env(t, t0, a, d):
    """Attack-decay envelope around t0 (0 outside)."""
    if t < t0 - a or t > t0 + d:
        return 0.0
    if t < t0:
        return smooth((t - (t0 - a)) / max(a, 1e-4))
    return math.exp(-3.5 * (t - t0) / max(d, 1e-4))


# ------------------------------------------------------------------ geometry
def transform(img, zoom=1.0, dx=0.0, dy=0.0, rot=0.0, flip=False):
    """Digital camera: zoom about centre, pan (pixels), roll (radians), optional mirror."""
    if flip:
        img = img[:, ::-1]
    if abs(zoom - 1) < 1e-4 and abs(dx) < 0.05 and abs(dy) < 0.05 and abs(rot) < 1e-5:
        return img
    c, s = math.cos(rot) * zoom, math.sin(rot) * zoom
    cx, cy = W / 2, H / 2
    M = np.array([[c, -s, cx - c * cx + s * cy + dx], [s, c, cy - s * cx - c * cy + dy]], np.float32)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def shake(t, amp, seed=0.0):
    f = (1.9, 3.7, 7.3, 13.1)
    a = (1.0, 0.55, 0.3, 0.15)
    dx = sum(ai * math.sin(2 * math.pi * fi * t + seed + k) for k, (fi, ai) in enumerate(zip(f, a)))
    dy = sum(ai * math.sin(2 * math.pi * fi * 1.13 * t + seed * 1.7 + 2 * k) for k, (fi, ai) in enumerate(zip(f, a)))
    dr = sum(ai * math.sin(2 * math.pi * fi * 0.87 * t + seed * 2.3 + 3 * k) for k, (fi, ai) in enumerate(zip(f, a)))
    return dx * amp, dy * amp, dr * amp * 0.0009


# ------------------------------------------------------------------ light
def blur_small(img, sigma, scale=4):
    small = cv2.resize(img, (W // scale, H // scale), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), sigma / scale)
    return cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)


def bloom(img, thr=0.72, strength=0.35, sigma=38, tint=(1.0, 0.95, 0.9)):
    hi = np.clip(img - thr, 0, None) / (1 - thr)
    b = blur_small(hi, sigma) * 0.6 + blur_small(hi, sigma * 3, 8) * 0.4
    return img + b * np.array(tint, np.float32) * strength


def halation(img, thr=0.6, strength=0.28, sigma=10):
    """Film halation: red-orange glow bleeding from hard highlights."""
    lum = img.max(axis=2)
    hi = np.clip(lum - thr, 0, None)[..., None] / (1 - thr)
    g = blur_small(np.repeat(hi, 3, 2), sigma, 2)
    return img + g * np.array([1.0, 0.25, 0.08], np.float32) * strength


def god_rays(img, src=(540, -200), strength=0.5, thr=0.35, tint=(0.6, 0.9, 1.0), steps=10, decay=0.9):
    """Radial light shafts streaming from src (e.g. the water surface above the frame)."""
    s = 4
    small = cv2.resize(img, (W // s, H // s), interpolation=cv2.INTER_AREA)
    hi = np.clip(small.mean(2, keepdims=True) - thr, 0, None)
    hi = np.repeat(hi, 3, 2)
    acc = hi.copy()
    cur = hi
    cx, cy = src[0] / s, src[1] / s
    w = 1.0
    for _ in range(steps):
        z = 1.06
        M = np.array([[z, 0, cx - z * cx], [0, z, cy - z * cy]], np.float32)
        cur = cv2.warpAffine(cur, M, (W // s, H // s), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        w *= decay
        acc += cur * w
    acc = cv2.GaussianBlur(acc, (0, 0), 2.0)
    rays = cv2.resize(acc, (W, H), interpolation=cv2.INTER_LINEAR)
    return img + rays * np.array(tint, np.float32) * strength / steps


def light_leak(img, t, amount, seed=0):
    if amount <= 0.01:
        return img
    yy, xx = np.mgrid[0:H // 8, 0:W // 8].astype(np.float32)
    cx = (0.8 + 0.3 * math.sin(t * 0.7 + seed)) * W / 8
    cy = (0.3 + 0.2 * math.cos(t * 0.5 + seed)) * H / 8
    g = np.exp(-(((xx - cx) / (W / 8 * 0.5)) ** 2 + ((yy - cy) / (H / 8 * 0.35)) ** 2))
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    return img + g * np.array([1.0, 0.45, 0.12], np.float32) * amount


# ------------------------------------------------------------------ colour
def grade(img, preset):
    """Thriller looks. Reds survive (the fish), everything else leans cold."""
    p = GRADES[preset]
    x = img * p.get('exposure', 1.0)
    lum = (x * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(2, keepdims=True)
    # selective saturation: keep strong reds, desaturate the rest
    red = np.clip((x[..., :1] - np.maximum(x[..., 1:2], x[..., 2:3]) * 1.3) * 4.0, 0, 1)
    sat = p.get('sat', 0.8) + (p.get('red_sat', 1.15) - p.get('sat', 0.8)) * red
    x = lum + (x - lum) * sat
    # split tone: shadows -> teal, highlights -> warm
    sh = np.clip(1 - lum * 2.2, 0, 1)
    hl = np.clip((lum - 0.45) * 1.8, 0, 1)
    x = x + sh * np.array(p.get('shadow', (-0.01, 0.012, 0.022)), np.float32) \
        + hl * np.array(p.get('high', (0.03, 0.01, -0.02)), np.float32)
    # contrast s-curve around 0.4, crushed floor
    c = p.get('contrast', 1.15)
    x = np.clip(x, 0, None)
    x = 0.4 + (x - 0.4) * c
    x = np.clip(x - p.get('floor', 0.012), 0, None) / (1 - p.get('floor', 0.012))
    return x


GRADES = {
    'room': dict(sat=0.78, red_sat=1.25, shadow=(-0.012, 0.010, 0.022), high=(0.035, 0.012, -0.02), contrast=1.18),
    'ocean': dict(sat=0.95, red_sat=1.25, shadow=(-0.02, 0.01, 0.03), high=(-0.01, 0.02, 0.03), contrast=1.12),
    'sun': dict(sat=1.05, red_sat=1.1, shadow=(0.0, 0.004, 0.02), high=(0.05, 0.02, -0.03), contrast=1.15),
    'sun_hot': dict(sat=1.0, red_sat=1.05, shadow=(0.0, 0.004, 0.02), high=(0.03, 0.01, -0.03), contrast=1.22,
                    exposure=0.7),
    'storm': dict(sat=0.55, red_sat=0.8, shadow=(-0.01, 0.01, 0.03), high=(-0.01, 0.0, 0.02), contrast=1.2,
                  exposure=0.9),
    'space': dict(sat=0.9, red_sat=1.0, shadow=(-0.005, 0.0, 0.015), high=(0.01, 0.01, 0.0), contrast=1.1),
    'tape': dict(sat=0.0, red_sat=0.0, shadow=(-0.01, 0.006, 0.03), high=(0.0, 0.02, 0.045), contrast=1.28,
                 floor=0.04, exposure=1.05),
    'none': dict(sat=1.0, red_sat=1.0, shadow=(0, 0, 0), high=(0, 0, 0), contrast=1.0, floor=0.0),
}


def vignette_mask(strength=0.55):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
    return (1 - strength * np.clip(r - 0.35, 0, 1) ** 1.6)[..., None].astype(np.float32)


class Grain:
    """Pre-baked animated film grain (luminance-weighted)."""

    def __init__(self, n=24, seed=5):
        rng = np.random.default_rng(seed)
        self.frames = []
        for _ in range(n):
            g = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
            g = cv2.GaussianBlur(g, (0, 0), 0.7)
            g = cv2.resize(g, (W, H), interpolation=cv2.INTER_CUBIC)
            self.frames.append(g.astype(np.float16))

    def apply(self, img, fi, amount=0.05):
        g = self.frames[fi % len(self.frames)].astype(np.float32)[..., None]
        lum = img.mean(2, keepdims=True)
        w = amount * (0.35 + 1.3 * lum * (1 - np.clip(lum, 0, 1)) * 2.2)
        return img + g * w


def chroma_ab(img, amount):
    """Radial chromatic aberration: R pushed out, B pulled in."""
    if amount <= 0.2:
        return img
    out = img.copy()
    for ch, k in ((0, 1 + amount / 1000), (2, 1 - amount / 1000)):
        M = np.array([[k, 0, W / 2 * (1 - k)], [0, k, H / 2 * (1 - k)]], np.float32)
        out[..., ch] = cv2.warpAffine(img[..., ch], M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return out


def glitch(img, t, amount, seed=0):
    """Digital tear: RGB split, displaced horizontal blocks, scanline dropouts."""
    if amount <= 0.01:
        return img
    rng = np.random.default_rng(int(t * 97 + seed * 13) % 2 ** 31)
    out = img.copy()
    sh = int(18 * amount)
    out[..., 0] = np.roll(img[..., 0], sh, axis=1)
    out[..., 2] = np.roll(img[..., 2], -sh, axis=1)
    for _ in range(int(3 + 9 * amount)):
        y = rng.integers(0, H - 40)
        h = int(rng.integers(8, 90))
        dx = int(rng.normal(0, 60 * amount))
        out[y:y + h] = np.roll(out[y:y + h], dx, axis=1)
    if amount > 0.4:
        lines = rng.integers(0, H, int(30 * amount))
        out[lines] *= 0.2
    return out


def scanlines(img, strength=0.08, t=0.0):
    rows = (np.arange(H) % 4 < 2).astype(np.float32)[:, None, None]
    out = img * (1 - strength * rows)
    # slow rolling brightness band (old monitor)
    y = (t * 140) % (H + 300) - 150
    band = np.exp(-((np.arange(H) - y) / 90.0) ** 2)[:, None, None].astype(np.float32)
    return out * (1 + 0.06 * band)


def letterbox(img, amount, ratio=2.0):
    """Animated cinema bars (amount 0..1)."""
    if amount <= 0.001:
        return img
    target_h = W / ratio * 1.8
    bar = int((H - target_h) / 2 * smooth(amount))
    if bar > 0:
        img[:bar] *= 0.0
        img[H - bar:] *= 0.0
    return img


# ------------------------------------------------------------------ scene FX
def people_shadows(img, t, amount, seed=0):
    """Silhouettes of passers-by crossing the light: soft dark shapes sliding across frame."""
    if amount <= 0.01:
        return img
    s = 8
    w, h = W // s, H // s
    m = np.zeros((h, w), np.float32)
    rng = np.random.default_rng(seed)
    for k in range(3):
        speed = rng.uniform(0.35, 0.6) * (1 if k % 2 == 0 else -1)
        phase = rng.uniform(0, 1)
        x = ((t * speed + phase) % 1.6 - 0.3) * w
        if speed < 0:
            x = w - x
        cx = int(x)
        cv2.ellipse(m, (cx, int(h * 0.28)), (int(w * 0.07), int(h * 0.05)), 0, 0, 360, 1.0, -1)
        cv2.ellipse(m, (cx, int(h * 0.62)), (int(w * 0.14), int(h * 0.3)), 0, 0, 360, 1.0, -1)
        # stride: legs swing
        sw = int(w * 0.05 * math.sin(t * 6 + k))
        cv2.line(m, (cx, int(h * 0.8)), (cx + sw, h), 1.0, int(w * 0.06))
    m = cv2.GaussianBlur(m, (0, 0), 7)
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    return img * (1 - 0.72 * amount * np.clip(m, 0, 1))


def bell_jar(img, amount, t):
    """'Don't let your mind become a cup': the face seen through a glass tumbler (cylindrical lens)."""
    if amount <= 0.01:
        return img
    R = W * 0.47
    cx = W / 2
    xs = np.arange(W, dtype=np.float32)
    u = (xs - cx) / R
    inside = np.abs(u) < 1
    # cylinder refraction: magnify the centre, squeeze toward the walls
    src = cx + R * np.where(inside, np.sin(np.clip(u, -1, 1) * math.pi / 2 * 0.86) / math.sin(math.pi / 2 * 0.86)
                            * (0.82 + 0.18 * np.abs(u)), u)
    src = xs + (src - xs) * amount
    mapx = np.repeat(src[None, :], H, 0).astype(np.float32)
    mapy = np.repeat(np.arange(H, dtype=np.float32)[:, None], W, 1)
    mapy = mapy + (np.abs(u)[None, :] ** 3 * 8 * amount).astype(np.float32)
    out = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    # glass: green edge tint, bright vertical wall highlights, faint reflection sheen
    edge = np.clip((np.abs(u) - 0.86) / 0.14, 0, 1)
    wall = np.exp(-((np.abs(u) - 0.975) / 0.012) ** 2) + 0.5 * np.exp(-((u + 0.62) / 0.03) ** 2)
    sheen = 0.06 * np.exp(-((u - 0.35 - 0.05 * math.sin(t)) / 0.12) ** 2)
    col = out * (1 - 0.35 * edge[None, :, None] * np.array([0.3, 0.0, 0.2], np.float32))
    col = col + (wall + sheen)[None, :, None] * np.array([0.8, 0.9, 1.0], np.float32) * 0.9
    out = img + (col - img) * amount
    # rim of the glass at the top: an ellipse highlight
    cv2.ellipse(out, (int(cx), int(H * 0.12)), (int(R), int(R * 0.12)), 0, 0, 360,
                (0.5 * amount, 0.55 * amount, 0.6 * amount), 3, cv2.LINE_AA)
    return out


def cracks(img, amount, seed=1, center=(540, 900)):
    """Glass shatter: branching crack lines + slight displacement."""
    if amount <= 0.01:
        return img
    rng = np.random.default_rng(seed)
    m = np.zeros((H, W), np.float32)

    def branch(x, y, ang, length, depth):
        for _ in range(int(length / 18)):
            nx = x + math.cos(ang) * 18
            ny = y + math.sin(ang) * 18
            cv2.line(m, (int(x), int(y)), (int(nx), int(ny)), 1.0, 2 if depth < 2 else 1, cv2.LINE_AA)
            x, y = nx, ny
            ang += rng.normal(0, 0.18)
            if depth < 3 and rng.random() < 0.07:
                branch(x, y, ang + rng.choice([-1, 1]) * rng.uniform(0.4, 1.0), length * 0.5, depth + 1)

    for k in range(14):
        branch(center[0], center[1], k / 14 * 2 * math.pi + rng.normal(0, 0.15), rng.uniform(500, 1300), 0)
    for r in (70, 160, 290):
        cv2.circle(m, center, r + int(rng.normal(0, 10)), 0.6, 1, cv2.LINE_AA)
    grow = np.clip(amount * 1.4, 0, 1)
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.hypot(xx - center[0], yy - center[1]) / 1400
    m = m * (dist < grow)
    glow = cv2.GaussianBlur(m, (0, 0), 3)
    disp = cv2.GaussianBlur(m, (0, 0), 12) * 18 * amount
    mapx = (xx + disp).astype(np.float32)
    mapy = (yy + disp * 0.5).astype(np.float32)
    out = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return out + (m[..., None] * 0.9 + glow[..., None] * 0.5) * np.array([0.85, 0.92, 1.0], np.float32)


def blinds_sweep(img, t, amount, speed=0.35):
    """Bars of window light sweeping across (time-lapse sun through venetian blinds)."""
    if amount <= 0.01:
        return img
    yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)
    ph = (xx * 0.6 + yy) / (H / 4) * 22 + t * speed * 40
    bars = np.clip((np.sin(ph) - 0.2) * 1.5, 0, 1)
    sweep = np.exp(-(((xx / (W / 4)) - ((t * speed) % 1.6 - 0.3)) / 0.35) ** 2)
    m = cv2.GaussianBlur(bars * sweep, (0, 0), 6.0)
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    return img + m * np.array([1.0, 0.85, 0.6], np.float32) * 0.35 * amount
