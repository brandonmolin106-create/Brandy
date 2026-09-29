"""Sets + render setup for 'The Fish in the Cup' thriller cut (Cycles, CPU-budgeted).

Every shot script calls  setup_render()  then builds one of the sets and a camera, then drives the animation per frame.
"""
import math
import os

import bpy
import mathutils

import props

HDRI = '/opt/assets/hdri'
TEX = '/opt/assets/betta'


def reset():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
        for x in list(coll):
            if x.users == 0:
                coll.remove(x)


def setup_render(w=540, h=960, spp=8, threads=4, adapt=0.06, trans=int(os.environ.get('TRB', 5)), transp=10, view='AgX', look='AgX - Punchy',
                 exposure=0.0, denoise=True):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'CPU'
    cy.samples = spp
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = adapt
    cy.use_denoising = denoise
    cy.denoiser = 'OPENIMAGEDENOISE'
    cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    cy.denoising_prefilter = 'FAST'
    cy.max_bounces = trans + 2
    cy.diffuse_bounces = 2
    cy.glossy_bounces = 2
    cy.transmission_bounces = trans
    cy.transparent_max_bounces = transp
    cy.volume_bounces = 0
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.blur_glossy = 0.8
    cy.sample_clamp_indirect = 4.0
    cy.seed = 0
    cy.use_animated_seed = True
    sc.render.threads_mode = 'FIXED'
    sc.render.threads = threads
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.fps = 24
    sc.render.use_persistent_data = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '16'
    sc.render.image_settings.color_mode = 'RGB'
    vs = sc.view_settings
    vs.view_transform = view
    vs.look = look
    vs.exposure = exposure
    return sc


def camera(loc, target, lens=85, fstop=4.0, focus=None, sensor=36, roll=0.0, name='cam'):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.sensor_fit = 'HORIZONTAL'
    cd.dof.use_dof = fstop is not None
    if fstop:
        cd.dof.aperture_fstop = fstop
        cd.dof.aperture_blades = 7
        cd.dof.aperture_rotation = 0.3
    cam = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(cam)
    aim(cam, loc, target, roll)
    d = (mathutils.Vector(target) - mathutils.Vector(loc)).length
    cd.dof.focus_distance = focus if focus else d
    bpy.context.scene.camera = cam
    cd.clip_start = 0.003
    cd.clip_end = 5000
    return cam


def aim(cam, loc, target, roll=0.0, focus=None):
    cam.location = loc
    d = mathutils.Vector(target) - mathutils.Vector(loc)
    q = d.to_track_quat('-Z', 'Y')
    if roll:
        q = q @ mathutils.Quaternion((0, 0, 1), roll)
    cam.rotation_euler = q.to_euler()
    if focus is not None:
        cam.data.dof.focus_distance = focus
    elif cam.data.dof.use_dof:
        cam.data.dof.focus_distance = d.length


def only_camera(ob):
    """Visible to the camera only (fake volumetrics etc.)."""
    ob.visible_shadow = False
    ob.visible_diffuse = False
    ob.visible_glossy = False
    ob.visible_transmission = False
    ob.visible_volume_scatter = False


