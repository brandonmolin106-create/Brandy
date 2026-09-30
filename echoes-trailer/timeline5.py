"""v5 cut (8:00): v4's 20 places + heaps more effects and narration.

Adds on top of timeline4 (same shots and timing):
  * energy surges racing through the emblem on every cut and hit once it has started to grow
  * lightning on the logo in every city / desert / canyon / badlands shot
  * light sweeps across the finished emblem on every monument shot
  * anamorphic lens streaks and drifting horizon mist (renderer, gated on V5)
  * more narration filling the quiet stretches
"""
import os

from timeline4 import *  # noqa: F401,F403
import timeline3 as T3
import timeline4 as T4

V5 = True
SHOTS = T4.SHOTS
shot_at = T4.shot_at
_STORMY = ("city", "skyline", "badlands", "desert", "canyon")

EXTRA_STRIKES = []
_k = 0
for s in SHOTS:
    if s.env in _STORMY and not s.sub and s.t1 - s.t0 > 0.8 and s.t0 > T3.BOOM:
        ts = round(s.t0 + 0.6, 2)
        if all(abs(ts - e) > 1.5 for e, _ in T3.STRIKES + EXTRA_STRIKES):
            EXTRA_STRIKES.append((ts, "emblem" if _k % 2 == 0 else "sky"))
            _k += 1
STRIKES = sorted(T3.STRIKES + EXTRA_STRIKES)
SHOCKWAVES = T3.SHOCKWAVES + [(t, 0.25) for t, k in EXTRA_STRIKES if k == "emblem"]
IMPACTS = sorted(T3.IMPACTS + [(t, 0.45) for t, k in EXTRA_STRIKES if k == "emblem"])

_surge = sorted([t for t in T3.CUTS if t > T3.BOOM + 5] + [t for t, s in IMPACTS if s >= 0.6 and t > T3.BOOM + 5])
SURGES = []
for t in _surge:
    if not SURGES or t - SURGES[-1][0] > 0.6:
        SURGES.append((t, 1.0))

SWEEPS = T3.SWEEPS + [(s.t0 + 0.4, s.t0 + 3.4) for s in SHOTS
                      if T3.COMPLETE < s.t0 < T3.COLLAPSE[0] and s.env not in ("black", "void")
                      and s.t1 - s.t0 >= 3.5]

_sky = [s.t0 for s in SHOTS if s.env in ("skyline", "city") and 159.0 < s.t0 < 172.0]
_have = {int(f[:-4]) for f in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "voice"))
         if f.endswith(".wav")}
_NEW = [(33, 138.0),                          # In the deepest woods... the trees remember every whisper.
        (34, 157.4),                          # Oceans could not drown it.
        (35, (_sky[0] + 0.2) if _sky else 164.0),   # Cities could not silence it.
        (36, T3.A0 + 6.4),                    # Every world. Every shadow. Every sound.
        (39, 266.0),                          # Hold your breath.
        (42, 352.0),                          # Nothing escapes the echo.
        (43, 364.6),                          # Remember this moment.
        (44, 388.0)]                          # A new name... carved in light.
VOICE = sorted(T4.VOICE + [(n, t) for n, t in _NEW if n in _have], key=lambda v: v[1])
