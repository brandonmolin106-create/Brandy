"""Procedurally generate every audio/visual asset so nothing is licensed from anyone else.

Writes assets/pad_loop.wav, whoosh.wav, boom.wav and starfield.png into the current directory.
"""
import os
import numpy as np, wave
from scipy.signal import fftconvolve, butter, sosfilt
from PIL import Image, ImageFilter
SR = 48000
rng = np.random.default_rng(7)
os.makedirs('assets', exist_ok=True)

def write_wav(path, x):
    x = np.clip(x, -1, 1)
    if x.ndim == 1: x = np.stack([x, x], 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())

def note(n):  # MIDI -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)

def reverb_ir(seconds=4.5, predelay=0.03):
    n = int(seconds * SR); t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t / (seconds / 6.5))[:, None]
    ir = sosfilt(butter(2, 6000, 'low', fs=SR, output='sos'), ir, axis=0)
    ir = np.concatenate([np.zeros((int(predelay * SR), 2)), ir])
    return ir / np.sqrt((ir ** 2).sum(0))

# ---------- ambient "cosmic" pad: 8 chords x 8 s = 64 s seamless loop ----------
chords = [[45,52,59,60,67],[41,48,52,57,59],[48,55,59,62,64],[43,50,55,57,62],
          [45,52,59,60,67],[38,45,53,57,60],[41,48,52,57,64],[40,47,52,56,59]]
CH = 8.0; L = int(CH * len(chords) * SR); tail = int(8 * SR)
pad = np.zeros((L + tail, 2))
for i, ch in enumerate(chords):
    n = int((CH + 4) * SR); t = np.arange(n) / SR
    env = np.minimum(1, t / 2.5) * np.clip((CH + 4 - t) / 4, 0, 1) ** 1.5
    voice = np.zeros((n, 2))
    for k, m in enumerate(ch):
        f = note(m)
        for d, pan in ((-0.07, 0.25), (0.0, 0.5), (0.07, 0.75)):   # detuned unison, spread L/R
            ph = rng.uniform(0, 2 * np.pi)
            lfo = 1 + 0.25 * np.sin(2 * np.pi * rng.uniform(0.05, 0.15) * t + ph)
            s = (np.sin(2 * np.pi * (f + d) * t + ph) + 0.18 * np.sin(4 * np.pi * (f + d) * t)) * lfo
            voice[:, 0] += s * (1 - pan); voice[:, 1] += s * pan
    # airy shimmer an octave up on the top note
    voice += 0.12 * np.sin(2 * np.pi * note(ch[-1] + 12) * t)[:, None] * (0.5 + 0.5 * np.sin(2 * np.pi * 0.2 * t))[:, None]
    s0 = int(i * CH * SR)
    pad[s0:s0 + n] += voice[:len(pad) - s0] * env[:len(pad) - s0, None]
pad[:tail] += pad[L:L + tail]; pad = pad[:L]                      # wrap the tail -> seamless loop
# filter two periods and keep the second, so the filter state matches at the loop seam (no click)
pad = sosfilt(butter(2, 2200, 'low', fs=SR, output='sos'), np.concatenate([pad, pad]), axis=0)[L:]
wet = fftconvolve(np.concatenate([pad, pad]), reverb_ir(), axes=0)[L:2 * L]  # circular-ish reverb for looping
pad = 0.45 * pad + 0.55 * wet
pad *= 10 ** (-16 / 20) / np.sqrt(np.mean(pad ** 2))             # ~-16 dBFS RMS
write_wav('assets/pad_loop.wav', pad * 0.9)

