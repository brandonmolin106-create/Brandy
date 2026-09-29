"""Open-ocean sets: underwater (the fish set free) and the surface world (storm, sunrise, the tree on the cliff).

Registers its shots into shots.SHOTS on import.
"""
import math

import bpy
import mathutils
import numpy as np

import props
import sets
import shots
from betta import Betta, L
from shots import FPS, Ctx, cam, ease, lerp, lerp3, place_fish, shot  # noqa: F401


# ---------------------------------------------------------------- underwater
def underwater_world(top=(0.10, 0.42, 0.62), mid=(0.012, 0.09, 0.16), deep=(0.0, 0.006, 0.014), strength=1.0):
    """Infinite water: bright cyan toward the surface, fading to black in the deep."""
    w = bpy.context.scene.world or bpy.data.worlds.new('World')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for x in list(nt.nodes):
        nt.nodes.remove(x)
    out = nt.nodes.new('ShaderNodeOutputWorld')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    el = ramp.color_ramp.elements
    el[0].position = 0.25
    el[0].color = (*deep, 1)
    el[1].position = 1.0
    el[1].color = (*top, 1)
    e = el.new(0.52)
    e.color = (*mid, 1)
    e2 = el.new(0.8)
    e2.color = (top[0] * 0.45, top[1] * 0.45, top[2] * 0.45, 1)
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = -1.0
    mr.inputs['From Max'].default_value = 1.0
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], ramp.inputs['Fac'])
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = strength
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    return w


