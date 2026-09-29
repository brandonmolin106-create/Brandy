"""Procedural texture set for the hero betta: imbricated scales, operculum, fin rays, ragged fin edges.

Run with system python (numpy + opencv). Writes 16-bit/8-bit PNGs into OUTDIR:
  body_albedo.png body_height.png body_rough.png body_film.png   (UV: x = head->tail, y = around the body)
  fin_caudal_*.png fin_dorsal_*.png fin_anal_*.png fin_pelvic_*.png fin_pectoral_*.png (UV: x = across rays, y = root->edge)
"""
import os
import sys

import cv2
import numpy as np

RNG = np.random.default_rng(7)


def smoothstep(a, b, x):
    t = np.clip((x - a) / np.where(b == a, 1e-6, b - a), 0, 1)
    return t * t * (3 - 2 * t)


def value_noise(shape, cells, seed, octaves=4):
    """Tileable-ish fractal value noise in [0,1]."""
    rng = np.random.default_rng(seed)
    h, w = shape
    out = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        cy, cx = max(2, int(cells[0] * 2 ** o)), max(2, int(cells[1] * 2 ** o))
        g = rng.random((cy, cx)).astype(np.float32)
        out += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= 0.5
    out /= tot
    return np.clip((out - out.min()) / (out.max() - out.min() + 1e-6), 0, 1)


def save(path, arr, bits=8):
    arr = np.clip(arr, 0, 1)
    if bits == 16:
        img = (arr * 65535).astype(np.uint16)
    else:
        img = (arr * 255 + 0.5).astype(np.uint8)
    if img.ndim == 3:
        img = img[..., ::-1]
    # numpy row 0 = UV v=0; Blender samples UV (0,0) at the bottom-left of the image
    cv2.imwrite(path, np.ascontiguousarray(np.flipud(img)))


