"""Echoes in the Dark v3 - the 8:00 score.

The whole v2 score is rebuilt with every event re-timed through timeline3.m() (so it
follows the v2 story into its new slots), then four new cues fill the inserted gaps:
  C  the star over ice and fire     A  RISE / BURN / ECHO hyper montage
  B  monuments over ice and fire    D  hyper recap into dead black before the SLAM
plus a stab/whoosh/hit on every new hard cut.

  python3 audio3.py   -> out3/soundtrack_raw.wav (48 kHz stereo float)
"""
import os

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly, sosfilt

import audio as K
import audio2 as A2
import timeline2 as V2
import importlib
from audio import (NOTE, SR, bell, choir, echo, env_adsr, heartbeat, make_ir, noise_swell, pad, pan_st, reverb,
                   sos_bp, sos_hp, sos_lp, sub_hit, taiko, tick, whoosh)
from audio2 import (braam2, card_slam, crackle, debris, glitch, hit_stack, pulse_bass, reverse_swell, screech,
                    shepard, stab, thunder, tremolo, wind_bed)

HERE = os.path.dirname(os.path.abspath(__file__))
T = importlib.import_module(os.environ.get("TRAILER_TIMELINE", "timeline3"))
OUT = os.path.join(HERE, os.environ.get("TRAILER_OUT", "out3"))
N = int(T.DURATION * SR) + SR
A2.N = K.N = N
rng = np.random.default_rng(303)
BEAT, BAR = 0.5, 2.0
REMAP = [True]


class MapBus(A2.Bus32):
    """float32 bus; while REMAP is on, every event time is v2 time and gets mapped to v3."""

    def add(self, t0, *a, **k):
        return super().add(T.m(t0) if REMAP[0] else t0, *a, **k)


