"""v9 cut (10:00): v8 + a new chapter, "THE WORLDS ANSWER".

Two minutes open up right after the monuments (v8 364 s): the finished emblem stands in every world in
turn, cut to a fixed rhythm, while a second voice - the Echo - answers the narrator world by world. Then
a hyper recap and dead air before the name. Everything after the insert moves 120 s later.
"""
import timeline8 as T8
from timeline2 import Shot, cam
from timeline8 import FPS, H, W, V5, V6, V7, V8  # noqa: F401

P, ADD = 364.0, 120.0
DURATION = T8.DURATION + ADD


def sh(t):
    return t + ADD if t >= P else t


def sh_end(t):
    return t + ADD if t > P else t


def m(t):
    return sh(T8.m(t))


def _pair(p):
    return (sh(p[0]), sh_end(p[1]))


for _n in ("SPARK", "BOOM", "COMPLETE", "GLINT", "STAR_OUT", "SLAM", "C0", "A0", "B0", "D0"):
    globals()[_n] = sh(getattr(T8, _n))
for _n in ("GROW", "SILENCE", "MATERIALIZE", "LOCKUP", "LETTERS", "TAGLINE", "REVEAL", "COLLAPSE", "FADE_END",
           "GATHER", "DROSTE"):
    globals()[_n] = _pair(getattr(T8, _n))
RINGS = [sh(t) for t in T8.RINGS]
GROW_RINGS = [sh(t) for t in T8.GROW_RINGS]
LATE_RINGS = [sh(t) for t in T8.LATE_RINGS]
NEW_STRIKES = [(sh(t), k) for t, k in T8.NEW_STRIKES]
RBE = [(sh(t), w) for t, w in T8.RBE]
DESTINY_CARDS = [(sh(t), w) for t, w in T8.DESTINY_CARDS]
CARDS = [(sh(a), sh_end(b), s) for a, b, s in T8.CARDS]
SWEEPS = [_pair(p) for p in T8.SWEEPS]
PRE_HIT_SILENCE = [_pair(p) for p in T8.PRE_HIT_SILENCE]
VOICE = [(n, sh(t)) for n, t in T8.VOICE]
CUTS = [sh(t) for t in T8.CUTS]
EXTRA_STRIKES = [(sh(t), k) for t, k in T8.EXTRA_STRIKES]
STRIKES = [(sh(t), k) for t, k in T8.STRIKES]
SHOCKWAVES = [(sh(t), s) for t, s in T8.SHOCKWAVES]
IMPACTS = [(sh(t), s) for t, s in T8.IMPACTS]
SURGES = [(sh(t), s) for t, s in T8.SURGES]
WORD_CARDS = [(sh(t), w) for t, w in T8.WORD_CARDS]

# ---- the new chapter ------------------------------------------------------------------
E0 = P                                   # 364
GROUPS = [  # (Echo line, places)
    (102, ["aurora", "snowfield", "dolomites"]),
    (103, ["desert", "badlands", "canyon"]),
    (104, ["city", "skyline"]),
    (105, ["icecave", "falls"]),
    (106, ["ruins", "deadwood", "forest"]),
    (107, ["ocean", "starsea"]),
    (108, ["mountain", "storm", "pillars", "void"]),
]
HZ = {"desert": 0.72, "badlands": 0.72, "canyon": 0.85, "city": 0.62, "ruins": 0.72, "falls": 0.8, "icecave": 0.7,
      "dolomites": 0.7, "snowfield": 0.8, "deadwood": 0.85, "pillars": 0.7, "ocean": 0.6, "starsea": 0.6,
      "aurora": 0.5, "mountain": 0.72, "storm": 0.72, "forest": 0.8}
STORMY = ("city", "skyline", "badlands", "desert", "canyon", "storm")
CHAPTER_CARDS = [(E0, "THE WORLDS"), (E0 + 1.3, "ANSWER")]
CHAPTER = (E0, E0 + ADD)
CH_CUTS, CH_GROUPS, CH_STRIKES = [], [], []


