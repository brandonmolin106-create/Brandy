"""4. The Road: a long road at dusk toward a colossal wall that blocks the horizon. As the player
walks closer, the wall shrinks (scaled by distance on the client) until it is a small rock you
can step over. road_3 lands right as it starts to shrink.

The wall is in the kit, built around a pivot at its base centre; the client scales every part
about that pivot. The corridor is fenced by invisible walls so the wall can't be walked around.
"""
import math
import random

from .rbx import Inst, S, B, F, V3, U2, CFrame, look_at, attr_vec3
from . import kit
from .kit import (part, deco, disc, pillar, ball, label, surface_gui, billboard, prompt, point_light, particles,
                  one_color, speech_stone, insight_pedestal, return_portal, checkpoint, video_screen,
                  screen_console, spot_light)
from .zone_time import marker

ORIGIN = (0.0, 0.0, -2400.0)
ROAD_W = 24.0
WALL_Z = -600.0          # relative to ORIGIN
ROAD_END = -660.0
SHRINK_START = 260.0     # distance (studs) from the wall where the big shrink begins
SHRINK_END = 36.0        # distance where it has become the rock

ASPHALT = (54, 52, 58)
DIRT = (150, 112, 82)
FIELD = (120, 104, 70)
WALL_STONE = (70, 64, 72)

def W(x, y, z):
    return (ORIGIN[0] + x, ORIGIN[1] + y, ORIGIN[2] + z)

