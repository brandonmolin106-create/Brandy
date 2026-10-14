#!/usr/bin/env python3
"""
Draws every texture Echo Strike needs (16x16 item icons, the armor layer, the operative skins)
and writes the item model JSON files. Run from anywhere:

    python3 echo-strike/tools/gen_assets.py
"""
import json
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "src", "main", "resources", "assets", "echostrike")
TEX = os.path.join(RES, "textures")

P = {
    "k": (42, 42, 46, 255),      # dark gray
    "g": (85, 85, 92, 255),      # gray
    "l": (138, 138, 146, 255),   # light gray
    "h": (184, 184, 192, 255),   # highlight
    "b": (17, 17, 20, 255),      # black
    "w": (107, 74, 43, 255),     # wood
    "W": (140, 100, 60, 255),    # light wood
    "r": (208, 32, 42, 255),     # red
    "o": (224, 138, 42, 255),    # orange
    "y": (212, 178, 74, 255),    # brass
    "n": (74, 122, 58, 255),     # green
    "d": (47, 79, 40, 255),      # dark green
    "s": (74, 106, 138, 255),    # steel blue
    "c": (120, 170, 220, 255),   # lens
    "e": (240, 240, 240, 255),   # white
    "t": (150, 120, 80, 255),    # cardboard
    "m": (90, 60, 40, 255),      # dark cardboard
}


def new(w=16, h=16):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def rect(img, x0, y0, x1, y1, color):
    """Inclusive rectangle."""
    ImageDraw.Draw(img).rectangle([x0, y0, x1, y1], fill=P[color] if isinstance(color, str) else color)


def px(img, x, y, color):
    img.putpixel((x, y), P[color] if isinstance(color, str) else color)