def build():
    A2.Bus32 = MapBus
    mus, sfx, wet = A2.build()          # the whole v2 score, re-timed
    REMAP[0] = False

    def M(t0, sig, g, pan=0.0, width=0.0, send=0.3):
        mus.add(t0, sig, g, pan, width)
        wet.add(t0, sig, g * send, pan, width)

    def X(t0, sig, g, pan=0.0, width=0.0, send=0.4):
        sfx.add(t0, sig, g, pan, width)
        wet.add(t0, sig, g * send, pan, width)

    def HIT(t0, g=1.0, pre=1.2):
        X(t0 - pre, reverse_swell(pre), 0.35 * g, width=1, send=0.6)
        X(t0, hit_stack(g, 5.0), 0.9 * g, width=1, send=0.6)

    def grid(a, b, root_seq, inten, fast=False, rolls=False):
        t0, i = a, 0
        while t0 < b - 1e-6:
            root = NOTE[root_seq[i % len(root_seq)]]
            step = BEAT / 4 if fast else BEAT / 2
            for k in range(int(round(BAR / step))):
                tk = t0 + k * step
                if tk >= b:
                    break
                M(tk, pulse_bass(root * (2 if k % 8 == 6 else 1), 0.2), 0.17 * inten * (1.0 if k % 4 == 0 else 0.7),
                  send=0.08)
            X(t0, taiko(1.6, 95, 48), 0.58 * inten, send=0.5)
            X(t0 + 2 * BEAT, taiko(1.4, 110, 55), 0.48 * inten, send=0.5)
            for kk in (1.5, 3.0, 3.5):
                X(t0 + kk * BEAT, taiko(0.9, 150, 80), 0.3 * inten, pan=rng.uniform(-0.5, 0.5), send=0.4)
            if rolls:
                for kk in range(8):
                    X(t0 + kk * BEAT / 2, taiko(0.5, 190, 110), 0.15 * inten, pan=0.5 if kk % 2 else -0.5, send=0.3)
            for kk in range(8):
                X(t0 + kk * BEAT / 2, tick(kk % 2 == 0), 0.05 * inten, pan=0.3 if kk % 2 else -0.3, send=0.08)
            X(t0, braam2(root / 2, BAR + 1.5, 0.7 + 0.4 * inten), 0.34 * inten, width=1, send=0.5)
            t0 += BAR
            i += 1

    def strikes(a, b):
        for ts, kind in T.NEW_STRIKES:
            if a <= ts < b:
                X(ts, thunder(6.0, 0.25 if kind != "sky" else 0.6), 0.6, width=1, send=0.4)
                if kind == "emblem":
                    X(ts, crackle(1.2, 160), 0.28, width=1, send=0.2)
                    X(ts, hit_stack(0.6, 2.5), 0.5, width=1, send=0.5)

    # ---- C: the star over ice (55-65.7), then fire (65.7-75)
    c0 = T.C0
    X(c0 - 0.5, reverse_swell(0.5), 0.4, width=1)
    HIT(c0, 0.6, pre=0.01)
    wb = wind_bed(10.7)
    X(c0, wb * env_adsr(len(wb), 0.5, 1, 1, 1.0), 0.14, width=1, send=0.2)
    M(c0, choir(["D3", "F3", "A3", "D4"], 11.0, att=1.5, rel=2.0), 0.26, width=1, send=0.8)
    M(c0, pad(["D3", "A3", "D4", "F4"], 11.0, fc=2400, att=1.0, rel=2.0), 0.16, width=1, send=0.7)
    for i, tb in enumerate(np.arange(c0 + 0.5, c0 + 10.5, 1.25)):
        X(tb, echo(bell(NOTE[["A5", "D6", "F6", "E6"][i % 4]], 3.0) * 0.5, 0.42, 0.45, 5), 0.07,
          pan=rng.uniform(-0.7, 0.7))
    for r in T.RINGS:
        if c0 <= r < c0 + 20:
            X(r, heartbeat(1.1), 0.55, send=0.15)
    v = c0 + 10.7
    X(v - 1.0, noise_swell(1.0, 400, 9000), 0.35, width=1)
    HIT(v, 0.9, pre=0.01)
    X(v, braam2(NOTE["D1"], 6.0, 1.3), 0.65, width=1, send=0.6)
    X(v, sub_hit(6.0, 60, 28), 0.5, send=0.3)
    X(v, debris(4.0, 70), 0.25, width=1, send=0.5)
    X(v, crackle(8.0, 70), 0.14, width=1, send=0.2)
    M(v, tremolo(["D4", "D#4", "A3", "D5"], 9.3, rate=16, att=2.0, rel=0.5), 0.1, width=1, send=0.5)
    for k, tk in enumerate(np.arange(v + 1.0, c0 + 19.0, BEAT / 2)):
        X(tk, taiko(0.8, 120, 60), 0.12 + 0.3 * (tk - v) / 8, pan=0.4 if k % 2 else -0.4, send=0.4)
    strikes(c0, c0 + 20)
    for tc in T.CUTS:
        if c0 < tc < c0 + 20 and abs(tc - v) > 0.05:
            X(tc - 0.3, whoosh(0.35, rev=True), 0.25, width=1, send=0.3)
            X(tc, stab(NOTE["D3"] * 2 ** (rng.integers(0, 4) / 12), 0.4, 1.0), 0.4, width=1, send=0.4)
    X(c0 + 19.0, screech(1.0), 0.18, width=1, send=0.6)

    # ---- A: RISE / BURN / ECHO hyper montage (198-238)
    a0 = T.A0
    HIT(a0, 0.9, pre=0.01)
    X(a0, braam2(NOTE["D1"], 5.0, 1.4), 0.7, width=1, send=0.6)
    for i, (tw, w) in enumerate(T.RBE):
        X(tw - 0.35, reverse_swell(0.35), 0.45, width=1)
        X(tw, card_slam(1.1 + 0.2 * i), 0.85 + 0.15 * i, width=1, send=0.6)
        X(tw, braam2(NOTE[["D1", "F1", "A1"][i]], 2.5, 1.5), 0.55, width=1, send=0.6)
    grid(a0 + 7.0, a0 + 17.0, ["D2", "D2", "A#1", "A1", "D2", "C2"], 1.05, fast=True, rolls=True)
    M(a0 + 7.0, choir(["D3", "F3", "A3", "D4"], 10.5, att=0.5, rel=1.5), 0.2, width=1, send=0.7)
    # voice 28 over the aurora: the floor drops out, strings + choir hold the tension
    M(a0 + 17.0, choir(["A#2", "D3", "F3", "A#3"], 10.5, att=0.8, rel=2.0), 0.3, width=1, send=0.8)
    M(a0 + 17.0, tremolo(["D4", "F4", "A4", "D5"], 10.5, rate=14, att=1.0, rel=1.0), 0.12, width=1, send=0.6)
    for tk in np.arange(a0 + 17.0, a0 + 27.2, BEAT * 2):
        X(tk, taiko(1.8, 85, 42), 0.42, send=0.6)
        X(tk, heartbeat(0.8), 0.3, send=0.2)
    # volcanic lightning
    HIT(a0 + 27.2, 0.9, pre=0.6)
    grid(a0 + 27.2, a0 + 34.2, ["D2", "A#1", "C2", "A1"], 1.1, fast=True, rolls=True)
    strikes(a0, a0 + 40)
    # accelerating roll into dead air, then the slam back into the formation
    X(a0 + 32.0, shepard(7.6, 40, 7, 0.2, 0.9), 0.32, width=1, send=0.3)
    for k, tk in enumerate(np.arange(a0 + 34.2, a0 + 39.6, BEAT / 8)):
        X(tk, taiko(0.35, 190, 110), 0.12 + 0.5 * ((tk - a0 - 34.2) / 5.4) ** 2, pan=0.4 if k % 2 else -0.4, send=0.3)
    X(a0 + 36.5, K.riser(3.1, 80, 5000), 0.3, width=1, send=0.3)
    HIT(a0 + 40.0, 1.3, pre=0.01)
    X(a0 + 40.0, braam2(NOTE["D1"], 7.0, 1.5), 0.8, width=1, send=0.6)
    X(a0 + 40.05, debris(3.0, 70), 0.3, width=1, send=0.5)

    # ---- B: monuments over ice and fire (324-364)
    b0 = T.B0
    HIT(b0, 0.8, pre=0.5)
    M(b0, choir(["D3", "F3", "A3", "D4"], 14.5, att=0.4, rel=2.5), 0.4, width=1, send=0.8)
    M(b0, pad(["D3", "A3", "D4", "F4", "A4"], 14.5, fc=3000, att=0.4, rel=2.5), 0.22, width=1, send=0.7)
    X(b0, braam2(NOTE["D1"], 7.0, 1.2), 0.55, width=1, send=0.6)
    for k, tk in enumerate(np.arange(b0 + 2.0, b0 + 14.0, BEAT * 2)):
        X(tk, taiko(1.8, 85, 42), 0.45, send=0.6)
        if k % 2:
            X(tk, braam2(NOTE["A#1"] if k % 4 == 1 else NOTE["C2"], 3.0, 0.9), 0.28, width=1, send=0.5)
    for s0, s1 in T.SWEEPS:
        if b0 <= s0 < b0 + 40:
            X(s0, whoosh(s1 - s0), 0.16, width=1, send=0.5)
    wb = wind_bed(14.0)
    X(b0, wb * env_adsr(len(wb), 0.5, 1, 1, 1.0), 0.12, width=1, send=0.1)
    v = b0 + 14.0
    HIT(v, 1.2, pre=0.01)
    X(v, braam2(NOTE["D1"], 9.0, 1.6, notes=[NOTE["D1"], NOTE["D2"], NOTE["A2"], NOTE["D3"], NOTE["F3"]]), 0.85,
      width=1, send=0.7)
    X(v, sub_hit(6.0, 70, 26), 0.5, send=0.3)
    X(v, crackle(12.0, 80), 0.14, width=1, send=0.2)
    M(v, choir(["A#2", "D3", "F3", "A#3"], 12.5, att=0.3, rel=2.0), 0.34, width=1, send=0.8)
    grid(v + 2.0, v + 12.0, ["D2", "A#1", "C2", "A1"], 1.0, fast=False, rolls=True)
    strikes(b0, b0 + 40)
    HIT(b0 + 26.0, 1.0, pre=0.8)
    grid(b0 + 26.0, b0 + 38.0, ["D2", "D2", "A#1", "A1", "D2", "C2"], 1.15, fast=True, rolls=True)
    X(b0 + 30.0, shepard(8.5, 40, 7, 0.1, 0.8), 0.32, width=1, send=0.3)
    M(b0 + 26.0, choir(["D3", "F3", "A3", "D4"], 12.5, att=1.0, rel=0.5), 0.3, width=1, send=0.7)
    for k, tk in enumerate(np.arange(b0 + 35.0, b0 + 38.5, BEAT / 8)):
        X(tk, taiko(0.35, 190, 110), 0.15 + 0.5 * ((tk - b0 - 35.0) / 3.5) ** 2, pan=0.4 if k % 2 else -0.4, send=0.3)
    X(b0 + 38.5, screech(1.5), 0.14, width=1, send=0.6)
    HIT(b0 + 40.0, 0.9, pre=0.01)

    # ---- D: hyper recap (438-458)
    d0 = T.D0
    HIT(d0, 1.0, pre=0.01)
    X(d0, shepard(12.8, 40, 7, 0.2, 1.1), 0.35, width=1, send=0.3)
    M(d0, tremolo(["D5", "D#5", "A4", "G#4"], 12.8, rate=18, att=1.0, rel=0.3), 0.12, width=1, send=0.5)
    ld = K.drone([NOTE["D1"], NOTE["G#1"]], 20.0, fc=300)
    M(d0, ld * env_adsr(len(ld), 1.0, 1.0, 1.0, 2.0), 0.22, width=1, send=0.3)
    for tk in np.arange(d0 + 12.8, d0 + 19.5, 1.4):
        X(tk, heartbeat(1.0), 0.55, send=0.3)
    X(d0 + 17.0, screech(2.5), 0.16, width=1, send=0.6)

    # ---- v5: lightning on the logo in every city / desert / canyon shot
    for ts, kind in getattr(T, "EXTRA_STRIKES", ()):
        X(ts, thunder(6.0, 0.25 if kind != "sky" else 0.6), 0.55, width=1, send=0.4)
        if kind == "emblem":
            X(ts, crackle(1.2, 160), 0.26, width=1, send=0.2)

    # ---- every new hard cut: whoosh + stab + glitch; every new impact gets a hit
    for tc in T.CUTS:
        if T.C0 < tc < T.C0 + 20:
            continue
        X(tc - 0.3, whoosh(0.35, rev=True), 0.22, width=1, send=0.3)
        X(tc, stab(NOTE["D3"] * 2 ** (rng.integers(0, 4) / 12), 0.35, 1.0), 0.36, width=1, send=0.4)
        if T.shot_at(tc + 0.01).stutter > 0 or tc > T.D0:
            X(tc, glitch(0.25), 0.28, pan=rng.uniform(-0.6, 0.6), send=0.2)
    old = {T.m(t) for t, s in V2.IMPACTS}
    explicit = {T.C0, T.C0 + 10.7, T.A0, T.A0 + 40.0, T.B0, T.B0 + 14.0, T.B0 + 26.0, T.B0 + 40.0, T.D0}
    explicit |= {t for t, w in T.RBE}
    for ti, sv in T.IMPACTS:
        if any(abs(ti - e) < 0.05 for e in old | explicit):
            continue
        X(ti - 0.25, reverse_swell(0.25), 0.22 * sv, width=1)
        X(ti, hit_stack(0.55 * sv + 0.2, 3.0), 0.5 * sv + 0.1, width=1, send=0.5)
    return mus, sfx, wet


