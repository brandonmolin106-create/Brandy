"""5. Chains: a stormy valley. Walking through the gate chains the player's legs (server-side:
glowing cuffs, beams and a weight; WalkSpeed and JumpPower drop). Ringing the three I CAN bells
cracks the chains; the third breaks them and gives a speed boost for a sprint-and-jump run up
the mountain path to the Insight.

Path rule: 4-stud gaps, 1-stud rises between rock pillars; ramps are ~15 degrees. While chained
(JumpPower 25) the gaps are impossible, so the bells can't be skipped.
"""
import math
import random

from .rbx import Inst, S, B, F, V3, U2, CFrame, look_at, attr_vec3
from . import kit
from .kit import (part, deco, disc, pillar, ball, wedge, label, surface_gui, billboard, prompt, point_light,
                  particles, one_color, speech_stone, insight_pedestal, return_portal, checkpoint, video_screen,
                  screen_console, path_attrs, block_on)
from .zone_time import marker

ORIGIN = (2400.0, 0.0, 2400.0)
BELLS = [(-40.0, -50.0), (46.0, -95.0), (-24.0, -145.0)]
CHAIN_AREA = ((-90.0, -5.0, -170.0), (90.0, 40.0, -8.0))     # min, max (relative)

VALLEY = (66, 70, 70)
ROCK = (84, 84, 96)
ROCK_DARK = (58, 58, 70)
BRONZE = (176, 122, 62)

def W(x, y, z):
    return (ORIGIN[0] + x, ORIGIN[1] + y, ORIGIN[2] + z)

def blk(name, x, ytop, zz, sx, sy, sz, color, material='Slate'):
    """Rock block (zone-relative coordinates) whose top face is at ytop."""
    return block_on(name, ORIGIN[0] + x, ORIGIN[1] + ytop, ORIGIN[2] + zz, sx, sy, sz, color, material)

