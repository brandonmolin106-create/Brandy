"""2. The Hole: a deep pit carved with negative self-talk. Seven Better Thought orbs appear one
at a time; each one collected raises the next flight of stone steps out of the wall, so the
player climbs out on better thoughts.

Steps spiral up the wall (radius 13.5-20), 2 studs per step, 6 steps per flight (the 6th is a
wider landing where the next orb waits). Floor at -86, last landing at -2, rim at 0.
The steps live in the kit at their RISEN positions; the client retracts them into the wall
and slides each flight out when the server confirms an orb.
"""
import math
import random

from .rbx import Inst, S, B, F, V3, U2, CFrame, look_at, attr_vec3
from . import kit
from .kit import (part, deco, disc, pillar, ball, label, surface_gui, billboard, prompt, point_light, particles,
                  one_color, speech_stone, insight_pedestal, return_portal, checkpoint, video_screen,
                  screen_console, path_attrs, spot_light)
from .zone_time import marker

ORIGIN = (0.0, 0.0, 2400.0)
R_IN, WALL_T = 20.0, 12.0
FLOOR_Y = -86.0
STEP_R0, STEP_R1 = 13.5, 21.0          # radial extent (the outer 1 stud is inside the wall)
STEP_W, LAND_W, STEP_T = 6.0, 10.0, 2.0
PITCH, LAND_PITCH = 28.0, 34.6
FLIGHTS, STEPS = 7, 6
THETA0 = 200.0                          # angle of the first step (degrees from +Z toward +X)
RETRACT = 8.0

WALL = (54, 50, 62)
WALL_DARK = (40, 37, 48)
NIGHT_GRASS = (40, 58, 52)

def W(x, y, z):
    return (ORIGIN[0] + x, ORIGIN[1] + y, ORIGIN[2] + z)

def polar(r, deg, y):
    a = math.radians(deg)
    return W(r * math.sin(a), y, r * math.cos(a))

def step_layout():
    """[(flight, step, angle_deg, top_y, width)]"""
    out = []
    ang = THETA0
    for f in range(1, FLIGHTS + 1):
        for s in range(1, STEPS + 1):
            if f == 1 and s == 1:
                pass
            elif s == 1:
                ang += LAND_PITCH               # leaving the previous landing
            elif s == STEPS:
                ang += LAND_PITCH               # into the landing
            else:
                ang += PITCH
            top = FLOOR_Y + 12 * (f - 1) + 2 * s
            out.append((f, s, ang, top, LAND_W if s == STEPS else STEP_W))
    return out

