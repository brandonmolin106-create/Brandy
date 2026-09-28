"""1. The Clock Tower: a brass-gear spiral around a tower, two clock-dial rides, a pendulum,
falling sand, and the Insight on the roof.

Path: a square spiral 26 studs from the tower axis. Nodes sit every 13 studs along the
perimeter and rise 2 studs each (gap 3 studs between 10-stud gears). At two corners the
path becomes a clock dial: a fixed hub with two rotating hands that sweep past an entry
and an exit ledge (1 stud gap), so the player rides a hand or rests on the hub.
"""
import math
import random

from .rbx import Inst, S, B, F, V3, C3, U2, CFrame, look_at, attr_vec3
from . import kit
from .kit import (part, deco, disc, pillar, ball, label, surface_gui, billboard, prompt, point_light, particles,
                  one_color, speech_stone, insight_pedestal, return_portal, checkpoint, video_screen,
                  screen_console, path_attrs)

ORIGIN = (2400.0, 0.0, 0.0)
SIDE = 26.0
LOOP = 208.0
GEAR_D = 10.0
LEDGE = 7.0
LANDING = 10.0
HUB_D = 5.0
HAND_R0, HAND_R1 = 2.5, 11.5
DIAL_U = (52.0, 364.0)
ROTATING_U = (13.0, 91.0, 143.0, 182.0, 234.0, 286.0, 325.0)

SAND = (214, 186, 132)
SANDSTONE = (196, 164, 116)
BRICK = (150, 110, 78)

def W(x, y, z):
    return (ORIGIN[0] + x, ORIGIN[1] + y, ORIGIN[2] + z)

def perim(u):
    u = u % LOOP
    if u < 52:
        return (-26 + u, 26.0)
    if u < 104:
        return (26.0, 26 - (u - 52))
    if u < 156:
        return (26 - (u - 104), -26.0)
    return (-26.0, -26 + (u - 156))

def path_nodes():
    """[(kind, u, top_y)] from the ground to the last dial exit."""
    seq = [('corner', 0.0), ('gear', 13.0), ('gear', 26.0), ('ledge', 36.0), ('dial', 52.0), ('ledge', 68.0)]
    for k in range(6, 27):
        u = 13.0 * k
        seq.append(('corner' if u % 52 == 0 else 'gear', u))
    seq += [('ledge', 348.0), ('dial', 364.0), ('ledge', 380.0)]
    out, h = [], 2.0
    for i, (kind, u) in enumerate(seq):
        if i > 0:
            prev_kind = seq[i - 1][0]
            flat = kind == 'dial' or (kind == 'ledge' and prev_kind == 'dial')
            if not flat:
                h += 2.0
        out.append((kind, u, h))
    return out

def gear_model(name, center, diameter, thickness, color, teeth=6, spokes=False, tooth_col=None):
    """A gear: collidable disc + decorative teeth (+ spokes so rotation is visible)."""
    x, y, z = center
    m = Inst('Model', name)
    d = disc('Disc', (x, y, z), diameter, thickness, color, 'Metal')
    m.add(d)
    tc = tooth_col or kit.BRASS_DARK
    r = diameter / 2
    for i in range(teeth):
        a = 2 * math.pi * i / teeth
        m.add(deco('Tooth', CFrame.new(x + (r + 0.35) * math.sin(a), y - thickness / 2 - 0.15,
                                       z + (r + 0.35) * math.cos(a), 0, math.degrees(a), 0),
                   (1.6, thickness * 0.8, 1.4), tc, 'Metal'))
    m.add(deco('Cap', CFrame.new(x, y + 0.03, z, 0, 0, 90), (0.08, diameter * 0.36, diameter * 0.36),
               kit.BRASS_DARK, 'Metal'))
    if spokes:
        for i in range(3):
            m.add(deco('Spoke', CFrame.new(x, y + 0.04, z, 0, i * 60, 0), (0.5, 0.08, diameter * 0.86),
                       (120, 84, 38), 'Metal'))
    return m, d

