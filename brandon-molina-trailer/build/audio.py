import numpy as np, wave
from scipy.signal import fftconvolve, butter, sosfilt
from timeline import *

SR = 48000
N = int(TOTAL * SR)
rng = np.random.default_rng(7)
t_all = np.arange(N) / SR


def env_adsr(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na) ** 2
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'low', fs=SR, output='sos'), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'high', fs=SR, output='sos'), x)


def ir(decay, pre=0.02, seed=0):
    r = np.random.default_rng(seed)
    n = int((decay * 1.4 + pre) * SR)
    tt = np.arange(n) / SR
    out = []
    for ch in range(2):
        noise = r.standard_normal(n) * np.exp(-6.9 * tt / decay)
        noise = lp(noise, 6500) * 0.7 + lp(noise, 2500) * 0.3
        noise[: int(pre * SR)] = 0
        out.append(noise / np.sqrt(np.sum(noise ** 2)))
    return np.stack(out)


def reverb(x, decay, wet, seed=0):
    R = ir(decay, seed=seed)
    y = np.stack([fftconvolve(x, R[c])[: len(x)] for c in range(2)])
    return np.stack([x, x]) * (1 - wet * 0.35) + y * wet


def place(buf, sig, t0, gain=1.0):
    i = int(t0 * SR)
    if sig.ndim == 1:
        sig = np.stack([sig, sig])
    j = min(N, i + sig.shape[1])
    if j > i:
        buf[:, i:j] += sig[:, : j - i] * gain


def note_hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def curve(points):
    """piecewise-linear automation over the whole timeline"""
    xs, ys = zip(*points)
    return np.interp(t_all, xs, ys)


# ---------------- music -----------------
music = np.zeros((2, N))

# heartbeat pulse, lub-dub every ~1.05s, until the cut
pulse = np.zeros(N)
beat = 1.05
for k in range(int(48.6 / beat) + 1):
    for off, g in [(0, 1.0), (0.2, 0.6)]:
        t0 = 0.3 + k * beat + off
        if t0 >= 48.55:
            continue
        n = int(0.5 * SR)
        tt = np.arange(n) / SR
        f = 48 + 30 * np.exp(-tt * 30)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9) * g
        i = int(t0 * SR)
        pulse[i:i + n] += s[: max(0, min(n, N - i))]
pulse_amt = curve([(0, 0.0), (1.0, 0.45), (5, 0.55), (25.8, 0.75), (40.4, 0.95), (48.5, 1.1), (48.6, 0.0), (TOTAL, 0)])
music += np.stack([pulse, pulse]) * pulse_amt * 0.55

# strings: additive detuned saw voices, low-passed; chord progression in D minor
def string_voice(freq, dur, bright=2500, vib=0.004):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    out = np.zeros((2, n))
    for ch, det in enumerate([-0.12, 0.12]):
        for d2 in [-0.07, 0.0, 0.07]:
            f = freq * 2 ** ((det + d2) / 12) * (1 + vib * np.sin(2 * np.pi * (5.1 + d2) * tt + ch))
            ph = 2 * np.pi * np.cumsum(f) / SR + rng.random() * 6
            s = sum(np.sin(h * ph) / h for h in range(1, 12) if h * freq < 9000)
            out[ch] += s
    out = np.stack([lp(out[c], bright, 2) for c in range(2)]) / 6
    return out


chords = [  # (start, dur, midi notes)
    (2.5, 10.2, [38, 45, 50]),            # Dm low drone
    (12.7, 10.7, [34, 41, 50, 53]),       # Bb
    (23.4, 8.0, [41, 48, 53, 57]),        # F
    (31.4, 9.0, [36, 43, 52, 55, 60]),    # C
    (40.4, 4.2, [34, 46, 53, 58, 62]),    # Bb (lift)
    (44.6, 4.0, [41, 53, 57, 60, 65, 69]),  # F major - light breaks
]
for i, (s, d, notes) in enumerate(chords):
    for m in notes:
        br = 1200 + 500 * i + (m - 36) * 25
        v = string_voice(note_hz(m), d + 1.6, bright=br)
        v *= env_adsr(v.shape[1], 1.6 if i < 4 else 0.25, 1.6)
        place(music, v, s, 0.09 / np.sqrt(len(notes)) * (1 + 0.25 * i))
# high violin line for the second half (light breaking through)
vl = np.zeros((2, N))
melody = [(26.0, 4.0, 69), (30.0, 3.2, 72), (33.2, 4.4, 74), (37.6, 2.8, 72), (40.4, 4.2, 74), (44.6, 4.0, 77)]
for s, d, m in melody:
    v = string_voice(note_hz(m), d + 1.2, bright=5000, vib=0.006) * 0.045
    v *= env_adsr(v.shape[1], 0.9, 1.2)
    place(vl, v, s)
music += vl

