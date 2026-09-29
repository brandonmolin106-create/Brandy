"""Big-world sets: storm ocean, sunrise, the lone tree, the pet-store shelf of cups, Earth and the galaxy.

Registers its shots into shots.SHOTS on import.
"""
import math

import bpy
import mathutils
import numpy as np

import props
import sets
import shots
from betta import Betta
from shots import FPS, cam, ease, lerp, lerp3, place_fish, shot  # noqa: F401

HDRI = sets.HDRI


# ---------------------------------------------------------------- sky + sea
def nishita_world(elev_deg=2.0, rot_deg=0.0, strength=1.0, air=1.0, dust=1.0, ozone=1.0, sun_size=0.8,
                  sun_intensity=1.0):
    w = bpy.context.scene.world or bpy.data.worlds.new('World')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for x in list(nt.nodes):
        nt.nodes.remove(x)
    out = nt.nodes.new('ShaderNodeOutputWorld')
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'NISHITA'
    sky.sun_elevation = math.radians(elev_deg)
    sky.sun_rotation = math.radians(rot_deg)
    sky.air_density = air
    sky.dust_density = dust
    sky.ozone_density = ozone
    sky.sun_disc = True
    sky.sun_size = math.radians(sun_size)
    sky.sun_intensity = sun_intensity
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = strength
    nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    return w, sky, bg


def sea(size=400.0, wave_scale=1.0, chop=1.0, wind=12.0, res=14, color=(0.004, 0.018, 0.024), foam=True):
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
    ob = bpy.context.active_object
    ob.name = 'sea'
    mod = ob.modifiers.new('ocean', 'OCEAN')
    mod.geometry_mode = 'GENERATE'
    mod.repeat_x = 3
    mod.repeat_y = 3
    mod.spatial_size = int(size / 3)
    mod.resolution = res
    mod.wave_scale = wave_scale
    mod.choppiness = chop
    mod.wind_velocity = wind
    mod.use_normals = True
    if foam:
        mod.use_foam = True
        mod.foam_layer_name = 'foam'
        mod.foam_coverage = 0.35
    ob.location = (-size / 2, -size / 2, 0)
    m, nt, b = props.new_mat('sea_mat')
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = 0.035
    b.inputs['IOR'].default_value = 1.333
    b.inputs['Subsurface Weight'].default_value = 0.0
    if foam:
        at = nt.nodes.new('ShaderNodeAttribute')
        at.attribute_name = 'foam'
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[1].position = 0.9
        nt.links.new(at.outputs['Fac'], ramp.inputs['Fac'])
        mixc = nt.nodes.new('ShaderNodeMixRGB')
        mixc.inputs['Color1'].default_value = (*color, 1)
        mixc.inputs['Color2'].default_value = (0.55, 0.6, 0.62, 1)
        nt.links.new(ramp.outputs['Color'], mixc.inputs['Fac'])
        nt.links.new(mixc.outputs['Color'], b.inputs['Base Color'])
        rr = nt.nodes.new('ShaderNodeMapRange')
        rr.inputs['To Min'].default_value = 0.035
        rr.inputs['To Max'].default_value = 0.6
        nt.links.new(ramp.outputs['Color'], rr.inputs['Value'])
        nt.links.new(rr.outputs['Result'], b.inputs['Roughness'])
    ob.data.materials.append(m)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob, mod


