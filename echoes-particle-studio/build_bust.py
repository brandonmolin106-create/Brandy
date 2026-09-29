"""Build Brandon's 3D particle bust from one clean frontal frame.

usage: python build_bust.py VIDEO FRAME_INDEX OUT.npz [--debug DIR]

Pipeline: MediaPipe face landmarks + selfie multiclass segmentation +
Depth Anything V2 (relative depth, calibrated against the landmark mesh
depth) -> jittered particles carrying colour, region class and rig data
(face-mesh barycentrics for expression retargeting, head weight for
rigid head motion).
"""
import argparse
import os
import subprocess

import cv2
import mediapipe as mp
import numpy as np
import torch
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision
from PIL import Image
from scipy.spatial import Delaunay, cKDTree
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

INNER_UP = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308]
INNER_LO = [308, 324, 318, 402, 317, 14, 87, 178, 88, 95, 78]
MOUTH_RING = set(INNER_UP + INNER_LO)
FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377,
             152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]


def grab_frame(video, idx):
    """Decode sequentially (same numbering as capture.py) and return frame idx."""
    w, h = [int(x) for x in subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
        '-of', 'csv=p=0', video]).decode().strip().split(',')]
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', video, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         stdout=subprocess.PIPE)
    n = w * h * 3
    for i in range(idx + 1):
        buf = p.stdout.read(n)
    p.kill()
    return np.frombuffer(buf, np.uint8).reshape(h, w, 3).copy()


def landmarks(rgb):
    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=mpt.BaseOptions(model_asset_path='/opt/models/face_landmarker.task'),
        output_face_blendshapes=True, num_faces=1))
    res = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
    h, w = rgb.shape[:2]
    return np.array([[p.x * w, p.y * h, p.z * w] for p in res.face_landmarks[0]], np.float64)


def segment(rgb):
    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=mpt.BaseOptions(model_asset_path='/opt/models/selfie_multiclass.tflite'),
        output_confidence_masks=True, output_category_mask=True))
    res = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
    conf = np.stack([np.squeeze(m.numpy_view()).astype(np.float32) for m in res.confidence_masks], -1)
    return conf  # (h, w, 6): bg, hair, body-skin, face-skin, clothes, others


def depth(rgb):
    name = 'depth-anything/Depth-Anything-V2-Base-hf'
    proc = AutoImageProcessor.from_pretrained(name)
    model = AutoModelForDepthEstimation.from_pretrained(name).eval()
    # run at higher internal resolution for detail
    inp = proc(images=Image.fromarray(rgb), return_tensors='pt', size={'height': 924, 'width': 518},
               keep_aspect_ratio=True)
    with torch.no_grad():
        pred = model(**inp).predicted_depth
    d = torch.nn.functional.interpolate(pred[None], size=rgb.shape[:2], mode='bicubic', align_corners=False)[0, 0]
    return d.numpy().astype(np.float64)


