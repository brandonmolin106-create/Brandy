#!/usr/bin/env python3
"""
Paints every texture the mod uses (pixel art, drawn with code) and writes them into
src/main/resources/assets/turtlepower/textures.

Run:  python3 tools/gen_textures.py
Needs Pillow (pip install pillow).
"""
import os
import random
from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..", "src", "main", "resources", "assets", "turtlepower", "textures")


# ----------------------------------------------------------------------------- helpers

def hexc(c, a=255):
    if isinstance(c, tuple):
        return c if len(c) == 4 else (c[0], c[1], c[2], a)
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), a)


def shade(c, f):
    r, g, b, a = hexc(c)
    return (max(0, min(255, int(r * f))), max(0, min(255, int(g * f))), max(0, min(255, int(b * f))), a)


def new(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def px(im, x, y, c):
    if 0 <= x < im.width and 0 <= y < im.height:
        im.putpixel((x, y), hexc(c))


def rect(im, x0, y0, x1, y1, c):
    """Filled rectangle, inclusive corners."""
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            px(im, x, y, c)


def noisy(im, x0, y0, w, h, c, var=0.08, seed=1):
    rnd = random.Random(seed * 7919 + x0 * 31 + y0)
    for x in range(x0, x0 + w):
        for y in range(y0, y0 + h):
            px(im, x, y, shade(c, 1.0 + rnd.uniform(-var, var)))


def line(im, x0, y0, x1, y1, c):
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        px(im, x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def faces(u, v, w, h, d):
    """UV rectangles (x, y, width, height) of a Minecraft model box."""
    return {
        "top": (u + d, v, w, d),
        "bottom": (u + d + w, v, w, d),
        "right": (u, v + d, d, h),
        "front": (u + d, v + d, w, h),
        "left": (u + d + w, v + d, d, h),
        "back": (u + d + w + d, v + d, w, h),
    }


def fill_box(im, u, v, w, h, d, c, var=0.07, seed=1):
    for name, (x, y, fw, fh) in faces(u, v, w, h, d).items():
        noisy(im, x, y, fw, fh, c, var, seed + hash(name) % 97)


def save(im, *path):
    out = os.path.join(ROOT, *path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out)


# Standard humanoid UV layout (64x64, like a player skin but without the overlay layers).
HEAD = (0, 0, 8, 8, 8)
HAT = (32, 0, 8, 8, 8)
BODY = (16, 16, 8, 12, 4)
R_ARM = (40, 16, 4, 12, 4)
L_ARM = (32, 48, 4, 12, 4)
R_LEG = (0, 16, 4, 12, 4)
L_LEG = (16, 48, 4, 12, 4)


def limb_rows(im, box, rows, c):
    """Paint horizontal bands (row offsets inside the limb, 0 = top) all the way around a limb."""
    u, v, w, h, d = box
    for name in ("right", "front", "left", "back"):
        x, y, fw, fh = faces(u, v, w, h, d)[name]
        for r in rows:
            for i in range(fw):
                px(im, x + i, y + r, c)


def band_around_head(im, box, rows, c):
    u, v, w, h, d = box
    for name in ("right", "front", "left", "back"):
        x, y, fw, fh = faces(u, v, w, h, d)[name]
        for r in rows:
            for i in range(fw):
                px(im, x + i, y + r, c)


# ----------------------------------------------------------------------------- turtles

TURTLES = {
    # name: (skin, mask, plastron, shell)
    "leonardo": ("#4f8f3a", "#1f4fd8", "#d9c27a", "#4d5a2a"),
    "raphael": ("#3e7a33", "#d01a1a", "#cdb46c", "#44502a"),
    "donatello": ("#5b8f2e", "#7b2fbf", "#d4bd78", "#4f5b2c"),
    "michelangelo": ("#6fae45", "#f08a1c", "#e0c985", "#566330"),
}
PAD = "#7a5230"
WRAP = "#cfc39a"


def shell_pattern(im, x, y, w, h, base, chip=False, seed=3):
    """Hexagon-ish scutes on the back of a shell."""
    noisy(im, x, y, w, h, base, 0.06, seed)
    light = shade(base, 1.25)
    dark = shade(base, 0.6)
    for yy in range(h):
        for xx in range(w):
            # scute grid: vertical lines every 3-4, staggered horizontal lines
            col = xx // 3
            edge_v = xx % 3 == 0 and xx not in (0,)
            edge_h = (yy + (col % 2) * 2) % 4 == 0
            if edge_v or edge_h:
                px(im, x + xx, y + yy, dark)
            elif (xx + yy) % 5 == 0:
                px(im, x + xx, y + yy, light)
    # rim
    for xx in range(w):
        px(im, x + xx, y, shade(base, 0.5))
        px(im, x + xx, y + h - 1, shade(base, 0.5))
    for yy in range(h):
        px(im, x, y + yy, shade(base, 0.5))
        px(im, x + w - 1, y + yy, shade(base, 0.5))
    if chip:
        # Raph's famous chipped shell
        for (cx, cy) in [(w - 2, h - 4), (w - 3, h - 3), (w - 2, h - 3), (w - 2, h - 2), (w - 3, h - 2), (w - 4, h - 2)]:
            px(im, x + cx, y + cy, (0, 0, 0, 0) if False else shade(base, 0.3))


def turtle_face(im, name, skin, mask):
    x, y, w, h = faces(*HEAD)["front"]  # (8, 8, 8, 8)
    # mask band rows 2..4 of the face (y 10..12) all around the head
    band_around_head(im, HEAD, [2, 3, 4], mask)
    # eye holes: white eyes with a pupil looking a bit inward
    for ex in (1, 2):
        px(im, x + ex, y + 3, "#ffffff")
    for ex in (5, 6):
        px(im, x + ex, y + 3, "#ffffff")
    px(im, x + 2, y + 3, "#101010")
    px(im, x + 5, y + 3, "#101010")
    # darker mask edge for depth
    for i in range(8):
        px(im, x + i, y + 4, shade(mask, 0.75))
    # knot on the back of the head
    bx, by, _, _ = faces(*HEAD)["back"]
    rect(im, bx + 3, by + 2, bx + 4, by + 4, shade(mask, 0.8))
    # mouths
    mouth = shade(skin, 0.45)
    if name == "michelangelo":
        for i in range(2, 6):
            px(im, x + i, y + 6, mouth)
        px(im, x + 1, y + 5, mouth)
        px(im, x + 6, y + 5, mouth)
        rect(im, x + 3, y + 6, x + 4, y + 6, "#ffffff")
        # freckles
        for (fx, fy) in [(1, 5), (6, 5)]:
            px(im, x + fx, y + fy - 0, shade(skin, 0.7))
    elif name == "raphael":
        for i in range(2, 6):
            px(im, x + i, y + 6, mouth)
        px(im, x + 1, y + 7, mouth)
        px(im, x + 6, y + 7, mouth)
        # scowl lines under the mask
        px(im, x + 3, y + 5, shade(skin, 0.7))
    elif name == "donatello":
        for i in range(2, 6):
            px(im, x + i, y + 6, mouth)
        px(im, x + 4, y + 6, "#ffffff")  # the famous gap tooth
    else:
        for i in range(2, 6):
            px(im, x + i, y + 6, mouth)


def plastron(im, box, color, straps, strap_color=PAD):
    x, y, w, h = faces(*box)["front"]
    rect(im, x + 1, y + 1, x + w - 2, y + h - 2, color)
    for yy in range(y + 3, y + h - 1, 3):
        for xx in range(x + 1, x + w - 1):
            px(im, xx, yy, shade(color, 0.8))
    for yy in range(y + 1, y + h - 1):
        px(im, x + w // 2 - 1, yy, shade(color, 0.85))
    # belt
    for xx in range(x, x + w):
        px(im, xx, y + 9, strap_color)
        px(im, xx, y + 10, shade(strap_color, 0.8))
    if straps == "x":
        line(im, x, y, x + w - 1, y + 8, strap_color)
        line(im, x + w - 1, y, x, y + 8, strap_color)
    elif straps == "one":
        line(im, x, y, x + w - 1, y + 8, strap_color)
    # buckle
    rect(im, x + 3, y + 9, x + 4, y + 10, "#c0c0c0")


def paint_turtle(name, for_player=False):
    skin, mask, plas, shellc = TURTLES[name]
    im = new(64, 64)
    for box, seed in ((HEAD, 1), (BODY, 2), (R_ARM, 3), (L_ARM, 4), (R_LEG, 5), (L_LEG, 6)):
        fill_box(im, *box, skin, 0.08, seed)
    turtle_face(im, name, skin, mask)
    # body: plastron front, shell-coloured back and sides
    plastron(im, BODY, plas, {"leonardo": "x", "donatello": "one", "michelangelo": "one", "raphael": None}[name])
    bx, by, bw, bh = faces(*BODY)["back"]
    shell_pattern(im, bx, by, bw, bh, shellc, name == "raphael")
    for side in ("right", "left"):
        sx, sy, sw, sh = faces(*BODY)[side]
        noisy(im, sx, sy, sw, sh, shade(shellc, 0.9), 0.05, 9)
    # elbow pads, wrist wraps, knee pads, ankle wraps
    for arm in (R_ARM, L_ARM):
        limb_rows(im, arm, [5, 6], PAD)
        limb_rows(im, arm, [10, 11], WRAP)
    for leg in (R_LEG, L_LEG):
        limb_rows(im, leg, [4, 5], PAD)
        limb_rows(im, leg, [10, 11], WRAP)
    # three big fingers / toes hints on the bottom faces
    for limb in (R_ARM, L_ARM, R_LEG, L_LEG):
        x, y, w, h = faces(*limb)["bottom"]
        noisy(im, x, y, w, h, shade(skin, 0.85), 0.05, 11)
    if not for_player:
        # 3D shell (texOffs 0,32; 10x13x3)
        sf = faces(0, 32, 10, 13, 3)
        for k in ("top", "bottom", "right", "left", "front"):
            x, y, w, h = sf[k]
            noisy(im, x, y, w, h, "#b89a5c" if k != "front" else shade(shellc, 0.6), 0.08, 13)
        x, y, w, h = sf["back"]
        shell_pattern(im, x, y, w, h, shellc, name == "raphael", 21)
        # mask tails
        for (u, v) in ((0, 58), (48, 58)):
            for k, (x, y, w, h) in faces(u, v, 1, 1, 5).items():
                rect(im, x, y, x + w - 1, y + h - 1, mask)
    else:
        # player skin: put a slightly raised mask on the hat layer
        hx, hy, hw, hh = faces(*HAT)["front"]
        band_around_head(im, HAT, [2, 3, 4], mask)
        for ex in (1, 2, 5, 6):
            px(im, hx + ex, hy + 3, (0, 0, 0, 0))
        px(im, hx + 1, hy + 3, (0, 0, 0, 0))
    return im


# ----------------------------------------------------------------------------- other characters

def paint_splinter():
    fur, dark, robe, pink = "#7a5a3c", "#5a4028", "#7a1f2b", "#d98c9a"
    im = new(64, 64)
    fill_box(im, *HEAD, fur, 0.1, 1)
    fill_box(im, *BODY, robe, 0.06, 2)
    fill_box(im, *R_ARM, robe, 0.06, 3)
    fill_box(im, *L_ARM, robe, 0.06, 4)
    fill_box(im, *R_LEG, robe, 0.06, 5)
    fill_box(im, *L_LEG, robe, 0.06, 6)
    x, y, w, h = faces(*HEAD)["front"]
    # lighter muzzle, beard, eyes, whiskers
    rect(im, x + 2, y + 4, x + 5, y + 7, "#9c7a5a")
    rect(im, x + 2, y + 7, x + 5, y + 7, "#d8d4cc")
    px(im, x + 3, y + 7, "#ffffff")
    px(im, x + 4, y + 7, "#ffffff")
    for ex in (1, 5):
        px(im, x + ex, y + 3, "#101010")
        px(im, x + ex + 1, y + 3, "#101010")
        px(im, x + ex, y + 2, "#3a2a1a")
    px(im, x + 2, y + 3, "#ffffff") if False else None
    # grey eyebrows (he's old)
    for ex in (1, 2, 5, 6):
        px(im, x + ex, y + 2, "#bdb8b0")
    # arms end in fur hands, belt, robe edge
    for arm in (R_ARM, L_ARM):
        limb_rows(im, arm, [10, 11], fur)
        limb_rows(im, arm, [9], shade(robe, 0.7))
    for leg in (R_LEG, L_LEG):
        limb_rows(im, leg, [8, 9, 10, 11], fur)
        limb_rows(im, leg, [7], shade(robe, 0.7))
    fx, fy, fw, fh = faces(*BODY)["front"]
    for xx in range(fx, fx + fw):
        px(im, xx, fy + 7, "#3b2a1a")
    line(im, fx + 1, fy, fx + 5, fy + 6, shade(robe, 0.7))  # robe fold
    # ears (0,32) and (8,32): 3x3x1
    for (u, v) in ((0, 32), (8, 32)):
        fill_box(im, u, v, 3, 3, 1, fur, 0.05, 7)
        ex, ey, _, _ = faces(u, v, 3, 3, 1)["front"]
        rect(im, ex, ey, ex + 2, ey + 2, pink)
        px(im, ex + 1, ey + 1, shade(pink, 0.8))
    # snout (16,32): 3x3x3, black nose at the tip
    fill_box(im, 16, 32, 3, 3, 3, "#9c7a5a", 0.05, 8)
    sx, sy, _, _ = faces(16, 32, 3, 3, 3)["front"]
    rect(im, sx, sy, sx + 2, sy, "#1a1010")
    px(im, sx + 1, sy + 1, "#1a1010")
    # tail (28,32): 1x1x12
    for k, (x0, y0, w0, h0) in faces(28, 32, 1, 1, 12).items():
        noisy(im, x0, y0, w0, h0, "#b98a86", 0.08, 12)
    return im


def paint_april():
    skinc, hair = "#f2c9a0", "#d9642a"
    im = new(64, 64)
    fill_box(im, *HEAD, skinc, 0.03, 1)
    fill_box(im, *HAT, (0, 0, 0, 0), 0, 1)
    fill_box(im, *BODY, "#f2c230", 0.05, 2)
    fill_box(im, *R_ARM, "#1c1c22", 0.05, 3)
    fill_box(im, *L_ARM, "#1c1c22", 0.05, 4)
    fill_box(im, *R_LEG, "#1c1c22", 0.05, 5)
    fill_box(im, *L_LEG, "#1c1c22", 0.05, 6)
    # hair on top, sides and back, plus a fringe
    for k in ("top", "right", "left", "back"):
        x, y, w, h = faces(*HEAD)[k]
        noisy(im, x, y, w, h if k in ("top",) else h, hair, 0.08, 5)
    x, y, w, h = faces(*HEAD)["front"]
    rect(im, x, y, x + 7, y + 1, hair)
    px(im, x, y + 2, hair)
    px(im, x + 7, y + 2, hair)
    # yellow headband
    for k in ("front", "right", "left", "back"):
        hx, hy, hw, hh = faces(*HEAD)[k]
        for i in range(hw):
            px(im, hx + i, hy + 1, "#f2c230")
    # face: blue eyes, mouth
    for ex in (1, 5):
        px(im, x + ex, y + 4, "#ffffff")
        px(im, x + ex + 1, y + 4, "#2d6fd1")
    rect(im, x + 3, y + 6, x + 4, y + 6, "#c0584a")
    # ponytail on the hat layer at the back
    bx, by, bw, bh = faces(*HAT)["back"]
    rect(im, bx + 3, by + 3, bx + 4, by + 7, hair)
    # shirt: black number 5 on the front
    fx, fy, fw, fh = faces(*BODY)["front"]
    for (dx, dy) in [(3, 2), (4, 2), (5, 2), (3, 3), (3, 4), (4, 4), (5, 5), (5, 6), (3, 7), (4, 7)]:
        px(im, fx + dx, fy + dy, "#1c1c22")
    # jean shorts over leggings, boots
    for leg in (R_LEG, L_LEG):
        limb_rows(im, leg, [0, 1, 2, 3], "#3a5f9c")
        limb_rows(im, leg, [9, 10, 11], "#6b4226")
    # skin hands
    for arm in (R_ARM, L_ARM):
        limb_rows(im, arm, [11], skinc)
    return im


def paint_kraang(prime=False):
    metal = "#5b2a86" if prime else "#d9dde3"
    trim = "#e0b040" if prime else "#9aa0a8"
    joint = "#2a2a30"
    brain = "#e56bb7"
    im = new(64, 64)
    for box, seed in ((HEAD, 1), (BODY, 2), (R_ARM, 3), (L_ARM, 4), (R_LEG, 5), (L_LEG, 6)):
        fill_box(im, *box, metal, 0.05, seed)
    # visor with two glowing dots
    x, y, w, h = faces(*HEAD)["front"]
    rect(im, x + 1, y + 2, x + 6, y + 4, "#15151a")
    px(im, x + 2, y + 3, "#ff78cf")
    px(im, x + 5, y + 3, "#ff78cf")
    rect(im, x + 2, y + 6, x + 5, y + 6, trim)
    # body: dark chest cavity where the Kraang rides, seams
    fx, fy, fw, fh = faces(*BODY)["front"]
    rect(im, fx + 1, fy + 2, fx + fw - 2, fy + 9, "#1a1520")
    for xx in range(fx, fx + fw):
        px(im, xx, fy + 11, trim)
    bx, by, bw, bh = faces(*BODY)["back"]
    for yy in range(by, by + bh, 3):
        for xx in range(bx, bx + bw):
            px(im, xx, yy, shade(metal, 0.8))
    # joints
    for arm in (R_ARM, L_ARM):
        limb_rows(im, arm, [5], joint)
        limb_rows(im, arm, [10, 11], joint)
    for leg in (R_LEG, L_LEG):
        limb_rows(im, leg, [5], joint)
        limb_rows(im, leg, [11], joint)
    # the Kraang itself (brain box at 0,32: 5x5x2)
    fill_box(im, 0, 32, 5, 5, 2, brain, 0.12, 20)
    bx, by, bw, bh = faces(0, 32, 5, 5, 2)["front"]
    line(im, bx, by + 1, bx + 4, by + 1, shade(brain, 0.7))
    line(im, bx + 1, by + 3, bx + 3, by + 3, shade(brain, 0.7))
    px(im, bx + 2, by + 2, "#ffe14a")  # its eye
    px(im, bx + 2, by + 2, "#ffe14a")
    px(im, bx + 3, by + 2, "#101010")
    px(im, bx + 1, by + 4, "#a0306a")  # beak
    px(im, bx + 3, by + 4, "#a0306a")
    return im


def paint_foot():
    black, gray = "#1a1a1e", "#3a3a42"
    im = new(64, 64)
    for box, seed in ((HEAD, 1), (BODY, 2), (R_ARM, 3), (L_ARM, 4), (R_LEG, 5), (L_LEG, 6)):
        fill_box(im, *box, black, 0.12, seed)
    x, y, w, h = faces(*HEAD)["front"]
    rect(im, x + 1, y + 3, x + 6, y + 3, "#e8e8e8")
    px(im, x + 3, y + 3, black)
    px(im, x + 4, y + 3, black)
    band_around_head(im, HEAD, [1], gray)
    # red foot clan emblem: a three-toed foot
    fx, fy, fw, fh = faces(*BODY)["front"]
    red = "#b3161b"
    rect(im, fx + 3, fy + 4, fx + 4, fy + 7, red)
    px(im, fx + 2, fy + 3, red)
    px(im, fx + 3, fy + 2, red)
    px(im, fx + 4, fy + 2, red)
    px(im, fx + 5, fy + 3, red)
    for xx in range(fx, fx + fw):
        px(im, xx, fy + 9, gray)
    for limb in (R_ARM, L_ARM):
        limb_rows(im, limb, [8, 9, 10], gray)
    for limb in (R_LEG, L_LEG):
        limb_rows(im, limb, [8, 9, 10], gray)
    return im


def paint_dummy():
    straw, rope, wood = "#c9a45c", "#8a5a2b", "#6b4a2a"
    im = new(64, 64)
    fill_box(im, *HEAD, "#d8c39a", 0.1, 1)
    fill_box(im, *BODY, straw, 0.18, 2)
    fill_box(im, *R_ARM, straw, 0.18, 3)
    fill_box(im, *L_ARM, straw, 0.18, 4)
    fill_box(im, *R_LEG, wood, 0.1, 5)
    fill_box(im, *L_LEG, wood, 0.1, 6)
    # target on the face
    x, y, w, h = faces(*HEAD)["front"]
    for yy in range(8):
        for xx in range(8):
            d = ((xx - 3.5) ** 2 + (yy - 3.5) ** 2) ** 0.5
            if d < 1.2 or 2.2 < d < 3.2:
                px(im, x + xx, y + yy, "#c02020")
    for arm in (R_ARM, L_ARM):
        limb_rows(im, arm, [2, 7], rope)
    fx, fy, fw, fh = faces(*BODY)["front"]
    for yy in (fy + 3, fy + 8):
        for xx in range(fx, fx + fw):
            px(im, xx, yy, rope)
    band_around_head(im, HEAD, [7], rope)
    return im


def paint_player_shell():
    im = new(32, 32)
    shellc = TURTLES["raphael"][3]
    sf = faces(0, 0, 10, 13, 3)
    for k in ("top", "bottom", "right", "left", "front"):
        x, y, w, h = sf[k]
        noisy(im, x, y, w, h, "#b89a5c" if k != "front" else shade(shellc, 0.6), 0.08, 13)
    x, y, w, h = sf["back"]
    shell_pattern(im, x, y, w, h, shellc, True, 21)
    return im


# ----------------------------------------------------------------------------- armor layers (64x32)

def paint_mask_armor():
    im = new(64, 32)
    red = TURTLES["raphael"][1]
    band_around_head(im, HEAD, [2, 3, 4], red)
    x, y, w, h = faces(*HEAD)["front"]
    for ex in (1, 2, 5, 6):
        px(im, x + ex, y + 3, "#ffffff")
    px(im, x + 2, y + 3, "#101010")
    px(im, x + 5, y + 3, "#101010")
    for i in range(8):
        px(im, x + i, y + 4, shade(red, 0.75))
    bx, by, _, _ = faces(*HEAD)["back"]
    rect(im, bx + 3, by + 2, bx + 4, by + 5, shade(red, 0.8))
    px(im, bx + 3, by + 6, red)
    px(im, bx + 4, by + 7, red)
    return im


def paint_shell_armor():
    im = new(64, 32)
    skin, mask, plas, shellc = TURTLES["raphael"]
    plastron(im, BODY, plas, None)
    bx, by, bw, bh = faces(*BODY)["back"]
    shell_pattern(im, bx, by, bw, bh, shellc, True, 4)
    for side in ("right", "left"):
        sx, sy, sw, sh = faces(*BODY)[side]
        noisy(im, sx, sy, sw, sh, shade(shellc, 0.9), 0.05, 9)
    # elbow pads on the armour arms
    limb_rows(im, R_ARM, [5, 6], PAD)
    return im


# ----------------------------------------------------------------------------- items (16x16)

def item(draw):
    im = new(16, 16)
    draw(im)
    return im


def draw_sai(im):
    silver, dark, handle = "#dfe3e8", "#8a9098", "#b01818"
    # handle bottom-left, wrapped in red
    for i in range(4):
        px(im, 1 + i, 14 - i, handle)
        px(im, 2 + i, 14 - i, shade(handle, 0.7))
    px(im, 1, 15, "#cfcfcf")
    # guard prongs
    line(im, 4, 9, 6, 7, dark)
    line(im, 6, 12, 8, 10, dark)
    line(im, 3, 8, 4, 6, silver)
    line(im, 7, 13, 9, 12, silver)
    px(im, 4, 5, silver)
    px(im, 10, 12, silver)
    # long centre blade to the top-right
    line(im, 5, 10, 14, 1, silver)
    line(im, 6, 10, 14, 2, dark)
    px(im, 15, 0, "#ffffff")


def draw_katana(im):
    blade, edge, guard, handle = "#e8ecf0", "#9aa2aa", "#d4a82a", "#1c2a6a"
    line(im, 5, 10, 15, 0, blade)
    line(im, 6, 10, 15, 1, edge)
    line(im, 4, 9, 14, 0, shade(blade, 0.9))
    rect(im, 3, 10, 5, 12, guard)
    px(im, 4, 11, "#101010")
    for i in range(4):
        px(im, 3 - i + 0, 12 + i, handle)
        px(im, 2 - i + 1, 13 + i, shade(handle, 1.4) if i % 2 else handle)
    px(im, 0, 15, "#101010")


def draw_bo(im):
    wood, dark, tape = "#8a5a2b", "#5a3a1a", "#e0d6b0"
    for i in range(15):
        px(im, i, 15 - i, wood)
        px(im, i + 1, 15 - i, dark)
    for k in (1, 7, 13):
        px(im, k, 15 - k, tape)
        px(im, k + 1, 15 - k, tape)
        px(im, k + 1, 14 - k, tape)


def draw_nunchucks(im):
    wood, dark, chain = "#d07a2a", "#8a4a16", "#9aa0a8"
    rect(im, 2, 6, 3, 14, wood)
    rect(im, 3, 7, 3, 14, dark)
    for i in range(8):
        px(im, 7 + i // 2, 14 - i, wood)
        px(im, 8 + i // 2, 14 - i, dark)
    line(im, 3, 5, 5, 2, chain)
    line(im, 5, 2, 8, 2, chain)
    line(im, 8, 2, 10, 6, chain)
    rect(im, 2, 5, 3, 5, "#303030")
    rect(im, 10, 7, 11, 7, "#303030")


def draw_shuriken(im):
    steel, dark = "#d7dce2", "#6c737c"
    c = 7.5
    for y in range(16):
        for x in range(16):
            dx, dy = x - c, y - c
            r = (dx * dx + dy * dy) ** 0.5
            ax, ay = abs(dx), abs(dy)
            if (ax < 1.6 and ay < 7.5) or (ay < 1.6 and ax < 7.5) or (r < 3.5):
                px(im, x, y, steel if (x + y) % 3 else dark)
    rect(im, 7, 7, 8, 8, (0, 0, 0, 0))
    for (x, y) in [(7, 0), (8, 15), (0, 8), (15, 7)]:
        px(im, x, y, "#ffffff")


def draw_smoke_bomb(im):
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 9.5) ** 2) ** 0.5
            if d < 5.5:
                px(im, x, y, shade("#2a2a30", 1.0 + (5.5 - d) / 12))
    px(im, 5, 7, "#8a8a95")
    px(im, 6, 6, "#8a8a95")
    line(im, 8, 4, 10, 2, "#c9a45c")
    for (x, y) in [(11, 1), (12, 0), (12, 2), (13, 1), (10, 0)]:
        px(im, x, y, "#b0b0b8")
    px(im, 11, 1, "#ff9020")


def draw_tphone(im):
    case, screen = "#3e7a33", "#101418"
    rect(im, 4, 1, 11, 14, case)
    rect(im, 5, 2, 10, 11, screen)
    rect(im, 4, 1, 11, 1, shade(case, 1.3))
    # green T on the screen
    rect(im, 6, 4, 9, 4, "#6dff6d")
    rect(im, 7, 5, 8, 9, "#6dff6d")
    rect(im, 7, 12, 8, 13, "#d9c27a")
    px(im, 4, 14, shade(case, 0.7))
    px(im, 11, 14, shade(case, 0.7))


def draw_canister(im, liquid="#5aff3a"):
    cap, glass = "#9aa0a8", "#e8fff0"
    rect(im, 5, 1, 10, 2, cap)
    rect(im, 5, 13, 10, 14, cap)
    rect(im, 6, 0, 9, 0, shade(cap, 0.8))
    rect(im, 5, 3, 10, 12, liquid)
    for y in range(3, 13):
        px(im, 5, y, shade(liquid, 0.7))
        px(im, 10, y, shade(liquid, 0.7))
        px(im, 6, y, shade(liquid, 1.25))
    for (x, y) in [(8, 5), (7, 8), (9, 10), (8, 11)]:
        px(im, x, y, glass)
    rect(im, 4, 2, 4, 13, shade(cap, 0.6))
    rect(im, 11, 2, 11, 13, shade(cap, 0.6))


def draw_pizza(im, special=False):
    crust, cheese, pep = "#c8843a", "#f7d154", "#c0301e"
    for y in range(16):
        for x in range(16):
            # slice: point at the bottom, crust along the top
            half = (15 - y) * 0.5
            if y >= 2 and abs(x - 7.5) <= half and y < 15:
                px(im, x, y, cheese)
            if 1 <= y <= 3 and abs(x - 7.5) <= half + 0.5:
                px(im, x, y, crust if y < 3 else shade(crust, 1.1))
    if special:
        for (x, y, c) in [(5, 5, "#ff3fa0"), (6, 5, "#ff3fa0"), (9, 6, "#3fd0ff"), (10, 7, "#3fd0ff"),
                          (7, 8, "#6dff3f"), (8, 9, "#6dff3f"), (7, 11, "#ff9f30"), (9, 4, "#8a3fff")]:
            px(im, x, y, c)
    else:
        for (x, y) in [(5, 5), (9, 5), (7, 8), (8, 11), (10, 7)]:
            px(im, x, y, pep)
            px(im, x + 1, y, shade(pep, 0.8))


def draw_blaster(im):
    body, dark, glow = "#e6e8ec", "#5a5f68", "#ff78cf"
    rect(im, 3, 6, 13, 8, body)
    rect(im, 3, 8, 13, 8, dark)
    rect(im, 13, 6, 15, 7, glow)
    rect(im, 4, 9, 6, 13, dark)
    rect(im, 8, 9, 8, 10, dark)
    rect(im, 6, 5, 10, 5, "#c060a0")
    px(im, 15, 6, "#ffffff")


def draw_bolt(im):
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + ((y - 7.5) * 1.6) ** 2) ** 0.5
            if d < 6:
                a = int(255 * min(1, (6 - d) / 3))
                px(im, x, y, (255, 120 + int((6 - d) * 20), 210, a))
    rect(im, 6, 7, 9, 8, "#ffffff")


def draw_mask_icon(im):
    red = "#d01a1a"
    rect(im, 1, 5, 14, 9, red)
    rect(im, 1, 9, 14, 9, shade(red, 0.7))
    rect(im, 3, 6, 5, 7, "#ffffff")
    rect(im, 10, 6, 12, 7, "#ffffff")
    line(im, 13, 9, 15, 14, red)
    line(im, 12, 9, 13, 15, shade(red, 0.8))


def draw_shell_icon(im):
    base = TURTLES["raphael"][3]
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) / 7) ** 2 + ((y - 7.5) / 7.5) ** 2
            if d <= 1:
                px(im, x, y, base)
    shell_pattern(im, 3, 2, 10, 12, base, True, 5)
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) / 7) ** 2 + ((y - 7.5) / 7.5) ** 2
            if 0.8 < d <= 1:
                px(im, x, y, "#b89a5c")


