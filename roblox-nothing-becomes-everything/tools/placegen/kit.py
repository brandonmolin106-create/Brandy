"""Shared building blocks for every zone: parts, GUIs, prompts and set pieces
(speech stones, insight pedestals, portals, checkpoints, video screens, trees...)."""
import math
import random

from .rbx import (Inst, S, B, I, F, D, T, V3, V2, C3, C3u8, U2, U, NR, NS, CS, CT, FONT, FAMILY,
                  CFrame, look_at, attr_vec3)

MAT = dict(Plastic=256, SmoothPlastic=272, Neon=288, Wood=512, WoodPlanks=528, Marble=784, Basalt=788,
           Slate=800, CrackedLava=804, Concrete=816, Limestone=820, Granite=832, Pavement=836, Brick=848,
           Pebble=864, Cobblestone=880, Rock=896, Sandstone=912, CorrodedMetal=1040, DiamondPlate=1056,
           Foil=1072, Metal=1088, Grass=1280, LeafyGrass=1284, Sand=1296, Fabric=1312, Snow=1328, Mud=1344,
           Ground=1360, Asphalt=1376, Salt=1392, Ice=1536, Glacier=1552, Glass=1568, ForceField=1584)
BALL, BLOCK, CYL = 0, 1, 2

# palette (matches the loading screen: deep navy, cyan glow, white serif)
NAVY = (10, 12, 30)
CYAN = (120, 225, 240)
WHITE = (245, 245, 245)
SOFT = (200, 208, 232)
GOLD = (255, 214, 140)
STONE = (92, 96, 112)
STONE_DARK = (58, 60, 74)
BRASS = (196, 150, 72)
BRASS_DARK = (140, 100, 44)

TITLE_FONT = FAMILY['Fantasy']      # Balthazar, a classical serif (Enum.Font.Fantasy)
UI_FONT = FAMILY['BuilderSans']

# ----------------------------------------------------------------------------- parts
def as_cf(cf):
    if isinstance(cf, CFrame):
        return cf
    if isinstance(cf, tuple) and len(cf) == 3:
        return CFrame(cf)
    raise TypeError(cf)

def part(name, cf, size, color, material='SmoothPlastic', shape=None, collide=True, touch=True, query=True,
         shadow=True, transparency=0.0, reflect=None, cls='Part', anchored=True):
    p = Inst(cls, name)
    p.set(Anchored=B(anchored), CanCollide=B(collide), CanTouch=B(touch), CanQuery=B(query), CastShadow=B(shadow),
          CFrame=as_cf(cf).val(), size=V3(*size), Color3uint8=C3u8(color), Material=T(MAT[material]),
          TopSurface=T(0), BottomSurface=T(0), Transparency=F(transparency))
    if reflect is not None:
        p.set(Reflectance=F(reflect))
    if shape is not None and cls in ('Part', 'Seat', 'SpawnLocation'):
        p.set(shape=T(shape))
    return p

def deco(name, cf, size, color, material='SmoothPlastic', shape=None, transparency=0.0, shadow=False, reflect=None,
         cls='Part'):
    """Decoration: no collision, no touch, no raycasts, no shadow (cheap)."""
    return part(name, cf, size, color, material, shape=shape, collide=False, touch=False, query=False,
                shadow=shadow, transparency=transparency, reflect=reflect, cls=cls)

def wedge(name, cf, size, color, material='Slate', collide=True, shadow=True, transparency=0.0):
    """WedgePart: full height at the back (+Z), sloping down to the front (-Z)."""
    return part(name, cf, size, color, material, collide=collide, touch=collide, query=collide, shadow=shadow,
                transparency=transparency, cls='WedgePart')

def disc(name, center, diameter, thickness, color, material='SmoothPlastic', **kw):
    """Horizontal cylinder disc whose TOP is at center.y."""
    x, y, z = center
    return part(name, CFrame.new(x, y - thickness / 2, z, 0, 0, 90), (thickness, diameter, diameter), color,
                material, shape=CYL, **kw)

def pillar(name, base, diameter, height, color, material='Slate', **kw):
    """Vertical cylinder standing on base (x, y, z)."""
    x, y, z = base
    return part(name, CFrame.new(x, y + height / 2, z, 0, 0, 90), (height, diameter, diameter), color, material,
                shape=CYL, **kw)