def body(out, W=4096, H=2048):
    u = (np.arange(W, dtype=np.float32) + 0.5) / W          # head -> tail
    v = (np.arange(H, dtype=np.float32) + 0.5) / H          # around: 0 right side, .25 top, .5 left, .75 belly
    U, V = np.meshgrid(u, v)
    # --- imbricated scales: staggered lattice, the most anterior covering scale is on top
    rows, cols = 34.0, 22.0                                  # scale rows head->tail / around
    su, sv = U * rows, V * cols
    height = np.zeros((H, W), np.float32)
    edge = np.zeros((H, W), np.float32)
    center = np.zeros((H, W), np.float32)
    sid = np.zeros((H, W), np.float32)
    best = np.full((H, W), 1e9, np.float32)
    iu0 = np.floor(su)
    r = 0.78
    for di in (-1, 0, 1):
        iu = iu0 + di
        off = 0.5 * (np.mod(iu, 2))
        iv0 = np.floor(sv - off)
        for dj in (-1, 0, 1):
            iv = iv0 + dj
            cu, cvv = iu + 0.35, iv + off + 0.5
            du, dv = (su - cu), (sv - cvv) * 0.92
            d = np.sqrt(du * du + dv * dv)
            inside = d < r
            better = inside & (cu < best)                     # most anterior covering scale wins
            best = np.where(better, cu, best)
            # height ramps toward the free (posterior) edge, drops at the rim
            h = 0.25 + 0.75 * np.clip((du / r + 1) * 0.5, 0, 1) ** 1.3
            rim = smoothstep(r, r * 0.86, d)
            hh = h * (0.35 + 0.65 * rim)
            height = np.where(better, hh, height)
            edge = np.where(better, 1 - smoothstep(r * 0.72, r * 0.98, d) * (du > -0.1), edge)
            center = np.where(better, 1 - d / r, center)
            sid = np.where(better, (np.sin(cu * 12.9898 + cvv * 78.233) * 43758.5453) % 1.0, sid)
    edge = 1 - edge
    # head has no scales: fade scales in behind the operculum (curved gill line)
    gill_u = 0.205 + 0.028 * np.cos((V - 0.25) * 2 * np.pi) ** 2
    scale_mask = smoothstep(gill_u, gill_u + 0.03, U) * (1 - smoothstep(0.965, 1.0, U) * 0.6)
    skin = value_noise((H, W), (6, 24), 3)
    height = height * scale_mask + (1 - scale_mask) * (0.45 + 0.1 * skin)
    # operculum ridge + gill slit shadow
    dg = U - gill_u
    ridge = np.exp(-(dg / 0.004) ** 2) * 0.35 - np.exp(-((dg - 0.006) / 0.003) ** 2) * 0.25
    side = np.abs(np.cos(V * 2 * np.pi)) ** 0.5               # only on the flanks
    height += ridge * side * (U < 0.3)
    # lateral line: tiny pores along the flank midline
    for vc in (0.0, 0.5, 1.0):
        ll = np.exp(-((V - vc) / 0.006) ** 2) * (np.sin(U * rows * 2 * np.pi) > 0.6) * scale_mask
        height -= ll * 0.08
    height = cv2.GaussianBlur(height, (0, 0), 1.0)
    save(f'{out}/body_height.png', height, 16)

    # --- colour: deep crimson, darker dorsum, iridescent steel-blue scale margins near head/shoulder
    top = np.clip(np.sin(V * 2 * np.pi), 0, 1)                # 1 on the back
    belly = np.clip(-np.sin(V * 2 * np.pi), 0, 1)
    n1 = value_noise((H, W), (4, 16), 11)
    base = np.stack([0.30 + 0.08 * n1, 0.006 + 0.004 * n1, 0.012 + 0.006 * n1], -1)
    base *= (1 - 0.55 * top[..., None] ** 1.5)[..., :]
    base[..., 0] *= 1 + 0.25 * belly
    var = (sid - 0.5)[..., None] * np.array([0.08, 0.006, 0.012])
    base = base + var * scale_mask[..., None]
    # scale centres slightly darker, pocket shadow behind each rim
    base *= (0.78 + 0.32 * (1 - center * 0.6))[..., None] ** 1.0
    base *= (1 - 0.45 * (1 - edge) * 0 - 0.25 * smoothstep(0.35, 0.0, height))[..., None]
    # dark head mask with red cheeks, black lips
    head = 1 - smoothstep(0.08, 0.26, U)
    base *= (1 - 0.6 * head * (0.6 + 0.4 * top))[..., None]
    # scale outlines catch light: brighter crimson rims
    base = base + (1 - edge)[..., None] * scale_mask[..., None] * np.array([0.10, 0.003, 0.008])
    lips = (1 - smoothstep(0.0, 0.03, U))
    base *= (1 - 0.8 * lips)[..., None]
    # iridescent margins (the thin-film shader colours them; albedo gets a cool lift)
    film_mask = np.clip((1 - edge) * scale_mask * (0.35 + 0.65 * (1 - smoothstep(0.25, 0.75, U)))
                        * (0.4 + 0.6 * np.abs(np.cos(V * 2 * np.pi))), 0, 1)
    base = base * (1 - 0.35 * film_mask[..., None]) + film_mask[..., None] * np.array([0.012, 0.016, 0.055])
    save(f'{out}/body_albedo.png', np.clip(base, 0, 1) ** (1 / 2.2))
    rough = 0.32 - 0.14 * film_mask + 0.08 * (1 - scale_mask) + 0.05 * n1
    save(f'{out}/body_rough.png', rough)
    film = (0.35 + 0.65 * film_mask * (0.6 + 0.4 * sid)) * (0.15 + 0.85 * scale_mask) * (1 - 0.6 * head)
    save(f'{out}/body_film.png', film)