def add_ripples(m, scale=45.0, strength=0.3):
    """Small wind ripples on top of the simulated swell (bump)."""
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    noi = nt.nodes.new('ShaderNodeTexNoise')
    noi.inputs['Scale'].default_value = scale
    noi.inputs['Detail'].default_value = 6.0
    nt.links.new(tc.outputs['Object'], noi.inputs['Vector'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = strength
    nt.links.new(noi.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])


def hdri_world(name, strength=1.0, rot_z=0.0, tint=(1, 1, 1), sat=1.0):
    w = props.world_hdri(f'{HDRI}/{name}', strength=strength, rot_z=rot_z)
    nt = w.node_tree
    env = [n for n in nt.nodes if n.type == 'TEX_ENVIRONMENT'][0]
    bg = [n for n in nt.nodes if n.type == 'BACKGROUND'][0]
    hsv = nt.nodes.new('ShaderNodeHueSaturation')
    hsv.inputs['Saturation'].default_value = sat
    mul = nt.nodes.new('ShaderNodeMixRGB')
    mul.blend_type = 'MULTIPLY'
    mul.inputs['Fac'].default_value = 1.0
    mul.inputs['Color2'].default_value = (*tint, 1)
    nt.links.new(env.outputs['Color'], hsv.inputs['Color'])
    nt.links.new(hsv.outputs['Color'], mul.inputs['Color1'])
    nt.links.new(mul.outputs['Color'], bg.inputs['Color'])
    mp = [n for n in nt.nodes if n.type == 'MAPPING'][0]
    return w, mp


@shot('ocean_storm', 96, spp=8)
def ocean_storm(ctx, i, t):
    """'If someone says the ocean is small...'  Heavy black water under a bruised overcast."""
    if i is None:
        ctx.w, ctx.mp = hdri_world('kloofendal_overcast_puresky_2k.hdr', strength=0.22, rot_z=-0.4,
                                   tint=(0.62, 0.72, 0.95), sat=0.3)
        ctx.sea, ctx.ocean = sea(wave_scale=2.2, chop=1.5, wind=22.0, res=16, color=(0.0015, 0.006, 0.009), foam=False)
        add_ripples(ctx.sea.data.materials[0], strength=0.35)
        return
    ctx.ocean.time = 5.0 + t * 1.0
    p = ease(t / 4.0)
    cam(ctx, lerp3((0.0, -6.0, 1.1), (0.0, -4.8, 0.9), p), (0.0, 30.0, 1.2), lens=28, fstop=None)
    ctx.cam.rotation_euler.y += 0.035 * math.sin(t * 0.9)


@shot('sunrise', 96, spp=8)
def sunrise(ctx, i, t):
    """'...does the sun stop shining?'  The sun climbs off the horizon; the sea turns to fire."""
    if i is None:
        ctx.w, ctx.mp = hdri_world('qwantani_sunrise_puresky_2k.hdr', strength=1.0, rot_z=-2.201, sat=1.25,
                                   tint=(1.0, 0.85, 0.7))
        ctx.sea, ctx.ocean = sea(wave_scale=0.6, chop=0.9, wind=8.0, res=13, color=(0.003, 0.010, 0.016), foam=False)
        return
    ctx.ocean.time = 2.0 + t * 0.6
    # tilt the sky so the sun climbs ~3 degrees over the shot
    ctx.mp.inputs['Rotation'].default_value = (math.radians(lerp(2.5, -1.5, ease(t / 4.0))), 0, -2.201)
    cam(ctx, (0.0, 0.0, 1.6), (0.0, 60.0, 2.4), lens=50, fstop=None)


@shot('sunrise_wide', 96, spp=8)
def sunrise_wide(ctx, i, t):
    """'I lived?'  Wide golden ocean, clouds on fire, drifting forward."""
    if i is None:
        ctx.w, ctx.mp = hdri_world('industrial_sunset_02_puresky_2k.hdr', strength=1.0, rot_z=-2.198, sat=1.3,
                                   tint=(1.0, 0.82, 0.62))
        ctx.sea, ctx.ocean = sea(wave_scale=0.9, chop=1.0, wind=10.0, res=13, color=(0.003, 0.010, 0.016), foam=False)
        return
    ctx.ocean.time = 3.0 + t * 0.6
    p = ease(t / 4.0)
    cam(ctx, lerp3((0.0, -2.0, 2.6), (0.0, 2.0, 3.4), p), (0.0, 80.0, 4.0), lens=24, fstop=None)


# ---------------------------------------------------------------- the lone tree
def build_tree(seed=4, levels=4):
    """Procedural broadleaf: tapered branch tubes (curves) + leaf cards. Returns (branch_obj, leaf_obj)."""
    rng = np.random.default_rng(seed)
    cu = bpy.data.curves.new('tree', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = 1.0
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    leaves = []

    def grow(p0, d, length, radius, lvl):
        n = 6
        pts = []
        d = mathutils.Vector(d).normalized()
        p = mathutils.Vector(p0)
        for k in range(n + 1):
            f = k / n
            pts.append((p.copy(), radius * (1 - 0.65 * f)))
            bend = mathutils.Vector(rng.normal(0, 0.12, 3)) + mathutils.Vector((0, 0, 0.05 if lvl < 2 else -0.04))
            d = (d + bend).normalized()
            p = p + d * (length / n)
        sp = cu.splines.new('POLY')
        sp.points.add(len(pts) - 1)
        for k, (q, r) in enumerate(pts):
            sp.points[k].co = (q.x, q.y, q.z, 1)
            sp.points[k].radius = r
        if lvl >= levels:
            for k in range(3, len(pts)):
                for _ in range(10):
                    leaves.append(pts[k][0] + mathutils.Vector(rng.normal(0, 0.35 * length, 3)))
            return
        nkids = 4 if lvl == 0 else 3
        for c in range(nkids):
            f = 0.35 + 0.6 * (c + rng.uniform(0, 0.8)) / nkids
            q = pts[int(f * n)][0]
            yaw = rng.uniform(0, 2 * math.pi)
            pitch = math.radians(rng.uniform(35, 60))
            base_dir = mathutils.Vector((math.cos(yaw) * math.sin(pitch), math.sin(yaw) * math.sin(pitch),
                                         math.cos(pitch)))
            nd = (base_dir + d * 0.4).normalized()
            grow(q, nd, length * rng.uniform(0.55, 0.7), radius * 0.5, lvl + 1)

    grow((0, 0, -0.2), (0.05, 0, 1), 3.4, 0.28, 0)
    br = bpy.data.objects.new('tree_branches', cu)
    bpy.context.scene.collection.objects.link(br)
    m, nt, b = props.new_mat('bark')
    b.inputs['Base Color'].default_value = (0.03, 0.022, 0.016, 1)
    b.inputs['Roughness'].default_value = 0.9
    cu.materials.append(m)
    # leaf cards: one mesh, random orientation
    verts, faces, uvs = [], [], []
    for c in leaves:
        s = rng.uniform(0.07, 0.12)
        ax = mathutils.Vector(rng.normal(0, 1, 3)).normalized()
        up = mathutils.Vector(rng.normal(0, 1, 3)).normalized().cross(ax).normalized()
        k = len(verts)
        for a, b_ in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            v = c + ax * (a * s * 0.5) + up * (b_ * s)
            verts.append(tuple(v))
        faces.append((k, k + 1, k + 2, k + 3))
        uvs += [(0, 0), (1, 0), (1, 1), (0, 1)]
    me = props.make_mesh('leaves', verts, faces, uvs, smooth_shade=False)
    lm, nt, b = props.new_mat('leaf')
    b.inputs['Base Color'].default_value = (0.03, 0.06, 0.012, 1)
    b.inputs['Roughness'].default_value = 0.55
    tr = nt.nodes.new('ShaderNodeBsdfTranslucent')
    tr.inputs['Color'].default_value = (0.12, 0.2, 0.02, 1)
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = 0.4
    nt.links.new(b.outputs['BSDF'], mix.inputs[1])
    nt.links.new(tr.outputs['BSDF'], mix.inputs[2])
    # leaf silhouette (ellipse) via UV distance -> alpha
    uv = nt.nodes.new('ShaderNodeUVMap')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(uv.outputs['UV'], sep.inputs['Vector'])
    dx = nt.nodes.new('ShaderNodeMath')
    dx.operation = 'SUBTRACT'
    dx.inputs[1].default_value = 0.5
    nt.links.new(sep.outputs['X'], dx.inputs[0])
    dy = nt.nodes.new('ShaderNodeMath')
    dy.operation = 'SUBTRACT'
    dy.inputs[1].default_value = 0.5
    nt.links.new(sep.outputs['Y'], dy.inputs[0])
    vl = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(dx.outputs['Value'], vl.inputs['X'])
    nt.links.new(dy.outputs['Value'], vl.inputs['Y'])
    ln = nt.nodes.new('ShaderNodeVectorMath')
    ln.operation = 'LENGTH'
    nt.links.new(vl.outputs['Vector'], ln.inputs[0])
    lt = nt.nodes.new('ShaderNodeMath')
    lt.operation = 'LESS_THAN'
    lt.inputs[1].default_value = 0.48
    nt.links.new(ln.outputs['Value'], lt.inputs[0])
    trn = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix2 = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lt.outputs['Value'], mix2.inputs['Fac'])
    nt.links.new(trn.outputs['BSDF'], mix2.inputs[1])
    nt.links.new(mix.outputs['Shader'], mix2.inputs[2])
    nt.links.new(mix2.outputs['Shader'], nt.nodes['Material Output'].inputs['Surface'])
    lo = props.link_obj('leaves', me, lm)
    return br, lo, np.array(verts)


def hill(coll=None):
    import bmesh
    me = bpy.data.meshes.new('hill')
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=120, y_segments=120, size=40)
    for v in bm.verts:
        x, y = v.co.x, v.co.y
        r = math.hypot(x, y - 6)
        v.co.z = 2.2 * math.exp(-(r / 14) ** 2) - 2.2 + 0.08 * math.sin(x * 1.3) * math.cos(y * 0.9)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    m, nt, b = props.new_mat('grass')
    b.inputs['Base Color'].default_value = (0.012, 0.016, 0.006, 1)
    b.inputs['Roughness'].default_value = 0.95
    ob = props.link_obj('hill', me, m, coll)
    ob.location = (0, -6, 0)
    return ob


