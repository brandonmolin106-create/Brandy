# ============================================================================
#
#     E N D L E S S   D E S T I N Y
#     a song-structured galaxy music video, built by one Blender script
#     an  ECHOES IN THE DARK  production
#
#     Works in Blender 4.2 LTS, 4.5 LTS and 5.0 (Cycles and EEVEE).
#
# ============================================================================
"""
WHAT THIS BUILDS
  * A barred spiral galaxy made of real points of light: 1.2 million stars on
    HIGH (3 million on ULTRA), each coloured by its blackbody temperature. Hot
    blue O/B stars and open clusters trace the arms, gold giants fill the bulge
    and bar, faint red stars make up the halo, plus 130 globular clusters and two
    satellite dwarf galaxies.
  * Volumetric gas: glowing spiral arms, pink H-II star-forming knots, dark dust
    lanes on the inner edge of every arm, and a bright bar and bulge.
  * The Destiny Nebula (Hubble-palette gas around a newborn star cluster), the
    Destiny Star with echo rings, a pulsar that spins on the beat, a black hole
    with an accretion disk and photon ring, relativistic jets, a galactic
    shockwave, and 3000 background galaxies laid out along a cosmic web.
  * A camera flight in 10 acts that follow the song. The audio drives star
    pulses, twinkles, flashes, camera shake, meteors and a constellation that
    draws itself on the beat.

QUICK START (Blender window)
  1. Put your "Endless Destiny" audio file in the same folder as this script
     (any file name with "endless" or "destiny" in it works), or paste its full
     path into AUDIO_PATH below.
  2. Blender > Scripting tab > Open > endless_destiny.py > Run Script (the play
     button). Building takes about a minute.
  3. In the viewport press Numpad 0 for the camera view and Space to play. The
     timeline markers show where each act starts. F12 renders one frame, and
     Render > Render Animation renders the whole video.

QUICK START (command line)
  blender -b -P endless_destiny.py -- --audio "Endless Destiny.mp3" --render

  Options (all optional):
    --audio PATH          the song (mp3 / wav / ogg / flac / m4a)
    --engine CYCLES|EEVEE
    --quality PREVIEW|HIGH|ULTRA
    --fps N               frames per second (default 30)
    --res WxH             for example 1920x1080 or 3840x2160
    --bpm N               force the tempo instead of detecting it
    --acts a,b,c,...      10 act start times in seconds (skips auto-detection)
    --seed N              a different galaxy
    --output DIR          where frames and videos are written
    --mp4                 render straight to one .mp4 instead of PNG frames
    --render              render the animation after building it
    --frames A-B          render only these frames (for splitting the work)
    --still SECONDS       render one still at this song time (repeatable)
    --save FILE.blend     save the built scene
    --video               join rendered PNG frames and the song into an .mp4
"""

import math
import os
import sys
import time
import warnings

import bpy
import numpy as np
from mathutils import Matrix, Vector

# ============================================================================
#  1. SETTINGS
# ============================================================================

CONFIG = {
    # ---- the song ----------------------------------------------------------
    # Full path to your "Endless Destiny" file. Leave "" and the script looks
    # next to itself for an audio file with "endless" or "destiny" in its name.
    "AUDIO_PATH": "",
    # 0 means detect the tempo from the audio (120 BPM when there's no audio).
    "BPM": 0,
    # Song length in seconds. Only used when there is NO audio file.
    "SONG_SECONDS": 200.0,
    # Optional: 10 act start times in seconds, to place the acts by hand, e.g.
    # [0, 14, 40, 52, 76, 102, 112, 136, 158, 186]. None = automatic.
    "ACT_STARTS": None,

    # ---- rendering ---------------------------------------------------------
    "ENGINE": "EEVEE",           # "EEVEE" (fast, the default) or "CYCLES" (slower, cleanest gas)
    "QUALITY": "HIGH",           # "PREVIEW", "HIGH" or "ULTRA"
    "FPS": 30,
    "RESOLUTION": (1920, 1080),
    "OUTPUT": "PNG",             # "PNG" frames (safe, resumable) or "MP4"
    "OUTPUT_DIR": "",            # "" = a "render" folder next to this script

    # ---- look --------------------------------------------------------------
    "SEED": 7,
    "SHOW_TITLES": True,
    "STUDIO_NAME": "ECHOES IN THE DARK",
    "SONG_TITLE": "ENDLESS DESTINY",
}

QUALITY_PRESETS = {
    #            stars       Cycles spp  EEVEE spp  vol tile  vol samples  motion blur
    "PREVIEW": dict(stars=250_000, cycles=24, eevee=16, tile="8", vsamp=64, mblur=False),
    "HIGH": dict(stars=1_200_000, cycles=64, eevee=64, tile="4", vsamp=128, mblur=True),
    "ULTRA": dict(stars=3_000_000, cycles=160, eevee=128, tile="2", vsamp=256, mblur=True),
}

# The 10 acts. The share is the default fraction of the song each act gets
# before the boundaries are snapped to the real musical changes in the audio.
ACTS = [
    # key        title                       share
    ("INTRO", "Echo in the Dark", 0.07),
    ("VERSE1", "Nursery of Stars", 0.13),
    ("BUILD1", "The Pull", 0.06),
    ("CHORUS1", "Destiny Revealed", 0.12),
    ("VERSE2", "Riding the Arms", 0.13),
    ("BUILD2", "Alignment", 0.05),
    ("CHORUS2", "Written in the Stars", 0.12),
    ("BRIDGE", "Heart of the Galaxy", 0.11),
    ("FINALE", "The Heart Ignites", 0.14),
    ("OUTRO", "Endless", 0.07),
]
ACT_KEYS = [a[0] for a in ACTS]

# Which way the music should move at the start of each act (used to snap act
# boundaries to real drops and breakdowns): +1 louder, -1 quieter, 0 either.
ACT_ENERGY_DIRECTION = {
    "VERSE1": 0, "BUILD1": 0, "CHORUS1": +1, "VERSE2": -1, "BUILD2": 0,
    "CHORUS2": +1, "BRIDGE": -1, "FINALE": +1, "OUTRO": -1,
}

PREFIX = "ED_"
SCENE_NAME = "Endless Destiny"

# Galaxy geometry (Blender units; the disk is about 250 units across).
R0 = 18.0                         # radius where the arms leave the bar
PITCH = math.radians(19.0)        # spiral arm pitch angle
KSP = 2.0 / math.tan(PITCH)       # log-spiral winding constant for m = 2 arms
NEBULA_R = 64.0                   # radius of the Destiny Nebula on arm 0
NEBULA_SIZE = 7.0
BH_RADIUS = 0.5

BLENDER = bpy.app.version


def log(msg):
    print(f"[EndlessDestiny] {msg}", flush=True)


# ============================================================================
#  2. SMALL MATH HELPERS
# ============================================================================

def clip01(x):
    return np.clip(np.asarray(x, dtype=float), 0.0, 1.0)


def smoothstep(e0, e1, x):
    t = clip01((np.asarray(x, dtype=float) - e0) / (e1 - e0))
    return t * t * (3.0 - 2.0 * t)


def smoother(x):
    t = clip01(x)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def ease_in(x, p=2.0):
    return clip01(x) ** p


def ease_out(x, p=2.0):
    return 1.0 - (1.0 - clip01(x)) ** p


def mix(a, b, t):
    return a + (b - a) * t


def mixv(a, b, t):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    t = np.asarray(t, dtype=float)
    return a[None, :] + (b - a)[None, :] * t[:, None]


def loglerp(a, b, t):
    return np.exp(np.log(a) + (np.log(b) - np.log(a)) * np.asarray(t, dtype=float))


def norm(v):
    v = np.asarray(v, dtype=float)
    return v / max(1e-12, float(np.linalg.norm(v)))


def rotz(p, ang):
    p = np.atleast_2d(p)
    ang = np.broadcast_to(np.asarray(ang, dtype=float), (p.shape[0],))
    c, s = np.cos(ang), np.sin(ang)
    return np.stack([c * p[:, 0] - s * p[:, 1], s * p[:, 0] + c * p[:, 1], p[:, 2]], -1)


def sph(d, az, el):
    d, az, el = np.broadcast_arrays(np.asarray(d, float), np.asarray(az, float), np.asarray(el, float))
    return np.stack([d * np.cos(el) * np.cos(az), d * np.cos(el) * np.sin(az), d * np.sin(el)], -1)


def to_sph(p):
    p = np.asarray(p, dtype=float)
    d = float(np.linalg.norm(p))
    return d, math.atan2(p[1], p[0]), math.asin(max(-1.0, min(1.0, p[2] / max(d, 1e-9))))


def slerp_dir(a, b, t):
    a, b = norm(a), norm(b)
    t = np.asarray(t, dtype=float)
    om = math.acos(max(-1.0, min(1.0, float(np.dot(a, b)))))
    if om < 1e-4:
        out = mixv(a, b, t)
    else:
        so = math.sin(om)
        out = (np.sin((1 - t) * om) / so)[:, None] * a[None] + (np.sin(t * om) / so)[:, None] * b[None]
    return out / np.linalg.norm(out, axis=1, keepdims=True)


def wrap_angle(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def timed_spline(times, pts, tq):
    """C1 Hermite spline through pts at the given times (Catmull-Rom tangents)."""
    times = np.asarray(times, dtype=float)
    pts = np.asarray(pts, dtype=float)
    if pts.ndim == 1:
        pts = pts[:, None]
    k = len(times)
    m = np.zeros_like(pts)
    for i in range(k):
        if i == 0:
            m[i] = (pts[1] - pts[0]) / (times[1] - times[0])
        elif i == k - 1:
            m[i] = (pts[-1] - pts[-2]) / (times[-1] - times[-2])
        else:
            m[i] = (pts[i + 1] - pts[i - 1]) / (times[i + 1] - times[i - 1])
    tq = np.asarray(tq, dtype=float)
    idx = np.clip(np.searchsorted(times, tq, side="right") - 1, 0, k - 2)
    t0, t1 = times[idx], times[idx + 1]
    h = (t1 - t0)[:, None]
    s = np.clip((tq - t0) / (t1 - t0), 0.0, 1.0)[:, None]
    h00 = 2 * s**3 - 3 * s**2 + 1
    h10 = s**3 - 2 * s**2 + s
    h01 = -2 * s**3 + 3 * s**2
    h11 = s**3 - s**2
    return h00 * pts[idx] + h10 * h * m[idx] + h01 * pts[idx + 1] + h11 * h * m[idx + 1]


# ---- the spiral: one formula shared by the stars (numpy) and the gas (nodes) --

def arm_warp(r, th):
    return 0.45 * np.sin(r / 13.0 + 0.7) + 0.25 * np.sin(r / 5.1 + 3.0 * th + 1.9)


def arm_phase(r, th):
    return 2.0 * th - KSP * np.log(np.maximum(r, 0.5) / R0) + arm_warp(r, th)


def armness(r, th, p=5.0):
    ph = arm_phase(r, th)
    main = ((1.0 + np.cos(ph)) * 0.5) ** p
    second = 0.25 * ((1.0 - np.cos(ph)) * 0.5) ** (p + 2.0) * smoothstep(40.0, 65.0, r)
    return np.maximum(main, second)


def arm_mask(r):
    return smoothstep(14.0, 26.0, r) * (1.0 - smoothstep(112.0, 140.0, r))


def crest_theta(r, n=0, phi0=0.0):
    """Angle of the crest of arm n at radius r (solves arm_phase = 2*pi*n + phi0)."""
    r = np.asarray(r, dtype=float)
    base = KSP * np.log(np.maximum(r, 0.5) / R0) + 2.0 * math.pi * np.asarray(n, float) + phi0
    th = base / 2.0
    for _ in range(8):
        th = (base - arm_warp(r, th)) / 2.0
    return th


def arm_point(r, n=0, z=0.0):
    th = float(crest_theta(r, n))
    return np.array([r * math.cos(th), r * math.sin(th), z])


def arm_frame(r, n=0):
    """Unit tangent (towards larger r) and lateral vector of arm n at radius r."""
    t = norm(arm_point(r + 0.5, n) - arm_point(r - 0.5, n))
    lat = norm(np.cross([0.0, 0.0, 1.0], t))
    return t, lat


class KeyPoints:
    """Named places in the galaxy (galaxy-local coordinates)."""

    def __init__(self):
        th = float(crest_theta(NEBULA_R, 0))
        self.e_r = np.array([math.cos(th), math.sin(th), 0.0])
        self.e_t = np.array([-math.sin(th), math.cos(th), 0.0])
        self.e_z = np.array([0.0, 0.0, 1.0])
        self.nebula = NEBULA_R * self.e_r + 0.5 * self.e_z
        n, er, et, ez = self.nebula, self.e_r, self.e_t, self.e_z
        self.destiny = n + 3.4 * er - 0.9 * et + 1.1 * ez          # the Destiny Star
        self.cluster = n + 0.6 * er - 0.7 * et + 0.2 * ez          # newborn cluster
        self.center = np.zeros(3)
        # Filled in by the choreographer:
        self.align_cam = None       # the one viewpoint where the constellation aligns
        self.align_tgt = None
        self.align_lens = 38.0
        self.flight_arm = 0
        self.pulsar = None


# ============================================================================
#  3. BLENDER VERSION HELPERS (4.2 / 4.5 / 5.0 differ in a few places)
# ============================================================================

def node_tree_of(idblock):
    """Materials and worlds only need use_nodes switched on before Blender 5.0."""
    if BLENDER < (5, 0, 0) or idblock.node_tree is None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            idblock.use_nodes = True
    return idblock.node_tree


def set_engine(scene, engine):
    if engine == "CYCLES":
        scene.render.engine = "CYCLES"
        return
    for eid in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = eid
            return
        except TypeError:
            continue


def seq_strips(sequence_editor):
    return sequence_editor.strips if hasattr(sequence_editor, "strips") else sequence_editor.sequences


def fcurves_of(idblock):
    """F-curves of an ID. Blender 4.4+ keeps them per action slot (an object and its
    camera data can share one action), older versions keep one flat list."""
    ad = idblock.animation_data
    if ad is None or ad.action is None:
        return []
    act = ad.action
    if hasattr(act, "layers") and getattr(ad, "action_slot", None) is not None:
        try:
            from bpy_extras import anim_utils
            bag = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
            if bag is not None:
                return list(bag.fcurves)
        except (ImportError, AttributeError):
            pass
    return list(getattr(act, "fcurves", []))


def find_fcurve(idblock, path, index):
    for fc in fcurves_of(idblock):
        if fc.data_path == path and fc.array_index == index:
            return fc
    return None


INTERP = {"CONSTANT": 0, "LINEAR": 1, "BEZIER": 2}


def bake(idblock, path, index, frames, values, interp="LINEAR"):
    """Write many keyframes at once (fast, works in 4.2 through 5.0)."""
    frames = np.asarray(frames, dtype=np.float32)
    values = np.asarray(values, dtype=np.float32)
    idblock.keyframe_insert(data_path=path, index=index, frame=float(frames[0]))
    fc = find_fcurve(idblock, path, max(index, 0))
    if fc is None:
        raise RuntimeError(f"could not create an F-curve for {idblock.name}.{path}")
    kp = fc.keyframe_points
    kp.clear()
    kp.add(len(frames))
    co = np.empty(len(frames) * 2, dtype=np.float32)
    co[0::2] = frames
    co[1::2] = values
    kp.foreach_set("co", co)
    kp.foreach_set("interpolation", [INTERP[interp]] * len(frames))
    if interp == "BEZIER":
        for k in kp:
            k.handle_left_type = "AUTO_CLAMPED"
            k.handle_right_type = "AUTO_CLAMPED"
    fc.update()
    return fc


def bake_keys(idblock, path, index, keys, interp="BEZIER"):
    """keys: list of (frame, value). Sorted, de-duplicated sparse keyframes."""
    if not keys:
        return
    keys = sorted(keys, key=lambda k: k[0])
    clean = []
    for f, v in keys:
        if clean and abs(clean[-1][0] - f) < 1e-3:
            clean[-1] = (f, v)
        else:
            clean.append((f, v))
    fr, va = zip(*clean)
    bake(idblock, path, index, fr, va, interp)


def drive(owner, prop, expression, variables, index=-1):
    """Add a driver. variables: {name: (id_block, data_path)}"""
    fc = owner.driver_add(prop, index) if index >= 0 else owner.driver_add(prop)
    if isinstance(fc, list):
        fc = fc[0]
    for m in list(fc.modifiers):
        fc.modifiers.remove(m)
    drv = fc.driver
    drv.type = "SCRIPTED"
    for name, (idb, path) in variables.items():
        v = drv.variables.new()
        v.name = name
        v.type = "SINGLE_PROP"
        tgt = v.targets[0]
        if isinstance(idb, bpy.types.Object):
            tgt.id_type = "OBJECT"
        elif isinstance(idb, bpy.types.Scene):
            tgt.id_type = "SCENE"
        elif isinstance(idb, bpy.types.Camera):
            tgt.id_type = "CAMERA"
        tgt.id = idb
        tgt.data_path = path
    drv.expression = expression
    return fc


def script_dir():
    try:
        f = __file__
        if f and os.path.isfile(f):
            return os.path.dirname(os.path.abspath(f))
    except NameError:
        pass
    for t in bpy.data.texts:
        p = bpy.path.abspath(t.filepath) if t.filepath else ""
        if p and os.path.isfile(p) and "endless" in os.path.basename(p).lower():
            return os.path.dirname(p)
    if bpy.data.filepath:
        return os.path.dirname(bpy.data.filepath)
    return os.getcwd()


# ============================================================================
#  4. NODE BUILDER  (turns little math formulas into node networks)
# ============================================================================

MATH_FUNCS = {
    "sin": "SINE", "cos": "COSINE", "tan": "TANGENT", "exp": "EXPONENT",
    "sqrt": "SQRT", "abs": "ABSOLUTE", "floor": "FLOOR", "fract": "FRACT",
    "min": "MINIMUM", "max": "MAXIMUM", "pow": "POWER", "atan2": "ARCTAN2",
    "sign": "SIGN", "tanh": "TANH", "gt": "GREATER_THAN", "lt": "LESS_THAN",
    "log": "LOGARITHM", "mod": "FLOORED_MODULO",
}


class NodeBuilder:
    """Adds nodes to a tree with a tidy left-to-right layout.

    nb.ex("exp(-r/30) * pow(0.5 + 0.5*cos(phi), 5)", r=sock_r, phi=sock_phi)
    builds the Math nodes for that formula and returns the output socket.
    """

    def __init__(self, tree, clear=True):
        self.tree = tree
        if clear:
            tree.nodes.clear()
        self.depth = {}
        self.rows = {}
        self.cache = {}

    # ---- layout ----------------------------------------------------------
    def _place(self, node, depth):
        row = self.rows.get(depth, 0)
        self.rows[depth] = row + 1
        node.location = (depth * 200.0, -row * 160.0)
        self.depth[node.name] = depth

    @staticmethod
    def _sock(collection, key):
        if isinstance(key, int):
            return collection[key]
        for s in collection:
            if s.identifier == key:
                return s
        for s in collection:
            if s.name == key and s.enabled:
                return s
        return collection[key]

    def node(self, type_, ins=None, **props):
        n = self.tree.nodes.new(type_)
        for k, v in props.items():
            setattr(n, k, v)
        d = 0
        for key, val in (ins or {}).items():
            if val is None:
                continue
            sock = self._sock(n.inputs, key)
            if isinstance(val, bpy.types.NodeSocket):
                self.tree.links.new(val, sock)
                d = max(d, self.depth.get(val.node.name, 0) + 1)
            else:
                sock.default_value = val
        self._place(n, d)
        return n

    def out(self, node, key=0):
        return self._sock(node.outputs, key)

    def link(self, a, b):
        self.tree.links.new(a, b)

    # ---- math ------------------------------------------------------------
    def math(self, op, a, b=None, c=None, clamp=False):
        ins = {0: a}
        if b is not None:
            ins[1] = float(b) if isinstance(b, (int, float)) else b
        if c is not None:
            ins[2] = float(c) if isinstance(c, (int, float)) else c
        if isinstance(a, (int, float)):
            ins[0] = float(a)
        return self.node("ShaderNodeMath", ins, operation=op, use_clamp=clamp).outputs[0]

    def ex(self, src, **env):
        import ast
        return self._emit(ast.parse(src.strip(), mode="eval").body, env)

    def _emit(self, n, env):
        import ast
        if isinstance(n, ast.Constant):
            return float(n.value)
        if isinstance(n, ast.Name):
            v = env[n.id]
            return float(v) if isinstance(v, (int, float)) else v
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            v = self._emit(n.operand, env)
            return -v if isinstance(v, float) else self.math("MULTIPLY", v, -1.0)
        if isinstance(n, ast.BinOp):
            a = self._emit(n.left, env)
            b = self._emit(n.right, env)
            if isinstance(a, float) and isinstance(b, float):
                return float(eval(compile(ast.Expression(n), "<c>", "eval"), {}, {}))
            op = {ast.Add: "ADD", ast.Sub: "SUBTRACT", ast.Mult: "MULTIPLY",
                  ast.Div: "DIVIDE", ast.Pow: "POWER", ast.Mod: "FLOORED_MODULO"}[type(n.op)]
            if isinstance(a, float):
                node = self.node("ShaderNodeMath", {0: a, 1: b}, operation=op)
                return node.outputs[0]
            return self.math(op, a, b)
        if isinstance(n, ast.Call):
            fname = n.func.id
            args = [self._emit(a, env) for a in n.args]
            if fname == "ln":
                return self.math("LOGARITHM", args[0], math.e)
            if fname == "clamp":
                if len(args) == 1:
                    return self.math("MULTIPLY", args[0], 1.0, clamp=True)
                return self.node("ShaderNodeClamp", {"Value": args[0], "Min": args[1], "Max": args[2]}).outputs[0]
            if fname == "smoothstep":
                return self.node("ShaderNodeMapRange", {"Value": args[2], "From Min": args[0], "From Max": args[1],
                                                        "To Min": 0.0, "To Max": 1.0},
                                 interpolation_type="SMOOTHSTEP", clamp=True).outputs[0]
            if fname == "mix":
                a, b, t = args
                return self._emit(ast.parse("A + (B - A) * T", mode="eval").body, {"A": a, "B": b, "T": t})
            if fname == "noise":           # noise(vector_socket, scale, detail, roughness)
                return self.noise(*args).outputs["Fac"]
            op = MATH_FUNCS[fname]
            return self.math(op, *args)
        raise ValueError(f"unsupported expression node {ast.dump(n)}")

    # ---- vectors / colours -------------------------------------------------
    def combine(self, x, y, z):
        return self.node("ShaderNodeCombineXYZ", {0: x, 1: y, 2: z}).outputs[0]

    def separate(self, v):
        n = self.node("ShaderNodeSeparateXYZ", {0: v})
        return n.outputs[0], n.outputs[1], n.outputs[2]

    def vmath(self, op, a, b=None, scale=None):
        ins = {0: a}
        if b is not None:
            ins[1] = b
        if scale is not None:
            ins[3] = scale
        n = self.node("ShaderNodeVectorMath", ins, operation=op)
        return n.outputs["Value"] if op in ("LENGTH", "DOT_PRODUCT", "DISTANCE") else n.outputs["Vector"]

    def rgb(self, color, strength):
        """colour (tuple or socket) * strength (float socket) -> colour socket"""
        if isinstance(color, (tuple, list)):
            color = tuple(color[:3])
        return self.vmath("SCALE", color, scale=strength)

    def add(self, *vecs):
        acc = vecs[0]
        for v in vecs[1:]:
            acc = self.vmath("ADD", acc, v)
        return acc

    def noise(self, vec, scale=1.0, detail=2.0, rough=0.5, lac=2.0, dims="3D"):
        n = self.node("ShaderNodeTexNoise", {"Vector": vec, "Scale": scale, "Detail": detail,
                                              "Roughness": rough, "Lacunarity": lac})
        n.noise_dimensions = dims
        return n

    def voronoi(self, vec, scale=1.0, randomness=1.0, feature="F1"):
        n = self.node("ShaderNodeTexVoronoi", {"Vector": vec, "Scale": scale, "Randomness": randomness})
        n.voronoi_dimensions = "3D"
        n.feature = feature
        return n

    def value(self, v=0.0, label=""):
        n = self.node("ShaderNodeValue")
        n.outputs[0].default_value = v
        if label:
            n.label = label
        return n.outputs[0]


# ============================================================================
#  5. COLOUR SCIENCE  (blackbody temperature -> linear RGB)
# ============================================================================

def _blackbody_lut():
    T = np.geomspace(1200.0, 45000.0, 600)
    lam_nm = np.arange(380.0, 781.0, 4.0)
    lam = lam_nm * 1e-9

    def g(x, mu, s1, s2):
        s = np.where(x < mu, s1, s2)
        return np.exp(-0.5 * ((x - mu) / s) ** 2)

    xb = 1.056 * g(lam_nm, 599.8, 37.9, 31.0) + 0.362 * g(lam_nm, 442.0, 16.0, 26.7) - 0.065 * g(lam_nm, 501.1, 20.4, 26.2)
    yb = 0.821 * g(lam_nm, 568.8, 46.9, 40.5) + 0.286 * g(lam_nm, 530.9, 16.3, 31.1)
    zb = 1.217 * g(lam_nm, 437.0, 11.8, 36.0) + 0.681 * g(lam_nm, 459.0, 26.0, 13.8)
    planck = 1.0 / (lam[None, :] ** 5 * (np.exp(1.4388e-2 / (lam[None, :] * T[:, None])) - 1.0))
    xyz = np.stack([(planck * xb).sum(1), (planck * yb).sum(1), (planck * zb).sum(1)], 1)
    m = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]])
    rgb = np.clip(xyz @ m.T, 0.0, None)
    rgb /= rgb.max(1, keepdims=True)
    # A touch more saturation than nature, so the colours read on screen.
    lum = (rgb @ np.array([0.2126, 0.7152, 0.0722]))[:, None]
    rgb = np.clip(lum + (rgb - lum) * 1.55, 0.0, None)
    rgb /= rgb.max(1, keepdims=True)
    return T, rgb