def wall_gear(name, center, normal, diameter, speed, color=kit.BRASS, teeth=8):
    """Big vertical decorative gear on a wall, rotating about the wall's outward normal (kit)."""
    x, y, z = center
    ry = {(0, 0, 1): -90, (0, 0, -1): 90, (1, 0, 0): 0, (-1, 0, 0): 180}[normal]
    base = CFrame.new(x, y, z, 0, ry, 0)          # local X (cylinder axis) = outward normal
    m = Inst('Model', name).attr(Kinetic='rotate', Pivot=attr_vec3(x, y, z), Axis=attr_vec3(*normal), Speed=speed,
                                  Phase=0.0)
    m.add(deco('Disc', base, (1.4, diameter, diameter), color, 'Metal', shape=kit.CYL, shadow=True))
    r = diameter / 2
    for i in range(teeth):
        a = 360.0 * i / teeth
        m.add(deco('Tooth', base * CFrame.new(0, 0, 0, a, 0, 0) * CFrame.new(0, r + 0.6, 0), (1.2, 1.6, 2.0),
                   kit.BRASS_DARK, 'Metal'))
    m.add(deco('Hub', base * CFrame.new(0.5, 0, 0), (1.0, diameter * 0.28, diameter * 0.28), (90, 64, 30), 'Metal',
               shape=kit.CYL))
    for i in range(2):
        m.add(deco('Spoke', base * CFrame.new(0.72, 0, 0, i * 90, 0, 0), (0.2, diameter * 0.9, 0.9),
                   (120, 84, 38), 'Metal'))
    return m