# ----------------------------------------------------------------------------- blocks (16x16)

def block_manhole():
    im = new(16, 16)
    noisy(im, 0, 0, 16, 16, "#4a4d52", 0.06, 1)
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            if 6.2 < d < 7.6:
                px(im, x, y, "#2c2e32")
            elif d <= 6.2 and (x + y) % 3 == 0:
                px(im, x, y, "#6a6e75")
            elif d <= 6.2 and (x - y) % 3 == 0:
                px(im, x, y, "#3a3d42")
    rect(im, 4, 7, 11, 8, "#2c2e32")
    for x in (5, 7, 9):
        px(im, x, 7, "#8a8e95")
    return im


def block_ooze():
    im = new(16, 16)
    noisy(im, 0, 0, 16, 16, "#48e02a", 0.15, 2)
    rnd = random.Random(5)
    for _ in range(9):
        x, y = rnd.randrange(16), rnd.randrange(16)
        px(im, x, y, "#c8ff9a")
        px(im, (x + 1) % 16, y, "#8aff5a")
    for _ in range(6):
        x, y = rnd.randrange(16), rnd.randrange(16)
        px(im, x, y, "#1f8a14")
    return im


def block_tank():
    im = new(16, 16)
    rect(im, 0, 0, 15, 15, "#3aff2a")
    noisy(im, 1, 2, 14, 12, "#44f032", 0.12, 3)
    rect(im, 0, 0, 15, 1, "#8a9098")
    rect(im, 0, 14, 15, 15, "#8a9098")
    rect(im, 0, 0, 0, 15, "#6a7078")
    rect(im, 15, 0, 15, 15, "#6a7078")
    for (x, y) in [(4, 11), (5, 7), (10, 9), (11, 4), (7, 3)]:
        px(im, x, y, "#e0ffe0")
    rect(im, 2, 2, 2, 13, "#b0ffb0")
    return im


