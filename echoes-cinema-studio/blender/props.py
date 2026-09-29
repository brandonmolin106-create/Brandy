"""Set pieces for the thriller cut: glass cup + water (animated surface), table, room, lamp, blinds, rain window.

All geometry is generated procedurally with numpy; materials are Cycles node trees.
"""
import math

import bpy
import numpy as np

from betta import make_mesh


# ------------------------------------------------------------------ helpers
def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree, m.node_tree.nodes['Principled BSDF']


def link(nt, a, b):
    nt.links.new(a, b)


def node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n


def lathe(profile, seg=160, name='lathe'):
    """Revolve (r, z) polyline around Z. Points with r == 0 become single pole vertices. Returns (verts, faces,
    ring_index) where ring_index[i] = list of vertex ids for profile point i."""
    verts, rings = [], []
    ang = np.arange(seg) / seg * 2 * np.pi
    for r, z in profile:
        if r <= 1e-9:
            rings.append([len(verts)])
            verts.append((0.0, 0.0, z))
        else:
            ids = list(range(len(verts), len(verts) + seg))
            verts += [(r * math.cos(a), r * math.sin(a), z) for a in ang]
            rings.append(ids)
    faces = []
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        if len(a) == 1 and len(b) == 1:
            continue
        for j in range(seg):
            j1 = (j + 1) % seg
            if len(a) == 1:
                faces.append((a[0], b[j], b[j1]))
            elif len(b) == 1:
                faces.append((a[j], b[0], a[j1]))
            else:
                faces.append((a[j], b[j], b[j1], a[j1]))
    return verts, faces, rings


