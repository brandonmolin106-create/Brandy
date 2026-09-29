"""The cut: every shot and hit of 'The Fish in the Cup' thriller version, timed to Brandon's words (seconds)."""
import json
import os
import sys

import typo
from typo import Counter, Slam, TypeLine

HERE = os.path.dirname(os.path.abspath(__file__))
PROD = os.path.join(HERE, '..', '..', 'echoes-particle-studio', 'productions', 'fish-in-the-cup')
sys.path.insert(0, os.path.join(HERE, '..', '..', 'echoes-particle-studio'))

END = 365.0
FACE = 'face'
BLACK = 'black'


def build():
    E = []

    def S(t0, t1, src, **kw):
        d = dict(t0=t0, t1=t1, src=src)
        d.update(kw)
        E.append(d)

    # ---------------------------------------------------------------- cold open
    S(0.00, 2.00, 'reveal_wide', ct0=0.0)
    S(2.00, 5.72, FACE)
    S(5.72, 7.10, 'reveal_wide', ct0=2.0, push=(1.0, 1.06))
    S(7.10, 7.46, BLACK)
    S(7.46, 8.70, FACE)
    S(8.70, 8.82, BLACK)
    # ---------------------------------------------------------------- the fish, the cup
    S(8.82, 11.78, 'fish_macro_turn', ct0=0.3)
    S(11.78, 15.10, 'cup_high_loop', loop=True, push=(1.0, 1.1))
    S(15.10, 18.20, 'cup_top_loop', loop=True, push=(1.05, 1.18))
    S(18.20, 19.50, FACE)
    S(19.50, 23.10, 'ocean_vast', grade='ocean', rays=0.9)
    S(23.10, 26.10, 'fish_free', ct0=2.0, grade='ocean', rays=0.6)
    S(26.10, 27.88, 'sunrise_wide', ct0=1.0, grade='sun')
    S(27.88, 29.86, 'cup_side_loop', ct0=1.0, loop=True, push=(1.08, 1.12))
    S(29.86, 33.42, 'cup_top_loop', ct0=1.5, loop=True, push=(1.1, 1.2))
    S(33.42, 36.04, FACE)
    S(36.04, 39.90, 'cup_high_loop', ct0=2.0, loop=True, push=(1.0, 1.12))
    # ---------------------------------------------------------------- it hits glass
    S(39.90, 41.22, 'cup_side_loop', ct0=0.0, loop=True, push=(1.1, 1.14))
    S(41.22, 43.82, 'hit_glass', ct0=0.0)
    S(43.82, 46.18, 'hit_glass', ct0=1.6, speed=0.8)
    S(46.18, 48.20, 'hit_glass', ct0=0.0, flip=True, push=(1.08, 1.08))
    S(48.20, 53.50, 'cup_side_loop', loop=True, speed=3.0, timelapse=0.9, push=(1.0, 1.15))
    S(53.50, 58.90, 'cup_top_loop', loop=True, push=(1.0, 1.1))
    # ---------------------------------------------------------------- it stops trying
    S(58.90, 60.50, FACE)
    S(60.50, 65.50, 'stops_trying', ct0=0.0, speed=0.8)
    S(65.50, 68.20, FACE)
    S(68.20, 71.40, 'stops_trying', ct0=3.2, speed=0.25, push=(1.0, 1.1))
    S(71.40, 75.80, 'eye_macro', ct0=0.0)
    S(75.80, 77.10, FACE)
    # ---------------------------------------------------------------- the people walking past
    S(77.10, 79.10, 'cup_side_loop', ct0=0.5, loop=True, shadows=1.0)
    S(79.10, 82.30, 'cup_high_loop', ct0=1.0, loop=True, shadows=1.0, push=(1.0, 1.08))
    S(82.30, 85.40, 'cup_top_loop', ct0=2.0, loop=True, shadows=1.0)
    S(85.40, 87.30, FACE, shadows=0.8)
    S(87.30, 89.40, FACE)
    S(89.40, 91.96, 'cup_side_loop', ct0=2.0, loop=True, push=(1.0, 1.1))
    S(91.96, 92.58, 'flare', ct0=1.0)
    S(92.58, 96.94, FACE)
    S(96.94, 97.66, 'flare', ct0=1.8)
    S(97.66, 101.14, 'fish_macro_turn', ct0=0.5)
    S(101.14, 105.12, 'flare', ct0=0.0, speed=0.75, push=(1.0, 1.08))
    # ---------------------------------------------------------------- lifted into the ocean
    S(105.12, 108.26, 'reveal_wide', ct0=2.5, speed=0.5, push=(1.0, 1.14))
    S(108.26, 112.08, 'lift', ct0=0.3)
    S(112.08, 113.94, 'lift', ct0=3.6, speed=0.3)
    S(113.94, 118.18, 'cup_sinks', ct0=0.0, speed=0.95, grade='ocean', rays=0.8)
    S(118.18, 122.30, 'ocean_vast', ct0=0.0, grade='ocean', rays=1.0)
    S(122.30, 127.76, 'fish_free', ct0=0.0, speed=0.92, grade='ocean', rays=0.7)
    S(127.76, 129.22, 'sunrise_wide', ct0=2.0, grade='sun')
    S(129.22, 131.44, FACE)
    S(131.44, 137.88, 'ghost_circles', loop=True, grade='ocean', rays=0.5)
    S(137.88, 138.68, FACE)
    S(138.68, 144.54, 'ghost_circles', ct0=2.0, loop=True, grade='ocean', rays=0.5, push=(1.0, 1.1))
    S(144.54, 149.08, FACE)
    # ---------------------------------------------------------------- so many of them
    S(149.08, 153.52, 'shelf', ct0=0.0)
    S(153.52, 156.86, FACE)
    S(156.86, 158.80, 'shelf', ct0=3.0, speed=0.5)
    S(158.80, 161.46, FACE)
    S(161.46, 163.64, 'stops_trying', ct0=2.0, speed=0.5)
    S(163.64, 167.66, FACE)
    S(167.66, 170.22, 'stops_trying', ct0=3.0, speed=0.4)
    S(170.22, 175.66, FACE)
    S(175.66, 178.72, 'cup_top_loop', ct0=1.0, loop=True, shadows=1.0)
    # ---------------------------------------------------------------- ocean / sun / tree: NO.
    S(178.72, 181.44, FACE)
    S(181.44, 188.64, 'ocean_storm', ct0=0.0, speed=0.55, grade='storm', handheld=4.0)
    S(188.64, 189.18, BLACK)
    S(189.18, 196.29, 'sunrise', ct0=0.0, speed=0.56, grade='sun', bloom=0.5)
    S(196.29, 196.87, BLACK)
    S(196.87, 202.11, 'tree_storm', ct0=0.0, speed=0.76, grade='sun')
    S(202.11, 202.81, BLACK)
    S(202.81, 206.49, FACE, handheld=5.0)
    S(206.49, 211.53, 'cup_side_loop', ct0=0.0, loop=True, shadows=1.0, push=(1.0, 1.1))
    S(211.53, 217.88, FACE)
    S(217.88, 221.18, 'fish_free', ct0=2.5, grade='ocean', dim=0.35)
    S(221.18, 223.74, FACE)
    S(223.74, 227.14, FACE, bell=True, crack=227.0)
    S(227.14, 228.74, 'sunrise_wide', ct0=0.5, grade='sun')
    S(228.74, 233.34, 'sunrise_wide', ct0=1.5, speed=0.8, grade='sun', push=(1.0, 1.08))
    S(233.34, 237.60, FACE)
    S(237.60, 239.06, 'sunrise', ct0=3.0, grade='sun', bloom=0.6)
    S(239.06, 242.84, FACE, freeze=(239.06, 239.5))
    # ---------------------------------------------------------------- nine million years
    S(242.84, 247.56, 'cup_side_loop', loop=True, speed=4.0, timelapse=1.3, age=True, push=(1.0, 1.1))
    S(247.56, 248.56, 'empty_cup')
    S(248.56, 254.24, 'dry_cup', shadows=0.6, push=(1.0, 1.08))
    S(254.24, 260.54, 'dry_cup', push=(1.08, 1.18), dim=0.8)
    S(260.54, 268.30, 'no_cup', push=(1.0, 1.1), dim=0.7)
    S(268.30, 280.60, 'earth_turn', ct0=0.0, speed=0.49, grade='space')
    S(280.60, 287.10, 'galaxy', ct0=0.0, speed=0.46, grade='space')
    S(287.10, 298.78, 'galaxy', ct0=3.0, speed=0.26, grade='space')
    S(298.78, 302.32, BLACK)
    # ---------------------------------------------------------------- gone
    S(302.32, 303.34, 'dry_cup', push=(1.1, 1.12))
    S(303.34, 303.90, BLACK)
    S(303.90, 304.56, 'empty_cup', push=(1.1, 1.12))
    S(304.56, 305.14, BLACK)
    S(305.14, 306.42, FACE)
    S(306.42, 306.96, BLACK)
    S(306.96, 307.80, 'no_cup', shadows=1.0)
    S(307.80, 308.34, BLACK)
    S(308.34, 309.50, BLACK)
    S(309.50, 310.70, 'eye_macro', ct0=2.0)
    S(310.70, 311.56, BLACK)
    S(311.56, 322.40, 'reveal_wide', ct0=4.0, speed=-0.37, push=(1.12, 1.0))
    S(322.40, 329.07, BLACK)
    # ---------------------------------------------------------------- the question
    S(329.07, 331.03, FACE)
    S(331.03, 336.35, 'cup_high_loop', loop=True, push=(1.0, 1.1))
    S(336.35, 342.00, 'earth_turn', ct0=3.0, speed=0.5, grade='space')
    S(342.00, 350.54, FACE)
    S(350.54, 353.54, 'cup_top_loop', ct0=2.0, loop=True, push=(1.0, 1.25))
    S(353.54, 357.21, 'eye_macro', ct0=0.0, speed=1.09, push=(1.0, 1.35))
    S(357.21, END, 'reveal_wide', ct0=4.0, dim=0.22, push=(1.15, 1.2))

    # ---------------------------------------------------------------- events
    ev = dict(impacts=[], glitches=[], flashes=[], leaks=[], slams=[], types=[], counters=[], letterbox=[],
              no_captions=[], fades=[])
    WHITE, RED = (1.0, 1.0, 1.0), (0.9, 0.05, 0.03)

    def slam(t0, t1, text, style='red', impact=0.7, flash=None, **kw):
        ev['slams'].append(Slam(t0, t1, text, style, **kw))
        if impact:
            ev['impacts'].append((t0, impact))
        if flash:
            ev['flashes'].append((t0, 0.08, flash))

    slam(7.10, 7.46, 'NEVER', 'red', 0.8, WHITE)
    ev['impacts'].append((8.70, 0.5))
    ev['flashes'] += [(19.50, 0.12, WHITE), (127.76, 0.18, WHITE), (227.14, 0.14, WHITE), (8.82, 0.06, WHITE)]
    slam(42.12, 42.95, 'GLASS', 'white', 1.0, WHITE)
    slam(43.28, 43.82, 'WALL.', 'red', 0.6)
    ev['impacts'].append((47.08, 0.8))
    ev['flashes'].append((47.08, 0.06, WHITE))
    for tt in (48.28, 50.14):
        ev['flashes'].append((tt, 0.05, WHITE))
    slam(52.44, 53.40, 'YEARS', 'white', 0.5)
    slam(61.17, 62.10, 'STOPS', 'small', 0.3)
    slam(75.88, 77.10, 'THINK.', 'white', 0.5)
    slam(81.48, 82.60, 'NOT VERY GOOD', 'whisper', 0.2)
    slam(83.78, 85.30, "IT CAN'T DO ANYTHING", 'whisper', 0.2, wrap=["IT CAN'T", 'DO ANYTHING'])
    slam(86.02, 87.20, 'HA. HA. HA.', 'whisper', 0.15)
    slam(91.26, 91.90, 'SMALLER?', 'small', 0.2)
    slam(91.96, 92.58, 'NO.', 'giant', 1.0, WHITE)
    slam(96.94, 97.66, 'NO.', 'giant', 1.0, WHITE)
    slam(127.76, 129.10, 'FREE.', 'white', 0.4)
    slam(137.88, 138.62, 'WHY?', 'red', 0.6)
    slam(144.02, 144.54, 'MIND.', 'white', 0.3)
    slam(157.58, 158.80, 'QUIET.', 'small', 0.0)
    slam(188.64, 189.18, 'NO.', 'giant', 1.0, WHITE)
    slam(196.29, 196.87, 'NO.', 'giant', 1.0, WHITE)
    slam(202.11, 202.81, 'NO.', 'giant', 1.0, WHITE)
    slam(203.47, 204.05, 'WHY?', 'red', 0.8, RED)
    slam(205.45, 206.45, 'WHY?', 'giant', 1.0, RED)
    for w, a, b in (('JUST', 217.88, 218.42), ('GO', 218.44, 218.90), ('FOR', 218.92, 219.40), ('IT.', 219.42, 221.10)):
        slam(a, b, w, 'giant' if w != 'IT.' else 'red', 1.0 if w == 'IT.' else 0.6, WHITE if w == 'IT.' else None)
    ev['impacts'].append((227.14, 1.0))
    slam(237.60, 239.00, 'I LIVED?', 'gold', 0.3)
    ev['glitches'] += [(239.06, 0.45, 0.9)]
    ev['counters'].append(Counter(242.84, 247.4, 0, 9_000_000, 'YEARS'))
    slam(248.04, 248.56, 'GONE.', 'small', 0.3)
    ev['counters'].append(Counter(269.88, 271.4, 9_000_000, 18_000_000, 'YEARS', y=1500))
    ev['counters'].append(Counter(272.40, 273.5, 18_000_000, 27_000_000, 'YEARS', y=1500))
    ev['counters'].append(Counter(273.58, 276.2, 27_000_000, 36_000_000, 'YEARS', y=1500))
    for txt, a, b in (('1,000,000', 280.68, 281.60), ('9,000,000', 281.62, 282.86), ('100,000,000', 282.88, 283.92),
                      ('1,000,000,000', 283.94, 284.88), ('1,000,000,000,000', 284.90, 285.82),
                      ('+1,000,000,000,000', 286.30, 287.3)):
        slam(a, b, txt, 'number', 0.35)
    slam(299.10, 300.00, 'MORE TIME.', 'small', 0.0)
    slam(300.40, 301.30, 'MORE SILENCE.', 'small', 0.0)
    slam(301.36, 302.20, 'NO NOISE.', 'small', 0.0)
    for tt in (303.34, 304.56, 306.42, 307.80, 309.00, 310.70):
        slam(tt, tt + 0.52, 'GONE.', 'red', 0.5)
    ev['types'].append(TypeLine(308.34, 309.0, 'THE NAMES', 960, size=72, cps=16))
    slam(314.24, 315.9, 'NOTHING.', 'small', 0.0)
    slam(327.31, 328.9, 'NOTHING.', 'white', 0.2)
    slam(355.85, 357.21, 'THE BIGGEST PLACE', 'white', 0.3, wrap=['THE BIGGEST', 'PLACE?'])

    # tape glitch on every hard cut into Brandon + digital hits
    ev['glitches'] += [(t, 0.1, 0.5) for t in (87.30, 202.81, 211.53)]
    ev['leaks'] += [(26.10, 0.5), (127.76, 0.6), (189.18, 0.5), (228.74, 0.6), (237.60, 0.4)]
    ev['letterbox'] += [(181.44, 202.11), (228.74, 233.34)]
    ev['no_captions'] += [(217.8, 221.1), (357.3, 1e9), (280.6, 287.3)]
    ev['fades'] += [(0.0, 0.5, 'in'), (363.8, 365.0, 'out')]
    ev['end_card'] = 358.0

    # captions from the hand-written line breaks, aligned word-for-word to the transcript
    from overlay import align
    words = json.load(open(os.path.join(PROD, 'words.json')))
    phrases = align(os.path.join(PROD, 'captions.txt'), words)
    ev['captions'] = typo.Captions(phrases, cx=540, cy=1520, size=66, max_w=900)
    # sanity: contiguous cover
    E.sort(key=lambda s: s['t0'])
    for a, b in zip(E, E[1:]):
        assert abs(a['t1'] - b['t0']) < 1e-6, (a['t0'], a['t1'], b['t0'])
    return E, ev