def block_kraang():
    im = new(16, 16)
    noisy(im, 0, 0, 16, 16, "#6a2a7a", 0.08, 4)
    for i in range(16):
        px(im, i, 0, "#2a0a3a")
        px(im, 0, i, "#2a0a3a")
        px(im, i, 8, "#4a1a5a")
        px(im, 8, i, "#4a1a5a")
    for (x, y) in [(4, 4), (12, 4), (4, 12), (12, 12)]:
        rect(im, x - 1, y - 1, x, y, "#ff78cf")
        px(im, x - 1, y - 1, "#ffd0f0")
    return im


def block_pizza_top(empty=False):
    im = new(16, 16)
    noisy(im, 0, 0, 16, 16, "#c9a270", 0.05, 6)
    rect(im, 0, 0, 15, 0, "#a07a4a")
    rect(im, 0, 15, 15, 15, "#a07a4a")
    rect(im, 0, 0, 0, 15, "#a07a4a")
    rect(im, 15, 0, 15, 15, "#a07a4a")
    if empty:
        for (x, y) in [(5, 6), (6, 6), (9, 9), (10, 10), (7, 11)]:
            px(im, x, y, "#9a7a4a")
        return im
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            if d < 6.8:
                px(im, x, y, "#f7d154" if d < 5.6 else "#c8843a")
    for (x, y) in [(5, 5), (9, 4), (10, 9), (5, 10), (8, 7), (7, 11)]:
        px(im, x, y, "#c0301e")
        px(im, x + 1, y, "#9a2414")
    line(im, 2, 8, 13, 8, "#e0b040")
    line(im, 8, 2, 8, 13, "#e0b040")
    return im