def outline(img):
    """One pixel dark outline around everything opaque, so icons read well on any background."""
    w, h = img.size
    src = img.copy()
    for x in range(w):
        for y in range(h):
            if src.getpixel((x, y))[3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and src.getpixel((nx, ny))[3] != 0:
                        img.putpixel((x, y), (20, 20, 24, 255))
                        break
    return img


def save(img, *path):
    out = os.path.join(TEX, *path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)


# ----------------------------------------------------------------------------- guns
#
# Each gun is a list of parts: (x0, y0, x1, y1, color, depth). The rectangle is in 16x16 icon
# pixels (inclusive, y down, muzzle to the right); depth is how thick that part is in the 3D
# model. The same list draws the 2D icon and builds the 3D JSON model.

BODY, BARREL, MAG, GRIP, STOCK, RAIL, SCOPE, THIN = 3.0, 1.6, 2.2, 2.2, 2.6, 1.2, 2.4, 1.0

GUNS = {
    "g18": [
        (3, 5, 12, 6, "k", BODY),      # polymer slide
        (3, 7, 11, 8, "g", BODY),      # frame
        (13, 6, 13, 6, "k", BARREL),   # muzzle
        (6, 9, 8, 13, "k", GRIP),      # grip + extended mag
        (4, 9, 5, 9, "k", THIN),       # trigger guard
        (5, 10, 5, 10, "k", THIN),
        (10, 5, 10, 5, "r", THIN),     # accent
        (4, 4, 4, 4, "l", THIN),       # rear sight
    ],
    "deagle": [
        (2, 4, 13, 6, "h", BODY),      # big chrome slide
        (2, 7, 12, 8, "l", BODY),      # frame
        (13, 5, 14, 6, "g", BARREL),   # muzzle
        (7, 9, 9, 12, "w", GRIP),      # wood grip
        (4, 9, 6, 9, "k", THIN),       # trigger guard
        (6, 10, 6, 10, "k", THIN),
        (3, 5, 3, 5, "r", THIN),
    ],
    "mp5": [
        (0, 7, 2, 8, "k", STOCK),      # collapsed stock
        (2, 6, 11, 8, "k", BODY),      # body
        (3, 5, 10, 5, "g", RAIL),      # top
        (11, 6, 15, 7, "g", BARREL),   # barrel
        (7, 9, 8, 13, "k", MAG),       # curved mag
        (4, 9, 5, 12, "k", GRIP),      # grip
        (5, 7, 5, 7, "r", THIN),
        (12, 5, 13, 5, "l", THIN),
    ],
    "ump45": [
        (0, 6, 2, 9, "k", STOCK),      # folding stock
        (2, 6, 11, 8, "g", BODY),      # body
        (3, 5, 12, 5, "l", RAIL),      # rail
        (12, 6, 15, 7, "k", BARREL),   # barrel
        (7, 9, 8, 12, "k", MAG),       # mag
        (4, 9, 5, 12, "k", GRIP),      # grip
        (10, 7, 10, 7, "r", THIN),
        (13, 5, 14, 5, "l", THIN),
    ],
    "vector": [
        (1, 6, 3, 7, "k", STOCK),      # stock
        (3, 5, 12, 8, "k", BODY),      # chunky body
        (4, 5, 11, 5, "g", RAIL),      # top rail
        (12, 6, 15, 6, "g", BARREL),   # barrel
        (8, 9, 9, 13, "k", MAG),       # mag
        (5, 9, 6, 11, "k", GRIP),      # grip
        (10, 9, 11, 9, "g", GRIP),     # foregrip
        (4, 7, 4, 7, "r", THIN),
    ],
    "ak47": [
        (0, 7, 3, 9, "w", STOCK),      # stock
        (3, 6, 10, 8, "g", BODY),      # receiver
        (8, 7, 11, 8, "W", BODY),      # handguard
        (10, 5, 14, 5, "l", RAIL),     # gas tube
        (11, 6, 15, 6, "k", BARREL),   # barrel
        (6, 9, 7, 10, "k", MAG),       # curved mag
        (7, 11, 8, 12, "k", MAG),
        (4, 9, 5, 11, "k", GRIP),      # grip
        (9, 6, 9, 6, "r", THIN),
        (4, 6, 6, 6, "h", THIN),
    ],
    "m4a1": [
        (0, 7, 3, 8, "k", STOCK),      # collapsible stock
        (3, 6, 10, 8, "g", BODY),      # receiver
        (4, 5, 12, 5, "l", RAIL),      # flat top rail
        (8, 7, 12, 8, "k", BODY),      # rail handguard
        (12, 6, 15, 6, "k", BARREL),   # barrel
        (6, 9, 7, 12, "k", MAG),       # straight mag
        (4, 9, 5, 11, "k", GRIP),      # grip
        (9, 6, 9, 6, "r", THIN),
        (7, 4, 8, 4, "k", THIN),       # carry handle sight
    ],
    "m870": [
        (0, 7, 3, 9, "w", STOCK),      # stock
        (3, 6, 7, 8, "g", BODY),       # receiver
        (6, 5, 15, 6, "k", BARREL),    # barrel
        (7, 7, 14, 7, "l", BARREL),    # tube
        (8, 8, 11, 9, "W", GRIP),      # pump
        (5, 9, 6, 10, "k", THIN),      # trigger
        (4, 6, 4, 6, "r", THIN),
    ],
    "awm": [
        (0, 8, 2, 10, "d", STOCK),     # green stock
        (2, 7, 9, 8, "d", BODY),       # body
        (9, 7, 15, 7, "k", BARREL),    # barrel
        (5, 4, 10, 5, "k", SCOPE),     # scope
        (10, 4, 10, 4, "c", SCOPE),    # lens
        (5, 4, 5, 4, "c", SCOPE),
        (7, 6, 7, 6, "l", THIN),       # mount
        (4, 9, 5, 11, "k", GRIP),      # grip
        (11, 8, 11, 10, "k", THIN),    # bipod
        (13, 8, 13, 10, "k", THIN),
        (3, 7, 3, 7, "r", THIN),
    ],
    "m249": [
        (0, 7, 2, 8, "k", STOCK),      # stock
        (2, 6, 9, 8, "g", BODY),       # body
        (9, 5, 13, 5, "l", RAIL),      # shroud
        (10, 6, 15, 6, "k", BARREL),   # barrel
        (4, 9, 7, 12, "d", MAG),       # box mag
        (5, 10, 6, 10, "n", THIN),
        (8, 9, 9, 11, "k", GRIP),      # grip
        (12, 7, 12, 10, "k", THIN),    # bipod
        (14, 7, 14, 10, "k", THIN),
        (3, 6, 3, 6, "r", THIN),
    ],
}


def gun_icon(parts):
    i = new()
    for x0, y0, x1, y1, color, _ in parts:
        rect(i, x0, y0, x1, y1, color)
    return outline(i)


# The 3D models paint every cube from one 16x16 palette texture: 4x4 swatches, 4 pixels each.
PALETTE_ORDER = ["k", "g", "l", "h", "b", "w", "W", "r", "o", "y", "n", "d", "s", "c", "e", "t"]


def palette_texture():
    i = new()
    for n, key in enumerate(PALETTE_ORDER):
        cx, cy = (n % 4) * 4, (n // 4) * 4
        rect(i, cx, cy, cx + 3, cy + 3, key)
    return i


def swatch_uv(key):
    n = PALETTE_ORDER.index(key)
    cx, cy = (n % 4) * 4, (n // 4) * 4
    return [cx + 1, cy + 1, cx + 3, cy + 3]


# How the gun sits in the hand, in the GUI and on the ground. The model points its muzzle at +X.
GUN_DISPLAY = {
    # First person: the hand space looks down -Z, so the muzzle (+X) must turn to -Z.
    "firstperson_righthand": {"rotation": [0, 90, 0], "translation": [-2.0, 3.5, 0.0], "scale": [0.7, 0.7, 0.7]},
    "firstperson_lefthand": {"rotation": [0, -90, 0], "translation": [2.0, 3.5, 0.0], "scale": [0.7, 0.7, 0.7]},
    # Third person: +Z of the hand space points forward along the arm.
    "thirdperson_righthand": {"rotation": [0, -90, 0], "translation": [0, 3.0, 1.5], "scale": [0.8, 0.8, 0.8]},
    "thirdperson_lefthand": {"rotation": [0, 90, 0], "translation": [0, 3.0, 1.5], "scale": [0.8, 0.8, 0.8]},
    "gui": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1.0, 1.0, 1.0]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
    "fixed": {"rotation": [0, 180, 0], "translation": [0, 0, 0], "scale": [1.0, 1.0, 1.0]},
}


def gun_model(parts):
    elements = []
    for x0, y0, x1, y1, color, depth in parts:
        uv = swatch_uv(color)
        faces = {side: {"uv": uv, "texture": "#p"} for side in ("north", "south", "east", "west", "up", "down")}
        elements.append({
            "from": [x0, 15 - y1, round(8 - depth / 2, 3)],
            "to": [x1 + 1, 16 - y0, round(8 + depth / 2, 3)],
            "faces": faces,
        })
    return {
        "credit": "Echoes in the Dark - generated by tools/gen_assets.py",
        "gui_light": "front",
        "textures": {"particle": "echostrike:item/gun_palette", "p": "echostrike:item/gun_palette"},
        "elements": elements,
        "display": GUN_DISPLAY,
    }


def knife():
    i = new()
    for n in range(8):
        px(i, 7 + n, 8 - n, "l")
        px(i, 8 + n, 8 - n, "h")
        if n < 7:
            px(i, 7 + n, 9 - n, "l")
    for n in range(4):
        px(i, 3 + n, 13 - n, "k")
        px(i, 4 + n, 13 - n, "k")
        px(i, 3 + n, 12 - n, "b")
    px(i, 6, 9, "r")
    px(i, 7, 9, "r")
    return outline(i)


# ----------------------------------------------------------------------------- ammo & gear

def ammo_box(base, dark, stripe, bullets):
    i = new()
    rect(i, 3, 6, 12, 13, base)
    rect(i, 3, 6, 12, 7, dark)
    rect(i, 3, 10, 12, 10, stripe)
    for n in range(bullets):
        x = 4 + n * 2
        px(i, x, 4, "y")
        px(i, x, 5, "o")
    return outline(i)


def light_ammo():
    return ammo_box("t", "m", "r", 4)


def heavy_ammo():
    return ammo_box("k", "b", "o", 4)


def shotgun_shells():
    i = new()
    for n in range(4):
        x = 3 + n * 3
        rect(i, x, 4, x + 1, 11, "r")
        rect(i, x, 10, x + 1, 12, "y")
    return outline(i)


def sniper_rounds():
    i = new()
    for n in range(3):
        x = 3 + n * 4
        rect(i, x, 3, x + 1, 11, "y")
        rect(i, x, 2, x + 1, 2, "o")
        rect(i, x, 10, x + 1, 13, "w")
    return outline(i)


def grenade():
    i = new()
    ImageDraw.Draw(i).ellipse([3, 5, 12, 14], fill=P["d"])
    ImageDraw.Draw(i).ellipse([5, 7, 10, 12], outline=P["n"])
    rect(i, 7, 2, 9, 4, "k")
    rect(i, 9, 3, 11, 3, "l")
    px(i, 6, 3, "l")
    return outline(i)


def medkit():
    i = new()
    rect(i, 2, 5, 13, 13, "e")
    rect(i, 6, 3, 9, 4, "k")
    rect(i, 7, 7, 8, 11, "r")
    rect(i, 5, 8, 10, 9, "r")
    rect(i, 2, 5, 13, 5, "h")
    return outline(i)


def armor_plate():
    i = new()
    rect(i, 3, 3, 12, 12, "g")
    rect(i, 4, 4, 11, 11, "l")
    rect(i, 5, 12, 10, 13, "g")
    rect(i, 4, 7, 11, 7, "r")
    return outline(i)


def helmet():
    i = new()
    ImageDraw.Draw(i).ellipse([3, 3, 12, 12], fill=P["k"])
    rect(i, 3, 8, 12, 9, "k")
    rect(i, 4, 9, 11, 10, "r")
    rect(i, 5, 4, 9, 4, "g")
    return outline(i)


def vest():
    i = new()
    rect(i, 3, 3, 12, 13, "k")
    rect(i, 3, 3, 5, 4, (0, 0, 0, 0))
    rect(i, 10, 3, 12, 4, (0, 0, 0, 0))
    rect(i, 6, 3, 9, 5, (0, 0, 0, 0))
    rect(i, 4, 7, 6, 9, "g")
    rect(i, 9, 7, 11, 9, "g")
    rect(i, 6, 10, 9, 12, "g")
    rect(i, 7, 6, 8, 6, "r")
    return outline(i)


# ----------------------------------------------------------------------------- armor layer (64x32)

def armor_layer():
    i = new(64, 32)
    dark, mid, acc = P["k"], P["g"], P["r"]
    # Helmet: all faces of the head box.
    rect(i, 8, 0, 23, 7, dark)      # top/bottom
    rect(i, 0, 8, 31, 15, dark)     # sides
    rect(i, 8, 11, 15, 12, acc)     # visor stripe on the front face
    rect(i, 16, 11, 23, 12, mid)
    # Chest: body box.
    rect(i, 20, 16, 27, 19, dark)   # top/bottom
    rect(i, 16, 20, 39, 31, dark)   # sides
    rect(i, 22, 23, 25, 26, mid)    # chest pouches
    rect(i, 21, 27, 26, 29, mid)
    rect(i, 23, 21, 24, 21, acc)
    # Arms: both arms use the right arm box in the armor layout.
    rect(i, 44, 16, 51, 19, dark)
    rect(i, 40, 20, 55, 31, dark)
    rect(i, 40, 22, 55, 23, mid)
    # Legs + boots regions left empty (no leg armor in the mod).
    return i


# ----------------------------------------------------------------------------- operative skins (64x64)

def skin(team):
    suit = [(38, 40, 46), (30, 36, 60), (58, 64, 42), (70, 32, 36)][team]
    accent = [(208, 32, 42), (60, 140, 230), (220, 190, 60), (240, 240, 240)][team]
    skinc = (205, 160, 120, 255)
    i = new(64, 64)
    suit = suit + (255,)
    dark = tuple(max(0, c - 18) for c in suit[:3]) + (255,)
    light = tuple(min(255, c + 22) for c in suit[:3]) + (255,)
    accent = accent + (255,)

    # head: balaclava, red visor band on the front face
    rect(i, 8, 0, 23, 7, dark)
    rect(i, 0, 8, 31, 15, dark)
    rect(i, 8, 11, 15, 12, accent)
    rect(i, 10, 11, 10, 12, (10, 10, 12, 255))
    rect(i, 13, 11, 13, 12, (10, 10, 12, 255))
    # hat layer: headset band
    rect(i, 32, 8, 63, 9, (20, 20, 24, 255))
    # body
    rect(i, 20, 16, 27, 19, suit)
    rect(i, 16, 20, 39, 31, suit)
    rect(i, 20, 20, 27, 31, light)      # chest front: plate carrier
    rect(i, 21, 22, 26, 29, dark)
    rect(i, 22, 24, 23, 25, accent)
    rect(i, 24, 26, 25, 27, light)
    rect(i, 32, 20, 39, 31, light)      # back
    # right arm (classic box at 40,16)
    rect(i, 44, 16, 51, 19, suit)
    rect(i, 40, 20, 55, 31, suit)
    rect(i, 44, 28, 47, 31, skinc)      # bare hands? gloves: keep dark
    rect(i, 44, 28, 47, 31, dark)
    rect(i, 40, 21, 55, 22, accent)     # armband
    # right leg (0,16)
    rect(i, 4, 16, 11, 19, dark)
    rect(i, 0, 20, 15, 31, dark)
    rect(i, 0, 29, 15, 31, (20, 20, 24, 255))   # boots
    rect(i, 4, 24, 7, 26, suit)        # knee pad
    # left leg (16,48)
    rect(i, 20, 48, 27, 51, dark)
    rect(i, 16, 52, 31, 63, dark)
    rect(i, 16, 61, 31, 63, (20, 20, 24, 255))
    rect(i, 20, 56, 23, 58, suit)
    # left arm (32,48)
    rect(i, 36, 48, 43, 51, suit)
    rect(i, 32, 52, 47, 63, suit)
    rect(i, 36, 60, 39, 63, dark)
    return i


# ----------------------------------------------------------------------------- models

HANDHELD = ["combat_knife"]
GENERATED = ["light_ammo", "heavy_ammo", "shotgun_shells", "sniper_rounds", "frag_grenade", "medkit",
             "armor_plate", "strike_helmet", "strike_vest"]


def write_models():
    d = os.path.join(RES, "models", "item")
    os.makedirs(d, exist_ok=True)
    for name in HANDHELD:
        with open(os.path.join(d, name + ".json"), "w") as f:
            json.dump({"parent": "minecraft:item/handheld", "textures": {"layer0": "echostrike:item/" + name}}, f, indent=2)
    for name in GENERATED:
        with open(os.path.join(d, name + ".json"), "w") as f:
            json.dump({"parent": "minecraft:item/generated", "textures": {"layer0": "echostrike:item/" + name}}, f, indent=2)
    with open(os.path.join(d, "operative_spawn_egg.json"), "w") as f:
        json.dump({"parent": "minecraft:item/template_spawn_egg"}, f, indent=2)
    for name, parts in GUNS.items():
        with open(os.path.join(d, name + ".json"), "w") as f:
            json.dump(gun_model(parts), f, indent=1)


def main():
    icons = {
        "combat_knife": knife, "light_ammo": light_ammo, "heavy_ammo": heavy_ammo, "shotgun_shells": shotgun_shells,
        "sniper_rounds": sniper_rounds, "frag_grenade": grenade, "medkit": medkit, "armor_plate": armor_plate,
        "strike_helmet": helmet, "strike_vest": vest,
    }
    for name, fn in icons.items():
        save(fn(), "item", name + ".png")
    for name, parts in GUNS.items():
        save(gun_icon(parts), "item", name + ".png")   # kept for docs and the icon contact sheet
    save(palette_texture(), "item", "gun_palette.png")
    save(armor_layer(), "models", "armor", "strike_layer_1.png")
    save(armor_layer(), "models", "armor", "strike_layer_2.png")
    for team in range(4):
        save(skin(team), "entity", f"operative_{team}.png")
    write_models()
    print("assets written to", RES)


if __name__ == "__main__":
    main()