def build(ctx):
    rnd = random.Random(7)
    z = Inst('Model', 'hole').attr(Zone='hole')
    kitf = Inst('Folder', 'hole').attr(Zone='hole', PitCenter=attr_vec3(*W(0, 0, 0)), Retract=RETRACT,
                                       FloorY=FLOOR_Y + ORIGIN[1])
    col = ctx.rgb('hole')
    layout = step_layout()
    last_angle = layout[-1][2]

    # ---------------------------------------------------------------- ground around the opening
    for (cx, cz, sx, sz) in ((0, 90, 320, 140), (0, -90, 320, 140), (90, 0, 140, 40), (-90, 0, 140, 40)):
        z.add(part('Ground', CFrame(W(cx, -2, cz)), (sx, 4, sz), NIGHT_GRASS, 'Grass'))
    z.add(disc('Floor', W(0, FLOOR_Y, 0), 46, 4, (46, 40, 44), 'Mud'))

    # ---------------------------------------------------------------- the shaft (12 wall segments)
    carvings = ctx.story['holeCarvings']
    side = 2 * (R_IN + WALL_T) * math.tan(math.radians(15)) + 0.2
    height = -FLOOR_Y + 2 - 0.05          # tops sit just under the ground (no z-fighting)
    for i in range(12):
        ang = i * 30 + 15
        r = R_IN + WALL_T / 2
        cxyz = polar(r, ang, FLOOR_Y - 2 + height / 2)
        cf = look_at(cxyz, W(0, FLOOR_Y - 2 + height / 2, 0))
        seg = part('Wall', cf, (side, height, WALL_T), WALL if i % 2 == 0 else WALL_DARK, 'Slate')
        if i % 3 != 2:
            labels = []
            for j in range(3):
                txt = carvings[(i + j * 5) % len(carvings)]
                yscale = 0.12 + j * 0.26 + rnd.uniform(-0.04, 0.05)
                world_h = FLOOR_Y - 2 + height * (1 - yscale) - height * 0.03
                lb = label(f'Carving{j + 1}', txt, color=(24, 22, 32), family=kit.FAMILY['Antique'],
                           size=U2(0.52, 0, 0.055, 0), pos=U2(0.24 + rnd.uniform(-0.03, 0.03), 0, yscale, 0),
                           stroke=0.35, stroke_color=(150, 120, 160), max_size=120, z=2)
                lb.set(Rotation=('float', rnd.uniform(-7, 7)))
                lb.attr(Height=world_h)
                labels.append(lb)
            seg.add(surface_gui('Carvings', 12, *labels, brightness=0.9, light_influence=0.6))
        z.add(seg)
    # a faint rim so the opening reads against the sky
    z.add(deco('RimGlow', CFrame(W(0, 0.06, 0), None) * CFrame.new(0, 0, 0, 0, 0, 90), (0.1, 44, 44),
               (150, 170, 255), 'Neon', shape=kit.CYL, transparency=0.85))

    # ---------------------------------------------------------------- pit floor
    z.add(*checkpoint('hole', 0, W(0, FLOOR_Y + 0.3, 0), (9, 0.6, 9), shape='disc', color=(60, 56, 68),
                      material='Slate', glow=col, ry=THETA0 + 180))
    for i in range(10):
        a = rnd.uniform(0, 360)
        r = rnd.uniform(9, 16)
        d = rnd.uniform(4, 8)
        z.add(ball('DirtPile', polar(r, a, FLOOR_Y - d * 0.3), d, (58, 44, 38), 'Mud', collide=False, touch=False,
                   query=False, shadow=False))
    z.add(speech_stone('SpeechStone', polar(12, THETA0 - 60, FLOOR_Y), W(0, FLOOR_Y, 0), 'hole_1',
                       ctx.excerpt('hole_1'), accent=col))
    fog = part('PitFog', CFrame(W(0, FLOOR_Y + 6, 0)), (36, 10, 36), (0, 0, 0), transparency=1, collide=False,
               touch=False, query=False, shadow=False)
    fog.add(particles('Mist', one_color((90, 80, 120)), rate=6, life=(6, 9), speed=(0.2, 0.6), light=0,
                      size=((0, 4, 0), (1, 7, 0)), transparency=((0, 1, 0), (0.3, 0.86, 0), (1, 1, 0)), shape=0))
    z.add(fog)

    # ---------------------------------------------------------------- flights of steps (kit)
    flights = Inst('Folder', 'Flights')
    order = 1
    floor_node = part('FloorNode', CFrame(W(0, FLOOR_Y - 0.5, 0)), (30, 1, 30), (0, 0, 0), transparency=1,
                      collide=False, touch=False, query=False, shadow=False)
    path_attrs(floor_node, 'hole', order, 'box')   # the floor, for the jump checker only
    kitf.add(floor_node)
    fl = None
    for (f, s, ang, top, width) in layout:
        if s == 1:
            fl = Inst('Folder', f'Flight{f}').attr(Index=f)
            flights.add(fl)
        rmid = (STEP_R0 + STEP_R1) / 2
        pos = polar(rmid, ang, top - STEP_T / 2)
        cf = look_at(pos, W(0, top - STEP_T / 2, 0))      # front (-Z) faces the pit centre
        st = part(f'Step{s}', cf, (width, STEP_T, STEP_R1 - STEP_R0), (104, 100, 112) if s < STEPS else (120, 116, 128),
                  'Slate')
        st.attr(Index=s)
        order += 1
        path_attrs(st, 'hole', order, 'box')
        fl.add(st)
        if s == STEPS:
            fl.add(deco('LandingGlow', cf * CFrame.new(0, STEP_T / 2 + 0.02, 0, 0, 0, 0), (width - 2, 0.05, 0.3),
                        col, 'Neon', transparency=0.4))
    kitf.add(flights)
    rim_node = part('RimNode', CFrame(polar(26, last_angle, -0.5)), (12, 1, 12), (0, 0, 0), transparency=1,
                    collide=False, touch=False, query=False, shadow=False)
    order += 1
    path_attrs(rim_node, 'hole', order, 'box')         # the wall top / ground at the exit, for the checker
    kitf.add(rim_node)

    # ---------------------------------------------------------------- Better Thought orbs (kit)
    orbs = Inst('Folder', 'Orbs')
    thoughts = ctx.story['betterThoughts']
    landing_angles = [ang for (f, s, ang, top, w) in layout if s == STEPS]
    landing_tops = [top for (f, s, ang, top, w) in layout if s == STEPS]
    for k in range(1, FLIGHTS + 1):
        if k == 1:
            pos = polar(7, THETA0 - 10, FLOOR_Y + 3.6)
        else:
            pos = polar((STEP_R0 + R_IN) / 2 - 0.5, landing_angles[k - 2], landing_tops[k - 2] + 3.4)
        om = Inst('Model', f'Orb{k}').attr(Index=k, Phrase=thoughts[(k - 1) % len(thoughts)])
        core = part('Core', CFrame(pos), (2.2, 2.2, 2.2), (255, 236, 180), 'Neon', shape=kit.BALL, collide=False,
                    touch=False, query=False, shadow=False)
        core.add(point_light((255, 226, 160), 18, 2.2))
        core.add(particles('Sparkle', ((0, (255, 240, 200)), (1, col)), rate=8, life=(1, 2), speed=(0.5, 1.5),
                           size=((0, 0.25, 0), (1, 0, 0))))
        core.add(billboard('Label', 9, 2.2, 3.0, 90,
            label('Phrase', thoughts[(k - 1) % len(thoughts)], color=(255, 244, 214), family=kit.TITLE_FONT,
                  stroke=0.4, stroke_color=(120, 90, 30), max_size=64), always_on_top=False))
        halo = deco('Halo', CFrame(pos), (3.6, 3.6, 3.6), (255, 220, 150), 'Neon', shape=kit.BALL, transparency=0.78)
        om.add(core, halo)
        orbs.add(om)
    kitf.add(orbs)

    # ---------------------------------------------------------------- light shaft (kit, grows as you climb)
    shaft = deco('LightShaft', CFrame(W(0, (FLOOR_Y + 6) / 2, 0), None) * CFrame.new(0, 0, 0, 0, 0, 90),
                 (-FLOOR_Y + 6, 15, 15), (200, 216, 255), 'Neon', shape=kit.CYL, transparency=1)
    kitf.add(shaft)
    lamp = part('SkyLight', CFrame(W(0, 6, 0)), (1, 1, 1), (0, 0, 0), transparency=1, collide=False, touch=False,
                query=False, shadow=False)
    lamp.add(spot_light((200, 214, 255), 110, 0, angle=34, face=4, name='Spot'))
    lamp.add(particles('Dust', one_color((220, 230, 255)), rate=0, life=(8, 12), speed=(1, 2), emission_dir=4,
                       spread=(10, 10), light=0.6, size=((0, 0.12, 0), (1, 0.12, 0)),
                       transparency=((0, 1, 0), (0.2, 0.3, 0), (1, 1, 0))))
    kitf.add(lamp)
    marker(kitf, 'hole_move', polar(25, last_angle, 1.5), 8)

    # ---------------------------------------------------------------- the rim: moonlit meadow
    ins = polar(46, last_angle, 0)
    z.add(insight_pedestal('hole', ins, ctx.zone('hole')['name'], col))
    for j, (lid, da) in enumerate((('hole_2', -34), ('hole_3', -17), ('hole_4', 17), ('hole_move', 34))):
        z.add(speech_stone('SpeechStone', polar(56, last_angle + da, 0), ins, lid, ctx.excerpt(lid), accent=col))
    z.add(return_portal(polar(62, last_angle + 62, 0), ins, color=col))
    screen, _ = video_screen('hole', polar(80, last_angle - 55, 14), ins, 22, accent=col, subtitle=ctx.theme('hole'))
    z.add(screen, screen_console('hole', polar(70, last_angle - 50, 0), ins, accent=col))
    z.add(*checkpoint('hole', 8, polar(36, last_angle, 0.1), (8, 0.2, 8), color=(58, 70, 66), material='Slate',
                      glow=col, ry=0))
    for i in range(26):
        a = rnd.uniform(0, 360)
        r = rnd.uniform(48, 150)
        x, y, zz = polar(r, a, 0)
        near = abs(((a - last_angle + 180) % 360) - 180) < 45 and r < 95
        if near:
            continue
        if rnd.random() < 0.5:
            z.add(kit.pine('Pine', (x, 0, zz), rnd, scale=rnd.uniform(1.0, 1.6), col=(28, 52, 48)))
        else:
            s = rnd.uniform(2, 5)
            z.add(kit.rock('Rock', (x, s * 0.3, zz), (s * 1.5, s, s * 1.2), rnd, color=(70, 72, 84)))
    for i in range(3):
        ff = part('Fireflies', CFrame(polar(60 + i * 25, last_angle + i * 50 - 50, 5)), (50, 8, 50), (0, 0, 0),
                  transparency=1, collide=False, touch=False, query=False, shadow=False)
        ff.add(particles('Glow', ((0, (210, 255, 150)), (1, (150, 255, 200))), rate=4, life=(4, 7), speed=(0.3, 1),
                         size=((0, 0, 0), (0.2, 0.22, 0), (0.8, 0.22, 0), (1, 0, 0)),
                         transparency=((0, 1, 0), (0.2, 0.1, 0), (0.8, 0.1, 0), (1, 1, 0)), shape=0))
        z.add(ff)
    for i in range(16):
        a = 360 * i / 16
        z.add(part('Boundary', look_at(polar(158, a, 25), W(0, 25, 0)), (64, 50, 2), (0, 0, 0), transparency=1,
                   shadow=False, touch=False, query=False))
    return z, kitf