def voice_track():
    vb, wet = A2.Bus32(), A2.Bus32()
    hp = sos_hp(70, 2)
    lens = {}
    for idx, t0 in T.VOICE:
        path = os.path.join(HERE, "assets", "voice", f"{idx}.wav")
        if not os.path.exists(path):
            print("missing voice line", idx)
            continue
        x, sr = sf.read(path, always_2d=True)
        x = x.mean(1)
        x = resample_poly(x, SR, sr) if sr != SR else x
        x = sosfilt(hp, x)
        low = sosfilt(sos_lp(160, 2), x)
        pres = sosfilt(sos_bp(2500, 5000, 2), x)
        x = x + low * 0.7 + pres * 0.35
        env = np.sqrt(sosfilt(sos_lp(12, 1), x * x) + 1e-9)
        x = x * np.minimum(1.0, (0.12 / np.maximum(env, 1e-4)) ** 0.55)
        x = np.tanh(x / (np.max(np.abs(x)) + 1e-9) * 1.4) / np.tanh(1.4)
        st = pan_st(x)
        if idx in (2, 7, 19, 8, 24, 27, 30, 32):
            st = echo(x, 0.38, 0.38, 4)
        vg = 1.25 if idx in (20, 27) else 0.62          # the word-card lines must punch through their slams
        vb.add(t0, st, vg)
        wet.add(t0, st, 0.14 * vg / 0.62)
        envx = np.convolve(np.abs(x), np.ones(960) / 960, "same")
        on = np.where(envx > 0.02 * np.abs(x).max())[0]
        lens[idx] = (on[-1] / SR + 0.15) if len(on) else len(x) / SR
    return vb, wet, lens