def block_pizza_side():
    im = new(16, 16)
    noisy(im, 0, 0, 16, 16, "#c9a270", 0.05, 7)
    for x in range(1, 15, 3):
        px(im, x, 13, "#c0301e")
        px(im, x + 1, 13, "#c0301e")
    return im


def gui_arrow():
    im = new(16, 16)
    green, dark = "#5aff5a", "#0a3a0a"
    pts = []
    for y in range(16):
        for x in range(16):
            # arrow pointing up: triangle head + stem
            head = y <= 8 and abs(x - 7.5) <= (y + 0.5) * 0.9
            stem = y > 8 and 5 <= x <= 10 and y <= 14
            if head or stem:
                pts.append((x, y))
    s = set(pts)
    for (x, y) in pts:
        edge = any((x + dx, y + dy) not in s for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        px(im, x, y, dark if edge else green)
    return im


def logo():
    im = new(128, 128)
    for y in range(128):
        for x in range(128):
            d = ((x - 63.5) / 60) ** 2 + ((y - 63.5) / 62) ** 2
            if d <= 1:
                px(im, x, y, "#3e7a33")
    shell = new(10, 13)
    shell_pattern(shell, 0, 0, 10, 13, "#44502a", True, 3)
    big = shell.resize((80, 104), Image.NEAREST)
    im.alpha_composite(big, (24, 12))
    rect(im, 14, 50, 113, 72, "#d01a1a")
    rect(im, 34, 56, 48, 64, "#ffffff")
    rect(im, 79, 56, 93, 64, "#ffffff")
    return im


def main():
    for name in TURTLES:
        save(paint_turtle(name), "entity", name + ".png")
    save(paint_turtle("raphael", for_player=True), "entity", "raphael.png")
    save(paint_turtle("raphael", for_player=False), "entity", "raphael_npc.png")
    save(paint_splinter(), "entity", "splinter.png")
    save(paint_april(), "entity", "april.png")
    save(paint_kraang(False), "entity", "kraang_droid.png")
    save(paint_kraang(True), "entity", "kraang_prime.png")
    save(paint_foot(), "entity", "foot_ninja.png")
    save(paint_dummy(), "entity", "training_dummy.png")
    save(paint_player_shell(), "entity", "player_shell.png")

    save(paint_mask_armor(), "models", "armor", "raph_mask.png")
    save(paint_shell_armor(), "models", "armor", "turtle_shell.png")

    items = {
        "sai": draw_sai, "katana": draw_katana, "bo_staff": draw_bo, "nunchucks": draw_nunchucks,
        "shuriken": draw_shuriken, "smoke_bomb": draw_smoke_bomb, "t_phone": draw_tphone,
        "mutagen_canister": draw_canister, "retro_mutagen": lambda im: draw_canister(im, "#3ad0ff"),
        "pizza_slice": draw_pizza, "mikey_special_pizza": lambda im: draw_pizza(im, True),
        "kraang_blaster": draw_blaster, "kraang_bolt": draw_bolt,
        "raph_mask": draw_mask_icon, "turtle_shell": draw_shell_icon,
    }
    for name, fn in items.items():
        save(item(fn), "item", name + ".png")

    save(block_manhole(), "block", "manhole_cover.png")
    save(block_ooze(), "block", "mutagen_ooze.png")
    save(block_tank(), "block", "mutagen_tank.png")
    save(block_kraang(), "block", "kraang_panel.png")
    save(block_pizza_top(), "block", "pizza_box_top.png")
    save(block_pizza_top(True), "block", "pizza_box_empty.png")
    save(block_pizza_side(), "block", "pizza_box_side.png")
    save(gui_arrow(), "gui", "arrow.png")

    logo_path = os.path.join(os.path.dirname(__file__), "..", "src", "main", "resources", "turtlepower_logo.png")
    logo().save(logo_path)
    print("textures written to", os.path.abspath(ROOT))


if __name__ == "__main__":
    main()
