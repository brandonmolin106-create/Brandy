"""Photographic background plates for the v2 cut.

Crops each source photo to 16:9 with headroom for camera moves, grades it into the
trailer's night look, and cuts occlusion masks so the logo can sit *behind* real
mountains and trees.

Sources (assets/plates/, see CREDITS in README):
  weic2205a.jpg  "Cosmic Cliffs" in Carina - NASA, ESA, CSA, STScI (CC BY 4.0)
  ocean_b.jpg    Anthony Cantin, Unsplash License
  mount_a.jpg    Gantavya Bhatt, Unsplash License
  forest_a.jpg   Wolfgang Hasselmann, Unsplash License

Output: assets/cache/plates/<name>.npz with rgb (uint8, 1.12x 4K), mask (uint8) and meta.
"""
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "assets", "plates")
OUT = os.path.join(HERE, "assets", "cache", "plates")
W4, H4 = 3840, 2160
OVER = 1.12
PW, PH = int(W4 * OVER), int(H4 * OVER)


def crop169(img, cx=0.5, cy=0.5, width=1.0):
    """Largest-ish 16:9 crop centred at (cx, cy), `width` = fraction of source width."""
    h, w = img.shape[:2]
    cw = int(w * width)
    ch = int(cw * 9 / 16)
    if ch > h:
        ch = h
        cw = int(ch * 16 / 9)
    x0 = int(np.clip(cx * w - cw / 2, 0, w - cw))
    y0 = int(np.clip(cy * h - ch / 2, 0, h - ch))
    return img[y0:y0 + ch, x0:x0 + cw], (x0, y0, cw, ch)


def to_lin(img):
    return (img.astype(np.float32) / 255.0) ** 2.2


def to_u8(lin):
    return np.clip((np.clip(lin, 0, 1) ** (1 / 2.2)) * 255 + 0.5, 0, 255).astype(np.uint8)


def desat(lin, amt):
    lum = lin @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    return lin * (1 - amt) + lum[..., None] * amt


def denoise(img):
    return cv2.fastNlMeansDenoisingColored(img, None, 3, 3, 7, 21)


# Ridge line traced by eye on a 1% grid (x, y as fractions of the cropped plate),
# then snapped to the strongest nearby edge in code.
RIDGE_TRACE = [
    (0.000, 0.708), (0.020, 0.704), (0.040, 0.701), (0.060, 0.698), (0.075, 0.695), (0.083, 0.689),
    (0.092, 0.678), (0.099, 0.672), (0.111, 0.671), (0.122, 0.670), (0.131, 0.666), (0.139, 0.662),
    (0.147, 0.659), (0.154, 0.660), (0.164, 0.665), (0.175, 0.670), (0.183, 0.678), (0.192, 0.683),
    (0.200, 0.681), (0.208, 0.686), (0.215, 0.695), (0.228, 0.697), (0.242, 0.698), (0.250, 0.706),
    (0.258, 0.710), (0.267, 0.706), (0.278, 0.701), (0.286, 0.689), (0.294, 0.683), (0.303, 0.682),
    (0.314, 0.686), (0.322, 0.682), (0.333, 0.678), (0.342, 0.675), (0.350, 0.662), (0.361, 0.659),
    (0.372, 0.650), (0.381, 0.647), (0.392, 0.630), (0.400, 0.621), (0.411, 0.613), (0.422, 0.608),
    (0.431, 0.600), (0.439, 0.597), (0.444, 0.600), (0.450, 0.608), (0.458, 0.628), (0.469, 0.650),
    (0.478, 0.663), (0.489, 0.669), (0.500, 0.678), (0.511, 0.688), (0.522, 0.695), (0.531, 0.689),
    (0.542, 0.684), (0.556, 0.675), (0.567, 0.669), (0.581, 0.667), (0.592, 0.665), (0.601, 0.669),
    (0.611, 0.669), (0.618, 0.656), (0.622, 0.641), (0.631, 0.628), (0.644, 0.617), (0.661, 0.611),
    (0.678, 0.608), (0.694, 0.608), (0.704, 0.610), (0.711, 0.608), (0.722, 0.595), (0.733, 0.584),
    (0.744, 0.574), (0.761, 0.559), (0.778, 0.546), (0.794, 0.537), (0.808, 0.530), (0.817, 0.526),
    (0.833, 0.523), (0.850, 0.522), (0.867, 0.525), (0.878, 0.530), (0.894, 0.539), (0.911, 0.552),
    (0.928, 0.567), (0.944, 0.576), (0.961, 0.574), (0.972, 0.569), (0.983, 0.563), (1.000, 0.567)]


