"""Vectorise-ish the Echoes in the Dark emblem into high-res fields the renderer animates.

Outputs (assets/cache/):
  alpha.npy  - anti-aliased emblem coverage, perfectly mirrored (float16)
  dist.npy   - geodesic distance from the two top tips, through the strokes, 0..1 (float16)
  edt.npy    - distance to the stroke edge, normalised per stroke (float16)
  sdf.npy    - signed distance to the stroke edge in mask pixels (crisp edges at any zoom)
  grain.npy  - fine multi-octave "brushed metal" detail texture in mask space
  meta.json  - star position, emblem bbox, scale, growth-front centroid path
"""
import json
import os

import cv2
import numpy as np
from scipy.ndimage import distance_transform_edt
from skimage.graph import MCP_Geometric

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "assets", "logo-source.jpg")
OUT = os.path.join(HERE, "assets", "cache")
S = 8  # upscale factor from the 768px source

# Crop around the emblem in source pixels (text and background excluded).
X0, Y0, X1, Y1 = 200, 140, 570, 520
STAR_SRC = (383.0, 209.5)  # centre of the gold star in the source


def main():
    os.makedirs(OUT, exist_ok=True)
    g = cv2.imread(SRC, cv2.IMREAD_GRAYSCALE).astype(np.float32)
    crop = g[Y0:Y1, X0:X1]
    # Paint the gold star out so only black strokes remain.
    crop = crop.copy()
    sx, sy = STAR_SRC[0] - X0, STAR_SRC[1] - Y0
    cv2.circle(crop, (int(sx), int(sy)), 20, 255.0, -1)

    up = cv2.resize(crop, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
    up = cv2.GaussianBlur(up, (0, 0), S * 1.1)  # irons out JPEG wobble in the source

    # Find the axis of symmetry from the two halves and mirror the cleaner left half.
    dark = up < 128
    cols = np.where(dark.any(0))[0]
    axis = (cols.min() + cols.max()) / 2.0
    h, w = up.shape
    xs = np.arange(w, dtype=np.float32)
    mirror_x = (2 * axis - xs).astype(np.float32)
    mapx = np.where(xs[None, :] > axis, mirror_x[None, :], xs[None, :]).repeat(h, 0)
    mapy = np.arange(h, dtype=np.float32)[:, None].repeat(w, 1)
    sym = cv2.remap(up, mapx.astype(np.float32), mapy, cv2.INTER_LINEAR, borderValue=255)

    alpha = np.clip((136.0 - sym) / 16.0, 0, 1)  # crisp, anti-aliased edge
    alpha = alpha * alpha * (3 - 2 * alpha)
    binm = (sym < 128).astype(np.uint8)

    ys, xs_ = np.where(binm > 0)
    bbox = [int(xs_.min()), int(ys.min()), int(xs_.max()), int(ys.max())]

    # Distance to the stroke edge, normalised by the local stroke half-width so thin
    # tapers and fat strokes both "grow from the centreline".
    edt = cv2.distanceTransform(binm, cv2.DIST_L2, 5)
    local_max = cv2.dilate(edt, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (S * 9, S * 9)))
    local_max = cv2.GaussianBlur(local_max, (0, 0), S * 2.5)
    edt_n = np.clip(cv2.GaussianBlur(edt, (0, 0), 1.5) / np.maximum(local_max, 1e-3), 0, 1)

    # Geodesic distance along the strokes, seeded at the top tip of each half.
    D = 4
    small = cv2.resize(binm, (w // D, h // D), interpolation=cv2.INTER_AREA)
    small = cv2.dilate(small, np.ones((3, 3), np.uint8))
    cost = np.where(small > 0, 1.0, np.inf)
    n, lab = cv2.connectedComponents(small, connectivity=8)
    seeds = []
    for i in range(1, n):
        yy, xx = np.where(lab == i)
        if len(yy) < 200:
            continue
        k = np.argmin(yy)
        seeds.append((int(yy[k]), int(xx[k])))
    mcp = MCP_Geometric(cost)
    dist, _ = mcp.find_costs(seeds)
    finite = np.isfinite(dist)
    dist[~finite] = dist[finite].max()
    dist = dist / dist[finite].max()
    dist = cv2.resize(dist.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
    # Every pixel near a stroke inherits the growth distance of the nearest solid
    # interior pixel, so the growth front never frays the stroke edges.
    inside = binm.astype(bool) & (cv2.distanceTransform(binm, cv2.DIST_L2, 5) > 2)
    _, (iy, ix) = distance_transform_edt(~inside, return_indices=True)
    dist = dist[iy, ix]

    star = [(STAR_SRC[0] - X0) * S, (STAR_SRC[1] - Y0) * S]
    star[0] = float(axis)  # dead centre on the axis

    # Signed distance field: interpolates linearly, so edges stay razor sharp even
    # when the camera is 5x inside the logo.
    din = cv2.distanceTransform(binm, cv2.DIST_L2, 5)
    dout = cv2.distanceTransform(1 - binm, cv2.DIST_L2, 5)
    sdf_bin = np.where(binm > 0, din - 0.5, -(dout - 0.5)).astype(np.float32)
    # Near the outline use the smooth greyscale itself (value / gradient) for a
    # sub-pixel accurate edge; far away the distance transform is fine.
    gx = cv2.Sobel(sym, cv2.CV_32F, 1, 0, ksize=3) / 8.0
    gy = cv2.Sobel(sym, cv2.CV_32F, 0, 1, ksize=3) / 8.0
    grad = np.sqrt(gx * gx + gy * gy)
    sdf_near = (128.0 - sym) / np.maximum(grad, 1e-3)
    wnear = np.clip(1.0 - (np.abs(sdf_bin) - 2.0) / 3.0, 0, 1) * (grad > 0.5)
    sdf = (sdf_near * wnear + sdf_bin * (1 - wnear)).astype(np.float32)

    # Micro detail: anisotropic multi-octave noise (reads as brushed / cast metal).
    rng = np.random.default_rng(5)
    grain = np.zeros((h, w), np.float32)
    for o, amp in ((6, 1.0), (14, 0.6), (40, 0.35), (120, 0.2)):
        n = rng.normal(0, 1, (max(2, h // (192 // o + 1)), max(2, w // (48 // max(1, o // 3) + 1)))).astype(np.float32)
        grain += cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC) * amp
    grain = (grain - grain.mean()) / grain.std()

    # Where the growth front is (left half) for each tenth of a percent of growth,
    # so the camera can chase it.
    ys_, xs2 = np.where(binm > 0)
    dd = dist[ys_, xs2]
    left = xs2 < axis
    bins = np.linspace(0, 1, 201)
    cen = []
    for i in range(200):
        sel = left & (dd >= bins[i]) & (dd < bins[i + 1])
        if sel.sum() < 20:
            cen.append(cen[-1] if cen else [float(xs2[left].mean()), float(ys_[left].min())])
        else:
            cen.append([float(xs2[sel].mean()), float(ys_[sel].mean())])

    np.save(os.path.join(OUT, "sdf.npy"), sdf.astype(np.float16))
    np.save(os.path.join(OUT, "grain.npy"), grain.astype(np.float16))
    np.save(os.path.join(OUT, "alpha.npy"), alpha.astype(np.float16))
    np.save(os.path.join(OUT, "dist.npy"), dist.astype(np.float16))
    np.save(os.path.join(OUT, "edt.npy"), edt_n.astype(np.float16))
    meta = {
        "size": [w, h],
        "bbox": bbox,
        "axis": float(axis),
        "star": star,
        "star_radius": 14.5 * S,
        "seeds": [[s[1] * D, s[0] * D] for s in seeds],
        "front_centroid": cen,
    }
    with open(os.path.join(OUT, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps({k: v for k, v in meta.items() if k != 'front_centroid'}))


if __name__ == "__main__":
    main()
