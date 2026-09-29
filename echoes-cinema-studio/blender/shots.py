"""Shot definitions for the thriller cut.  Each shot = build(ctx) once + frame(ctx, i, t) per frame.

Run:  blender -b --factory-startup --python run_shot.py -- SHOT OUTDIR [first last]
"""
import math

import bpy
import mathutils
import numpy as np

import props
import sets
from betta import Betta, L

FPS = 24


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lerp(a, b, x):
    return a + (b - a) * x


def lerp3(a, b, x):
    return tuple(lerp(p, q, x) for p, q in zip(a, b))


class Ctx(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


# ---------------------------------------------------------------- cup set
CUP_KW = dict(wall=0.0014, base=0.007, r_bottom=0.042, r_top=0.05, height=0.115, fill=0.8)
FISH_SCALE = 0.6


def cup_set(ctx, lamp=50.0, moon=0.45, beam=0.0, fish=True, water=True, back=0.0):
    ctx.room = sets.Room(lamp_power=lamp, moon=moon, beam=beam, back_light=back)
    ctx.cup = props.Cup(**CUP_KW)
    if not water:
        ctx.cup.water.hide_render = True
    ctx.fish = None
    if fish:
        f = Betta(sets.TEX)
        f.root.scale = (FISH_SCALE,) * 3
        f.root.parent = ctx.cup.root
        ctx.fish = f
    ctx.zmid = ctx.cup.base + 0.043
    return ctx


def place_fish(f, pos, heading, pitch=0.0, roll=0.0):
    f.root.location = pos
    f.root.rotation_euler = (roll, pitch, heading)


def circle_swim(ctx, t, T=4.0, r=0.012, z=None, phase=0.0, bob=0.003, ccw=True):
    """Sad little laps inside the cup (periodic in T)."""
    f = ctx.fish
    z = ctx.zmid if z is None else z
    a = 2 * math.pi * t / T * (1 if ccw else -1) + phase
    pos = (r * math.cos(a), r * math.sin(a), z + bob * math.sin(2 * math.pi * t / T * 2 + 0.7))
    heading = a + (math.pi / 2 if ccw else -math.pi / 2)
    place_fish(f, pos, heading, pitch=0.05 * math.sin(2 * math.pi * t / T), roll=(0.18 if ccw else -0.18))
    f.pose(t, swim=0.38, freq=1.25, flare=0.62, turn=(1.0 if ccw else -1.0) * 1.4, flutter=1.0)


def cam(ctx, loc, target, lens=85, fstop=5.6, focus=None):
    if 'cam' not in ctx:
        ctx.cam = sets.camera(loc, target, lens=lens, fstop=fstop, focus=focus)
    else:
        ctx.cam.data.lens = lens
        if fstop:
            ctx.cam.data.dof.aperture_fstop = fstop
        sets.aim(ctx.cam, loc, target, focus=focus)


def kicker(ctx, loc, target, power=0.25, size=0.02):
    """Small soft light by the lens: catchlight in the eye + front fill for the macros."""
    if 'kick' not in ctx:
        ctx.kick = props.area_light('kicker', loc, (0, 0, 0), size, power, (1.0, 0.86, 0.72))
    ctx.kick.location = loc
    d = mathutils.Vector(target) - mathutils.Vector(loc)
    ctx.kick.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    ctx.kick.data.energy = power


def lamp_flicker(ctx, t, base):
    """Old tungsten bulb warming up / stuttering."""
    lamp, bulb = ctx.room.lamp, ctx.room.bulb
    lamp.data.energy = base
    em = bulb.active_material.node_tree.nodes['Emission']
    em.inputs['Strength'].default_value = 60.0 * base / 50.0


# ---------------------------------------------------------------- shots
SHOTS = {}


def shot(name, frames, res=(540, 960), spp=8, loop=None):
    def deco(fn):
        SHOTS[name] = dict(fn=fn, frames=frames, res=res, spp=spp, loop=loop)
        return fn
    return deco


@shot('reveal_wide', 96)
def reveal_wide(ctx, i, t):
    """Cold open: the lamp stutters on over the table, the glass and its prisoner."""
    if i is None:
        cup_set(ctx, lamp=0.0, beam=0.3, moon=0.35)
        ctx.fish.loop_T = 4.0
        return
    seq = [(0.0, 0.0), (0.55, 0.0), (0.6, 1.0), (0.66, 0.1), (0.75, 0.0), (0.95, 0.0), (1.0, 0.7), (1.05, 0.2),
           (1.12, 1.0), (4.0, 1.0)]
    k = float(np.interp(t, [a for a, _ in seq], [b for _, b in seq]))
    lamp_flicker(ctx, t, 55.0 * k)
    ctx.room.beam.active_material.node_tree.nodes['Emission'].inputs['Color'].default_value = (k, k * 0.78, k * 0.5, 1)
    circle_swim(ctx, t)
    ctx.cup.ripple(t)
    p = ease(t / 4.0)
    cam(ctx, lerp3((0.30, -0.95, 0.34), (0.24, -0.78, 0.29), p), (0.0, 0.0, 0.09), lens=50, fstop=4.0)


@shot('cup_side_loop', 96, loop=4.0)
def cup_side_loop(ctx, i, t):
    if i is None:
        cup_set(ctx)
        ctx.fish.loop_T = 4.0
        return
    circle_swim(ctx, t)
    ctx.cup.ripple(t)
    cam(ctx, (0.03, -0.27, 0.07), (0.0, 0.0, 0.054), lens=85, fstop=8)


@shot('cup_high_loop', 96, loop=4.0)
def cup_high_loop(ctx, i, t):
    if i is None:
        cup_set(ctx)
        ctx.fish.loop_T = 4.0
        return
    circle_swim(ctx, t, phase=1.3)
    ctx.cup.ripple(t)
    cam(ctx, (0.15, -0.29, 0.23), (0.0, 0.0, 0.048), lens=85, fstop=8)


@shot('cup_top_loop', 96, loop=4.0)
def cup_top_loop(ctx, i, t):
    """Looking straight down into the cup: the same circle, forever."""
    if i is None:
        cup_set(ctx, lamp=36.0)
        ctx.fish.loop_T = 4.0
        return
    circle_swim(ctx, t, r=0.012, phase=0.4)
    ctx.cup.ripple(t, calm=1.4)
    cam(ctx, (0.0, -0.012, 0.36), (0.0, 0.0, 0.03), lens=60, fstop=8)


@shot('fish_macro_turn', 96)
def fish_macro_turn(ctx, i, t):
    """'Just imagine a fish': underwater macro inside the cup - the betta glides past and unfurls in profile."""
    if i is None:
        cup_set(ctx, lamp=55.0)
        return
    f = ctx.fish
    p = ease(t / 4.0)
    heading = lerp(math.radians(160), math.radians(195), p)
    pos = (lerp(0.010, -0.004, p), 0.008, ctx.zmid + 0.002 * math.sin(t * 1.3))
    place_fish(f, pos, heading, pitch=-0.04, roll=0.0)
    f.pose(t, swim=lerp(0.32, 0.14, p), freq=0.9, flare=lerp(0.35, 1.0, ease((t - 0.8) / 2.6)),
           turn=lerp(-0.5, 0.2, p), flutter=1.2, dt=1 / FPS)
    ctx.cup.ripple(t)
    # camera sits in the water, 5 cm off the fish: no glass between us and the detail
    loc = lerp3((0.010, -0.030, ctx.zmid + 0.004), (0.002, -0.026, ctx.zmid + 0.002), p)
    cam(ctx, loc, (pos[0], pos[1], pos[2]), lens=50, fstop=8, focus=None)
    kicker(ctx, (loc[0] + 0.012, loc[1] - 0.005, loc[2] + 0.015), pos, power=0.02, size=0.004)


@shot('hit_glass', 84)
def hit_glass(ctx, i, t):
    """It swims forward - it hits GLASS. Like a wall.  Underwater, in profile: the fish rams its own reflection."""
    if i is None:
        cup_set(ctx, lamp=55.0)
        return
    f = ctx.fish
    rin = ctx.cup.r_inner(ctx.zmid)
    nose = 0.5 * L * FISH_SCALE
    wall = rin - nose - 0.0005
    t_hit = 0.9
    if t < t_hit:
        x = lerp(-0.012, wall, ease(t / t_hit) ** 1.5)
        swim, freq, flare = 0.9, 3.2, 0.3
    elif t < 1.5:
        k = (t - t_hit) / 0.6
        x = wall - 0.008 * math.sin(min(k, 1) * math.pi / 2) * math.exp(-k * 0.5)
        swim, freq, flare = lerp(0.2, 0.05, k), 0.8, lerp(0.85, 0.5, k)
    else:
        k = ease((t - 1.5) / 2.0)
        x = wall - 0.008 - 0.012 * k
        swim, freq, flare = 0.35, 1.2, 0.55
    heading = 0.0 if t < 1.5 else lerp(0.0, math.pi - 0.3, ease((t - 1.5) / 1.6))
    fy = 0.010
    place_fish(f, (x, fy, ctx.zmid), heading, pitch=0.0, roll=0.0)
    turn = 0.0 if t < 1.5 else 1.2 * math.sin(math.pi * min(1, (t - 1.5) / 1.6))
    f.pose(t, swim=swim, freq=freq, flare=flare, turn=turn, flutter=1.3 if t > t_hit else 0.8, dt=1 / FPS)
    ctx.cup.ripple(t, extra=[(t_hit, rin - 0.004, fy, 1.3)])
    shake = 0.0008 * math.exp(-max(0, t - t_hit) * 7) * (t > t_hit)
    loc = (0.0 + shake * math.sin(t * 90), fy - 0.035, ctx.zmid + 0.003 + shake * math.cos(t * 77))
    tgt = (0.030, fy, ctx.zmid)
    cam(ctx, loc, tgt, lens=40, fstop=8, focus=0.045)
    kicker(ctx, (loc[0] - 0.01, loc[1] - 0.004, loc[2] + 0.012), tgt, power=0.02, size=0.004)


@shot('stops_trying', 96)
def stops_trying(ctx, i, t):
    """The fish stops. Sinks. Fins fold. The lamp sags."""
    if i is None:
        cup_set(ctx, lamp=50.0)
        return
    f = ctx.fish
    p = ease(t / 4.0)
    place_fish(f, (0.004, 0.002, lerp(ctx.zmid, ctx.cup.base + 0.011, p)), math.radians(200),
               pitch=lerp(0.0, 0.12, p), roll=lerp(0.0, 0.1, p))
    f.pose(t, swim=lerp(0.25, 0.02, p), freq=lerp(1.0, 0.4, p), flare=lerp(0.5, 0.0, p), turn=lerp(0.3, 0.05, p),
           flutter=lerp(1.0, 0.35, p), dt=1 / FPS)
    lamp_flicker(ctx, t, lerp(50.0, 30.0, p))
    ctx.cup.ripple(t, calm=lerp(1.0, 0.2, p))
    cam(ctx, lerp3((0.02, -0.3, 0.075), (0.015, -0.26, 0.055), p), (0.0, 0.0, lerp(ctx.zmid, 0.03, p)), lens=85,
        fstop=8)


@shot('flare', 72)
def flare(ctx, i, t):
    """NO. The fish squares up in three-quarter profile and throws every fin open (underwater)."""
    if i is None:
        cup_set(ctx, lamp=60.0)
        return
    f = ctx.fish
    p = ease(t / 1.2)
    pos = (0.004, 0.012, ctx.zmid)
    place_fish(f, pos, math.radians(-150) + 0.12 * math.sin(t * 1.4), pitch=-0.03, roll=0.0)
    f.pose(t, swim=lerp(0.4, 0.1, p), freq=lerp(1.6, 0.8, p), flare=lerp(0.4, 1.0, p), turn=0.25 * math.sin(t * 1.4),
           flutter=1.4, dt=1 / FPS)
    ctx.cup.ripple(t)
    q = ease(t / 3)
    loc = lerp3((-0.004, -0.030, ctx.zmid - 0.006), (-0.002, -0.024, ctx.zmid - 0.004), q)
    cam(ctx, loc, pos, lens=40, fstop=8)
    kicker(ctx, (loc[0] + 0.01, loc[1] - 0.004, loc[2] + 0.014), pos, power=0.02, size=0.004)


@shot('lift', 96)
def lift(ctx, i, t):
    """Someone lifts the cup. Table-level, the glass leaves its wet ring behind."""
    if i is None:
        cup_set(ctx, lamp=50.0, beam=0.18)
        ring_mat, nt, b = props.new_mat('wet_ring')
        b.inputs['Base Color'].default_value = (0.01, 0.006, 0.004, 1)
        b.inputs['Roughness'].default_value = 0.05
        verts, faces, _ = props.lathe([(0.0, 0.0), (0.0345, 0.0), (0.035, 0.0), (0.0, 0.0)], 96)
        ring = props.link_obj('wet_ring', props.make_mesh('wet_ring', verts, faces), ring_mat)
        ring.location = (0, 0, 0.0002)
        ctx.fish.loop_T = None
        return
    k = ease((t - 0.6) / 3.0)
    ctx.cup.root.location = (0.0, 0.0, 0.26 * k ** 1.3)
    ctx.cup.root.rotation_euler = (0.06 * math.sin(t * 2.2) * k, 0.05 * math.sin(t * 1.7 + 1) * k, 0)
    circle_swim(ctx, t, r=0.011)
    jolt = [(0.62, 0.0, 0.0, 1.6), (1.4, 0.01, 0.0, 0.8)]
    ctx.cup.ripple(t, calm=1.0 + 2.0 * k, extra=jolt)
    cam(ctx, (0.02, -0.34, 0.035 + 0.05 * k), (0.0, 0.0, 0.05 + 0.14 * k), lens=50, fstop=4.0, focus=0.34)


@shot('eye_macro', 96)
def eye_macro(ctx, i, t):
    """Final push: into the eye (underwater macro inside the cup)."""
    if i is None:
        cup_set(ctx, lamp=55.0)
        return
    f = ctx.fish
    place_fish(f, (0.0, 0.012, ctx.zmid), math.radians(180) + 0.05 * math.sin(t * 0.8), pitch=0.0, roll=0.0)
    f.pose(t, swim=0.08, freq=0.6, flare=0.7, turn=0.05, flutter=0.8, dt=1 / FPS)
    ctx.cup.ripple(t, calm=0.5)
    eye = [ob for sd, ob in f.eyes if sd == 1][0]
    bpy.context.view_layer.update()
    e = eye.matrix_world.translation
    p = ease(t / 4.0)
    loc = (e.x + 0.002, e.y - lerp(0.032, 0.012, p), e.z + 0.001)
    cam(ctx, loc, (e.x, e.y, e.z), lens=50, fstop=11, focus=(mathutils.Vector(loc) - e).length)
    kicker(ctx, (loc[0] + 0.008, loc[1] - 0.004, loc[2] + 0.01), (e.x, e.y, e.z), power=0.015, size=0.003)


def still(name, **kw):
    SHOTS[name] = dict(fn=None, frames=1, res=(540, 960), spp=24, loop=None, still=kw)


@shot('empty_cup', 1, spp=24)
def empty_cup(ctx, i, t):
    if i is None:
        cup_set(ctx, lamp=40.0, fish=False)
        return
    ctx.cup.ripple(0.0, calm=0.0)
    cam(ctx, (0.03, -0.34, 0.07), (0.0, 0.0, 0.056), lens=85, fstop=8)


@shot('dry_cup', 1, spp=24)
def dry_cup(ctx, i, t):
    if i is None:
        cup_set(ctx, lamp=35.0, fish=False, water=False)
        return
    cam(ctx, (0.03, -0.34, 0.07), (0.0, 0.0, 0.056), lens=85, fstop=8)


@shot('no_cup', 1, spp=24)
def no_cup(ctx, i, t):
    if i is None:
        cup_set(ctx, lamp=30.0, fish=False, water=False)
        ctx.cup.glass.hide_render = True
        return
    cam(ctx, (0.03, -0.34, 0.07), (0.0, 0.0, 0.056), lens=85, fstop=8)
