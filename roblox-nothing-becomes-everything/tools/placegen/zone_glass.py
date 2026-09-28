"""3. The Glass Box: a glass room on a lakeshore. Heavy word blocks drop in and the (visual only)
water rises with each one. Each block has a 'Let it go' prompt; letting go dissolves it and the
water drains. The door was unlocked the whole time; it glows once the water is low. Walking
out shatters the box outward.

The box, blocks, water and door are in the kit (per player, client-side); the platform, the
shore, the pier and the Insight are static.
"""
import math
import random

from .rbx import Inst, S, B, F, V3, U2, CFrame, look_at, attr_vec3
from . import kit
from .kit import (part, deco, disc, pillar, ball, label, surface_gui, billboard, prompt, point_light, particles,
                  one_color, speech_stone, insight_pedestal, return_portal, checkpoint, video_screen,
                  screen_console)

ORIGIN = (-2400.0, 0.0, 0.0)
HALF, FLOOR, TOP = 20.0, 1.0, 23.0
DOOR_W, DOOR_H = 7.0, 11.0
WATER_STEP = 2.8

GRASS = (98, 150, 100)
SHORE = (214, 200, 160)
GLASS_COL = (206, 232, 255)
BEAM = (70, 80, 96)

BLOCK_SPOTS = [(-11, -8, 10), (11, -11, -15), (-12, 8, -5), (12, 7, 12), (6.5, -1, 90)]

def W(x, y, z):
    return (ORIGIN[0] + x, ORIGIN[1] + y, ORIGIN[2] + z)