def build(ctx):
    rnd = random.Random(55)
    z = Inst('Model', 'chains').attr(Zone='chains')
    kitf = Inst('Folder', 'chains').attr(Zone='chains')
    col = ctx.rgb('chains')

    # ---------------------------------------------------------------- valley
    z.add(part('Valley', CFrame(W(0, -2, -170)), (320, 4, 480), VALLEY, 'Ground'))
    for sx in (-1, 1):
        for i in range(5):
            h = rnd.uniform(60, 120)
            z.add(part('Ridge', CFrame(W(sx * rnd.uniform(130, 150), h / 2 - 2, 40 - i * 95)) *
                       CFrame.new(0, 0, 0, 0, rnd.uniform(-20, 20), rnd.uniform(-6, 6)),
                       (40, h, rnd.uniform(80, 110)), ROCK_DARK, 'Slate', shadow=False))
    z.add(*checkpoint('chains', 0, W(0, 0.3, 22), (10, 0.3, 10), color=ROCK, material='Slate', glow=col))
    z.add(speech_stone('SpeechStone', W(-15, 0, -1), W(0, 0, 22), 'chains_1', ctx.excerpt('chains_1'), accent=col))
    screen, _ = video_screen('chains', W(-36, 14, 16), W(0, 14, -12), 22, frame_color=ROCK_DARK, accent=col,
                             subtitle=ctx.theme('chains'))
    z.add(screen, screen_console('chains', W(-26, 0, 10), W(0, 0, -12), accent=col))

    # the chain gate with hanging chains
    for sx in (-1, 1):
        z.add(part('GatePillar', CFrame(W(sx * 10, 11, -6)), (3.2, 22, 3.2), ROCK, 'Slate'))
        z.add(deco('GateRune', CFrame(W(sx * 10, 11, -4.3)), (0.5, 16, 0.2), col, 'Neon', transparency=0.3))
    z.add(part('GateLintel', CFrame(W(0, 23, -6)), (24, 2.4, 4), ROCK, 'Slate'))
    for sx in (-1, 1):
        for k in range(7):
            yy = 21.2 - k * 1.25
            z.add(deco('Link', CFrame(W(sx * 4, yy, -6)) * CFrame.new(0, 0, 0, 0, 90 * (k % 2), 90),
                       (0.25, 1.5, 1.0), (150, 130, 190), 'Neon', shape=kit.CYL, transparency=0.2))

    # chained area (read by the server; the client uses it for the rain)
    area = part('ChainArea', CFrame(W((CHAIN_AREA[0][0] + CHAIN_AREA[1][0]) / 2, (CHAIN_AREA[0][1] + CHAIN_AREA[1][1]) / 2,
                                      (CHAIN_AREA[0][2] + CHAIN_AREA[1][2]) / 2)),
                (CHAIN_AREA[1][0] - CHAIN_AREA[0][0], CHAIN_AREA[1][1] - CHAIN_AREA[0][1],
                 CHAIN_AREA[1][2] - CHAIN_AREA[0][2]), (0, 0, 0), transparency=1, collide=False, touch=False,
                query=False, shadow=False)
    kitf.add(area)

    # ---------------------------------------------------------------- the three I CAN bells
    for i, (bx, bz) in enumerate(BELLS, start=1):
        m = Inst('Model', f'Bell{i}').attr(Index=i)
        face = W(0, 0, 22)
        cf = look_at(W(bx, 6.5, bz), (face[0], 6.5, face[2]))
        for sx in (-1, 1):
            m.add(part('Post', cf * CFrame.new(sx * 4.4, 0, 0), (1.8, 13, 1.8), ROCK, 'Slate'))
        beam = part('Beam', cf * CFrame.new(0, 6.9, 0), (11, 1.6, 2), ROCK_DARK, 'Slate')
        m.add(beam)
        plaque = part('Plaque', cf * CFrame.new(0, 6.9, -1.05), (6, 1.2, 0.1), (24, 22, 36), 'SmoothPlastic',
                      collide=False, shadow=False)
        plaque.add(surface_gui('Label', 40, label('Text', ctx.story['bellLabel'], color=kit.GOLD, family=kit.TITLE_FONT,
                                                  max_size=60, stroke=0.6)))
        m.add(plaque)
        body = part('Body', cf * CFrame.new(0, 2.6, 0), (4.4, 4.4, 4.4), BRONZE, 'Metal', shape=kit.BALL)
        body.tag('Bell').attr(Index=i, Pivot=attr_vec3(*cf.point((0, 6.1, 0))))
        body.add(prompt('bell', 'Ring', ctx.story['bellLabel'], dist=12, Index=i))
        m.add(body)
        m.add(part('Lip', cf * CFrame.new(0, 0.7, 0, 0, 0, 90), (1.1, 5.4, 5.4), BRONZE, 'Metal', shape=kit.CYL,
                   collide=False, shadow=False))
        m.add(deco('Crown', cf * CFrame.new(0, 5.2, 0, 0, 0, 90), (1.4, 1.4, 1.4), (120, 84, 44), 'Metal',
                   shape=kit.CYL))
        m.add(deco('Clapper', cf * CFrame.new(0, 0.2, 0), (0.9, 0.9, 0.9), (90, 64, 36), 'Metal', shape=kit.BALL))
        ring = deco('Halo', CFrame(W(bx, 0.08, bz)) * CFrame.new(0, 0, 0, 0, 0, 90), (0.08, 12, 12), col, 'Neon',
                    shape=kit.CYL, transparency=0.75)
        ring.tag('BellHalo').attr(Index=i)
        ring.add(point_light(col, 16, 0.8))
        m.add(ring)
        z.add(m)

    # boulders and dead trees in the valley
    for i in range(24):
        x = rnd.uniform(-110, 110)
        zz = rnd.uniform(-170, 10)
        if abs(x) < 16 and zz > -20:
            continue
        if any(math.hypot(x - bx, zz - bz) < 12 for bx, bz in BELLS):
            continue
        s = rnd.uniform(2, 6)
        z.add(kit.rock('Boulder', W(x, s * 0.3, zz), (s * 1.4, s, s * 1.2), rnd, color=ROCK))
    for i in range(10):
        x = rnd.uniform(-110, 110)
        zz = rnd.uniform(-170, 0)
        if any(math.hypot(x - bx, zz - bz) < 14 for bx, bz in BELLS) or abs(x) < 14:
            continue
        h = rnd.uniform(8, 13)
        tm = Inst('Model', 'DeadTree')
        tm.add(pillar('Trunk', W(x, 0, zz), 1.1, h, (60, 52, 50), 'Wood'))
        for k in range(3):
            tm.add(deco('Branch', CFrame(W(x, h * (0.55 + k * 0.15), zz)) *
                        CFrame.new(0, 0, 0, 0, rnd.uniform(0, 360), rnd.uniform(35, 60)) * CFrame.new(0, 2, 0),
                        (0.45, 4.5, 0.45), (60, 52, 50), 'Wood'))
        z.add(tm)

    # storm rain (kit; the client turns it off when the chains break)
    rain = part('Rain', CFrame(W(0, 90, -100)), (220, 1, 260), (0, 0, 0), transparency=1, collide=False, touch=False,
                query=False, shadow=False)
    rain.add(particles('Drops', one_color((190, 200, 230)), rate=260, life=(1.2, 1.5), speed=(70, 80), spread=(2, 2),
                       emission_dir=4, light=0.1, size=((0, 0.08, 0), (1, 0.08, 0)),
                       transparency=((0, 0.45, 0), (1, 0.6, 0)), texture=kit.SPARKLE))
    kitf.add(rain)

    # ---------------------------------------------------------------- mountain path
    order = 0
    def P(p):
        nonlocal order
        order += 1
        path_attrs(p, 'chains', order, 'ramp' if p.cls == 'WedgePart' else 'box')
        z.add(p)
        return p

    P(part('PathStart', CFrame(W(0, -0.45, -174)), (14, 1, 12), ROCK, 'Slate'))
    z.add(*checkpoint('chains', 1, W(0, 0.1, -174), (8, 0.2, 8), color=ROCK, material='Slate', glow=col, ry=0))
    # ramp 1: north, 0 -> 14 (a WedgePart is tallest at its back; turned 180 so it rises toward -Z)
    P(wedge('Ramp', CFrame(W(0, 7, -210), None) * CFrame.new(0, 0, 0, 0, 180, 0), (10, 14, 60), ROCK))
    P(blk('Landing', 3.5, 14, -246, 17, 14, 12, ROCK, 'Slate'))
    for i, x in enumerate((19.5, 30.5, 41.5)):
        P(blk('Pillar', x, 15 + i, -246, 7, 15 + i, 7, ROCK_DARK, 'Slate'))
    P(blk('Landing', 55, 18, -247, 12, 18, 14, ROCK, 'Slate'))
    z.add(*checkpoint('chains', 2, W(55, 18.05, -247), (7, 0.2, 7), color=ROCK, material='Slate', glow=col, ry=0))
    # ramp 2: north, 18 -> 30, on a rock support
    z.add(part('RampBase', CFrame(W(55, 9, -279)), (10, 18, 50), ROCK_DARK, 'Slate'))
    P(wedge('Ramp', CFrame(W(55, 24, -279), None) * CFrame.new(0, 0, 0, 0, 180, 0), (10, 12, 50), ROCK))
    P(blk('Landing', 53, 30, -310, 18, 30, 12, ROCK, 'Slate'))
    for i, x in enumerate((36.5, 25.5, 14.5, 3.5)):
        P(blk('Pillar', x, 31 + i, -310, 7, 31 + i, 7, ROCK_DARK, 'Slate'))
    P(blk('Landing', -10, 35, -311, 12, 35, 14, ROCK, 'Slate'))
    z.add(*checkpoint('chains', 3, W(-10, 35.05, -311), (7, 0.2, 7), color=ROCK, material='Slate', glow=col, ry=0))
    # ramp 3: north, 35 -> 49
    z.add(part('RampBase', CFrame(W(-10, 17.5, -343)), (10, 35, 50), ROCK_DARK, 'Slate'))
    P(wedge('Ramp', CFrame(W(-10, 42, -343), None) * CFrame.new(0, 0, 0, 0, 180, 0), (10, 14, 50), ROCK))
    summit = P(blk('Summit', -5, 49, -394, 60, 49, 52, ROCK, 'Slate'))
    z.add(*checkpoint('chains', 4, W(-10, 49.05, -376), (8, 0.2, 8), color=ROCK, material='Slate', glow=col, ry=0))
    z.add(insight_pedestal('chains', W(-5, 49, -398), ctx.zone('chains')['name'], col))
    z.add(speech_stone('SpeechStone', W(-22, 49, -392), W(-5, 49, -398), 'chains_3', ctx.excerpt('chains_3'),
                       accent=col))
    z.add(speech_stone('SpeechStone', W(12, 49, -392), W(-5, 49, -398), 'chains_4', ctx.excerpt('chains_4'),
                       accent=col))
    z.add(return_portal(W(-5, 49, -414), W(-5, 49, -398), color=col))
    marker(kitf, 'chains_4', W(-8, 52, -386), 12)
    # a banner of light on the summit (lit after the break, by the client)
    beacon = deco('Beacon', CFrame(W(-5, 49 + 40, -404)), (1.5, 80, 1.5), col, 'Neon', transparency=0.6)
    beacon.add(point_light(col, 40, 2))
    z.add(beacon)

    # the mountain mass around the path: sloped massifs that rise AWAY from the path
    # (a WedgePart is tallest at its back, so ry picks which way the slope climbs)
    for (x, zz, w, h, d, ry) in ((0, -505, 280, 170, 120, 180), (-112, -330, 150, 120, 90, -90),
                                 (122, -330, 150, 130, 90, 90), (-70, -470, 120, 140, 90, 200),
                                 (80, -470, 130, 150, 90, 160)):
        z.add(wedge('Massif', CFrame(W(x, h / 2 - 2, zz)) * CFrame.new(0, 0, 0, 0, ry, 0), (w, h, d), ROCK_DARK,
                    'Slate', shadow=False))
    for (x, zz, h, ry) in ((-40, -560, 150, 10), (30, -575, 190, -14), (95, -545, 120, 30), (-105, -520, 110, -25)):
        z.add(part('Spire', CFrame(W(x, h / 2 - 2, zz)) * CFrame.new(0, 0, 0, 0, ry, 4), (34, h, 30), (70, 70, 84),
                   'Slate', shadow=False, collide=False, touch=False, query=False))
    for i in range(16):
        a = 360 * i / 16
        z.add(part('Boundary', look_at((ORIGIN[0] + 190 * math.sin(math.radians(a)), 60,
                                        ORIGIN[2] - 190 + 260 * math.cos(math.radians(a))),
                                       (ORIGIN[0], 60, ORIGIN[2] - 190)),
                   (90, 120, 2), (0, 0, 0), transparency=1, shadow=False, touch=False, query=False))
    return z, kitf
