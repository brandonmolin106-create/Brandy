"""v3 cut (8:00): the v2 story stretched and cut harder.

The v2 timeline is re-timed onto 8 minutes by opening four gaps in it:
  C  55-75   before the BOOM: the star over the aurora, then over an erupting volcano
  A  198-238 mid-growth: a second hyper montage, RISE / BURN / ECHO
  B  324-364 after the completion: the finished emblem as a monument over ice and fire
  D  438-458 before the SLAM: a hyper-speed recap through every world, then dead black
Every long v2 shot is also chopped into 4-6 s pieces with hard framing jumps, so the
cut never sits still.
"""
import timeline2 as V2
from timeline2 import AXIS, FPS, H, W, Y_LOWER, Y_MID, Y_STAR, Y_TIPS, Y_UPPER, Shot, ax, cam  # noqa: F401

DURATION = 480.0
INSERTS = [(55.0, 20.0), (178.0, 40.0), (264.0, 40.0), (338.0, 20.0)]   # (v2 time, seconds added)


def m(t):
    """v2 time -> v3 time (events on an insert point move to after the insert)."""
    return t + sum(d for a, d in INSERTS if t >= a)


def m_end(t):
    """v2 time -> v3 time for the *end* of something (stays before the insert)."""
    return t + sum(d for a, d in INSERTS if t > a)


def mp(p):
    return (m(p[0]), m_end(p[1]) if p[1] != p[0] else m(p[1]))


# --- story clock (mapped) ---------------------------------------------------------
SPARK = m(V2.SPARK)
BOOM = m(V2.BOOM)
GROW = (m(V2.GROW[0]), m_end(V2.GROW[1]))
SILENCE = mp(V2.SILENCE)
COMPLETE = m(V2.COMPLETE)
MATERIALIZE = mp(V2.MATERIALIZE)
LOCKUP = mp(V2.LOCKUP)
LETTERS = mp(V2.LETTERS)
GLINT = m(V2.GLINT)
TAGLINE = mp(V2.TAGLINE)
REVEAL = mp(V2.REVEAL)
COLLAPSE = mp(V2.COLLAPSE)
STAR_OUT = m(V2.STAR_OUT)
SLAM = m(V2.SLAM)
FADE_END = mp(V2.FADE_END)
GATHER = (m(V2.GATHER[0]), m_end(V2.GATHER[1]))

# --- new beats -------------------------------------------------------------------
C0, A0, B0, D0 = 55.0, m_end(178.0), m_end(264.0), m_end(338.0)       # 55, 198, 324, 438
RBE = [(A0 + 1.38, "RISE"), (A0 + 3.14, "BURN"), (A0 + 4.94, "ECHO")]  # synced to line 27 words

RINGS = [m(r) for r in V2.RINGS] + [C0 + 1.0 + 2.0 * i for i in range(10)]
GROW_RINGS = [m(r) for r in V2.GROW_RINGS] + [A0 + 8.0 + 4.0 * i for i in range(8)]
LATE_RINGS = [BOOM, COMPLETE, GLINT, REVEAL[0], STAR_OUT, SLAM, B0 + 14.0, B0 + 26.0]

NEW_STRIKES = [(C0 + 11.5, "sky"), (C0 + 13.2, "ground"), (C0 + 15.8, "sky"), (C0 + 17.9, "ground"),
               (A0 + 28.5, "emblem"), (A0 + 30.0, "ground"), (A0 + 31.3, "emblem"), (A0 + 32.6, "sky"),
               (A0 + 33.7, "emblem"),
               (B0 + 15.5, "emblem"), (B0 + 18.0, "sky"), (B0 + 21.0, "ground"), (B0 + 23.5, "emblem"),
               (B0 + 25.0, "emblem")]
STRIKES = sorted([(m(t), k) for t, k in V2.STRIKES] + NEW_STRIKES)

SHOCKWAVES = [(SPARK, 0.35), (BOOM, 1.0), (COMPLETE, 1.5), (GLINT, 0.3), (REVEAL[0], 0.5),
              (STAR_OUT, 0.3), (SLAM, 1.3), (A0 + 40.0, 0.9), (B0 + 26.0, 0.9)] + [
    (t, 0.25) for t, k in STRIKES if k == "emblem" and t > 60]

