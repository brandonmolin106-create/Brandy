"""0. The Clearing: night meadow, campfire, glowing stones, cinema screen, journal, map, portals."""
import math
import random

from .rbx import Inst, S, B, I, F, V3, C3, U2, U, NS, CS, CFrame, look_at
from . import kit
from .kit import (part, deco, disc, pillar, ball, label, frame, surface_gui, billboard, prompt, point_light,
                  particles, one_color, speech_stone, video_screen, screen_console, corner, stroke, gradient)

ORIGIN = (0.0, 0.0, 0.0)
PORTAL_ANGLES = {'time': 40, 'hole': 80, 'glass': 120, 'road': 240, 'chains': 280, 'everything': 320}
PORTAL_RADIUS = 96.0
SPAWN_POS = (0.0, 0.0, 34.0)

GRASS = (58, 96, 70)
GRASS_IN = (64, 104, 76)
FOREST = (34, 58, 46)

def polar(r, deg, y=0.0):
    """North is -Z, angles go clockwise (toward +X) like a compass."""
    a = math.radians(deg)
    return (r * math.sin(a), y, -r * math.cos(a))

def build(ctx):
    rnd = random.Random(2026)
    z = Inst('Model', 'hub').attr(Zone='hub')
    center = (0.0, 0.0, 0.0)

    # ground layers
    z.add(disc('Ground', (0, 0, 0), 330, 6, GRASS, 'Grass'))
    z.add(disc('ForestFloor', (0, -0.3, 0), 600, 6, FOREST, 'LeafyGrass', shadow=False))
    z.add(disc('RingPath', (0, 0.06, 0), 66, 0.4, (126, 116, 102), 'Pebble', shadow=False))
    z.add(disc('InnerGrass', (0, 0.1, 0), 50, 0.4, GRASS_IN, 'Grass', shadow=False))

    # campfire
    fire = Inst('Model', 'Campfire')
    fire.add(disc('FirePit', (0, 0.16, 0), 9, 0.3, (46, 44, 50), 'Slate', shadow=False))
    for i in range(10):
        a = math.radians(i * 36 + rnd.uniform(-6, 6))
        s = rnd.uniform(1.3, 1.9)
        fire.add(kit.rock('PitStone', (3.7 * math.sin(a), 0.5, 3.7 * math.cos(a)), (s * 1.3, s, s), rnd,
                          color=(84, 84, 94)))
    embers = disc('Embers', (0, 0.4, 0), 4.6, 0.3, (255, 112, 40), 'Neon', collide=False, touch=False, query=False,
                  shadow=False, transparency=0.15)
    fire.add(embers)
    for i in range(3):
        fire.add(part('Log', CFrame.new(0, 1.3, 0, 0, i * 60, 62), (5.6, 1.1, 1.1), (98, 66, 44), 'Wood',
                      shape=kit.CYL, collide=False, touch=False, query=False))
    core = part('FireCore', CFrame.new(0, 1.6, 0), (2, 2, 2), (0, 0, 0), transparency=1, collide=False, touch=False,
                query=False, shadow=False)
    core.add(Inst('Fire', 'Fire', size_xml=F(6), heat_xml=F(11), Color=C3(255, 150, 64), SecondaryColor=C3(255, 70, 24),
                  Enabled=B(True)))
    core.add(point_light((255, 156, 86), 44, 2.4, shadows=True, name='FireLight'))
    core.add(particles('Embers', ((0, (255, 200, 120)), (1, (255, 90, 30))), rate=14, life=(1.8, 3.6),
                       speed=(3, 7), spread=(22, 22), accel=(0, 1.5, 0), size=((0, 0.18, 0), (1, 0, 0))))
    core.add(Inst('Smoke', 'Smoke', Color=C3(90, 90, 100), opacity_xml=F(0.06), riseVelocity_xml=F(3.5), size_xml=F(4),
                  Enabled=B(True)))
    core.tag('Flicker')
    fire.add(core)
    z.add(fire)

    # log benches around the fire (open to the north so the screen stays visible)
    for deg in (115, 150, 180, 210, 245):
        x, _, zz = polar(11.5, deg)
        cf = look_at((x, 0.8, zz), (0, 0.8, 0))
        seat = part('LogSeat', cf, (5.2, 1.6, 1.6), (104, 72, 50), 'Wood', shape=kit.CYL, cls='Seat')
        z.add(seat)

    # spawn (south), facing the fire and the screen (north)
    sp = part('SpawnLocation', CFrame.new(*SPAWN_POS), (10, 0.4, 10), (70, 76, 96), 'Slate', cls='SpawnLocation')
    sp.set(Neutral=B(True), Duration=I(0), Enabled=B(True), AllowTeamChangeOnTouch=B(False))
    sp.tag('Checkpoint').attr(Zone='hub', Index=0)
    z.add(sp, deco('SpawnRing', CFrame.new(SPAWN_POS[0], 0.24, SPAWN_POS[2], 0, 0, 90), (0.06, 8.6, 8.6),
                   kit.CYAN, 'Neon', shape=kit.CYL, transparency=0.55))

    # cinema screen (north), framed by two giant standing stones and a lintel
    scr_center = (0, 19, -68)
    screen, scf = video_screen('hub', scr_center, (0, 19, 0), 26, subtitle=ctx.theme('hub'))
    z.add(screen)
    for side in (-1, 1):
        z.add(part('ScreenStone', CFrame.new(side * 11.8, 17, -69.5, 0, 0, side * 1.5), (5.5, 34, 5), (66, 70, 86),
                   'Slate'))
        z.add(deco('ScreenRune', CFrame.new(side * 11.8, 18, -66.9), (0.6, 22, 0.25), kit.CYAN, 'Neon',
                   transparency=0.3))
    lintel = part('Lintel', CFrame.new(0, 35.8, -69.5), (31, 4, 6), (66, 70, 86), 'Slate')
    lintel.add(surface_gui('Title', 24, label('Text', 'NOTHING BECOMES EVERYTHING', color=kit.WHITE,
                                              family=kit.TITLE_FONT, max_size=72, stroke=0.6,
                                              stroke_color=(20, 40, 60)), face=2, brightness=1.3))
    z.add(lintel)
    z.add(part('ScreenPlaza', CFrame.new(0, 0.1, -58), (34, 0.3, 26), (120, 112, 100), 'Pebble', shadow=False))
    z.add(screen_console('hub', (0, 0.25, -50), (0, 0, 0)))

    # tall glowing stones between the portals
    for i, deg in enumerate((20, 60, 100, 140, 220, 260, 300, 340)):
        x, _, zz = polar(47, deg)
        h = rnd.uniform(14, 21)
        col = kit.CYAN if i % 2 == 0 else (170, 130, 255)
        cf = look_at((x, h / 2 - 0.5, zz), (0, h / 2 - 0.5, 0)) * CFrame.new(0, 0, 0, rnd.uniform(-3, 3), 0,
                                                                              rnd.uniform(-3, 3))
        st = part('GlowStone', cf, (4.6, h, 3.2), (70, 74, 90), 'Slate')
        z.add(st)
        rune = deco('Rune', cf * CFrame.new(0, 1.0, -1.65), (0.55, h * 0.62, 0.2), col, 'Neon', transparency=0.2)
        rune.add(point_light(col, 20, 1.3))
        z.add(rune)
        z.add(kit.rock('StoneBase', (x * 1.03, 0.4, zz * 1.03), (5, 1.4, 4), rnd, color=(60, 62, 74)))

    # portals
    for zone, deg in PORTAL_ANGLES.items():
        z.add(build_portal(ctx, zone, deg))
        # pebble path from the ring to the portal
        mid = polar((33 + PORTAL_RADIUS - 8) / 2, deg, 0.08)
        z.add(part('PortalPath', look_at(mid, (0, 0.08, 0)), (6, 0.3, PORTAL_RADIUS - 8 - 33), (116, 108, 96),
                   'Pebble', shadow=False))

    # journal pedestal (south-west of the fire)
    jx, _, jz = polar(19, 205)
    jm = Inst('Model', 'Journal')
    jm.add(pillar('Pedestal', (jx, 0, jz), 3.0, 3.4, (222, 218, 208), 'Marble'))
    bcf = look_at((jx, 3.9, jz), (0, 3.9, 0)) * CFrame.new(0, 0, 0, 28, 0, 0)
    book = part('Book', bcf, (3.4, 0.3, 2.4), (70, 40, 60), 'Fabric')
    book.add(prompt('journal', 'Read', 'Insight Journal', dist=10))
    jm.add(book)
    for side in (-1, 1):
        page = deco('Page', bcf * CFrame.new(side * 0.8, 0.22, 0, 0, 0, side * -6), (1.55, 0.1, 2.2),
                    (244, 236, 214), 'SmoothPlastic')
        jm.add(page)
    glow = deco('BookGlow', bcf * CFrame.new(0, 0.6, 0), (0.4, 0.4, 0.4), (255, 230, 170), 'Neon', transparency=1)
    glow.add(point_light((255, 226, 170), 12, 1.4))
    glow.add(particles('Motes', one_color((255, 236, 190)), rate=4, life=(2, 4), speed=(0.3, 0.8),
                       size=((0, 0.14, 0), (1, 0, 0)), accel=(0, 0.4, 0)))
    jm.add(glow)
    z.add(jm)

    # zone map on a stone tablet (south-east of the fire)
    mx, _, mz = polar(19, 155)
    tcf = look_at((mx, 6.4, mz), (0, 6.4, 0))
    tablet = part('MapTablet', tcf, (9.5, 11, 1.2), (74, 78, 94), 'Slate')
    tablet.tag('MapTablet')
    rows = []
    for i, zd in enumerate(ctx.zones):
        row = frame(f'Row_{zd["id"]}', size=U2(0.9, 0, 0.095, 0), pos=U2(0.05, 0, 0.2 + i * 0.107, 0),
                    color=(20, 22, 40), transparency=0.35, z=2)
        row.add(corner(0.3, 0))
        row.add(label('Numeral', zd.get('numeral', '') or '•', color=ctx.rgb(zd['id']), family=kit.TITLE_FONT,
                      size=U2(0.14, 0, 0.8, 0), pos=U2(0.02, 0, 0.1, 0), z=3, max_size=40))
        row.add(label('Name', zd['name'], color=kit.WHITE, family=kit.TITLE_FONT, size=U2(0.62, 0, 0.7, 0),
                      pos=U2(0.18, 0, 0.15, 0), xalign=0, z=3, max_size=40))
        row.add(label('Mark', '', color=kit.CYAN, family=kit.UI_FONT, weight=700, size=U2(0.18, 0, 0.6, 0),
                      pos=U2(0.8, 0, 0.2, 0), z=3, max_size=30))
        rows.append(row)
    tablet.add(surface_gui('Map', 40,
        label('Title', 'THE JOURNEY', color=kit.GOLD, family=kit.TITLE_FONT, size=U2(0.8, 0, 0.1, 0),
              pos=U2(0.1, 0, 0.05, 0), max_size=60, stroke=0.7),
        *rows, brightness=1.2))
    z.add(tablet, part('TabletBase', look_at((mx, 0.5, mz), (0, 0.5, 0)), (11, 1, 3), (58, 60, 72), 'Slate'))

    # tip jar lantern by the fire (removed by the server when Config has no product id)
    tx, _, tz = polar(13, 128)
    tip = Inst('Model', 'TipJar')
    tip.add(pillar('Stump', (tx, 0, tz), 2.4, 2.6, (100, 72, 50), 'Wood'))
    lantern = part('Lantern', CFrame.new(tx, 3.5, tz), (1.3, 1.8, 1.3), (230, 240, 255), 'Glass', transparency=0.45)
    lantern.add(prompt('tip', 'Tip Brandon', 'Campfire', dist=9))
    flame = deco('Flame', CFrame.new(tx, 3.45, tz), (0.6, 0.6, 0.6), (255, 200, 110), 'Neon', shape=kit.BALL)
    flame.add(point_light((255, 196, 120), 10, 1.2))
    tip.add(lantern, flame, deco('LanternCap', CFrame.new(tx, 4.5, tz), (1.5, 0.2, 1.5), kit.BRASS, 'Metal'))
    z.add(tip)

    # echo aura shrine (removed by the server when Config has no game pass id)
    ax, _, az = polar(13, 232)
    shrine = Inst('Model', 'AuraShrine')
    stone = part('Shrine', look_at((ax, 2, az), (0, 2, 0)), (2.4, 4, 2.4), (226, 222, 212), 'Marble')
    stone.add(prompt('aura', 'Echo Aura', 'Game pass', dist=9))
    orb = deco('Orb', CFrame.new(ax, 5, az), (1.2, 1.2, 1.2), kit.CYAN, 'Neon', shape=kit.BALL, transparency=0.1)
    orb.add(particles('Aura', ((0, kit.CYAN), (1, (170, 130, 255))), rate=12, life=(1.5, 3), speed=(0.5, 1.5),
                      size=((0, 0.3, 0), (1, 0, 0))))
    orb.add(point_light(kit.CYAN, 12, 1.2))
    shrine.add(stone, orb)
    z.add(shrine)

    # the welcome stone
    wx, _, wz = polar(24, 170)
    line = ctx.line('hub_welcome')
    z.add(speech_stone('SpeechStone', (wx, 0, wz), (0, 0, 0), 'hub_welcome', ctx.excerpt('hub_welcome')))

    # forest ring
    trees = Inst('Folder', 'Forest')
    for i in range(40):
        ang = rnd.uniform(0, 360)
        r = rnd.uniform(128, 250)
        x, _, zz = polar(r, ang)
        if rnd.random() < 0.55:
            trees.add(kit.pine('Pine', (x, 0, zz), rnd, scale=rnd.uniform(1.3, 2.1)))
        else:
            trees.add(kit.tree('Tree', (x, 0, zz), rnd, scale=rnd.uniform(1.1, 1.6)))
    for i in range(10):
        ang = rnd.uniform(0, 360)
        x, _, zz = polar(rnd.uniform(60, 125), ang)
        if all(abs(((ang - d + 180) % 360) - 180) > 12 for d in PORTAL_ANGLES.values()) and abs(ang) > 15:
            s = rnd.uniform(2.5, 5)
            trees.add(kit.rock('Boulder', (x, s * 0.25, zz), (s * 1.4, s, s * 1.2), rnd, color=(76, 80, 92)))
    z.add(trees)

    # glowing flowers
    flowers = Inst('Folder', 'Flowers')
    cols = [(120, 225, 240), (170, 140, 255), (255, 190, 240)]
    for i in range(44):
        ang = rnd.uniform(0, 360)
        r = rnd.uniform(28, 118)
        near_path = any(abs(((ang - d + 180) % 360) - 180) < 5 for d in PORTAL_ANGLES.values())
        if near_path or (r < 40 and abs(((ang - 180 + 180) % 360) - 180) < 20):
            continue
        x, _, zz = polar(r, ang)
        h = rnd.uniform(0.8, 1.6)
        flowers.add(deco('Stem', CFrame.new(x, h / 2, zz), (0.12, h, 0.12), (60, 110, 80), 'Grass'))
        bloom = deco('Bloom', CFrame.new(x, h + 0.15, zz), (0.5, 0.5, 0.5), cols[i % 3], 'Neon', shape=kit.BALL,
                     transparency=0.1)
        flowers.add(bloom)
    z.add(flowers)

    # fireflies
    for i, (r, deg) in enumerate(((70, 30), (70, 150), (70, 270), (130, 90), (130, 210), (130, 330))):
        x, _, zz = polar(r, deg)
        ff = part('Fireflies', CFrame.new(x, 6, zz), (60, 8, 60), (0, 0, 0), transparency=1, collide=False,
                  touch=False, query=False, shadow=False)
        ff.add(particles('Glow', ((0, (210, 255, 150)), (1, (150, 255, 200))), rate=5, life=(4, 7),
                         speed=(0.3, 1.0), size=((0, 0, 0), (0.2, 0.22, 0), (0.8, 0.22, 0), (1, 0, 0)),
                         transparency=((0, 1, 0), (0.2, 0.1, 0), (0.8, 0.1, 0), (1, 1, 0)), emission_dir=1,
                         shape=0))
        z.add(ff)

    # distant hills
    for i in range(7):
        x, _, zz = polar(rnd.uniform(430, 520), i * 360 / 7 + rnd.uniform(-10, 10))
        d = rnd.uniform(230, 330)
        z.add(ball('Hill', (x, -d * 0.36, zz), d, (26, 40, 38), 'Grass', collide=False, touch=False, query=False,
                   shadow=False))

    # invisible boundary at the forest edge
    for i in range(18):
        a = 360 * i / 18
        x, _, zz = polar(262, a)
        z.add(part('Boundary', look_at((x, 25, zz), (0, 25, 0)), (92, 50, 2), (0, 0, 0), transparency=1,
                   shadow=False, touch=False, query=False))
    return z, None