@shot('tree_storm', 96, spp=8)
def tree_storm(ctx, i, t):
    """'If someone says the tree is ugly... does the tree stop growing?'  Lone tree, burning sky behind."""
    if i is None:
        ctx.w, ctx.mp = hdri_world('belfast_sunset_puresky_2k.hdr', strength=1.4, rot_z=-2.232 + 0.12, sat=1.35,
                                   tint=(1.0, 0.75, 0.6))
        hill()
        ctx.br, ctx.lv, ctx.lv0 = build_tree()
        ld = bpy.data.lights.new('rim_sun', 'SUN')
        ld.energy = 3.0
        ld.color = (1.0, 0.55, 0.3)
        ld.angle = math.radians(1.0)
        s = bpy.data.objects.new('rim_sun', ld)
        bpy.context.scene.collection.objects.link(s)
        s.rotation_euler = mathutils.Vector((0.1, -1.0, -0.06)).to_track_quat('-Z', 'Y').to_euler()
        return
    # wind: leaves sway with height
    v = ctx.lv0.copy()
    h = np.clip(v[:, 2] / 4.0, 0, 1)
    v[:, 0] += 0.05 * h * np.sin(t * 2.3 + v[:, 1] * 1.7) + 0.02 * np.sin(t * 7 + v[:, 2] * 5)
    v[:, 1] += 0.03 * h * np.sin(t * 1.9 + v[:, 0] * 1.3)
    ctx.lv.data.vertices.foreach_set('co', v.astype(np.float32).ravel())
    ctx.lv.data.update()
    ctx.br.rotation_euler = (0.01 * math.sin(t * 1.1), 0.012 * math.sin(t * 0.9), 0)
    ctx.mp.inputs['Rotation'].default_value = (0, 0, -2.232 + 0.12 + t * 0.004)
    p = ease(t / 4.0)
    cam(ctx, lerp3((0.5, -8.5, -0.6), (0.3, -7.2, -0.4), p), (0.0, 0.0, 2.0), lens=35, fstop=None)