_BB_T, _BB_RGB = _blackbody_lut()


def blackbody(temps):
    lt = np.log(np.clip(temps, _BB_T[0], _BB_T[-1]))
    lT = np.log(_BB_T)
    return np.stack([np.interp(lt, lT, _BB_RGB[:, c]) for c in range(3)], 1)


# ============================================================================
#  6. THE SONG  (audio analysis, tempo, beats, and the act timeline)
# ============================================================================

AUDIO_EXTS = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".opus", ".aif", ".aiff")


def find_audio(explicit):
    if explicit:
        p = bpy.path.abspath(explicit)
        if os.path.isfile(p):
            return p
        log(f"WARNING: audio file not found: {p}")
    dirs = [script_dir()]
    if bpy.data.filepath:
        dirs.append(os.path.dirname(bpy.data.filepath))
    dirs.append(os.getcwd())
    for d in dirs:
        try:
            names = sorted(os.listdir(d))
        except OSError:
            continue
        for f in names:
            low = f.lower()
            if low.endswith(AUDIO_EXTS) and ("endless" in low or "destiny" in low):
                return os.path.join(d, f)
    return None


def load_audio(path):
    """Return (mono float32 samples, sample rate). Tries Blender's audio library,
    then Python's wave module, then an ffmpeg on the PATH."""
    data, sr = None, None
    try:
        import aud
        snd = aud.Sound(path)
        sr = float(snd.specs[0])
        arr = np.asarray(snd.data(), dtype=np.float32)
        data = arr.mean(axis=1) if arr.ndim == 2 else arr
    except Exception as e:  # noqa: BLE001
        log(f"Blender's audio reader could not open the song ({e}); trying fallbacks")
    if data is None and path.lower().endswith(".wav"):
        try:
            import wave
            with wave.open(path, "rb") as w:
                sr = float(w.getframerate())
                ch, sw, n = w.getnchannels(), w.getsampwidth(), w.getnframes()
                raw = w.readframes(n)
            dt = {1: np.uint8, 2: np.int16, 4: np.int32}[sw]
            a = np.frombuffer(raw, dtype=dt).astype(np.float32)
            if sw == 1:
                a = (a - 128.0) / 128.0
            else:
                a /= float(2 ** (8 * sw - 1))
            data = a.reshape(-1, ch).mean(axis=1)
        except Exception as e:  # noqa: BLE001
            log(f"wave reader failed ({e})")
    if data is None:
        import shutil
        import subprocess
        exe = shutil.which("ffmpeg")
        if exe:
            try:
                raw = subprocess.run([exe, "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "22050", "-"],
                                     capture_output=True, check=True).stdout
                data, sr = np.frombuffer(raw, dtype=np.float32).copy(), 22050.0
            except Exception as e:  # noqa: BLE001
                log(f"ffmpeg reader failed ({e})")
    if data is None or len(data) < 1000:
        return None, None
    factor = int(round(sr / 22050.0))
    if factor >= 2:
        n = len(data) // factor * factor
        data = data[:n].reshape(-1, factor).mean(axis=1)
        sr = sr / factor
    return data.astype(np.float32), sr


def _envelope(x, fps, attack, release):
    """Peak-follower: fast rise, exponential fall (times in seconds)."""
    out = np.zeros_like(x)
    a = math.exp(-1.0 / max(1e-3, attack * fps)) if attack > 0 else 0.0
    r = math.exp(-1.0 / max(1e-3, release * fps))
    y = 0.0
    for i, v in enumerate(x):
        y = (a * y + (1 - a) * v) if v > y else (r * y + (1 - r) * v)
        out[i] = y
    return out


def _normalize(x, lo=5.0, hi=97.0):
    a, b = np.percentile(x, lo), np.percentile(x, hi)
    return clip01((x - a) / max(1e-9, b - a))


def _moving_avg(x, n):
    n = max(1, int(n))
    if n == 1:
        return x.copy()
    k = np.ones(n) / n
    pad = np.pad(x, (n // 2, n - 1 - n // 2), mode="edge")
    return np.convolve(pad, k, mode="valid")


def _pulses(times, strengths, n_frames, fps, decay):
    out = np.zeros(n_frames)
    fr = np.arange(n_frames) / fps
    for t, s in zip(times, strengths):
        i0 = int(math.floor(t * fps))
        i1 = min(n_frames, i0 + int(decay * fps * 6) + 2)
        if i0 >= n_frames or i1 <= 0:
            continue
        seg = fr[max(0, i0):i1] - t
        val = np.where(seg >= -0.5 / fps, s * np.exp(-np.maximum(seg, 0.0) / decay), 0.0)
        out[max(0, i0):i1] = np.maximum(out[max(0, i0):i1], val)
    return out


class Song:
    """Everything the animation needs to know about the music."""

    def __init__(self, fps, audio_path=None, bpm=0.0, fallback_seconds=200.0, act_starts=None):
        self.fps = fps
        self.audio_path = audio_path
        self.has_audio = False
        samples, sr = (None, None)
        if audio_path:
            samples, sr = load_audio(audio_path)
        if samples is not None:
            self.has_audio = True
            self.duration = len(samples) / sr
        else:
            if audio_path:
                log("Could not read the audio; running without it.")
            self.duration = float(fallback_seconds)
        self.n_frames = int(math.ceil(self.duration * fps))
        self.t = np.arange(self.n_frames) / fps
        if self.has_audio:
            self._analyze(samples, sr, bpm)
        else:
            self.bpm = float(bpm) if bpm else 120.0
            self.beat_phase = 0.5
        self._make_beats()
        self._place_acts(act_starts)
        self._act_arrays()
        if not self.has_audio:
            self._synthesize()

    # ---- audio analysis --------------------------------------------------
    def _analyze(self, x, sr, bpm_hint):
        fps, nf = self.fps, self.n_frames
        n = 2048
        win = np.hanning(n).astype(np.float32)
        freqs = np.fft.rfftfreq(n, 1.0 / sr)
        bands = {"bass": (25, 150), "lowmid": (150, 500), "mid": (500, 2500), "high": (2500, 11000)}
        masks = {k: (freqs >= lo) & (freqs < hi) for k, (lo, hi) in bands.items()}
        edges = np.geomspace(40.0, min(11000.0, sr / 2 - 1), 17)
        tim_masks = [(freqs >= edges[i]) & (freqs < edges[i + 1]) for i in range(16)]
        pad = np.concatenate([np.zeros(n, np.float32), x, np.zeros(2 * n, np.float32)])
        band_e = {k: np.zeros(nf) for k in bands}
        timbre = np.zeros((nf, 16))
        rms = np.zeros(nf)
        flux = np.zeros(nf)
        bflux = np.zeros(nf)
        hflux = np.zeros(nf)
        prev = None
        offs = np.arange(-n // 2, n // 2)
        for c0 in range(0, nf, 400):
            idx = np.arange(c0, min(nf, c0 + 400))
            centers = ((idx + 0.5) / fps * sr).astype(np.int64) + n
            seg = pad[centers[:, None] + offs[None, :]]
            rms[idx] = np.sqrt((seg ** 2).mean(axis=1) + 1e-12)
            spec = np.abs(np.fft.rfft(seg * win, axis=1)).astype(np.float32)
            p = spec ** 2
            for k, m in masks.items():
                band_e[k][idx] = p[:, m].sum(axis=1)
            for i, m in enumerate(tim_masks):
                timbre[idx, i] = np.log10(p[:, m].sum(axis=1) + 1e-9)
            lg = np.log1p(spec * 10.0)
            if prev is None:
                prev = lg[:1]
            d = np.diff(np.concatenate([prev, lg], axis=0), axis=0)
            d = np.maximum(d, 0.0)
            flux[idx] = d.sum(axis=1)
            bflux[idx] = d[:, masks["bass"]].sum(axis=1)
            hflux[idx] = d[:, masks["high"]].sum(axis=1)
            prev = lg[-1:]

        db = lambda e: 10.0 * np.log10(e + 1e-10)  # noqa: E731
        self.energy = _moving_avg(_normalize(20.0 * np.log10(rms + 1e-6)), 0.35 * fps)
        self.bass = _envelope(_normalize(db(band_e["bass"]), 20, 99), fps, 0.0, 0.18)
        self.mid = _envelope(_normalize(db(band_e["mid"]), 20, 99), fps, 0.0, 0.25)
        self.sparkle = _envelope(_normalize(hflux, 30, 99.5), fps, 0.0, 0.12)

        # kicks = peaks in the bass-band onset strength
        b = bflux / max(1e-9, np.percentile(bflux, 99.0))
        avg = _moving_avg(b, 0.5 * fps)
        kicks, strengths = [], []
        last = -1.0
        for i in range(1, nf - 1):
            if b[i] >= b[i - 1] and b[i] > b[i + 1] and b[i] > 0.28 and b[i] > avg[i] * 1.35:
                t = i / fps
                if t - last >= 0.14:
                    kicks.append(t)
                    strengths.append(min(1.0, b[i]))
                    last = t
        self.kick_times = np.array(kicks)
        self.kick_strength = np.array(strengths)

        # tempo from a finer onset envelope
        hop = 256
        n2 = 1024
        win2 = np.hanning(n2).astype(np.float32)
        frames = (len(x) - n2) // hop
        env = np.zeros(max(frames, 1))
        prev = None
        for c0 in range(0, frames, 2000):
            idx = np.arange(c0, min(frames, c0 + 2000))
            seg = x[idx[:, None] * hop + np.arange(n2)[None, :]]
            lg = np.log1p(np.abs(np.fft.rfft(seg * win2, axis=1)) * 10.0)
            if prev is None:
                prev = lg[:1]
            d = np.maximum(np.diff(np.concatenate([prev, lg]), axis=0), 0.0)
            env[idx] = d.sum(axis=1)
            prev = lg[-1:]
        rate = sr / hop
        self._onset_offset = 0.5 * n2 / sr
        env = env - _moving_avg(env, rate * 1.0)
        env = np.maximum(env, 0.0)
        self._onset_env, self._onset_rate = env, rate
        self.bpm, self.beat_phase = self._tempo(env, rate, bpm_hint)

        # novelty curve for section boundaries (2 blocks per second)
        blk = max(1, int(fps // 2))
        nb = nf // blk
        feats = np.concatenate([timbre[: nb * blk].reshape(nb, blk, 16).mean(1),
                                (self.energy[: nb * blk].reshape(nb, blk).mean(1) * 6.0)[:, None]], axis=1)
        feats = (feats - feats.mean(0)) / (feats.std(0) + 1e-6)
        en_blk = self.energy[: nb * blk].reshape(nb, blk).mean(1)
        csum = np.concatenate([np.zeros((1, feats.shape[1])), np.cumsum(feats, 0)])
        nov = np.zeros(nb)
        for w in (6, 12, 20):
            for i in range(w, nb - w):
                before = (csum[i] - csum[i - w]) / w
                after = (csum[i + w] - csum[i]) / w
                nov[i] += np.linalg.norm(after - before) / math.sqrt(feats.shape[1])
        nov /= max(1e-9, nov.max())

        # how much the bass and the loudness jump across every point (4 s either side)
        def jump(v, w=8):
            cs = np.concatenate([[0.0], np.cumsum(v)])
            out = np.zeros(nb)
            for i in range(w, nb - w):
                out[i] = (cs[i + w] - cs[i]) / w - (cs[i] - cs[i - w]) / w
            return out
        # linear amplitudes (not dB) so a drop stands out even after a loud build
        bass_amp = _moving_avg(np.sqrt(band_e["bass"]), 0.5 * fps)
        bass_amp /= np.percentile(bass_amp, 98) + 1e-9
        loud_amp = _moving_avg(rms, 0.5 * fps)
        loud_amp /= np.percentile(loud_amp, 98) + 1e-9
        d_bass = jump(bass_amp[: nb * blk].reshape(nb, blk).mean(1))
        d_en = jump(loud_amp[: nb * blk].reshape(nb, blk).mean(1))
        self._d_bass_norm = max(1e-6, float(np.percentile(np.abs(d_bass), 98)))
        self._d_en_norm = max(1e-6, float(np.percentile(np.abs(d_en), 98)))
        cands = []
        for i in range(1, nb - 1):
            is_nov = nov[i] >= nov[i - 1] and nov[i] >= nov[i + 1] and nov[i] > 0.12
            is_rise = d_bass[i] >= d_bass[i - 1] and d_bass[i] >= d_bass[i + 1] and d_bass[i] > 0.3 * self._d_bass_norm
            is_fall = d_en[i] <= d_en[i - 1] and d_en[i] <= d_en[i + 1] and d_en[i] < -0.3 * self._d_en_norm
            if is_nov or is_rise or is_fall:
                cands.append((i * blk / fps, float(nov[i]), float(d_en[i]), float(d_bass[i])))
        # keep the most eventful candidate in every 2.5-second neighbourhood
        eventful = lambda c: c[1] + abs(c[2]) / self._d_en_norm + abs(c[3]) / self._d_bass_norm  # noqa: E731
        cands.sort(key=lambda c: -eventful(c))
        kept = []
        for c in cands:
            if all(abs(c[0] - q[0]) >= 2.5 for q in kept):
                kept.append(c)
        self.boundaries = sorted(kept)

    def _tempo(self, env, rate, bpm_hint):
        dur = len(env) / rate
        t_env = np.arange(len(env)) / rate + self._onset_offset
        if bpm_hint:
            bpm0 = float(bpm_hint)
        else:
            x = env - env.mean()
            f = np.fft.rfft(x, 2 * len(x))
            ac = np.fft.irfft(f * np.conj(f))[: len(x)]
            lags = np.arange(len(ac))
            with np.errstate(divide="ignore"):
                bpm = 60.0 * rate / np.maximum(lags, 1)
            valid = (bpm >= 60) & (bpm <= 200)
            prior = np.exp(-0.5 * (np.log2(bpm / 120.0) / 0.9) ** 2)
            score = np.where(valid, ac * prior, -np.inf)
            L = int(np.argmax(score))
            if 1 <= L < len(ac) - 1:
                y0, y1, y2 = ac[L - 1], ac[L], ac[L + 1]
                den = y0 - 2 * y1 + y2
                L = L + (0.5 * (y0 - y2) / den if abs(den) > 1e-12 else 0.0)
            bpm0 = 60.0 * rate / max(L, 1e-6)
            while bpm0 < 80:
                bpm0 *= 2
            while bpm0 > 170:
                bpm0 /= 2
        best = (-1.0, bpm0, 0.0)
        for bpm in np.linspace(bpm0 * 0.985, bpm0 * 1.015, 121):
            period = 60.0 / bpm
            beats = np.arange(0.0, dur, period)
            phases = np.linspace(0.0, period, 48, endpoint=False)
            vals = np.interp(beats[None, :] + phases[:, None], t_env, env, right=0.0)
            s = vals.mean(1)
            j = int(np.argmax(s))
            if s[j] > best[0]:
                best = (float(s[j]), float(bpm), float(phases[j]))
        return best[1], best[2]

    def _make_beats(self):
        period = 60.0 / self.bpm
        self.beat_times = np.arange(self.beat_phase % period, self.duration, period)
        down = 0
        if self.has_audio and len(self.beat_times) >= 8:
            b = np.interp(self.beat_times, self.t, self.bass)
            scores = [b[k::4].mean() for k in range(4)]
            down = int(np.argmax(scores))
        self.downbeat_offset = down
        self.downbeats = self.beat_times[down::4]

    # ---- the 10 acts -----------------------------------------------------
    def _place_acts(self, manual):
        T = self.duration
        shares = np.array([a[2] for a in ACTS])
        default = np.concatenate([[0.0], np.cumsum(shares)[:-1] / shares.sum() * T])
        self.act_source = ["start"]
        if manual:
            starts = [float(v) for v in manual][: len(ACTS)]
            if len(starts) == len(ACTS) and all(b > a for a, b in zip(starts, starts[1:])) and starts[-1] < T:
                self.act_starts = np.array(starts)
                self.act_source = ["manual"] * len(ACTS)
                return
            log("ACT_STARTS ignored: it needs 10 increasing times inside the song")
        starts = [0.0]
        min_len = max(3.0, 0.025 * T)
        peaks = getattr(self, "boundaries", [])
        for k in range(1, len(ACTS)):
            d = default[k]
            lo = starts[-1] + min_len
            hi = T - min_len * (len(ACTS) - k)
            win = max(10.0, 0.1 * T)
            want = ACT_ENERGY_DIRECTION.get(ACT_KEYS[k], 0)
            best, best_score = None, 0.2
            for (t, nov, d_en, d_bass) in peaks:
                if t < max(lo, d - win) or t > min(hi, d + win):
                    continue
                up_b, up_e = d_bass / self._d_bass_norm, d_en / self._d_en_norm
                if want > 0:      # a drop: the bass and the loudness jump up
                    score = 0.45 * nov + 1.0 * np.clip(up_b, 0, 1) + 0.35 * np.clip(up_e, 0, 1)
                elif want < 0:    # a breakdown: things get quieter
                    score = 0.45 * nov + 1.0 * np.clip(-up_e, 0, 1) + 0.35 * np.clip(-up_b, 0, 1)
                else:
                    score = nov
                score *= 1.0 - 0.5 * abs(t - d) / win
                if score > best_score:
                    best, best_score = t, score
            if best is not None:
                t, src = best, "music"
            else:
                t, src = float(np.clip(d, lo, hi)), "default"
            if len(self.downbeats):
                j = int(np.argmin(np.abs(self.downbeats - t)))
                if abs(self.downbeats[j] - t) <= 60.0 / self.bpm * 2.1 and lo <= self.downbeats[j] <= hi:
                    t = float(self.downbeats[j])
                    src += "+bar"
            starts.append(t)
            self.act_source.append(src)
        self.act_starts = np.array(starts)

    def _act_arrays(self):
        self.act_ends = np.append(self.act_starts[1:], self.duration)
        self.act_frame0 = np.round(self.act_starts * self.fps).astype(int)
        self.act_frame1 = np.append(self.act_frame0[1:], self.n_frames)
        self.act_index = np.zeros(self.n_frames, dtype=int)
        self.act_u = np.zeros(self.n_frames)
        for k in range(len(ACTS)):
            f0, f1 = self.act_frame0[k], self.act_frame1[k]
            self.act_index[f0:f1] = k
            self.act_u[f0:f1] = (np.arange(f0, f1) - f0) / max(1, f1 - f0)

    def act(self, key):
        k = ACT_KEYS.index(key)
        return self.act_starts[k], self.act_ends[k]

    def frames_of(self, key):
        k = ACT_KEYS.index(key)
        return int(self.act_frame0[k]), int(self.act_frame1[k])

    # ---- a stand-in "song" when there's no audio file ------------------------
    def _synthesize(self):
        fps, nf = self.fps, self.n_frames
        level = {"INTRO": 0.18, "VERSE1": 0.45, "BUILD1": 0.6, "CHORUS1": 0.95, "VERSE2": 0.5,
                 "BUILD2": 0.62, "CHORUS2": 1.0, "BRIDGE": 0.32, "FINALE": 1.0, "OUTRO": 0.3}
        e = np.array([level[ACT_KEYS[k]] for k in self.act_index])
        u = self.act_u
        for key in ("BUILD1", "BUILD2"):
            m = self.act_index == ACT_KEYS.index(key)
            e[m] += 0.35 * u[m] ** 2
        m = self.act_index == ACT_KEYS.index("OUTRO")
        e[m] *= 1.0 - 0.8 * u[m]
        self.energy = _moving_avg(e, fps * 0.8)
        kicks, strengths = [], []
        for i, bt in enumerate(self.beat_times):
            k = self.act_index[min(nf - 1, int(bt * fps))]
            key = ACT_KEYS[k]
            if key in ("CHORUS1", "CHORUS2", "FINALE"):
                kicks.append(bt); strengths.append(1.0)
            elif key in ("VERSE1", "VERSE2"):
                if i % 2 == 0:
                    kicks.append(bt); strengths.append(0.7)
            elif key in ("BUILD1", "BUILD2"):
                kicks.append(bt); strengths.append(0.6)
                kicks.append(bt + 30.0 / self.bpm); strengths.append(0.45)
            elif key in ("INTRO", "OUTRO"):
                if i % 2 == 0:  # heartbeat: lub-dub
                    kicks.append(bt); strengths.append(0.55)
                    kicks.append(bt + 0.22); strengths.append(0.35)
            elif key == "BRIDGE" and i % 4 == 0:
                kicks.append(bt); strengths.append(0.5)
        self.kick_times = np.array(kicks)
        self.kick_strength = np.array(strengths)
        kick = _pulses(self.kick_times, self.kick_strength, nf, fps, 0.16)
        self.bass = np.clip(_envelope(kick, fps, 0.0, 0.2) * 0.8 + self.energy * 0.3, 0, 1)
        self.mid = np.clip(self.energy * 0.9, 0, 1)
        hats = _pulses(self.beat_times + 30.0 / self.bpm, np.full(len(self.beat_times), 0.7), nf, fps, 0.08)
        self.sparkle = np.clip(hats * self.energy, 0, 1)

    # ---- per-frame pulses the visuals use -----------------------------------
    def pulses(self):
        kick = _pulses(self.kick_times, self.kick_strength, self.n_frames, self.fps, 0.16)
        strength = np.where((np.arange(len(self.beat_times)) - self.downbeat_offset) % 4 == 0, 1.0, 0.6)
        beat = _pulses(self.beat_times, strength, self.n_frames, self.fps, 0.2)
        return kick, beat

    def report(self):
        m, s = divmod(self.duration, 60)
        log(f"Song: {int(m)}:{s:04.1f} long, {self.bpm:.1f} BPM, {self.n_frames} frames at {self.fps} fps"
            + ("" if self.has_audio else "  (no audio file: using a stand-in rhythm)"))
        log("  act                        starts   ends     placed by")
        for k, (key, title, _) in enumerate(ACTS):
            a, b = self.act_starts[k], self.act_ends[k]
            log(f"  {k + 1:>2}. {key:<8} {title:<21} {int(a // 60)}:{a % 60:04.1f}   "
                f"{int(b // 60)}:{b % 60:04.1f}   {self.act_source[k]}")


# ============================================================================
#  7. THE DIRECTOR  (animated channels that everything listens to)
# ============================================================================

class Director:
    """An empty whose custom properties are keyframed every frame. Materials read
    them through drivers, so one baked curve can steer many shaders."""

    def __init__(self, scene, coll, n_frames):
        self.obj = bpy.data.objects.new(PREFIX + "Director", None)
        self.obj.empty_display_size = 2.0
        coll.objects.link(self.obj)
        self.obj.hide_render = True
        self.frames = np.arange(1, n_frames + 1)
        self.channels = {}

    def set(self, name, values):
        values = np.asarray(values, dtype=float)
        self.channels[name] = values
        self.obj[name] = float(values[0])

    def get(self, name):
        return self.channels[name]

    def bake(self):
        for name, values in self.channels.items():
            bake(self.obj, f'["{name}"]', -1, self.frames, values)

    def path(self, name):
        return (self.obj, f'["{name}"]')


def channel_value(nb, director, expression, label, **names):
    """A Value node driven by director channels, e.g. channel_value(nb, d, "u*g", "glow", u="universe", g="galaxy_gain")."""
    key = (expression, tuple(sorted(names.items())))
    if key in nb.cache:
        return nb.cache[key]
    sock = nb.value(0.0, label)
    drive(sock, "default_value", expression, {v: director.path(c) for v, c in names.items()})
    nb.cache[key] = sock
    return sock


# ============================================================================
#  8. BUILDING BLOCKS  (meshes, objects, materials)
# ============================================================================

def new_collection(name, parent):
    c = bpy.data.collections.new(PREFIX + name)
    parent.children.link(c)
    return c


def new_object(name, data, coll, parent=None, location=(0, 0, 0)):
    ob = bpy.data.objects.new(PREFIX + name, data)
    coll.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    ob.location = location
    return ob


def point_mesh(name, pts, attrs=None):
    me = bpy.data.meshes.new(PREFIX + name)
    pts = np.asarray(pts, dtype=np.float32).reshape(-1, 3)
    me.vertices.add(len(pts))
    me.vertices.foreach_set("co", pts.ravel())
    for key, val in (attrs or {}).items():
        val = np.asarray(val, dtype=np.float32)
        if val.ndim == 2:
            a = me.attributes.new(key, "FLOAT_COLOR", "POINT")
            rgba = np.concatenate([val[:, :3], np.ones((len(val), 1), np.float32)], 1)
            a.data.foreach_set("color", rgba.ravel())
        else:
            a = me.attributes.new(key, "FLOAT", "POINT")
            a.data.foreach_set("value", val.ravel())
    me.update()
    return me


def quad_mesh(name, centers, us, vs, attrs=None):
    """Many quads: centre c, half-axis vectors u and v. UVs run -1..1 across each."""
    centers = np.asarray(centers, float).reshape(-1, 3)
    us = np.asarray(us, float).reshape(-1, 3)
    vs = np.asarray(vs, float).reshape(-1, 3)
    n = len(centers)
    corners = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]], float)
    verts = centers[:, None, :] + corners[None, :, 0:1] * us[:, None, :] + corners[None, :, 1:2] * vs[:, None, :]
    me = bpy.data.meshes.new(PREFIX + name)
    me.vertices.add(n * 4)
    me.vertices.foreach_set("co", verts.astype(np.float32).ravel())
    me.loops.add(n * 4)
    me.loops.foreach_set("vertex_index", np.arange(n * 4, dtype=np.int32))
    me.polygons.add(n)
    me.polygons.foreach_set("loop_start", np.arange(0, n * 4, 4, dtype=np.int32))
    uv = me.uv_layers.new(name="UVMap")
    uvs = np.tile(((corners + 1.0) * 0.5).ravel(), n).astype(np.float32)
    uv.data.foreach_set("uv", uvs)
    for key, val in (attrs or {}).items():
        val = np.repeat(np.asarray(val, np.float32), 4, axis=0)
        if val.ndim == 2:
            a = me.attributes.new(key, "FLOAT_COLOR", "POINT")
            rgba = np.concatenate([val[:, :3], np.ones((len(val), 1), np.float32)], 1)
            a.data.foreach_set("color", rgba.ravel())
        else:
            a = me.attributes.new(key, "FLOAT", "POINT")
            a.data.foreach_set("value", val)
    me.update()
    me.validate()
    return me


def disc_mesh(name, r_in, r_out, seg=128, rings=12):
    """Flat annulus in the XY plane."""
    verts, faces = [], []
    for j in range(rings + 1):
        r = r_in + (r_out - r_in) * (j / rings)
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append((r * math.cos(a), r * math.sin(a), 0.0))
    for j in range(rings):
        for i in range(seg):
            a, b = j * seg + i, j * seg + (i + 1) % seg
            faces.append((a, b, b + seg, a + seg))
    me = bpy.data.meshes.new(PREFIX + name)
    me.from_pydata(verts, [], faces)
    me.update()
    return me


def cylinder_mesh(name, radius, z0, z1, seg=64, caps=True, r1=None, rings=1):
    r1 = radius if r1 is None else r1
    verts, faces = [], []
    for j in range(rings + 1):
        f = j / rings
        z = z0 + (z1 - z0) * f
        r = radius + (r1 - radius) * f
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for j in range(rings):
        for i in range(seg):
            a, b = j * seg + i, j * seg + (i + 1) % seg
            faces.append((a, b, b + seg, a + seg))
    if caps:
        faces.append(tuple(range(seg - 1, -1, -1)))
        faces.append(tuple(range(rings * seg, rings * seg + seg)))
    me = bpy.data.meshes.new(PREFIX + name)
    me.from_pydata(verts, [], faces)
    me.update()
    return me


def sphere_mesh(name, radius, seg=48, rings=24):
    verts, faces = [], []
    for j in range(1, rings):
        th = math.pi * j / rings
        for i in range(seg):
            ph = 2 * math.pi * i / seg
            verts.append((radius * math.sin(th) * math.cos(ph), radius * math.sin(th) * math.sin(ph), radius * math.cos(th)))
    top, bot = len(verts), len(verts) + 1
    verts += [(0, 0, radius), (0, 0, -radius)]
    # winding chosen so every normal points outwards (Cycles needs that to know
    # when a ray enters or leaves a volume)
    for j in range(rings - 2):
        for i in range(seg):
            a, b = j * seg + i, j * seg + (i + 1) % seg
            faces.append((a, a + seg, b + seg, b))
    last = (rings - 2) * seg
    for i in range(seg):
        faces.append((top, i, (i + 1) % seg))
        faces.append((bot, last + (i + 1) % seg, last + i))
    me = bpy.data.meshes.new(PREFIX + name)
    me.from_pydata(verts, [], faces)
    for p in me.polygons:
        p.use_smooth = True
    me.update()
    return me


def new_material(name, additive=False):
    m = bpy.data.materials.new(PREFIX + name)
    node_tree_of(m)
    if additive:
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "BLENDED"
        elif hasattr(m, "blend_method"):
            m.blend_method = "BLEND"
    try:
        m.use_backface_culling = False
    except AttributeError:
        pass
    return m


def color_out(node):
    for sock in node.outputs:
        if sock.identifier == "Result_Color":
            return sock
    return node.outputs[0]


def finish_additive(nb, emission_color, strength):
    """Transparent + Emission = pure additive light, no sorting problems."""
    em = nb.node("ShaderNodeEmission", {"Color": emission_color, "Strength": strength})
    tr = nb.node("ShaderNodeBsdfTransparent")
    add = nb.node("ShaderNodeAddShader", {0: tr.outputs[0], 1: em.outputs[0]})
    nb.node("ShaderNodeOutputMaterial", {"Surface": add.outputs[0]})


def set_cycles_volume_step(mat, rate):
    try:
        mat.cycles.volume_step_rate = rate
    except AttributeError:
        pass
    try:
        mat.cycles.volume_interpolation = "LINEAR"
        mat.cycles.volume_sampling = "DISTANCE"
    except (AttributeError, TypeError):
        pass


# ---- the star sizer: keeps every star at least ~1 pixel, conserving its light ---

def star_sizer_group():
    g = bpy.data.node_groups.new(PREFIX + "StarSizer", "GeometryNodeTree")
    iface = g.interface
    iface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    iface.new_socket("Camera", in_out="INPUT", socket_type="NodeSocketObject")
    s = iface.new_socket("Pixel Angle", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 0.0004
    s = iface.new_socket("Min Pixels", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 0.9
    s = iface.new_socket("Max Pixels", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 5.0
    iface.new_socket("Material", in_out="INPUT", socket_type="NodeSocketMaterial")
    iface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nb = NodeBuilder(g)
    gi = nb.node("NodeGroupInput")
    cam = nb.node("GeometryNodeObjectInfo", {"Object": gi.outputs["Camera"]}, transform_space="RELATIVE")
    pos = nb.node("GeometryNodeInputPosition")
    dist = nb.vmath("DISTANCE", pos.outputs[0], cam.outputs["Location"])
    rad_attr = nb.node("GeometryNodeInputNamedAttribute", {"Name": "rad"}, data_type="FLOAT")
    radius = nb.ex("max(d*pa*mn, min(r, d*pa*mx))", d=dist, pa=gi.outputs["Pixel Angle"],
                   mn=gi.outputs["Min Pixels"], mx=gi.outputs["Max Pixels"], r=rad_attr.outputs["Attribute"])
    # Brightness: falls off as 1/d^1.15 (gentler than nature's 1/d^2, so both the
    # far galaxy and a star you fly past look right), times (ref/pixel angle)^2 so
    # a star carries the same light at any render resolution.
    flux = nb.ex("min(pow(PR/pa, 2.0) * pow(D0/max(d, 0.02), G), FMAX)", PR=PIXEL_ANGLE_REF, pa=gi.outputs["Pixel Angle"],
                 D0=10.0, d=dist, G=1.15, FMAX=60.0)
    store = nb.node("GeometryNodeStoreNamedAttribute", {"Geometry": gi.outputs["Geometry"], "Name": "flux", "Value": flux},
                    data_type="FLOAT", domain="POINT")
    pts = nb.node("GeometryNodeMeshToPoints", {"Mesh": store.outputs[0], "Radius": radius})
    setm = nb.node("GeometryNodeSetMaterial", {"Geometry": pts.outputs[0], "Material": gi.outputs["Material"]})
    nb.node("NodeGroupOutput", {0: setm.outputs[0]})
    return g


def add_star_sizer(ob, group, camera, material, min_px=0.9, max_px=5.0):
    mod = ob.modifiers.new(PREFIX + "StarSizer", "NODES")
    mod.node_group = group
    ids = {item.name: item.identifier for item in group.interface.items_tree
           if getattr(item, "in_out", None) == "INPUT"}
    mod[ids["Camera"]] = camera
    mod[ids["Material"]] = material
    mod[ids["Min Pixels"]] = float(min_px)
    mod[ids["Max Pixels"]] = float(max_px)
    scene = camera.users_scene[0] if camera.users_scene else bpy.context.scene
    drive(ob, f'modifiers["{mod.name}"]["{ids["Pixel Angle"]}"]', "sw/(lens*rx*pct*0.01)",
          {"sw": (camera.data, "sensor_width"), "lens": (camera.data, "lens"),
           "rx": (scene, "render.resolution_x"), "pct": (scene, "render.resolution_percentage")})
    return mod


# ============================================================================
#  9. THE STARS  (1.2 million of them, generated with numpy)
# ============================================================================

YOUNG = [(0.25, 10000, 32000), (0.35, 7500, 10000), (0.25, 6000, 7500), (0.15, 4500, 6000)]
OLD = [(0.10, 6000, 7500), (0.35, 5200, 6000), (0.40, 3900, 5200), (0.15, 3000, 3900)]
BULGE = [(0.20, 5000, 6000), (0.55, 3800, 5000), (0.25, 3000, 3800)]
HALO = [(0.40, 4500, 5500), (0.60, 3200, 4500)]
GLOBULAR = [(0.67, 4800, 6200), (0.30, 3500, 4800), (0.03, 7000, 9000)]
NEWBORN = [(0.6, 15000, 36000), (0.4, 8000, 15000)]


def sample_temps(rng, n, table):
    w = np.array([t[0] for t in table], float)
    idx = rng.choice(len(table), size=n, p=w / w.sum())
    lo = np.array([t[1] for t in table], float)[idx]
    hi = np.array([t[2] for t in table], float)[idx]
    return np.exp(rng.uniform(np.log(lo), np.log(hi)))


def sample_radius(rng, n, scale, rmin, rmax):
    grid = np.linspace(rmin, rmax, 4096)
    pdf = grid * np.exp(-grid / scale)
    cdf = np.cumsum(pdf)
    cdf /= cdf[-1]
    return np.interp(rng.random(n), cdf, grid)


def plummer(rng, n, a):
    u = rng.uniform(0.02, 0.98, n)
    r = a / np.sqrt(u ** (-2.0 / 3.0) - 1.0)
    r = np.minimum(r, 6 * a)
    d = rng.normal(size=(n, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    return d * r[:, None]


def generate_stars(rng, total, kp):
    parts = []

    def add(pos, temps, lum_mu, lum_sigma, pop, pulse, reveal=None, giants=0.0):
        n = len(pos)
        temps = np.asarray(temps, float)
        lum = np.exp(rng.normal(lum_mu, lum_sigma, n)) * (temps / 6000.0) ** 1.1
        if giants > 0:
            g = rng.random(n) < giants
            temps[g] = rng.uniform(3300, 4800, g.sum())
            lum[g] *= 5.0
        lum = np.clip(lum, 0.02, 25.0)
        if reveal is None:
            reveal = rng.uniform(0.12, 1.08, n)
        parts.append(dict(pos=np.asarray(pos, float), T=temps, lum=lum, pop=np.full(n, pop, float),
                          pulse=np.full(n, pulse, float), reveal=np.asarray(reveal, float)))

    N = lambda f: max(10, int(total * f))  # noqa: E731

    # 1. old disk stars, gently following the arms
    want = N(0.36)
    got, chunks = 0, []
    while got < want:
        k = int((want - got) * 2.2) + 2000
        r = sample_radius(rng, k, 30.0, 2.0, 150.0)
        th = rng.uniform(-math.pi, math.pi, k)
        keep = rng.random(k) < 0.3 + 0.7 * armness(r, th, 4.0) * arm_mask(r)
        r, th = r[keep], th[keep]
        z = rng.normal(0.0, 0.8 + 0.012 * r)
        chunks.append(np.stack([r * np.cos(th), r * np.sin(th), z], 1))
        got += len(r)
    pos = np.concatenate(chunks)[:want]
    add(pos, sample_temps(rng, want, OLD), -0.3, 0.6, 0, 0.45, giants=0.05)

    # 2. young stars riding the arm crests (2 main arms + 2 fainter ones)
    n = N(0.31)
    r = sample_radius(rng, n, 42.0, R0, 128.0)
    main = (rng.random(n) < 0.88) | (r < 50.0)
    arm = rng.integers(0, 2, n).astype(float)
    th = np.where(main, crest_theta(r, arm), crest_theta(r, arm, math.pi))
    width = (2.6 + 0.07 * r) * np.where(main, 1.0, 1.4)
    th = th + rng.normal(0.0, 1.0, n) * width / r
    r = r + rng.normal(0.0, 1.0, n)
    z = rng.normal(0.0, 0.3 + 0.004 * r)
    add(np.stack([r * np.cos(th), r * np.sin(th), z], 1), sample_temps(rng, n, YOUNG), 0.05, 0.9, 1, 1.0)

    # 3. open clusters strung along the arms
    n = N(0.06)
    n_cl = max(40, n // 90)
    rc = sample_radius(rng, n_cl, 45.0, R0 + 4, 120.0)
    ac = rng.integers(0, 2, n_cl)
    thc = crest_theta(rc, ac) + rng.normal(0, 0.05, n_cl)
    centers = np.stack([rc * np.cos(thc), rc * np.sin(thc), rng.normal(0, 0.25, n_cl)], 1)
    sizes = rng.uniform(0.25, 0.9, n_cl)
    which = rng.integers(0, n_cl, n)
    pos = centers[which] + rng.normal(size=(n, 3)) * sizes[which, None]
    add(pos, sample_temps(rng, n, YOUNG), 0.2, 0.8, 2, 1.0)

    # 4. bulge: old gold and orange stars, thinned right at the black hole
    n = N(0.13)
    sig = np.where(rng.random(n) < 0.6, 4.5, 9.0)
    pos = rng.normal(size=(n, 3)) * sig[:, None]
    pos[:, 2] *= 0.65
    rr = np.linalg.norm(pos, axis=1)
    keep = (rr > 0.9) & ((rr > 3.0) | (rng.random(n) < 0.3))
    pos = pos[keep]
    add(pos, sample_temps(rng, len(pos), BULGE), -0.1, 0.6, 3, 0.55, giants=0.08)

    # 5. the bar
    n = N(0.05)
    pos = np.stack([np.clip(rng.normal(0, 11.0, n), -24, 24), rng.normal(0, 2.6, n), rng.normal(0, 1.6, n)], 1)
    add(pos, sample_temps(rng, n, BULGE), -0.15, 0.6, 3, 0.55, giants=0.06)

    # 6. the halo
    n = N(0.025)
    r = np.minimum(12.0 * (rng.uniform(0.02, 1.0, n) ** (-1.0 / 1.6) - 1.0) + 5.0, 230.0)
    d = rng.normal(size=(n, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    pos = d * r[:, None]
    pos[:, 2] *= 0.8
    add(pos, sample_temps(rng, n, HALO), -0.8, 0.5, 4, 0.3)

    # 7. globular clusters
    n = N(0.03)
    n_gc = 130
    rg = rng.uniform(15.0, 135.0, n_gc)
    d = rng.normal(size=(n_gc, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    gcs = d * rg[:, None]
    per = np.maximum(1, (n // n_gc))
    pos = np.concatenate([gcs[i] + plummer(rng, per, rng.uniform(0.35, 0.8)) for i in range(n_gc)])
    add(pos, sample_temps(rng, len(pos), GLOBULAR), -0.4, 0.55, 5, 0.4)

    # 8. two satellite dwarf galaxies
    n = N(0.025)
    sats = [(np.array([168.0, -96.0, -42.0]), 0.65, 7.0), (np.array([206.0, 44.0, -70.0]), 0.35, 4.5)]
    for center, frac, size in sats:
        m = int(n * frac)
        blobs = center + rng.normal(size=(5, 3)) * size * 0.6
        which = rng.integers(0, 5, m)
        pos = blobs[which] + rng.normal(size=(m, 3)) * size * rng.uniform(0.3, 0.8, 5)[which, None]
        temps = np.where(rng.random(m) < 0.5, sample_temps(rng, m, YOUNG), sample_temps(rng, m, OLD))
        add(pos, temps, -0.1, 0.7, 6, 0.6)

    # 9. the newborn cluster inside the Destiny Nebula (first stars to appear)
    m = 2500
    pos = kp.cluster + plummer(rng, m, 0.7)
    add(pos, sample_temps(rng, m, NEWBORN), -0.9, 0.8, 7, 1.0, reveal=rng.uniform(0.04, 0.75, m))

    allp = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    # keep the Destiny Star's neighbourhood clear so the opening shot is clean
    dd = np.linalg.norm(allp["pos"] - kp.destiny[None, :], axis=1)
    keep = dd > 1.2
    allp = {k: v[keep] for k, v in allp.items()}
    n = len(allp["pos"])
    allp["color"] = blackbody(allp["T"])
    allp["rad"] = 0.0005 * allp["lum"] ** 0.3
    allp["phase"] = rng.random(n)
    return allp


# ============================================================================
#  10. MATERIALS
# ============================================================================

K_STARS = 8.0        # overall star brightness
PIXEL_ANGLE_REF = 36.0 / (35.0 * 1920.0)   # 35 mm lens at 1920 px wide


def mat_stars(director, n_stars):
    k_stars = K_STARS
    m = new_material("StarLight", additive=True)
    nb = NodeBuilder(m.node_tree)
    a = lambda name: nb.node("ShaderNodeAttribute", attribute_name=name, attribute_type="GEOMETRY")  # noqa: E731
    col = a("star_color").outputs["Color"]
    lum, flux, phase = a("lum").outputs["Fac"], a("flux").outputs["Fac"], a("phase").outputs["Fac"]
    reveal, pulse = a("reveal").outputs["Fac"], a("pulse").outputs["Fac"]
    t = channel_value(nb, director, "t", "time", t="time")
    ign = channel_value(nb, director, "i", "ignite", i="ignite")
    fade = channel_value(nb, director, "f*g", "fade x gain", f="fadeout", g="star_gain")
    bass = channel_value(nb, director, "b", "bass", b="bass")
    kick = channel_value(nb, director, "k", "kick", k="kick")
    spk = channel_value(nb, director, "s", "sparkle", s="sparkle")
    strength = nb.ex(
        "K * lum * flux * fade"
        " * (1 + (0.1 + 0.35*spk) * sin(t*(1.3 + 4.0*ph) + ph*60.0))"
        " * clamp((ign - rev) * 5.0)"
        " * (1 + 1.1*bass*pul + 0.7*kick*pul)",
        K=k_stars, lum=lum, flux=flux, fade=fade, spk=spk, t=t, ph=phase, ign=ign, rev=reveal,
        bass=bass, pul=pulse, kick=kick)
    # additive: a star adds light and never blocks the glowing gas behind it
    finish_additive(nb, col, strength)
    return m


def mat_special_star(color=(1.0, 0.86, 0.62), k=380.0):
    """Destiny Star / beacon / pulsar: brightness = object colour alpha."""
    m = new_material("SpecialStar", additive=True)
    nb = NodeBuilder(m.node_tree)
    oi = nb.node("ShaderNodeObjectInfo")
    finish_additive(nb, color + (1.0,), nb.ex("a * K", a=oi.outputs["Alpha"], K=k))
    return m


def spiral_phase_nodes(nb, x, y):
    r = nb.ex("sqrt(x*x + y*y) + 0.001", x=x, y=y)
    th = nb.math("ARCTAN2", y, x)
    w = nb.ex("0.45*sin(r/13.0 + 0.7) + 0.25*sin(r/5.1 + 3.0*th + 1.9)", r=r, th=th)
    phi = nb.ex("2.0*th - K*ln(max(r, 0.5)/R0) + w", th=th, K=KSP, r=r, R0=R0, w=w)
    return r, th, phi


def mat_galaxy_gas(director):
    """The diffuse light of billions of unresolved stars, plus dark dust lanes."""
    m = new_material("GalaxyGas")
    set_cycles_volume_step(m, 0.02)
    nb = NodeBuilder(m.node_tree)
    p = nb.node("ShaderNodeTexCoord").outputs["Object"]
    x, y, z = nb.separate(p)
    r, th, phi = spiral_phase_nodes(nb, x, y)
    warp = nb.noise(nb.vmath("SCALE", p, scale=0.018), 1.0, 1.0, 0.5).outputs["Fac"]
    phi_g = nb.ex("phi + (w - 0.5)*1.1", phi=phi, w=warp)
    arms = nb.ex("max(pow(0.5 + 0.5*cos(phi), 4.0), 0.25*pow(0.5 - 0.5*cos(phi), 6.0)*smoothstep(40.0, 65.0, r))",
                 phi=phi_g, r=r)
    amask = nb.ex("smoothstep(14.0, 26.0, r) * (1.0 - smoothstep(112.0, 140.0, r))", r=r)
    clump = nb.noise(nb.vmath("SCALE", p, scale=0.11), 1.0, 4.0, 0.62).outputs["Fac"]
    disk = nb.ex("exp(-r/34.0) * exp(-pow(z/(1.2 + 0.012*r), 2.0)) * (1.0 - smoothstep(95.0, 136.0, r))", r=r, z=z)
    e_disk = nb.ex("d * (0.1 + 1.6*a*m*(0.3 + 1.1*smoothstep(0.4, 0.72, c)))", d=disk, a=arms, m=amask, c=clump)
    e_bar = nb.ex("exp(-pow(x/17.0, 2.0) - pow(y/4.5, 2.0) - pow(z/2.2, 2.0)) * 0.8", x=x, y=y, z=z)
    # dust lanes hug the inner edge of each arm and are torn into filaments
    dust_n = nb.noise(nb.vmath("SCALE", p, scale=0.2), 1.0, 5.0, 0.68).outputs["Fac"]
    dust = nb.ex("3.2 * exp(-pow(z/0.8, 2.0)) * exp(-r/50.0) * (0.1 + 1.4*pow(0.5 + 0.5*cos(phi - 0.6), 6.0))"
                 " * smoothstep(0.45, 0.7, n) * smoothstep(5.0, 15.0, r)", z=z, r=r, phi=phi_g, n=dust_n)
    arm_col = color_out(nb.node("ShaderNodeMix", {"Factor_Float": arms, "A_Color": (1.0, 0.84, 0.66, 1.0),
                                                  "B_Color": (0.52, 0.68, 1.0, 1.0)}, data_type="RGBA"))
    col = nb.add(nb.rgb((1.0, 0.7, 0.4), e_bar), nb.rgb(arm_col, e_disk))
    gain = channel_value(nb, director, "u*g*(1+0.35*b)", "gas gain", u="universe", g="galaxy_gain", b="bass")
    em = nb.node("ShaderNodeEmission", {"Color": col, "Strength": nb.math("MULTIPLY", gain, 1.1)})
    ab = nb.node("ShaderNodeVolumeAbsorption", {"Color": (0.62, 0.42, 0.3, 1.0), "Density": nb.math("MULTIPLY", dust, gain)})
    add = nb.node("ShaderNodeAddShader", {0: em.outputs[0], 1: ab.outputs[0]})
    nb.node("ShaderNodeOutputMaterial", {"Volume": add.outputs[0]})
    return m


def mat_puffs(director):
    """Soft glowing spheres: pink H-II star-forming regions and blue arm haze."""
    m = new_material("NebulaPuffs", additive=True)
    nb = NodeBuilder(m.node_tree)
    col = nb.node("ShaderNodeAttribute", attribute_name="puff_color", attribute_type="GEOMETRY").outputs["Color"]
    glow = nb.node("ShaderNodeAttribute", attribute_name="glow", attribute_type="GEOMETRY").outputs["Fac"]
    lw = nb.node("ShaderNodeLayerWeight", {"Blend": 0.5})
    gain = channel_value(nb, director, "u*g*(1+0.5*b)", "puff gain", u="universe", g="galaxy_gain", b="bass")
    finish_additive(nb, col, nb.ex("pow(1.0 - f, 2.5) * g * k", f=lw.outputs["Facing"], g=glow, k=gain))
    return m


def puff_sizer_group():
    g = bpy.data.node_groups.new(PREFIX + "PuffSizer", "GeometryNodeTree")
    g.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    g.interface.new_socket("Material", in_out="INPUT", socket_type="NodeSocketMaterial")
    g.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nb = NodeBuilder(g)
    gi = nb.node("NodeGroupInput")
    rad = nb.node("GeometryNodeInputNamedAttribute", {"Name": "rad"}, data_type="FLOAT")
    pts = nb.node("GeometryNodeMeshToPoints", {"Mesh": gi.outputs["Geometry"], "Radius": rad.outputs["Attribute"]})
    setm = nb.node("GeometryNodeSetMaterial", {"Geometry": pts.outputs[0], "Material": gi.outputs["Material"]})
    nb.node("NodeGroupOutput", {0: setm.outputs[0]})
    return g


def generate_puffs(rng, count):
    """H-II knots (pink, with hot blue-white hearts) just downstream of the arm crests,
    and faint blue haze puffs that make the arms glow."""
    pos, col, rad, glow = [], [], [], []
    n_knots = count
    r = sample_radius(rng, n_knots, 45.0, 24.0, 122.0)
    arm = rng.integers(0, 2, n_knots)
    th = crest_theta(r, arm) + 0.07 + rng.normal(0, 0.05, n_knots)
    c = np.stack([r * np.cos(th), r * np.sin(th), rng.normal(0, 0.35, n_knots)], 1)
    size = np.exp(rng.uniform(np.log(0.6), np.log(2.8), n_knots))
    pink = np.array([1.0, 0.28, 0.5])
    for k in range(4):
        off = rng.normal(size=(n_knots, 3)) * size[:, None] * (0.0 if k == 0 else 0.7)
        off[:, 2] *= 0.5
        pos.append(c + off)
        rad.append(size * (1.0 if k == 0 else rng.uniform(0.35, 0.7, n_knots)))
        tint = pink + rng.normal(0, 0.06, (n_knots, 3))
        col.append(np.clip(tint, 0, 1))
        glow.append(np.full(n_knots, 0.9 if k == 0 else 0.7) / np.maximum(size, 0.8))
    pos.append(c + rng.normal(size=(n_knots, 3)) * size[:, None] * 0.15)
    rad.append(size * 0.25)
    col.append(np.tile([0.75, 0.85, 1.0], (n_knots, 1)))
    glow.append(np.full(n_knots, 3.0) / np.maximum(size, 0.8))
    n_haze = count
    r = sample_radius(rng, n_haze, 40.0, 22.0, 125.0)
    arm = rng.integers(0, 2, n_haze)
    th = crest_theta(r, arm) + rng.normal(0, 1.0, n_haze) * (3.0 + 0.06 * r) / r
    pos.append(np.stack([r * np.cos(th), r * np.sin(th), rng.normal(0, 0.6, n_haze)], 1))
    hs = rng.uniform(3.0, 7.0, n_haze)
    rad.append(hs)
    col.append(np.tile([0.45, 0.62, 1.0], (n_haze, 1)))
    glow.append(np.full(n_haze, 0.05))
    return np.concatenate(pos), np.concatenate(col), np.concatenate(rad), np.concatenate(glow)


def mat_bulge(director):
    m = new_material("BulgeGlow")
    set_cycles_volume_step(m, 0.05)
    nb = NodeBuilder(m.node_tree)
    p = nb.node("ShaderNodeTexCoord").outputs["Object"]
    x, y, z = nb.separate(p)
    R = nb.ex("sqrt(x*x + y*y + pow(z/0.65, 2.0)) + 0.001", x=x, y=y, z=z)
    n = nb.noise(nb.vmath("SCALE", p, scale=0.35), 1.0, 2.0, 0.55).outputs["Fac"]
    e = nb.ex("(1.2*exp(-R/3.0) + 0.25*exp(-pow(R/10.0, 2.0))) * (0.1 + 0.9*smoothstep(1.2, 5.5, R)) * (0.8 + 0.4*n)",
              R=R, n=n)
    gain = channel_value(nb, director, "u*g*(1+0.3*b)", "bulge gain", u="universe", g="galaxy_gain", b="bass")
    em = nb.node("ShaderNodeEmission", {"Color": (1.0, 0.74, 0.46, 1.0), "Strength": nb.math("MULTIPLY", e, gain)})
    nb.node("ShaderNodeOutputMaterial", {"Volume": em.outputs[0]})
    return m


def mat_nebula(director, cluster_offset):
    """The Destiny Nebula: a bubble blown by the newborn cluster. Teal oxygen glow
    inside, red hydrogen walls, gold sulphur edges and dark dust pillars."""
    m = new_material("DestinyNebula")
    set_cycles_volume_step(m, 0.07)
    nb = NodeBuilder(m.node_tree)
    p = nb.node("ShaderNodeTexCoord").outputs["Object"]
    wv = nb.noise(nb.vmath("SCALE", p, scale=0.3), 1.0, 2.0, 0.5).outputs["Color"]
    pw = nb.vmath("ADD", p, nb.vmath("SCALE", nb.vmath("SUBTRACT", wv, (0.5, 0.5, 0.5)), scale=3.2))
    rn = nb.ex("l / S", l=nb.vmath("LENGTH", p), S=NEBULA_SIZE)
    edge_n = nb.noise(nb.vmath("SCALE", p, scale=0.25), 1.0, 2.0, 0.5).outputs["Fac"]
    shell = nb.ex("smoothstep(1.1, 0.5, r + 0.45*(e - 0.5))", r=rn, e=edge_n)
    dcl = nb.vmath("DISTANCE", p, tuple(cluster_offset))
    n1 = nb.noise(nb.vmath("SCALE", pw, scale=0.5), 1.0, 6.0, 0.6).outputs["Fac"]
    cavity = nb.ex("smoothstep(1.0, 2.8, d)", d=dcl)
    rim = nb.ex("exp(-pow((d - 3.4)/1.3, 2.0))", d=dcl)
    dens = nb.ex("(pow(smoothstep(0.52, 0.76, n), 2.0)*1.4 + rim*pow(smoothstep(0.44, 0.66, n), 2.0)*1.3) * s * c",
                 n=n1, s=shell, c=cavity, rim=rim)
    rid = nb.noise(nb.vmath("SCALE", pw, scale=0.9), 1.0, 4.0, 0.6).outputs["Fac"]
    ridge = nb.ex("pow(1.0 - abs(2.0*r - 1.0), 5.0) * s * smoothstep(2.2, 3.5, d)", r=rid, s=shell, d=dcl)
    mixn = nb.noise(nb.vmath("SCALE", p, scale=0.14), 1.0, 2.0, 0.5).outputs["Fac"]
    goldn = nb.noise(nb.vmath("SCALE", pw, scale=0.7), 1.0, 2.0, 0.5).outputs["Fac"]
    ion = nb.ex("exp(-d/2.5)", d=dcl)
    t_col = nb.ex("smoothstep(1.8, 4.2, d + 2.0*(m - 0.5))", d=dcl, m=mixn)
    teal_red = color_out(nb.node("ShaderNodeMix", {"Factor_Float": t_col, "A_Color": (0.08, 0.85, 0.85, 1.0),
                                                   "B_Color": (1.0, 0.22, 0.34, 1.0)}, data_type="RGBA"))
    col = nb.add(nb.rgb(teal_red, nb.ex("d * (0.9 + 2.5*i)", d=dens, i=ion)),
                 nb.rgb((1.0, 0.6, 0.15), nb.ex("d * smoothstep(0.55, 0.72, g) * smoothstep(0.45, 0.85, r) * 1.2",
                                                d=dens, g=goldn, r=rn)),
                 nb.rgb((0.55, 0.8, 1.0), nb.ex("i*i*0.06*s", i=ion, s=shell)))
    gain = channel_value(nb, director, "u*g*(1+0.4*b)", "nebula gain", u="universe", g="nebula_gain", b="bass")
    em = nb.node("ShaderNodeEmission", {"Color": col, "Strength": nb.math("MULTIPLY", gain, 1.8)})
    ab = nb.node("ShaderNodeVolumeAbsorption", {"Color": (0.45, 0.28, 0.22, 1.0),
                                                "Density": nb.ex("(0.25*d + 2.0*r) * g", d=dens, r=ridge, g=gain)})
    add = nb.node("ShaderNodeAddShader", {0: em.outputs[0], 1: ab.outputs[0]})
    nb.node("ShaderNodeOutputMaterial", {"Volume": add.outputs[0]})
    return m


def mat_world(director, scene):
    w = bpy.data.worlds.new(PREFIX + "DeepSpace")
    scene.world = w
    nb = NodeBuilder(node_tree_of(w))
    d = nb.vmath("NORMALIZE", nb.node("ShaderNodeTexCoord").outputs["Generated"])
    layers = []
    for scale, size, power, k in ((140.0, 0.06, 7.0, 6.0), (420.0, 0.05, 9.0, 2.5)):
        v = nb.voronoi(d, scale, 1.0)
        rc, gc, _ = nb.separate(v.outputs["Color"])
        bright = nb.ex("smoothstep(S, 0.0, dist) * pow(r, P) * K", S=size, dist=v.outputs["Distance"], r=rc, P=power, K=k)
        bb = nb.node("ShaderNodeBlackbody", {"Temperature": nb.ex("3500.0 + g*9000.0", g=gc)})
        layers.append(nb.rgb(bb.outputs[0], bright))
    haze_n = nb.noise(nb.vmath("SCALE", d, scale=1.8), 1.0, 6.0, 0.6)
    haze = nb.rgb(color_out(nb.node("ShaderNodeMix", {"Factor_Float": nb.separate(haze_n.outputs["Color"])[0],
                                            "A_Color": (0.05, 0.08, 0.25, 1.0), "B_Color": (0.25, 0.05, 0.3, 1.0)},
                          data_type="RGBA")),
                  nb.ex("pow(n, 4.0) * 0.012", n=haze_n.outputs["Fac"]))
    col = nb.add(layers[0], layers[1], haze)
    gain = channel_value(nb, director, "u", "universe", u="universe")
    bg = nb.node("ShaderNodeBackground", {"Color": col, "Strength": gain})
    nb.node("ShaderNodeOutputWorld", {"Surface": bg.outputs[0]})
    return w


def mat_galaxy_sprite(director, name="GalaxySprite", channel="deepfield", k=2.2):
    """Background galaxies: spiral or elliptical, drawn from UVs, varied per quad."""
    m = new_material(name, additive=True)
    nb = NodeBuilder(m.node_tree)
    uv = nb.node("ShaderNodeTexCoord").outputs["UV"]
    u, v, _ = nb.separate(uv)
    x = nb.ex("u*2.0 - 1.0", u=u)
    y = nb.ex("v*2.0 - 1.0", v=v)
    rnd = nb.node("ShaderNodeAttribute", attribute_name="gal_rand", attribute_type="GEOMETRY").outputs["Fac"]
    typ = nb.node("ShaderNodeAttribute", attribute_name="gal_type", attribute_type="GEOMETRY").outputs["Fac"]
    rho = nb.ex("sqrt(x*x + y*y) + 0.0001", x=x, y=y)
    ang = nb.math("ARCTAN2", y, x)
    arms = nb.ex("pow(0.5 + 0.5*cos(2.0*a - ln(r + 0.02)*(3.0 + 3.0*q) + q*40.0), 3.0)", a=ang, r=rho, q=rnd)
    spiral = nb.ex("exp(-r/0.06)*1.6 + exp(-r/0.22)*(0.2 + 0.9*A)", r=rho, A=arms)
    ellip = nb.ex("exp(-pow(sqrt(x*x*(1.0 + q) + y*y*(2.2 - q))/0.28, 0.7)*2.6)*1.7", x=x, y=y, q=rnd)
    irr_n = nb.noise(nb.combine(x, y, rnd), 2.5, 3.0, 0.6).outputs["Fac"]
    irreg = nb.ex("exp(-r/0.35) * smoothstep(0.45, 0.7, n) * 1.4", r=rho, n=irr_n)
    shape = nb.ex("(spiral*gt(1.5, t)*gt(t, 0.5) + ellip*lt(t, 0.5) + irreg*gt(t, 1.5)) * (1.0 - smoothstep(0.75, 1.0, r))",
                  spiral=spiral, ellip=ellip, irreg=irreg, t=typ, r=rho)
    core = color_out(nb.node("ShaderNodeMix", {"Factor_Float": nb.ex("smoothstep(0.03, 0.4, r)", r=rho),
                                     "A_Color": (1.0, 0.78, 0.5, 1.0), "B_Color": (0.55, 0.7, 1.0, 1.0)},
                   data_type="RGBA"))
    tint = color_out(nb.node("ShaderNodeMix", {"Factor_Float": nb.ex("lt(q, 0.35)*0.6", q=rnd), "A_Color": core,
                                     "B_Color": (1.0, 0.6, 0.7, 1.0)}, data_type="RGBA"))
    gain = channel_value(nb, director, "u*c", f"{channel} gain", u="universe", c=channel)
    finish_additive(nb, tint, nb.ex("s * g * K", s=shape, g=gain, K=k))
    return m


def mat_ring(director, name="EchoRing", color=(0.7, 0.85, 1.0), k=6.0):
    """Echo rings / photon ring: a glowing ring on a quad, alpha from the object colour."""
    m = new_material(name, additive=True)
    nb = NodeBuilder(m.node_tree)
    p = nb.node("ShaderNodeTexCoord").outputs["Object"]
    x, y, _ = nb.separate(p)
    rho = nb.ex("sqrt(x*x + y*y)", x=x, y=y)
    ring = nb.ex("(exp(-pow((r - 0.9)/0.035, 2.0)) + 0.3*exp(-pow((r - 0.8)/0.12, 2.0))) * (1.0 - smoothstep(0.96, 1.0, r))", r=rho)
    oi = nb.node("ShaderNodeObjectInfo")
    finish_additive(nb, color + (1.0,), nb.ex("ring * a * K", ring=ring, a=oi.outputs["Alpha"], K=k))
    return m


def mat_accretion(director):
    m = new_material("AccretionDisk", additive=True)
    nb = NodeBuilder(m.node_tree)
    p = nb.node("ShaderNodeTexCoord").outputs["Object"]
    x, y, _ = nb.separate(p)
    rho = nb.ex("sqrt(x*x + y*y) + 0.001", x=x, y=y)
    ang = nb.math("ARCTAN2", y, x)
    t = channel_value(nb, director, "t", "time", t="time")
    swirl = nb.ex("a + t*1.6*pow(r, -1.5)", a=ang, t=t, r=rho)
    streak_v = nb.combine(nb.math("MULTIPLY", rho, 9.0), nb.math("COSINE", swirl), nb.math("SINE", swirl))
    streak = nb.noise(streak_v, 1.6, 6.0, 0.62).outputs["Fac"]
    prof = nb.ex("smoothstep(0.85, 1.05, r) * exp(-(r - 1.0)/1.1) * (1.0 - smoothstep(3.8, 4.5, r))", r=rho)
    temp = nb.ex("2600.0 + 11000.0*pow(clamp(1.3/r), 1.6)", r=rho)
    bb = nb.node("ShaderNodeBlackbody", {"Temperature": temp}).outputs[0]
    geo = nb.node("ShaderNodeNewGeometry")
    wp = geo.outputs["Position"]
    wx, wy, _ = nb.separate(wp)
    wl = nb.ex("sqrt(wx*wx + wy*wy) + 0.0001", wx=wx, wy=wy)
    tang = nb.combine(nb.ex("-wy/l", wy=wy, l=wl), nb.ex("wx/l", wx=wx, l=wl), 0.0)
    dop = nb.ex("pow(1.0 + 0.5*d, 3.0)", d=nb.vmath("DOT_PRODUCT", tang, geo.outputs["Incoming"]))
    gain = channel_value(nb, director, "u*h*(1+0.5*b)", "black hole", u="universe", h="bh", b="bass")
    finish_additive(nb, bb, nb.ex("prof * (0.12 + 1.9*smoothstep(0.35, 0.75, s)) * dop * g * 40.0",
                                  prof=prof, s=streak, dop=dop, g=gain))
    return m


def mat_lensed_halo(director):
    """Camera-facing ring: the far side of the disk bent over the top by gravity."""
    m = new_material("LensedHalo", additive=True)
    nb = NodeBuilder(m.node_tree)
    p = nb.node("ShaderNodeTexCoord").outputs["Object"]
    x, y, _ = nb.separate(p)
    rho = nb.ex("sqrt(x*x + y*y) + 0.0001", x=x, y=y)
    ang = nb.math("ARCTAN2", y, x)
    t = channel_value(nb, director, "t", "time", t="time")
    sv = nb.combine(nb.math("MULTIPLY", rho, 8.0), nb.math("COSINE", nb.ex("a + t*0.9", a=ang, t=t)),
                    nb.math("SINE", nb.ex("a + t*0.9", a=ang, t=t)))
    streak = nb.noise(sv, 1.5, 5.0, 0.6).outputs["Fac"]
    photon = nb.ex("exp(-pow((r - 0.78)/0.022, 2.0)) * 3.0", r=rho)
    halo = nb.ex("smoothstep(0.82, 0.95, r) * exp(-(r - 0.9)/0.55) * (0.3 + s) * 0.9 * (1.0 + 0.45*x/r)",
                 r=rho, s=streak, x=x)
    bb = nb.node("ShaderNodeBlackbody", {"Temperature": nb.ex("4200.0 + 5000.0*exp(-(r - 0.78)/0.4)", r=rho)}).outputs[0]
    gain = channel_value(nb, director, "u*h*(1+0.5*b)", "black hole", u="universe", h="bh", b="bass")
    finish_additive(nb, bb, nb.ex("(photon + halo) * g * 9.0", photon=photon, halo=halo, g=gain))
    return m


def mat_black():
    m = new_material("EventHorizon")
    nb = NodeBuilder(m.node_tree)
    em = nb.node("ShaderNodeEmission", {"Color": (0.0, 0.0, 0.0, 1.0), "Strength": 0.0})
    nb.node("ShaderNodeOutputMaterial", {"Surface": em.outputs[0]})
    return m


def mat_jet(director):
    m = new_material("RelativisticJet", additive=True)
    nb = NodeBuilder(m.node_tree)
    p = nb.node("ShaderNodeTexCoord").outputs["Object"]
    x, y, z = nb.separate(p)
    s = nb.ex("abs(z)/160.0", z=z)
    t = channel_value(nb, director, "t", "time", t="time")
    ang = nb.math("ARCTAN2", y, x)
    flow = nb.noise(nb.combine(nb.math("COSINE", ang), nb.math("SINE", ang), nb.ex("abs(z)*0.07 - t*1.8", z=z, t=t)),
                    2.0, 4.0, 0.6).outputs["Fac"]
    lw = nb.node("ShaderNodeLayerWeight", {"Blend": 0.5})
    core = nb.ex("pow(1.0 - f, 2.5)", f=lw.outputs["Facing"])
    gain = channel_value(nb, director, "u*j*(1+0.6*b)", "jets", u="universe", j="jets", b="bass")
    strength = nb.ex("exp(-s*3.5) * (0.15 + 1.4*smoothstep(0.45, 0.72, f)) * c * g * 3.0 * smoothstep(0.0, 0.01, s)",
                     s=s, f=flow, c=core, g=gain)
    finish_additive(nb, (0.55, 0.75, 1.0, 1.0), strength)
    return m


def mat_shockwave():
    m = new_material("Shockwave", additive=True)
    nb = NodeBuilder(m.node_tree)
    p = nb.node("ShaderNodeTexCoord").outputs["Object"]
    x, y, _ = nb.separate(p)
    rho = nb.ex("sqrt(x*x + y*y)", x=x, y=y)
    n = nb.noise(nb.vmath("SCALE", p, scale=6.0), 1.0, 4.0, 0.6).outputs["Fac"]
    ring = nb.ex("(exp(-pow((r - 0.965)/0.018, 2.0))*(0.6 + 0.8*n) + 0.18*exp(-pow((r - 0.85)/0.1, 2.0)))"
                 " * (1.0 - smoothstep(0.985, 1.0, r))", r=rho, n=n)
    oi = nb.node("ShaderNodeObjectInfo")
    finish_additive(nb, (0.6, 0.8, 1.0, 1.0), nb.ex("ring * a * 14.0", ring=ring, a=oi.outputs["Alpha"]))
    return m


def mat_line(director):
    m = new_material("ConstellationLine", additive=True)
    nb = NodeBuilder(m.node_tree)
    oi = nb.node("ShaderNodeObjectInfo")
    g = channel_value(nb, director, "c*(1+0.8*k)", "constellation", c="constellation", k="kick")
    lw = nb.node("ShaderNodeLayerWeight", {"Blend": 0.5})
    core = nb.ex("pow(1.0 - f, 2.0)", f=lw.outputs["Facing"])
    finish_additive(nb, (0.62, 0.8, 1.0, 1.0), nb.ex("g * a * c * 7.0", g=g, a=oi.outputs["Alpha"], c=core))
    return m


def mat_constellation_stars(director):
    m = new_material("ConstellationStars", additive=True)
    nb = NodeBuilder(m.node_tree)
    order = nb.node("ShaderNodeAttribute", attribute_name="order", attribute_type="GEOMETRY").outputs["Fac"]
    flux = nb.node("ShaderNodeAttribute", attribute_name="flux", attribute_type="GEOMETRY").outputs["Fac"]
    c = channel_value(nb, director, "c", "constellation", c="constellation")
    dr = channel_value(nb, director, "d", "draw", d="draw")
    k = channel_value(nb, director, "k", "kick", k="kick")
    s = nb.ex("c * flux * 90.0 * (1.0 + 2.5*exp(-pow((d - o)*1.4, 2.0)) + 0.6*k)",
              c=c, flux=flux, d=dr, o=order, k=k)
    finish_additive(nb, (0.78, 0.88, 1.0, 1.0), s)
    return m


def mat_streak(director, name, channel, color=(0.7, 0.85, 1.0), k=6.0):
    """Warp streaks (moving dashes) - brightness from a director channel."""
    m = new_material(name, additive=True)
    nb = NodeBuilder(m.node_tree)
    p = nb.node("ShaderNodeTexCoord").outputs["Object"]
    _, _, z = nb.separate(p)
    rnd = nb.node("ShaderNodeAttribute", attribute_name="rnd", attribute_type="GEOMETRY").outputs["Fac"]
    off = channel_value(nb, director, "o", "warp offset", o="warp_offset")
    dash = nb.ex("pow(fract(z*0.035 + o + r*7.0), 6.0)", z=z, o=off, r=rnd)
    g = channel_value(nb, director, "w", channel, w=channel)
    finish_additive(nb, color + (1.0,), nb.ex("d * g * K * (0.4 + r)", d=dash, g=g, K=k, r=rnd))
    return m


def mat_meteor():
    m = new_material("Meteor", additive=True)
    nb = NodeBuilder(m.node_tree)
    uv = nb.node("ShaderNodeTexCoord").outputs["UV"]
    u, v, _ = nb.separate(uv)
    oi = nb.node("ShaderNodeObjectInfo")
    s = nb.ex("pow(u, 4.0) * exp(-pow((v - 0.5)/0.18, 2.0)) * a * 40.0", u=u, v=v, a=oi.outputs["Alpha"])
    finish_additive(nb, (0.85, 0.92, 1.0, 1.0), s)
    return m


def mat_beam(director):
    m = new_material("PulsarBeam", additive=True)
    nb = NodeBuilder(m.node_tree)
    p = nb.node("ShaderNodeTexCoord").outputs["Object"]
    _, _, z = nb.separate(p)
    lw = nb.node("ShaderNodeLayerWeight", {"Blend": 0.5})
    g = channel_value(nb, director, "u*p*(1+0.8*k)", "pulsar", u="universe", p="pulsar", k="kick")
    s = nb.ex("exp(-abs(z)/7.0) * pow(1.0 - f, 3.0) * g * 5.0", z=z, f=lw.outputs["Facing"], g=g)
    finish_additive(nb, (0.6, 0.8, 1.0, 1.0), s)
    return m


def mat_title():
    m = new_material("TitleText", additive=True)
    nb = NodeBuilder(m.node_tree)
    oi = nb.node("ShaderNodeObjectInfo")
    finish_additive(nb, (0.85, 0.92, 1.0, 1.0), nb.ex("a * 3.0", a=oi.outputs["Alpha"]))
    return m


# ============================================================================
#  11. CAMERA CHOREOGRAPHY  (a 10-act flight, all in numpy)
# ============================================================================

class Path:
    def __init__(self, n_frames, fps, spin):
        self.F, self.fps, self.spin = n_frames, fps, spin
        self.pos = np.zeros((n_frames, 3))
        self.tgt = np.zeros((n_frames, 3))
        self.lens = np.zeros(n_frames)
        self.roll = np.zeros(n_frames)
        self.end = None
        self.joins = []

    def spin_at(self, f):
        return self.spin[min(max(int(f), 0), self.F - 1)]

    def segment(self, f0, f1, fn, space="world"):
        """fn(s) -> (pos(n,3), tgt(n,3), lens(n), roll(n)); s runs 0..1 over [f0, f1]."""
        if f1 <= f0:
            return
        s = (np.arange(f0, f1) - f0) / float(f1 - f0)
        s_all = np.append(s, 1.0)
        p, t, ln, rl = fn(s_all)
        spins = np.append(self.spin[f0:f1], self.spin_at(f1))
        if space == "local":
            p = rotz(p, spins)
            t = rotz(t, spins)
        self.pos[f0:f1], self.tgt[f0:f1] = p[:-1], t[:-1]
        self.lens[f0:f1], self.roll[f0:f1] = ln[:-1], rl[:-1]
        if self.end is not None:
            self.joins.append(f0)
        self.end = dict(pos=p[-1], tgt=t[-1], lens=float(ln[-1]), roll=float(rl[-1]), frame=f1)

    def start_local(self):
        a = self.spin_at(self.end["frame"])
        return rotz(self.end["pos"], -a)[0], rotz(self.end["tgt"], -a)[0]

    def fillet(self, seconds=0.55):
        w0 = int(seconds * self.fps)
        bounds = [0] + self.joins + [self.F]
        for j_i, j in enumerate(self.joins):
            w = max(2, min(w0, (j - bounds[j_i]) // 3, (bounds[j_i + 2] - j) // 3))
            a, b = j - w, j + w
            if a < 1 or b > self.F - 2:
                continue
            for arr in (self.pos, self.tgt, self.lens, self.roll):
                v = arr if arr.ndim == 2 else arr[:, None]
                p0, p1 = v[a].copy(), v[b].copy()
                m0 = (v[a] - v[a - 1]) * (b - a)
                m1 = (v[b + 1] - v[b]) * (b - a)
                s = ((np.arange(a, b + 1) - a) / (b - a))[:, None]
                h = (2 * s**3 - 3 * s**2 + 1) * p0 + (s**3 - 2 * s**2 + s) * m0 + (-2 * s**3 + 3 * s**2) * p1 + (s**3 - s**2) * m1
                v[a:b + 1] = h


def spin_schedule(song):
    """Galaxy rotation angle per frame; it spins faster when the chorus hits."""
    speed = {"INTRO": 0.3, "VERSE1": 0.3, "BUILD1": 0.6, "CHORUS1": 3.0, "VERSE2": 0.35, "BUILD2": 0.4,
             "CHORUS2": 0.8, "BRIDGE": 0.3, "FINALE": 2.0, "OUTRO": 1.0}
    deg = np.array([speed[ACT_KEYS[k]] for k in song.act_index])
    deg = _moving_avg(deg, song.fps * 1.5)
    return np.cumsum(np.radians(deg) / song.fps)


def choreograph(song, kp, aspect):
    fps = song.fps
    spin = spin_schedule(song)
    path = Path(song.n_frames, fps, spin)
    fr = song.frames_of
    er, et, ez = kp.e_r, kp.e_t, kp.e_z
    N, S = kp.nebula, kp.destiny

    # ---- 1 INTRO: a single star in the dark; the universe fades in around it
    def intro(s):
        e = smoother(s)
        d0 = norm(S - N + 0.35 * ez)
        ang = np.radians(25.0) * e
        dirs = rotz(np.repeat(d0[None], len(s), 0), ang)
        dist = loglerp(0.33, 2.4, e ** 1.2)
        pos = S[None] + dirs * dist[:, None]
        tgt = S[None] + (N - S)[None] * 0.22 * smoothstep(0.55, 1.0, s)[:, None]
        return pos, tgt, mix(50.0, 40.0, e), np.radians(mix(0.0, 5.0, e))
    path.segment(*fr("INTRO"), intro, "local")

    # ---- 2 VERSE1: drift through the Destiny Nebula and its newborn cluster
    p0, t0 = path.start_local()
    cams = [p0, N + 5.5 * er + 2.5 * et + 1.6 * ez, N + 3.2 * er - 2.6 * et + 2.2 * ez,
            N - 1.2 * er - 4.6 * et + 2.8 * ez, N - 3.5 * er - 6.2 * et + 5.0 * ez]
    tgts = [t0, S, kp.cluster, kp.cluster, N - 3.5 * et + 1.0 * ez]
    times = [0.0, 0.22, 0.5, 0.78, 1.0]

    def verse1(s):
        return (timed_spline(times, cams, s), timed_spline(times, tgts, s),
                mix(40.0, 30.0, smoother(s)), np.radians(5.0 * np.cos(s * math.pi * 1.5)))
    path.segment(*fr("VERSE1"), verse1, "local")

    # ---- 3 BUILD1: the pull - rocket up and out of the arm
    p0, t0 = path.start_local()
    off0 = p0 - N
    d0 = float(np.linalg.norm(off0))
    dir1 = norm(0.25 * er - 0.35 * et + 0.9 * ez)

    def build1(s):
        e = smoother(s)
        focus = mixv(N, 0.62 * N, e)
        dirs = slerp_dir(off0, dir1, e)
        dist = loglerp(d0, 150.0, ease_in(s, 2.3))
        pos = focus + dirs * dist[:, None]
        blend = smoothstep(0.0, 0.3, s)[:, None]
        tgt = t0[None] * (1 - blend) + focus * blend
        return pos, tgt, mix(30.0, 20.0, ease_in(s, 1.5)), np.radians(mix(0.0, -10.0, e))
    path.segment(*fr("BUILD1"), build1, "local")

    # ---- 4 CHORUS1: the whole galaxy revealed, a majestic spinning orbit
    c0 = path.end["pos"]
    tg0 = path.end["tgt"]
    dA, azA, elA = to_sph(c0)
    # choose the orbit sweep so it finishes above the outer end of a spiral arm
    f_c1 = fr("CHORUS1")
    a_end = path.spin_at(f_c1[1])
    best = None
    for n_arm in (0, 1):
        q = arm_point(112.0, n_arm)
        sweep = wrap_angle(math.atan2(q[1], q[0]) + a_end - azA)
        score = abs(abs(math.degrees(sweep)) - 85.0)
        if best is None or score < best[0]:
            best = (score, n_arm, sweep)
    _, kp.flight_arm, sweep = best

    def chorus1(s):
        e = smoother(s)
        dist = loglerp(dA, 265.0, ease_out(s, 2.0))
        el = mix(elA, math.radians(30.0), e)
        az = azA + sweep * mix(s, e, 0.5)
        pos = sph(dist, az, el)
        blend = smoothstep(0.0, 0.3, s)[:, None]
        tgt = tg0[None] * (1 - blend)
        return pos, tgt, mix(20.0, 32.0, e), np.radians(mix(-10.0, 3.0, e))
    path.segment(*f_c1, chorus1, "world")

    # ---- 5 VERSE2: swoop down and fly low along a spiral arm
    n_arm = kp.flight_arm
    p0, t0 = path.start_local()
    radii = [112.0, 100.0, 84.0, 66.0, 50.0]
    heights = [34.0, 4.0, 3.0, 3.2, 3.6]
    lat_off = [-10.0, -10.0, -10.0, -11.0, -10.0]
    pts, tgs = [p0], [t0]
    for r, h, lo in zip(radii, heights, lat_off):
        _, lat = arm_frame(r, n_arm)
        pts.append(arm_point(r, n_arm) + lat * lo + np.array([0, 0, h]))
        _, lat2 = arm_frame(r - 16.0, n_arm)
        tgs.append(arm_point(r - 16.0, n_arm) + lat2 * (lo + 6.0) + np.array([0, 0, 1.2]))
    v_times = [0.0, 0.2, 0.36, 0.58, 0.8, 1.0]
    kp.pulsar = arm_point(74.0, n_arm) + arm_frame(74.0, n_arm)[1] * -19.0 + np.array([0, 0, 5.0])

    def verse2(s):
        pos = timed_spline(v_times, pts, s)
        tgt = timed_spline(v_times, tgs, s)
        lens = np.where(s < 0.36, mix(32.0, 22.0, smoother(s / 0.36)), 22.0)
        roll = np.radians(7.0 * np.sin(math.pi * smoothstep(0.3, 1.0, s)))
        return pos, tgt, lens, roll
    path.segment(*fr("VERSE2"), verse2, "local")

    # ---- 6 BUILD2: rise to the one viewpoint where the stars align
    p0, t0 = path.start_local()
    vh = norm(np.array([-p0[0], -p0[1], 0.0]))
    c_star = p0 - 30.0 * vh + np.array([0.0, 0.0, 24.0])
    t_star = np.array([0.0, 0.0, 2.0])
    kp.align_cam, kp.align_tgt = c_star, t_star
    b_pts = [p0, 0.5 * (p0 + c_star) + np.array([0, 0, 9.0]) - 6.0 * vh, c_star]
    b_tgt = [t0, 0.5 * (t0 + t_star), t_star]

    def build2(s):
        e = smoother(s)
        return (timed_spline([0, 0.55, 1.0], b_pts, e), timed_spline([0, 0.45, 1.0], b_tgt, e),
                mix(22.0, 35.0, e), np.radians(mix(float(np.degrees(path.end["roll"])), 0.0, e)))
    path.segment(*fr("BUILD2"), build2, "local")

    # ---- 7 CHORUS2: hold the alignment while the constellation draws itself
    beats_per_sway = 16.0 * 60.0 / song.bpm
    c2a, c2b = song.act("CHORUS2")
    kp.align_lens = 38.0

    def chorus2(s):
        e = smoother(s)
        leave = smoothstep(0.82, 1.0, s) ** 2
        pos = c_star[None] + (t_star - c_star)[None] * 0.12 * leave[:, None]
        tgt = np.repeat(t_star[None], len(s), 0)
        t_abs = c2a + s * (c2b - c2a)
        roll = np.radians(3.0 * np.sin(2 * math.pi * (t_abs - c2a) / beats_per_sway)) * (1 - leave)
        return pos, tgt, mix(35.0, 44.0, e), roll
    path.segment(*fr("CHORUS2"), chorus2, "local")

    # ---- 8 BRIDGE: fall into the heart of the galaxy - the black hole
    p0, t0 = path.start_local()
    dB, azB, elB = to_sph(p0)

    def bridge(s):
        e = ease_out(s, 2.5)
        dist = loglerp(dB, 7.5, e)
        el = mix(elB, math.radians(11.0), smoother(s))
        az = azB + math.radians(55.0) * e + math.radians(12.0) * s
        blend = smoother(smoothstep(0.0, 0.5, s))[:, None]
        tgt = t0[None] * (1 - blend)
        return sph(dist, az, el), tgt, mix(44.0, 30.0, smoother(s)), np.radians(mix(0.0, 4.0, smoother(s)))
    path.segment(*fr("BRIDGE"), bridge, "local")

    # ---- 9 FINALE: the core ignites - blast back out past the jets
    c0 = path.end["pos"]
    dF, azF, elF = to_sph(c0)

    def finale(s):
        s1 = clip01(s / 0.5)
        s2 = clip01((s - 0.5) / 0.5)
        dist = np.where(s < 0.5, loglerp(dF, 520.0, ease_out(s1, 2.2)), loglerp(520.0, 3600.0, smoother(s2)))
        el = np.where(s < 0.5, mix(elF, math.radians(24.0), smoother(s1)), mix(math.radians(24.0), math.radians(38.0), smoother(s2)))
        az = azF + math.radians(25.0) * s
        lens = np.where(s < 0.5, mix(30.0, 22.0, ease_out(s1, 3.0)), mix(22.0, 30.0, smoother(s2)))
        roll = np.radians(np.where(s < 0.5, mix(4.0, -3.0, smoother(s1)), mix(-3.0, 0.0, smoother(s2))))
        return sph(dist, az, el), np.zeros((len(s), 3)), lens, roll
    path.segment(*fr("FINALE"), finale, "world")

    # ---- 10 OUTRO: drift out until the whole galaxy is one point of light
    c0 = path.end["pos"]
    dO, azO, elO = to_sph(c0)

    def outro(s):
        e = ease_out(s, 1.8)
        return (sph(loglerp(dO, 60000.0, e), azO + math.radians(10.0) * s, mix(elO, math.radians(55.0), smoother(s))),
                np.zeros((len(s), 3)), mix(30.0, 50.0, smoother(s)), np.zeros(len(s)))
    path.segment(*fr("OUTRO"), outro, "world")

    path.fillet()
    return path, spin


def camera_rotations(path, song, kick):
    """Look-at + roll + a little beat shake -> quaternions (continuous)."""
    n = song.n_frames
    quats = np.zeros((n, 4))
    prev = None
    rng = np.random.default_rng(99)
    chorus = np.isin(song.act_index, [ACT_KEYS.index(k) for k in ("CHORUS1", "CHORUS2", "FINALE")])
    shake_amp = np.radians(0.22) * kick * np.where(chorus, 1.0, 0.45)
    hand = np.radians(0.06)
    wob = np.stack([_moving_avg(rng.normal(size=n), song.fps * 0.7) for _ in range(2)], 1)
    wob /= max(1e-6, np.abs(wob).max())
    jit = rng.normal(size=(n, 2))
    for i in range(n):
        f = path.tgt[i] - path.pos[i]
        f = f / max(1e-9, np.linalg.norm(f))
        up = np.array([0.0, 0.0, 1.0])
        if abs(np.dot(f, up)) > 0.995:
            up = np.array([0.0, 1.0, 0.0])
        r = np.cross(f, up)
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        m = Matrix(((r[0], u[0], -f[0]), (r[1], u[1], -f[1]), (r[2], u[2], -f[2])))
        yaw = hand * wob[i, 0] + shake_amp[i] * jit[i, 0]
        pitch = hand * wob[i, 1] + shake_amp[i] * jit[i, 1]
        m = m @ Matrix.Rotation(path.roll[i], 3, "Z") @ Matrix.Rotation(pitch, 3, "X") @ Matrix.Rotation(yaw, 3, "Y")
        q = m.to_quaternion()
        if prev is not None and q.dot(prev) < 0:
            q.negate()
        prev = q
        quats[i] = (q.w, q.x, q.y, q.z)
    return quats


def gas_emission_np(p, kp):
    """numpy twin of the gas shaders (without the fine noise) for the light meter."""
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    r = np.sqrt(x * x + y * y) + 1e-3
    ph = arm_phase(r, np.arctan2(y, x))
    arms = np.maximum(((1 + np.cos(ph)) * 0.5) ** 4, 0.25 * ((1 - np.cos(ph)) * 0.5) ** 6 * smoothstep(40, 65, r))
    disk = np.exp(-r / 34.0) * np.exp(-(z / (1.2 + 0.012 * r)) ** 2) * (1 - smoothstep(95, 136, r))
    e = disk * (0.1 + 1.6 * arms * arm_mask(r) * 0.85) * 0.85
    e += np.exp(-(x / 17) ** 2 - (y / 4.5) ** 2 - (z / 2.2) ** 2) * 0.62
    R = np.sqrt(x * x + y * y + (z / 0.65) ** 2)
    e += (1.2 * np.exp(-R / 3.0) + 0.25 * np.exp(-(R / 10) ** 2)) * (0.1 + 0.9 * smoothstep(1.2, 5.5, R)) * 0.8
    dn = np.linalg.norm(p - kp.nebula, axis=-1)
    dc = np.linalg.norm(p - kp.cluster, axis=-1)
    e += 0.16 * (0.9 + 2.5 * np.exp(-dc / 2.5)) * smoothstep(9.0, 4.0, dn)
    return e


def light_meter(pos, tgt, lens, spin, kp, aspect):
    """Average gas radiance seen by a camera (24 rays through the numpy gas)."""
    gx, gy = np.meshgrid(np.linspace(-0.8, 0.8, 6), np.linspace(-0.75, 0.75, 4))
    ndc = np.stack([gx.ravel(), gy.ravel()], 1)
    u = (np.arange(1, 161) / 160.0) ** 1.6
    f = norm(tgt - pos)
    up = np.array([0.0, 0.0, 1.0]) if abs(f[2]) < 0.995 else np.array([0.0, 1.0, 0.0])
    rt = norm(np.cross(f, up))
    uv = np.cross(rt, f)
    tx = 36.0 / (2.0 * lens)
    dirs = f[None] + ndc[:, :1] * tx * rt[None] + ndc[:, 1:] * (tx / aspect) * uv[None]
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    cl = rotz(pos, -spin)[0]
    dl = rotz(dirs, -spin)
    b = dl @ cl
    disc = b * b - (cl @ cl - 150.0 ** 2)
    sq = np.sqrt(np.maximum(disc, 0.0))
    t0 = np.maximum(-b - sq, 0.0)
    t1 = np.maximum(-b + sq, 0.0)
    ts = t0[:, None] + (t1 - t0)[:, None] * u[None, :]
    pts = cl[None, None, :] + dl[:, None, :] * ts[:, :, None]
    ds = np.diff(np.concatenate([t0[:, None], ts], 1), axis=1)
    rad = (gas_emission_np(pts, kp) * ds).sum(1) * (disc > 0)
    return float(rad.mean())


def auto_exposure(song, path, spin, kp, aspect):
    """Exposure (in stops) that keeps every shot as bright as the face-on reveal."""
    ref = light_meter(np.array([0.0, -60.0, 330.0]), np.zeros(3), 30.0, 0.0, kp, aspect)
    idx = np.arange(0, song.n_frames, 3)
    meter = np.array([light_meter(path.pos[i], path.tgt[i], path.lens[i], spin[i], kp, aspect) for i in idx])
    meter = np.interp(np.arange(song.n_frames), idx, meter)
    ev = np.clip(-0.78 * np.log2((meter + 1e-4) / ref), -5.0, 0.4)
    # a touch of artistic exposure per act on top of the meter (in stops)
    bias = {"INTRO": 0.5, "VERSE1": 1.6, "BUILD1": 0.3, "CHORUS1": 0.0, "VERSE2": 0.3, "BUILD2": 0.0,
            "CHORUS2": 0.0, "BRIDGE": 0.8, "FINALE": 0.0, "OUTRO": 0.0}
    ev = ev + np.array([bias[ACT_KEYS[k]] for k in song.act_index])
    ev = _moving_avg(ev, song.fps * 0.8)
    u = song.act_u
    ev = np.where(song.act_index == 0, ev * smoothstep(0.1, 0.7, u), ev)
    ev = np.where(song.act_index == len(ACTS) - 1, ev * (1.0 - smoothstep(0.3, 0.9, u)), ev)
    return ev


# ============================================================================
#  12. STORY CHANNELS  (what should be visible / bright at every frame)
# ============================================================================

def story_channels(song, director, kick, beat):
    n, fps = song.n_frames, song.fps
    ai, u = song.act_index, song.act_u
    K = {k: i for i, k in enumerate(ACT_KEYS)}
    is_ = lambda key: ai == K[key]  # noqa: E731

    def per_act(values, smooth=1.0):
        arr = np.array([values[ACT_KEYS[k]] for k in ai], dtype=float)
        return _moving_avg(arr, fps * smooth)

    t = song.t
    director.set("time", t)
    director.set("energy", song.energy)
    director.set("bass", np.clip(song.bass, 0, 1))
    director.set("sparkle", np.clip(song.sparkle, 0, 1))
    director.set("kick", kick)
    director.set("beat", beat)

    # universe fades in during the intro and out at the very end
    intro_in = np.where(is_("INTRO"), smoothstep(0.05, 0.8, u), 1.0)
    outro_out = np.where(is_("OUTRO"), 1.0 - smoothstep(0.35, 0.9, u), 1.0)
    universe = np.minimum(intro_in, outro_out)
    director.set("universe", universe)
    director.set("fadeout", outro_out)

    # stars ignite one after another, in bursts on the kicks
    f0, f1 = song.frames_of("INTRO")
    ign = np.full(n, 1.3)
    kk = kick[f0:f1]
    cum = np.cumsum(kk)
    cum = cum / max(1e-6, cum[-1]) if cum[-1] > 0 else np.linspace(0, 1, f1 - f0)
    lin = np.linspace(0.0, 1.0, f1 - f0)
    ign[f0:f1] = 0.02 + 1.25 * (0.35 * lin + 0.65 * cum)
    director.set("ignite", ign)

    director.set("star_gain", per_act({"INTRO": 1.0, "VERSE1": 1.0, "BUILD1": 1.1, "CHORUS1": 1.25, "VERSE2": 1.0,
                                       "BUILD2": 1.05, "CHORUS2": 1.15, "BRIDGE": 0.9, "FINALE": 1.3, "OUTRO": 1.0}))
    # the gas dims near the black hole so the accretion disk can shine, then floods
    # back as the camera blasts out in the finale
    gg = np.array([{"INTRO": 0.4, "VERSE1": 0.55, "BUILD1": 0.95, "CHORUS1": 1.15, "VERSE2": 1.0, "BUILD2": 1.0,
                    "CHORUS2": 1.0, "BRIDGE": 0.3, "FINALE": 1.2, "OUTRO": 1.1}[ACT_KEYS[k]] for k in ai], dtype=float)
    gg = np.where(is_("BRIDGE"), mix(0.9, 0.3, smoothstep(0.0, 0.45, u)), gg)
    gg = np.where(is_("FINALE"), mix(0.3, 1.2, smoothstep(0.08, 0.5, u)), gg)
    director.set("galaxy_gain", _moving_avg(gg, fps * 1.0))
    director.set("nebula_gain", per_act({k: 1.0 for k in ACT_KEYS}))
    bh = per_act({"INTRO": 0.3, "VERSE1": 0.3, "BUILD1": 0.3, "CHORUS1": 0.35, "VERSE2": 0.35, "BUILD2": 0.4,
                  "CHORUS2": 0.45, "BRIDGE": 1.0, "FINALE": 1.2, "OUTRO": 0.8}, 3.0)
    director.set("bh", bh)

    fa, _ = song.act("FINALE")
    jets = np.where(t >= fa, smoothstep(fa, fa + 0.35, t), 0.0)
    director.set("jets", jets)

    b1 = np.where(is_("BUILD1"), smoothstep(0.1, 0.95, u) * 0.9, 0.0)
    c1a, _ = song.act("CHORUS1")
    b1 = np.maximum(b1, np.where((t >= c1a) & (t < c1a + 1.2), 0.9 * (1 - smoothstep(c1a, c1a + 1.2, t)), 0.0))
    fin = np.where(is_("FINALE"), 1.0 - smoothstep(0.0, 0.22, u), 0.0) * smoothstep(fa, fa + 0.3, t)
    warp = np.maximum(b1, fin)
    director.set("warp", warp)
    director.set("warp_offset", np.cumsum(0.4 + 2.2 * warp) / fps)

    const = np.zeros(n)
    const += np.where(is_("BUILD2"), smoothstep(0.0, 0.6, u), 0.0)
    const += np.where(is_("CHORUS2"), 1.0, 0.0)
    const += np.where(is_("BRIDGE"), 1.0 - smoothstep(0.0, 0.35, u), 0.0)
    director.set("constellation", const)
    director.set("draw", np.full(n, -2.0))   # filled in on the beat by schedule_events

    flash = np.zeros(n)
    for key, amp in (("CHORUS1", 0.8), ("CHORUS2", 0.5), ("FINALE", 1.15)):
        a, _ = song.act(key)
        flash = np.maximum(flash, np.where(t >= a, amp * np.exp(-(t - a) / 0.55), 0.0))
    director.set("flash", flash)

    # after the opening the Destiny Star becomes one star among many
    destiny = np.full(n, 0.03)
    destiny = np.where(is_("INTRO"), 1.0 + 1.4 * kick * (1 - u), destiny)
    destiny = np.where(is_("VERSE1"), mix(1.0, 0.03, smoothstep(0.0, 0.8, u)), destiny)
    destiny = np.where(ai >= K["OUTRO"], 0.0, destiny)
    destiny[0] = 1.0
    director.set("destiny", destiny)

    beacon = np.where(is_("OUTRO"), smoothstep(0.3, 0.88, u), 0.0)
    beacon[-1] = 1.0
    director.set("beacon", beacon)

    director.set("pulsar", _moving_avg(np.where(is_("VERSE2") | is_("BUILD2"), 1.0, 0.04), fps * 2.0))
    director.set("deepfield", per_act({"INTRO": 0.5, "VERSE1": 0.5, "BUILD1": 0.6, "CHORUS1": 0.8, "VERSE2": 0.6,
                                       "BUILD2": 0.7, "CHORUS2": 0.8, "BRIDGE": 0.6, "FINALE": 1.0, "OUTRO": 1.0}))
    return director


# ============================================================================
#  13. BUILD THE UNIVERSE
# ============================================================================

def purge_previous():
    old = bpy.data.scenes.get(SCENE_NAME)
    if old is not None:
        if len(bpy.data.scenes) == 1:
            bpy.data.scenes.new("Scene")
        for w in bpy.context.window_manager.windows:
            if w.scene == old:
                w.scene = [s for s in bpy.data.scenes if s != old][0]
        bpy.data.scenes.remove(old)
    for coll_name in ("objects", "meshes", "curves", "materials", "node_groups", "cameras", "worlds",
                      "collections", "actions", "sounds", "images"):
        coll = getattr(bpy.data, coll_name)
        for idb in list(coll):
            if idb.name.startswith(PREFIX):
                try:
                    coll.remove(idb)
                except Exception:  # noqa: BLE001
                    pass


def build(cfg, song):
    t_start = time.time()
    q = QUALITY_PRESETS[cfg["QUALITY"]]
    rng = np.random.default_rng(int(cfg["SEED"]))
    purge_previous()
    scene = bpy.data.scenes.new(SCENE_NAME)
    for w in bpy.context.window_manager.windows:
        w.scene = scene
    scene.render.fps = song.fps
    scene.render.fps_base = 1.0
    scene.render.resolution_x, scene.render.resolution_y = cfg["RESOLUTION"]
    scene.render.resolution_percentage = 50 if cfg["QUALITY"] == "PREVIEW" else 100
    scene.frame_start, scene.frame_end = 1, song.n_frames
    aspect = cfg["RESOLUTION"][0] / cfg["RESOLUTION"][1]

    root = bpy.data.collections.new(PREFIX + "Endless Destiny")
    scene.collection.children.link(root)
    c_rig = new_collection("Camera & Director", root)
    c_gal = new_collection("Galaxy", root)
    c_fx = new_collection("Effects", root)
    c_deep = new_collection("Deep Field", root)

    kp = KeyPoints()
    kick, beat = song.pulses()

    director = Director(scene, c_rig, song.n_frames)
    story_channels(song, director, kick, beat)

    log("Choreographing the camera...")
    path, spin = choreograph(song, kp, aspect)
    log("Metering the light for every shot...")
    ev = auto_exposure(song, path, spin, kp, aspect)
    chorus = np.isin(song.act_index, [ACT_KEYS.index(k) for k in ("CHORUS1", "CHORUS2", "FINALE")])
    director.set("exposure", ev + 1.25 * director.get("flash") + 0.07 * kick * chorus)

    cam_data = bpy.data.cameras.new(PREFIX + "Camera")
    cam_data.sensor_width = 36.0
    cam_data.sensor_fit = "HORIZONTAL"
    cam = new_object("Camera", cam_data, c_rig)
    cam.rotation_mode = "QUATERNION"
    scene.camera = cam

    galaxy = new_object("Galaxy", None, c_gal)
    galaxy.empty_display_size = 40.0

    # ---- stars -----------------------------------------------------------
    log(f"Generating {q['stars']:,} stars...")
    stars = generate_stars(rng, q["stars"], kp)
    log(f"  {len(stars['pos']):,} stars made")
    sizer = star_sizer_group()
    m_stars = mat_stars(director, len(stars["pos"]))
    me = point_mesh("Stars", stars["pos"], {
        "star_color": stars["color"], "lum": stars["lum"], "rad": stars["rad"], "phase": stars["phase"],
        "reveal": stars["reveal"], "pulse": stars["pulse"], "pop": stars["pop"]})
    ob_stars = new_object("Stars", me, c_gal, galaxy)
    add_star_sizer(ob_stars, sizer, cam, m_stars, 0.9, 5.0)

    # ---- gas ----------------------------------------------------------------
    ob = new_object("GalaxyGas", cylinder_mesh("GalaxyGasShape", 140.0, -5.5, 5.5, 96), c_gal, galaxy)
    ob.data.materials.append(mat_galaxy_gas(director))
    ob = new_object("BulgeGlow", sphere_mesh("BulgeShape", 26.0, 48, 24), c_gal, galaxy)
    ob.data.materials.append(mat_bulge(director))
    puff_pos, puff_col, puff_rad, puff_glow = generate_puffs(rng, max(300, q["stars"] // 800))
    me = point_mesh("Puffs", puff_pos, {"puff_color": puff_col, "rad": puff_rad, "glow": puff_glow})
    ob = new_object("NebulaPuffs", me, c_gal, galaxy)
    mod = ob.modifiers.new(PREFIX + "PuffSizer", "NODES")
    mod.node_group = puff_sizer_group()
    mod[[i.identifier for i in mod.node_group.interface.items_tree
         if getattr(i, "in_out", "") == "INPUT" and i.name == "Material"][0]] = mat_puffs(director)
    ob = new_object("DestinyNebula", sphere_mesh("NebulaShape", NEBULA_SIZE * 1.3, 48, 24), c_gal, galaxy, kp.nebula)
    ob.data.materials.append(mat_nebula(director, kp.cluster - kp.nebula))

    # ---- special stars ----------------------------------------------------
    m_special = mat_special_star()
    destiny = new_object("DestinyStar", point_mesh("DestinyPoint", [[0, 0, 0]], {"rad": [0.00008]}), c_gal, galaxy, kp.destiny)
    add_star_sizer(destiny, sizer, cam, m_special, 2.4, 2.4)
    beacon = new_object("Beacon", point_mesh("BeaconPoint", [[0, 0, 0]], {"rad": [0.00008]}), c_gal, galaxy)
    add_star_sizer(beacon, sizer, cam, m_special, 2.4, 2.4)
    frames = director.frames
    bake(destiny, "color", 3, frames, director.get("destiny"))
    bake(beacon, "color", 3, frames, director.get("beacon"))

    # ---- black hole ---------------------------------------------------------
    bh = new_object("BlackHole", None, c_gal, galaxy)
    ob = new_object("EventHorizon", sphere_mesh("HorizonShape", BH_RADIUS, 48, 24), c_gal, bh)
    ob.data.materials.append(mat_black())
    ob = new_object("AccretionDisk", disc_mesh("AccretionShape", 0.9, 4.6, 160, 24), c_gal, bh)
    ob.data.materials.append(mat_accretion(director))
    halo = new_object("LensedHalo", quad_mesh("HaloQuad", [[0, 0, 0]], [[2.6, 0, 0]], [[0, 2.6, 0]]), c_gal, bh)
    halo.data.materials.append(mat_lensed_halo(director))
    con = halo.constraints.new("TRACK_TO")
    con.target, con.track_axis, con.up_axis = cam, "TRACK_Z", "UP_Y"
    m_jet = mat_jet(director)
    for name, sgn in (("JetNorth", 1.0), ("JetSouth", -1.0)):
        ob = new_object(name, cylinder_mesh(name + "Shape", 0.25, 0.4 * sgn, 160.0 * sgn, 32, caps=False, r1=7.0, rings=40),
                        c_fx, bh)
        ob.data.materials.append(m_jet)
    shock = new_object("Shockwave", quad_mesh("ShockQuad", [[0, 0, 0]], [[1, 0, 0]], [[0, 1, 0]]), c_fx, galaxy)
    shock.data.materials.append(mat_shockwave())

    # ---- echo rings (the Destiny Star's heartbeat and the final beacon) -----------
    m_ring = mat_ring(director)
    ring_quad = quad_mesh("RingQuad", [[0, 0, 0]], [[1, 0, 0]], [[0, 1, 0]])
    rings = []
    for i in range(8):
        parent = destiny if i < 5 else beacon
        ob = new_object(f"EchoRing{i:02d}", ring_quad, c_fx, parent)
        if i == 0:
            ob.data.materials.append(m_ring)
        con = ob.constraints.new("TRACK_TO")
        con.target, con.track_axis, con.up_axis = cam, "TRACK_Z", "UP_Y"
        rings.append(ob)

    # ---- the pulsar (beams sweep past once per beat) --------------------------
    pul = new_object("Pulsar", None, c_fx, galaxy, kp.pulsar)
    pul.rotation_euler = (math.radians(38.0), math.radians(12.0), 0.0)
    spin_e = new_object("PulsarSpin", None, c_fx, pul)
    star = new_object("PulsarStar", point_mesh("PulsarPoint", [[0, 0, 0]], {"rad": [0.02]}), c_fx, spin_e)
    add_star_sizer(star, sizer, cam, m_special, 1.8, 6.0)
    bake(star, "color", 3, frames, 0.6 * director.get("pulsar"))
    m_beam = mat_beam(director)
    for name, sgn in (("BeamA", 1.0), ("BeamB", -1.0)):
        me = cylinder_mesh(name + "Shape", 0.05, 0.1, 18.0, 24, caps=False, r1=0.9, rings=12)
        ob = new_object(name, me, c_fx, spin_e)
        ob.rotation_euler = (math.radians(-90.0 * sgn), 0.0, 0.0)
        ob.data.materials.append(m_beam)

    # ---- constellation of destiny ------------------------------------------------
    build_constellation(song, kp, director, cam, sizer, c_fx, galaxy, aspect, cfg)

    # ---- deep field + satellites ---------------------------------------------
    build_deep_field(rng, director, c_deep, galaxy, cam)

    # ---- camera-space effects: warp tunnel, meteors, titles ---------------------------
    build_warp(rng, director, c_fx, cam)
    meteors = build_meteors(c_fx, cam)
    titles = build_titles(cfg, c_fx, cam) if cfg["SHOW_TITLES"] else {}

    # ---- world ----------------------------------------------------------------
    mat_world(director, scene)

    # ---- animate ------------------------------------------------------------------
    log("Baking the animation...")
    schedule_events(song, kp, director, path, rings, shock, meteors, titles, spin_e, kick, scene, aspect)
    director.bake()
    bake(galaxy, "rotation_euler", 2, frames, spin)
    quats = camera_rotations(path, song, kick)
    for i in range(3):
        bake(cam, "location", i, frames, path.pos[:, i])
    for i in range(4):
        bake(cam, "rotation_quaternion", i, frames, quats[:, i])
    bake(cam_data, "lens", -1, frames, path.lens)
    focus_d = np.linalg.norm(path.pos - path.tgt, axis=1)
    bake(cam_data, "clip_start", -1, frames, np.clip(focus_d * 2e-4, 0.002, 0.3))
    bake(cam_data, "clip_end", -1, frames, np.maximum(40000.0, focus_d * 4.0))

    # ---- markers + audio --------------------------------------------------------
    for k, (key, title, _) in enumerate(ACTS):
        scene.timeline_markers.new(f"{k + 1}. {title}", frame=int(song.act_frame0[k]) + 1)
    if song.has_audio:
        se = scene.sequence_editor_create()
        try:
            seq_strips(se).new_sound(PREFIX + "Song", song.audio_path, 1, 1)
            scene.sync_mode = "AUDIO_SYNC"
        except RuntimeError as e:  # only the pip "bpy" module lacks audio support
            log(f"Could not add the song to the timeline ({e}). The animation is still synced to it.")

    # In the solid viewport, show volumes as boxes and glow cards as wireframes so
    # they don't hide the stars. None of this changes the render.
    for ob in root.all_objects:
        base = ob.name[len(PREFIX):]
        if base in ("GalaxyGas", "BulgeGlow", "DestinyNebula"):
            ob.display_type = "BOUNDS"
        elif ob.type == "MESH" and not base.startswith(("Stars", "Constellation", "DestinyStar", "Beacon",
                                                          "PulsarStar", "NebulaPuffs", "EventHorizon")):
            ob.display_type = "WIRE"

    setup_render(scene, cfg, q, path, director)
    log(f"Built in {time.time() - t_start:.1f} s")
    return scene, path, kp


def build_constellation(song, kp, director, cam, sizer, coll, galaxy, aspect, cfg):
    """14 bright stars at different depths that only line up into an infinity sign
    from one place in the galaxy - the alignment viewpoint at the end of BUILD2."""
    C, T = kp.align_cam, kp.align_tgt
    f = norm(T - C)
    r = norm(np.cross(f, [0, 0, 1]))
    u = np.cross(r, f)
    lens = kp.align_lens
    tan_x = 36.0 / (2 * lens)
    tan_y = tan_x / aspect
    rng = np.random.default_rng(int(cfg["SEED"]) + 1)
    n = 14
    ts = np.arange(n) * 2 * math.pi / n + math.pi / 28
    lx = np.cos(ts) / (1 + np.sin(ts) ** 2)
    ly = np.sin(ts) * np.cos(ts) / (1 + np.sin(ts) ** 2)
    xn = 0.58 * lx
    yn = 0.58 * ly * aspect + 0.04
    depth = rng.uniform(20.0, 52.0, n)
    pts = []
    for i in range(n):
        d = norm(f + xn[i] * tan_x * r + yn[i] * tan_y * u)
        pts.append(C + d * depth[i])
    pts = np.array(pts)
    px = 36.0 / (lens * cfg["RESOLUTION"][0])
    me = point_mesh("ConstellationPoints", pts, {"rad": depth * px * 2.4, "order": np.arange(n, dtype=float)})
    ob = new_object("Constellation", me, coll, galaxy)
    add_star_sizer(ob, sizer, cam, mat_constellation_stars(director), 1.6, 7.0)
    m_line = mat_line(director)
    lines = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        w0, w1 = depth[i] * px * 0.7, depth[(i + 1) % n] * px * 0.7
        L = float(np.linalg.norm(b - a))
        me = cylinder_mesh(f"LineShape{i:02d}", w0, 0.0, L, 8, caps=False, r1=w1)
        ob = new_object(f"Line{i:02d}", me, coll, galaxy, a)
        ob.rotation_mode = "QUATERNION"
        ob.rotation_quaternion = Vector(b - a).to_track_quat("Z", "Y")
        ob.data.materials.append(m_line)
        ob.color = (1, 1, 1, 1)
        lines.append(ob)
    kp.lines = lines
    kp.constellation_points = pts


def build_deep_field(rng, director, coll, galaxy, cam):
    """3000 galaxies strung along a cosmic web, plus glows for the two satellites."""
    nodes = [np.array([2600.0, 900.0, -700.0])]
    while len(nodes) < 60:
        p = rng.normal(size=3)
        p = p / np.linalg.norm(p) * rng.uniform(3000.0, 30000.0)
        nodes.append(p)
    nodes = np.array(nodes)
    pos = []
    for i in range(len(nodes)):
        d = np.linalg.norm(nodes - nodes[i], axis=1)
        for j in np.argsort(d)[1:4]:
            if j < i:
                continue
            k = int(np.linalg.norm(nodes[j] - nodes[i]) / 350.0)
            s = rng.random(k)[:, None]
            pos.append(nodes[i] + (nodes[j] - nodes[i]) * s + rng.normal(size=(k, 3)) * 380.0)
    for p in nodes:
        pos.append(p + rng.normal(size=(40, 3)) * 1200.0)
    local = np.array([2600.0, 900.0, -700.0])
    pos.append(local * rng.uniform(0.2, 1.0, (30, 1)) + rng.normal(size=(30, 3)) * 700.0)
    pos = np.concatenate(pos)
    pos = pos[np.linalg.norm(pos, axis=1) > 800.0]
    if len(pos) > 3200:
        pos = pos[rng.choice(len(pos), 3200, replace=False)]
    n = len(pos)
    size = np.exp(rng.uniform(np.log(45.0), np.log(260.0), n))
    ax = rng.normal(size=(n, 3))
    ax /= np.linalg.norm(ax, axis=1, keepdims=True)
    tmp = np.where(np.abs(ax[:, 2:3]) < 0.9, np.array([[0, 0, 1.0]]), np.array([[1.0, 0, 0]]))
    uu = np.cross(ax, tmp)
    uu /= np.linalg.norm(uu, axis=1, keepdims=True)
    vv = np.cross(ax, uu)
    gal_type = np.where(rng.random(n) < 0.62, 1.0, np.where(rng.random(n) < 0.75, 0.0, 2.0))
    me = quad_mesh("DeepFieldQuads", pos, uu * size[:, None], vv * size[:, None],
                   {"gal_rand": rng.random(n), "gal_type": gal_type})
    ob = new_object("DeepField", me, coll)
    ob.data.materials.append(mat_galaxy_sprite(director))
    # satellites (they orbit with the galaxy, so they're parented to it and face the camera)
    m_sat = mat_galaxy_sprite(director, "SatelliteGlow", "universe", 1.6)
    for i, (c, sz) in enumerate(((np.array([168.0, -96.0, -42.0]), 16.0), (np.array([206.0, 44.0, -70.0]), 11.0))):
        me = quad_mesh(f"SatelliteQuad{i}", [[0, 0, 0]], [[sz, 0, 0]], [[0, sz, 0]], {"gal_rand": [0.3 + 0.4 * i], "gal_type": [2.0]})
        ob = new_object(f"SatelliteGlow{i}", me, coll, galaxy, c)
        ob.data.materials.append(m_sat)
        con = ob.constraints.new("TRACK_TO")
        con.target, con.track_axis, con.up_axis = cam, "TRACK_Z", "UP_Y"


def build_warp(rng, director, coll, cam):
    n = 1400
    ang = rng.uniform(0, 2 * math.pi, n)
    rad = rng.uniform(0.9, 4.0, n)
    z = rng.uniform(-60.0, -2.0, n)
    length = rng.uniform(3.0, 9.0, n)
    width = rng.uniform(0.01, 0.03, n)
    radial = np.stack([np.cos(ang), np.sin(ang), np.zeros(n)], 1)
    tangent = np.stack([-np.sin(ang), np.cos(ang), np.zeros(n)], 1)
    centers = radial * rad[:, None] + np.stack([np.zeros(n), np.zeros(n), z], 1)
    us = tangent * width[:, None]
    vs = np.repeat(np.array([[0.0, 0.0, 1.0]]), n, 0) * length[:, None]
    me = quad_mesh("WarpQuads", centers, us, vs, {"rnd": rng.random(n)})
    ob = new_object("WarpTunnel", me, coll, cam)
    ob.data.materials.append(mat_streak(director, "WarpStreak", "warp"))


def build_meteors(coll, cam):
    m = mat_meteor()
    quad = quad_mesh("MeteorQuad", [[0, 0, 0]], [[1, 0, 0]], [[0, 1, 0]])
    out = []
    for i in range(10):
        ob = new_object(f"Meteor{i:02d}", quad, coll, cam, (0, 0, -5.0))
        if i == 0:
            ob.data.materials.append(m)
        ob.rotation_mode = "XYZ"
        ob.color = (1, 1, 1, 0)
        ob.scale = (0.0001, 0.0001, 1)
        out.append(ob)
    return out


def build_titles(cfg, coll, cam):
    m = mat_title()
    out = {}
    specs = {"studio": cfg["STUDIO_NAME"], "presents": "presents", "song": cfg["SONG_TITLE"]}
    for key, text in specs.items():
        cu = bpy.data.curves.new(PREFIX + "Title_" + key, "FONT")
        cu.body = text
        cu.align_x, cu.align_y = "CENTER", "CENTER"
        cu.size = 1.0
        cu.space_character = 1.45
        ob = new_object("Title_" + key, cu, coll, cam, (0.0, 0.0, -1.0))
        ob.data.materials.append(m)
        ob.color = (1, 1, 1, 0)
        out[key] = ob
    return out


# ============================================================================
#  14. EVENTS ON THE BEAT  (echo rings, line drawing, meteors, titles, shockwave)
# ============================================================================

def fit_title(ob, lens, aspect, width_frac, y_frac):
    """Scale a camera-parented title (1 unit in front of the lens) to a fraction of the frame width."""
    half_w = 36.0 / (2.0 * lens)
    natural = max(1e-6, ob.dimensions.x / max(ob.scale.x, 1e-9))
    k = width_frac * 2.0 * half_w / natural
    ob.scale = (k, k, k)
    ob.location = (0.0, y_frac * half_w / aspect, -1.0)


def schedule_events(song, kp, director, path, rings, shock, meteors, titles, pulsar_spin, kick, scene=None, aspect=16 / 9):
    fps = song.fps
    frame = lambda t: 1.0 + t * fps  # noqa: E731
    beats = song.beat_times

    # echo rings around the Destiny Star in the intro, and the beacon in the outro
    ia, ib = song.act("INTRO")
    oa, ob_ = song.act("OUTRO")
    intro_beats = [b for b in (song.downbeats if (ib - ia) > 8 * 60 / song.bpm else beats) if ia + 0.3 < b < ib - 0.5]
    outro_beats = [b for b in song.downbeats if oa + 0.45 * (ob_ - oa) < b < ob_ - 1.5]
    ring_keys = {r.name: ([], []) for r in rings}
    events = [(b, 0) for b in intro_beats] + [(b, 1) for b in outro_beats]
    counters = [0, 0]
    for tb, which in events:
        pool = rings[:5] if which == 0 else rings[5:]
        r = pool[counters[which] % len(pool)]
        counters[which] += 1
        i = min(song.n_frames - 1, int(tb * fps))
        dist = float(np.linalg.norm(path.pos[i] - path.tgt[i])) if which == 1 else \
            float(np.linalg.norm(path.pos[i] - rotz(kp.destiny, path.spin[i])[0]))
        dist = max(dist, 0.05)
        half_h = dist * 36.0 / (2.0 * path.lens[i]) / 1.78
        s0, s1 = half_h * 0.03, half_h * 0.95
        dur = 1.8
        sk, ak = ring_keys[r.name]
        sk += [(frame(tb) - 1, s0), (frame(tb), s0), (frame(tb + dur), s1)]
        ak += [(frame(tb) - 1, 0.0), (frame(tb), 1.0), (frame(tb + dur), 0.0)]
    for r in rings:
        sk, ak = ring_keys[r.name]
        if not sk:
            r.scale = (0.001,) * 3
            r.color = (1, 1, 1, 0)
            continue
        for axis in range(3):
            bake_keys(r, "scale", axis, sk, "BEZIER")
        bake_keys(r, "color", 3, [(1.0, 0.0)] + ak, "LINEAR")

    # the constellation draws itself on the beats of CHORUS2
    ca, cb = song.act("CHORUS2")
    lines = kp.lines
    draw_beats = [b for b in beats if ca + 0.1 < b < ca + 0.58 * (cb - ca)]
    if len(draw_beats) >= len(lines):
        step = len(draw_beats) / len(lines)
        draw_times = [draw_beats[int(i * step)] for i in range(len(lines))]
    else:
        draw_times = list(np.linspace(ca + 0.2, ca + 0.58 * (cb - ca), len(lines)))
    draw = np.full(song.n_frames, -2.0)
    for i, (ln, tb) in enumerate(zip(lines, draw_times)):
        f0 = frame(tb)
        bake_keys(ln, "scale", 2, [(1.0, 0.0), (f0, 0.0), (f0 + 0.35 * fps, 1.0)], "BEZIER")
        draw = np.where(song.t >= tb, np.maximum(draw, i + smoothstep(tb, tb + 0.35, song.t)), draw)
    draw = np.where(song.t >= draw_times[-1] + 0.4, 20.0, draw)
    director.set("draw", draw)

    # the shockwave rolls through the disk when the heart ignites
    fa, _ = song.act("FINALE")
    f0 = frame(fa)
    bake_keys(shock, "scale", 0, [(1.0, 1.5), (f0, 1.5), (f0 + 7.0 * fps, 175.0)], "BEZIER")
    bake_keys(shock, "scale", 1, [(1.0, 1.5), (f0, 1.5), (f0 + 7.0 * fps, 175.0)], "BEZIER")
    bake_keys(shock, "color", 3, [(1.0, 0.0), (f0 - 1, 0.0), (f0, 1.0), (f0 + 2.0 * fps, 0.6), (f0 + 7.0 * fps, 0.0)], "LINEAR")

    # meteors on the strongest kicks of the choruses
    windows = []
    for key in ("CHORUS1", "CHORUS2", "FINALE"):
        a, b = song.act(key)
        windows.append((a + 0.25 * (b - a), b - 0.5))
    cands = [(t, s) for t, s in zip(song.kick_times, song.kick_strength) if any(a <= t <= b for a, b in windows)]
    cands.sort(key=lambda c: -c[1])
    chosen = []
    for t, s in cands:
        if all(abs(t - c) > 1.6 for c in chosen):
            chosen.append(t)
        if len(chosen) >= 24:
            break
    chosen.sort()
    rng = np.random.default_rng(5)
    mk = {m.name: dict(x=[], y=[], rz=[], a=[], sx=[], sy=[]) for m in meteors}
    for j, t in enumerate(chosen):
        m = meteors[j % len(meteors)]
        i = min(song.n_frames - 1, int(t * fps))
        half_w = 5.0 * 36.0 / (2.0 * path.lens[i])
        half_h = half_w / 1.78
        ang = rng.uniform(math.radians(200), math.radians(340))
        start = np.array([rng.uniform(-0.9, 0.9) * half_w, rng.uniform(0.2, 0.95) * half_h])
        travel = np.array([math.cos(ang), math.sin(ang)]) * half_w * rng.uniform(0.5, 0.9)
        end = start + travel
        length = half_w * rng.uniform(0.12, 0.22)
        dur = rng.uniform(0.35, 0.6)
        f0, f1 = frame(t), frame(t + dur)
        d = mk[m.name]
        d["x"] += [(f0 - 1, start[0]), (f0, start[0]), (f1, end[0])]
        d["y"] += [(f0 - 1, start[1]), (f0, start[1]), (f1, end[1])]
        d["rz"] += [(f0 - 1, ang), (f0, ang)]
        d["a"] += [(f0 - 1, 0.0), (f0, 1.0), (f0 + (f1 - f0) * 0.6, 0.8), (f1, 0.0)]
        d["sx"] += [(f0 - 1, length), (f0, length)]
        d["sy"] += [(f0 - 1, length * 0.02), (f0, length * 0.02)]
    for m in meteors:
        d = mk[m.name]
        if not d["x"]:
            continue
        bake_keys(m, "location", 0, d["x"], "LINEAR")
        bake_keys(m, "location", 1, d["y"], "LINEAR")
        bake_keys(m, "rotation_euler", 2, d["rz"], "CONSTANT")
        bake_keys(m, "scale", 0, d["sx"], "CONSTANT")
        bake_keys(m, "scale", 1, d["sy"], "CONSTANT")
        bake_keys(m, "color", 3, [(1.0, 0.0)] + d["a"], "LINEAR")

    # titles
    if titles:
        if scene is not None:
            for vl in scene.view_layers:
                vl.update()
        a, b = song.act("INTRO")
        lens = path.lens[min(song.n_frames - 1, int((a + 0.55 * (b - a)) * fps))]
        fit_title(titles["studio"], lens, aspect, 0.44, -0.52)
        fit_title(titles["presents"], lens, aspect, 0.11, -0.66)
        f0, f1 = frame(a + 0.3 * (b - a)), frame(a + 0.85 * (b - a))
        fade = min(1.2 * fps, (f1 - f0) / 3)
        for key in ("studio", "presents"):
            bake_keys(titles[key], "color", 3, [(1.0, 0.0), (f0, 0.0), (f0 + fade, 1.0), (f1 - fade, 1.0), (f1, 0.0)], "BEZIER")
        a, b = song.act("CHORUS1")
        lens = path.lens[min(song.n_frames - 1, int((a + 2.5) * fps))]
        fit_title(titles["song"], lens, aspect, 0.62, -0.5)
        f0, f1 = frame(a + 0.25), frame(a + min(5.5, 0.35 * (b - a)))
        fade = min(0.8 * fps, (f1 - f0) / 3)
        bake_keys(titles["song"], "color", 3, [(1.0, 0.0), (f0, 0.0), (f0 + fade * 0.5, 1.0), (f1 - fade, 1.0), (f1, 0.0)], "BEZIER")

    # pulsar: one full turn every two beats, so a beam sweeps past on every beat
    period = 60.0 / song.bpm
    phase = (song.t - song.beat_times[0]) / (2.0 * period) if len(song.beat_times) else song.t
    bake(pulsar_spin, "rotation_euler", 2, director.frames, phase * 2 * math.pi)


# ============================================================================
#  15. RENDER SETTINGS + COMPOSITOR
# ============================================================================

def enable_gpu(scene):
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
    except KeyError:
        return "CPU"
    for backend in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            prefs.compute_device_type = backend
            prefs.get_devices()
        except (TypeError, AttributeError):
            continue
        gpus = [d for d in prefs.devices if d.type != "CPU"]
        if gpus:
            for d in prefs.devices:
                d.use = d.type != "CPU"
            scene.cycles.device = "GPU"
            return backend
    return "CPU"


def glare(tree, kind, threshold, size, strength, streaks=4, angle=0.0, fade=0.9):
    g = tree.nodes.new("CompositorNodeGlare")
    names = {"BLOOM": "Bloom", "FOG_GLOW": "Fog Glow", "STREAKS": "Streaks"}
    if "Type" in g.inputs:                            # 5.0+
        g.inputs["Type"].default_value = names[kind]
        g.inputs["Quality"].default_value = "High"
    else:
        g.glare_type = kind
        g.quality = "HIGH"
    if "Strength" in g.inputs:                         # 4.5+ (sockets appear per glare type)
        for name, value in (("Threshold", threshold), ("Strength", strength), ("Size", size),
                            ("Streaks", streaks), ("Streaks Angle", angle), ("Fade", fade)):
            if name in g.inputs:
                g.inputs[name].default_value = value
    else:                                              # 4.2
        g.threshold = threshold
        g.mix = strength * 2.0 - 1.0
        g.size = int(round(6 + size * 3))
        g.streaks = streaks
        g.angle_offset = angle
        g.fade = fade
    return g


def setup_compositor(scene, director):
    if hasattr(scene, "compositing_node_group"):       # Blender 5.0+
        tree = bpy.data.node_groups.new(PREFIX + "Compositor", "CompositorNodeTree")
        tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        scene.compositing_node_group = tree
        out = tree.nodes.new("NodeGroupOutput")
        out_socket = out.inputs[0]
    else:
        scene.use_nodes = True
        tree = scene.node_tree
        tree.nodes.clear()
        out = tree.nodes.new("CompositorNodeComposite")
        out_socket = out.inputs["Image"]
    rl = tree.nodes.new("CompositorNodeRLayers")
    rl.scene = scene
    expo = tree.nodes.new("CompositorNodeExposure")
    ev_sock = [i for i in expo.inputs if i.name == "Exposure"][0]
    drive(ev_sock, "default_value", "e", {"e": director.path("exposure")})
    bloom = glare(tree, "BLOOM", 1.0, 0.62, 0.45)
    spikes = glare(tree, "STREAKS", 400.0, 0.5, 0.2, streaks=4, angle=math.radians(45.0), fade=0.92)
    lens = tree.nodes.new("CompositorNodeLensdist")
    lens.inputs["Dispersion"].default_value = 0.012
    try:
        lens.use_fit = False
    except AttributeError:
        pass
    viewer = tree.nodes.new("CompositorNodeViewer")
    tree.links.new(rl.outputs["Image"], expo.inputs["Image"])
    tree.links.new(expo.outputs["Image"], bloom.inputs["Image"])
    tree.links.new(bloom.outputs["Image"], spikes.inputs["Image"])
    tree.links.new(spikes.outputs["Image"], lens.inputs["Image"])
    tree.links.new(lens.outputs["Image"], out_socket)
    tree.links.new(lens.outputs["Image"], viewer.inputs["Image"])
    for i, node in enumerate((rl, expo, bloom, spikes, lens, out)):
        node.location = (i * 260, 0)
    viewer.location = (5 * 260, -220)
    scene.render.use_compositing = True


def setup_render(scene, cfg, q, path, director):
    set_engine(scene, cfg["ENGINE"])
    r = scene.render
    r.film_transparent = False
    r.use_motion_blur = q["mblur"]
    r.motion_blur_shutter = 0.4
    vs = scene.view_settings
    try:
        vs.view_transform = "AgX"
        vs.look = "AgX - Punchy"
    except TypeError:
        pass
    cyc = scene.cycles
    cyc.samples = q["cycles"]
    cyc.use_adaptive_sampling = True
    cyc.adaptive_threshold = 0.03
    cyc.use_denoising = False
    cyc.max_bounces = 0
    cyc.diffuse_bounces = cyc.glossy_bounces = cyc.transmission_bounces = cyc.volume_bounces = 0
    cyc.transparent_max_bounces = 64
    cyc.volume_step_rate = 1.0
    cyc.volume_max_steps = 2048
    cyc.caustics_reflective = cyc.caustics_refractive = False
    cyc.filter_width = 1.2
    if hasattr(cyc, "volume_biased"):
        cyc.volume_biased = True
    r.use_persistent_data = True
    if scene.render.engine == "CYCLES":
        backend = enable_gpu(scene)
        log(f"Cycles device: {backend}")
    ee = scene.eevee
    ee.taa_render_samples = q["eevee"]
    for attr, val in (("volumetric_tile_size", q["tile"]), ("volumetric_samples", q["vsamp"]),
                      ("volumetric_sample_distribution", 0.85), ("use_volumetric_shadows", False),
                      ("use_shadows", False), ("use_raytracing", False), ("volumetric_start", 0.05),
                      ("volumetric_end", 1200.0)):
        try:
            setattr(ee, attr, val)
        except (AttributeError, TypeError):
            pass
    if scene.render.engine != "CYCLES":
        focus = np.linalg.norm(path.pos - path.tgt, axis=1)
        frames = np.arange(1, len(focus) + 1)
        try:
            bake(scene, "eevee.volumetric_start", -1, frames, np.clip(focus * 0.004, 0.02, 20.0))
            bake(scene, "eevee.volumetric_end", -1, frames, np.clip(focus * 3.0, 60.0, 8000.0))
        except Exception:  # noqa: BLE001
            pass
    setup_compositor(scene, director)
    set_output(scene, cfg)


def output_dir(cfg):
    d = cfg["OUTPUT_DIR"] or os.path.join(script_dir(), "render")
    return bpy.path.abspath(d)


def set_output(scene, cfg):
    r = scene.render
    ims = r.image_settings
    out = output_dir(cfg)
    if cfg["OUTPUT"].upper() == "MP4":
        if hasattr(ims, "media_type"):
            ims.media_type = "VIDEO"
        ims.file_format = "FFMPEG"
        ff = r.ffmpeg
        ff.format = "MPEG4"
        ff.codec = "H264"
        ff.constant_rate_factor = "HIGH"
        ff.ffmpeg_preset = "GOOD"
        ff.audio_codec = "AAC"
        ff.audio_bitrate = 256
        ff.audio_channels = "STEREO"
        r.filepath = os.path.join(out, "endless_destiny_")
    else:
        if hasattr(ims, "media_type"):
            ims.media_type = "IMAGE"
        ims.file_format = "PNG"
        ims.color_mode = "RGB"
        ims.color_depth = "8"
        ims.compression = 15
        r.filepath = os.path.join(out, "frames", "ed_")
        r.use_overwrite = False
        r.use_placeholder = True


def assemble_video(cfg, song):
    """Join rendered PNG frames + the song into one .mp4, using Blender's video editor."""
    frames_dir = os.path.join(output_dir(cfg), "frames")
    files = sorted(f for f in os.listdir(frames_dir) if f.startswith("ed_") and f.endswith(".png")) if os.path.isdir(frames_dir) else []
    if not files:
        log(f"No frames found in {frames_dir}")
        return
    sc = bpy.data.scenes.new(PREFIX + "Assemble")
    se = sc.sequence_editor_create()
    strips = seq_strips(se)
    img = strips.new_image(PREFIX + "Frames", os.path.join(frames_dir, files[0]), 1, 1)
    for f in files[1:]:
        img.elements.append(f)
    if song.has_audio:
        strips.new_sound(PREFIX + "Song", song.audio_path, 2, 1)
    first = bpy.data.images.load(os.path.join(frames_dir, files[0]))
    w, h = first.size
    sc.render.resolution_x, sc.render.resolution_y = w - w % 2, h - h % 2   # H.264 needs even sizes
    sc.render.resolution_percentage = 100
    sc.render.fps = song.fps
    sc.frame_start, sc.frame_end = 1, len(files)
    cfg2 = dict(cfg)
    cfg2["OUTPUT"] = "MP4"
    set_output(sc, cfg2)
    sc.render.filepath = os.path.join(output_dir(cfg), "ENDLESS_DESTINY.mp4")
    sc.render.use_sequencer = True
    sc.render.use_compositing = False
    log(f"Writing {sc.render.filepath} ...")
    bpy.ops.render.render(animation=True, scene=sc.name)
    log("Video done.")


# ============================================================================
#  16. MAIN
# ============================================================================

def benchmark(scene, song, cfg):
    """Time three typical frames (a wide shot, the nebula, the black hole) and
    estimate how long the whole video takes on this computer."""
    picks = [("the galaxy reveal", "CHORUS1", 0.5), ("inside the nebula", "VERSE1", 0.5),
             ("the black hole", "BRIDGE", 0.8)]
    out = os.path.join(output_dir(cfg), "benchmark")
    os.makedirs(out, exist_ok=True)
    ims = scene.render.image_settings
    if hasattr(ims, "media_type"):
        ims.media_type = "IMAGE"
    ims.file_format = "PNG"
    times = []
    for label, key, frac in picks:
        f0, f1 = song.frames_of(key)
        f = int(f0 + frac * (f1 - f0)) + 1
        scene.frame_set(f)
        scene.render.filepath = os.path.join(out, f"bench_{key.lower()}.png")
        t0 = time.time()
        bpy.ops.render.render(write_still=True, scene=scene.name)
        dt = time.time() - t0
        times.append(dt)
        log(f"  {label:<18} frame {f:>5}: {dt:6.1f} s")
    avg = sum(times) / len(times)
    total_h = avg * song.n_frames / 3600.0
    log(f"About {avg:.0f} s per frame -> roughly {total_h:.1f} hours for all {song.n_frames} frames "
        f"({cfg['ENGINE']}, {cfg['QUALITY']}, {scene.render.resolution_x}x{scene.render.resolution_y} "
        f"at {scene.render.resolution_percentage}%).")
    set_output(scene, cfg)


def parse_args(cfg):
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opts = dict(render=False, stills=[], save=None, frames=None, video=False, benchmark=False)
    i = 0
    while i < len(argv):
        a = argv[i]
        nxt = argv[i + 1] if i + 1 < len(argv) else None
        if a == "--audio":
            cfg["AUDIO_PATH"] = nxt; i += 1
        elif a == "--engine":
            cfg["ENGINE"] = nxt.upper(); i += 1
        elif a == "--quality":
            cfg["QUALITY"] = nxt.upper(); i += 1
        elif a == "--fps":
            cfg["FPS"] = int(nxt); i += 1
        elif a == "--res":
            w, h = nxt.lower().split("x"); cfg["RESOLUTION"] = (int(w), int(h)); i += 1
        elif a == "--bpm":
            cfg["BPM"] = float(nxt); i += 1
        elif a == "--acts":
            cfg["ACT_STARTS"] = [float(v) for v in nxt.split(",")]; i += 1
        elif a == "--seed":
            cfg["SEED"] = int(nxt); i += 1
        elif a == "--seconds":
            cfg["SONG_SECONDS"] = float(nxt); i += 1
        elif a == "--output":
            cfg["OUTPUT_DIR"] = nxt; i += 1
        elif a == "--mp4":
            cfg["OUTPUT"] = "MP4"
        elif a == "--no-titles":
            cfg["SHOW_TITLES"] = False
        elif a == "--render":
            opts["render"] = True
        elif a == "--still":
            opts["stills"].append(float(nxt)); i += 1
        elif a == "--save":
            opts["save"] = nxt; i += 1
        elif a == "--frames":
            a0, a1 = nxt.split("-"); opts["frames"] = (int(a0), int(a1)); i += 1
        elif a == "--video":
            opts["video"] = True
        elif a == "--benchmark":
            opts["benchmark"] = True
        else:
            log(f"unknown option {a}")
        i += 1
    return opts


def main():
    cfg = dict(CONFIG)
    opts = parse_args(cfg)
    audio = find_audio(cfg["AUDIO_PATH"])
    log(f"Blender {bpy.app.version_string} | audio: {audio or 'none found'}")
    song = Song(cfg["FPS"], audio, cfg["BPM"], cfg["SONG_SECONDS"], cfg["ACT_STARTS"])
    song.report()
    if opts["video"]:
        assemble_video(cfg, song)
        return
    scene, path, kp = build(cfg, song)
    if bpy.context.screen is not None:
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.clip_start, space.clip_end = 0.01, 1e6
                        space.region_3d.view_perspective = "CAMERA"
                        space.shading.background_type = "VIEWPORT"
                        space.shading.background_color = (0.0, 0.0, 0.0)
    scene.frame_set(1)
    if opts["save"]:
        target = os.path.abspath(opts["save"])
        os.makedirs(os.path.dirname(target), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=target)
        log(f"Saved {opts['save']}")
    for t in opts["stills"]:
        f = max(1, min(song.n_frames, int(round(t * song.fps)) + 1))
        scene.frame_set(f)
        out = os.path.join(output_dir(cfg), f"still_{t:07.2f}s.png")
        scene.render.filepath = out
        ims = scene.render.image_settings
        if hasattr(ims, "media_type"):
            ims.media_type = "IMAGE"
        ims.file_format = "PNG"
        bpy.ops.render.render(write_still=True, scene=scene.name)
        log(f"Still written: {out}")
    if opts["stills"]:
        set_output(scene, cfg)
    if opts["benchmark"]:
        benchmark(scene, song, cfg)
    if opts["render"]:
        if opts["frames"]:
            scene.frame_start, scene.frame_end = opts["frames"]
        log(f"Rendering frames {scene.frame_start}-{scene.frame_end} to {scene.render.filepath}")
        bpy.ops.render.render(animation=True, scene=scene.name)
        log("Render finished.")
    log("Ready. Numpad 0 = camera view, Space = play, F12 = render a frame.")


if __name__ == "__main__":
    main()