def build(ctx):
    rnd = random.Random(1)
    z = Inst('Model', 'time').attr(Zone='time')
    kitf = Inst('Folder', 'time').attr(Zone='time')
    col = ctx.rgb('time')

    # ---------------------------------------------------------------- ground
    z.add(disc('Desert', W(0, 0, 0), 300, 6, SAND, 'Sand'))
    z.add(disc('Plaza', W(0, 0.1, 0), 92, 0.4, SANDSTONE, 'Sandstone', shadow=False))
    z.add(part('Walkway', CFrame(W(0, 0.1, 70)), (9, 0.4, 50), SANDSTONE, 'Sandstone', shadow=False))
    for i in range(9):
        a = math.radians(i * 40 + rnd.uniform(-12, 12))
        d = rnd.uniform(70, 115)
        r = rnd.uniform(118, 150)
        z.add(ball('Dune', W(r * math.sin(a), -d * 0.37, r * math.cos(a)), d, (206, 176, 120), 'Sand',
                   collide=False, touch=False, query=False, shadow=False))
    z.add(*checkpoint('time', 0, W(0, 0.4, 100), (12, 0.8, 12), color=(120, 100, 76), material='Sandstone',
                      glow=col))

    # ---------------------------------------------------------------- tower
    z.add(part('Core', CFrame(W(0, 26.5, 0)), (30, 53, 30), BRICK, 'Brick'))
    for y in (13, 26, 39, 52):
        z.add(part('Band', CFrame(W(0, y, 0)), (31, 1.2, 31), kit.BRASS, 'Metal', shadow=False))
    for (nx, nz) in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        for wy in (19.5, 45):
            wx, wz = nx * 15.1, nz * 15.1
            win = deco('Window', CFrame(W(wx, wy, wz)), (0.4 if nx else 4, 6, 4 if nx else 0.4), (255, 196, 120),
                       'Neon', transparency=0.15)
            z.add(win)
    roof = part('Roof', CFrame(W(0, 53.5, 0)), (34, 1, 34), SANDSTONE, 'Sandstone')
    z.add(roof)
    # railings with a gap on the west side where the bridge arrives
    z.add(part('Rail', CFrame(W(0, 55.2, 16.7)), (34, 2.4, 0.6), kit.BRASS, 'Metal', shadow=False))
    z.add(part('Rail', CFrame(W(0, 55.2, -16.7)), (34, 2.4, 0.6), kit.BRASS, 'Metal', shadow=False))
    z.add(part('Rail', CFrame(W(16.7, 55.2, 0)), (0.6, 2.4, 34), kit.BRASS, 'Metal', shadow=False))
    z.add(part('Rail', CFrame(W(-16.7, 55.2, 5.1)), (0.6, 2.4, 23.8), kit.BRASS, 'Metal', shadow=False))
    z.add(part('Rail', CFrame(W(-16.7, 55.2, -15.0)), (0.6, 2.4, 4.0), kit.BRASS, 'Metal', shadow=False))
    z.add(part('Upper', CFrame(W(0, 67, 0)), (14, 26, 14), BRICK, 'Brick'))
    z.add(part('UpperBand', CFrame(W(0, 79.6, 0)), (15, 1, 15), kit.BRASS, 'Metal', shadow=False))
    z.add(ball('Dome', W(0, 80, 0), 15, kit.BRASS, 'Metal'))
    z.add(pillar('Spire', W(0, 87, 0), 0.8, 9, kit.BRASS_DARK, 'Metal', shadow=False))
    top = deco('SpireOrb', CFrame(W(0, 96.8, 0)), (1.8, 1.8, 1.8), col, 'Neon', shape=kit.BALL)
    top.add(point_light(col, 40, 2))
    z.add(top)
    # clock faces on the upper tower (south and north); their hands are animated from the kit
    for sgn in (1, -1):
        fz = sgn * 7.15
        face = part('ClockFace', CFrame(W(0, 70, fz), None) * CFrame.new(0, 0, 0, 0, 90, 0), (0.3, 11, 11),
                    (240, 228, 198), 'Marble', shape=kit.CYL, shadow=False)
        z.add(face)
        for i in range(12):
            a = math.radians(i * 30)
            long = i % 3 == 0
            z.add(deco('Tick', CFrame(W(4.4 * math.sin(a), 70 + 4.4 * math.cos(a), fz + sgn * 0.2)) *
                       CFrame.new(0, 0, 0, 0, 0, -math.degrees(a)), (0.35, 1.1 if long else 0.6, 0.1),
                       (60, 44, 30), 'Metal'))
        for hand, (length, width, speed) in (('Minute', (4.2, 0.45, 6.0)), ('Hour', (2.8, 0.6, 0.5))):
            hm = Inst('Model', f'{hand}Hand').attr(Kinetic='rotate', Pivot=attr_vec3(*W(0, 70, fz)),
                                                   Axis=attr_vec3(0, 0, -sgn), Speed=speed, Phase=0.0)
            hm.add(deco('Hand', CFrame(W(0, 70 + length / 2, fz + sgn * 0.35)), (width, length, 0.12), (40, 30, 24),
                        'Metal'))
            kitf.add(hm)
    # wall gears (rotating, kit)
    kitf.add(wall_gear('WallGear', W(0, 30, 15.9), (0, 0, 1), 16, 12))
    kitf.add(wall_gear('WallGear', W(10.6, 23.5, 15.9), (0, 0, 1), 9, -21.3))
    kitf.add(wall_gear('WallGear', W(0, 30, -15.9), (0, 0, -1), 16, -12))
    kitf.add(wall_gear('WallGear', W(15.9, 30, 0), (1, 0, 0), 14, 10))
    kitf.add(wall_gear('WallGear', W(15.9, 38, -9), (1, 0, 0), 8, -17.5))
    kitf.add(wall_gear('WallGear', W(-15.9, 30, 0), (-1, 0, 0), 14, -10))

    # ---------------------------------------------------------------- the gear spiral
    nodes = path_nodes()
    order = 0
    cp_index = 1
    for i, (kind, u, h) in enumerate(nodes):
        px, pz = perim(u)
        if kind == 'dial':
            order += 1
            build_dial(ctx, z, kitf, (px, h, pz), i, order, cp_index, col)
            cp_index += 1
            continue
        order += 1
        if kind == 'gear':
            rotating = u in ROTATING_U
            gm, d = gear_model('Gear', W(px, h, pz), GEAR_D, 1.2, kit.BRASS, teeth=6, spokes=rotating)
            path_attrs(d, 'time', order, 'disc')
            if rotating:
                speed = 24.0 if (i % 2 == 0) else -24.0
                gm.attr(Kinetic='rotate', Pivot=attr_vec3(*W(px, h, pz)), Axis=attr_vec3(0, 1, 0), Speed=speed,
                        Phase=0.0)
                kitf.add(gm)
            else:
                z.add(gm)
                if u in (26.0, 117.0, 221.0, 299.0):
                    d.add(particles('SandFall', one_color((222, 192, 138)), rate=18, life=(2.5, 3.5),
                                    speed=(8, 12), spread=(3, 3), emission_dir=4, light=0.2,
                                    size=((0, 0.16, 0), (1, 0.1, 0)), transparency=((0, 0.1, 0), (1, 0.6, 0))))
        elif kind == 'corner':
            if u == 208.0:
                pad, ring = checkpoint('time', cp_index, W(px, h, pz), (LANDING, 1, LANDING),
                                       color=SANDSTONE, material='Sandstone', glow=col)
                cp_index += 1
                path_attrs(pad, 'time', order, 'box')
                z.add(pad, ring)
                z.add(speech_stone('SpeechStone', W(px - 2.6, h, pz + 2.6), W(0, h, 0), 'time_2',
                                   ctx.excerpt('time_2'), accent=col))
                marker(kitf, 'time_2', W(px, h + 3, pz), 9)
            else:
                pad = part('Landing', CFrame(W(px, h - 0.5, pz)), (LANDING, 1, LANDING), SANDSTONE, 'Sandstone')
                path_attrs(pad, 'time', order, 'box')
                z.add(pad)
            z.add(part('LandingTrim', CFrame(W(px, h - 1.1, pz)), (LANDING + 0.6, 0.3, LANDING + 0.6), kit.BRASS,
                       'Metal', shadow=False, collide=False, touch=False, query=False))
        elif kind == 'ledge':
            pad = part('Ledge', CFrame(W(px, h - 0.5, pz)), (LEDGE, 1, LEDGE), SANDSTONE, 'Sandstone')
            path_attrs(pad, 'time', order, 'box')
            z.add(pad)

    # bridge from the last dial's exit ledge up to the roof
    order += 1
    bridge = part('Bridge', CFrame(W(-19.25, 52.5, -10)), (4.5, 1, 4), SANDSTONE, 'Sandstone')
    path_attrs(bridge, 'time', order, 'box')
    z.add(bridge)
    order += 1
    path_attrs(roof, 'time', order, 'box')
    pad, ring = checkpoint('time', cp_index, W(-11, 54.05, -11), (7, 0.2, 7), color=SANDSTONE,
                           material='Sandstone', glow=col, ry=-90)
    z.add(pad, ring)

    # insight, last speech stone and the way home, on the roof (south side)
    z.add(insight_pedestal('time', W(0, 54, 11.5), ctx.zone('time')['name'], col))
    z.add(speech_stone('SpeechStone', W(-11, 54, 12), W(0, 54, 40), 'time_3', ctx.excerpt('time_3'), accent=col))
    z.add(return_portal(W(11, 54, 13), W(11, 54, 40), color=col))

    # pendulum gantry + the pendulum itself (kit, swinging)
    z.add(part('Gantry', CFrame(W(0, 78, -25.5)), (2, 2, 37), kit.BRASS_DARK, 'Metal'))
    z.add(part('Strut', look_at(W(0, 70, -12), W(0, 78, -30)), (1.2, 1.2, 20), kit.BRASS_DARK, 'Metal',
               shadow=False))
    z.add(part('PivotBox', CFrame(W(0, 77, -44)), (3, 3, 3), kit.BRASS, 'Metal'))
    pend = Inst('Model', 'Pendulum').attr(Kinetic='swing', Pivot=attr_vec3(*W(0, 77, -44)), Axis=attr_vec3(0, 0, 1),
                                          Amplitude=26.0, Period=4.0, Phase=0.0)
    pend.add(deco('Rod', CFrame(W(0, 57.5, -44)), (0.6, 39, 0.6), kit.BRASS_DARK, 'Metal'))
    bob = deco('Bob', CFrame(W(0, 36, -44), None) * CFrame.new(0, 0, 0, 0, 90, 0), (1.6, 8, 8), kit.BRASS, 'Metal',
               shape=kit.CYL, shadow=True)
    bob.add(point_light(col, 24, 1.4))
    pend.add(bob, deco('BobGlow', CFrame(W(0, 36, -44), None) * CFrame.new(0, 0, 0, 0, 90, 0), (1.8, 3, 3), col,
                       'Neon', shape=kit.CYL))
    kitf.add(pend)

    # hourglass landmark with falling sand
    hx, hz = -64.0, 48.0
    hg = Inst('Model', 'Hourglass')
    hg.add(disc('HourglassBase', W(hx, 1.4, hz), 22, 1.4, kit.BRASS_DARK, 'Metal'))
    hg.add(disc('HourglassTop', W(hx, 41, hz), 22, 1.4, kit.BRASS_DARK, 'Metal'))
    for i in range(4):
        a = math.radians(45 + 90 * i)
        hg.add(pillar('Post', W(hx + 9.5 * math.sin(a), 1.4, hz + 9.5 * math.cos(a)), 1.4, 38.2, kit.BRASS, 'Metal'))
    hg.add(ball('Bulb', W(hx, 11.2, hz), 17.5, (225, 238, 255), 'Glass', transparency=0.6, reflect=0.1))
    hg.add(ball('Bulb', W(hx, 30.4, hz), 17.5, (225, 238, 255), 'Glass', transparency=0.6, reflect=0.1))
    hg.add(ball('SandPile', W(hx, 3.4, hz), 15, (222, 190, 132), 'Sand', collide=False, touch=False, query=False))
    hg.add(ball('SandTop', W(hx, 31.5, hz), 9, (222, 190, 132), 'Sand', collide=False, touch=False, query=False))
    stream = deco('Stream', CFrame(W(hx, 19, hz)), (0.35, 12, 0.35), (230, 200, 140), 'Neon', transparency=0.25)
    stream.add(particles('Grains', one_color((236, 206, 150)), rate=30, life=(0.8, 1.1), speed=(12, 14),
                         spread=(4, 4), emission_dir=4, light=0.4, size=((0, 0.14, 0), (1, 0.1, 0))))
    hg.add(stream)
    z.add(hg)

    # giant clock hands half-buried in the dunes
    for (x, zz, ry, tilt) in ((70, -40, 30, 18), (-80, -30, -50, 14), (50, 90, 110, 20)):
        z.add(part('BuriedHand', CFrame(W(x, 4, zz)) * CFrame.new(0, 0, 0, tilt, ry, 0), (3, 1.2, 34),
                   (60, 46, 34), 'Metal'))

    # sand drifting down over the whole zone
    sky = part('SandSky', CFrame(W(0, 130, 0)), (260, 1, 260), (0, 0, 0), transparency=1, collide=False, touch=False,
               query=False, shadow=False)
    sky.add(particles('Sand', one_color((230, 200, 150)), rate=45, life=(12, 16), speed=(6, 9), spread=(8, 8),
                      emission_dir=4, light=0.25, size=((0, 0.14, 0), (1, 0.14, 0)),
                      transparency=((0, 0.2, 0), (0.85, 0.3, 0), (1, 1, 0))))
    z.add(sky)

    # screen for Brandon's video (faces the arrival pad)
    screen, _ = video_screen('time', W(38, 15, 76), W(0, 15, 100), 22, frame_color=(110, 84, 58), accent=col,
                             subtitle=ctx.theme('time'))
    z.add(screen, screen_console('time', W(30, 0, 84), W(0, 0, 100), accent=col))

    # first speech stone at the foot of the spiral
    z.add(speech_stone('SpeechStone', W(-38, 0, 40), W(0, 0, 100), 'time_1', ctx.excerpt('time_1'), accent=col))
    return z, kitf

