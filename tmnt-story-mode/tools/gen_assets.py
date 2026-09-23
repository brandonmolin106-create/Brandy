#!/usr/bin/env python3
"""
Writes the JSON side of the mod: item/block models, blockstates, the English names, and the
"TMNT New York" world type (a flat harbour world the mod builds the city on).

Run:  python3 tools/gen_assets.py
"""
import json
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "src", "main", "resources")
ASSETS = os.path.join(BASE, "assets", "turtlepower")
DATA = os.path.join(BASE, "data")
MOD = "turtlepower"


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def item_model(name, parent="minecraft:item/generated", texture=None):
    obj = {"parent": parent}
    if parent in ("minecraft:item/generated", "minecraft:item/handheld"):
        obj["textures"] = {"layer0": texture or f"{MOD}:item/{name}"}
    write(os.path.join(ASSETS, "models", "item", name + ".json"), obj)


HANDHELD = ["sai", "katana", "bo_staff", "nunchucks", "kraang_blaster"]
FLAT = ["shuriken", "smoke_bomb", "t_phone", "mutagen_canister", "retro_mutagen", "pizza_slice",
        "mikey_special_pizza", "kraang_bolt", "raph_mask", "turtle_shell"]
EGGS = ["leonardo", "donatello", "michelangelo", "splinter", "april", "kraang_droid", "kraang_prime",
        "foot_ninja", "training_dummy"]


def trapdoor_state(model_prefix):
    b, t, o = model_prefix + "_bottom", model_prefix + "_top", model_prefix + "_open"
    rot = {"north": 0, "east": 90, "south": 180, "west": 270}
    open_top_y = {"north": 180, "east": 270, "south": 0, "west": 90}
    v = {}
    for f, y in rot.items():
        v[f"facing={f},half=bottom,open=false"] = {"model": b, "y": y} if y else {"model": b}
        v[f"facing={f},half=bottom,open=true"] = {"model": o, "y": y} if y else {"model": o}
        v[f"facing={f},half=top,open=false"] = {"model": t, "y": y} if y else {"model": t}
        v[f"facing={f},half=top,open=true"] = {"model": o, "x": 180, "y": open_top_y[f]}
    return {"variants": v}