def srgb_to_lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def bilinear(img, x, y):
    """Bilinear sample img (h, w[, c]) at float pixel coords -> (n[, c])."""
    img = img.astype(np.float64)
    h, w = img.shape[:2]
    x = np.clip(np.asarray(x, np.float64), 0, w - 1.001)
    y = np.clip(np.asarray(y, np.float64), 0, h - 1.001)
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx = x - x0
    fy = y - y0
    if img.ndim == 3:
        fx = fx[:, None]
        fy = fy[:, None]
    a = img[y0, x0] * (1 - fx) + img[y0, x0 + 1] * fx
    b = img[y0 + 1, x0] * (1 - fx) + img[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('frame', type=int)
    ap.add_argument('out')
    ap.add_argument('--debug', default=None)
    ap.add_argument('--density', type=float, default=1.6)
    ap.add_argument('--cam-dist', type=float, default=0.38)
    ap.add_argument('--size', type=float, default=0.62)
    a = ap.parse_args()

    rgb = grab_frame(a.video, a.frame)
    h, w = rgb.shape[:2]
    lm = landmarks(rgb)
    conf = segment(rgb)
    disp = depth(rgb)

    person = 1.0 - conf[..., 0]
    person = cv2.GaussianBlur(person, (0, 0), 0.8)
    cls = conf[..., 1:5].argmax(-1) + 1  # 1 hair 2 body 3 face 4 clothes

    # scale: face width (234 <-> 454) ~ 0.15 m
    face_w_px = np.linalg.norm(lm[234, :2] - lm[454, :2])
    mpp = 0.15 / face_w_px

    # calibrate disparity -> mediapipe z (px units) on landmark positions
    ld = bilinear(disp[..., None], lm[:, 0], lm[:, 1])[:, 0]
    A = np.stack([ld, np.ones_like(ld)], -1)
    coef, *_ = np.linalg.lstsq(A, lm[:, 2], rcond=None)
    zpx = disp * coef[0] + coef[1]  # mediapipe-z-like (negative = toward camera)
    # keep depth sane outside the face: fill the background-contaminated edge with person depth
    core = (person > 0.6).astype(np.uint8)
    zf = zpx.astype(np.float32).copy()
    zmin, zmax = np.percentile(zpx[core > 0], [1, 99])
    zf = np.clip(zf, zmin, zmax + 0.25 * (zmax - zmin))
    zf[core == 0] = 0
    dist, (iy, ix) = None, (None, None)
    from scipy import ndimage
    _, inds = ndimage.distance_transform_edt(core == 0, return_indices=True)
    zf = zf[inds[0], inds[1]]
    zf_fine = cv2.GaussianBlur(zf, (0, 0), 1.2)
    zf_coarse = cv2.GaussianBlur(zf, (0, 0), 7.0)
    hair_m = (cls == 1).astype(np.float32) * (person > 0.3)
    near_hair = cv2.GaussianBlur(cv2.dilate(hair_m, np.ones((15, 15), np.uint8)), (0, 0), 6.0)
    wblend = np.clip(near_hair * 1.3, 0, 1)
    face_core = cv2.erode(((cls == 3) & (person > 0.5)).astype(np.uint8), np.ones((25, 25), np.uint8))
    wblend *= 1.0 - cv2.GaussianBlur(face_core.astype(np.float32), (0, 0), 6.0)
    zf = zf_fine * (1 - wblend) + zf_coarse * wblend

    # head centre / pivot
    cx, cy = lm[168, 0], lm[168, 1]
    chin_y = lm[152, 1]

    # ---- particles
    rng = np.random.default_rng(3)
    ys, xs = np.nonzero(person > 0.04)
    alpha = person[ys, xs]
    c = cls[ys, xs]
    dens = np.where(c == 3, a.density * 1.25, np.where(c == 1, a.density, a.density * 0.8)) * alpha
    k = np.floor(dens).astype(int) + (rng.random(len(dens)) < (dens - np.floor(dens)))
    rep = np.repeat(np.arange(len(xs)), k)
    px = xs[rep] + rng.uniform(-0.5, 0.5, len(rep))
    py = ys[rep] + rng.uniform(-0.5, 0.5, len(rep))
    col = srgb_to_lin(bilinear(rgb, px, py))
    z = bilinear(zf[..., None], px, py)[:, 0]
    pcls = cls[np.clip(py.round().astype(int), 0, h - 1), np.clip(px.round().astype(int), 0, w - 1)]
    palpha = bilinear(person[..., None], px, py)[:, 0]

    D = a.cam_dist

    def backproject(u, v, zz):
        zw = -(zz - lm[168, 2]) * mpp  # toward camera = positive
        k = (D - zw) / D
        return np.stack([(u - cx) * mpp * k, -(v - cy) * mpp * k, zw], -1)

    X = backproject(px, py, z)
    LW = backproject(lm[:, 0], lm[:, 1], lm[:, 2])

    # ---- rig: face mesh barycentrics (mouth hole removed)
    tri = Delaunay(lm[:, :2])
    simp = tri.simplices
    keep = np.array([not all(v in MOUTH_RING for v in s) for s in simp])
    # also drop sliver triangles spanning the lips (two ring verts from different lips + closed mouth)
    up, lo = set(INNER_UP[1:-1]), set(INNER_LO[1:-1])
    keep &= np.array([not (len(set(s) & up) >= 1 and len(set(s) & lo) >= 1 and len(set(s) & MOUTH_RING) == 3)
                      for s in simp])
    simp = simp[keep]
    tri2 = Delaunay(lm[:, :2])  # for point location we re-run on kept simplices manually
    P2 = np.stack([px, py], -1)
    # locate: barycentric against every kept triangle is too slow; use the full Delaunay then remap
    loc = tri2.find_simplex(P2)
    kept_idx = -np.ones(len(tri2.simplices), int)
    kept_idx[np.nonzero(keep)[0]] = np.arange(keep.sum())
    tri_id = np.where(loc >= 0, kept_idx[np.maximum(loc, 0)], -1)
    # points inside removed (mouth) triangles -> nearest kept triangle by centroid
    cent = lm[simp][:, :, :2].mean(1)
    ctree = cKDTree(cent)
    bad = (loc >= 0) & (tri_id < 0)
    if bad.any():
        _, nn = ctree.query(P2[bad])
        tri_id[bad] = nn
    inside = tri_id >= 0
    bary = np.zeros((len(px), 3))
    off = np.zeros((len(px), 3))
    if inside.any():
        T = lm[simp[tri_id[inside]]][:, :, :2]
        v0 = T[:, 1] - T[:, 0]
        v1 = T[:, 2] - T[:, 0]
        v2 = P2[inside] - T[:, 0]
        d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1)
        d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
        den = d00 * d11 - d01 * d01
        bv = (d11 * d20 - d01 * d21) / den
        bw = (d00 * d21 - d01 * d20) / den
        bu = 1 - bv - bw
        bary[inside] = np.stack([bu, bv, bw], -1)
        interp = (LW[simp[tri_id[inside]]] * bary[inside][:, :, None]).sum(1)
        off[inside] = X[inside] - interp

    # outside-mesh head particles: IDW on the face-oval landmarks
    oval = np.array(FACE_OVAL)
    otree = cKDTree(lm[oval, :2])
    dd, ii = otree.query(P2, k=4)
    wts = 1.0 / np.maximum(dd, 1.0) ** 2
    wts /= wts.sum(1, keepdims=True)
    face_scale = face_w_px
    fall = np.exp(-(dd[:, 0] / (0.18 * face_scale)) ** 2)  # influence fades away from the face

    # head weight: 1 above the jaw, ramps to 0 down the neck
    yw = (py - chin_y) / face_w_px
    head_w = np.clip(1.0 - (yw - 0.05) / 0.35, 0.0, 1.0)
    head_w = head_w * head_w * (3 - 2 * head_w)
    head_w[pcls == 1] = np.maximum(head_w[pcls == 1], np.clip(1.2 - yw[pcls == 1], 0, 1))

    pivot = np.array([0.0, (-(lm[152, 1] - cy) * mpp) - 0.06, -0.02])
    size = np.full(len(px), a.size * mpp) * np.where(pcls == 1, 1.05, 1.0)

    np.savez_compressed(
        a.out, pos=X.astype(np.float32), col=col.astype(np.float32), size=size.astype(np.float32),
        cls=pcls.astype(np.int8), alpha=palpha.astype(np.float32), tri=tri_id.astype(np.int32),
        bary=bary.astype(np.float32), off=off.astype(np.float32), idw_i=oval[ii].astype(np.int32),
        idw_w=wts.astype(np.float32), idw_fall=fall.astype(np.float32), head_w=head_w.astype(np.float32),
        lm_world=LW.astype(np.float32), lm_px=lm.astype(np.float32), simplices=simp.astype(np.int32),
        pivot=pivot.astype(np.float32), mpp=mpp, face_w_px=face_w_px, img=rgb, frame=a.frame)
    print('particles', len(px), 'face-mesh', int(inside.sum()), 'mpp', mpp, 'z-range m',
          float(X[:, 2].min()), float(X[:, 2].max()))

    if a.debug:
        os.makedirs(a.debug, exist_ok=True)
        cv2.imwrite(os.path.join(a.debug, 'frame.png'), rgb[..., ::-1])
        dv = (zf - zf.min()) / (np.ptp(zf) + 1e-9)
        cv2.imwrite(os.path.join(a.debug, 'depth.png'), (255 * (1 - dv) * (person > 0.05)).astype(np.uint8))
        cv2.imwrite(os.path.join(a.debug, 'mask.png'), (255 * person).astype(np.uint8))
        segv = np.array([[0, 0, 0], [40, 40, 200], [80, 200, 80], [200, 160, 120], [200, 80, 200]], np.uint8)[cls]
        cv2.imwrite(os.path.join(a.debug, 'classes.png'), (segv * (person > 0.3)[..., None]).astype(np.uint8))
        dbg = rgb[..., ::-1].copy()
        for s in simp:
            pts = lm[s, :2].astype(np.int32)
            cv2.polylines(dbg, [pts], True, (0, 255, 0), 1)
        cv2.imwrite(os.path.join(a.debug, 'mesh.png'), dbg)


if __name__ == '__main__':
    main()