SWEEPS = [mp(s) for s in V2.SWEEPS] + [(B0 + 4.0, B0 + 8.0)]

VOICE = sorted([(n, m(t)) for n, t in V2.VOICE] + [
    (25, C0 + 0.0),     # Beneath the frozen lights...      (speech starts 2.0 s into the file)
    (26, C0 + 12.2),    # Through rivers of fire...
    (27, A0 + 1.0),     # Rise. Burn. Echo.                 (word onsets 0.38 / 2.14 / 3.94 s)
    (28, A0 + 17.5),    # No light can hide it. No silence can stop it.
    (29, B0 + 9.0),     # Born in fire. Crowned in ice.
    (30, D0 + 15.0),    # Can you hear it now?
], key=lambda v: v[1])

CARDS = [(m(a), m_end(b) if b not in (55.0, 178.0, 264.0, 338.0) else m_end(b), s) for a, b, s in V2.CARDS]
WORD_CARDS = [(m(t), w) for t, w in V2.WORD_CARDS] + RBE

# fast cut list for the new montages: filled in by _build(), exported for the audio
CUTS = []


def _base_shots():
    out = []
    for s in V2.SHOTS:
        t0, t1 = m(s.t0), m_end(s.t1)
        if s.t1 in (55.0, 178.0, 264.0, 338.0):
            t1 = m_end(s.t1)
        n = Shot(t0, t1, s.env, s.c0, s.c1, s.ease, s.pan, s.horizon, s.flash, s.sub, s.seed, s.leak, s.punch,
                 s.card, s.stutter)
        out.append(n)
    return out


ZJUMP = [1.0, 1.22, 0.9, 1.12, 0.95, 1.3]


def _split(S):
    """Chop long shots into 4-6 s pieces with hard framing jumps."""
    out = []
    for s in S:
        d = s.t1 - s.t0
        f0, f1 = s.c0["f"], s.c1["f"]
        keep = (d < 9.0 or s.sub or s.card is not None or s.ease in ("rush", "lock") or f0 != f1
                or f0 == "LOCK" or s.c0["yaw"] != 0 or s.c1["yaw"] != 0 or s.t0 < 7.5)
        if keep:
            out.append(s)
            continue
        n = max(2, int(round(d / 4.8)))
        for i in range(n):
            a, b = i / n, (i + 1) / n
            lz = lambda u: s.c0["z"] * (s.c1["z"] / s.c0["z"]) ** u
            lo = lambda k, u: s.c0[k] + (s.c1[k] - s.c0[k]) * u
            zj = ZJUMP[(i + int(s.t0)) % len(ZJUMP)]
            ca = dict(s.c0, z=lz(a) * zj, ox=lo("ox", a), oy=lo("oy", a), roll=lo("roll", a))
            cb = dict(s.c0, z=lz(b) * zj * 1.06, ox=lo("ox", b), oy=lo("oy", b), roll=lo("roll", b))
            pa = s.pan[0] + (s.pan[1] - s.pan[0]) * a
            pb = s.pan[0] + (s.pan[1] - s.pan[0]) * b
            t0 = s.t0 + d * a
            out.append(Shot(t0, s.t0 + d * b, s.env, ca, cb, "lin", (pa, pb), s.horizon,
                            s.flash if i == 0 else 0.35, s.sub, s.seed + i, s.leak, 0.0 if i == 0 else 0.07,
                            None, 0.0))
            if i > 0:
                CUTS.append(t0)
    return out


