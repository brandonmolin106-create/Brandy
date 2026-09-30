"""v8 cut (8:00): "Endless Destiny". v7 + golden threads of fate running from the edge of every world into
the emblem, ENDLESS / DESTINY slammed in the dark before the final SLAM, and an infinite zoom finale:
the camera dives into the star and finds the whole scene inside it, forever."""
from timeline7 import *  # noqa: F401,F403
import timeline3 as T3
import timeline7 as T7
from timeline2 import Shot

V8 = True
DESTINY_CARDS = [(T3.D0 + 17.4, "ENDLESS"), (T3.D0 + 18.5, "DESTINY")]
WORD_CARDS = T7.WORD_CARDS + DESTINY_CARDS
IMPACTS = sorted(T7.IMPACTS + [(t, 0.9) for t, w in DESTINY_CARDS])
DROSTE = (T3.SLAM + 8.0, T3.FADE_END[1])


def _cards(shots):
    out = []
    (c0, w0), (c1, w1) = DESTINY_CARDS
    for s in shots:
        if s.t0 <= c0 < s.t1:
            out.append(Shot(s.t0, c0, s.env, s.c0, s.c1, card=s.card))
            out.append(Shot(c0, c1, "black", s.c0, card=w0, flash=0.8, punch=0.12))
            out.append(Shot(c1, c1 + 1.1, "black", s.c0, card=w1, flash=0.9, punch=0.14))
            out.append(Shot(c1 + 1.1, s.t1, s.env, s.c0, s.c1, card=s.card))
        else:
            out.append(s)
    return out


SHOTS = _cards(T7.SHOTS)
VOICE = T7.VOICE


def shot_at(t):
    lo, hi = 0, len(SHOTS) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if SHOTS[mid].t0 <= t:
            lo = mid
        else:
            hi = mid - 1
    return SHOTS[lo]
