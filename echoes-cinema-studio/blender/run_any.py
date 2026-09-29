"""Render one shot (resumable): blender -b --factory-startup --python run_shot.py -- SHOT OUTDIR [first last] [spp]"""
import os
import sys
import time

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sets  # noqa: E402
import shots  # noqa: E402
import ocean  # noqa: E402,F401  (registers underwater shots)
import world  # noqa: E402,F401  (registers surface, shelf and space shots)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:]
    name, outdir = argv[0], argv[1]
    spec = shots.SHOTS[name]
    first = int(argv[2]) if len(argv) > 2 else 0
    last = int(argv[3]) if len(argv) > 3 else spec['frames'] - 1
    spp = int(argv[4]) if len(argv) > 4 else spec['spp']
    os.makedirs(outdir, exist_ok=True)
    sets.reset()
    w, h = spec['res']
    if os.environ.get('PREVIEW'):
        w, h, spp = w // 2, h // 2, 4
    sc = sets.setup_render(w, h, spp)
    ctx = shots.Ctx()
    spec['fn'](ctx, None, 0.0)
    # warm the fish rig from a little before the first frame so the fins have settled into their motion
    f = ctx.get('fish')
    t_first = first / shots.FPS
    if f is not None and f.loop_T is None:
        for k in range(24, 0, -1):
            f.pose(max(0.0, t_first - k / shots.FPS), dt=1 / shots.FPS)
    only = [int(x) for x in os.environ.get('ONLY', '').split(',') if x]
    step = int(os.environ.get('STEP', 1))   # slow shots: render every Nth frame, the compositor blends between
    for i in range(first, last + 1):
        if (only and i not in only) or (step > 1 and i % step and i != last):
            if f is not None:
                spec['fn'](ctx, i, i / shots.FPS)
            continue
        path = f'{outdir}/{name}_{i:04d}.png'
        t = i / shots.FPS
        spec['fn'](ctx, i, t)
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            continue
        sc.frame_current = i
        sc.cycles.seed = i
        sc.render.filepath = path
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f'SHOT {name} frame {i} {time.time() - t0:.1f}s', flush=True)


main()
