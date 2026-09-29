import cv2, numpy as np, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
from timeline import *

F = f'{S}/fonts/x/'
rng = np.random.default_rng(3)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
nx, ny = (xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)


def smooth(a, b, x):
    x = np.clip((x - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


# ---------------- static layers ----------------
vignette = (1 - 0.62 * np.clip((nx ** 2 * 0.9 + ny ** 2 * 0.55), 0, 1.4) ** 1.3).clip(0.15, 1)[..., None]
# top / bottom shadow bands (deep shadows, also hide burned-in captions)
band = (smooth(0.07, 0.33, yy / H) * (1 - smooth(0.80, 1.0, yy / H)) * 0.94 + 0.06)[..., None]


def make_sky(seed, w=W, h=int(H * 1.25)):
    r = np.random.default_rng(seed)
    y = np.linspace(0, 1, h)[:, None, None]
    top = np.array([0.012, 0.018, 0.045]); bot = np.array([0.03, 0.05, 0.10])
    sky = (top * (1 - y) + bot * y) * np.ones((h, w, 3))
    # faint haze / milky band
    hz = cv2.GaussianBlur(r.random((h // 16, w // 16)).astype(np.float32), (0, 0), 3)
    hz = cv2.resize(hz, (w, h))[..., None]
    diag = np.exp(-((np.arange(w)[None, :] * 0.6 - np.arange(h)[:, None] * 0.35 - w * 0.1) / (w * 0.35)) ** 2)[..., None]
    sky += hz * diag * np.array([0.05, 0.06, 0.11]) * 1.2
    stars = np.zeros((h, w), np.float32)
    n = 2600
    sx, sy = r.integers(0, w, n), r.integers(0, h, n)
    br = r.random(n) ** 6
    stars[sy, sx] = br * 0.9 + 0.08
    big = r.random(n) < 0.02
    glow = np.zeros_like(stars)
    glow[sy[big], sx[big]] = 3.0
    stars = stars + cv2.GaussianBlur(glow, (0, 0), 2.2)
    return sky.astype(np.float32), stars, (sx, sy, r.random(n) * 6.28)


SKY, STARS, STAR_PTS = make_sky(1)


def sky_frame(t, drift=18.0, twinkle=True, bright=1.0):
    off = int(t * drift) % (SKY.shape[0] - H)
    base = SKY[off:off + H]
    st = STARS[off:off + H]
    if twinkle:
        st = st * (0.8 + 0.2 * np.sin(t * 2.3 + xx * 0.013 + yy * 0.021))
    return base + st[..., None] * np.array([0.85, 0.9, 1.0], np.float32) * bright


# rain-lit window: droplet bokeh on glass + sliding drips + falling streaks
def make_glass(seed):
    r = np.random.default_rng(seed)
    g = np.zeros((H, W), np.float32)
    for _ in range(900):
        x, y, rad = r.integers(0, W), r.integers(0, H), r.integers(2, 9)
        cv2.circle(g, (int(x), int(y)), int(rad), float(r.uniform(0.2, 0.9)), -1, cv2.LINE_AA)
    g = cv2.GaussianBlur(g, (0, 0), 1.6)
    bokeh = np.zeros((H, W), np.float32)
    for _ in range(60):
        x, y, rad = r.integers(0, W), r.integers(0, H), r.integers(25, 90)
        cv2.circle(bokeh, (int(x), int(y)), int(rad), float(r.uniform(0.1, 0.35)), -1, cv2.LINE_AA)
    bokeh = cv2.GaussianBlur(bokeh, (0, 0), 14)
    return g, bokeh


GLASS, BOKEH = make_glass(5)
DRIPS = [(rng.uniform(0, W), rng.uniform(-H, H), rng.uniform(60, 180), rng.uniform(3, 6)) for _ in range(28)]
STREAKS = rng.random((260, 3))


def rain_layer(t):
    lay = GLASS * 0.35 + BOKEH
    lay = lay.copy()
    for x, y0, v, rad in DRIPS:
        y = (y0 + v * t) % (H * 1.2) - 0.1 * H
        cv2.line(lay, (int(x), int(y - 60)), (int(x + 2), int(y)), 0.35, int(rad * 0.5), cv2.LINE_AA)
        cv2.circle(lay, (int(x + 2), int(y)), int(rad), 0.8, -1, cv2.LINE_AA)
    for sx, sy, sp in STREAKS:
        x = sx * W + 0.18 * ((sy * H + t * (1800 + 900 * sp)) % H)
        y = (sy * H + t * (1800 + 900 * sp)) % H
        cv2.line(lay, (int(x), int(y)), (int(x + 9), int(y + 50)), 0.18, 1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 1.0)
    # cool city-light tint through the glass
    return lay[..., None] * np.array([0.55, 0.7, 1.0], np.float32)


GRAIN = [cv2.resize(rng.standard_normal((H // 2, W // 2)).astype(np.float32), (W, H))[..., None] for _ in range(6)]

# ---------------- text ----------------
def font(name, size):
    return ImageFont.truetype(F + name, size)


def text_img(txt, fnt, tracking=0, fill=(235, 238, 245)):
    """RGBA text with optional letter-spacing, returned as float arrays"""
    widths = [fnt.getlength(c) for c in txt]
    tw = int(sum(widths) + tracking * (len(txt) - 1)) + 40
    asc, desc = fnt.getmetrics()
    im = Image.new('L', (tw, asc + desc + 30), 0)
    d = ImageDraw.Draw(im)
    x = 20
    for c, w_ in zip(txt, widths):
        d.text((x, 15), c, font=fnt, fill=255)
        x += w_ + tracking
    a = np.asarray(im).astype(np.float32) / 255
    return a, np.array(fill, np.float32) / 255


def put_text(img, a, color, cx, cy, alpha, glow=0.0, blur=0.0):
    if alpha <= 0.001:
        return img
    if blur > 0.3:
        a = cv2.GaussianBlur(a, (0, 0), blur)
    h, w = a.shape
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xs0, ys0 = max(0, -x0), max(0, -y0)
    x1, y1 = min(W, x0 + w), min(H, y0 + h)
    x0c, y0c = max(0, x0), max(0, y0)
    sub = a[ys0:ys0 + (y1 - y0c), xs0:xs0 + (x1 - x0c)][..., None] * alpha
    reg = img[y0c:y1, x0c:x1]
    if glow > 0:
        gl = cv2.GaussianBlur(sub[..., 0], (0, 0), 12)[..., None] * glow
        reg[:] = reg + gl * color
    # dark soft shadow for legibility
    sh = cv2.GaussianBlur(sub[..., 0], (0, 0), 6)[..., None] * 0.55
    reg[:] = reg * (1 - sh)
    reg[:] = reg * (1 - sub) + color * sub
    return img


F_SUB = font('inter-latin-400-normal.woff', 44)
F_MONO = font('jetbrains-mono-latin-400-normal.woff', 30)
F_MONO_S = font('jetbrains-mono-latin-300-normal.woff', 26)
F_TITLE = font('cormorant-garamond-latin-500-normal.woff', 88)
F_TAG = font('cormorant-garamond-latin-400-normal.woff', 54)
F_HANDLE = font('inter-latin-300-normal.woff', 50)


def wrap(txt, fnt, maxw):
    words, lines, cur = txt.split(), [], ''
    for w_ in words:
        test = (cur + ' ' + w_).strip()
        if fnt.getlength(test) > maxw and cur:
            lines.append(cur); cur = w_
        else:
            cur = test
    lines.append(cur)
    return lines


SUBS = []
for (idx, t0, _), txt in zip(VO, VO_TEXT):
    import wave
    wv = wave.open(f'{S}/vo/{idx:02d}.wav'); d = wv.getnframes() / wv.getframerate()
    SUBS.append((t0 - 0.15, t0 + d + 0.55, [text_img(l, F_SUB, 1) for l in wrap(txt, F_SUB, 860)]))

TITLE = text_img('BRANDON MOLINA', F_TITLE, 9)
TAG = text_img('A place to pause. A voice to come back to.', F_TAG, 1, fill=(215, 222, 235))
HANDLE = text_img('@brandonmolina651', F_HANDLE, 6)
CLOCK = [text_img(s, F_MONO, 4, fill=(170, 185, 210)) for s in ['2:47 AM', '2:47 AM ·  can\'t sleep']]
COUNTER = [text_img(f'{i + 1:02d} / 09', F_MONO_S, 6, fill=(170, 185, 210)) for i in range(9)]

# ---------------- clips ----------------
class Clip:
    def __init__(self, p, dur, base_zoom=1.22):
        self.p = p
        self.cap = cv2.VideoCapture(f"{S}/src/{p['v']}.mp4")
        self.sfps = self.cap.get(cv2.CAP_PROP_FPS)
        self.cap.set(cv2.CAP_PROP_POS_MSEC, p['t0'] * 1000)
        self.cur_t = p['t0'] - 1 / self.sfps
        self.frame = None
        sw, sh = int(self.cap.get(3)), int(self.cap.get(4))
        # letterbox detection
        c2 = cv2.VideoCapture(f"{S}/src/{p['v']}.mp4")
        acc = np.zeros(sh)
        for k in range(8):
            c2.set(cv2.CAP_PROP_POS_MSEC, (p['t0'] + k * dur / 8) * 1000)
            ok, f = c2.read()
            if ok:
                acc += f.mean(axis=(1, 2))
        rows = np.where(acc / 8 > 10)[0]
        top, bot = (rows[0], rows[-1]) if len(rows) else (0, sh)
        lbox = (bot - top) < sh * 0.8
        self.ctop, self.cbot = top + (4 if lbox else 0), bot - (4 if lbox else 0)
        ch_full = min(self.cbot - self.ctop, sw * 16 / 9)
        z = 1.0 if lbox else base_zoom
        self.ch0 = ch_full / z
        fx, fy, fw, fh = p['face']
        self.fcx, self.fcy = fx + fw / 2, fy + fh / 2
        self.sw, self.sh = sw, sh
        self.dur = dur
        # exposure normalisation from face patch
        c2.set(cv2.CAP_PROP_POS_MSEC, (p['t0'] + dur / 2) * 1000)
        ok, f = c2.read()
        patch = f[int(fy):int(fy + fh), int(fx):int(fx + fw)]
        m = patch.mean() / 255 if patch.size else 0.3
        self.gain = float(np.clip(0.42 / max(m, 0.03), 0.7, 3.4))

    def get(self, lt):
        """frame at local time lt, returned raw BGR uint8"""
        target = self.p['t0'] + lt
        while self.frame is None or self.cur_t + 1 / self.sfps <= target + 1e-6:
            ok, f = self.cap.read()
            if not ok:
                break
            self.frame = f
            self.cur_t += 1 / self.sfps
        return self.frame

    def render(self, lt, push=0.07, face_y=0.40):
        f = self.get(lt)
        k = lt / self.dur
        ch = self.ch0 / (1 + push * smooth(0, 1, k))
        cw = ch * 9 / 16
        cx = np.clip(self.fcx, cw / 2, self.sw - cw / 2)
        cy = np.clip(self.fcy - (face_y - 0.5) * ch, self.ctop + ch / 2, self.cbot - ch / 2)
        s = W / cw
        M = np.float32([[s, 0, W / 2 - s * cx], [0, s, H / 2 - s * cy]])
        out = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return out[..., ::-1].astype(np.float32) / 255


def grade(img, gain, light):
    """light: 0 = cold/intimate, 1 = warm light breaking through"""
    img = np.clip(img * gain, 0, 1.4)
    lum = img @ np.array([0.299, 0.587, 0.114], np.float32)
    lum = lum[..., None]
    sat = 0.45 + 0.35 * light
    img = lum + (img - lum) * sat
    # split tone: teal shadows, warmer highlights as light grows
    sh_t = np.array([0.86, 0.98, 1.12], np.float32)
    hi_t = np.array([1.0 + 0.08 * light, 1.0 + 0.02 * light, 1.0 - 0.06 * light], np.float32)
    w = np.clip(lum * 1.6, 0, 1)
    img = img * (sh_t * (1 - w) + hi_t * w)
    # filmic contrast
    img = np.clip(img, 0, 1.5)
    img = img ** 1.08
    img = np.clip((img - 0.035) / 0.965, 0, 1.2)
    img = img ** 1.3 * 1.05
    return img


def flash_amt(t):
    a = 0.0
    for th, g in IMPACTS:
        if th <= t < th + 0.8:
            a += g * np.exp(-(t - th) * 7)
    for th in SOFT_HITS:
        if th <= t < th + 0.5:
            a += 0.18 * np.exp(-(t - th) * 10)
    return a


def light_level(t):
    return float(np.interp(t, [0, 25.8, 40.4, 44.6, 48.6, 49.5, 61], [0, 0.15, 0.55, 0.85, 1.0, 0.45, 0.45]))


LEAK = np.exp(-(((xx - W * 0.85) / (W * 0.6)) ** 2 + ((yy - H * 0.05) / (H * 0.45)) ** 2))[..., None] * np.array([1.0, 0.72, 0.42], np.float32)

# per-video framing overrides (zoom, face position) to crop out burned-in captions
OVR = {'7677257839844347143': (1.7, 0.36), '7651262992369077522': (1.65, 0.36), '7685934513406364936': (1.35, 0.40)}
# extra lower shadow for the clip with a burned-in bottom caption
LOWMASK_V = {'7685934513406364936'}
LOWMASK = (1 - 0.97 * smooth(0.60, 0.69, yy / H))[..., None]
clips = [Clip(PICKS[i], e - s, base_zoom=OVR.get(PICKS[i]['v'], (1.22, 0.40))[0]) for i, s, e in CLIPS]
hold = Clip(PICKS[HOLD[0]], HOLD[2] - HOLD[1], base_zoom=1.18)
glimpse = Clip(PICKS[HOLD[0]], 1.0, base_zoom=1.3)
# montage: short bits from later in each video
mont = []
seg = (MONTAGE[1] - MONTAGE[0]) / 9
for k, (i, s, e) in enumerate(CLIPS):
    p = dict(PICKS[i]); p['t0'] = p['t0'] + (e - s) + 0.6
    mont.append(Clip(p, seg, base_zoom=1.45))


def rain_amt(t):
    return float(np.interp(t, [0, 5, 10, 15.2, 18.8, 23.4, 24.0, 25.8, 26, 33.2, 33.6, 37.4, 37.8, 68],
                              [0, 0.35, 0.45, 0.35, 0.0, 0.0, 0.9, 0.9, 0.0, 0.0, 0.75, 0.75, 0.0, 0]))


def star_amt(t):
    return float(np.interp(t, [0, 30, 30.3, 33, 33.2, 68], [0.22, 0.22, 0.7, 0.7, 0.22, 0.22]))


def clip_fade(lt, dur, fin=0.35, fout=0.35):
    return smooth(0, fin, lt) * (1 - smooth(dur - fout, dur, lt))


def frame(t):
    L = light_level(t)
    img = np.zeros((H, W, 3), np.float32)
    person = None
    person_a = 0.0
    # ---- intro ----
    if t < CLIPS[0][1]:
        img = sky_frame(t, drift=8) * smooth(0.8, 4.2, t)
        # pulse glow in darkness
        pl = max(0.0, np.sin((t - 0.3) / 1.05 * 2 * np.pi)) ** 8 * smooth(0, 1.5, t) * (1 - smooth(4.5, 5.0, t))
        img += np.exp(-((nx) ** 2 + (ny * 0.56) ** 2) * 6)[..., None] * np.array([0.12, 0.16, 0.3], np.float32) * pl * 0.5
        if GLIMPSE[0] <= t < GLIMPSE[1]:
            lt = t - GLIMPSE[0]
            fl = [1, 0.2, 0.9, 0, 0.6, 0.3, 0.7, 0.1][int(lt * 16) % 8]
            g = grade(glimpse.render(0.5 + lt, push=0.0), glimpse.gain * 0.5, 0) * vignette * band
            img = img * (1 - fl * 0.8) + g * fl * 0.8
        # tail blends into clip 1
        if t > 4.6:
            person_a = smooth(4.6, 5.0, t)
    # ---- nine clips ----
    for k, (i, s, e) in enumerate(CLIPS):
        if s - 0.35 <= t < e + 0.05:
            c = clips[k]
            lt = max(0.0, t - s)
            fin = 0.9 if k == 0 else (0.5 if k == 4 else 0.3)
            fout = 0.9 if k == 3 else 0.3
            a = clip_fade(lt, e - s, fin, fout)
            push = 0.06 + 0.02 * k
            fr = grade(c.render(lt, push=push, face_y=OVR.get(c.p['v'], (1.22, 0.40))[1]), c.gain, L) * vignette * band
            if c.p['v'] in LOWMASK_V:
                fr = fr * LOWMASK
            img = img * (1 - a) + fr * a
    # ---- interlude: night sky through a rain-lit window ----
    if INTERLUDE[0] - 0.9 <= t < INTERLUDE[1] + 0.3:
        a = smooth(INTERLUDE[0] - 0.9, INTERLUDE[0] + 0.2, t) * (1 - smooth(INTERLUDE[1] - 0.1, INTERLUDE[1] + 0.3, t))
        z = 1 + 0.08 * smooth(INTERLUDE[0], INTERLUDE[1], t)
        sk = sky_frame(t, drift=40, bright=1.3)
        sk = cv2.resize(sk, None, fx=z, fy=z)[int((H * z - H) / 2):int((H * z - H) / 2) + H, int((W * z - W) / 2):int((W * z - W) / 2) + W]
        img = img * (1 - a) + sk * a
    # ---- montage ----
    if MONTAGE[0] <= t < MONTAGE[1]:
        k = min(8, int((t - MONTAGE[0]) / seg))
        lt = t - MONTAGE[0] - k * seg
        c = mont[k]
        fr = grade(c.render(lt, push=0.12), c.gain, L) * vignette * band
        a = smooth(0, 0.06, lt)
        img = img * (1 - a) + fr * a
    # ---- hold: direct look into the camera ----
    if HOLD[1] - 0.05 <= t < HOLD[2] + 0.8:
        lt = min(t - HOLD[1], HOLD[2] - HOLD[1] - 0.01)
        c = hold
        dim = 1 - 0.62 * smooth(TITLE_IN - 0.5, TITLE_IN + 1.5, t)
        fr = grade(c.render(max(lt, 0), push=0.16, face_y=0.42), c.gain * 0.95, L) * vignette * band * dim
        a = smooth(HOLD[1] - 0.05, HOLD[1] + 0.05, t) * (1 - smooth(HOLD[2] - 0.4, HOLD[2] + 0.8, t))
        img = img * (1 - a) + fr * a
    # ---- final sky ----
    if t >= SKY_START - 0.4:
        a = smooth(SKY_START - 0.4, SKY_START + 1.2, t)
        sk = sky_frame(t, drift=10, bright=1.1)
        # soft horizon glow: reassurance
        sk += np.exp(-((yy - H * 1.05) / (H * 0.35)) ** 2)[..., None] * np.array([0.10, 0.09, 0.12], np.float32)
        img = img * (1 - a) + sk * a

    # ---- overlays ----
    if t >= CLIPS[0][1] - 0.4 and t < SKY_START:
        off = int(t * 14) % (SKY.shape[0] - H)
        st = (STARS[off:off + H] * star_amt(t))[..., None] * np.array([0.85, 0.9, 1.0], np.float32)
        img = 1 - (1 - img) * (1 - np.clip(st, 0, 1))  # screen
    ra = rain_amt(t)
    if ra > 0.01:
        rl = rain_layer(t) * ra
        img = 1 - (1 - np.clip(img, 0, 1)) * (1 - np.clip(rl, 0, 1))
        img *= (1 - 0.15 * ra)
    if L > 0.02 and t < SKY_START:
        breath = 0.85 + 0.15 * np.sin(t * 1.3)
        img += LEAK * (0.35 * L * breath)
    fa = flash_amt(t)
    if fa > 0.005:
        img += np.array([1.0, 0.95, 0.88], np.float32) * fa
    # thin light sweep line on the big cuts
    for th, g in IMPACTS:
        if th <= t < th + 0.45:
            p_ = (t - th) / 0.45
            y = int(H * (0.2 + 0.6 * p_))
            img[max(0, y - 1):y + 2] += 0.6 * g * (1 - p_)

    # ---- motion graphics ----
    # clock in the intro
    if 1.1 <= t < 4.9:
        a = smooth(1.1, 1.6, t) * (1 - smooth(4.4, 4.9, t))
        ci = 1 if t > 2.9 else 0
        ta, tc = CLOCK[ci]
        n_show = int(np.clip((t - 1.1) * 18, 0, ta.shape[1]))
        vis = ta.copy(); vis[:, int(ta.shape[1] * min(1, (t - 1.1) / (0.6 if ci == 0 else 2.2))):] = 0
        img = put_text(img, vis, tc, W / 2, H * 0.62, a * 0.9)
        ln = int(W * 0.3 * smooth(1.2, 2.4, t))
        img[int(H * 0.655):int(H * 0.655) + 2, W // 2 - ln // 2:W // 2 + ln // 2] += 0.35 * a
    # clip counter + progress line
    for k, (i, s, e) in enumerate(CLIPS):
        if s <= t < e:
            a = smooth(s, s + 0.4, t) * (1 - smooth(e - 0.3, e, t)) * 0.75
            ta, tc = COUNTER[k]
            img = put_text(img, ta, tc, 150, H * 0.085, a)
            pr = (t - s) / (e - s)
            x0 = 64
            img[int(H * 0.085) + 26:int(H * 0.085) + 28, x0:x0 + int(170 * pr)] += 0.5 * a
            img[int(H * 0.085) + 26:int(H * 0.085) + 28, x0:x0 + 170] += 0.12 * a
    # subtitles
    for s0, s1, lines in SUBS:
        if s0 <= t < s1:
            a = smooth(s0, s0 + 0.3, t) * (1 - smooth(s1 - 0.35, s1, t))
            y0 = H * 0.80 - (len(lines) - 1) * 30
            for j, (la, lc) in enumerate(lines):
                img = put_text(img, la, lc, W / 2, y0 + j * 60, a * 0.95, blur=(1 - a) * 3)
    # title + tagline: tracking-in reveal
    if t >= TITLE_IN:
        a = smooth(TITLE_IN, TITLE_IN + 1.6, t) * (1 - smooth(SKY_START + 0.2, SKY_START + 1.0, t))
        ta, tc = TITLE
        sc = 1.12 - 0.12 * smooth(TITLE_IN, TITLE_IN + 3.5, t)
        tas = cv2.resize(ta, None, fx=sc, fy=1.0)
        img = put_text(img, tas, tc, W / 2, H * 0.48, a, glow=0.35 * a, blur=(1 - a) * 6)
        ln = int(W * 0.46 * smooth(TITLE_IN + 0.6, TITLE_IN + 2.0, t))
        img[int(H * 0.515):int(H * 0.515) + 2, W // 2 - ln // 2:W // 2 + ln // 2] += 0.5 * a
        b = smooth(TAG_IN, TAG_IN + 1.4, t) * (1 - smooth(SKY_START + 0.2, SKY_START + 1.0, t))
        ta, tc = TAG
        img = put_text(img, ta, tc, W / 2, H * 0.555, b, blur=(1 - b) * 4)
    if t >= HANDLE_IN:
        a = smooth(HANDLE_IN, HANDLE_IN + 1.5, t)
        ta, tc = HANDLE
        img = put_text(img, ta, tc, W / 2, H * 0.5, a, glow=0.3 * a, blur=(1 - a) * 5)
        ln = int(W * 0.18 * smooth(HANDLE_IN + 0.5, HANDLE_IN + 1.8, t))
        img[int(H * 0.535):int(H * 0.535) + 2, W // 2 - ln // 2:W // 2 + ln // 2] += 0.4 * a

    # grain + final fade
    img = img + GRAIN[int(t * FPS) % 6] * 0.022
    img *= 1 - smooth(*FADE_OUT, t)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'stills':
        import time
        ts = [float(x) for x in sys.argv[2].split(',')]
        for t in ts:
            # clips read forward, so rebuild readers per still
            for c in clips + mont + [hold, glimpse]:
                c.cap.set(cv2.CAP_PROP_POS_MSEC, c.p['t0'] * 1000); c.cur_t = c.p['t0'] - 1 / c.sfps; c.frame = None
            im = frame(t)
            cv2.imwrite(f'{S}/sheets/st_{t:05.1f}.jpg', (im[..., ::-1] * 255).astype(np.uint8)[::2, ::2])
        sys.exit()
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-i', f'{S}/mix.wav', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', '-shortest', f'{S}/trailer.mp4'], stdin=subprocess.PIPE)
    nfr = int(TOTAL * FPS)
    for n in range(nfr):
        ff.stdin.write((frame(n / FPS) * 255 + 0.5).astype(np.uint8).tobytes())
        if n % 150 == 0:
            print(n, '/', nfr, flush=True)
    ff.stdin.close(); ff.wait()
    print('done')