# ---------------------------------------------------------------- the shelf of cups
@shot('shelf', 96, spp=8)
def shelf(ctx, i, t):
    """'How many people live like that?  There is a lot.'  Night pet store: row after row of cups."""
    if i is None:
        sets.black_world()
        wood = props.wood_material('shelf_wood', darken=0.2)
        ctx.cups = []
        base = props.Cup(**shots.CUP_KW)
        fishes = []
        for k in range(3):
            f = Betta(sets.TEX, name=f'b{k}')
            f.root.scale = (shots.FISH_SCALE,) * 3
            for q in range(30):
                f.pose(q / 24.0 + k, swim=0.25, freq=0.8 + 0.2 * k, flare=0.3 + 0.2 * k, turn=0.4 - 0.3 * k,
                       dt=1 / 24.0)
            fishes.append(f)
        rows, cols, dx, dz = 3, 7, 0.11, 0.2
        for r in range(rows):
            board = props.plane(f'board{r}', 1.1, 0.24, (0.3, 0.0, r * dz - 0.002), (0, 0, 0), wood)
            for c in range(cols):
                x = c * dx - 0.03
                z = r * dz
                if r == 0 and c == 0:
                    root = base.root
                else:
                    root = bpy.data.objects.new(f'cup_{r}_{c}', None)
                    bpy.context.scene.collection.objects.link(root)
                    for src in (base.glass, base.water):
                        dup = bpy.data.objects.new(f'{src.name}_{r}_{c}', src.data)
                        bpy.context.scene.collection.objects.link(dup)
                        dup.parent = root
                root.location = (x, 0.0, z)
                # which fish, facing where
                f = fishes[(r * 7 + c * 3) % 3]
                froot = bpy.data.objects.new(f'fishinst_{r}_{c}', None)
                bpy.context.scene.collection.objects.link(froot)
                for ob in f.objs.values():
                    d = bpy.data.objects.new(f'{ob.name}_{r}_{c}', ob.data)
                    bpy.context.scene.collection.objects.link(d)
                    d.parent = froot
                for side, eo in f.eyes:
                    d = bpy.data.objects.new(f'{eo.name}_{r}_{c}', eo.data)
                    bpy.context.scene.collection.objects.link(d)
                    d.parent = froot
                    d.location, d.rotation_euler, d.scale = eo.location, eo.rotation_euler, eo.scale
                froot.location = (x + 0.004 * ((c * 7) % 3 - 1), 0.004 * ((c * 5) % 3 - 1), z + 0.05 + 0.006 * (c % 2))
                froot.rotation_euler = (0, 0, math.radians((r * 97 + c * 61) % 360))
                froot.scale = (shots.FISH_SCALE,) * 3
                ctx.cups.append(root)
        for f in fishes:  # originals parked out of shot
            f.root.location = (0, 0, -5)
        # flickering fluorescent tube above the aisle + cold bounce
        ctx.tube = props.area_light('tube', (0.3, -0.3, 0.8), (math.radians(40), 0, 0), 1.4, 110.0, (0.8, 0.95, 1.0),
                                    size_y=0.05)
        props.area_light('fill', (0.3, -1.2, 0.3), (math.radians(80), 0, 0), 1.0, 4.0, (0.3, 0.45, 0.7))
        return
    fl = 1.0 if (int(t * 24) % 37) not in (5, 6, 19) else 0.25
    ctx.tube.data.energy = 110.0 * fl
    p = ease(t / 4.0)
    cam(ctx, lerp3((-0.05, -0.62, 0.30), (0.55, -0.58, 0.26), p), lerp3((0.15, 0.0, 0.22), (0.62, 0.0, 0.2), p),
        lens=40, fstop=5.6)