# shimmer / light: soft bell arpeggios from clip 5 onward
bells = np.zeros((2, N))
arp = [69, 72, 76, 81, 76, 72]
tt0 = 26.0
k = 0
while tt0 < 48.4:
    m = arp[k % len(arp)] + (5 if tt0 > 44.6 else 0)
    n = int(2.5 * SR)
    tt = np.arange(n) / SR
    s = (np.sin(2 * np.pi * note_hz(m) * tt) + 0.3 * np.sin(2 * np.pi * note_hz(m) * 2.01 * tt)) * np.exp(-tt * 2.2)
    pan = 0.5 + 0.4 * np.sin(k)
    place(bells, np.stack([s * (1 - pan), s * pan]), tt0, 0.05)
    step = 0.525 if tt0 < 40.4 else 0.2625
    tt0 += step
    k += 1
bell_amt = curve([(0, 0), (25.8, 0), (30, 0.4), (40.4, 0.7), (48.5, 1.0), (48.6, 0), (TOTAL, 0)])
music += bells * bell_amt


# rises: filtered noise swell + upward tone into big moments
def riser(dur, peak):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = rng.standard_normal(n)
    out = np.zeros(n)
    seg = n // 24
    for j in range(24):
        fc = 300 * (12000 / 300) ** (j / 23)
        a, b = j * seg, (j + 1) * seg if j < 23 else n
        out[a:b] = lp(x, fc)[a:b]
    tone = np.sin(2 * np.pi * np.cumsum(200 * 2 ** (2 * tt / dur)) / SR)
    e = (tt / dur) ** 2.5
    return np.stack([out, np.roll(out, 300)]) * e * peak + tone * e * peak * 0.25


for t_hit, d, g in [(25.8, 2.4, 0.18), (40.4, 3.0, 0.22), (44.6, 1.8, 0.2), (48.6, 3.8, 0.3)]:
    place(music, riser(d, g), t_hit - d)


def impact(g):
    n = int(3.5 * SR)
    tt = np.arange(n) / SR
    f = 36 + 60 * np.exp(-tt * 18)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.2)
    nz = lp(rng.standard_normal(n), 1800) * np.exp(-tt * 12) * 0.5
    dry = (sub + nz) * g
    return reverb(dry, 2.8, 0.5, seed=3)


for t_hit, g in IMPACTS:
    place(music, impact(g * 0.55), t_hit)
for t_hit in SOFT_HITS:
    n = int(1.2 * SR)
    tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * np.cumsum(55 + 40 * np.exp(-tt * 25)) / SR) * np.exp(-tt * 5) * 0.12
    place(music, reverb(s, 1.5, 0.4, seed=5), t_hit)

# global music automation, then cut to near-silence at 48.6
music_amt = curve([(0, 0.8), (5, 0.85), (25.8, 1.0), (40.4, 1.15), (48.55, 1.25), (48.62, 0.0), (TOTAL, 0)])
music *= music_amt
# the impact tail at 48.6 must survive the cut a little: re-place softer
place(music, impact(0.35), 48.6)

# near-silence bed: airy high drone + one low reassuring chord under the title and sky
air = hp(rng.standard_normal(N), 5000) * 0.004
air_amt = curve([(0, 0), (48.6, 0), (49.5, 1), (TOTAL - 1.5, 1), (TOTAL, 0)])
music += np.stack([air, np.roll(air, 999)]) * air_amt
for m in [50, 57, 62, 66]:  # D major, soft: reassurance
    v = string_voice(note_hz(m), 12.5, bright=1600) * 0.045
    v *= env_adsr(v.shape[1], 3.5, 4.0)
    place(music, v, 55.5)
# final gentle bell as the handle appears
n = int(4 * SR); tt = np.arange(n) / SR
s = np.sin(2 * np.pi * note_hz(74) * tt) * np.exp(-tt * 1.3) * 0.06
place(music, reverb(s, 3.5, 0.6, seed=9), HANDLE_IN)

# trailer braams on the big hits
def braam(dur, g):
    n = int(dur * SR); tt = np.arange(n) / SR
    out = np.zeros(n)
    for m in [26, 38, 45, 50]:
        f = note_hz(m) * (1 + 0.003 * np.sin(2 * np.pi * 0.7 * tt))
        ph = 2 * np.pi * np.cumsum(f) / SR
        out += sum(np.sin(h * ph) / h for h in range(1, 24))
    fc = 180 + 2200 * np.exp(-tt * 2.5)
    y = np.zeros(n); seg = n // 40
    for j in range(40):
        a, b = j * seg, (j + 1) * seg if j < 39 else n
        y[a:b] = lp(out, fc[a])[a:b]
    y *= np.minimum(1, tt / 0.03) * np.exp(-tt * 0.9) * g / 4
    return np.tanh(y * 2) / 2


for t_hit, g in [(25.8, 0.5), (40.4, 0.7), (48.6, 0.9)]:
    place(music, reverb(braam(3.2, g), 2.5, 0.35, seed=31), t_hit)


def whoosh(dur, g):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = rng.standard_normal(n)
    y = np.zeros(n); seg = n // 16
    for j in range(16):
        fc = 400 * 16 ** (j / 15)
        a, b = j * seg, (j + 1) * seg if j < 15 else n
        y[a:b] = hp(lp(x, fc * 1.6), fc * 0.5)[a:b]
    e = np.sin(np.pi * (tt / dur) ** 1.6) ** 2
    pan = tt / dur
    return np.stack([y * e * (1 - pan), y * e * pan]) * g