def beam_material(color=(1.0, 0.78, 0.5), strength=0.35):
    """Fake volumetric light cone: glows toward its axis (facing ratio), with drifting haze noise."""
    m = bpy.data.materials.new('beam')
    m.use_nodes = True
    nt = m.node_tree
    for x in list(nt.nodes):
        nt.nodes.remove(x)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    lw = nt.nodes.new('ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.5
    inv = nt.nodes.new('ShaderNodeMath')
    inv.operation = 'SUBTRACT'
    inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs['Facing'], inv.inputs[1])
    pw = nt.nodes.new('ShaderNodeMath')
    pw.operation = 'POWER'
    pw.inputs[1].default_value = 2.2
    nt.links.new(inv.outputs['Value'], pw.inputs[0])
    tc = nt.nodes.new('ShaderNodeTexCoord')
    noi = nt.nodes.new('ShaderNodeTexNoise')
    noi.inputs['Scale'].default_value = 7.0
    noi.inputs['Detail'].default_value = 2.0
    nt.links.new(tc.outputs['Object'], noi.inputs['Vector'])
    # vertical falloff: brightest near the lamp (object z = 0 at the apex, -1 at the base)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    fall = nt.nodes.new('ShaderNodeMapRange')
    fall.inputs['From Min'].default_value = 0.0
    fall.inputs['From Max'].default_value = 1.0
    fall.inputs['To Min'].default_value = 0.35
    fall.inputs['To Max'].default_value = 1.0
    nt.links.new(sep.outputs['Z'], fall.inputs['Value'])
    m1 = nt.nodes.new('ShaderNodeMath')
    m1.operation = 'MULTIPLY'
    nt.links.new(pw.outputs['Value'], m1.inputs[0])
    nt.links.new(noi.outputs['Fac'], m1.inputs[1])
    m2 = nt.nodes.new('ShaderNodeMath')
    m2.operation = 'MULTIPLY'
    nt.links.new(m1.outputs['Value'], m2.inputs[0])
    nt.links.new(fall.outputs['Result'], m2.inputs[1])
    m3 = nt.nodes.new('ShaderNodeMath')
    m3.operation = 'MULTIPLY'
    m3.inputs[1].default_value = strength
    nt.links.new(m2.outputs['Value'], m3.inputs[0])
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*color, 1)
    nt.links.new(m3.outputs['Value'], em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    add = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(em.outputs['Emission'], add.inputs[0])
    nt.links.new(tr.outputs['BSDF'], add.inputs[1])
    nt.links.new(add.outputs['Shader'], out.inputs['Surface'])
    return m


def light_cone(apex, length, angle_deg, mat, name='beam'):
    r = length * math.tan(math.radians(angle_deg) / 2)
    verts, faces, _ = props.lathe([(0.0, 0.0), (r * 0.02, -0.001), (r, -length)], 64)
    me = props.make_mesh(name, verts, faces)
    ob = props.link_obj(name, me, mat)
    ob.location = apex
    only_camera(ob)
    return ob


def black_world():
    w = bpy.context.scene.world or bpy.data.worlds.new('World')
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
    return w


class Room:
    """Dark interrogation room: scarred wooden table, one hard pendant lamp (with haze beam), moonlight through
    venetian blinds raking the back wall, near-black surroundings."""

    def __init__(self, lamp_power=50.0, moon=0.6, beam=0.35, blinds_tilt=-0.55, back_light=0.0, hdri=0.0):
        self.table = props.table(size=(1.8, 1.0))
        self.wall = props.plane('back_wall', 5.0, 3.0, (0, 1.1, 1.0), (math.radians(90), 0, 0),
                                props.plaster_material('wall', (0.03, 0.032, 0.035)))
        self.side = props.plane('side_wall', 5.0, 3.0, (-1.6, 0, 1.0), (math.radians(90), 0, math.radians(90)),
                                props.plaster_material('wall2', (0.025, 0.027, 0.03)))
        self.blinds = props.blinds(width=1.3, height=1.4, slats=32, tilt=blinds_tilt, loc=(1.3, 0.35, 0.75),
                                   rot=(0, 0, math.radians(90)))
        ld = bpy.data.lights.new('moon', 'SUN')
        ld.energy = moon
        ld.color = (0.5, 0.66, 1.0)
        ld.angle = math.radians(0.4)
        self.moon = bpy.data.objects.new('moon', ld)
        bpy.context.scene.collection.objects.link(self.moon)
        self.moon.rotation_euler = mathutils.Vector((-1.0, 0.55, -0.45)).to_track_quat('-Z', 'Y').to_euler()
        self.shade, self.bulb, self.lamp = props.pendant_lamp(loc=(0.0, 0.02, 0.58), power=lamp_power, cone_deg=38)
        self.lamp.data.spot_blend = 0.35
        self.lamp.data.shadow_soft_size = 0.012
        self.beam = light_cone((0.0, 0.02, 0.555), 0.56, 34, beam_material(strength=beam)) if beam > 0 else None
        if back_light > 0:
            props.area_light('back', (0.25, 0.6, 0.25), (math.radians(-75), 0, math.radians(165)), 0.4, back_light,
                             (0.55, 0.72, 1.0))
        if hdri > 0:
            props.world_hdri(f'{HDRI}/unfinished_office_night_2k.hdr', strength=hdri, rot_z=1.2, bg_strength=0.0)
        else:
            black_world()
