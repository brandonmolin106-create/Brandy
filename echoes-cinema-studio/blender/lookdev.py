"""Look-dev / benchmark: the hero 'fish in the cup' interrogation-room set.

blender -b --factory-startup --python lookdev.py -- OUT.png WIDTH HEIGHT SAMPLES [t]
"""
import math
import os
import sys
import time

import bpy
import mathutils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props  # noqa: E402
from betta import Betta  # noqa: E402

TEX = '/opt/assets/betta'
HDRI = '/opt/assets/hdri'


def reset():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)


def setup_render(w, h, samples, threads=4):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'CPU'
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = float(os.environ.get('ADAPT', 0.04))
    cy.use_denoising = os.environ.get('DENOISE', '1') == '1'
    cy.denoiser = 'OPENIMAGEDENOISE'
    cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    cy.denoising_prefilter = 'ACCURATE'
    E = os.environ.get
    cy.max_bounces = int(E('MAXB', 10))
    cy.diffuse_bounces = int(E('DIFB', 2))
    cy.glossy_bounces = int(E('GLOB', 3))
    cy.transmission_bounces = int(E('TRB', 8))
    cy.transparent_max_bounces = int(E('TPB', 12))
    cy.volume_bounces = 0
    cy.caustics_reflective = False
    cy.caustics_refractive = E('CAUST', '0') == '1'
    cy.denoising_prefilter = E('PREF', 'ACCURATE')
    cy.blur_glossy = 0.6
    cy.sample_clamp_indirect = 6.0
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
    vs.view_transform = os.environ.get('VIEW', 'Khronos PBR Neutral')
    vs.look = 'None'
    vs.exposure = 0.0
    sc.render.film_transparent = False


def camera(loc, target, lens=85, fstop=2.8, focus=None, sensor=36):
    cd = bpy.data.cameras.new('cam')
    cd.lens = lens
    cd.sensor_width = sensor
    cd.sensor_fit = 'HORIZONTAL'
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    cd.dof.aperture_blades = 7
    cd.dof.aperture_rotation = 0.3
    cam = bpy.data.objects.new('cam', cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    d = mathutils.Vector(target) - mathutils.Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cd.dof.focus_distance = focus if focus else d.length
    bpy.context.scene.camera = cam
    cd.clip_start = 0.005
    return cam


def build_room():
    tb = props.table(size=(1.8, 1.0))
    wall = props.plane('back_wall', 4.0, 3.0, (0, 0.9, 1.0), (math.radians(90), 0, 0), props.plaster_material())
    side = props.plane('side_wall', 4.0, 3.0, (-1.4, 0, 1.0), (math.radians(90), 0, math.radians(90)),
                       props.plaster_material('wall2', (0.04, 0.042, 0.046)))
    # window with blinds on the right: cold moonlight through slats
    props.blinds(width=1.2, height=1.3, slats=30, tilt=0.5, loc=(1.25, 0.2, 0.75), rot=(0, 0, math.radians(90)))
    # moonlight: a sun lamp raking through the blinds -> crisp noir light bars
    ld = bpy.data.lights.new('moon', 'SUN')
    ld.energy = float(os.environ.get('MOON', 2.5))
    ld.color = (0.55, 0.7, 1.0)
    ld.angle = math.radians(0.6)
    mo = bpy.data.objects.new('moon', ld)
    bpy.context.scene.collection.objects.link(mo)
    mo.rotation_euler = mathutils.Vector((-1.0, 0.35, -0.55)).to_track_quat('-Z', 'Y').to_euler()
    # cold back light behind the cup: glass edges + backlit fins
    props.area_light('back', (0.35, 0.75, 0.35), (math.radians(-70), 0, math.radians(160)), 0.5,
                     float(os.environ.get('BACK', 60)), (0.6, 0.75, 1.0))
    shade, bulb, lamp = props.pendant_lamp(loc=(-0.02, -0.02, 0.62), power=float(os.environ.get('LAMP', 160)))
    props.world_hdri(f'{HDRI}/unfinished_office_night_2k.hdr', strength=0.25, rot_z=1.2, bg_strength=0.05)
    return tb


def main():
    argv = sys.argv[sys.argv.index('--') + 1:]
    out, w, h, spp = argv[0], int(argv[1]), int(argv[2]), int(argv[3])
    t = float(argv[4]) if len(argv) > 4 else 1.3
    reset()
    setup_render(w, h, spp)
    build_room()
    cup = props.Cup()
    fish = Betta(TEX)
    fish.root.scale = (0.82, 0.82, 0.82)
    fish.root.location = (0.004, 0.0, cup.base + 0.043)
    fish.root.rotation_euler = (0, math.radians(-4), math.radians(-28))
    for k in range(int(t * 24) + 1):
        fish.pose(k / 24.0, swim=0.3, freq=1.0, flare=0.75, turn=0.25, dt=1 / 24.0)
    cup.ripple(t)
    d = float(os.environ.get('CAMD', 0.23))
    camera((0.0, -d, 0.068), (0.0, 0.0, 0.056), lens=85, fstop=float(os.environ.get('FSTOP', 2.8)), focus=d - 0.004)
    if os.environ.get('BORDER'):
        x0, x1, y0, y1 = [float(v) for v in os.environ['BORDER'].split(',')]
        sc = bpy.context.scene
        sc.render.use_border = True
        sc.render.use_crop_to_border = False
        sc.render.border_min_x, sc.render.border_max_x, sc.render.border_min_y, sc.render.border_max_y = x0, x1, y0, y1
    nfr = int(os.environ.get('NFR', 1))
    for k in range(nfr):
        if k:
            fish.pose(t + k / 24.0, swim=0.3, freq=1.0, flare=0.75, turn=0.25, dt=1 / 24.0)
            cup.ripple(t + k / 24.0)
        t0 = time.time()
        bpy.context.scene.render.filepath = out if k == 0 else out.replace('.png', f'_{k}.png')
        bpy.ops.render.render(write_still=True)
        print(f'RENDER_TIME {time.time() - t0:.1f}s  {w}x{h} spp={spp} frame {k}', flush=True)


if __name__ == '__main__':
    main()