cut_times = [c[1] for c in CLIPS] + [INTERLUDE[0], MONTAGE[0], HOLD[1]]
for tc in cut_times:
    place(music, whoosh(0.7, 0.35), tc - 0.55)
# glitch ticks at cuts + montage stutters
seg_m = (MONTAGE[1] - MONTAGE[0]) / 9
for tc in [c[1] for c in CLIPS] + [MONTAGE[0] + k * seg_m for k in range(9)]:
    n = int(0.08 * SR)
    tk = np.sign(np.sin(2 * np.pi * rng.uniform(900, 2400) * np.arange(n) / SR)) * np.exp(-np.arange(n) / SR * 60) * 0.05
    place(music, tk, tc)

# reverb bus for the music: spacious
music = np.stack([music[0], music[1]])
mw = np.stack([fftconvolve(music[c], ir(3.2, seed=11)[c])[:N] for c in range(2)])
music = music * 0.85 + mw * 0.35

# ---------------- narration -----------------
vo = np.zeros((2, N))
KEY_LINES = {1, 4, 5, 9, 10, 11, 12}
vo_env = np.zeros(N)


def read_wav(p):
    w = wave.open(p)
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    return x


for idx, t0, size in VO:
    x = read_wav(f'{S}/vo/{idx:02d}.wav')
    x = hp(x, 90)
    # gentle warmth + presence
    x = x + 0.25 * lp(x, 250) + 0.15 * hp(x, 3500)
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.5
    x = np.concatenate([x, np.zeros(int(4.5 * SR))])
    decay = 0.9 + 3.6 * size
    wet = 0.10 + 0.32 * size
    y = reverb(x, decay, wet, seed=idx)
    # echo tail: dotted delay taps, darker each repeat
    if idx in KEY_LINES:
        for n_, (dt, g_) in enumerate([(0.375, 0.28), (0.75, 0.16), (1.125, 0.09)]):
            e = lp(x, 3000 - 700 * n_) * g_
            e = np.concatenate([np.zeros(int(dt * SR)), e])[: len(x)]
            ew = reverb(e, decay, 0.6, seed=idx + 20)
            ew[0] *= 1.0 if n_ % 2 == 0 else 0.4
            ew[1] *= 0.4 if n_ % 2 == 0 else 1.0
            y += ew
        # reverse-reverb swell leading into the first word
        head = x[: int(0.7 * SR)]
        rr = reverb(np.concatenate([head, np.zeros(int(2.5 * SR))]), 2.8, 1.0, seed=idx + 40)
        rr = rr - np.stack([np.concatenate([head, np.zeros(int(2.5 * SR))])] * 2) * 0.65
        rr = rr[:, ::-1] * 0.35
        place(vo, rr, t0 - rr.shape[1] / SR + 0.05)
    # warm saturation on the voice
    y = np.tanh(y * 1.4) / 1.4
    place(vo, y, t0)
    i = int(t0 * SR)
    j = min(N, i + int((len(x) / SR - 4.5 + 0.3) * SR))
    vo_env[i:j] = 1

# duck music under narration (smoothed sidechain)
k = int(0.25 * SR)
duck = np.convolve(vo_env, np.ones(k) / k, mode='same')
music *= 1 - 0.45 * duck


def smooth_rms(x, win):
    k = int(win * SR)
    return np.sqrt(np.convolve(np.mean(x ** 2, axis=0), np.ones(k) / k, mode='same') + 1e-12)


# adaptive: keep voice >= 11 dB over music wherever narration is active
vr = smooth_rms(vo * vo_env, 0.6)
mr = smooth_rms(music, 0.6)
g = np.where(duck > 0.05, np.minimum(1.0, (vr / 10 ** (11 / 20)) / mr), 1.0)
g = np.maximum(g, 0.12)
k = int(0.15 * SR)
g = np.convolve(g, np.ones(k) / k, mode='same')
music *= g

mix = music * 0.9 + vo * 1.0
mix = np.tanh(mix * 1.2) / 1.2  # soft safety saturation
mix = mix / np.max(np.abs(mix)) * 0.94
# fade out at the very end
mix[:, int(FADE_OUT[1] * SR - 0.8 * SR):] *= np.linspace(1, 0, int(0.8 * SR))

out = (mix.T * 32767).astype(np.int16)
w = wave.open(f'{S}/mix.wav', 'wb')
w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(out.tobytes()); w.close()
print('ok', mix.shape, 'vo peak', np.max(np.abs(vo)), 'music rms', np.sqrt(np.mean(music ** 2)))

for idx, t0, size in VO:
    i = int(t0 * SR); j = i + int(1.0 * SR)
    rv = np.sqrt(np.mean(vo[:, i:j] ** 2)); rm = np.sqrt(np.mean(music[:, i:j] ** 2))
    print(idx, 'voice-over-music dB', round(20 * np.log10(rv / rm), 1))
