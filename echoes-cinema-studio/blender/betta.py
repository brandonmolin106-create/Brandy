"""Hero halfmoon betta for Blender/Cycles: lofted body, five fin membranes, eyes, and a per-frame swim rig.

Everything is generated from numpy so the animation can be driven directly from Python while rendering:

    fish = Betta(tex_dir)            # builds meshes + materials under one parent empty
    fish.pose(t, swim=..., flare=...) # deforms body + fins for time t (seconds)
    fish.root.location = ...         # place / orient the whole fish

Local frame: +X = forward (snout), +Z = up, +Y = fish's left.  Units: metres (body length L = 5 cm).
"""
import math

import bpy
import numpy as np

L = 0.05


def catmull(u, pts):
    """Smooth interpolation through (u, value) control points (Catmull-Rom, clamped ends)."""
    us = np.array([p[0] for p in pts], np.float64)
    vs = np.array([p[1] for p in pts], np.float64)
    u = np.clip(np.asarray(u, np.float64), us[0], us[-1])
    i = np.clip(np.searchsorted(us, u, side='right') - 1, 0, len(us) - 2)
    u0, u1 = us[i], us[i + 1]
    p1, p2 = vs[i], vs[i + 1]
    p0 = vs[np.maximum(i - 1, 0)]
    p3 = vs[np.minimum(i + 2, len(vs) - 1)]
    t = (u - u0) / (u1 - u0)
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


# body profiles in units of L:  (u, value), u = 0 snout .. 1 caudal peduncle
H_TOP = [(0, 0), (0.015, 0.026), (0.05, 0.058), (0.1, 0.090), (0.18, 0.118), (0.28, 0.134), (0.38, 0.138),
         (0.5, 0.131), (0.6, 0.118), (0.7, 0.100), (0.8, 0.082), (0.9, 0.068), (0.97, 0.061), (1.0, 0.059)]
H_BOT = [(0, 0), (0.015, 0.028), (0.05, 0.064), (0.1, 0.102), (0.18, 0.136), (0.28, 0.158), (0.38, 0.164),
         (0.5, 0.152), (0.6, 0.130), (0.7, 0.106), (0.8, 0.084), (0.9, 0.068), (0.97, 0.060), (1.0, 0.057)]
HALF_W = [(0, 0), (0.015, 0.022), (0.05, 0.045), (0.1, 0.062), (0.18, 0.074), (0.28, 0.079), (0.38, 0.077),
          (0.5, 0.070), (0.6, 0.061), (0.7, 0.051), (0.8, 0.041), (0.9, 0.032), (0.97, 0.027), (1.0, 0.026)]
CENTER = [(0, 0.016), (0.08, 0.008), (0.2, 0.0), (1.0, 0.0)]  # upturned mouth


def prof(u):
    return (catmull(u, H_TOP) * L, catmull(u, H_BOT) * L, catmull(u, HALF_W) * L, catmull(u, CENTER) * L)