def _chapter():
    S = []
    sky = lambda z, y=-0.08: cam("C", z, oy=y * H)
    S.append(Shot(E0, E0 + 1.3, "black", cam("S", 6.0), card="THE WORLDS", flash=0.8, punch=0.12))
    S.append(Shot(E0 + 1.3, E0 + 2.8, "black", cam("S", 6.0), card="ANSWER", flash=0.9, punch=0.14))
    t, i = E0 + 2.8, 0
    for line, places in GROUPS:
        CH_GROUPS.append((t, line))
        for p in places:
            d = 5.4
            z = [0.72, 0.8, 0.9, 0.76][i % 4]
            y = -0.13 if p in ("ocean", "starsea") else (-0.1 if p == "aurora" else -0.07)
            if p == "void":
                c0, c1 = cam("C", 1.05), cam("C", 1.18)
            else:
                c0, c1 = sky(z, y), sky(z * 1.1, y)
            S.append(Shot(t, t + d, p, c0, c1, ease="lin", pan=(90 * (-1) ** i, -90 * (-1) ** i),
                          horizon=HZ.get(p, 0.7), flash=0.5, seed=40 + i, punch=0.1, leak=(p == "deadwood")))
            CH_CUTS.append(t)
            if p in STORMY:
                CH_STRIKES.append((round(t + 1.6, 2), "emblem"))
                CH_STRIKES.append((round(t + 3.6, 2), "sky"))
            t += d
            i += 1
    # hyper recap through every world, the emblem burned in, then dead air before the name
    order = [p for _, ps in GROUPS for p in ps]
    k = 0
    while t < E0 + ADD - 4.0:
        dd = max(0.22, 0.9 * 0.9 ** k)
        S.append(Shot(t, t + dd, order[k % len(order)], sky(0.72 + 0.05 * (k % 3)), sky(0.8), flash=0.7, punch=0.16,
                      sub=True, seed=90 + k, horizon=HZ.get(order[k % len(order)], 0.7)))
        CH_CUTS.append(t)
        t += dd
        k += 1
    S.append(Shot(t, E0 + ADD, "black", cam("S", 6.0), card=""))
    return S


_CH = _chapter()
SHOTS = sorted([Shot(sh(s.t0), sh_end(s.t1), s.env, s.c0, s.c1, s.ease, s.pan, s.horizon, s.flash, s.sub, s.seed,
                     s.leak, s.punch, s.card, s.stutter) for s in T8.SHOTS] + _CH, key=lambda s: s.t0)

WORD_CARDS += CHAPTER_CARDS
CUTS = sorted(CUTS + CH_CUTS)
STRIKES = sorted(STRIKES + CH_STRIKES)
EXTRA_STRIKES = sorted(EXTRA_STRIKES + CH_STRIKES)
SHOCKWAVES += [(t, 0.25) for t, k in CH_STRIKES if k == "emblem"]
IMPACTS = sorted(IMPACTS + [(t, 0.9) for t, w in CHAPTER_CARDS] + [(t, 0.8) for t, _ in CH_GROUPS]
                 + [(t, 0.35) for t in CH_CUTS] + [(t, 0.45) for t, k in CH_STRIKES if k == "emblem"])
SURGES = sorted(SURGES + [(t, 1.0) for t in CH_CUTS])
SWEEPS = sorted(SWEEPS + [(t + 0.5, t + 3.5) for t in CH_CUTS if t < E0 + ADD - 15])
PRE_HIT_SILENCE = sorted(PRE_HIT_SILENCE + [(E0 + ADD - 0.6, E0 + ADD)])
VOICE = sorted(VOICE + [(101, E0 + 0.9)] + [(n, t + 0.8) for t, n in CH_GROUPS]
               + [(109, E0 + ADD - 11.5), (110, E0 + ADD - 3.4)], key=lambda v: v[1])


def shot_at(t):
    lo, hi = 0, len(SHOTS) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if SHOTS[mid].t0 <= t:
            lo = mid
        else:
            hi = mid - 1
    return SHOTS[lo]
