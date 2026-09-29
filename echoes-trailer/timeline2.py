"""v2 cut (6:00): faster pacing, more scenery, more narration, more effects.

The trailer is a list of shots. Each shot picks an environment (black, void, ocean,
mountain, storm, forest) and a camera move; the logo's growth runs on one continuous
story clock underneath, so every cut shows the formation a little further along.
"""
FPS = 24
DURATION = 360.0
W, H = 3840, 2160

# --- story clock --------------------------------------------------------------
SPARK = 14.0
BOOM = 75.0
GROW = (75.0, 223.5)
SILENCE = (224.3, 225.0)
COMPLETE = 225.0
MATERIALIZE = (225.4, 231.0)
LOCKUP = (270.0, 275.0)
LETTERS = (274.5, 281.5)
GLINT = 285.2
TAGLINE = (289.0, 299.0)
REVEAL = (307.0, 309.6)
COLLAPSE = (321.0, 323.5)
STAR_OUT = 333.5
SLAM = 340.0
FADE_END = (356.5, 360.0)
GATHER = (55.0, 70.8)

RINGS = [16.0 + 2.0 * i for i in range(26)] + [
    66.8, 67.5, 68.1, 68.6, 69.0, 69.4, 69.7, 70.0, 70.25, 70.5, 70.7, 70.9, 71.1]
GROW_RINGS = [84.0 + 8.0 * i for i in range(18)]
LATE_RINGS = [BOOM, COMPLETE, GLINT, REVEAL[0], STAR_OUT, SLAM]

# lightning: (time, kind) kind = emblem | ground | sky
STRIKES = [(63.6, "sky"), (64.6, "ground"),
           (85.2, "ground"), (86.8, "emblem"), (88.9, "sky"), (90.6, "emblem"), (92.4, "ground"),
           (94.1, "emblem"), (95.9, "sky"), (97.3, "emblem"), (99.0, "ground"),
           (158.25, "emblem"), (165.95, "ground"), (168.3, "emblem"), (169.8, "sky"), (170.6, "emblem"),
           (175.1, "emblem"), (242.0, "sky"), (247.5, "sky")]

# distortion shockwaves: (time, strength)
SHOCKWAVES = [(SPARK, 0.35), (BOOM, 1.0), (COMPLETE, 1.5), (GLINT, 0.3), (REVEAL[0], 0.5),
              (STAR_OUT, 0.3), (SLAM, 1.3)] + [(t, 0.25) for t, k in STRIKES if k == "emblem" and t > 60]

SWEEPS = [(228.0, 232.0), (236.0, 239.5), (266.0, 269.5), (292.0, 296.0), (346.0, 350.0)]

VOICE = [
    (15, 0.6),     # Every legend begins with a sound.
    (1, 8.0),      # Before the light... there was only the dark.
    (2, 20.0),     # And in the dark... every sound leaves an echo.
    (16, 32.8),    # Across the silent sea...
    (17, 44.0),    # Over mountains no one has ever climbed...
    (3, 55.5),     # A whisper. A heartbeat. A single spark.
    (9, 64.0),     # They said nothing could grow here.
    (10, 72.0),    # They were wrong.
    (4, 78.2),     # From that spark... something began to grow.
    (18, 88.0),    # It grew through the storm. It grew through the silence.
    (5, 101.0),    # Line by line. Story by story.
    (19, 114.0),   # Every root. Every branch. Every echo.
    (11, 130.0),   # Every story we tell... carves itself into the dark.
    (20, 157.78),  # Faster. Louder. Stronger. (word onsets 0.27 / 1.37 / 2.33 s)
    (12, 168.0),   # Bigger. Deeper. Darker than anything before.
    (21, 180.0),   # The dark is not empty. It is waiting... listening.
    (13, 213.0),   # And now... it is almost here.
    (6, 229.0),    # This is where legends are born.
    (22, 241.5),   # Forged in shadow. Carved in light.
    (23, 253.0),   # A studio for the stories that refuse to fade.
    (7, 283.0),    # Echoes... in the Dark.
    (24, 300.5),   # The stories you hear in the dark... will follow you into the light.
    (14, 311.0),   # Our story begins now.
    (8, 325.0),    # Listen closely. The dark is calling.
]