def ball(name, center, diameter, color, material='SmoothPlastic', **kw):
    return part(name, as_cf(center), (diameter, diameter, diameter), color, material, shape=BALL, **kw)

def block_on(name, x, ytop, z, sx, sy, sz, color, material='Slate', ry=0.0, **kw):
    """Block whose top face is at ytop."""
    return part(name, CFrame.new(x, ytop - sy / 2, z, 0, ry, 0), (sx, sy, sz), color, material, **kw)

def value(cls, name, v):
    tags = {'IntValue': ('int64',), 'NumberValue': ('double',), 'StringValue': ('string',), 'BoolValue': ('bool',)}
    if cls == 'StringValue':
        return Inst(cls, name, Value=S(v))
    if cls == 'BoolValue':
        return Inst(cls, name, Value=B(v))
    if cls == 'NumberValue':
        return Inst(cls, name, Value=D(v))
    raise ValueError(cls)

# ----------------------------------------------------------------------------- lights & effects
def point_light(color, rng=16, brightness=1.0, shadows=False, enabled=True, name='Light'):
    return Inst('PointLight', name, Color=C3(*color), Range=F(rng), Brightness=F(brightness), Shadows=B(shadows),
                Enabled=B(enabled))

def spot_light(color, rng=40, brightness=2.0, angle=60, face=4, shadows=False, name='Spot'):
    return Inst('SpotLight', name, Color=C3(*color), Range=F(rng), Brightness=F(brightness), Angle=F(angle),
                Face=T(face), Shadows=B(shadows), Enabled=B(True))

SPARKLE = 'rbxasset://textures/particles/sparkles_main.dds'

def particles(name, color_seq, rate=10, life=(2, 4), speed=(1, 3), size=((0, 0.3, 0), (1, 0, 0)),
              transparency=((0, 0.2, 0), (0.8, 0.4, 0), (1, 1, 0)), spread=(180, 180), accel=(0, 0, 0),
              light=1.0, emission_dir=1, texture=SPARKLE, drag=0.0, rot=(0, 0), rotspeed=(0, 0), enabled=True,
              zoffset=0.0, shape=None, brightness=1.0, lock=False):
    pe = Inst('ParticleEmitter', name, Rate=F(rate), Lifetime=NR(*life), Speed=NR(*speed),
              SpreadAngle=V2(*spread), EmissionDirection=T(emission_dir), LightEmission=F(light),
              Color=CS(*color_seq), Size=NS(*size), Transparency=NS(*transparency),
              Acceleration=V3(*accel), Texture=CT(texture), Drag=F(drag), Rotation=NR(*rot),
              RotSpeed=NR(*rotspeed), Enabled=B(enabled), ZOffset=F(zoffset), Brightness=F(brightness),
              LockedToPart=B(lock))
    if shape is not None:
        pe.set(Shape=T(shape))
    return pe

def one_color(rgb):
    return ((0, rgb), (1, rgb))

# ----------------------------------------------------------------------------- GUI
def label(name, text, color=WHITE, size=U2(1, 0, 1, 0), pos=U2(0, 0, 0, 0), family=None, weight=400,
          style='Normal', stroke=1.0, stroke_color=(0, 0, 0), bg=None, bg_t=1.0, z=1, wrapped=True,
          max_size=None, min_size=8, scaled=True, text_size=24, xalign=2, yalign=1, transparency=0.0,
          visible=True, anchor=(0, 0), line_height=1.0, rich=False):
    lb = Inst('TextLabel', name, Size=size, Position=pos, AnchorPoint=V2(*anchor), BackgroundTransparency=F(bg_t),
              BorderSizePixel=I(0), Text=S(text), TextColor3=C3(*color), TextScaled=B(scaled),
              TextSize=F(text_size), TextWrapped=B(wrapped), FontFace=FONT(family or UI_FONT, weight, style),
              TextStrokeTransparency=F(stroke), TextStrokeColor3=C3(*stroke_color), ZIndex=I(z),
              TextXAlignment=T(xalign), TextYAlignment=T(yalign), TextTransparency=F(transparency),
              Visible=B(visible), LineHeight=F(line_height), RichText=B(rich))
    if bg is not None:
        lb.set(BackgroundColor3=C3(*bg))
    if max_size:
        lb.add(Inst('UITextSizeConstraint', 'TextSize', MaxTextSize=I(max_size), MinTextSize=I(min_size)))
    return lb

