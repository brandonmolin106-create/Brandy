"""Look-dev render of the posed particle avatar in a simple cosmic set."""
import sys
import time

import cv2
import numpy as np

import render_core as rc
from avatar import Bust, Performance
from director import Compositor, Frame
from elements import Dust, Nebula, Starfield

WORK = sys.argv[1]
frames = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else [300]
looks = sys.argv[3].split(',') if len(sys.argv) > 3 else ['starlight']
KEEP = [float(k) for k in sys.argv[4].split(',')] if len(sys.argv) > 4 else [1.0]

bust = Bust(f'{WORK}/bust.npz')
perf = Performance(f'{WORK}/perf_capture.npz', bust)
stars = Starfield()
neb = Nebula(center=(0, 5, -120), extent=(140, 90, 60), bright=0.0012, thresh=0.12)
dust = Dust()
comp = Compositor()
outs = []
for li, fi in enumerate(frames):
    look = looks[li % len(looks)]
    t = fi / 30.0
    E, R, lean, sway, jaw = perf.at(fi)
    base = bust.look(look, gain=1.5)
    t0 = time.time()
    pos, col, size, hw = bust.pose(E, R, lean, sway, t=t, energy=0.3, col=base, fx=dict(keep=KEEP[li % len(KEEP)], point_size=0.6, aura=0.015, aura_frac=0.05))
    g = bust.eye_glints(E, R, lean, sway)
    pos, col, size = np.concatenate([pos, g[0]]), np.concatenate([col, g[1]]), np.concatenate([size, g[2]])
    t1 = time.time()
    cam = rc.Camera(eye=(0.1, 0.03, 0.66), target=(0.0, -0.01, 0.0), fov=36, dof=6.0, focus=0.64)
    bgp = [stars.at(t), neb.at(t)]
    bg = (np.concatenate([b[0] for b in bgp]), np.concatenate([b[1] for b in bgp]), np.concatenate([b[2] for b in bgp]))
    F = Frame(cam, bg=bg, fg=dust.at(t, center=(0, 0, 0.3), cam_pos=cam.eye, gain=0.5), rays=((560, 520), 0.5, 0.7), bg_dof=2.0, occl=0.96,
              grade=dict(exposure=1.0))
    out = comp.compose(F, (pos, col, size), fi)
    t2 = time.time()
    print(f'frame {fi} look {look}: pose {t1-t0:.3f}s compose {t2-t1:.3f}s jaw {jaw:.2f}', flush=True)
    outs.append(cv2.resize(out, (540, 960), interpolation=cv2.INTER_AREA))
cv2.imwrite(f'{WORK}/frames/avatar_test.jpg', np.concatenate(outs, 1)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