# --- shots ----------------------------------------------------------------------
AXIS = 1476.5          # the logo's vertical axis (mask px): every shot is centred on it
Y_TIPS, Y_STAR, Y_UPPER, Y_MID, Y_LOWER, Y_BOTTOM = 300.0, 556.0, 950.0, 1537.0, 2150.0, 2700.0

# kinetic title cards: (start, end, text)
CARDS = [(27.0, 29.1, "EVERY SOUND"), (29.1, 31.0, "HAS AN ECHO"), (72.6, 74.9, "THEY WERE WRONG")]
WORD_CARDS = [(158.05, "FASTER"), (159.15, "LOUDER"), (160.11, "STRONGER")]  # synced to line 20 words

# visual + audio impact events: (time, strength). >= 0.9 gets the full shock treatment
# (white-hot frame, negative frame, zoom-blur punch, streak burst, glitch).
IMPACTS = ([(7.0, 0.55), (SPARK, 0.6), (27.0, 0.8), (29.1, 0.8), (31.0, 0.4), (43.0, 0.4), (55.0, 0.35),
            (72.6, 0.8), (BOOM, 1.0), (84.0, 0.5), (100.0, 0.45), (112.0, 0.4), (128.0, 0.45), (142.0, 0.45),
            (178.0, 0.55), (196.0, 0.45), (212.0, 0.5), (COMPLETE, 1.5), (240.0, 0.6), (252.0, 0.55),
            (270.0, 0.5), (GLINT, 0.55), (REVEAL[0], 0.8), (SLAM, 1.4)]
           + [(t, 0.4) for t in (3.35, 4.25, 4.95, 5.45, 5.85, 6.15, 6.40, 6.60)]
           + [(t, 0.9) for t, w in WORD_CARDS]
           + [(t, 0.45) for t, k in STRIKES if k == "emblem" and t > 60])
# dead air right before the biggest hits (audio is gated here)
PRE_HIT_SILENCE = [(26.92, 27.0), (72.52, 72.6), (74.72, 75.0), (SILENCE[0], SILENCE[1]), (306.72, 307.0),
                   (339.55, 340.0)]


def cam(f="C", z=1.0, roll=0.0, yaw=0.0, ox=0.0, oy=0.0):
    """f: anchor ('C' logo centre, 'S' star, 'AXF' growth front on the centre line,
    'LOCK' logo lockup) or (x, y) in mask px. z: zoom relative to the hero framing
    (lockup framing for 'LOCK'). ox/oy: where the focus sits on screen (4K px from centre)."""
    return dict(f=f, z=z, roll=roll, yaw=yaw, ox=ox, oy=oy)


def ax(y, z, **k):
    return cam((AXIS, y), z, **k)


class Shot:
    def __init__(self, t0, t1, env, c0, c1=None, ease="io", pan=(0.0, 0.0), horizon=0.66,
                 flash=0.0, sub=False, seed=0, leak=False, punch=0.0, card=None, stutter=0.0):
        self.t0, self.t1, self.env = t0, t1, env
        self.c0, self.c1 = c0, (c1 or c0)
        self.ease, self.pan, self.horizon = ease, pan, horizon
        self.flash, self.sub, self.seed = flash, sub, seed
        self.leak, self.punch, self.card, self.stutter = leak, punch, card, stutter