# ---------- whoosh: noise through a resonant low-pass sweeping up then down ----------
def whoosh(dur=0.75, f0=250, f1=4200, peak=0.55):
    n = int(dur * SR); t = np.arange(n) / SR; x = rng.standard_normal(n)
    pos = t / dur
    fc = np.where(pos < peak, f0 + (f1 - f0) * (pos / peak) ** 2,
                  f1 - (f1 - f0 * 1.5) * (np.clip(pos - peak, 0, None) / (1 - peak)) ** 0.7)
    y = np.zeros(n); low = band = 0.0; q = 0.35
    for i in range(n):                                             # Chamberlin state-variable filter
        g = 2 * np.sin(np.pi * min(fc[i], SR / 6) / SR)
        low += g * band; high = x[i] - low - q * band; band += g * high; y[i] = 0.6 * low + 0.4 * band
    env = np.where(pos < peak, (pos / peak) ** 2.2, ((1 - pos) / (1 - peak)) ** 1.6)
    y *= env; pan = np.clip(pos, 0, 1)
    st = np.stack([y * np.cos(pan * np.pi / 2), y * np.sin(pan * np.pi / 2)], 1)
    st = 0.7 * st + 0.3 * fftconvolve(st, reverb_ir(1.2), axes=0)[:n]
    return st / np.abs(st).max() * 0.5
write_wav('assets/whoosh.wav', whoosh())

# ---------- cinematic boom for the title hit ----------
n = int(3.5 * SR); t = np.arange(n) / SR
f = 38 + 52 * np.exp(-t * 6); boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.3)
click = rng.standard_normal(n) * np.exp(-t * 60) * 0.35
b = np.stack([boom + click] * 2, 1); b = 0.75 * b + 0.25 * fftconvolve(b, reverb_ir(3.0), axes=0)[:n]
write_wav('assets/boom.wav', b / np.abs(b).max() * 0.8)

# ---------- starfield + nebula backdrop (oversized so we can drift/zoom it) ----------
W, H = 2304, 1296
yy, xx = np.mgrid[0:H, 0:W] / np.array([H, W])[:, None, None]
img = np.zeros((H, W, 3))
img += np.array([4, 5, 16]) * (1 - yy[..., None]) + np.array([1, 1, 6]) * yy[..., None]
for _ in range(9):                                                # nebula clouds: purple / teal / magenta
    cx, cy, r = rng.uniform(0.1, 0.9), rng.uniform(0.15, 0.85), rng.uniform(0.12, 0.35)
    col = np.array([[120, 50, 200], [30, 140, 190], [190, 50, 150], [70, 60, 220]][rng.integers(4)])
    d = ((xx - cx) ** 2 * (W / H) ** 2 + (yy - cy) ** 2) / r ** 2
    img += col * np.exp(-d * 2.2)[..., None] * rng.uniform(0.10, 0.28)
noise = Image.fromarray((rng.random((H // 8, W // 8)) * 255).astype('uint8')).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(18))
img *= (0.55 + 0.9 * np.asarray(noise)[..., None] / 255)
stars = np.zeros((H, W))
for _ in range(2600):
    x, y = rng.integers(0, W), rng.integers(0, H); stars[y, x] = rng.uniform(0.25, 1) ** 2.5
glow = np.asarray(Image.fromarray((stars * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(2.2))) / 255
img += (stars * 255 + glow * 900)[..., None] * np.array([0.9, 0.95, 1.0])
Y, X = np.mgrid[0:H, 0:W]
for _ in range(14):                                               # a few big stars: float glow + bright core
    x, y = rng.integers(40, W - 40), rng.integers(40, H - 40)      # (blurring a uint8 image left grey squares)
    r2 = (X - x) ** 2 + (Y - y) ** 2
    img += (np.exp(-r2 / (2 * 7.0 ** 2)) * 60 + np.exp(-r2 / (2 * 1.6 ** 2)) * 230)[..., None] * np.array([0.8, 0.9, 1.0])
vign = 1 - 0.55 * (((xx - 0.5) ** 2 + (yy - 0.5) ** 2) / 0.5) ** 1.2
img = np.clip(img * vign[..., None], 0, 255).astype('uint8')
Image.fromarray(img).save('assets/starfield.png')
print("assets done")