def main():
    for n in HANDHELD:
        item_model(n, "minecraft:item/handheld")
    for n in FLAT:
        item_model(n)
    for n in EGGS:
        item_model(n + "_spawn_egg", "minecraft:item/template_spawn_egg")

    models = os.path.join(ASSETS, "models", "block")
    states = os.path.join(ASSETS, "blockstates")

    # Manhole cover (trapdoor).
    for kind in ("bottom", "top", "open"):
        write(os.path.join(models, f"manhole_cover_{kind}.json"), {
            "parent": f"minecraft:block/template_orientable_trapdoor_{kind}",
            "textures": {"texture": f"{MOD}:block/manhole_cover"}})
    write(os.path.join(states, "manhole_cover.json"), trapdoor_state(f"{MOD}:block/manhole_cover"))
    item_model("manhole_cover", f"{MOD}:block/manhole_cover_bottom")

    # Mutagen ooze puddle (1 pixel high).
    tex = f"{MOD}:block/mutagen_ooze"
    write(os.path.join(models, "mutagen_ooze.json"), {
        "parent": "minecraft:block/block",
        "ambientocclusion": False,
        "textures": {"particle": tex, "ooze": tex},
        "elements": [{
            "from": [0, 0, 0], "to": [16, 1, 16],
            "faces": {
                "up": {"uv": [0, 0, 16, 16], "texture": "#ooze"},
                "down": {"uv": [0, 0, 16, 16], "texture": "#ooze", "cullface": "down"},
                "north": {"uv": [0, 15, 16, 16], "texture": "#ooze"},
                "south": {"uv": [0, 15, 16, 16], "texture": "#ooze"},
                "west": {"uv": [0, 15, 16, 16], "texture": "#ooze"},
                "east": {"uv": [0, 15, 16, 16], "texture": "#ooze"}}}]})
    write(os.path.join(states, "mutagen_ooze.json"), {"variants": {"": {"model": f"{MOD}:block/mutagen_ooze"}}})
    item_model("mutagen_ooze", f"{MOD}:block/mutagen_ooze")

    for cube in ("mutagen_tank", "kraang_panel"):
        write(os.path.join(models, cube + ".json"), {
            "parent": "minecraft:block/cube_all", "textures": {"all": f"{MOD}:block/{cube}"}})
        write(os.path.join(states, cube + ".json"), {"variants": {"": {"model": f"{MOD}:block/{cube}"}}})
        item_model(cube, f"{MOD}:block/{cube}")

    # Pizza box.
    for variant, top in (("pizza_box", "pizza_box_top"), ("pizza_box_empty", "pizza_box_empty")):
        write(os.path.join(models, variant + ".json"), {
            "parent": "minecraft:block/block",
            "textures": {"particle": f"{MOD}:block/pizza_box_side", "top": f"{MOD}:block/{top}",
                         "side": f"{MOD}:block/pizza_box_side"},
            "elements": [{
                "from": [1, 0, 1], "to": [15, 3, 15],
                "faces": {
                    "up": {"uv": [1, 1, 15, 15], "texture": "#top"},
                    "down": {"uv": [1, 1, 15, 15], "texture": "#side", "cullface": "down"},
                    "north": {"uv": [1, 13, 15, 16], "texture": "#side"},
                    "south": {"uv": [1, 13, 15, 16], "texture": "#side"},
                    "west": {"uv": [1, 13, 15, 16], "texture": "#side"},
                    "east": {"uv": [1, 13, 15, 16], "texture": "#side"}}}]})
    v = {}
    for f, y in {"north": 0, "east": 90, "south": 180, "west": 270}.items():
        for s in range(9):
            m = f"{MOD}:block/pizza_box_empty" if s == 0 else f"{MOD}:block/pizza_box"
            v[f"facing={f},slices={s}"] = {"model": m, "y": y} if y else {"model": m}
    write(os.path.join(states, "pizza_box.json"), {"variants": v})
    item_model("pizza_box", f"{MOD}:block/pizza_box")

    # Names.
    lang = {
        "itemGroup.turtlepower": "TMNT Turtle Power",
        "item.turtlepower.sai": "Raphael's Sai",
        "item.turtlepower.katana": "Leonardo's Katana",
        "item.turtlepower.bo_staff": "Donatello's Bo Staff",
        "item.turtlepower.nunchucks": "Michelangelo's Nunchucks",
        "item.turtlepower.shuriken": "Shuriken",
        "item.turtlepower.smoke_bomb": "Ninja Smoke Bomb",
        "item.turtlepower.t_phone": "T-Phone",
        "item.turtlepower.mutagen_canister": "Mutagen Canister",
        "item.turtlepower.retro_mutagen": "Retro-Mutagen",
        "item.turtlepower.pizza_slice": "Pepperoni Pizza Slice",
        "item.turtlepower.mikey_special_pizza": "Mikey's Special Pizza",
        "item.turtlepower.kraang_blaster": "Kraang Blaster",
        "item.turtlepower.kraang_bolt": "Kraang Laser Bolt",
        "item.turtlepower.raph_mask": "Raphael's Mask",
        "item.turtlepower.turtle_shell": "Turtle Shell",
        "block.turtlepower.manhole_cover": "Manhole Cover",
        "block.turtlepower.mutagen_ooze": "Mutagen Ooze",
        "block.turtlepower.mutagen_tank": "Mutagen Tank",
        "block.turtlepower.kraang_panel": "Kraang Tech Panel",
        "block.turtlepower.pizza_box": "Pizza Box",
        "entity.turtlepower.leonardo": "Leonardo",
        "entity.turtlepower.donatello": "Donatello",
        "entity.turtlepower.michelangelo": "Michelangelo",
        "entity.turtlepower.splinter": "Master Splinter",
        "entity.turtlepower.april": "April O'Neil",
        "entity.turtlepower.training_dummy": "Training Dummy",
        "entity.turtlepower.kraang_droid": "Kraang Droid",
        "entity.turtlepower.kraang_prime": "Kraang Prime",
        "entity.turtlepower.foot_ninja": "Foot Ninja",
        "entity.turtlepower.shuriken": "Shuriken",
        "entity.turtlepower.smoke_bomb": "Smoke Bomb",
        "entity.turtlepower.kraang_bolt": "Kraang Laser Bolt",
        "generator.turtlepower.new_york": "TMNT New York (Story Mode)",
        "biome.turtlepower.new_york": "New York Harbor",
    }
    for e in EGGS:
        lang[f"item.turtlepower.{e}_spawn_egg"] = lang[f"entity.turtlepower.{e}"] + " Spawn Egg"
    write(os.path.join(ASSETS, "lang", "en_us.json"), lang)

    # ---- data: the TMNT New York world type ----
    write(os.path.join(DATA, MOD, "worldgen", "biome", "new_york.json"), {
        "has_precipitation": True,
        "temperature": 0.7,
        "downfall": 0.6,
        "effects": {
            "sky_color": 7972607,
            "fog_color": 12638463,
            "water_color": 0x3C7489,
            "water_fog_color": 0x1A3A44,
            "grass_color": 0x5E9E45,
            "foliage_color": 0x4E8E3A,
            "mood_sound": {"sound": "minecraft:ambient.cave", "tick_delay": 6000, "block_search_extent": 8, "offset": 2.0},
        },
        "spawners": {
            "monster": [
                {"type": "turtlepower:kraang_droid", "weight": 40, "minCount": 1, "maxCount": 2},
                {"type": "turtlepower:foot_ninja", "weight": 25, "minCount": 1, "maxCount": 2},
                {"type": "minecraft:zombie", "weight": 30, "minCount": 1, "maxCount": 2},
                {"type": "minecraft:spider", "weight": 20, "minCount": 1, "maxCount": 1},
            ],
            "creature": [],
            "ambient": [{"type": "minecraft:bat", "weight": 10, "minCount": 1, "maxCount": 2}],
            "water_creature": [{"type": "minecraft:squid", "weight": 2, "minCount": 1, "maxCount": 2}],
            "water_ambient": [{"type": "minecraft:cod", "weight": 10, "minCount": 2, "maxCount": 4}],
            "underground_water_creature": [],
            "axolotls": [],
            "misc": [],
        },
        "spawn_costs": {},
        "carvers": {},
        "features": [],
    })
    write(os.path.join(DATA, MOD, "worldgen", "world_preset", "new_york.json"), {
        "dimensions": {
            "minecraft:overworld": {
                "type": "minecraft:overworld",
                "generator": {
                    "type": "minecraft:flat",
                    "settings": {
                        "biome": "turtlepower:new_york",
                        "features": False,
                        "lakes": False,
                        "layers": [
                            {"block": "minecraft:bedrock", "height": 1},
                            {"block": "minecraft:stone", "height": 92},
                            {"block": "minecraft:sand", "height": 2},
                            {"block": "minecraft:water", "height": 3},
                        ],
                        "structure_overrides": [],
                    },
                },
            },
            "minecraft:the_nether": {
                "type": "minecraft:the_nether",
                "generator": {"type": "minecraft:noise", "settings": "minecraft:nether",
                              "biome_source": {"type": "minecraft:multi_noise", "preset": "minecraft:nether"}},
            },
            "minecraft:the_end": {
                "type": "minecraft:the_end",
                "generator": {"type": "minecraft:noise", "settings": "minecraft:end",
                              "biome_source": {"type": "minecraft:the_end"}},
            },
        }
    })
    write(os.path.join(DATA, "minecraft", "tags", "worldgen", "world_preset", "normal.json"),
          {"replace": False, "values": ["turtlepower:new_york"]})
    print("assets written")


if __name__ == "__main__":
    main()