def ridge_mask(img):
    """Mountains vs sky from the hand-traced ridge, snapped to the strongest vertical
    edge (stars median-filtered away) within a small window, then smoothed."""
    h, w = img.shape[:2]
    tr = np.array(RIDGE_TRACE)
    ridge = np.interp(np.arange(w) / (w - 1), tr[:, 0], tr[:, 1]) * h
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    g = cv2.medianBlur(cv2.medianBlur(g, 7), 7).astype(np.float32)
    g = cv2.GaussianBlur(g, (0, 0), 2)
    gy = np.abs(cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=5))
    win = int(0.008 * h)
    snapped = ridge.copy()
    for x in range(w):
        y0 = int(max(0, ridge[x] - win))
        y1 = int(min(h, ridge[x] + win))
        col = gy[y0:y1, x]
        if len(col) and col.max() > 0:
            snapped[x] = y0 + int(col.argmax())
    d = snapped - ridge
    d = cv2.medianBlur(d.astype(np.float32)[None, :], 5)[0]
    ridge = ridge + cv2.GaussianBlur(d[None, :], (0, 0), 3)[0]
    ys = np.arange(h)
    m = (ys[:, None] > ridge[None, :] - 1.5).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    return (m * 255).astype(np.uint8), ridge


def trunk_mask(img):
    """Dark trunks/branches in front of the misty background."""
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    b = cv2.GaussianBlur(g, (0, 0), 3)
    bg = cv2.GaussianBlur(g, (0, 0), 60)
    m = np.clip((bg * 0.72 - b) / (bg * 0.25 + 1), 0, 1)
    m = cv2.GaussianBlur(m, (0, 0), 1.5)
    return (m * 255).astype(np.uint8)


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {}

    # --- deep space (Webb): cool, dark, detailed
    im = cv2.cvtColor(cv2.imread(os.path.join(SRC, "weic2205a.jpg")), cv2.COLOR_BGR2RGB)
    c, _ = crop169(im, 0.5, 0.42, 1.0)
    c = cv2.resize(c, (PW, PH), interpolation=cv2.INTER_AREA)
    lin = to_lin(c)
    lin = desat(lin, 0.25) * np.float32([0.85, 0.9, 1.05]) * 0.30
    np.savez(os.path.join(OUT, "space.npz"), rgb=to_u8(lin))
    meta["space"] = {}

    # --- ocean at dusk: find the horizon, keep the ember glow, darken the sky
    im = cv2.cvtColor(cv2.imread(os.path.join(SRC, "ocean_b.jpg")), cv2.COLOR_BGR2RGB)
    h, w = im.shape[:2]
    c, (x0, y0, cw, ch) = crop169(im, 0.5, 1.0, 1.0)
    hor_src = 2334
    c = cv2.resize(denoise(c), (PW, PH), interpolation=cv2.INTER_AREA)
    hor = (hor_src - y0) / ch * PH
    lin = to_lin(c)
    yy = np.arange(PH, dtype=np.float32)[:, None, None]
    sky = yy < hor
    lin = np.where(sky, lin * 0.5 * np.clip((yy / hor) ** 0.6, 0.35, 1.0), desat(lin, 0.35) * 0.5)
    np.savez(os.path.join(OUT, "ocean.npz"), rgb=to_u8(lin))
    meta["ocean"] = {"horizon": float(hor)}

    # --- mountains under the Milky Way (+ a storm grade of the same plate)
    im = cv2.cvtColor(cv2.imread(os.path.join(SRC, "mount_a.jpg")), cv2.COLOR_BGR2RGB)
    c, _ = crop169(im, 0.5, 1.0, 1.0)
    c = cv2.resize(c, (PW, PH), interpolation=cv2.INTER_AREA)
    m, ridge = ridge_mask(c)
    lin = to_lin(c)
    lin = desat(lin, 0.2) * np.float32([0.85, 0.92, 1.1]) * 1.05
    np.savez(os.path.join(OUT, "mount.npz"), rgb=to_u8(lin), mask=m)
    storm = desat(to_lin(c), 0.6) * np.float32([0.8, 0.86, 1.0]) * 0.45
    np.savez(os.path.join(OUT, "storm.npz"), rgb=to_u8(storm), mask=m)
    meta["mount"] = meta["storm"] = {"ridge_mean": float(ridge.mean()), "ridge_min": float(ridge.min())}

    # --- haunted forest: tame the teal, sink it into night
    im = cv2.cvtColor(cv2.imread(os.path.join(SRC, "forest_a.jpg")), cv2.COLOR_BGR2RGB)
    c, _ = crop169(im, 0.5, 0.52, 1.0)
    c = cv2.resize(c, (PW, PH), interpolation=cv2.INTER_AREA)
    tm = trunk_mask(c)
    lin = to_lin(c)
    lin = desat(lin, 0.6) * np.float32([0.7, 0.85, 1.1]) * 0.3
    lin = lin ** 1.25 * 1.6  # deeper contrast: the mist glows, the trunks go black
    np.savez(os.path.join(OUT, "forest.npz"), rgb=to_u8(lin), mask=tm)
    meta["forest"] = {}

    with open(os.path.join(OUT, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
