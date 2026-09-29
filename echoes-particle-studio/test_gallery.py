"""Look-dev gallery of the story elements."""
import sys
import time

import cv2
import numpy as np

import render_core as rc
from director import Compositor, Frame
from elements import Dust, Galaxy, Nebula, ParticleText, Starfield, _cat
from elements2 import Cup, Fish, Ocean, Person, Planet, Sun, Tree, circle_path, trail_ring

OUT = sys.argv[1]
comp = Compositor()
stars = Starfield()
t = 3.0
tiles = []


def shot(F):
    t0 = time.time()
    img = comp.compose(F, None, 0)
    print('shot', round(time.time() - t0, 3), flush=True)
    tiles.append(cv2.resize(img, (360, 640), interpolation=cv2.INTER_AREA))


fish = Fish()
# 1 fish close-up
cam = rc.Camera(eye=(0.15, 0.08, 0.55), target=(0, 0, 0), fov=35, dof=8, focus=0.56)
shot(Frame(cam, bg=_cat(stars.at(t), fish.at(t, scale=0.4, heading=(1, 0, 0.2))), bloom=dict(threshold=0.9)))

# 2 cup with fish
cup = Cup()
fp, fd = circle_path(t, center=(0, 0.4, 0), radius=0.15, omega=1.5)
cam = rc.Camera(eye=(0.0, 0.75, 2.2), target=(0, 0.42, 0), fov=35, dof=5, focus=2.2)
shot(Frame(cam, bg=_cat(stars.at(t), cup.at(t, cam_pos=cam.eye), fish.at(t, pos=fp, heading=fd, scale=0.22),
                        trail_ring((0, 0.4, 0), 0.15, t, 1.5, gain=0.5)), bloom=dict(threshold=0.9)))

# 3 ocean vista
oc = Ocean()
cam = rc.Camera(eye=(0, 4.0, 12), target=(0, 2.0, -60), fov=50)
shot(Frame(cam, bg=_cat(stars.at(t), oc.at(t, cam_pos=cam.eye, light_dir=(0, 0.15, -1))), fog=0.004,
           fog_color=(0.02, 0.05, 0.1)))

# 4 people around cup
pp = Person()
cam = rc.Camera(eye=(0, 1.2, 6.5), target=(0, 1.0, 0), fov=40)
parts = [stars.at(t), cup.at(t, T=(0, 0, 1.5), scale=0.5, cam_pos=cam.eye)]
for k, x in enumerate([-1.8, 0.2, 2.0]):
    parts.append(pp.at(t + k, pos=(x, 0, -0.5 - k * 0.3), yaw=1.57 if k != 1 else -1.57, cam_pos=cam.eye))
shot(Frame(cam, bg=_cat(*parts)))

# 5 sun + tree
sun = Sun()
tree = Tree()
cam = rc.Camera(eye=(0, 2.0, 9), target=(0, 2.6, 0), fov=45)
shot(Frame(cam, bg=_cat(stars.at(t), sun.at(t, center=(2, 6, -40), radius=3), tree.at(t, grow=0.9, pos=(0, 0, 0))),
           rays=((cam.project(np.array([[2, 6, -40]]))[0][0]), 0.8, 0.8)))

# 6 planet + galaxy
pl = Planet()
gx = Galaxy()
cam = rc.Camera(eye=(0, 1.0, 4.5), target=(0, 0, 0), fov=40)
shot(Frame(cam, bg=_cat(stars.at(t), gx.at(t, center=(-30, 25, -120)), pl.at(t, cam_pos=cam.eye))))

# 7 particle text
txt = ParticleText('JUST GO FOR IT', height=0.5)
cam = rc.Camera(eye=(0, 0, 4), target=(0, 0, 0), fov=40)
shot(Frame(cam, bg=_cat(stars.at(t), txt.at(t, form=1.0))))

# 8 nebula
neb = Nebula(center=(0, 0, -100), extent=(80, 60, 40), bright=0.0015)
cam = rc.Camera(eye=(0, 0, 0), target=(0, 0, -100), fov=50)
shot(Frame(cam, bg=_cat(stars.at(t), neb.at(t))))

row1 = np.concatenate(tiles[:4], 1)
row2 = np.concatenate(tiles[4:8], 1)
cv2.imwrite(OUT, np.concatenate([row1, row2], 0)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