def frame(name, size=U2(1, 0, 1, 0), pos=U2(0, 0, 0, 0), color=NAVY, transparency=0.0, z=1, anchor=(0, 0),
          visible=True):
    return Inst('Frame', name, Size=size, Position=pos, AnchorPoint=V2(*anchor), BackgroundColor3=C3(*color),
                BackgroundTransparency=F(transparency), BorderSizePixel=I(0), ZIndex=I(z), Visible=B(visible))

def corner(radius_scale=0.0, radius_px=8):
    return Inst('UICorner', 'Corner', CornerRadius=U(radius_scale, radius_px))

def stroke(color=CYAN, thickness=2, transparency=0.0, mode=1):
    return Inst('UIStroke', 'Stroke', Color=C3(*color), Thickness=F(thickness), Transparency=F(transparency),
                ApplyStrokeMode=T(mode))

def gradient(seq, rotation=90, transparency=None):
    g = Inst('UIGradient', 'Gradient', Color=CS(*seq), Rotation=F(rotation))
    if transparency:
        g.set(Transparency=NS(*transparency))
    return g

def surface_gui(name, ppstud, *kids, face=5, brightness=1.0, light_influence=0.0, always_on_top=False):
    g = Inst('SurfaceGui', name, Face=T(face), SizingMode=T(1), PixelsPerStud=F(ppstud),
             LightInfluence=F(light_influence), Brightness=F(brightness), AlwaysOnTop=B(always_on_top),
             ClipsDescendants=B(True), MaxDistance=F(0), ZIndexBehavior=T(1), ResetOnSpawn=B(False))
    return g.add(*kids)

def billboard(name, studs_w, studs_h, offset_y, max_dist, *kids, always_on_top=False, light_influence=0.0):
    g = Inst('BillboardGui', name, Size=U2(studs_w, 0, studs_h, 0), StudsOffset=V3(0, offset_y, 0),
             MaxDistance=F(max_dist), LightInfluence=F(light_influence), AlwaysOnTop=B(always_on_top),
             ClipsDescendants=B(False), ZIndexBehavior=T(1), ResetOnSpawn=B(False))
    return g.add(*kids)

def prompt(action, action_text, object_text='', hold=0.0, dist=10.0, key=101, **attrs):
    """ProximityPrompt. The 'Action' attribute routes it (server: Server.server.lua, client: Interactions)."""
    pp = Inst('ProximityPrompt', 'Prompt', ActionText=S(action_text), ObjectText=S(object_text),
              HoldDuration=F(hold), MaxActivationDistance=F(dist), RequiresLineOfSight=B(False),
              KeyboardKeyCode=T(key), Enabled=B(True), ClickablePrompt=B(True))
    pp.attr(Action=action, **attrs)
    return pp

# ----------------------------------------------------------------------------- set pieces
def speech_stone(name, base, face_toward, line_id, excerpt, accent=CYAN, height=6.5):
    """A standing stone that plays one of Brandon's lines ('Listen' prompt)."""
    x, y, z = base
    m = Inst('Model', name).attr(LineId=line_id).tag('SpeechStone')
    cf = look_at((x, y + height / 2, z), (face_toward[0], y + height / 2, face_toward[2]))
    stone = part('Stone', cf, (4.2, height, 1.4), STONE, 'Slate')
    stone.add(prompt('listen', 'Listen', 'Brandon', dist=11, LineId=line_id))
    stone.add(surface_gui('Words', 60,
        label('Quote', excerpt, color=(236, 238, 250), family=TITLE_FONT, style='Italic', size=U2(0.86, 0, 0.34, 0),
              pos=U2(0.07, 0, 0.06, 0), max_size=48, stroke=0.7, stroke_color=(20, 20, 40)),
        label('Hint', 'LISTEN', color=accent, family=UI_FONT, weight=700, size=U2(0.6, 0, 0.07, 0),
              pos=U2(0.2, 0, 0.86, 0), stroke=1.0),
        brightness=1.2))
    # glowing rune strip between the quote (top) and the LISTEN hint (bottom)
    glow_cf = cf * CFrame.new(0, height * (0.5 - 0.63), -0.72)
    glow = part('Glow', glow_cf, (0.35, height * 0.34, 0.12), accent, 'Neon', collide=False, touch=False, query=False,
                shadow=False, transparency=0.35)
    glow.add(point_light(accent, 14, 2.2, enabled=False))
    basecf = look_at((x, y + 0.4, z), (face_toward[0], y + 0.4, face_toward[2]))
    m.add(stone, glow, part('Base', basecf, (5.4, 0.8, 2.6), STONE_DARK, 'Slate', shadow=False))
    return m