# ---------------------------------------------------------------- space
def star_world(density=0.9, strength=1.0):
    w = bpy.context.scene.world or bpy.data.worlds.new('World')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for x in list(nt.nodes):
        nt.nodes.remove(x)
    out = nt.nodes.new('ShaderNodeOutputWorld')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    acc = None
    for scale, thr, gain in ((180.0, 0.035, 3.0), (420.0, 0.025, 1.6), (900.0, 0.02, 0.8)):
        vor = nt.nodes.new('ShaderNodeTexVoronoi')
        vor.inputs['Scale'].default_value = scale
        nt.links.new(tc.outputs['Generated'], vor.inputs['Vector'])
        lt = nt.nodes.new('ShaderNodeMath')
        lt.operation = 'LESS_THAN'
        lt.inputs[1].default_value = thr * density
        nt.links.new(vor.outputs['Distance'], lt.inputs[0])
        g = nt.nodes.new('ShaderNodeMath')
        g.operation = 'MULTIPLY'
        g.inputs[1].default_value = gain
        nt.links.new(lt.outputs['Value'], g.inputs[0])
        g2 = nt.nodes.new('ShaderNodeMath')
        g2.operation = 'MULTIPLY'
        nt.links.new(g.outputs['Value'], g2.inputs[0])
        nt.links.new(vor.outputs['Color'], g2.inputs[1])  # random brightness per star (uses R channel)
        if acc is None:
            acc = g2
        else:
            ad = nt.nodes.new('ShaderNodeMath')
            ad.operation = 'ADD'
            nt.links.new(acc.outputs['Value'], ad.inputs[0])
            nt.links.new(g2.outputs['Value'], ad.inputs[1])
            acc = ad
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.9, 0.93, 1.0, 1)
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = strength
    nt.links.new(acc.outputs['Value'], mul.inputs[0])
    nt.links.new(mul.outputs['Value'], bg.inputs['Strength'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    return w


def earth(sun_dir=(-1.0, -0.35, 0.15)):
    import bmesh
    E = '/opt/assets/earth'

    def sphere(name, r, seg=160):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bm.loops.layers.uv.new('UVMap')
        bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r, calc_uvs=True)
        bm.to_mesh(me)
        bm.free()
        me.shade_smooth()
        return me

    sdir = mathutils.Vector(sun_dir).normalized()
    # ground: day albedo, night lights on the dark side
    m, nt, b = props.new_mat('earth')
    day = nt.nodes.new('ShaderNodeTexImage')
    day.image = bpy.data.images.load(f'{E}/day.jpg', check_existing=True)
    night = nt.nodes.new('ShaderNodeTexImage')
    night.image = bpy.data.images.load(f'{E}/night.jpg', check_existing=True)
    nt.links.new(day.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.7
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    dot = nt.nodes.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    dot.inputs[1].default_value = tuple(-sdir)
    nt.links.new(geo.outputs['Normal'], dot.inputs[0])
    dark = nt.nodes.new('ShaderNodeMapRange')
    dark.inputs['From Min'].default_value = 0.0
    dark.inputs['From Max'].default_value = 0.25
    nt.links.new(dot.outputs['Value'], dark.inputs['Value'])
    nm = nt.nodes.new('ShaderNodeMath')
    nm.operation = 'MULTIPLY'
    nm.inputs[1].default_value = 3.0
    nt.links.new(dark.outputs['Result'], nm.inputs[0])
    lum = nt.nodes.new('ShaderNodeRGBToBW')
    nt.links.new(night.outputs['Color'], lum.inputs['Color'])
    nm2 = nt.nodes.new('ShaderNodeMath')
    nm2.operation = 'MULTIPLY'
    nt.links.new(lum.outputs['Val'], nm2.inputs[0])
    nt.links.new(nm.outputs['Value'], nm2.inputs[1])
    b.inputs['Emission Color'].default_value = (1.0, 0.62, 0.3, 1)
    nt.links.new(nm2.outputs['Value'], b.inputs['Emission Strength'])
    ground = props.link_obj('earth', sphere('earth', 1.0), m)
    # clouds
    cm, nt, b = props.new_mat('clouds')
    cl = nt.nodes.new('ShaderNodeTexImage')
    cl.image = bpy.data.images.load(f'{E}/clouds.jpg', check_existing=True)
    b.inputs['Base Color'].default_value = (1, 1, 1, 1)
    b.inputs['Roughness'].default_value = 1.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    bw = nt.nodes.new('ShaderNodeRGBToBW')
    nt.links.new(cl.outputs['Color'], bw.inputs['Color'])
    nt.links.new(bw.outputs['Val'], mix.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mix.inputs[1])
    nt.links.new(b.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], nt.nodes['Material Output'].inputs['Surface'])
    clouds = props.link_obj('clouds', sphere('clouds', 1.008), cm)
    # atmosphere rim
    am = bpy.data.materials.new('atmo')
    am.use_nodes = True
    nt = am.node_tree
    for x in list(nt.nodes):
        nt.nodes.remove(x)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    lw = nt.nodes.new('ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.35
    pw = nt.nodes.new('ShaderNodeMath')
    pw.operation = 'POWER'
    pw.inputs[1].default_value = 3.0
    nt.links.new(lw.outputs['Facing'], pw.inputs[0])
    # only on the sunlit side
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    dot = nt.nodes.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    dot.inputs[1].default_value = tuple(-sdir)
    nt.links.new(geo.outputs['Normal'], dot.inputs[0])
    lit = nt.nodes.new('ShaderNodeMapRange')
    lit.inputs['From Min'].default_value = -0.3
    lit.inputs['From Max'].default_value = 0.4
    nt.links.new(dot.outputs['Value'], lit.inputs['Value'])
    m2 = nt.nodes.new('ShaderNodeMath')
    m2.operation = 'MULTIPLY'
    nt.links.new(pw.outputs['Value'], m2.inputs[0])
    nt.links.new(lit.outputs['Result'], m2.inputs[1])
    m3 = nt.nodes.new('ShaderNodeMath')
    m3.operation = 'MULTIPLY'
    m3.inputs[1].default_value = 6.0
    nt.links.new(m2.outputs['Value'], m3.inputs[0])
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.25, 0.5, 1.0, 1)
    nt.links.new(m3.outputs['Value'], em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    add = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(em.outputs['Emission'], add.inputs[0])
    nt.links.new(tr.outputs['BSDF'], add.inputs[1])
    nt.links.new(add.outputs['Shader'], out.inputs['Surface'])
    atmo = props.link_obj('atmo', sphere('atmo', 1.03, 96), am)
    ld = bpy.data.lights.new('sun_space', 'SUN')
    ld.energy = 4.5
    ld.angle = math.radians(0.5)
    sun = bpy.data.objects.new('sun_space', ld)
    bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = sdir.to_track_quat('-Z', 'Y').to_euler()
    return ground, clouds, atmo


@shot('earth_turn', 144, spp=12)
def earth_turn(ctx, i, t):
    """Nine million years: the planet turns, the city lights crawl across the night side."""
    if i is None:
        star_world(strength=1.0)
        ctx.g, ctx.c, ctx.a = earth()
        return
    ctx.g.rotation_euler = (math.radians(23.4), 0, t * 0.35)
    ctx.c.rotation_euler = (math.radians(23.4), 0, t * 0.39)
    p = ease(t / 6.0)
    cam(ctx, lerp3((0.25, -2.3, 0.55), (0.55, -3.2, 0.8), p), (0.0, 0.0, 0.15), lens=35, fstop=None)


def galaxy_disc():
    import bmesh
    me = bpy.data.meshes.new('galaxy')
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
    bm.to_mesh(me)
    bm.free()
    m = bpy.data.materials.new('galaxy')
    m.use_nodes = True
    nt = m.node_tree
    for x in list(nt.nodes):
        nt.nodes.remove(x)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
    # polar coords
    r = nt.nodes.new('ShaderNodeVectorMath')
    r.operation = 'LENGTH'
    nt.links.new(tc.outputs['Object'], r.inputs[0])
    ang = nt.nodes.new('ShaderNodeMath')
    ang.operation = 'ARCTAN2'
    nt.links.new(sep.outputs['Y'], ang.inputs[0])
    nt.links.new(sep.outputs['X'], ang.inputs[1])
    lnr = nt.nodes.new('ShaderNodeMath')
    lnr.operation = 'LOGARITHM'
    lnr.inputs[1].default_value = 2.718
    nt.links.new(r.outputs['Value'], lnr.inputs[0])
    tw = nt.nodes.new('ShaderNodeMath')
    tw.operation = 'MULTIPLY'
    tw.inputs[1].default_value = 4.2
    nt.links.new(lnr.outputs['Value'], tw.inputs[0])
    a2 = nt.nodes.new('ShaderNodeMath')
    a2.operation = 'MULTIPLY'
    a2.inputs[1].default_value = 2.0
    nt.links.new(ang.outputs['Value'], a2.inputs[0])
    arg = nt.nodes.new('ShaderNodeMath')
    arg.operation = 'SUBTRACT'
    nt.links.new(a2.outputs['Value'], arg.inputs[0])
    nt.links.new(tw.outputs['Value'], arg.inputs[1])
    sn = nt.nodes.new('ShaderNodeMath')
    sn.operation = 'COSINE'
    nt.links.new(arg.outputs['Value'], sn.inputs[0])
    arms = nt.nodes.new('ShaderNodeMapRange')
    arms.inputs['From Min'].default_value = 0.2
    arms.inputs['From Max'].default_value = 1.0
    nt.links.new(sn.outputs['Value'], arms.inputs['Value'])
    noi = nt.nodes.new('ShaderNodeTexNoise')
    noi.inputs['Scale'].default_value = 16.0
    noi.inputs['Detail'].default_value = 10.0
    noi.inputs['Roughness'].default_value = 0.65
    nt.links.new(tc.outputs['Object'], noi.inputs['Vector'])
    armn = nt.nodes.new('ShaderNodeMath')
    armn.operation = 'MULTIPLY'
    nt.links.new(arms.outputs['Result'], armn.inputs[0])
    nt.links.new(noi.outputs['Fac'], armn.inputs[1])
    fall = nt.nodes.new('ShaderNodeMapRange')
    fall.inputs['From Min'].default_value = 0.0
    fall.inputs['From Max'].default_value = 0.5
    fall.inputs['To Min'].default_value = 1.0
    fall.inputs['To Max'].default_value = 0.0
    nt.links.new(r.outputs['Value'], fall.inputs['Value'])
    body = nt.nodes.new('ShaderNodeMath')
    body.operation = 'MULTIPLY'
    nt.links.new(armn.outputs['Value'], body.inputs[0])
    nt.links.new(fall.outputs['Result'], body.inputs[1])
    core = nt.nodes.new('ShaderNodeMath')
    core.operation = 'POWER'
    core.inputs[1].default_value = 6.0
    nt.links.new(fall.outputs['Result'], core.inputs[0])
    col_arm = nt.nodes.new('ShaderNodeEmission')
    col_arm.inputs['Color'].default_value = (0.55, 0.7, 1.0, 1)
    b2 = nt.nodes.new('ShaderNodeMath')
    b2.operation = 'MULTIPLY'
    b2.inputs[1].default_value = 3.0
    nt.links.new(body.outputs['Value'], b2.inputs[0])
    nt.links.new(b2.outputs['Value'], col_arm.inputs['Strength'])
    col_core = nt.nodes.new('ShaderNodeEmission')
    col_core.inputs['Color'].default_value = (1.0, 0.8, 0.55, 1)
    c2 = nt.nodes.new('ShaderNodeMath')
    c2.operation = 'MULTIPLY'
    c2.inputs[1].default_value = 12.0
    nt.links.new(core.outputs['Value'], c2.inputs[0])
    nt.links.new(c2.outputs['Value'], col_core.inputs['Strength'])
    add = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(col_arm.outputs['Emission'], add.inputs[0])
    nt.links.new(col_core.outputs['Emission'], add.inputs[1])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    add2 = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(add.outputs['Shader'], add2.inputs[0])
    nt.links.new(tr.outputs['BSDF'], add2.inputs[1])
    nt.links.new(add2.outputs['Shader'], out.inputs['Surface'])
    ob = props.link_obj('galaxy', me, m)
    ob.scale = (60, 60, 60)
    return ob


@shot('galaxy', 144, spp=8)
def galaxy(ctx, i, t):
    """One million. Nine million. A billion. A trillion.  Pull back until the numbers stop meaning anything."""
    if i is None:
        star_world(strength=1.2)
        ctx.gal = galaxy_disc()
        ctx.gal.rotation_euler = (math.radians(62), 0, 0)
        return
    ctx.gal.rotation_euler = (math.radians(62), 0, t * 0.03)
    p = ease(t / 6.0)
    cam(ctx, lerp3((0.0, -26.0, 8.0), (0.0, -70.0, 22.0), p), (0.0, 0.0, 0.0), lens=35, fstop=None)