def build(ctx):
    rnd = random.Random(33)
    z = Inst('Model', 'glass').attr(Zone='glass')
    kitf = Inst('Folder', 'glass').attr(Zone='glass', BoxMin=attr_vec3(*W(-HALF, FLOOR, -HALF)),
                                        BoxMax=attr_vec3(*W(HALF, TOP, HALF)), WaterStep=WATER_STEP,
                                        DoorwayZ=ORIGIN[2] - HALF - 1.5)
    col = ctx.rgb('glass')

    # ---------------------------------------------------------------- land, shore and lake
    z.add(part('Ground', CFrame(W(0, -2, 60)), (380, 4, 240), GRASS, 'Grass'))
    z.add(part('Shore', CFrame(W(0, -1.95, -64)), (380, 4, 8), SHORE, 'Sand', shadow=False))
    z.add(part('LakeBed', CFrame(W(0, -5, -128)), (380, 4, 120), (70, 96, 90), 'Mud', shadow=False))
    z.add(part('Lake', CFrame(W(0, -0.9, -128)), (380, 0.4, 120), (70, 150, 196), 'Glass', collide=False, touch=False,
               query=False, shadow=False, transparency=0.3, reflect=0.2))
    z.add(part('Platform', CFrame(W(0, 0.5, 0)), (46, 1, 46), (230, 228, 224), 'Marble'))
    z.add(part('PlatformTrim', CFrame(W(0, 0.3, 0)), (47.2, 0.6, 47.2), (180, 186, 196), 'Marble', shadow=False))
    z.add(*checkpoint('glass', 0, W(0, 1.12, 12), (7, 0.2, 7), color=(210, 214, 222), material='Marble', glow=col))
    z.add(speech_stone('SpeechStone', W(-14, 1, 15), W(0, 1, 0), 'glass_1', ctx.excerpt('glass_1'), accent=col))

    # path to the pier, the pier, the insight
    z.add(part('ShorePath', CFrame(W(0, 0.05, -40)), (7, 0.3, 36), (200, 192, 170), 'Pebble', shadow=False))
    pier = Inst('Model', 'Pier')
    for i in range(12):
        pier.add(part('Plank', CFrame(W(0, 0.3, -58 - i * 2.05)), (8, 0.4, 1.9), (150, 110, 76), 'WoodPlanks',
                      shadow=False))
    for (px, pz) in ((-3.6, -60), (3.6, -60), (-3.6, -70), (3.6, -70), (-3.6, -80), (3.6, -80)):
        pier.add(pillar('PierPost', W(px, -5, pz), 0.8, 6, (110, 80, 56), 'Wood', shadow=False))
    z.add(pier)
    z.add(insight_pedestal('glass', W(0, 0.5, -78), ctx.zone('glass')['name'], col))
    z.add(*checkpoint('glass', 1, W(0, 0.2, -30), (7, 0.2, 7), color=(200, 192, 170), material='Pebble', glow=col))
    z.add(speech_stone('SpeechStone', W(-8, 0, -36), W(0, 0, -40), 'glass_2', ctx.excerpt('glass_2'), accent=col))
    z.add(speech_stone('SpeechStone', W(8, 0, -46), W(0, 0, -40), 'glass_3', ctx.excerpt('glass_3'), accent=col))
    z.add(return_portal(W(16, 0, -54), W(0, 0, -40), color=col))
    screen, _ = video_screen('glass', W(44, 14, -4), W(0, 14, 0), 22, frame_color=(200, 204, 214), accent=col,
                             subtitle=ctx.theme('glass'))
    z.add(screen, screen_console('glass', W(32, 0, -12), W(0, 0, 0), accent=col))

    # scenery: trees, reeds, rocks, flowers
    for i in range(36):
        x = rnd.uniform(-170, 170)
        zz = rnd.uniform(-50, 170)
        if abs(x) < 60 and zz < 70:
            continue
        if rnd.random() < 0.6:
            z.add(kit.tree('Tree', W(x, 0, zz), rnd, trunk_col=(96, 70, 50),
                           leaf_cols=((84, 150, 84), (100, 164, 90), (70, 136, 80)), scale=rnd.uniform(1.0, 1.5)))
        else:
            z.add(kit.pine('Pine', W(x, 0, zz), rnd, scale=rnd.uniform(1.1, 1.8), col=(60, 110, 76)))
    for i in range(30):
        x = rnd.uniform(-150, 150)
        if abs(x) < 8:
            continue
        h = rnd.uniform(2, 4)
        z.add(deco('Reed', CFrame(W(x, h / 2 - 1, -61 - rnd.uniform(0, 4))) * CFrame.new(0, 0, 0, rnd.uniform(-8, 8), 0,
                                                                                    rnd.uniform(-8, 8)),
                   (0.25, h, 0.25), (110, 140, 80), 'Grass'))
    for i in range(12):
        x = rnd.uniform(-160, 160)
        zz = rnd.uniform(-58, 160)
        if abs(x) < 34 and zz < 40:
            continue
        s = rnd.uniform(2, 5)
        z.add(kit.rock('Rock', W(x, s * 0.3, zz), (s * 1.5, s, s * 1.2), rnd, color=(140, 142, 150)))
    flower_cols = [(255, 236, 140), (255, 190, 210), (220, 220, 255)]
    for i in range(40):
        x = rnd.uniform(-60, 60)
        zz = rnd.uniform(-56, 60)
        if abs(x) < 26 and abs(zz) < 26 or abs(x) < 6:
            continue
        z.add(deco('Flower', CFrame(W(x, 0.35, zz)), (0.6, 0.6, 0.6), flower_cols[i % 3], 'SmoothPlastic',
                   shape=kit.BALL))
    for i in range(16):
        a = 360 * i / 16
        z.add(part('Boundary', look_at((ORIGIN[0] + 180 * math.sin(math.radians(a)), 25,
                                        ORIGIN[2] + 180 * math.cos(math.radians(a))), (ORIGIN[0], 25, ORIGIN[2])),
                   (72, 50, 2), (0, 0, 0), transparency=1, shadow=False, touch=False, query=False))

    # ---------------------------------------------------------------- the glass box (kit)
    box = Inst('Folder', 'Box')
    hgt = TOP - FLOOR

    def panel(name, cx, cy, cz, sx, sy, sz, outward):
        p = part(name, CFrame(W(cx, cy, cz)), (sx, sy, sz), GLASS_COL, 'Glass', transparency=0.62, reflect=0.12,
                 shadow=False)
        p.attr(Outward=attr_vec3(*outward))
        box.add(p)

    # south, east, west walls: 4 x 2 panels
    for (axis, sgn) in (('z', 1), ('x', 1), ('x', -1)):
        for c in range(4):
            for r in range(2):
                a = -HALF + 5 + c * 10
                cy = FLOOR + hgt / 4 + r * hgt / 2
                if axis == 'z':
                    panel('Panel', a, cy, sgn * HALF, 10, hgt / 2, 0.5, (0, 0, sgn))
                else:
                    panel('Panel', sgn * HALF, cy, a, 0.5, hgt / 2, 10, (sgn, 0, 0))
    # north wall with the door opening in the lower middle
    lower = hgt / 2
    for (x0, x1) in ((-20, -10), (-10, -DOOR_W / 2), (DOOR_W / 2, 10), (10, 20)):
        panel('Panel', (x0 + x1) / 2, FLOOR + lower / 2, -HALF, x1 - x0, lower, 0.5, (0, 0, -1))
    for c in range(4):
        panel('Panel', -HALF + 5 + c * 10, FLOOR + lower + hgt / 4, -HALF, 10, hgt / 2, 0.5, (0, 0, -1))
    for (cx, cz) in ((-10, -10), (10, -10), (-10, 10), (10, 10)):
        panel('Ceiling', cx, TOP, cz, 20, 0.5, 20, (cx / 10 * 0.4, 1, cz / 10 * 0.4))
    # frame beams
    def beam(cx, cy, cz, sx, sy, sz, outward):
        b = part('Beam', CFrame(W(cx, cy, cz)), (sx, sy, sz), BEAM, 'Metal', shadow=False)
        b.attr(Outward=attr_vec3(*outward))
        box.add(b)
    for sx in (-1, 1):
        for sz in (-1, 1):
            beam(sx * HALF, FLOOR + hgt / 2, sz * HALF, 0.8, hgt, 0.8, (sx, 0, sz))
    for s in (-1, 1):
        beam(0, TOP, s * HALF, 2 * HALF + 0.8, 0.8, 0.8, (0, 1, s))
        beam(s * HALF, TOP, 0, 0.8, 0.8, 2 * HALF + 0.8, (s, 1, 0))
        beam(0, FLOOR + hgt / 2, s * HALF, 2 * HALF, 0.4, 0.6, (0, 0, s))
        beam(s * HALF, FLOOR + hgt / 2, 0, 0.6, 0.4, 2 * HALF, (s, 0, 0))
    kitf.add(box)

    # the door: frame + hinged panel (hinge on the west side), unlocked the whole time
    door = Inst('Model', 'Door').attr(Hinge=attr_vec3(*W(-DOOR_W / 2, FLOOR, -HALF)))
    for sx in (-1, 1):
        door.add(part('FramePost', CFrame(W(sx * (DOOR_W / 2 + 0.3), FLOOR + DOOR_H / 2, -HALF)), (0.6, DOOR_H, 0.8),
                      BEAM, 'Metal', shadow=False))
    door.add(part('FrameHead', CFrame(W(0, FLOOR + DOOR_H + 0.3, -HALF)), (DOOR_W + 1.2, 0.6, 0.8), BEAM, 'Metal',
                  shadow=False))
    glow = deco('DoorGlow', CFrame(W(0, FLOOR + DOOR_H + 0.75, -HALF - 0.3)), (DOOR_W + 1.2, 0.3, 0.2), col, 'Neon',
                transparency=1)
    glow.add(point_light(col, 22, 2.5, enabled=False, name='Light'))
    door.add(glow)
    for sx in (-1, 1):
        door.add(deco('DoorGlowSide', CFrame(W(sx * (DOOR_W / 2 + 0.75), FLOOR + DOOR_H / 2, -HALF - 0.3)),
                      (0.3, DOOR_H + 1.2, 0.2), col, 'Neon', transparency=1))
    leaf = part('DoorLeaf', CFrame(W(0, FLOOR + DOOR_H / 2, -HALF)), (DOOR_W, DOOR_H, 0.35), (230, 240, 250), 'Glass',
                transparency=0.3, reflect=0.05, shadow=False)
    leaf.add(prompt('door', 'Open', 'Door', dist=9))
    leaf.add(surface_gui('Knob', 20, kit.frame('Handle', size=U2(0.06, 0, 0.12, 0), pos=U2(0.86, 0, 0.46, 0),
                                               color=(200, 170, 110), z=2)))
    door.add(leaf)
    kitf.add(door)

    # word blocks, placed at their resting spots (the client drops them in)
    blocks = Inst('Folder', 'Blocks')
    for i, (word, (bx, bz, ry)) in enumerate(zip(ctx.story['glassWords'], BLOCK_SPOTS), start=1):
        length = max(7.0, len(word) * 0.95 + 2.2)
        blk = part(f'Block{i}', CFrame(W(bx, FLOOR + 1.6, bz)) * CFrame.new(0, 0, 0, 0, ry, 0), (length, 3.2, 3.2),
                   (64, 66, 84), 'Slate')
        blk.attr(Index=i, Word=word)
        pp = prompt('letgo', 'Let it go', word, hold=0.8, dist=10, Index=i)
        pp.set(Enabled=('bool', False))
        blk.add(pp)
        for face in (5, 2, 1):
            blk.add(surface_gui(f'Word{face}', 26,
                label('Text', word, color=(236, 238, 248), family=kit.FAMILY['Antique'], size=U2(0.92, 0, 0.8, 0),
                      pos=U2(0.04, 0, 0.1, 0), stroke=0.5, stroke_color=(150, 60, 80), max_size=80),
                face=face, brightness=1.0, light_influence=0.4))
        blocks.add(blk)
    kitf.add(blocks)

    water = part('Water', CFrame(W(0, FLOOR + 0.005, 0)), (2 * HALF - 0.6, 0.01, 2 * HALF - 0.6), (70, 150, 205),
                 'Glass', collide=False, touch=False, query=False, shadow=False, transparency=0.5, reflect=0.08)
    kitf.add(water)
    return z, kitf