def _build():
    S = []
    add = S.append
    sky = lambda z, y=-0.18, **k: cam("C", z, oy=y * H, **k)
    black = lambda t0, t1: add(Shot(t0, t1, "black", cam("S", 6.0), card=""))

    # ---- cold open: black + subliminal flashes of what is coming
    black(0.0, 3.35)
    flashes = [(3.35, "storm"), (4.25, "void"), (4.95, "ocean"), (5.45, "mountain"), (5.85, "forest"),
               (6.15, "storm"), (6.40, "void"), (6.60, "ocean")]
    for i, (t, env) in enumerate(flashes):
        add(Shot(t, t + 2.0 / FPS, env, sky(0.55 + 0.04 * i, -0.13), flash=0.08, sub=True, seed=i,
                 horizon=0.6 if env == "ocean" else 0.72))
        black(t + 2.0 / FPS, flashes[i + 1][0] if i + 1 < len(flashes) else 7.0)

    # ---- Act I: the void and the world (always centred)
    add(Shot(7.0, 19.0, "void", cam("S", 7.0), cam("S", 5.0), ease="lin", pan=(0, -60)))
    add(Shot(19.0, 27.0, "void", cam("S", 3.4), cam("S", 2.6), pan=(-40, 40)))
    for t0, t1, text in CARDS[:2]:
        add(Shot(t0, t1, "black", cam("S", 6.0), card=text, flash=0.55, punch=0.08))
    add(Shot(31.0, 43.0, "ocean", sky(0.42, -0.14), sky(0.47, -0.14), pan=(0, -140), horizon=0.6, flash=0.3))
    add(Shot(43.0, 55.0, "mountain", sky(0.5, -0.17), sky(0.56, -0.18), pan=(120, -120), horizon=0.62,
             flash=0.3))
    add(Shot(55.0, 63.0, "void", cam("S", 3.0), cam("S", 2.1), pan=(30, -30)))
    m = [(63.0, "storm"), (65.2, "ocean"), (67.0, "void"), (68.5, "mountain"), (69.6, "forest"),
         (70.5, "storm"), (71.3, None)]
    for i in range(len(m) - 1):
        t0, env = m[i]
        t1 = m[i + 1][0]
        if env == "void":
            add(Shot(t0, t1, env, cam("S", 2.0), cam("S", 2.6), flash=0.4, punch=0.1))
        else:
            add(Shot(t0, t1, env, sky(0.5 + 0.03 * i, -0.15), sky(0.56 + 0.03 * i, -0.15),
                     pan=(60 * (-1) ** i, -60 * (-1) ** i), horizon=0.68 if env != "ocean" else 0.6,
                     flash=0.4, punch=0.1))
    add(Shot(71.3, 72.6, "void", cam("S", 1.6), cam("S", 1.45), flash=0.3))
    add(Shot(72.6, 74.9, "black", cam("S", 6.0), card=CARDS[2][2], flash=0.7, punch=0.1))
    black(74.9, 75.0)

    # ---- Act II: the formation, pushing straight down the centre line
    add(Shot(75.0, 78.5, "black", cam("S", 1.3), cam("AXF", 3.4), ease="rush", flash=1.0))
    add(Shot(78.5, 84.0, "black", cam("AXF", 3.4), cam("AXF", 3.1)))
    add(Shot(84.0, 100.0, "storm", sky(0.62, -0.02), sky(0.72, -0.03), pan=(0, -220), horizon=0.72, flash=0.6))
    add(Shot(100.0, 112.0, "black", cam("AXF", 3.1), cam("AXF", 2.7), flash=0.45))
    add(Shot(112.0, 128.0, "forest", sky(0.55, -0.04), sky(0.62, -0.05), pan=(-180, 180), horizon=0.8,
             flash=0.35, leak=True))
    add(Shot(128.0, 142.0, "black", cam("AXF", 2.8), cam("AXF", 2.3), flash=0.45))
    add(Shot(142.0, 156.0, "ocean", sky(0.48, -0.15), sky(0.54, -0.15), pan=(120, -120), horizon=0.6,
             flash=0.4))
    # montage: centred punch-ins down the axis, worlds, and the FASTER / LOUDER / STRONGER cards
    ys = [Y_STAR, Y_UPPER, Y_MID, Y_TIPS, Y_LOWER, Y_UPPER, Y_MID, Y_STAR, Y_LOWER, Y_UPPER, Y_MID, Y_STAR]
    mont = [(156.0, "black"), (158.05, "card0"), (158.55, "storm"), (159.15, "card1"), (159.65, "ocean"),
            (160.11, "card2"), (160.75, "black"), (161.3, "mountain"), (162.2, "black"), (163.2, "forest"),
            (164.2, "black"), (165.0, "storm"), (165.8, "black"), (166.6, "ocean"), (167.4, "black"),
            (168.0, "storm"), (171.0, "black"), (172.0, "ocean"), (173.0, "black"), (173.7, "mountain"),
            (174.4, "black"), (175.0, "storm"), (175.5, "black"), (176.0, "forest"), (176.5, "black"),
            (177.0, "void"), (177.5, "black"), (178.0, None)]
    k = 0
    for i in range(len(mont) - 1):
        t0, env = mont[i]
        t1 = mont[i + 1][0]
        if env.startswith("card"):
            add(Shot(t0, t1, "black", cam("S", 6.0), card=WORD_CARDS[int(env[-1])][1], flash=0.8, punch=0.12))
        elif env == "black":
            y = ys[k % len(ys)]
            z0 = [3.4, 4.2, 2.9, 5.0, 3.1, 4.6, 2.7, 5.4, 3.3, 4.0, 3.0, 4.8][k % 12]
            k += 1
            add(Shot(t0, t1, env, ax(y, z0), ax(y, z0 * 1.22), flash=0.5, punch=0.14, stutter=0.25))
        elif env == "void":
            add(Shot(t0, t1, env, cam("C", 1.2), cam("C", 1.35), flash=0.55, punch=0.14, stutter=0.2))
        else:
            zo = 0.5 if env == "ocean" else 0.62 + 0.02 * (i % 4)
            add(Shot(t0, t1, env, sky(zo, -0.07 if env != "ocean" else -0.13), sky(zo * 1.12, -0.07 if env != "ocean" else -0.13),
                     pan=(80 * (-1) ** i, -80 * (-1) ** i), horizon={"ocean": 0.6, "forest": 0.8}.get(env, 0.7),
                     flash=0.5, punch=0.14, leak=(env == "forest"), stutter=0.2))
    add(Shot(178.0, 196.0, "mountain", sky(0.72, -0.06), sky(0.8, -0.05), pan=(-120, 140), horizon=0.72,
             flash=0.45))
    add(Shot(196.0, 212.0, "black", cam("AXF", 2.6), cam("AXF", 1.7), flash=0.4))
    add(Shot(212.0, 225.0, "void", cam("C", 1.35), cam("C", 1.0), flash=0.35))

    # ---- Act III: the hit, realistic detail, monuments
    add(Shot(225.0, 240.0, "void", cam("C", 1.0, yaw=-0.2), cam("C", 1.08, yaw=0.2), ease="lin"))
    add(Shot(240.0, 252.0, "mountain", sky(0.78, -0.05), sky(0.85, -0.05), pan=(140, -140), horizon=0.73,
             flash=0.45))
    add(Shot(252.0, 264.0, "ocean", sky(0.5, -0.15), sky(0.56, -0.15), pan=(-100, 100), horizon=0.6,
             flash=0.4))
    add(Shot(264.0, 270.0, "black", ax(Y_STAR + 120, 7.0), ax(Y_STAR + 120, 5.2), flash=0.4))

    # ---- Act IV: the name
    add(Shot(270.0, 300.0, "void", cam("C", 1.08), cam("LOCK", 1.04), ease="lock", flash=0.35))
    add(Shot(300.0, 306.8, "ocean", cam("LOCK", 0.6, oy=-0.2 * H), cam("LOCK", 0.64, oy=-0.2 * H),
             horizon=0.62, flash=0.4))
    add(Shot(306.8, 323.5, "void", cam("LOCK", 1.0), cam("LOCK", 1.05), flash=0.25))

    # ---- Act V: finale
    add(Shot(323.5, 338.0, "void", cam("S", 2.0), cam("S", 3.4)))
    add(Shot(338.0, 360.0, "void", cam("LOCK", 1.0), cam("LOCK", 1.06), ease="lin"))
    S.sort(key=lambda s: s.t0)
    return S


SHOTS = _build()


def shot_at(t):
    lo, hi = 0, len(SHOTS) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if SHOTS[mid].t0 <= t:
            lo = mid
        else:
            hi = mid - 1
    return SHOTS[lo]