def fix_normals(me):
    """Make a closed mesh's normals point outward (the lathe winding depends on the profile direction)."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()


def arc(cx, cz, r, a0, a1, n):
    return [(cx + r * math.cos(a), cz + r * math.sin(a)) for a in np.linspace(a0, a1, n)]


# ------------------------------------------------------------------ materials
VOLUMES = __import__('os').environ.get('VOL', '0') == '1'


def shadow_pass_through(m, tint=(0.92, 0.95, 0.95)):
    """Let shadow rays pass straight through a refractive material (light reaches the fish inside the water;
    cheap stand-in for caustics, which are off for render budget)."""
    nt = m.node_tree
    out = nt.nodes['Material Output']
    src = out.inputs['Surface'].links[0].from_socket
    lp = nt.nodes.new('ShaderNodeLightPath')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    tr.inputs['Color'].default_value = (*tint, 1)
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Shadow Ray'], mix.inputs['Fac'])
    nt.links.new(src, mix.inputs[1])
    nt.links.new(tr.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    return m


def glass_material(name='glass', tint=(0.93, 0.98, 0.965), smudge=True):
    m, nt, b = new_mat(name)
    b.inputs['Base Color'].default_value = (0.97, 0.995, 0.99, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.5
    b.inputs['Roughness'].default_value = 0.0
    if smudge:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        noi = node(nt, 'ShaderNodeTexNoise', Scale=38.0, Detail=2.0, Roughness=0.6)
        link(nt, tc.outputs['Object'], noi.inputs['Vector'])
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.52
        ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1)
        ramp.color_ramp.elements[1].position = 0.75
        ramp.color_ramp.elements[1].color = (0.09, 0.09, 0.09, 1)
        link(nt, noi.outputs['Fac'], ramp.inputs['Fac'])
        link(nt, ramp.outputs['Color'], b.inputs['Roughness'])
        # fine scratches as bump
        wav = node(nt, 'ShaderNodeTexWave', Scale=160.0, Distortion=14.0, Detail=1.0)
        wav.wave_type = 'BANDS'
        link(nt, tc.outputs['Object'], wav.inputs['Vector'])
        bump = node(nt, 'ShaderNodeBump', Strength=0.015, Distance=0.00005)
        link(nt, wav.outputs['Fac'], bump.inputs['Height'])
        link(nt, bump.outputs['Normal'], b.inputs['Normal'])
    if VOLUMES:
        vol = nt.nodes.new('ShaderNodeVolumeAbsorption')
        vol.inputs['Color'].default_value = (*tint, 1)
        vol.inputs['Density'].default_value = 6.0
        link(nt, vol.outputs['Volume'], nt.nodes['Material Output'].inputs['Volume'])
    return m


def water_material(name='water', tint=(0.86, 0.95, 0.93), density=4.0, murk=0.0):
    m, nt, b = new_mat(name)
    b.inputs['Base Color'].default_value = (*tint, 1) if not VOLUMES else (1, 1, 1, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.333
    b.inputs['Roughness'].default_value = 0.0
    out = nt.nodes['Material Output']
    if not VOLUMES and murk <= 0:
        return m
    vol = nt.nodes.new('ShaderNodeVolumeAbsorption')
    vol.inputs['Color'].default_value = (*tint, 1)
    vol.inputs['Density'].default_value = density
    if murk > 0:
        sc = nt.nodes.new('ShaderNodeVolumeScatter')
        sc.inputs['Density'].default_value = murk
        sc.inputs['Anisotropy'].default_value = 0.6
        add = nt.nodes.new('ShaderNodeAddShader')
        link(nt, vol.outputs['Volume'], add.inputs[0])
        link(nt, sc.outputs['Volume'], add.inputs[1])
        link(nt, add.outputs['Shader'], out.inputs['Volume'])
    else:
        link(nt, vol.outputs['Volume'], out.inputs['Volume'])
    return m


def wood_material(name='table_wood', tex='/opt/assets/tex/black_walnut_veneer_02', scale=1.6, darken=0.3):
    """Scanned black-walnut veneer (Poly Haven, CC0): diffuse + roughness + normal, projected from above."""
    m, nt, b = new_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    link(nt, tc.outputs['Object'], mp.inputs['Vector'])
    base = tex.rsplit('/', 1)[1]

    def img(kind, cs):
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(f'{tex}_{kind}_2k.jpg'.replace(f'/{base}_', f'/{base}_'), check_existing=True)
        n.image.colorspace_settings.name = cs
        n.interpolation = 'Linear'
        link(nt, mp.outputs['Vector'], n.inputs['Vector'])
        return n
    d = img('diff', 'sRGB')
    r = img('rough', 'Non-Color')
    nm = img('nor_gl', 'Non-Color')
    mul = nt.nodes.new('ShaderNodeMixRGB')
    mul.blend_type = 'MULTIPLY'
    mul.inputs['Fac'].default_value = 1.0
    mul.inputs['Color2'].default_value = (darken, darken, darken, 1)
    link(nt, d.outputs['Color'], mul.inputs['Color1'])
    link(nt, mul.outputs['Color'], b.inputs['Base Color'])
    rr = nt.nodes.new('ShaderNodeMapRange')
    rr.inputs['To Min'].default_value = 0.22
    rr.inputs['To Max'].default_value = 0.6
    link(nt, r.outputs['Color'], rr.inputs['Value'])
    link(nt, rr.outputs['Result'], b.inputs['Roughness'])
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nmap.inputs['Strength'].default_value = 0.8
    link(nt, nm.outputs['Color'], nmap.inputs['Color'])
    link(nt, nmap.outputs['Normal'], b.inputs['Normal'])
    return m


def plaster_material(name='wall', color=(0.05, 0.052, 0.055)):
    m, nt, b = new_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    noi = node(nt, 'ShaderNodeTexNoise', Scale=6.0, Detail=2.0, Roughness=0.5)
    link(nt, tc.outputs['Object'], noi.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (color[0] * 0.6, color[1] * 0.6, color[2] * 0.6, 1)
    ramp.color_ramp.elements[1].color = (color[0] * 1.4, color[1] * 1.4, color[2] * 1.4, 1)
    link(nt, noi.outputs['Fac'], ramp.inputs['Fac'])
    link(nt, ramp.outputs['Color'], b.inputs['Base Color'])
    bump = node(nt, 'ShaderNodeBump', Strength=0.25, Distance=0.002)
    link(nt, noi.outputs['Fac'], bump.inputs['Height'])
    link(nt, bump.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.85
    return m


def emission_material(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for x in list(nt.nodes):
        nt.nodes.remove(x)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*color, 1)
    em.inputs['Strength'].default_value = strength
    link(nt, em.outputs['Emission'], out.inputs['Surface'])
    return m


def rain_glass_material(name='rain_window'):
    """Window pane with beaded rain drops + streaks (refraction via bump on thin glass)."""
    m, nt, b = new_mat(name)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.33
    b.inputs['Roughness'].default_value = 0.02
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vor = node(nt, 'ShaderNodeTexVoronoi', Scale=160.0, Randomness=1.0)
    vor.feature = 'F1'
    link(nt, tc.outputs['Object'], vor.inputs['Vector'])
    drop = nt.nodes.new('ShaderNodeMapRange')
    drop.inputs['From Min'].default_value = 0.0
    drop.inputs['From Max'].default_value = 0.35
    drop.inputs['To Min'].default_value = 1.0
    drop.inputs['To Max'].default_value = 0.0
    link(nt, vor.outputs['Distance'], drop.inputs['Value'])
    bump = node(nt, 'ShaderNodeBump', Strength=1.0, Distance=0.004)
    link(nt, drop.outputs['Result'], bump.inputs['Height'])
    link(nt, bump.outputs['Normal'], b.inputs['Normal'])
    return m


# ------------------------------------------------------------------ objects
def link_obj(name, me, mat=None, coll=None):
    ob = bpy.data.objects.new(name, me)
    if mat is not None:
        me.materials.append(mat)
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


class Cup:
    """Heavy-bottomed glass tumbler with a separate water volume whose surface can ripple."""

    def __init__(self, r_bottom=0.036, r_top=0.043, height=0.108, wall=0.0026, base=0.013, fill=0.78, name='cup',
                 coll=None, seg=160, water_tint=(0.86, 0.95, 0.93)):
        self.rb, self.rt, self.h, self.wall, self.base = r_bottom, r_top, height, wall, base
        self.name = name
        self.root = bpy.data.objects.new(f'{name}_root', None)
        (coll or bpy.context.scene.collection).objects.link(self.root)
        # glass profile (outer bottom center -> outer wall -> rim -> inner wall -> inner bottom center)
        bev = 0.004
        rim = wall * 0.5
        prof = [(0.0, 0.0)]
        prof += [(r, z) for r, z in arc(self.rb - bev, bev, bev, -math.pi / 2, 0.0, 8)]
        for z in np.linspace(bev + 0.004, height - rim, 26):
            prof.append((self.r_outer(z), z))
        prof += arc(self.r_outer(height - rim) - rim, height - rim, rim, 0.0, math.pi, 10)
        for z in np.linspace(height - rim - 0.002, base + 0.003, 26):
            prof.append((self.r_inner(z), z))
        bi = 0.003
        prof += arc(self.r_inner(base + bi) - bi, base + bi, bi, 0.0, -math.pi / 2, 6)
        # slightly domed inner floor
        for r in np.linspace(self.r_inner(base + bi) - bi - 0.002, 0.004, 6):
            prof.append((r, base + 0.0006 * (1 - r / self.rb)))
        prof.append((0.0, base + 0.0007))
        verts, faces, _ = lathe(prof, seg)
        me = make_mesh(f'{name}_glass', verts, faces)
        fix_normals(me)
        self.glass = link_obj(f'{name}_glass', me, shadow_pass_through(glass_material(f'{name}_glass_mat')), coll)
        self.glass.parent = self.root
        # water: overlaps the inner wall by 0.25 mm so the glass/water interface refracts correctly
        self.level = base + (height - base) * fill
        ov = 0.00025
        wp = [(0.0, base + 0.0009)]
        for r in np.linspace(0.004, self.r_inner(base + 0.004) + ov, 5):
            wp.append((r, base + 0.0009))
        for z in np.linspace(base + 0.004, self.level - 0.0005, 20):
            wp.append((self.r_inner(z) + ov, z))
        # meniscus climbs the wall
        rw = self.r_inner(self.level) + ov
        self.top_start = len(wp)
        nr = 56
        for k in range(nr):
            f = k / (nr - 1)
            r = rw * (1 - f) ** 1.0
            men = 0.0016 * math.exp(-(rw - r) / 0.0012)
            wp.append((max(r, 0.0) if k < nr - 1 else 0.0, self.level + men))
        verts, faces, rings = lathe(wp, seg)
        me = make_mesh(f'{name}_water', verts, faces)
        fix_normals(me)
        self.water = link_obj(f'{name}_water', me,
                              shadow_pass_through(water_material(f'{name}_water_mat', tint=water_tint), (0.85, 0.93, 0.92)),
                              coll)
        self.water.parent = self.root
        self.w_rest = np.array(verts, np.float64)
        top_ids = [i for ring in rings[self.top_start:] for i in ring]
        self.top_ids = np.array(top_ids)
        self.top_r = np.hypot(self.w_rest[self.top_ids, 0], self.w_rest[self.top_ids, 1])
        self.top_a = np.arctan2(self.w_rest[self.top_ids, 1], self.w_rest[self.top_ids, 0])
        self.rw = rw
        self.impacts = []  # (t0, x, y, strength)

    def r_outer(self, z):
        return self.rb + (self.rt - self.rb) * (z / self.h)

    def r_inner(self, z):
        return self.r_outer(z) - self.wall

    def ripple(self, t, calm=1.0, extra=None):
        """Animate the water surface: slow sloshing + ring ripples from impacts (list of (t0, x, y, amp))."""
        v = self.w_rest.copy()
        r, a = self.top_r, self.top_a
        x, y = v[self.top_ids, 0], v[self.top_ids, 1]
        edge = np.clip(r / self.rw, 0, 1)
        dz = calm * 0.00022 * (np.sin(2.1 * t + 3.0 * edge * np.cos(a - 0.4)) * edge
                               + 0.6 * np.sin(3.3 * t + 5.0 * r / self.rw + a) * edge ** 2)
        dz += 0.00005 * np.sin(40 * r + 5 * t) * calm
        for (t0, px, py, amp) in (self.impacts + (extra or [])):
            dtt = t - t0
            if dtt <= 0 or dtt > 3.0:
                continue
            d = np.hypot(x - px, y - py)
            front = 0.09 * dtt
            dz += amp * 0.0012 * np.exp(-((d - front) / 0.004) ** 2) * np.cos((d - front) * 900) * np.exp(-dtt * 1.4)
        v[self.top_ids, 2] += dz
        self.water.data.vertices.foreach_set('co', v.astype(np.float32).ravel())
        self.water.data.update()


def table(coll=None, size=(1.6, 0.9), thick=0.04):
    import bmesh
    me = bpy.data.meshes.new('table')
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(size[0], size[1], thick), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, -thick / 2), verts=bm.verts)
    bmesh.ops.bevel(bm, geom=[e for e in bm.edges], offset=0.004, segments=3, affect='EDGES')
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    return link_obj('table', me, wood_material(), coll)


def plane(name, w, h, loc, rot, mat, coll=None):
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    bmesh.ops.scale(bm, vec=(w, h, 1), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    ob = link_obj(name, me, mat, coll)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def blinds(coll=None, width=1.4, height=1.2, slats=26, gap_ratio=0.45, tilt=0.35, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Venetian blinds: thin tilted slats - cast those noir light bars."""
    import bmesh
    me = bpy.data.meshes.new('blinds')
    bm = bmesh.new()
    pitch = height / slats
    depth = pitch * (1 - gap_ratio) * 1.6
    for i in range(slats):
        z = -height / 2 + (i + 0.5) * pitch
        g = bmesh.ops.create_cube(bm, size=1.0)
        vs = g['verts']
        bmesh.ops.scale(bm, vec=(width, depth, 0.0012), verts=vs)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(tilt, 3, 'X'), verts=vs)
        bmesh.ops.translate(bm, vec=(0, 0, z), verts=vs)
    bm.to_mesh(me)
    bm.free()
    m, nt, b = new_mat('blinds_mat')
    b.inputs['Base Color'].default_value = (0.35, 0.33, 0.3, 1)
    b.inputs['Roughness'].default_value = 0.6
    ob = link_obj('blinds', me, m, coll)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def pendant_lamp(coll=None, loc=(0, 0, 0.6), power=18.0, color=(1.0, 0.72, 0.42), cone_deg=70):
    """Metal cone shade + hot bulb + spot light pointing down."""
    import bmesh
    prof = [(0.012, 0.09), (0.02, 0.085), (0.03, 0.06), (0.06, 0.02), (0.11, -0.03), (0.112, -0.034),
            (0.108, -0.034), (0.058, 0.016), (0.028, 0.055), (0.018, 0.08), (0.010, 0.085)]
    verts, faces, _ = lathe(prof, 96)
    me = make_mesh('lamp_shade', verts, faces)
    m, nt, b = new_mat('lamp_shade_mat')
    b.inputs['Base Color'].default_value = (0.02, 0.02, 0.022, 1)
    b.inputs['Metallic'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.35
    shade = link_obj('lamp_shade', me, m, coll)
    shade.location = loc
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=0.022)
    bme = bpy.data.meshes.new('bulb')
    bm.to_mesh(bme)
    bm.free()
    bulb = link_obj('lamp_bulb', bme, emission_material('bulb_mat', color, 60.0), coll)
    bulb.location = (loc[0], loc[1], loc[2] - 0.012)
    bulb.visible_shadow = False  # the spot light sits inside the bulb glass
    bulb.visible_glossy = False  # no long mirror streaks of the bulb down the curved glass
    bulb.visible_transmission = False
    ld = bpy.data.lights.new('lamp_spot', 'SPOT')
    ld.energy = power
    ld.color = color
    ld.spot_size = math.radians(cone_deg * 1.6)
    ld.spot_blend = 0.55
    ld.shadow_soft_size = 0.02
    lo = bpy.data.objects.new('lamp_spot', ld)
    (coll or bpy.context.scene.collection).objects.link(lo)
    lo.location = (loc[0], loc[1], loc[2] - 0.02)
    # cord
    cord_v, cord_f, _ = lathe([(0.0, 0.0), (0.0025, 0.0), (0.0025, 1.5), (0.0, 1.5)], 12)
    cme = make_mesh('lamp_cord', cord_v, cord_f)
    cord = link_obj('lamp_cord', cme, m, coll)
    cord.location = (loc[0], loc[1], loc[2] + 0.085)
    return shade, bulb, lo


