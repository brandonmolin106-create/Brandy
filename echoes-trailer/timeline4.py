"""v4 cut (8:00): no volcano, heaps more places.

Same beats and timing as v3, but every world rotates through a family of real places, so a
repeat visit to "the ocean" lands somewhere new (the NYC skyline, a starry sea...). The
volcano is gone: its slots become the desert, the canyon, the badlands and the city.
"""
from timeline3 import *  # noqa: F401,F403
import timeline3 as T3
from timeline2 import Shot

FAMILY = {
    "mountain": ["mountain", "dolomites", "desert", "canyon"],
    "ocean": ["ocean", "skyline", "starsea"],
    "forest": ["forest", "deadwood", "ruins"],
    "storm": ["storm", "city", "badlands"],
    "aurora": ["aurora", "snowfield", "icecave", "falls"],
    "volcano": ["city", "ruins", "falls", "icecave", "canyon", "skyline", "dolomites", "pillars", "starsea",
                "deadwood", "desert", "badlands"],
}
VOID_FAMILY = ["void", "pillars"]          # only in fast cuts; the long void shots carry the story
HORIZON = {"desert": 0.72, "badlands": 0.72, "canyon": 0.85, "city": 0.62, "ruins": 0.72, "falls": 0.8,
           "icecave": 0.7, "dolomites": 0.7, "snowfield": 0.8, "deadwood": 0.85, "pillars": 0.7}
# fixed picks where the story needs a particular place (start time window -> places in order)
OVERRIDE = [((T3.C0 + 10.0, T3.C0 + 19.0), ["desert", "canyon", "badlands"]),       # "across the endless sands"
            ((T3.A0 + 27.0, T3.A0 + 34.3), ["badlands", "desert"]),                  # desert lightning
            ((T3.B0 + 13.9, T3.B0 + 26.1), ["city", "skyline", "city"])]             # "the cities that never sleep"


def _rebuild():
    count = {}
    ov_i = [0] * len(OVERRIDE)
    out = []
    for s in T3.SHOTS:
        env = s.env
        new = env
        hit = [k for k, ((a, b), _) in enumerate(OVERRIDE) if a <= s.t0 < b and env == "volcano"]
        if hit:
            k = hit[0]
            new = OVERRIDE[k][1][ov_i[k] % len(OVERRIDE[k][1])]
            ov_i[k] += 1
        elif env in FAMILY:
            fam = FAMILY[env]
            new = fam[count.get(env, 0) % len(fam)]
            count[env] = count.get(env, 0) + 1
        elif env == "void" and (s.t1 - s.t0) < 1.5 and s.t0 > 7.5:
            new = VOID_FAMILY[count.get("void", 0) % 2]
            count["void"] = count.get("void", 0) + 1
        hz = HORIZON.get(new, s.horizon) if new != env else s.horizon
        out.append(Shot(s.t0, s.t1, new, s.c0, s.c1, s.ease, s.pan, hz, s.flash, s.sub, s.seed, s.leak or
                        new == "deadwood", s.punch, s.card, s.stutter))
    return out


SHOTS = _rebuild()

# narration: the fire lines are rewritten for the new places
VOICE = sorted([(31 if n == 26 else n, t) for n, t in T3.VOICE if n != 29] + [(32, T3.B0 + 6.0)],
               key=lambda v: v[1])
# 31: "Across the endless sands..."   32: "From the frozen north... to the cities that never sleep."


def shot_at(t):
    lo, hi = 0, len(SHOTS) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if SHOTS[mid].t0 <= t:
            lo = mid
        else:
            hi = mid - 1
    return SHOTS[lo]