def insight_pedestal(zone, base, zone_name, color):
    x, y, z = base
    m = Inst('Model', 'Insight').attr(Zone=zone)
    m.add(pillar('Pedestal', (x, y, z), 3.2, 3.4, (226, 222, 214), 'Marble'))
    m.add(disc('Cap', (x, y + 3.6, z), 4.2, 0.3, (236, 232, 222), 'Marble', shadow=False))
    crystal = part('Crystal', CFrame.new(x, y + 6.3, z, 45, 0, 45), (1.8, 1.8, 1.8), color, 'Neon',
                   collide=False, touch=False, shadow=False, transparency=0.05)
    crystal.tag('Insight').attr(Zone=zone)
    crystal.add(point_light(color, 22, 2.4))
    crystal.add(particles('Motes', one_color(color), rate=6, life=(2, 3.5), speed=(0.4, 1.2),
                          size=((0, 0.25, 0), (1, 0, 0)), accel=(0, 0.6, 0)))
    crystal.add(prompt('insight', 'Collect Insight', zone_name, hold=0.5, dist=11, Zone=zone))
    crystal.add(billboard('Label', 8, 1.6, 2.8, 70,
        label('Text', 'INSIGHT', color=color, family=TITLE_FONT, weight=700, stroke=0.6, max_size=40)))
    ring = deco('Ring', CFrame.new(x, y + 6.3, z, 0, 0, 90), (0.18, 4.4, 4.4), (250, 246, 230), 'Neon', shape=CYL,
                transparency=0.4)
    m.add(crystal, ring)
    return m

def return_portal(base, face_toward, color=CYAN, label_text='Return to the Clearing'):
    x, y, z = base
    m = Inst('Model', 'ReturnPortal')
    cf = look_at((x, y, z), (face_toward[0], y, face_toward[2]))
    for side in (-1, 1):
        m.add(part('Post', cf * CFrame.new(side * 4.2, 5, 0), (1.2, 10, 1.2), STONE, 'Slate'))
    m.add(part('Lintel', cf * CFrame.new(0, 10.4, 0), (10, 1.2, 1.6), STONE, 'Slate'))
    gate = part('Gate', cf * CFrame.new(0, 5, 0), (7, 9.4, 0.3), color, 'Neon', collide=False, touch=True,
                query=True, shadow=False, transparency=0.55)
    gate.attr(Action='return').tag('ReturnGate')
    gate.add(prompt('return', 'Return', 'The Clearing', hold=0.2, dist=10))
    gate.add(particles('Swirl', one_color(color), rate=10, life=(1.5, 2.5), speed=(0.5, 1.5),
                       size=((0, 0.3, 0), (1, 0, 0))))
    gate.add(point_light(color, 16, 1.5))
    sign = part('Sign', cf * CFrame.new(0, 11.8, -0.1), (8, 1.4, 0.2), NAVY, 'SmoothPlastic', collide=False,
                shadow=False)
    sign.add(surface_gui('Text', 40, label('Label', label_text, color=WHITE, family=TITLE_FONT, max_size=40,
                                            stroke=0.8), face=5))
    back = part('SignBack', cf * CFrame.new(0, 11.8, 0.1), (8, 1.4, 0.2), NAVY, 'SmoothPlastic', collide=False,
                shadow=False)
    back.add(surface_gui('Text', 40, label('Label', label_text, color=WHITE, family=TITLE_FONT, max_size=40,
                                            stroke=0.8), face=2))
    m.add(gate, sign, back)
    return m