def build_dial(ctx, z, kitf, center, node_i, order, cp_index, col):
    px, h, pz = center
    hub, ring = checkpoint('time', cp_index, W(px, h, pz), (HUB_D, 1, HUB_D), shape='disc', color=kit.BRASS,
                           material='Metal', glow=col)
    z.add(hub, ring)
    # decorative translucent dial face below the hands, with ticks
    z.add(deco('DialFace', CFrame(W(px, h - 3.6, pz), None) * CFrame.new(0, 0, 0, 0, 0, 90), (0.2, 25, 25),
               (240, 226, 196), 'Glass', shape=kit.CYL, transparency=0.55))
    z.add(deco('DialRing', CFrame(W(px, h - 3.5, pz), None) * CFrame.new(0, 0, 0, 0, 0, 90), (0.25, 26, 26), col,
               'Neon', shape=kit.CYL, transparency=0.6))
    for i in range(12):
        a = math.radians(i * 30)
        z.add(deco('DialTick', CFrame(W(px + 11 * math.sin(a), h - 3.3, pz + 11 * math.cos(a))) *
                   CFrame.new(0, 0, 0, 0, math.degrees(a), 0), (0.5, 0.2, 2.2 if i % 3 == 0 else 1.2),
                   (60, 44, 30), 'Metal'))
    z.add(pillar('DialPost', W(px, h - 30, pz), 1.6, 26.5, kit.BRASS_DARK, 'Metal', shadow=False, collide=False,
                 touch=False, query=False))
    speed = 14.0 if node_i < 10 else -16.0
    hands = Inst('Model', 'ClockHands').attr(Kinetic='rotate', Pivot=attr_vec3(*W(px, h, pz)),
                                             Axis=attr_vec3(0, 1, 0), Speed=speed, Phase=0.0)
    length = HAND_R1 - HAND_R0
    for k in (0, 1):
        a = k * 180.0
        mid = (HAND_R0 + HAND_R1) / 2
        hcf = CFrame(W(px, h, pz)) * CFrame.new(0, 0, 0, 0, a, 0) * CFrame.new(0, -0.5, mid)
        hand = part('Hand', hcf, (3.4, 1, length), (52, 40, 30), 'Metal')
        if k == 0:
            path_attrs(hand, 'time', order, 'sweep', SweepPivot=attr_vec3(*W(px, h, pz)), SweepRadius=HAND_R1)
        hands.add(hand)
        hands.add(deco('HandTip', hcf * CFrame.new(0, 0.02, length / 2 - 0.4, 0, 45, 0), (2.2, 1.02, 2.2),
                       (52, 40, 30), 'Metal'))
        hands.add(deco('HandInlay', hcf * CFrame.new(0, 0.52, 0), (0.5, 0.06, length - 1.5), col, 'Neon',
                       transparency=0.25))
    kitf.add(hands)

def marker(kitf, line_id, pos, radius):
    """Invisible trigger in the kit: the client auto-plays line_id once when the player comes near."""
    mk = part('BeatMarker', CFrame(pos), (1, 1, 1), (0, 0, 0), transparency=1, collide=False, touch=False,
              query=False, shadow=False)
    mk.attr(LineId=line_id, Radius=float(radius))
    kitf.add(mk)
    return mk