def build_portal(ctx, zone, deg):
    zd = ctx.zone(zone)
    col = ctx.rgb(zone)
    x, _, zz = polar(PORTAL_RADIUS, deg)
    cf = look_at((x, 0, zz), (0, 0, 0))   # front faces the fire
    m = Inst('Model', f'Portal_{zone}').attr(Zone=zone)
    m.add(part('Base', cf * CFrame.new(0, 0.2, 0, 0, 0, 90), (0.8, 19, 19), (70, 74, 90), 'Slate', shape=kit.CYL))
    for side in (-1, 1):
        m.add(part('Pillar', cf * CFrame.new(side * 7.8, 9.6, 0), (3, 18.4, 3), (76, 80, 96), 'Slate'))
        m.add(deco('PillarGlow', cf * CFrame.new(side * 7.8, 9.6, -1.55), (0.4, 15, 0.2), col, 'Neon',
                   transparency=0.25))
    m.add(part('Lintel', cf * CFrame.new(0, 19.8, 0), (19.5, 3, 4), (76, 80, 96), 'Slate'))
    sign = part('Sign', cf * CFrame.new(0, 19.8, -2.1), (16.5, 2.6, 0.2), (18, 20, 38), 'SmoothPlastic',
                collide=False, shadow=False)
    sign.add(surface_gui('Label', 30,
        label('Numeral', zd.get('numeral', ''), color=col, family=kit.TITLE_FONT, size=U2(0.12, 0, 0.9, 0),
              pos=U2(0.02, 0, 0.05, 0), max_size=64, stroke=0.8),
        label('Name', zd['name'].upper(), color=kit.WHITE, family=kit.TITLE_FONT, size=U2(0.8, 0, 0.8, 0),
              pos=U2(0.15, 0, 0.1, 0), max_size=64, stroke=0.8), brightness=1.3))
    m.add(sign)
    gate = part('Gate', cf * CFrame.new(0, 9.6, 0), (12.6, 17.6, 0.4), col, 'Neon', collide=False, touch=True,
                query=True, shadow=False, transparency=0.45)
    gate.tag('Portal').attr(Zone=zone, Action='portal')
    gate.add(prompt('portal', 'Enter', zd['name'], hold=0.25, dist=12, Zone=zone))
    gate.add(point_light(col, 24, 1.6))
    gate.add(particles('Swirl', one_color(col), rate=14, life=(1.5, 3), speed=(0.5, 2),
                       size=((0, 0.35, 0), (1, 0, 0))))
    gate.add(surface_gui('Status', 20,
        label('State', '', color=kit.WHITE, family=kit.TITLE_FONT, size=U2(0.9, 0, 0.12, 0), pos=U2(0.05, 0, 0.44, 0),
              max_size=60, stroke=0.4), face=5, brightness=1.2))
    m.add(gate)
    return m