def checkpoint(zone, index, top, size, shape='box', color=(70, 76, 96), material='Slate', glow=CYAN, ry=0.0):
    """Server-tracked checkpoint pad (tag 'Checkpoint') whose top face is at top=(x, y, z).
    size = (width, thickness, depth); for shape='disc' width is the diameter.
    Index 0 is the zone's arrival pad; respawns face the pad's front (-Z) direction."""
    x, ytop, z = top
    name = 'Checkpoint' if index > 0 else 'Spawn'
    if shape == 'disc':
        p = part(name, CFrame.new(x, ytop - size[1] / 2, z, 0, ry, 90), (size[1], size[0], size[0]), color, material,
                 shape=CYL)
        d = size[0]
    else:
        p = part(name, CFrame.new(x, ytop - size[1] / 2, z, 0, ry, 0), size, color, material)
        d = min(size[0], size[2])
    p.tag('Checkpoint').attr(Zone=zone, Index=index)
    ring = deco('CheckpointRing', CFrame.new(x, ytop + 0.02, z, 0, 0, 90), (0.06, d - 1.2, d - 1.2), glow, 'Neon',
                shape=CYL, transparency=0.55)
    return [p, ring]

def video_screen(zone, center, face_toward, height, frame_color=STONE_DARK, accent=CYAN, subtitle=''):
    """9:16 screen: SurfaceGui > VideoFrame 'Video' (tag ZoneScreen) + a 'Placeholder' panel."""
    w = height * 9 / 16
    cx, cy, cz = center
    cf = look_at(center, (face_toward[0], cy, face_toward[2]))
    m = Inst('Model', 'Screen').attr(Zone=zone)
    scr = part('Display', cf, (w, height, 0.5), (0, 0, 0), 'SmoothPlastic')
    video = Inst('VideoFrame', 'Video', Size=U2(1, 0, 1, 0), BackgroundColor3=C3(0, 0, 0),
                 BackgroundTransparency=F(0), BorderSizePixel=I(0), Looped=B(True), Volume=F(2), RollOffMode=T(3),
                 RollOffMinDistance=F(height * 1.2), RollOffMaxDistance=F(height * 7), ZIndex=I(1), Visible=B(False))
    video.tag('ZoneScreen').attr(Zone=zone, VideoKey=zone)
    ph = frame('Placeholder', color=(8, 10, 26), z=2)
    ph.add(gradient(((0, (22, 18, 58)), (0.55, (10, 12, 32)), (1, (6, 30, 44))), rotation=90))
    ring = frame('Emblem', size=U2(0.32, 0, 0.32, 0), pos=U2(0.5, 0, 0.3, 0), color=(10, 12, 30), z=3,
                 anchor=(0.5, 0.5))
    ring.add(Inst('UIAspectRatioConstraint', 'Aspect', AspectRatio=F(1)), corner(1, 0), stroke(accent, 5, 0.1))
    ring.add(label('Play', '▶', color=accent, family=UI_FONT, size=U2(0.5, 0, 0.5, 0), pos=U2(0.54, 0, 0.5, 0),
                   anchor=(0.5, 0.5), z=4))
    ph.add(ring)
    ph.add(label('Title', "Brandon's video goes here", color=WHITE, family=TITLE_FONT, size=U2(0.84, 0, 0.12, 0),
                 pos=U2(0.08, 0, 0.52, 0), z=3, max_size=64, stroke=1.0))
    ph.add(label('Subtitle', subtitle, color=SOFT, family=TITLE_FONT, style='Italic', size=U2(0.76, 0, 0.14, 0),
                 pos=U2(0.12, 0, 0.66, 0), z=3, max_size=40, stroke=1.0))
    ph.add(label('Brand', 'NOTHING BECOMES EVERYTHING', color=accent, family=UI_FONT, weight=700,
                 size=U2(0.8, 0, 0.035, 0), pos=U2(0.1, 0, 0.9, 0), z=3, max_size=28))
    scr.add(surface_gui('ScreenGui', 36, video, ph, brightness=1.15))
    m.add(scr)
    # frame
    t = 0.9
    for (px, py, sx, sy) in ((0, height / 2 + t / 2, w + 2 * t, t), (0, -height / 2 - t / 2, w + 2 * t, t),
                             (w / 2 + t / 2, 0, t, height), (-w / 2 - t / 2, 0, t, height)):
        m.add(part('Frame', cf * CFrame.new(px, py, 0.1), (sx, sy, 1.0), frame_color, 'Slate', shadow=False))
    for (px, py, sx, sy) in ((0, height / 2 + 0.12, w + 0.2, 0.18), (0, -height / 2 - 0.12, w + 0.2, 0.18),
                             (w / 2 + 0.12, 0, 0.18, height + 0.4), (-w / 2 - 0.12, 0, 0.18, height + 0.4)):
        m.add(deco('Trim', cf * CFrame.new(px, py, -0.3), (sx, sy, 0.2), accent, 'Neon', transparency=0.2))
    m.add(part('Back', cf * CFrame.new(0, 0, 0.8), (w + 2 * t, height + 2 * t, 0.6), frame_color, 'Slate'))
    return m, cf