def area_light(name, loc, rot, size, power, color, coll=None, shape='RECTANGLE', size_y=None):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = power
    ld.color = color
    ld.shape = shape
    ld.size = size
    if size_y is not None:
        ld.size_y = size_y
    ob = bpy.data.objects.new(name, ld)
    (coll or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def spot(name, loc, target, power, color, size_deg=40, blend=0.3, radius=0.05, coll=None):
    import mathutils
    ld = bpy.data.lights.new(name, 'SPOT')
    ld.energy = power
    ld.color = color
    ld.spot_size = math.radians(size_deg)
    ld.spot_blend = blend
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld)
    (coll or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    d = mathutils.Vector(target) - mathutils.Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


def world_hdri(path, strength=0.3, rot_z=0.0, bg_strength=None):
    w = bpy.context.scene.world or bpy.data.worlds.new('World')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for x in list(nt.nodes):
        nt.nodes.remove(x)
    out = nt.nodes.new('ShaderNodeOutputWorld')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0, 0, rot_z)
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(path, check_existing=True)
    link(nt, tc.outputs['Generated'], mp.inputs['Vector'])
    link(nt, mp.outputs['Vector'], env.inputs['Vector'])
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = strength
    link(nt, env.outputs['Color'], bg.inputs['Color'])
    if bg_strength is None:
        link(nt, bg.outputs['Background'], out.inputs['Surface'])
    else:
        # camera sees a different (darker) background than reflections do
        lp = nt.nodes.new('ShaderNodeLightPath')
        bg2 = nt.nodes.new('ShaderNodeBackground')
        bg2.inputs['Strength'].default_value = bg_strength
        link(nt, env.outputs['Color'], bg2.inputs['Color'])
        mix = nt.nodes.new('ShaderNodeMixShader')
        link(nt, lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
        link(nt, bg.outputs['Background'], mix.inputs[1])
        link(nt, bg2.outputs['Background'], mix.inputs[2])
        link(nt, mix.outputs['Shader'], out.inputs['Surface'])
    return w