def _build():
    S = _split(_base_shots())
    add = S.append
    sky = lambda z, y=-0.18, **k: cam("C", z, oy=y * H, **k)
    hz = {"ocean": 0.6, "forest": 0.8, "aurora": 0.5, "volcano": 0.7}
    ENVS = ["storm", "aurora", "ocean", "volcano", "mountain", "forest", "void"]

    def world(t0, t1, env, z, i, flash=0.5, punch=0.12, stutter=0.0, sub=False):
        if env == "void":
            add(Shot(t0, t1, env, cam("C", 1.2 * z / 0.6), cam("C", 1.35 * z / 0.6), flash=flash, punch=punch,
                     stutter=stutter, sub=sub, seed=i))
            return
        y = -0.13 if env == "ocean" else (-0.1 if env == "aurora" else -0.07)
        add(Shot(t0, t1, env, sky(z, y), sky(z * 1.12, y), pan=(80 * (-1) ** i, -80 * (-1) ** i),
                 horizon=hz.get(env, 0.7), flash=flash, punch=punch, leak=(env == "forest"), stutter=stutter,
                 sub=sub, seed=i))

    def card(t0, t1, text):
        add(Shot(t0, t1, "black", cam("S", 6.0), card=text, flash=0.8, punch=0.12))

    # ---- C: the star over ice, then fire (55-75)
    for i, (a, b) in enumerate([(0.0, 4.6), (4.6, 7.8), (7.8, 10.7)]):
        add(Shot(C0 + a, C0 + b, "aurora", sky(0.5 + 0.08 * i, -0.1), sky(0.56 + 0.08 * i, -0.1),
                 pan=(100 * (-1) ** i, -100 * (-1) ** i), horizon=0.5, flash=0.45 if i == 0 else 0.3,
                 punch=0.0 if i == 0 else 0.07))
        if i:
            CUTS.append(C0 + a)
    for i, (a, b) in enumerate([(10.7, 14.4), (14.4, 17.1), (17.1, 19.0)]):
        add(Shot(C0 + a, C0 + b, "volcano", sky(0.52 + 0.1 * i, -0.08), sky(0.6 + 0.1 * i, -0.08),
                 pan=(-120 * (-1) ** i, 120 * (-1) ** i), horizon=0.7, flash=0.6 if i == 0 else 0.35, punch=0.1))
        CUTS.append(C0 + a)
    add(Shot(C0 + 19.0, C0 + 20.0, "black", cam("S", 2.2), cam("S", 1.8), flash=0.3))

    # ---- A: second hyper montage (198-238) while the emblem keeps growing
    world(A0, A0 + 1.38, "volcano", 0.62, 0, flash=0.7)
    ts = [A0 + 1.38, A0 + 2.2, A0 + 3.14, A0 + 3.95, A0 + 4.94, A0 + 5.9]
    for j in range(3):
        card(ts[2 * j], ts[2 * j + 1], RBE[j][1])
        world(ts[2 * j + 1], ts[2 * j + 2] if j < 2 else A0 + 7.0, ["aurora", "volcano", "storm"][j], 0.66, j,
              flash=0.6, punch=0.15, stutter=0.2)
    t = A0 + 7.0
    k = 0
    durs = [1.1, 0.9, 1.0, 0.8, 0.9, 0.7, 0.8, 0.6, 0.7, 0.55, 0.6, 0.5, 0.55, 0.5, 0.45, 0.5, 0.45, 0.4]
    ys = [Y_STAR, Y_UPPER, Y_MID, Y_TIPS, Y_LOWER, Y_UPPER, Y_MID, Y_STAR, Y_LOWER]
    for i, dd in enumerate(durs):
        if i % 2 == 0:
            y = ys[k % len(ys)]
            z0 = [3.6, 4.4, 3.0, 5.2, 3.2, 4.8, 2.8, 5.6, 3.4][k % 9]
            k += 1
            add(Shot(t, t + dd, "black", ax(y, z0), ax(y, z0 * 1.25), flash=0.55, punch=0.15, stutter=0.2))
        else:
            world(t, t + dd, ENVS[(i // 2) % len(ENVS)], 0.6 + 0.03 * (i % 4), i, stutter=0.2)
        CUTS.append(t)
        t += dd
    # the voice line 28 over the aurora, then volcanic lightning
    for i, (a, b) in enumerate([(t - A0, 20.5), (20.5, 24.0), (24.0, 27.2)]):
        add(Shot(A0 + a, A0 + b, "aurora", sky(0.7 + 0.07 * i, -0.08), sky(0.78 + 0.07 * i, -0.08),
                 pan=(120 * (-1) ** i, -120 * (-1) ** i), horizon=0.5, flash=0.4, punch=0.08))
        CUTS.append(A0 + a)
    for i, (a, b) in enumerate([(27.2, 30.8), (30.8, 34.2)]):
        add(Shot(A0 + a, A0 + b, "volcano", sky(0.72 + 0.1 * i, -0.06), sky(0.82 + 0.1 * i, -0.06),
                 pan=(-140 * (-1) ** i, 140 * (-1) ** i), horizon=0.7, flash=0.5, punch=0.1))
        CUTS.append(A0 + a)
    t = A0 + 34.2
    for i, dd in enumerate([0.8, 0.7, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3, 0.3, 0.25, 0.25, 0.25]):
        if t + dd > A0 + 39.6:
            break
        if i % 2:
            y = ys[i % len(ys)]
            add(Shot(t, t + dd, "black", ax(y, 4.0 + 0.3 * i), ax(y, 5.0 + 0.3 * i), flash=0.6, punch=0.16))
        else:
            world(t, t + dd, ENVS[i % len(ENVS)], 0.66, i)
        CUTS.append(t)
        t += dd
    add(Shot(t, A0 + 40.0, "black", cam("S", 6.0), card=""))

    # ---- B: monuments over ice and fire (324-364), the emblem complete
    for i, (a, b) in enumerate([(0.0, 4.5), (4.5, 9.0), (9.0, 14.0)]):
        add(Shot(B0 + a, B0 + b, "aurora", sky(0.76 + 0.06 * i, -0.08), sky(0.82 + 0.06 * i, -0.08),
                 pan=(140 * (-1) ** i, -140 * (-1) ** i), horizon=0.5, flash=0.45, punch=0.0 if i == 0 else 0.08))
        if i:
            CUTS.append(B0 + a)
    for i, (a, b) in enumerate([(14.0, 18.5), (18.5, 22.5), (22.5, 26.0)]):
        add(Shot(B0 + a, B0 + b, "volcano", sky(0.74 + 0.08 * i, -0.06), sky(0.8 + 0.08 * i, -0.06),
                 pan=(-140 * (-1) ** i, 140 * (-1) ** i), horizon=0.7, flash=0.6 if i == 0 else 0.4, punch=0.1))
        CUTS.append(B0 + a)
    t = B0 + 26.0
    order = ["aurora", "volcano", "storm", "ocean", "mountain", "forest", "aurora", "volcano", "void"]
    i = 0
    while t < B0 + 38.5:
        dd = max(0.45, 1.8 - 0.14 * i)
        world(t, min(t + dd, B0 + 38.5), order[i % len(order)], 0.7 + 0.04 * (i % 3), i, flash=0.55, punch=0.12,
              stutter=0.15)
        CUTS.append(t)
        t += dd
        i += 1
    add(Shot(B0 + 38.5, B0 + 40.0, "black", cam("S", 6.0), card=""))

    # ---- D: hyper recap, every world, the full emblem burned in (438-458)
    t = D0
    i = 0
    while t < D0 + 12.5:
        dd = max(0.25, 1.2 * 0.87 ** i)
        world(t, t + dd, order[i % len(order)], 0.62 + 0.05 * (i % 3), i, flash=0.7, punch=0.16, sub=True)
        CUTS.append(t)
        t += dd
        gap = 2.0 / FPS
        add(Shot(t, t + gap, "black", cam("S", 6.0), card=""))
        t += gap
        i += 1
    add(Shot(t, D0 + 20.0, "black", cam("S", 6.0), card=""))
    S.sort(key=lambda s: s.t0)
    return S


SHOTS = _build()
CUTS.sort()

# visual + audio impacts
IMPACTS = ([(m(t), s) for t, s in V2.IMPACTS]
           + [(C0, 0.6), (C0 + 10.7, 0.8), (A0, 0.8), (A0 + 34.2, 0.6), (A0 + 40.0, 1.1), (B0, 0.8),
              (B0 + 14.0, 0.95), (B0 + 26.0, 0.9), (B0 + 40.0, 0.8), (D0, 0.9)]
           + [(t, 0.9) for t, w in RBE]
           + [(t, 0.35) for t in CUTS if not any(abs(t - c) < 0.05 for c in (C0, A0, B0, D0))]
           + [(t, 0.45) for t, k in NEW_STRIKES if k == "emblem"])
IMPACTS.sort()
PRE_HIT_SILENCE = [mp(p) if p[0] not in (55.0,) else p for p in V2.PRE_HIT_SILENCE] + [
    (A0 + 39.6, A0 + 40.0), (B0 + 38.5, B0 + 40.0), (D0 + 19.5, D0 + 20.0)]


def shot_at(t):
    lo, hi = 0, len(SHOTS) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if SHOTS[mid].t0 <= t:
            lo = mid
        else:
            hi = mid - 1
    return SHOTS[lo]