def main():
    mus, sfx, wet = build()
    vb, vwet, lens = voice_track()
    print("reverb...", flush=True)
    mus_wet = reverb(wet.x, make_ir(4.6, 1.4, 0.5, 0.03).astype(np.float32)).astype(np.float32)
    del wet
    v_wet = reverb(vwet.x, make_ir(2.2, 0.6, 0.25, 0.02, seed=4).astype(np.float32)).astype(np.float32)
    del vwet
    pre = mus.x
    pre += mus_wet * np.float32(0.55)
    pre += sfx.x
    del mus_wet, sfx
    duck = np.ones(N, np.float32)
    for idx, t0 in T.VOICE:
        if idx not in lens:
            continue
        i0, i1 = int((t0 + 0.3) * SR), int((t0 + lens[idx]) * SR)
        vr_line = np.sqrt(np.mean(vb.x[:, i0:i1] ** 2)) + 1e-9
        c = int(0.5 * SR)
        for j0 in range(int((t0 + 0.1) * SR), int((t0 + lens[idx] + 0.3) * SR), c):
            j1 = min(N, j0 + c)
            vr = max(np.sqrt(np.mean(vb.x[:, j0:j1] ** 2)), vr_line * 0.7) + 1e-9
            mr = np.sqrt(np.mean(pre[:, j0:j1] ** 2)) + 1e-9
            g = min(0.85, vr / (mr * 10 ** (7.0 / 20)))
            duck[j0:j1] = np.minimum(duck[j0:j1], g)
    lp = sos_lp(2.5, 1)
    duck = np.minimum(sosfilt(lp, sosfilt(lp, duck)[::-1])[::-1], 1.0).astype(np.float32)
    for ti, sv in T.IMPACTS:
        if sv >= 0.8:
            j0, j1 = int((ti - 0.03) * SR), int((ti + 0.6) * SR)
            ramp = np.clip((np.arange(j1 - j0) / SR - 0.4) / 0.2, 0, 1).astype(np.float32)
            duck[j0:j1] = np.maximum(duck[j0:j1], 1 - ramp * (1 - duck[j0:j1]))
    tg = np.arange(N, dtype=np.float32) / SR
    a, b = T.SILENCE
    gate = np.ones(N, np.float32)
    for g0, g1 in T.PRE_HIT_SILENCE:
        gate *= (1 - (1 - 0.004) * np.clip((tg - g0) / 0.03, 0, 1) * (tg < g1)).astype(np.float32)
    del tg
    music = pre
    music *= duck * gate
    breath = A2.Bus32()
    breath.add(a - 0.05, whoosh(b - a + 0.05, rev=True), 0.12, width=1)
    mix = music + breath.x + vb.x + v_wet * 0.8
    for idx, t0 in T.VOICE:
        if idx not in lens:
            continue
        i0, i1 = int((t0 + 0.4) * SR), int((t0 + min(lens[idx], 2.5)) * SR)
        vr = np.sqrt(np.mean(vb.x[:, i0:i1] ** 2)) + 1e-9
        mr = np.sqrt(np.mean(music[:, i0:i1] ** 2)) + 1e-9
        print(f"voice {idx:2d} @ {t0:6.1f}s  voice-to-score {20 * np.log10(vr / mr):5.1f} dB", flush=True)
    mix = sosfilt(sos_hp(24, 2), mix, axis=1).astype(np.float32)
    mix = np.tanh(mix * 1.15) / 1.15
    envl = np.max(np.abs(mix), 0)
    gain = np.minimum(1.0, 0.9 / np.maximum(sosfilt(sos_lp(8, 1), envl), 1e-6)).astype(np.float32)
    mix *= gain
    fade_out = np.clip((T.DURATION * SR - np.arange(N)) / (2.5 * SR), 0, 1).astype(np.float32)
    mix *= np.clip(np.arange(N) / (0.05 * SR), 0, 1).astype(np.float32) * fade_out
    mix = mix[:, :int(T.DURATION * SR)]
    mix /= np.max(np.abs(mix)) + 1e-9
    mix *= 10 ** (-1.0 / 20)
    os.makedirs(OUT, exist_ok=True)
    sf.write(os.path.join(OUT, "soundtrack_raw.wav"), mix.T.astype(np.float32), SR, subtype="FLOAT")
    print("wrote", os.path.join(OUT, "soundtrack_raw.wav"), flush=True)


if __name__ == "__main__":
    main()