def screen_console(zone, base, face_toward, accent=CYAN):
    x, y, z = base
    cf = look_at((x, y + 1.6, z), (face_toward[0], y + 1.6, face_toward[2]))
    m = Inst('Model', 'ScreenConsole')
    stand = part('Stand', cf, (2.4, 3.2, 1.6), STONE_DARK, 'Slate')
    stand.add(prompt('video', 'Play video', "Brandon's video", dist=12, Zone=zone))
    m.add(stand, deco('Glow', cf * CFrame.new(0, 1.62, 0), (2.5, 0.1, 1.7), accent, 'Neon', transparency=0.3))
    return m

# ----------------------------------------------------------------------------- nature
def tree(name, base, rnd, trunk_col=(70, 52, 40), leaf_cols=((40, 84, 70), (48, 96, 76)), scale=1.0,
         leaf_mat='LeafyGrass'):
    x, y, z = base
    h = rnd.uniform(9, 14) * scale
    m = Inst('Model', name)
    m.add(pillar('Trunk', (x, y, z), 1.6 * scale, h, trunk_col, 'Wood', shadow=True))
    c1 = rnd.choice(leaf_cols)
    s1 = rnd.uniform(8, 11) * scale
    m.add(ball('Leaves', (x, y + h + s1 * 0.15, z), s1, c1, leaf_mat, collide=False, touch=False, query=False))
    s2 = s1 * rnd.uniform(0.6, 0.75)
    m.add(ball('Leaves', (x + rnd.uniform(-1.5, 1.5) * scale, y + h + s1 * 0.55, z + rnd.uniform(-1.5, 1.5) * scale),
               s2, rnd.choice(leaf_cols), leaf_mat, collide=False, touch=False, query=False, shadow=False))
    return m

def pine(name, base, rnd, scale=1.0, col=(34, 70, 58)):
    """Stylised pine: trunk + three stacked, shrinking square tiers rotated 45 degrees."""
    x, y, z = base
    m = Inst('Model', name)
    h = 4 * scale
    m.add(pillar('Trunk', (x, y, z), 1.2 * scale, h + 2, (64, 46, 36), 'Wood'))
    yy = y + h
    for i, (w, th) in enumerate(((9, 4.5), (7, 4), (4.6, 3.6))):
        w *= scale; th *= scale
        m.add(part('Tier', CFrame.new(x, yy + th / 2, z, 0, 45 + i * 15, 0), (w, th, w), col, 'LeafyGrass',
                   collide=False, touch=False, query=False, shadow=(i == 0)))
        yy += th * 0.72
    return m

def rock(name, center, size, rnd, color=STONE, material='Slate', collide=True):
    x, y, z = center
    return part(name, CFrame.new(x, y, z, rnd.uniform(-12, 12), rnd.uniform(0, 360), rnd.uniform(-12, 12)), size,
                color, material, collide=collide, touch=collide, query=collide, shadow=collide)

def ring_positions(cx, cz, radius, count, start_deg=0.0):
    out = []
    for i in range(count):
        a = math.radians(start_deg + 360.0 * i / count)
        out.append((cx + radius * math.sin(a), cz + radius * math.cos(a), a))
    return out

def path_attrs(p, group, order, shape='box', **extra):
    """Mark a standable platform so tools/validate_place.py can check the jump gaps."""
    p.attr(PathGroup=group, PathOrder=order, PathShape=shape, **extra)
    return p