def build(ctx):
    rnd = random.Random(44)
    z = Inst('Model', 'road').attr(Zone='road')
    kitf = Inst('Folder', 'road').attr(Zone='road', WallZ=ORIGIN[2] + WALL_Z, ShrinkStart=SHRINK_START,
                                       ShrinkEnd=SHRINK_END)
    col = ctx.rgb('road')

    # ---------------------------------------------------------------- fields and the road
    length = -ROAD_END + 80
    zc = (ROAD_END - 60 + 20) / 2
    z.add(part('FieldWest', CFrame(W(-170, -2, zc)), (316, 4, length + 60), FIELD, 'Grass'))
    z.add(part('FieldEast', CFrame(W(170, -2, zc)), (316, 4, length + 60), FIELD, 'Grass'))
    z.add(part('Shoulders', CFrame(W(0, -1.95, zc)), (ROAD_W + 12, 4, length + 60), DIRT, 'Ground', shadow=False))
    seg = 80.0
    zz = 20.0
    while zz > ROAD_END:
        z.add(part('Road', CFrame(W(0, 0.1, zz - seg / 2)), (ROAD_W, 0.3, seg), ASPHALT, 'Asphalt', shadow=False))
        zz -= seg
    for sx in (-1, 1):
        z.add(deco('EdgeLine', CFrame(W(sx * (ROAD_W / 2 - 1), 0.27, (20 + ROAD_END) / 2)), (0.4, 0.05, 20 - ROAD_END),
                   (230, 224, 206), 'SmoothPlastic'))
    dz = 10.0
    while dz > ROAD_END + 6:
        z.add(deco('Dash', CFrame(W(0, 0.27, dz)), (0.45, 0.05, 6), (240, 200, 110), 'SmoothPlastic'))
        dz -= 16.0
    z.add(*checkpoint('road', 0, W(0, 0.3, 0), (10, 0.2, 10), color=ASPHALT, material='Asphalt', glow=col))
    z.add(*checkpoint('road', 1, W(0, 0.3, -300), (10, 0.2, 10), color=ASPHALT, material='Asphalt', glow=col))

    # street lamps (warm) on alternate sides
    lz, side = -30.0, 1
    while lz > ROAD_END + 20:
        x = side * (ROAD_W / 2 + 3)
        z.add(pillar('LampPost', W(x, 0, lz), 0.6, 14, (40, 40, 46), 'Metal'))
        z.add(part('LampArm', CFrame(W(x - side * 2, 14, lz)), (4.4, 0.4, 0.4), (40, 40, 46), 'Metal', shadow=False))
        head = deco('LampHead', CFrame(W(x - side * 3.8, 13.6, lz)), (1.4, 0.5, 1.0), (255, 206, 140), 'Neon')
        head.add(spot_light((255, 196, 130), 38, 1.8, angle=80, face=4))
        z.add(head)
        lz -= 64.0
        side = -side

    # telephone poles with sagging wires on the east field
    prev = None
    for i in range(12):
        pz = -20 - i * 55
        z.add(pillar('Pole', W(34, 0, pz), 0.9, 20, (80, 62, 48), 'Wood'))
        z.add(part('CrossArm', CFrame(W(34, 18.6, pz)), (6, 0.5, 0.5), (80, 62, 48), 'Wood', shadow=False))
        if prev is not None:
            for wx in (-2.4, 2.4):
                a, b = W(34 + wx, 18.9, prev), W(34 + wx, 18.9, pz)
                mid = ((a[0] + b[0]) / 2, a[1] - 1.2, (a[2] + b[2]) / 2)
                z.add(deco('Wire', look_at(mid, b), (0.12, 0.12, 55), (30, 30, 34), 'SmoothPlastic'))
        prev = pz

    # distant mesas and hills on both sides (silhouettes against the dusk)
    for i in range(14):
        sx = -1 if i % 2 == 0 else 1
        x = sx * rnd.uniform(230, 420)
        pz = rnd.uniform(ROAD_END - 200, 100)
        h = rnd.uniform(40, 110)
        w = rnd.uniform(70, 160)
        z.add(part('Mesa', CFrame(W(x, h / 2 - 2, pz)) * CFrame.new(0, 0, 0, 0, rnd.uniform(0, 90), 0), (w, h, w * 0.8),
                   (112, 72, 70), 'Sandstone', collide=False, touch=False, query=False, shadow=False))
    for i in range(18):
        x = rnd.choice((-1, 1)) * rnd.uniform(40, 150)
        pz = rnd.uniform(ROAD_END, 0)
        s = rnd.uniform(3, 8)
        z.add(kit.rock('Rock', W(x, s * 0.25, pz), (s * 1.5, s, s * 1.2), rnd, color=(118, 96, 84), material='Sandstone'))
    for i in range(22):
        x = rnd.choice((-1, 1)) * rnd.uniform(22, 140)
        pz = rnd.uniform(ROAD_END + 20, 0)
        z.add(kit.tree('Tree', W(x, 0, pz), rnd, trunk_col=(70, 50, 40), leaf_cols=((96, 92, 60), (110, 96, 58)),
                       scale=rnd.uniform(0.8, 1.2)))

    # invisible corridor fences so the wall can't be walked around
    for sx in (-1, 1):
        z.add(part('Fence', CFrame(W(sx * 150, 30, zc)), (2, 60, length + 60), (0, 0, 0), transparency=1,
                   shadow=False, touch=False, query=False))
    z.add(part('Fence', CFrame(W(0, 30, 50)), (300, 60, 2), (0, 0, 0), transparency=1, shadow=False, touch=False,
               query=False))
    z.add(part('Fence', CFrame(W(0, 30, ROAD_END - 70)), (300, 60, 2), (0, 0, 0), transparency=1, shadow=False,
               touch=False, query=False))

    # milestones (speech stones) and the lookout beyond the wall
    z.add(speech_stone('SpeechStone', W(-17, 0, -26), W(0, 0, 0), 'road_1', ctx.excerpt('road_1'), accent=col))
    z.add(speech_stone('SpeechStone', W(17, 0, -250), W(0, 0, -200), 'road_2', ctx.excerpt('road_2'), accent=col))
    z.add(speech_stone('SpeechStone', W(-17, 0, WALL_Z - 30), W(0, 0, WALL_Z), 'road_3', ctx.excerpt('road_3'),
                       accent=col))
    z.add(insight_pedestal('road', W(0, 0.25, WALL_Z - 44), ctx.zone('road')['name'], col))
    z.add(return_portal(W(16, 0, WALL_Z - 50), W(0, 0, WALL_Z - 40), color=col))
    z.add(part('Bench', CFrame(W(-10, 1, WALL_Z - 52)), (6, 0.5, 2), (110, 80, 56), 'WoodPlanks', cls='Seat'))
    screen, _ = video_screen('road', W(-30, 14, 26), W(0, 14, -10), 22, frame_color=(62, 56, 60), accent=col,
                             subtitle=ctx.theme('road'))
    z.add(screen, screen_console('road', W(-20, 0, 14), W(0, 0, -10), accent=col))

    # beats: road_1 at the start, road_2 midway (road_3 is triggered by the shrink itself)
    marker(kitf, 'road_1', W(0, 3, -6), 14)
    marker(kitf, 'road_2', W(0, 3, -200), 30)

    # ---------------------------------------------------------------- the colossal wall (kit)
    wall = Inst('Model', 'Wall').attr(Pivot=attr_vec3(*W(0, 0, WALL_Z)))
    wz = WALL_Z
    wall.add(part('Face', CFrame(W(0, 150, wz)), (720, 300, 30), WALL_STONE, 'Slate', collide=False, touch=False,
                  query=False, shadow=True))
    wall.add(part('Crown', CFrame(W(0, 303, wz)), (730, 8, 36), (58, 52, 60), 'Slate', collide=False, touch=False,
                  query=False, shadow=False))
    for i in range(9):
        bx = -320 + i * 80
        wall.add(part('Buttress', CFrame(W(bx, 130, wz + 20)), (26, 260, 14), (62, 56, 64), 'Slate', collide=False,
                      touch=False, query=False, shadow=False))
    for i in range(6):
        wall.add(deco('Course', CFrame(W(0, 40 + i * 44, wz + 15.2)), (720, 1.4, 0.6), (48, 44, 52), 'Slate'))
    for (cx, cy, h, rz) in ((-60, 120, 90, 12), (40, 190, 70, -18), (130, 90, 60, 6)):
        wall.add(deco('Crack', CFrame(W(cx, cy, wz + 15.4)) * CFrame.new(0, 0, 0, 0, 0, rz), (1.2, h, 0.4),
                      (30, 26, 34), 'Slate'))
    kitf.add(wall)
    rock = ball('Rock', W(0, -0.2, WALL_Z), 3.6, (104, 98, 108), 'Slate', shadow=False)
    rock.set(Transparency=('float', 1.0), CanCollide=('bool', False))
    kitf.add(rock)
    return z, kitf
