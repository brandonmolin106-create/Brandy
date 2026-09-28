"""6. The Summit: a peak above the clouds at sunrise over an endless ocean, with the monument
NOTHING BECOMES EVERYTHING, a screen for Brandon's video, and the finale (music, confetti, a
sunrise lighting shift, credits, then a portal home).
"""
import math
import random

from .rbx import Inst, S, B, F, V3, U2, CFrame, look_at, attr_vec3
from . import kit
from .kit import (part, deco, disc, pillar, ball, wedge, label, surface_gui, billboard, prompt, point_light,
                  particles, one_color, speech_stone, insight_pedestal, return_portal, checkpoint, video_screen,
                  screen_console, frame)
from .zone_time import marker

ORIGIN = (-3000.0, 0.0, 3000.0)
TOP = 260.0
HALF = 32.0

OCEAN = (40, 92, 140)
ROCK = (110, 100, 104)
ROCK_WARM = (138, 116, 108)
TERRACE = (226, 214, 198)

def W(x, y, z):
    return (ORIGIN[0] + x, ORIGIN[1] + y, ORIGIN[2] + z)

def build(ctx):
    rnd = random.Random(66)
    z = Inst('Model', 'everything').attr(Zone='everything')
    kitf = Inst('Folder', 'everything').attr(Zone='everything')
    col = ctx.rgb('everything')

    # ---------------------------------------------------------------- ocean and the mountain
    z.add(part('Ocean', CFrame(W(0, -2, 0)), (3000, 4, 3000), OCEAN, 'SmoothPlastic', reflect=0.35, shadow=False,
               touch=False, query=False))
    tiers = ((0, 60, 420, 13), (50, 120, 300, 10), (110, 180, 200, 8), (170, 236, 120, 7), (220, TOP - 6, 76, 5))
    for (y0, y1, w, n) in tiers:
        for i in range(n):
            a = 360 * i / n + rnd.uniform(-10, 10)
            r = w * rnd.uniform(0.18, 0.32)
            s = w * rnd.uniform(0.45, 0.62)
            h = (y1 - y0) * rnd.uniform(1.0, 1.25)
            x, zz = r * math.sin(math.radians(a)), r * math.cos(math.radians(a))
            z.add(part('Crag', CFrame(W(x, y0 + h / 2 - 2, zz)) * CFrame.new(0, 0, 0, rnd.uniform(-5, 5), rnd.uniform(0, 90),
                                                                             rnd.uniform(-5, 5)),
                       (s, h, s * rnd.uniform(0.8, 1.1)), ROCK if i % 2 else ROCK_WARM, 'Slate', shadow=False,
                       touch=False, query=False))
    # cloud sea below the summit
    for i in range(54):
        a = rnd.uniform(0, 360)
        r = rnd.uniform(90, 640)
        d = rnd.uniform(40, 110)
        y = rnd.uniform(170, 205)
        z.add(ball('Cloud', W(r * math.sin(math.radians(a)), y, r * math.cos(math.radians(a))), d, (255, 238, 228),
                   'SmoothPlastic', collide=False, touch=False, query=False, shadow=False, transparency=0.18))

    # ---------------------------------------------------------------- the terrace
    z.add(part('Terrace', CFrame(W(0, TOP - 1.5, 0)), (2 * HALF, 3, 2 * HALF), TERRACE, 'Marble'))
    z.add(part('TerraceRim', CFrame(W(0, TOP - 3.4, 0)), (2 * HALF + 3, 1.2, 2 * HALF + 3), (190, 176, 160), 'Marble',
               shadow=False))
    for s in (-1, 1):
        z.add(part('Balustrade', CFrame(W(0, TOP + 0.9, s * (HALF - 0.6))), (2 * HALF, 1.8, 1.2), TERRACE, 'Marble'))
        z.add(part('Balustrade', CFrame(W(s * (HALF - 0.6), TOP + 0.9, 0)), (1.2, 1.8, 2 * HALF), TERRACE, 'Marble'))
    for i in range(9):
        t = -HALF + 0.6 + i * (2 * HALF - 1.2) / 8
        for (x, zz) in ((t, -HALF + 0.6), (t, HALF - 0.6), (-HALF + 0.6, t), (HALF - 0.6, t)):
            z.add(pillar('Post', W(x, TOP, zz), 1.6, 2.6, (238, 228, 214), 'Marble', shadow=False, collide=False,
                         touch=False, query=False))
    z.add(*checkpoint('everything', 0, W(0, TOP + 0.05, 22), (9, 0.2, 9), color=TERRACE, material='Marble',
                      glow=col, ry=0))
    # invisible safety walls above the balustrade (nobody tumbles into the clouds)
    for s in (-1, 1):
        z.add(part('SafetyWall', CFrame(W(0, TOP + 8, s * HALF)), (2 * HALF, 14, 1), (0, 0, 0), transparency=1,
                   shadow=False, touch=False, query=False))
        z.add(part('SafetyWall', CFrame(W(s * HALF, TOP + 8, 0)), (1, 14, 2 * HALF), (0, 0, 0), transparency=1,
                   shadow=False, touch=False, query=False))

    # ---------------------------------------------------------------- the monument
    mz = -14.0
    z.add(part('MonumentBase', CFrame(W(0, TOP + 1.5, mz)), (14, 3, 7), (236, 230, 220), 'Marble'))
    stele = part('Monument', CFrame(W(0, TOP + 14, mz)), (10, 22, 2.6), (244, 240, 232), 'Marble')
    words = ctx.story['monument']
    for face in (5, 2):
        stele.add(surface_gui(f'Words{face}', 30,
            label('Line1', words[0], color=kit.GOLD, family=kit.TITLE_FONT, size=U2(0.9, 0, 0.14, 0),
                  pos=U2(0.05, 0, 0.12, 0), max_size=140, stroke=0.5, stroke_color=(120, 80, 30)),
            label('Line2', words[1], color=kit.GOLD, family=kit.TITLE_FONT, size=U2(0.9, 0, 0.14, 0),
                  pos=U2(0.05, 0, 0.3, 0), max_size=140, stroke=0.5, stroke_color=(120, 80, 30)),
            label('Line3', words[2], color=kit.GOLD, family=kit.TITLE_FONT, size=U2(0.94, 0, 0.16, 0),
                  pos=U2(0.03, 0, 0.47, 0), max_size=150, stroke=0.5, stroke_color=(120, 80, 30)),
            label('Byline', ctx.story['subtitle'], color=(150, 120, 80), family=kit.TITLE_FONT, style='Italic',
                  size=U2(0.6, 0, 0.06, 0), pos=U2(0.2, 0, 0.8, 0), max_size=60, stroke=1.0),
            face=face, brightness=1.4, light_influence=0.3))
    z.add(stele)
    crown = deco('MonumentCrown', CFrame(W(0, TOP + 25.3, mz)), (10.6, 0.6, 3.2), col, 'Neon')
    crown.add(point_light(col, 30, 1.6))
    z.add(crown)
    for sx in (-1, 1):
        brazier = deco('Brazier', CFrame(W(sx * 9, TOP + 3.4, mz + 2)), (1.4, 1.4, 1.4), (255, 190, 110), 'Neon',
                       shape=kit.BALL)
        brazier.add(Inst('Fire', 'Fire', size_xml=F(3), heat_xml=F(6), Color=('Color3', (1, 0.7, 0.35)),
                         SecondaryColor=('Color3', (1, 0.4, 0.2)), Enabled=B(True)))
        brazier.add(point_light((255, 190, 120), 20, 1.5))
        z.add(pillar('BrazierStand', W(sx * 9, TOP, mz + 2), 1.2, 2.8, (200, 190, 176), 'Marble', shadow=False))
        z.add(brazier)
    z.add(insight_pedestal('everything', W(0, TOP, -4), ctx.zone('everything')['name'], col))

    screen, _ = video_screen('everything', W(-27, TOP + 13, 2), W(0, TOP + 13, 2), 20, frame_color=(214, 202, 186),
                             accent=col, subtitle=ctx.theme('everything'))
    z.add(screen, screen_console('everything', W(-19, TOP, 6), W(0, TOP, 6), accent=col))
    z.add(speech_stone('SpeechStone', W(20, TOP, 14), W(0, TOP, 0), 'everything_1', ctx.excerpt('everything_1'),
                       accent=col))
    z.add(speech_stone('SpeechStone', W(20, TOP, -4), W(0, TOP, 0), 'everything_3', ctx.excerpt('everything_3'),
                       accent=col))
    marker(kitf, 'everything_1', W(0, TOP + 3, 20), 10)

    # ---------------------------------------------------------------- finale props (kit)
    home = Inst('Model', 'HomePortal').attr(Hidden=True)
    hcf = look_at(W(22, TOP, -20), W(0, TOP, 0))
    for sx in (-1, 1):
        home.add(part('Post', hcf * CFrame.new(sx * 4.2, 5, 0), (1.2, 10, 1.2), (236, 228, 214), 'Marble',
                      transparency=1, collide=False))
    home.add(part('Lintel', hcf * CFrame.new(0, 10.4, 0), (10, 1.2, 1.6), (236, 228, 214), 'Marble', transparency=1,
                  collide=False))
    gate = part('Gate', hcf * CFrame.new(0, 5, 0), (7, 9.4, 0.3), kit.CYAN, 'Neon', collide=False, touch=True,
                query=True, shadow=False, transparency=1)
    gate.attr(Action='return').tag('ReturnGate')
    pp = prompt('return', 'Go home', 'The Clearing', hold=0.2, dist=10)
    pp.set(Enabled=('bool', False))
    gate.add(pp)
    gate.add(particles('Swirl', one_color(kit.CYAN), rate=14, life=(1.5, 2.5), speed=(0.5, 1.5),
                       size=((0, 0.35, 0), (1, 0, 0)), enabled=False))
    gate.add(point_light(kit.CYAN, 18, 1.8, enabled=False))
    home.add(gate)
    kitf.add(home)
    confetti_cols = ((0, (255, 214, 140)), (0.25, (255, 150, 190)), (0.5, (120, 225, 240)), (0.75, (190, 160, 255)),
                     (1, (255, 255, 255)))
    for (x, zz) in ((-16, -8), (16, -8), (-16, 14), (16, 14), (0, 4)):
        c = part('Confetti', CFrame(W(x, TOP + 18, zz)), (6, 1, 6), (0, 0, 0), transparency=1, collide=False,
                 touch=False, query=False, shadow=False)
        c.add(particles('Burst', confetti_cols, rate=0, life=(3, 5), speed=(18, 30), spread=(40, 40),
                        emission_dir=1, accel=(0, -18, 0), drag=1.2, light=0.5, rot=(0, 360), rotspeed=(-240, 240),
                        size=((0, 0.35, 0), (1, 0.3, 0)), transparency=((0, 0, 0), (0.8, 0, 0), (1, 1, 0))))
        kitf.add(c)
    sun = part('SunGlow', CFrame(W(0, TOP + 40, -900)), (1, 1, 1), (0, 0, 0), transparency=1, collide=False,
               touch=False, query=False, shadow=False)
    kitf.add(sun)
    return z, kitf