def xpos(u):
    return L * (0.5 - u)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def make_mesh(name, verts, faces, uvs=None, smooth_shade=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    if uvs is not None:
        uv = me.uv_layers.new(name='UVMap')
        uv.data.foreach_set('uv', np.asarray(uvs, np.float32).ravel())
    if smooth_shade:
        me.shade_smooth()
    me.update()
    return me


def grid_faces(nr, nc, wrap=False):
    f = []
    cols = nc if wrap else nc - 1
    for i in range(nr - 1):
        for j in range(cols):
            j1 = (j + 1) % nc
            f.append((i * nc + j, (i + 1) * nc + j, (i + 1) * nc + j1, i * nc + j1))
    return f


def grid_loop_uvs(nr, nc, U, V, wrap=False):
    """Per-loop UVs matching grid_faces order (handles the wrap seam)."""
    out = []
    cols = nc if wrap else nc - 1
    for i in range(nr - 1):
        for j in range(cols):
            vj1 = V[j + 1] if j + 1 < len(V) else 1.0
            out += [(U[i], V[j]), (U[i + 1], V[j]), (U[i + 1], vj1), (U[i], vj1)]
    return out


# ------------------------------------------------------------------ materials
def _img(path, colorspace='sRGB'):
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = colorspace
    return img


def body_material(tex):
    m = bpy.data.materials.new('betta_body')
    m.use_nodes = True
    nt = m.node_tree
    n = nt.nodes
    for x in list(n):
        n.remove(x)
    out = n.new('ShaderNodeOutputMaterial')
    bsdf = n.new('ShaderNodeBsdfPrincipled')
    uv = n.new('ShaderNodeUVMap')
    alb = n.new('ShaderNodeTexImage')
    alb.image = _img(f'{tex}/body_albedo.png')
    rough = n.new('ShaderNodeTexImage')
    rough.image = _img(f'{tex}/body_rough.png', 'Non-Color')
    hgt = n.new('ShaderNodeTexImage')
    hgt.image = _img(f'{tex}/body_height.png', 'Non-Color')
    film = n.new('ShaderNodeTexImage')
    film.image = _img(f'{tex}/body_film.png', 'Non-Color')
    for t in (alb, rough, hgt, film):
        nt.links.new(uv.outputs['UV'], t.inputs['Vector'])
        t.interpolation = 'Linear'
    bump = n.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.9
    bump.inputs['Distance'].default_value = 0.0005
    nt.links.new(hgt.outputs['Color'], bump.inputs['Height'])
    fmul = n.new('ShaderNodeMath')
    fmul.operation = 'MULTIPLY'
    fmul.inputs[1].default_value = 420.0
    nt.links.new(film.outputs['Color'], fmul.inputs[0])
    nt.links.new(alb.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(rough.outputs['Color'], bsdf.inputs['Roughness'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    nt.links.new(fmul.outputs[0], bsdf.inputs['Thin Film Thickness'])
    bsdf.inputs['Thin Film IOR'].default_value = 1.33
    bsdf.inputs['Coat Weight'].default_value = 0.12
    bsdf.inputs['Coat Roughness'].default_value = 0.08
    bsdf.inputs['Specular IOR Level'].default_value = 0.35
    bsdf.inputs['Coat IOR'].default_value = 1.35
    bsdf.inputs['Subsurface Weight'].default_value = float(__import__('os').environ.get('SSS', 0.0))
    bsdf.inputs['Subsurface Radius'].default_value = (1.0, 0.25, 0.2)
    bsdf.inputs['Subsurface Scale'].default_value = 0.0012
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m


def fin_material(tex, name, translucency=0.55, film_nm=380.0):
    m = bpy.data.materials.new(f'betta_fin_{name}')
    m.use_nodes = True
    nt = m.node_tree
    n = nt.nodes
    for x in list(n):
        n.remove(x)
    out = n.new('ShaderNodeOutputMaterial')
    uv = n.new('ShaderNodeUVMap')
    alb = n.new('ShaderNodeTexImage')
    alb.image = _img(f'{tex}/fin_{name}_albedo.png')
    alp = n.new('ShaderNodeTexImage')
    alp.image = _img(f'{tex}/fin_{name}_alpha.png', 'Non-Color')
    ray = n.new('ShaderNodeTexImage')
    ray.image = _img(f'{tex}/fin_{name}_ray.png', 'Non-Color')
    for t in (alb, alp, ray):
        nt.links.new(uv.outputs['UV'], t.inputs['Vector'])
        t.interpolation = 'Linear'
    bsdf = n.new('ShaderNodeBsdfPrincipled')
    nt.links.new(alb.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.34
    bsdf.inputs['Specular IOR Level'].default_value = 0.3
    bsdf.inputs['Thin Film Thickness'].default_value = film_nm
    bsdf.inputs['Thin Film IOR'].default_value = 1.4
    bump = n.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.35
    bump.inputs['Distance'].default_value = 0.0002
    nt.links.new(ray.outputs['Color'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    trans = n.new('ShaderNodeBsdfTranslucent')
    boost = n.new('ShaderNodeMixRGB')
    boost.blend_type = 'MULTIPLY'
    boost.inputs['Fac'].default_value = 1.0
    boost.inputs['Color2'].default_value = (1.7, 0.55, 0.6, 1)
    nt.links.new(alb.outputs['Color'], boost.inputs['Color1'])
    nt.links.new(boost.outputs['Color'], trans.inputs['Color'])
    mix = n.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = translucency
    nt.links.new(bsdf.outputs['BSDF'], mix.inputs[1])
    nt.links.new(trans.outputs['BSDF'], mix.inputs[2])
    transp = n.new('ShaderNodeBsdfTransparent')
    mix2 = n.new('ShaderNodeMixShader')
    nt.links.new(alp.outputs['Color'], mix2.inputs['Fac'])
    nt.links.new(transp.outputs['BSDF'], mix2.inputs[1])
    nt.links.new(mix.outputs['Shader'], mix2.inputs[2])
    nt.links.new(mix2.outputs['Shader'], out.inputs['Surface'])
    return m


def eye_material():
    m = bpy.data.materials.new('betta_eye')
    m.use_nodes = True
    nt = m.node_tree
    n = nt.nodes
    bsdf = n['Principled BSDF']
    tc = n.new('ShaderNodeTexCoord')
    sep = n.new('ShaderNodeSeparateXYZ')
    nrm = n.new('ShaderNodeVectorMath')
    nrm.operation = 'NORMALIZE'
    nt.links.new(tc.outputs['Object'], nrm.inputs[0])
    nt.links.new(nrm.outputs['Vector'], sep.inputs['Vector'])
    # object-space +Y of the eye empty points outward: pupil where y ~ 1
    ramp = n.new('ShaderNodeValToRGB')
    el = ramp.color_ramp.elements
    el[0].position = 0.70
    el[0].color = (0.16, 0.012, 0.01, 1)           # skin around the eye
    el[1].position = 0.94
    el[1].color = (0.002, 0.0015, 0.0015, 1)       # pupil
    for pos, col in ((0.80, (0.012, 0.004, 0.003, 1)),   # dark limbal ring
                     (0.86, (0.16, 0.06, 0.015, 1)),     # thin dim gold iris
                     (0.905, (0.10, 0.02, 0.008, 1)),
                     (0.925, (0.02, 0.006, 0.004, 1))):
        e = el.new(pos)
        e.color = col
    mapr = n.new('ShaderNodeMapRange')
    mapr.inputs['From Min'].default_value = -1.0
    mapr.inputs['From Max'].default_value = 1.0
    nt.links.new(sep.outputs['Y'], mapr.inputs['Value'])
    nt.links.new(mapr.outputs['Result'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.35
    bsdf.inputs['Coat Weight'].default_value = 1.0
    bsdf.inputs['Coat Roughness'].default_value = 0.015
    bsdf.inputs['Coat IOR'].default_value = 1.38
    return m


# ------------------------------------------------------------------ the fish
class Betta:
    NU, NV = 170, 96

    def __init__(self, tex_dir, name='betta', collection=None):
        self.name = name
        self.coll = collection or bpy.context.scene.collection
        self.root = bpy.data.objects.new(f'{name}_root', None)
        self.coll.objects.link(self.root)
        self.objs = {}
        self._build_body(tex_dir)
        self._build_fins(tex_dir)
        self._build_eyes()
        self.phase = 0.0
        self.last_t = None
        self.loop_T = None      # when set, every oscillation completes whole cycles in loop_T seconds
        self.cur_freq = 1.0
        self.pose(0.0)

    # ---------------- construction
    def _link(self, name, me, mat):
        ob = bpy.data.objects.new(f'{self.name}_{name}', me)
        me.materials.append(mat)
        ob.parent = self.root
        self.coll.objects.link(ob)
        self.objs[name] = ob
        return ob

    def _build_body(self, tex):
        s = np.linspace(0, 1, self.NU)
        self.bu = s ** 1.25 * 0.995 + 0.004         # denser rings at the head; ring 0 just behind the snout tip
        self.bv = np.arange(self.NV) / self.NV
        verts = np.zeros((self.NU * self.NV + 2, 3))
        faces = grid_faces(self.NU, self.NV, wrap=True)
        uvs = grid_loop_uvs(self.NU, self.NV, self.bu, list(self.bv), wrap=True)
        tip, tail = self.NU * self.NV, self.NU * self.NV + 1
        for j in range(self.NV):
            j1 = (j + 1) % self.NV
            faces.append((tip, j, j1))
            v1 = self.bv[j + 1] if j + 1 < self.NV else 1.0
            uvs += [(0.0, (self.bv[j] + v1) / 2), (self.bu[0], self.bv[j]), (self.bu[0], v1)]
            a, b = (self.NU - 1) * self.NV + j, (self.NU - 1) * self.NV + j1
            faces.append((b, a, tail))
            uvs += [(self.bu[-1], v1), (self.bu[-1], self.bv[j]), (1.0, (self.bv[j] + v1) / 2)]
        me = make_mesh(f'{self.name}_body', verts, faces, uvs)
        self._link('body', me, body_material(tex))
        a = self.bv * 2 * np.pi
        ca, sa = np.cos(a), np.sin(a)
        ht, hb, hw, cc = prof(self.bu)
        ey = np.sign(ca) * np.abs(ca) ** 0.9
        ez = np.sign(sa) * np.abs(sa) ** 1.0
        narrow = 1 - 0.38 * np.clip(sa, 0, 1) ** 2 - 0.12 * np.clip(-sa, 0, 1) ** 2
        self.b_y = hw[:, None] * (ey * narrow)[None, :]
        self.b_z = cc[:, None] + np.where(sa[None, :] > 0, ht[:, None], hb[:, None]) * ez[None, :]
        self.b_x = xpos(self.bu)[:, None] + 0 * self.b_y
        self.h_top, self.h_bot, self.hw, self.cc = ht, hb, hw, cc

    def _fin_grid(self, ns, nt):
        s = np.linspace(0, 1, ns)
        t = np.linspace(0, 1, nt) ** 0.9
        S, T = np.meshgrid(s, t, indexing='ij')
        return S, T

    def _build_fins(self, tex):
        self.fins = {}
        specs = {
            # name: (ns, nt, texture, translucency)
            'caudal': (150, 60, 'caudal', 0.6),
            'dorsal': (90, 44, 'dorsal', 0.6),
            'anal': (130, 52, 'anal', 0.6),
            'pelvic_l': (10, 40, 'pelvic', 0.5),
            'pelvic_r': (10, 40, 'pelvic', 0.5),
            'pect_l': (24, 16, 'pectoral', 0.3),
            'pect_r': (24, 16, 'pectoral', 0.3),
        }
        mats = {}
        for name, (ns, nt_, texname, tr) in specs.items():
            if texname not in mats:
                mats[texname] = fin_material(tex, texname, tr, film_nm=300 if texname != 'pectoral' else 220)
            S, T = self._fin_grid(ns, nt_)
            verts = np.zeros((ns * nt_, 3))
            faces = grid_faces(ns, nt_)
            uvs = grid_loop_uvs(ns, nt_, list(S[:, 0]), list(T[0, :]))
            # grid_loop_uvs gives (row param, col param) = (s, t): texture x = across rays, y = root->edge
            me = make_mesh(f'{self.name}_{name}', verts, faces, uvs)
            self._link(name, me, mats[texname])
            self.fins[name] = (S, T)

    def _build_eyes(self):
        mat = eye_material()
        self.eyes = []
        for side in (1, -1):
            me = bpy.data.meshes.new(f'{self.name}_eye{side}')
            import bmesh
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=0.05 * L)
            bm.to_mesh(me)
            bm.free()
            me.shade_smooth()
            ob = bpy.data.objects.new(f'{self.name}_eye{side}', me)
            me.materials.append(mat)
            ob.parent = self.root
            self.coll.objects.link(ob)
            self.eyes.append((side, ob))

    # ---------------- animation
    def _q(self, w):
        if not self.loop_T:
            return w
        base = 2 * np.pi / self.loop_T
        return max(1, round(w / base)) * base

    def tw(self, w, t):
        """Phase of a free oscillator of angular frequency w at time t (loop-safe)."""
        return self._q(w) * t

    def ang(self, mult, t):
        """Phase of a fin component running at `mult` x the tail-beat frequency."""
        if self.loop_T:
            return self._q(2 * np.pi * self.cur_freq * mult) * t
        return self.phase * mult

    def wave(self, xi, amp, k=5.2):
        """Lateral displacement of the travelling body/fin wave at axial coordinate xi (0 snout, 1 peduncle, >1 fins)."""
        a = amp * L * (0.018 + 0.11 * np.clip(xi, 0, 1) ** 2 + 0.16 * np.clip(xi - 1, 0, None))
        return a * np.sin(self.phase - k * xi)

    def pose(self, t, swim=0.35, freq=1.1, flare=0.5, turn=0.0, flutter=1.0, pitch_bend=0.0, drift=0.0, dt=None):
        """Deform the fish for time t.  swim: tail-beat amplitude (0 hover .. 1 dash); flare: fin spread (0 folded .. 1
        full flare); turn: body curvature (-1..1, + turns left); flutter: fin ripple amount."""
        if self.last_t is None or dt is None:
            dt = 0.0 if self.last_t is None else t - self.last_t
        self.phase += 2 * np.pi * freq * dt
        self.cur_freq = freq
        if self.loop_T:
            self.phase = self._q(2 * np.pi * freq) * t
        self.last_t = t
        self._t = t
        # ---- body
        u = self.bu
        lat = self.wave(u, swim) + turn * L * 0.32 * u ** 2
        dlat = np.gradient(lat, xpos(u))  # cross sections rotate with the bend (small-angle)
        # rotate cross sections to follow the bend (small-angle: shift x by -y*slope)
        bx = self.b_x - self.b_y * dlat[:, None] * 0.5
        bz = self.b_z + pitch_bend * L * 0.2 * u[:, None] ** 2
        # breathing: gill covers pulse slightly
        breath = 1 + 0.02 * math.sin(self.tw(2 * np.pi * 1.6, t)) * np.exp(-((u - 0.2) / 0.05) ** 2)
        by = lat[:, None] + self.b_y * breath[:, None]
        v = np.zeros((self.NU * self.NV + 2, 3))
        v[:-2, 0] = bx.ravel()
        v[:-2, 1] = by.ravel()
        v[:-2, 2] = bz.ravel()
        v[-2] = (xpos(0.0) + 0.0005, self.wave(np.array([0.0]), swim)[0], self.cc[0] + 0.0)
        v[-1] = (xpos(1.0) - 0.001, lat[-1], bz[-1].mean())
        self._set(self.objs['body'], v)
        self._lat_u, self._lat = u, lat
        self._pose_fins(t, swim, flare, turn, flutter)
        self._pose_eyes()

    def _body_lat(self, xi):
        return np.interp(xi, self._lat_u, self._lat) if np.ndim(xi) else float(np.interp(xi, self._lat_u, self._lat))

    def _lat_ext(self, xi, swim, turn):
        """Body wave continued into the fins (xi > 1 behind the peduncle)."""
        inside = np.interp(np.clip(xi, 0, 1), self._lat_u, self._lat)
        ext = self.wave(xi, swim) - self.wave(np.minimum(xi, 1.0), swim) + turn * L * 0.32 * (xi ** 2 - np.minimum(xi, 1) ** 2)
        return inside + ext

    def _set(self, ob, v):
        ob.data.vertices.foreach_set('co', np.asarray(v, np.float32).ravel())
        ob.data.update()

    def _pose_fins(self, t, swim, flare, turn, flutter):
        ph = self.phase
        fl = flutter
        # ---------------- caudal: halfmoon fan from the peduncle
        S, T = self.fins['caudal']
        u0 = 0.975
        ht, hb, hw, cc = prof(np.array([u0]))
        zr = cc[0] + (-hb[0] * 0.88 + (ht[0] * 0.88 + hb[0] * 0.88) * S)
        xr = xpos(u0) + 0 * S
        phimax = np.radians(62 + 38 * flare)
        phi = (S * 2 - 1) * phimax
        rc = L * (0.62 + 0.18 * flare)
        rc = rc * (1 + 0.035 * np.sin(S * np.pi * 7 + 0.7) - 0.05 * np.abs(S * 2 - 1) ** 3)
        cx, cz = xpos(1.0) - 0.04 * L, cc[0]
        ex = cx - rc * np.cos(phi)
        ez = cz + rc * np.sin(phi) * 1.02
        # rays bend down a little (weight of the fin) and trail with the stroke
        x = xr + (ex - xr) * T
        z = zr + (ez - zr) * T - L * 0.05 * (1 - flare) * T ** 2
        dist = np.hypot(x - xr, z - zr)
        xi = 1.0 + dist / L
        pleat = L * (0.06 * (1 - flare) + 0.02) * np.sin(np.pi * 9 * S + 0.6 * np.sin(3 * S)) * T ** 1.2
        pleat += L * 0.035 * np.sin(np.pi * 2.5 * S + 0.8) * T ** 2.2  # large-scale billow of the whole fan
        ripple = L * 0.03 * fl * T ** 1.6 * np.sin(self.ang(1.7, t) - 7.5 * T + 5.0 * S) \
            + L * 0.015 * fl * T ** 2 * np.sin(self.tw(2.3, t) + 11 * S - 4 * T)
        y = self._lat_ext(xi, swim, turn) + pleat + ripple
        # fold the fan (pleats shorten the chord a bit)
        x = x + np.abs(pleat) * 0.3
        self._set(self.objs['caudal'], np.stack([x, y, z], -1).reshape(-1, 3))

        # ---------------- dorsal: along the back, rays up and back
        S, T = self.fins['dorsal']
        us = 0.47 + 0.47 * S
        ht, hb, hw, cc = prof(us)
        xr = xpos(us)
        zr = cc + ht * 0.96
        alpha = np.radians(18 + 42 * S ** 1.3 + 12 * (1 - flare))
        R = L * (0.22 + 0.36 * S ** 1.1) * (0.85 + 0.2 * flare)
        R = R * (1 - 0.45 * smooth(0.9, 1.0, S)) * (1 - 0.25 * smooth(0.15, 0.0, S))
        # rays curve backward along their length (flow + weight)
        bend = np.radians(10 + 30 * (1 - flare)) * T ** 1.5
        a2 = alpha + bend
        x = xr - R * T * np.sin(0.5 * (alpha + a2))
        z = zr + R * T * np.cos(0.5 * (alpha + a2))
        xi = us + R * T * np.sin(a2) / L
        ripple = L * 0.03 * fl * T ** 1.5 * np.sin(self.ang(1.3, t) - 6.0 * T - 6.0 * S + 1.0) \
            + L * 0.016 * fl * T ** 2 * np.sin(self.tw(1.9, t) + 8 * S) + L * 0.008 * fl * T ** 2 * np.sin(self.tw(3.1, t) + 19 * S - 5 * T)
        pleat = L * (0.02 + 0.02 * (1 - flare)) * np.sin(np.pi * 6 * S + 0.4) * T
        pleat += L * 0.03 * np.sin(np.pi * 1.6 * S + 0.3) * T ** 2 + L * 0.012 * T ** 5  # billow + edge curl
        y = self._lat_ext(xi, swim, turn) + ripple + pleat
        self._set(self.objs['dorsal'], np.stack([x, y, z], -1).reshape(-1, 3))

        # ---------------- anal: long ventral fin, pointed trailing end
        S, T = self.fins['anal']
        us = 0.34 + 0.62 * S
        ht, hb, hw, cc = prof(us)
        xr = xpos(us)
        zr = cc - hb * 0.95
        alpha = np.radians(22 + 38 * S ** 1.2 + 10 * (1 - flare))
        R = L * (0.26 + 0.30 * S ** 1.05) * (0.88 + 0.16 * flare)
        R = R * (1 + 0.25 * np.exp(-((S - 0.88) / 0.1) ** 2)) * (1 - 0.45 * smooth(0.95, 1.0, S))
        R = R * (1 - 0.3 * smooth(0.12, 0.0, S))
        bend = np.radians(8 + 26 * (1 - flare)) * T ** 1.5
        a2 = alpha + bend
        x = xr - R * T * np.sin(0.5 * (alpha + a2))
        z = zr - R * T * np.cos(0.5 * (alpha + a2))
        xi = us + R * T * np.sin(a2) / L
        ripple = L * 0.034 * fl * T ** 1.5 * np.sin(self.ang(1.25, t) - 6.5 * T - 7.0 * S + 2.0) \
            + L * 0.018 * fl * T ** 2 * np.sin(self.tw(2.1, t) + 9 * S) + L * 0.009 * fl * T ** 2 * np.sin(self.tw(2.9, t) + 23 * S - 6 * T)
        pleat = L * (0.022 + 0.02 * (1 - flare)) * np.sin(np.pi * 8 * S + 0.9) * T
        pleat += L * 0.034 * np.sin(np.pi * 1.8 * S + 1.1) * T ** 2 - L * 0.012 * T ** 5
        y = self._lat_ext(xi, swim, turn) + ripple + pleat
        self._set(self.objs['anal'], np.stack([x, y, z], -1).reshape(-1, 3))

        # ---------------- pelvic streamers
        for side, name in ((1, 'pelvic_l'), (-1, 'pelvic_r')):
            S, T = self.fins[name]
            u0 = 0.27
            ht, hb, hw, cc = prof(np.array([u0]))
            width = L * 0.03 * (1 - T ** 1.5)
            a = np.radians(28 + 10 * math.sin(self.tw(1.1, t) + side))
            Rl = L * 0.36
            x = xpos(u0) + (S - 0.5) * width - Rl * T * np.sin(a)
            z = cc[0] - hb[0] * 0.9 - Rl * T * np.cos(a)
            y = self._body_lat(u0) + side * (L * 0.012 + L * 0.06 * T * (0.4 + 0.2 * math.sin(self.tw(1.7, t) + side))) \
                + L * 0.03 * fl * T ** 1.5 * np.sin(self.ang(1.1, t) - 5 * T + side)
            self._set(self.objs[name], np.stack([x, y, z], -1).reshape(-1, 3))

        # ---------------- pectoral fans (fast flutter)
        for side, name in ((1, 'pect_l'), (-1, 'pect_r')):
            S, T = self.fins[name]
            u0 = 0.235
            ht, hb, hw, cc = prof(np.array([u0]))
            beat = math.sin(self.tw(2 * np.pi * 3.2, t) + (0 if side > 0 else 1.9))
            spread = np.radians(-35 + 70 * S)
            out = np.radians(35 + 25 * beat)
            Rl = L * 0.14 * (1 - 0.25 * np.abs(S * 2 - 1) ** 2)
            dx = -np.cos(spread) * np.cos(out)
            dy = np.sin(out) * side
            dz = np.sin(spread) * 0.8
            x = xpos(u0) + Rl * T * dx
            y = self._body_lat(u0) + side * hw[0] * 0.92 + Rl * T * dy + side * L * 0.01 * T ** 2 * np.sin(self.tw(20, t) + 6 * S)
            z = cc[0] - 0.1 * hb[0] + Rl * T * dz
            self._set(self.objs[name], np.stack([x, y, z], -1).reshape(-1, 3))

    def _pose_eyes(self):
        u0 = 0.105
        ht, hb, hw, cc = prof(np.array([u0]))
        lat = self._body_lat(u0)
        for side, ob in self.eyes:
            a = np.radians(18)
            y = lat + side * hw[0] * np.cos(a) * 0.86
            z = cc[0] + ht[0] * np.sin(a) * 0.95
            ob.location = (xpos(u0), y, z)
            # object +Y axis points outward (pupil)
            ob.rotation_euler = (0.0, 0.0, 0.0 if side > 0 else math.pi)
            ob.scale = (1.0, 0.8, 1.0)