def caustic_spot(loc=(0, 0, 1.2), power=40.0, size_deg=40, scale=18.0, color=(0.75, 0.92, 1.0)):
    """Spot light with an animated Voronoi 'caustic web' gobo (sunlight through surface waves)."""
    ld = bpy.data.lights.new('caustics', 'SPOT')
    ld.energy = power
    ld.color = color
    ld.spot_size = math.radians(size_deg)
    ld.spot_blend = 0.6
    ld.shadow_soft_size = 0.0
    ld.use_nodes = True
    nt = ld.node_tree
    em = nt.nodes['Emission']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vor = nt.nodes.new('ShaderNodeTexVoronoi')
    vor.voronoi_dimensions = '4D'
    vor.feature = 'SMOOTH_F1'
    vor.inputs['Scale'].default_value = scale
    vor.inputs['Smoothness'].default_value = 0.6
    nt.links.new(tc.outputs['Normal'], vor.inputs['Vector'])
    pw = nt.nodes.new('ShaderNodeMath')
    pw.operation = 'POWER'
    pw.inputs[1].default_value = 3.0
    nt.links.new(vor.outputs['Distance'], pw.inputs[0])
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = 14.0
    nt.links.new(pw.outputs['Value'], mul.inputs[0])
    add = nt.nodes.new('ShaderNodeMath')
    add.operation = 'ADD'
    add.inputs[1].default_value = 0.25
    nt.links.new(mul.outputs['Value'], add.inputs[0])
    nt.links.new(add.outputs['Value'], em.inputs['Strength'])
    ob = bpy.data.objects.new('caustics', ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (0, 0, 0)
    return ob, vor


def surface_plane(z=1.5, size=30.0, name='sea_surface'):
    """Wavy water surface seen from below (Snell's window + total internal reflection)."""
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    ob = bpy.context.active_object
    ob.name = name
    mod = ob.modifiers.new('ocean', 'OCEAN')
    mod.geometry_mode = 'GENERATE'
    mod.size = 1.0
    mod.spatial_size = 40
    mod.resolution = 12
    mod.wave_scale = 0.6
    mod.choppiness = 0.8
    mod.wind_velocity = 9
    ob.scale = (size / 40.0, size / 40.0, 1.0)
    m, nt, b = props.new_mat('sea_surface_mat')
    b.inputs['Base Color'].default_value = (1, 1, 1, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.333
    b.inputs['Roughness'].default_value = 0.02
    ob.data.materials.append(m)
    ob.data.shade_smooth() if hasattr(ob.data, 'shade_smooth') else None
    return ob, mod


def glass_in_water(name='glass_uw'):
    """Glass seen from water: relative IOR 1.5 / 1.333."""
    m = props.glass_material(name)
    m.node_tree.nodes['Principled BSDF'].inputs['IOR'].default_value = 1.125
    return m


def ghost_material():
    """Barely-there glass: the cup that only exists in the fish's mind."""
    m, nt, b = props.new_mat('ghost_glass')
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.08
    b.inputs['Roughness'].default_value = 0.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.5, 0.8, 1.0, 1)
    em.inputs['Strength'].default_value = 0.0
    lw = nt.nodes.new('ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.15
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = 0.0
    nt.links.new(lw.outputs['Facing'], mul.inputs[0])
    nt.links.new(mul.outputs['Value'], em.inputs['Strength'])
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = 0.0      # 0 = invisible, 1 = full glass
    nt.links.new(tr.outputs['BSDF'], mix.inputs[1])
    nt.links.new(b.outputs['BSDF'], mix.inputs[2])
    add = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(mix.outputs['Shader'], add.inputs[0])
    nt.links.new(em.outputs['Emission'], add.inputs[1])
    nt.links.new(add.outputs['Shader'], nt.nodes['Material Output'].inputs['Surface'])
    return m, mix, mul


def bubbles(n, seed, center, spread, rmin=0.0015, rmax=0.005):
    """Air bubbles (spheres, glass with IOR < 1 because they are air inside water)."""
    import bmesh
    rng = np.random.default_rng(seed)
    m, nt, b = props.new_mat(f'bubble_{seed}')
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 0.75
    b.inputs['Roughness'].default_value = 0.0
    obs = []
    for k in range(n):
        me = bpy.data.meshes.new(f'bub{seed}_{k}')
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
        bm.to_mesh(me)
        bm.free()
        me.shade_smooth()
        ob = props.link_obj(f'bub{seed}_{k}', me, m)
        r = rng.uniform(rmin, rmax)
        ob.scale = (r, r, r * 0.8)
        ob['r'] = r
        ob['off'] = rng.uniform(-1, 1, 3).tolist()
        ob['t0'] = float(rng.uniform(0, 1))
        ob['sp'] = float(rng.uniform(0.6, 1.4))
        obs.append(ob)
    return obs


def uw_setup(ctx, fish=True, cup=True, surface=True, caustic_power=40.0):
    underwater_world()
    ld = bpy.data.lights.new('sun_uw', 'SUN')
    ld.energy = 2.2
    ld.color = (0.55, 0.85, 1.0)
    ld.angle = math.radians(8)
    sun = bpy.data.objects.new('sun_uw', ld)
    bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(12), math.radians(8), 0)
    ctx.caus, ctx.vor = caustic_spot(power=caustic_power)
    if surface:
        ctx.surf, ctx.ocean = surface_plane(z=1.2)
    ctx.fish = None
    if fish:
        f = Betta(sets.TEX)
        f.root.scale = (shots.FISH_SCALE,) * 3
        ctx.fish = f
    ctx.cup = None
    if cup:
        c = props.Cup(**shots.CUP_KW)
        c.glass.data.materials[0] = glass_in_water()
        c.water.hide_render = True
        ctx.cup = c
    return ctx


def animate_uw(ctx, t, follow=None):
    ctx.vor.inputs['W'].default_value = t * 0.35
    if follow is not None:
        ctx.caus.location = (follow[0] + 0.02, follow[1], follow[2] + 1.0)
    if 'ocean' in ctx and ctx.ocean is not None:
        ctx.ocean.time = 1.0 + t * 0.8


def glide(ctx, t, pos, heading, swim=0.35, freq=1.1, flare=0.7, turn=0.0, pitch=0.0, roll=0.0):
    place_fish(ctx.fish, pos, heading, pitch=pitch, roll=roll)
    ctx.fish.pose(t, swim=swim, freq=freq, flare=flare, turn=turn, flutter=1.1, dt=1 / FPS)


@shot('cup_sinks', 96)
def cup_sinks(ctx, i, t):
    """...into the big open ocean: the glass drops through the blue, tumbling, the fish inside, air escaping."""
    if i is None:
        uw_setup(ctx)
        ctx.cup.root.rotation_mode = 'XYZ'
        f = ctx.fish
        f.root.parent = ctx.cup.root
        ctx.bubs = bubbles(26, 3, (0, 0, 0.1), 0.05)
        return
    p = t / 4.0
    z = lerp(0.35, -0.05, ease(p) * 0.6 + p * 0.4)
    ctx.cup.root.location = (0.0, 0.0, z)
    ctx.cup.root.rotation_euler = (math.radians(lerp(8, 24, p)), math.radians(lerp(-6, 10, p)), 0.3 * p)
    f = ctx.fish
    place_fish(f, (0.004, 0.0, ctx.cup.base + 0.045 + 0.004 * math.sin(t * 3)), 2.0 + 0.8 * p, pitch=0.1, roll=0.2)
    f.pose(t, swim=0.5, freq=2.0, flare=0.5, turn=0.9, flutter=1.4, dt=1 / FPS)
    rim = ctx.cup.root.matrix_world @ mathutils.Vector((0.0, 0.0, ctx.cup.h))
    for ob in ctx.bubs:
        age = (t * ob['sp'] + ob['t0'] * 2.0) % 2.0
        o = ob['off']
        ob.location = (rim.x + o[0] * 0.03 + 0.01 * math.sin(age * 5 + o[1] * 3), rim.y + o[1] * 0.03,
                       rim.z + age * 0.16 + o[2] * 0.01)
        s = ob['r'] * (1 + 0.3 * age)
        ob.scale = (s, s, s * (0.75 + 0.1 * math.sin(age * 20)))
    animate_uw(ctx, t, follow=(0, 0, z))
    cam(ctx, (0.05, -0.42, z - 0.08 + 0.06 * p), (0.0, 0.0, z + 0.05), lens=40, fstop=5.6)


@shot('fish_free', 120)
def fish_free(ctx, i, t):
    """No glass walls. Nothing stopping it. The fish leaves the cup - camera pulls back into the endless blue."""
    if i is None:
        uw_setup(ctx)
        ctx.cup.root.location = (0.0, 0.0, 0.0)
        ctx.cup.root.rotation_euler = (math.radians(90), 0, math.radians(-20))  # lying on its side, mouth toward +x
        return
    p = ease(t / 5.0)
    # the fish exits the cup mouth and swims off along +x, rising a little
    path = lerp(-0.02, 0.26, ease(t / 5.0) * 0.8 + t / 25.0)
    pos = (path * math.cos(math.radians(-20)) + 0.01, path * math.sin(math.radians(-20)) * 0.6,
           0.0 + 0.03 * p + 0.004 * math.sin(t * 2))
    glide(ctx, t, pos, math.radians(-20) + 0.15 * math.sin(t * 0.9), swim=0.55, freq=1.6, flare=0.8,
          turn=0.3 * math.sin(t * 0.9))
    animate_uw(ctx, t, follow=pos)
    cam(ctx, lerp3((0.06, -0.20, 0.03), (0.12, -0.75, 0.12), p), (lerp(0.03, 0.15, p), 0.0, lerp(0.0, 0.03, p)),
        lens=lerp(50, 35, p), fstop=5.6)


@shot('ocean_vast', 96)
def ocean_vast(ctx, i, t):
    """The water goes on and on and on: a speck of red in an infinite blue."""
    if i is None:
        uw_setup(ctx, cup=False, caustic_power=10.0)
        return
    pos = (0.0 + t * 0.03, 0.0, 0.0 + 0.004 * math.sin(t))
    glide(ctx, t, pos, 0.1 * math.sin(t * 0.5), swim=0.4, freq=1.2, flare=0.8, turn=0.2 * math.sin(t * 0.7))
    animate_uw(ctx, t, follow=pos)
    p = ease(t / 4.0)
    cam(ctx, lerp3((0.05, -0.9, -0.25), (0.1, -1.4, -0.35), p), (pos[0], 0.0, 0.1), lens=24, fstop=None)


@shot('ghost_circles', 96, loop=4.0)
def ghost_circles(ctx, i, t):
    """It stays swimming in the same small circles - the cup is gone, but it is still in its mind."""
    if i is None:
        uw_setup(ctx, cup=True)
        ctx.fish.loop_T = 4.0
        m, ctx.gmix, ctx.gem = ghost_material()
        ctx.cup.glass.data.materials[0] = m
        ctx.cup.root.location = (0, 0, -ctx.cup.base - 0.043)
        return
    a = 2 * math.pi * t / 4.0
    r = 0.012
    pos = (r * math.cos(a), r * math.sin(a), 0.003 * math.sin(2 * a + 0.7))
    place_fish(ctx.fish, pos, a + math.pi / 2, pitch=0.05 * math.sin(a), roll=0.18)
    ctx.fish.pose(t, swim=0.38, freq=1.25, flare=0.62, turn=1.4, flutter=1.0)
    # the ghost wall materialises then fades on each lap (driven by comp for the beat; mild here)
    g = 0.25 + 0.2 * math.sin(a)
    ctx.gmix.inputs['Fac'].default_value = g
    ctx.gem.inputs[1].default_value = 0.6 * g
    animate_uw(ctx, t, follow=(0, 0, 0))
    cam(ctx, (0.05, -0.22, 0.09), (0.0, 0.0, 0.0), lens=50, fstop=8)