def fin(out, name, W, H, rays0, splits, seed, tint, clear=False, edge_band=True, tip_len=0.02):
    """UV x across rays (0..1), y root(0) -> edge(1). Rays branch smoothly (Y-shaped) at the split depths."""
    x = (np.arange(W, dtype=np.float32) + 0.5) / W
    y = (np.arange(H, dtype=np.float32) + 0.5) / H
    X, Y = np.meshgrid(x, y)
    rng = np.random.default_rng(seed)
    ray = np.zeros((H, W), np.float32)
    pitch = 1.0 / rays0
    roots = (np.arange(rays0) + 0.5) * pitch + rng.normal(0, 0.08 * pitch, rays0)
    nlev = len(splits)
    yy = y[:, None]
    for k, p in enumerate(roots):
        for leaf in range(2 ** nlev):
            xpath = np.full_like(yy, p) + 0.003 * np.sin(yy * 7 + k * 1.3 + leaf) + 0.0015 * np.sin(yy * 19 + k)
            for lvl, ys in enumerate(splits):
                sign = 1 if (leaf >> (nlev - 1 - lvl)) & 1 else -1
                spread = pitch * 0.25 / (2 ** lvl) * (0.8 + 0.4 * rng.random())
                xpath = xpath + sign * spread * smoothstep(ys, ys + 0.12, yy)
            width = (1.6 - 0.8 * yy) / W + 0.0006
            d = np.abs(X - xpath)
            ray = np.maximum(ray, np.exp(-(d / width) ** 2))
    joints = 0.88 + 0.12 * (np.sin(Y * 150 + X * 3) > 0.75)
    ray *= joints
    n_edge = value_noise((4, W), (1, 12), seed + 1, octaves=5)[0]
    n_fine = value_noise((4, W), (1, 90), seed + 5, octaves=3)[0]
    streak = value_noise((H, W), (3, 60), seed + 2)            # streaks run along the rays
    edge_y = 0.94 - 0.06 * n_edge ** 1.4 - 0.025 * n_fine
    edge_y = edge_y[None, :]
    alpha = 1 - smoothstep(edge_y - 0.02, edge_y, Y)
    if tip_len > 0:
        tips = (ray > 0.5) * (1 - smoothstep(edge_y, edge_y + tip_len, Y)) * (Y >= edge_y - 0.02)
        alpha = np.maximum(alpha, tips)
    memb = (0.93 - 0.42 * Y ** 1.4) * (0.88 + 0.12 * streak)
    if clear:
        memb = 0.16 + 0.08 * streak
    opac = np.clip(memb + ray * 0.4, 0, 1) * alpha
    save(f'{out}/fin_{name}_alpha.png', opac)
    t = np.array(tint, np.float32)
    col = t[None, None, :] * (0.55 + 0.6 * smoothstep(0.0, 0.5, Y)[..., None])
    if edge_band:
        band = np.exp(-((Y - (edge_y - 0.13)) / 0.045) ** 2)
        col *= (1 - 0.5 * band)[..., None]
        rim = smoothstep(edge_y - 0.05, edge_y - 0.005, Y)
        col = col * (1 - 0.3 * rim[..., None]) + rim[..., None] * np.array([0.05, 0.02, 0.08])
    col *= (1 + 0.45 * ray)[..., None]
    col *= (0.86 + 0.28 * streak)[..., None]
    if clear:
        col = np.ones_like(col) * np.array([0.5, 0.32, 0.32])
    save(f'{out}/fin_{name}_albedo.png', np.clip(col, 0, 1) ** (1 / 2.2))
    save(f'{out}/fin_{name}_ray.png', np.clip(ray, 0, 1))


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/opt/assets/betta'
    os.makedirs(out, exist_ok=True)
    body(out)
    red = (0.55, 0.012, 0.02)
    fin(out, 'caudal', 2048, 1024, 22, [0.33, 0.62], 21, red)
    fin(out, 'dorsal', 1024, 1024, 12, [0.4, 0.7], 22, red)
    fin(out, 'anal', 2048, 1024, 20, [0.38, 0.68], 23, red)
    fin(out, 'pelvic', 256, 1024, 2, [0.5], 24, (0.55, 0.012, 0.02), tip_len=0.0)
    fin(out, 'pectoral', 512, 512, 9, [0.55], 25, (0.5, 0.3, 0.3), clear=True, edge_band=False, tip_len=0.0)
    print('textures ->', out)
