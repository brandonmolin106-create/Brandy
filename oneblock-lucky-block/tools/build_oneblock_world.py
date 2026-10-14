#!/usr/bin/env python3
"""Build the "OneBlock Lucky Block" Minecraft: Java Edition world.

Run:  python3 tools/build_oneblock_world.py

Produces:
  world/OneBlock Lucky Block/      the world save (drop into .minecraft/saves)
  OneBlock_Lucky_Block.zip         the same world, zipped for easy sharing

Everything the map does lives in the datapack this script writes
(data/lucky/function/**.mcfunction and data/lucky/loot_table/**.json).
Requires: python3, nbtlib, Pillow.
"""
from __future__ import annotations

import io
import json
import os
import random
import shutil
import struct
import time
import zipfile
import zlib
from pathlib import Path

import nbtlib
from nbtlib import Byte, Compound, Double, Float, Int, List, Long, String
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
WORLD_NAME = "OneBlock Lucky Block"
WORLD_DIR = ROOT / "world" / WORLD_NAME
ZIP_PATH = ROOT / "OneBlock_Lucky_Block.zip"
PACK_ID = "lucky_oneblock"
DP = WORLD_DIR / "datapacks" / PACK_ID
NS = DP / "data" / "lucky"

# World-save format targets Java 1.21.1; newer versions upgrade it on load.
DATA_VERSION = 3955
VERSION_NAME = "1.21.1"
DATAPACK_FORMAT = 48
RESOURCEPACK_FORMAT = 34

BLOCK = "0 63 0"  # the one block
TOP = "0.5 64 0.5"  # where things spawn (standing on the block)

# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------
# name, start-count, lucky%, chest%, mob%
PHASES = [
    (1, "THE PLAINS", 0, 6, 10, 10),
    (2, "THE CAVES", 60, 8, 10, 12),
    (3, "THE WILD", 150, 9, 10, 12),
    (4, "THE NETHER", 260, 10, 10, 13),
    (5, "THE END & DEEP DARK", 400, 11, 10, 14),
    (6, "LUCKY CHAOS", 560, 13, 10, 14),
]
BOSS_AT = 800

PHASE_COLORS = {1: "green", 2: "gray", 3: "dark_green", 4: "red", 5: "dark_purple", 6: "gold"}
PHASE_FLOOR = {
    1: "minecraft:grass_block",
    2: "minecraft:stone",
    3: "minecraft:moss_block",
    4: "minecraft:netherrack",
    5: "minecraft:end_stone",
    6: "minecraft:gold_block",
}

L = "[persistent=true]"  # leaves must not decay

# Blocks that fall (sand, gravel, anvils, concrete powder, dragon egg...) are
# deliberately absent: they would drop straight into the void.
# Blocks that are unbreakable in survival (bedrock, reinforced deepslate) too.
BLOCKS = {
    1: [
        ("minecraft:grass_block", 20), ("minecraft:dirt", 12), ("minecraft:oak_log", 14),
        ("minecraft:birch_log", 6), ("minecraft:spruce_log", 4), ("minecraft:oak_leaves" + L, 10),
        ("minecraft:birch_leaves" + L, 4), ("minecraft:stone", 10), ("minecraft:cobblestone", 4),
        ("minecraft:coal_ore", 5), ("minecraft:iron_ore", 2), ("minecraft:hay_block", 3),
        ("minecraft:pumpkin", 3), ("minecraft:melon", 3), ("minecraft:mossy_cobblestone", 2),
        ("minecraft:clay", 3), ("minecraft:sandstone", 3), ("minecraft:bookshelf", 1),
        ("minecraft:crafting_table", 1), ("minecraft:podzol", 2), ("minecraft:moss_block", 2),
        ("minecraft:flowering_azalea_leaves" + L, 1), ("minecraft:brown_mushroom_block", 1),
        ("minecraft:red_mushroom_block", 1), ("minecraft:oak_planks", 2), ("minecraft:white_wool", 2),
    ],
    2: [
        ("minecraft:stone", 20), ("minecraft:deepslate", 12), ("minecraft:cobblestone", 6),
        ("minecraft:granite", 5), ("minecraft:andesite", 5), ("minecraft:diorite", 5), ("minecraft:tuff", 5),
        ("minecraft:calcite", 3), ("minecraft:dripstone_block", 4), ("minecraft:coal_ore", 8),
        ("minecraft:iron_ore", 8), ("minecraft:copper_ore", 7), ("minecraft:gold_ore", 4),
        ("minecraft:lapis_ore", 3), ("minecraft:redstone_ore", 3), ("minecraft:deepslate_iron_ore", 4),
        ("minecraft:deepslate_diamond_ore", 1), ("minecraft:diamond_ore", 1), ("minecraft:emerald_ore", 1),
        ("minecraft:amethyst_block", 3), ("minecraft:budding_amethyst", 1), ("minecraft:moss_block", 3),
        ("minecraft:mossy_cobblestone", 3), ("minecraft:oak_log", 5), ("minecraft:dark_oak_log", 3),
        ("minecraft:clay", 2), ("minecraft:raw_iron_block", 1), ("minecraft:raw_copper_block", 1),
        ("minecraft:bone_block", 2), ("minecraft:magma_block", 2), ("minecraft:obsidian", 1),
        ("minecraft:sculk", 1), ("minecraft:cobbled_deepslate", 4),
        ('minecraft:spawner{SpawnData:{entity:{id:"minecraft:zombie"}}}', 1),
    ],
    3: [
        ("minecraft:jungle_log", 8), ("minecraft:jungle_leaves" + L, 5), ("minecraft:acacia_log", 4),
        ("minecraft:mangrove_log", 4), ("minecraft:mangrove_roots", 2), ("minecraft:muddy_mangrove_roots", 2),
        ("minecraft:mud", 4), ("minecraft:packed_mud", 2), ("minecraft:moss_block", 5),
        ("minecraft:bamboo_block", 3), ("minecraft:cherry_log", 4), ("minecraft:cherry_leaves" + L, 3),
        ("minecraft:snow_block", 5), ("minecraft:packed_ice", 4), ("minecraft:blue_ice", 2),
        ("minecraft:spruce_log", 4), ("minecraft:mycelium", 3), ("minecraft:red_mushroom_block", 2),
        ("minecraft:brown_mushroom_block", 2), ("minecraft:mushroom_stem", 1), ("minecraft:melon", 4),
        ("minecraft:pumpkin", 3), ("minecraft:hay_block", 2), ("minecraft:sea_lantern", 2),
        ("minecraft:prismarine", 4), ("minecraft:dark_prismarine", 2), ("minecraft:prismarine_bricks", 2),
        ("minecraft:brain_coral_block", 1), ("minecraft:tube_coral_block", 1), ("minecraft:fire_coral_block", 1),
        ("minecraft:terracotta", 3), ("minecraft:orange_terracotta", 2), ("minecraft:honeycomb_block", 1),
        ("minecraft:honey_block", 1), ("minecraft:slime_block", 1), ("minecraft:bee_nest", 1),
        ("minecraft:coal_ore", 3), ("minecraft:iron_ore", 3), ("minecraft:gold_ore", 2),
        ("minecraft:emerald_ore", 2), ("minecraft:lapis_ore", 2), ("minecraft:diamond_ore", 1),
        ("minecraft:bookshelf", 1), ("minecraft:chiseled_bookshelf", 1), ("minecraft:stone", 5),
        ("minecraft:deepslate", 3), ("minecraft:oak_log", 4), ("minecraft:dark_oak_log", 3),
        ("minecraft:dripstone_block", 2), ("minecraft:rooted_dirt", 2),
    ],
    4: [
        ("minecraft:netherrack", 20), ("minecraft:nether_quartz_ore", 8), ("minecraft:nether_gold_ore", 6),
        ("minecraft:soul_sand", 6), ("minecraft:soul_soil", 5), ("minecraft:basalt", 5),
        ("minecraft:smooth_basalt", 2), ("minecraft:blackstone", 6), ("minecraft:gilded_blackstone", 2),
        ("minecraft:glowstone", 4), ("minecraft:shroomlight", 3), ("minecraft:crimson_stem", 5),
        ("minecraft:warped_stem", 5), ("minecraft:crimson_nylium", 4), ("minecraft:warped_nylium", 4),
        ("minecraft:nether_wart_block", 4), ("minecraft:warped_wart_block", 3), ("minecraft:bone_block", 3),
        ("minecraft:magma_block", 3), ("minecraft:nether_bricks", 4), ("minecraft:red_nether_bricks", 2),
        ("minecraft:ancient_debris", 1), ("minecraft:obsidian", 2), ("minecraft:crying_obsidian", 2),
        ("minecraft:lodestone", 1), ("minecraft:quartz_block", 2), ("minecraft:polished_blackstone_bricks", 2),
        ("minecraft:oak_log", 3), ("minecraft:stone", 3), ("minecraft:iron_ore", 2), ("minecraft:gold_block", 1),
    ],
    5: [
        ("minecraft:end_stone", 20), ("minecraft:end_stone_bricks", 6), ("minecraft:purpur_block", 8),
        ("minecraft:purpur_pillar", 3), ("minecraft:obsidian", 5), ("minecraft:crying_obsidian", 2),
        ("minecraft:sculk", 8), ("minecraft:sculk_catalyst", 2), ("minecraft:deepslate", 6),
        ("minecraft:deepslate_tiles", 3), ("minecraft:deepslate_bricks", 3), ("minecraft:polished_deepslate", 2),
        ("minecraft:amethyst_block", 3), ("minecraft:deepslate_diamond_ore", 3), ("minecraft:deepslate_emerald_ore", 2),
        ("minecraft:deepslate_gold_ore", 3), ("minecraft:deepslate_lapis_ore", 2), ("minecraft:deepslate_redstone_ore", 2),
        ("minecraft:deepslate_iron_ore", 3), ("minecraft:shulker_box", 1), ("minecraft:oak_log", 3),
        ("minecraft:dark_oak_log", 3), ("minecraft:bookshelf", 2), ("minecraft:enchanting_table", 1),
        ("minecraft:ender_chest", 1), ("minecraft:glowstone", 2), ("minecraft:sea_lantern", 2),
        ("minecraft:lapis_block", 1), ("minecraft:gold_block", 1), ("minecraft:diamond_block", 1),
        ("minecraft:emerald_block", 1), ("minecraft:iron_block", 2),
    ],
    6: [
        ("minecraft:oak_log", 5), ("minecraft:spruce_log", 3), ("minecraft:cherry_log", 3), ("minecraft:crimson_stem", 3),
        ("minecraft:grass_block", 6), ("minecraft:stone", 6), ("minecraft:deepslate", 4), ("minecraft:netherrack", 4),
        ("minecraft:end_stone", 4), ("minecraft:diamond_ore", 4), ("minecraft:deepslate_diamond_ore", 3),
        ("minecraft:emerald_ore", 3), ("minecraft:ancient_debris", 2), ("minecraft:gold_block", 2),
        ("minecraft:diamond_block", 1), ("minecraft:emerald_block", 1), ("minecraft:netherite_block", 1),
        ("minecraft:beacon", 1), ("minecraft:iron_block", 2), ("minecraft:lapis_block", 2),
        ("minecraft:redstone_block", 2), ("minecraft:quartz_block", 3), ("minecraft:tnt", 3),
        ("minecraft:glass", 2), ("minecraft:red_concrete", 2), ("minecraft:lime_concrete", 2),
        ("minecraft:light_blue_concrete", 2), ("minecraft:yellow_wool", 2), ("minecraft:magenta_glazed_terracotta", 2),
        ("minecraft:note_block", 2), ("minecraft:jukebox", 1), ("minecraft:bookshelf", 2),
        ("minecraft:enchanting_table", 1), ("minecraft:ender_chest", 1), ("minecraft:respawn_anchor", 1),
        ("minecraft:target", 1), ("minecraft:honey_block", 1), ("minecraft:slime_block", 1),
        ("minecraft:hay_block", 2), ("minecraft:melon", 2), ("minecraft:pumpkin", 2), ("minecraft:glowstone", 2),
        ("minecraft:amethyst_block", 2), ("minecraft:copper_block", 2), ("minecraft:gilded_blackstone", 2),
        ("minecraft:sculk", 2), ("minecraft:purpur_block", 2), ("minecraft:coal_ore", 3), ("minecraft:iron_ore", 3),
        ("minecraft:gold_ore", 3), ("minecraft:lapis_ore", 2), ("minecraft:redstone_ore", 2), ("minecraft:copper_ore", 2),
        ("minecraft:nether_quartz_ore", 2), ("minecraft:nether_gold_ore", 2), ("minecraft:raw_gold_block", 1),
        ("minecraft:crafting_table", 1), ("minecraft:smithing_table", 1), ("minecraft:blast_furnace", 1),
    ],
}

# Mobs per phase (summoned on top of the block, no NBT = natural equipment)
MOBS = {
    1: [("chicken", 10), ("cow", 10), ("pig", 10), ("sheep", 10), ("rabbit", 6), ("villager", 3),
        ("wolf", 2), ("cat", 2), ("zombie", 4), ("spider", 2), ("bee", 3), ("horse", 2)],
    2: [("zombie", 14), ("skeleton", 12), ("spider", 8), ("cave_spider", 5), ("creeper", 5), ("bat", 6),
        ("silverfish", 4), ("villager", 2), ("sheep", 4), ("cow", 4), ("slime", 3), ("glow_squid", 2),
        ("iron_golem", 1), ("witch", 2)],
    3: [("panda", 5), ("parrot", 5), ("ocelot", 4), ("polar_bear", 4), ("fox", 5), ("wolf", 5), ("goat", 4),
        ("llama", 3), ("mooshroom", 3), ("turtle", 3), ("frog", 4), ("sniffer", 1), ("camel", 2),
        ("drowned", 6), ("witch", 4), ("husk", 5), ("stray", 5), ("zombie", 5), ("skeleton", 5),
        ("creeper", 4), ("spider", 4), ("pillager", 3), ("armadillo", 2), ("villager", 2)],
    4: [("zombified_piglin", 20), ("piglin", 12), ("hoglin", 6), ("magma_cube", 10), ("blaze", 8),
        ("wither_skeleton", 8), ("strider", 6), ("ghast", 3), ("skeleton", 6), ("piglin_brute", 2),
        ("zombie", 5), ("creeper", 3), ("chicken", 3)],
    5: [("enderman", 20), ("endermite", 8), ("shulker", 4), ("phantom", 6), ("zombie", 5), ("skeleton", 5),
        ("creeper", 4), ("spider", 4), ("witch", 3), ("warden", 1), ("allay", 3), ("ravager", 2),
        ("pillager", 4), ("vindicator", 3), ("evoker", 1), ("breeze", 3), ("bogged", 3), ("villager", 2)],
    6: [("zombie", 6), ("skeleton", 6), ("creeper", 5), ("enderman", 5), ("blaze", 4), ("wither_skeleton", 4),
        ("witch", 3), ("ravager", 2), ("evoker", 2), ("vindicator", 3), ("breeze", 3), ("bogged", 3),
        ("iron_golem", 3), ("snow_golem", 2), ("wandering_trader", 3), ("villager", 4), ("zombie_villager", 2),
        ("horse", 3), ("camel", 2), ("sniffer", 2), ("armadillo", 2), ("panda", 2), ("polar_bear", 2),
        ("allay", 3), ("shulker", 2), ("phantom", 3), ("hoglin", 2), ("piglin_brute", 2), ("warden", 1),
        ("cow", 4), ("pig", 4), ("sheep", 4), ("chicken", 4), ("bee", 3), ("axolotl", 1)],
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
files: dict[Path, str | bytes] = {}


def fn(name: str, body: str) -> None:
    """Register a function lucky:<name>."""
    lines = [ln.rstrip() for ln in body.strip("\n").splitlines()]
    files[NS / "function" / f"{name}.mcfunction"] = "\n".join(lines) + "\n"


def loot(name: str, table: dict) -> None:
    files[NS / "loot_table" / f"{name}.json"] = json.dumps(table, indent=2) + "\n"


def tell(parts: list) -> str:
    return "tellraw @a " + json.dumps(["", {"text": "[Lucky] ", "color": "gold", "bold": True}] + parts,
                                     ensure_ascii=False)


def msg(text: str, color: str = "yellow") -> str:
    return tell([{"text": text, "color": color}])


def weighted_dispatch(score_holder: str, entries: list[tuple[str, int]], fmt: str) -> str:
    """Build a `random value` roll + `execute if score ... matches a..b` chain."""
    total = sum(w for _, w in entries)
    out = [f"execute store result score {score_holder} ob.rng run random value 1..{total}"]
    lo = 1
    for value, w in entries:
        hi = lo + w - 1
        rng = f"{lo}" if lo == hi else f"{lo}..{hi}"
        out.append(f"execute if score {score_holder} ob.rng matches {rng} run " + fmt.format(v=value))
        lo = hi + 1
    return "\n".join(out)


def item(name: str, weight: int, lo: int = 1, hi: int | None = None, functions: list | None = None) -> dict:
    e = {"type": "minecraft:item", "name": f"minecraft:{name}", "weight": weight}
    funcs = list(functions or [])
    if hi is not None and (lo != 1 or hi != 1):
        funcs.insert(0, {"function": "minecraft:set_count", "count": uniform(lo, hi)})
    elif hi is None and lo != 1:
        funcs.insert(0, {"function": "minecraft:set_count", "count": lo})
    if funcs:
        e["functions"] = funcs
    return e


def uniform(lo: int, hi: int) -> dict:
    # Newer versions (26.x) require the number-provider type to be explicit.
    return {"type": "minecraft:uniform", "min": lo, "max": hi}


def ench(lo: int, hi: int) -> list:
    return [{"function": "minecraft:enchant_with_levels", "levels": uniform(lo, hi)}]


def rand_ench() -> list:
    return [{"function": "minecraft:enchant_randomly"}]


def potion(pid: str) -> list:
    return [{"function": "minecraft:set_potion", "id": f"minecraft:{pid}"}]


def named(text: str, color: str = "gold") -> list:
    return [{"function": "minecraft:set_name", "name": {"text": text, "color": color, "italic": False}}]


def table(pools: list[tuple[int | tuple[int, int], list]]) -> dict:
    out = {"type": "minecraft:chest", "pools": []}
    for rolls, entries in pools:
        r = rolls if isinstance(rolls, int) else uniform(rolls[0], rolls[1])
        out["pools"].append({"rolls": r, "entries": entries})
    return out


def firework(x: str, y: str, z: str, colors: list[int], shape: str = "large_ball") -> str:
    comp = {"explosions": [{"shape": shape, "colors": colors, "has_trail": True, "has_twinkle": True}],
            "flight_duration": 1}
    snbt = json.dumps(comp).replace('"colors": [', '"colors": [I;')
    return (f"summon minecraft:firework_rocket {x} {y} {z} "
            f'{{LifeTime:25,FireworksItem:{{id:"minecraft:firework_rocket",count:1,'
            f'components:{{"minecraft:fireworks":{snbt}}}}}}}')


SOUND_GOOD = "playsound minecraft:entity.player.levelup master @a 0 64 0 1 1"
SOUND_BAD = "playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4"
SOUND_WEIRD = "playsound minecraft:entity.villager.celebrate master @a 0 64 0 1 1"
GIVE = f"execute positioned {TOP} run give @p"
LOOT = f"execute positioned {TOP} run loot give @p loot"
EFFECT = f"execute positioned {TOP} run effect give @p"


# ---------------------------------------------------------------------------
# core: load / tick / init / block
# ---------------------------------------------------------------------------
GAMERULES = {
    "keepInventory": "true",
    "spawnRadius": "0",
    "doInsomnia": "false",
    "commandBlockOutput": "false",
    "logAdminCommands": "false",
    "doPatrolSpawning": "false",
    "doTraderSpawning": "false",
    "spawnChunkRadius": "2",
}

fn("load", f"""
scoreboard objectives add ob.count dummy
scoreboard objectives add ob.phase dummy
scoreboard objectives add ob.rng dummy
scoreboard objectives add ob.flag dummy
scoreboard objectives add ob.stats dummy
scoreboard objectives add ob.help trigger
scoreboard objectives add ob.rescue trigger
scoreboard objectives add ob.reroll trigger
scoreboard objectives add ob.dragonkill minecraft.killed:minecraft.ender_dragon
execute unless score #count ob.count = #count ob.count run scoreboard players set #count ob.count 0
execute unless score #phase ob.phase = #phase ob.phase run scoreboard players set #phase ob.phase 1
execute unless score #thresh ob.count = #thresh ob.count run scoreboard players set #thresh ob.count {PHASES[1][2]}
execute unless score #init ob.flag = #init ob.flag run scoreboard players set #init ob.flag 0
execute unless score #lucky ob.flag = #lucky ob.flag run scoreboard players set #lucky ob.flag 0
execute unless score #boss ob.flag = #boss ob.flag run scoreboard players set #boss ob.flag 0
execute unless score #rescue ob.flag = #rescue ob.flag run scoreboard players set #rescue ob.flag 1
execute unless score #luckycount ob.stats = #luckycount ob.stats run scoreboard players set #luckycount ob.stats 0
execute unless score #chests ob.stats = #chests ob.stats run scoreboard players set #chests ob.stats 0
execute unless score #mobs ob.stats = #mobs ob.stats run scoreboard players set #mobs ob.stats 0
scoreboard players set #tick ob.flag 0
scoreboard players set #stuck ob.flag 0
scoreboard players set #dragon_gone ob.flag 0
scoreboard players set #dragon_dying ob.flag 0
execute in minecraft:overworld run forceload add -16 -16 15 15
execute in minecraft:overworld run setworldspawn 0 64 0
""" + tell([{"text": "One Block: Lucky Block Edition loaded. Type ", "color": "gray"},
            {"text": "/trigger ob.help", "color": "yellow"}, {"text": " for the rules.", "color": "gray"}]))

fn("tick", f"""
execute in minecraft:overworld positioned {TOP} run function lucky:tick/main
""")

fn("tick/main", f"""
execute unless score #init ob.flag matches 1 if loaded {BLOCK} run function lucky:init
execute if score #init ob.flag matches 1 if block {BLOCK} #minecraft:air run function lucky:block/broken
execute if score #init ob.flag matches 1 run function lucky:block/stuck_timer
execute as @a[tag=!ob.joined] run function lucky:player/welcome
execute if score #rescue ob.flag matches 1 as @a[gamemode=!spectator,gamemode=!creative] at @s if dimension minecraft:overworld if entity @s[y=-300,dy=330] run function lucky:player/rescue
execute as @a[scores={{ob.help=1..}}] run function lucky:player/help
execute as @a[scores={{ob.rescue=1..}}] run function lucky:player/toggle_rescue
execute as @a[scores={{ob.reroll=1..}}] run function lucky:player/reroll
scoreboard players enable @a ob.help
scoreboard players enable @a ob.rescue
scoreboard players enable @a ob.reroll
execute as @e[type=item,distance=..64] if items entity @s contents minecraft:sponge run kill @s
scoreboard players add #tick ob.flag 1
execute if score #tick ob.flag matches 20.. run function lucky:hud/show
execute if score #boss ob.flag matches 1 run function lucky:boss/tick
""")

fn("init", f"""
setblock {BLOCK} minecraft:grass_block
scoreboard players set #init ob.flag 1
scoreboard players set #stuck ob.flag 0
kill @e[type=item,distance=..8]
""")

fn("block/broken", f"""
scoreboard players add #count ob.count 1
scoreboard players set #stuck ob.flag 0
execute as @e[type=item,x=0,y=62.5,z=0,dx=0,dy=1,dz=0] run function lucky:block/save_drop
execute as @e[type=experience_orb,x=0,y=62.5,z=0,dx=0,dy=1,dz=0] run tp @s 0.5 64.3 0.5
execute if score #lucky ob.flag matches 1 run function lucky:lucky/trigger
execute if score #lucky ob.flag matches 0 run function lucky:block/roll
function lucky:phase/check
""")

fn("block/save_drop", """
tp @s 0.5 64.25 0.5
data merge entity @s {Motion:[0.0d,0.12d,0.0d],PickupDelay:5s}
""")

fn("block/roll", "\n".join(
    f"execute if score #phase ob.phase matches {p} run function lucky:phase/{p}/roll" for p, *_ in PHASES))

fn("block/plain", "\n".join(
    f"execute if score #phase ob.phase matches {p} run function lucky:phase/{p}/blocks" for p, *_ in PHASES))

fn("block/place_lucky", f"""
setblock {BLOCK} minecraft:sponge
scoreboard players set #lucky ob.flag 1
particle minecraft:happy_villager 0.5 64.3 0.5 0.5 0.3 0.5 0.1 40 force
playsound minecraft:block.note_block.chime master @a 0 64 0 1 1.6
playsound minecraft:block.amethyst_block.chime master @a 0 64 0 1 0.8
""" + tell([{"text": "A LUCKY BLOCK appeared! Break it if you dare...", "color": "yellow", "bold": True}]))

fn("block/stuck_timer", f"""
scoreboard players add #stuck ob.flag 1
execute if score #stuck ob.flag matches 2400.. run function lucky:block/unstick
""")

fn("block/unstick", f"""
scoreboard players set #stuck ob.flag 0
scoreboard players set #lucky ob.flag 0
setblock {BLOCK} minecraft:dirt
""" + msg("That block sat there for 2 minutes, so it turned into dirt. Keep going!", "gray"))

# --- phases -----------------------------------------------------------------
for i, (p, pname, start, lucky_pct, chest_pct, mob_pct) in enumerate(PHASES):
    nxt = PHASES[i + 1][2] if i + 1 < len(PHASES) else BOSS_AT
    plain_pct = 100 - lucky_pct - chest_pct - mob_pct
    fn(f"phase/{p}/roll", weighted_dispatch("#r", [
        ("lucky:block/place_lucky", lucky_pct),
        (f"lucky:phase/{p}/chest", chest_pct),
        (f"lucky:phase/{p}/mob", mob_pct),
        (f"lucky:phase/{p}/blocks", plain_pct),
    ], "function {v}"))
    fn(f"phase/{p}/blocks", weighted_dispatch("#r2", BLOCKS[p], f"setblock {BLOCK} {{v}}"))
    fn(f"phase/{p}/chest", f"""
scoreboard players add #chests ob.stats 1
execute store result score #r2 ob.rng run random value 1..10
execute if score #r2 ob.rng matches 1..8 run setblock {BLOCK} minecraft:chest{{LootTable:"lucky:chest/phase_{p}"}}
execute if score #r2 ob.rng matches 9..10 run setblock {BLOCK} minecraft:barrel{{LootTable:"lucky:chest/phase_{p}"}}
playsound minecraft:block.chest.open master @a 0 64 0 0.6 1.2
""")
    fn(f"phase/{p}/mob", f"""
scoreboard players add #mobs ob.stats 1
setblock {BLOCK} {PHASE_FLOOR[p]}
""" + weighted_dispatch("#r2", MOBS[p], f"summon minecraft:{{v}} {TOP}"))
    if p > 1:
        color = PHASE_COLORS[p]
        fn(f"phase/{p}/enter", f"""
scoreboard players set #phase ob.phase {p}
scoreboard players set #thresh ob.count {nxt}
title @a title {json.dumps({"text": f"PHASE {p}", "color": color, "bold": True})}
title @a subtitle {json.dumps({"text": pname, "color": "white"})}
playsound minecraft:ui.toast.challenge_complete master @a 0 64 0 1 1
{firework("0.5", "66", "0.5", [16766720, 16777215])}
{firework("2.5", "66", "-1.5", [11141290, 16766720], "star")}
{firework("-1.5", "66", "2.5", [43775, 16777215], "burst")}
setblock {BLOCK} minecraft:chest{{LootTable:"lucky:chest/kit_{p}"}}
""" + tell([{"text": f"Phase {p}: {pname}! ", "color": color, "bold": True},
            {"text": "A kit chest spawned on the block. New blocks, new mobs, more lucky blocks.", "color": "white"}]))

check = []
for i in range(1, len(PHASES)):
    p = PHASES[i][0]
    check.append(f"execute if score #phase ob.phase matches {p - 1} if score #count ob.count matches {PHASES[i][2]}.. "
                 f"run function lucky:phase/{p}/enter")
check.append(f"execute if score #phase ob.phase matches 6 if score #boss ob.flag matches 0 "
             f"if score #count ob.count matches {BOSS_AT}.. run function lucky:boss/start")
fn("phase/check", "\n".join(check))

# --- HUD ---------------------------------------------------------------------
def hud_line(p: int, pname: str, tail: list) -> str:
    comp = ["",
            {"text": "⛏ ", "color": "gold"},
            {"score": {"name": "#count", "objective": "ob.count"}, "color": "white", "bold": True},
            {"text": " blocks   ", "color": "gray"},
            {"text": f"Phase {p}: {pname}", "color": PHASE_COLORS[p], "bold": True},
            {"text": "   ", "color": "gray"}] + tail + [
            {"text": "   ✦ ", "color": "gold"},
            {"score": {"name": "#luckycount", "objective": "ob.stats"}, "color": "gold"},
            {"text": " lucky", "color": "gold"}]
    return "title @a actionbar " + json.dumps(comp, ensure_ascii=False)


hud = ["scoreboard players set #tick ob.flag 0",
       "scoreboard players operation #next ob.count = #thresh ob.count",
       "scoreboard players operation #next ob.count -= #count ob.count"]
for p, pname, *_ in PHASES:
    if p < 6:
        tail = [{"text": "next phase in ", "color": "gray"},
                {"score": {"name": "#next", "objective": "ob.count"}, "color": "yellow"}]
        hud.append(f"execute if score #phase ob.phase matches {p} run " + hud_line(p, pname, tail))
    else:
        tail = [{"text": "DRAGON in ", "color": "light_purple"},
                {"score": {"name": "#next", "objective": "ob.count"}, "color": "yellow"}]
        hud.append(f"execute if score #phase ob.phase matches 6 if score #boss ob.flag matches 0 run " + hud_line(p, pname, tail))
        hud.append("execute if score #boss ob.flag matches 1 run " + hud_line(p, pname, [{"text": "SLAY THE DRAGON!", "color": "dark_purple", "bold": True}]))
        hud.append("execute if score #boss ob.flag matches 2 run " + hud_line(p, pname, [{"text": "DRAGON SLAIN ✔", "color": "green", "bold": True}]))
fn("hud/show", "\n".join(hud))

# --- players -----------------------------------------------------------------
fn("player/welcome", """
tag @s add ob.joined
title @s times 10 70 20
title @s title {"text":"ONE BLOCK","color":"gold","bold":true}
title @s subtitle {"text":"LUCKY BLOCK EDITION","color":"yellow"}
playsound minecraft:entity.player.levelup master @s ~ ~ ~ 1 0.8
tellraw @s ""
tellraw @s ["",{"text":"=== ONE BLOCK: LUCKY BLOCK EDITION ===","color":"gold","bold":true}]
tellraw @s ["",{"text":"You have ONE block. Break it. It comes back as something new.","color":"white"}]
tellraw @s ["",{"text":"Yellow ","color":"white"},{"text":"LUCKY BLOCKS","color":"yellow","bold":true},{"text":" can be amazing... or a disaster. Break them anyway.","color":"white"}]
tellraw @s ["",{"text":"6 phases, a kit chest every phase, and at 800 blocks: ","color":"white"},{"text":"THE DRAGON.","color":"dark_purple","bold":true}]
tellraw @s ["",{"text":"Fall in the void? You get rescued (toggle with ","color":"gray"},{"text":"/trigger ob.rescue","color":"yellow"},{"text":"). Rules: ","color":"gray"},{"text":"/trigger ob.help","color":"yellow"}]
tellraw @s ""
""")

fn("player/rescue", """
tp @s 0.5 66 0.5
effect give @s minecraft:slow_falling 4 0 true
playsound minecraft:entity.ender_eye.death master @s ~ ~ ~ 1 1.2
""")

fn("player/help", """
scoreboard players set @s ob.help 0
tellraw @s ["",{"text":"=== HOW TO PLAY ===","color":"gold","bold":true}]
tellraw @s ["",{"text":"1. ","color":"gold"},{"text":"Break the block. It regenerates instantly into a random block, a loot chest, a mob, or a Lucky Block.","color":"white"}]
tellraw @s ["",{"text":"2. ","color":"gold"},{"text":"Drops pop UP onto the block so you can grab them. Mobs spawn on top of you. Hold on.","color":"white"}]
tellraw @s ["",{"text":"3. ","color":"gold"},{"text":"Phases: Plains (0) > Caves (60) > Wild (150) > Nether (260) > End & Deep Dark (400) > Lucky Chaos (560) > THE DRAGON (800).","color":"white"}]
tellraw @s ["",{"text":"4. ","color":"gold"},{"text":"Lucky Blocks are 50% good, 30% bad, 20% weird. The chance goes up every phase.","color":"white"}]
tellraw @s ["",{"text":"5. ","color":"gold"},{"text":"Can't break the block (no pickaxe)? Wait 2 minutes and it turns to dirt, or type ","color":"white"},{"text":"/trigger ob.reroll","color":"yellow"},{"text":".","color":"white"}]
tellraw @s ["",{"text":"6. ","color":"gold"},{"text":"Build out with cobblestone (water + lava bucket from chests). Make land, farms, a base. Then go slay the dragon.","color":"white"}]
tellraw @s ["",{"text":"Commands: ","color":"gray"},{"text":"/trigger ob.rescue","color":"yellow"},{"text":" (void rescue on/off)  ","color":"gray"},{"text":"/trigger ob.reroll","color":"yellow"},{"text":" (replace a stuck block)","color":"gray"}]
""")

fn("player/toggle_rescue", """
scoreboard players set @s ob.rescue 0
execute if score #rescue ob.flag matches 1 run scoreboard players set #rescue ob.flag 2
execute if score #rescue ob.flag matches 0 run scoreboard players set #rescue ob.flag 1
execute if score #rescue ob.flag matches 2 run scoreboard players set #rescue ob.flag 0
execute if score #rescue ob.flag matches 1 run tellraw @s ["",{"text":"[Lucky] ","color":"gold","bold":true},{"text":"Void rescue: ON. Fall in and you get teleported back.","color":"green"}]
execute if score #rescue ob.flag matches 0 run tellraw @s ["",{"text":"[Lucky] ","color":"gold","bold":true},{"text":"Void rescue: OFF. Hardcore mode, huh? Respect.","color":"red"}]
""")

fn("player/reroll", f"""
scoreboard players set @s ob.reroll 0
scoreboard players set #lucky ob.flag 0
scoreboard players set #stuck ob.flag 0
execute unless block {BLOCK} #minecraft:air run setblock {BLOCK} minecraft:dirt
tellraw @s ["",{{"text":"[Lucky] ","color":"gold","bold":true}},{{"text":"Block replaced with dirt. No lucky stuff for that one, nice try.","color":"gray"}}]
""")

# --- admin -------------------------------------------------------------------
fn("admin/reset", f"""
scoreboard players set #count ob.count 0
scoreboard players set #phase ob.phase 1
scoreboard players set #thresh ob.count {PHASES[1][2]}
scoreboard players set #lucky ob.flag 0
scoreboard players set #boss ob.flag 0
scoreboard players set #luckycount ob.stats 0
scoreboard players set #chests ob.stats 0
scoreboard players set #mobs ob.stats 0
setblock {BLOCK} minecraft:grass_block
""" + msg("Progress reset to block 0, Phase 1.", "red"))

fn("admin/skip_phase", f"""
execute if score #phase ob.phase matches 1 run scoreboard players set #count ob.count {PHASES[1][2]}
execute if score #phase ob.phase matches 2 run scoreboard players set #count ob.count {PHASES[2][2]}
execute if score #phase ob.phase matches 3 run scoreboard players set #count ob.count {PHASES[3][2]}
execute if score #phase ob.phase matches 4 run scoreboard players set #count ob.count {PHASES[4][2]}
execute if score #phase ob.phase matches 5 run scoreboard players set #count ob.count {PHASES[5][2]}
execute if score #phase ob.phase matches 6 run scoreboard players set #count ob.count {BOSS_AT}
function lucky:phase/check
""")

fn("admin/stats", """
tellraw @a ["",{"text":"[Lucky] ","color":"gold","bold":true},{"text":"Blocks: ","color":"gray"},{"score":{"name":"#count","objective":"ob.count"},"color":"white"},{"text":"  Phase: ","color":"gray"},{"score":{"name":"#phase","objective":"ob.phase"},"color":"white"},{"text":"  Lucky blocks: ","color":"gray"},{"score":{"name":"#luckycount","objective":"ob.stats"},"color":"gold"},{"text":"  Chests: ","color":"gray"},{"score":{"name":"#chests","objective":"ob.stats"},"color":"white"},{"text":"  Mobs: ","color":"gray"},{"score":{"name":"#mobs","objective":"ob.stats"},"color":"white"}]
""")

# ---------------------------------------------------------------------------
# Lucky block events
# ---------------------------------------------------------------------------
GOOD: list[tuple[str, int]] = []
BAD: list[tuple[str, int]] = []
WEIRD: list[tuple[str, int]] = []


def good(name: str, weight: int, body: str) -> None:
    GOOD.append((name, weight))
    fn(f"event/good/{name}", SOUND_GOOD + "\n" + body)


def bad(name: str, weight: int, body: str) -> None:
    BAD.append((name, weight))
    fn(f"event/bad/{name}", SOUND_BAD + "\n" + body)


def weird(name: str, weight: int, body: str) -> None:
    WEIRD.append((name, weight))
    fn(f"event/weird/{name}", SOUND_WEIRD + "\n" + body)


# ---- GOOD -------------------------------------------------------------------
good("diamonds", 8, f"""
{GIVE} minecraft:diamond 5
particle minecraft:end_rod 0.5 65 0.5 0.4 0.6 0.4 0.05 60 force
""" + msg("DIAMONDS! 5 of them. Just like that."))

good("gear", 10, f"""
{LOOT} lucky:lucky/gear
particle minecraft:enchant 0.5 65 0.5 0.6 0.6 0.6 1 80 force
""" + msg("Enchanted gear! Check your inventory."))

good("books", 6, f"""
{LOOT} lucky:lucky/books
""" + msg("Enchanted books. Nerd loot, but the good kind."))

good("golden_apples", 6, f"""
{GIVE} minecraft:golden_apple 3
{GIVE} minecraft:enchanted_golden_apple 1
""" + msg("Golden apples, plus one NOTCH apple. Save it for the dragon."))

good("xp", 6, f"""
execute positioned {TOP} run xp add @p 10 levels
particle minecraft:totem_of_undying 0.5 65 0.5 0.5 0.5 0.5 0.2 60 force
""" + msg("+10 XP levels! Go enchant something."))

good("totem", 5, f"""
{GIVE} minecraft:totem_of_undying 1
""" + msg("A Totem of Undying. That's a free life, bro.", "green"))

good("starter_pack", 10, f"""
{LOOT} lucky:lucky/starter
""" + msg("Starter pack: saplings, seeds, bone meal, food, a water bucket. Build a farm!"))

good("buckets", 7, f"""
{GIVE} minecraft:water_bucket 1
{GIVE} minecraft:lava_bucket 1
""" + msg("Water bucket + lava bucket = infinite cobblestone. You know what to do."))

good("platform", 5, f"""
fill -1 62 -1 1 62 1 minecraft:cobblestone keep
particle minecraft:cloud 0.5 63 0.5 1.5 0.3 1.5 0.02 80 force
""" + msg("LAND! A 3x3 cobblestone platform grew under your block.", "green"))

good("ore_pillar", 5, f"""
setblock 0 64 3 minecraft:iron_ore
setblock 0 65 3 minecraft:gold_ore
setblock 0 66 3 minecraft:lapis_ore
setblock 0 67 3 minecraft:redstone_ore
setblock 0 68 3 minecraft:diamond_ore
""" + msg("An ore pillar appeared 3 blocks away. Bridge to it carefully!", "aqua"))

good("trader", 5, f"""
summon minecraft:wandering_trader {TOP}
""" + msg("A Wandering Trader dropped by. Got emeralds?"))

good("villager", 4, f"""
summon minecraft:villager {TOP}
""" + msg("A villager! Keep it safe and it'll trade with you."))

good("pets", 5, f"""
summon minecraft:wolf 0.5 64 0.5
summon minecraft:cat 0.5 64 0.5
summon minecraft:parrot 0.5 65 0.5
{GIVE} minecraft:bone 4
{GIVE} minecraft:cod 4
""" + msg("Pet party! A wolf, a cat and a parrot. Bones and fish included."))

good("treasure_chest", 7, f"""
setblock {BLOCK} minecraft:chest{{LootTable:"lucky:lucky/treasure"}}
playsound minecraft:block.chest.open master @a 0 64 0 1 1
""" + msg("TREASURE CHEST! The block itself is the chest. Open it.", "green"))

good("shulker_box", 4, f"""
setblock {BLOCK} minecraft:yellow_shulker_box{{Items:[{{Slot:0b,id:"minecraft:diamond",count:6}},{{Slot:1b,id:"minecraft:golden_apple",count:4}},{{Slot:2b,id:"minecraft:iron_ingot",count:16}},{{Slot:3b,id:"minecraft:oak_sapling",count:4}},{{Slot:4b,id:"minecraft:ender_pearl",count:4}},{{Slot:5b,id:"minecraft:experience_bottle",count:16}},{{Slot:6b,id:"minecraft:cooked_beef",count:12}},{{Slot:7b,id:"minecraft:emerald",count:8}},{{Slot:8b,id:"minecraft:torch",count:32}}]}}
""" + msg("A LUCKY BOX (shulker box) full of goodies. Break it and it's yours, contents and all.", "green"))

good("beacon_kit", 3, f"""
{GIVE} minecraft:beacon 1
{GIVE} minecraft:iron_block 9
""" + msg("A BEACON and 9 iron blocks. Build the pyramid when you have the room.", "aqua"))

good("elytra", 1, f"""
{GIVE} minecraft:elytra 1
{GIVE} minecraft:firework_rocket 32
title @a title {{"text":"ELYTRA!","color":"aqua","bold":true}}
""" + msg("ELYTRA + 32 rockets?! Ultra rare. Don't fly into the void, you hear me?", "aqua"))

good("golem", 3, f"""
summon minecraft:iron_golem {TOP}
""" + msg("An Iron Golem bodyguard. It falls off a lot, but it tries."))

# ---- BAD --------------------------------------------------------------------
bad("tnt", 10, f"""
summon minecraft:tnt {TOP} {{fuse:70}}
title @a title {{"text":"TNT!","color":"red","bold":true}}
""" + msg("TNT! You have 3.5 seconds. Good luck, there is nowhere to run.", "red"))

bad("creepers", 8, f"""
summon minecraft:creeper {TOP}
summon minecraft:creeper 0.5 65 0.5
execute if score #phase ob.phase matches 4.. run summon minecraft:creeper 0.5 66 0.5 {{powered:1b}}
""" + msg("Creepers. Aw man.", "red"))

bad("anvil_rain", 8, f"""
setblock 0 74 0 minecraft:anvil
setblock 0 80 0 minecraft:anvil
setblock 0 86 0 minecraft:anvil
setblock 1 78 0 minecraft:chipped_anvil
setblock 0 82 1 minecraft:damaged_anvil
""" + msg("ANVILS FROM THE SKY! Move! (Hey, free anvil though.)", "red"))

bad("lightning", 8, f"""
summon minecraft:lightning_bolt {TOP}
summon minecraft:lightning_bolt 1.5 64 0.5
summon minecraft:lightning_bolt -0.5 64 1.5
""" + msg("ZAP. Thor says hi.", "red"))

bad("horde", 12, """
execute if score #phase ob.phase matches ..2 run function lucky:event/bad/horde_early
execute if score #phase ob.phase matches 3..4 run function lucky:event/bad/horde_mid
execute if score #phase ob.phase matches 5.. run function lucky:event/bad/horde_late
""" + msg("A HORDE! Fight or get yeeted off the block.", "red"))
fn("event/bad/horde_early", f"""
summon minecraft:zombie {TOP}
summon minecraft:zombie 0.5 65 0.5
summon minecraft:zombie 0.5 66 0.5
summon minecraft:skeleton 0.5 67 0.5
""")
fn("event/bad/horde_mid", f"""
summon minecraft:husk {TOP}
summon minecraft:husk 0.5 65 0.5
summon minecraft:stray 0.5 66 0.5
summon minecraft:wither_skeleton 0.5 67 0.5
summon minecraft:blaze 0.5 68 0.5
""")
fn("event/bad/horde_late", f"""
summon minecraft:wither_skeleton {TOP}
summon minecraft:wither_skeleton 0.5 65 0.5
summon minecraft:vindicator 0.5 66 0.5
summon minecraft:vindicator 0.5 67 0.5
summon minecraft:evoker 0.5 68 0.5
summon minecraft:breeze 0.5 69 0.5
""")

bad("witch", 6, f"""
summon minecraft:witch {TOP}
""" + msg("A witch! Watch out for the potions.", "red"))

bad("skeleton_squad", 6, f"""
summon minecraft:skeleton {TOP}
summon minecraft:skeleton 0.5 65 0.5
summon minecraft:skeleton 0.5 66 0.5
""" + msg("Skeleton squad. Arrows incoming.", "red"))

bad("cobweb_trap", 6, f"""
fill 0 64 0 0 65 0 minecraft:cobweb
summon minecraft:cave_spider {TOP}
summon minecraft:cave_spider 0.5 66 0.5
""" + msg("Stuck in cobwebs with cave spiders. Yikes.", "red"))

bad("levitation", 6, f"""
execute positioned {TOP} run effect give @a[distance=..6] minecraft:levitation 6 1
execute positioned {TOP} run effect give @a[distance=..6] minecraft:slow_falling 25 0
""" + msg("Up, up and away! (Slow falling kicks in, you'll float back down... hopefully onto the block.)", "red"))

bad("poison_cloud", 6, f"""
summon minecraft:area_effect_cloud {TOP} {{Radius:3.0f,Duration:160,potion_contents:{{potion:"minecraft:poison"}}}}
""" + msg("Poison cloud! Hold your breath.", "red"))

bad("silverfish", 5, f"""
summon minecraft:silverfish {TOP}
summon minecraft:silverfish 0.5 65 0.5
summon minecraft:silverfish 0.5 65 0.5
summon minecraft:silverfish 0.5 66 0.5
summon minecraft:silverfish 0.5 66 0.5
""" + msg("Silverfish swarm. Ew ew ew.", "red"))

bad("fake_diamond", 5, f"""
setblock {BLOCK} minecraft:diamond_ore
schedule function lucky:event/bad/fake_diamond_pop 40t
""" + msg("Ooh, diamond ore! ...wait.", "aqua"))
fn("event/bad/fake_diamond_pop", f"""
execute if block {BLOCK} minecraft:diamond_ore run setblock {BLOCK} minecraft:slime_block
summon minecraft:slime {TOP} {{Size:1}}
summon minecraft:slime 0.5 65 0.5 {{Size:1}}
summon minecraft:slime 0.5 66 0.5 {{Size:1}}
playsound minecraft:entity.slime.squish master @a 0 64 0 1 0.7
""" + msg("Psych! It was slime the whole time.", "red"))

bad("lava_trap", 6, f"""
setblock 0 64 0 minecraft:lava
schedule function lucky:event/bad/lava_clear 100t
title @a title {{"text":"LAVA!","color":"red","bold":true}}
""" + msg("LAVA on top of the block! It clears in 5 seconds. Jump!", "red"))
fn("event/bad/lava_clear", """
execute if block 0 64 0 minecraft:lava run setblock 0 64 0 minecraft:air
""")

bad("midnight", 4, f"""
time set midnight
weather thunder 600
summon minecraft:phantom 0.5 72 0.5
summon minecraft:phantom 0.5 74 0.5
""" + msg("Midnight. Thunder. Phantoms. Sleep tight.", "red"))

bad("blaze_rush", 4, f"""
execute if score #phase ob.phase matches 4.. run summon minecraft:blaze {TOP}
execute if score #phase ob.phase matches 4.. run summon minecraft:blaze 0.5 66 0.5
execute if score #phase ob.phase matches 4.. run summon minecraft:blaze 0.5 68 0.5
execute if score #phase ob.phase matches ..3 run summon minecraft:spider {TOP}
execute if score #phase ob.phase matches ..3 run summon minecraft:spider 0.5 65 0.5
execute if score #phase ob.phase matches ..3 run summon minecraft:spider 0.5 66 0.5
""" + msg("Fire and fangs! Hot stuff.", "red"))

bad("evoker", 4, f"""
execute if score #phase ob.phase matches 5.. run summon minecraft:evoker {TOP}
execute if score #phase ob.phase matches 5.. run summon minecraft:vex 0.5 66 0.5
execute if score #phase ob.phase matches 5.. run summon minecraft:vex 0.5 66 0.5
execute if score #phase ob.phase matches ..4 run summon minecraft:pillager {TOP}
execute if score #phase ob.phase matches ..4 run summon minecraft:pillager 0.5 65 0.5
""" + msg("Illagers! They hate you specifically.", "red"))

bad("warden", 1, f"""
execute if score #phase ob.phase matches 5.. run summon minecraft:warden {TOP}
execute if score #phase ob.phase matches 5.. run title @a title {{"text":"WARDEN","color":"dark_aqua","bold":true}}
execute if score #phase ob.phase matches 5.. run {msg("THE WARDEN. Do NOT fight it. Run. Build. Pray.", "dark_aqua")}
execute if score #phase ob.phase matches ..4 run function lucky:event/bad/horde
""")

bad("wither", 1, f"""
execute if score #phase ob.phase matches 6 run summon minecraft:wither 0.5 72 0.5
execute if score #phase ob.phase matches 6 run title @a title {{"text":"THE WITHER","color":"dark_gray","bold":true}}
execute if score #phase ob.phase matches 6 run {msg("THE WITHER?! Ultra rare, ultra deadly. Kill it for a Nether Star!", "dark_gray")}
execute if score #phase ob.phase matches ..5 run function lucky:event/bad/creepers
""")

# ---- WEIRD ------------------------------------------------------------------
weird("chicken_rain", 10, "\n".join(
    f"summon minecraft:chicken {x} {y} {z}" for x, y, z in [
        ("0.5", "72", "0.5"), ("1.2", "73", "0.3"), ("-0.3", "74", "1.1"), ("0.7", "75", "-0.4"),
        ("0.5", "76", "0.5"), ("1.0", "77", "1.0"), ("0.0", "78", "0.0"), ("0.5", "79", "0.9"),
        ("0.2", "80", "0.6"), ("0.8", "81", "0.2"), ("0.5", "82", "0.5"), ("0.4", "83", "0.4")]
) + "\n" + msg("CHICKEN RAIN! Bawk bawk bawk.", "light_purple"))

weird("rainbow_sheep", 8, "\n".join(
    f"summon minecraft:sheep 0.5 {64 + i} 0.5 {{Color:{c}b}}" for i, c in enumerate([14, 1, 4, 5, 11, 10])
) + "\n" + msg("Rainbow sheep tower. Shear them!", "light_purple"))

weird("fireworks", 10, "\n".join([
    firework("0.5", "65", "0.5", [16711680, 16766720]),
    firework("2.5", "65", "2.5", [65280, 16777215], "star"),
    firework("-1.5", "65", "2.5", [255, 16711935], "burst"),
    firework("2.5", "65", "-1.5", [16766720], "creeper"),
    firework("-1.5", "65", "-1.5", [43775, 16777215], "large_ball"),
    firework("0.5", "66", "3.5", [16711680, 65280, 255], "star"),
]) + "\n" + msg("Fireworks show! Nothing happened, but it looked sick.", "light_purple"))

weird("pumpkin_head", 8, f"""
execute positioned {TOP} run item replace entity @p armor.head with minecraft:carved_pumpkin
""" + msg("You are now a pumpkin. Enjoy the view.", "light_purple"))

weird("blindness", 6, f"""
execute positioned {TOP} run effect give @a[distance=..6] minecraft:blindness 6 0
execute positioned {TOP} run effect give @a[distance=..6] minecraft:darkness 6 0
""" + msg("Lights out! Don't move...", "light_purple"))

weird("zoomies", 8, f"""
execute positioned {TOP} run effect give @a[distance=..6] minecraft:speed 60 3
execute positioned {TOP} run effect give @a[distance=..6] minecraft:jump_boost 60 2
execute positioned {TOP} run effect give @a[distance=..6] minecraft:haste 60 2
""" + msg("ZOOMIES! Speed, jump boost and haste for a minute. On a one-block. Careful.", "light_purple"))

weird("tiny_slimes", 6, "\n".join(
    f"summon minecraft:slime 0.5 {64 + i} 0.5 {{Size:0}}" for i in range(6)
) + "\n" + msg("Tiny slimes! They're basically harmless. Basically.", "light_purple"))

weird("dj", 6, f"""
{GIVE} minecraft:jukebox 1
execute store result score #r2 ob.rng run random value 1..3
execute if score #r2 ob.rng matches 1 run {GIVE} minecraft:music_disc_pigstep 1
execute if score #r2 ob.rng matches 2 run {GIVE} minecraft:music_disc_otherside 1
execute if score #r2 ob.rng matches 3 run {GIVE} minecraft:music_disc_cat 1
playsound minecraft:music_disc.pigstep record @a 0 64 0 1 1
""" + msg("DJ TIME. Jukebox + a music disc. Drop the beat.", "light_purple"))

weird("bats", 6, "\n".join(
    f"summon minecraft:bat 0.5 {65 + (i % 3)} 0.5" for i in range(10)
) + f"\nexecute positioned {TOP} run effect give @a[distance=..6] minecraft:darkness 4 0\n"
    + msg("BATS! So many bats.", "light_purple"))

weird("giant", 5, f"""
summon minecraft:giant 0.5 64 2.5
""" + msg("A GIANT ZOMBIE appeared. It just... stands there. Menacingly.", "light_purple"))

weird("villager_rave", 6, f"""
summon minecraft:villager {TOP}
summon minecraft:villager 0.5 65 0.5
summon minecraft:villager 0.5 66 0.5
summon minecraft:villager 0.5 67 0.5
summon minecraft:wandering_trader 0.5 68 0.5
playsound minecraft:music_disc.pigstep record @a 0 64 0 1 1
""" + msg("VILLAGER RAVE! Hmmm. Hmm hmm hmm.", "light_purple"))

weird("frogs", 5, f"""
summon minecraft:frog {TOP} {{variant:"minecraft:temperate"}}
summon minecraft:frog 0.5 65 0.5 {{variant:"minecraft:warm"}}
summon minecraft:frog 0.5 66 0.5 {{variant:"minecraft:cold"}}
summon minecraft:frog 0.5 67 0.5 {{variant:"minecraft:warm"}}
""" + msg("Frogs! All three kinds. Ribbit.", "light_purple"))

weird("snow_day", 6, f"""
weather clear
summon minecraft:snow_golem {TOP}
summon minecraft:snow_golem 0.5 66 0.5
{GIVE} minecraft:snowball 32
""" + msg("Snow day! Two snow golems and 32 snowballs. Snowball fight.", "light_purple"))

weird("pig_parade", 5, "\n".join(
    f"summon minecraft:pig 0.5 {64 + i} 0.5" for i in range(6)
) + f"\n{GIVE} minecraft:saddle 1\n{GIVE} minecraft:carrot_on_a_stick 1\n"
    + msg("Pig parade + a saddle + carrot on a stick. Ride a pig off the edge, I dare you.", "light_purple"))

weird("bees", 5, f"""
summon minecraft:bee 0.5 65 0.5
summon minecraft:bee 0.5 66 0.5
summon minecraft:bee 0.5 66 0.5
summon minecraft:bee 0.5 67 0.5
{GIVE} minecraft:honey_bottle 2
""" + msg("Bees! Don't hit them. Seriously, don't.", "light_purple"))

# ---- dispatch ---------------------------------------------------------------
fn("lucky/trigger", f"""
scoreboard players set #lucky ob.flag 0
scoreboard players add #luckycount ob.stats 1
function lucky:block/plain
particle minecraft:totem_of_undying 0.5 64.5 0.5 0.6 0.6 0.6 0.25 80 force
playsound minecraft:entity.firework_rocket.twinkle master @a 0 64 0 1 1
execute store result score #r ob.rng run random value 1..100
execute if score #r ob.rng matches 1..50 run function lucky:lucky/good
execute if score #r ob.rng matches 51..80 run function lucky:lucky/bad
execute if score #r ob.rng matches 81..100 run function lucky:lucky/weird
""")
fn("lucky/good", weighted_dispatch("#r", GOOD, "function lucky:event/good/{v}"))
fn("lucky/bad", weighted_dispatch("#r", BAD, "function lucky:event/bad/{v}"))
fn("lucky/weird", weighted_dispatch("#r", WEIRD, "function lucky:event/weird/{v}"))

# ---------------------------------------------------------------------------
# Boss: the dragon at BOSS_AT blocks
# ---------------------------------------------------------------------------
fn("boss/start", f"""
scoreboard players set #boss ob.flag 1
scoreboard players set #dragon_gone ob.flag 0
scoreboard players set #dragon_dying ob.flag 0
scoreboard players set #thresh ob.count 99999
fill -6 62 -6 6 62 6 minecraft:obsidian
fill -5 62 -5 5 62 5 minecraft:end_stone
setblock {BLOCK} minecraft:chest{{LootTable:"lucky:boss/kit"}}
title @a times 10 90 20
title @a title {{"text":"THE DRAGON","color":"dark_purple","bold":true}}
title @a subtitle {{"text":"FINAL BOSS. An arena rose from the void. SLAY IT.","color":"light_purple"}}
playsound minecraft:entity.ender_dragon.growl master @a 0 64 0 3 0.7
playsound minecraft:entity.wither.spawn master @a 0 64 0 1 0.5
summon minecraft:ender_dragon 0.5 95 0.5
""" + tell([{"text": "800 BLOCKS. ", "color": "dark_purple", "bold": True},
            {"text": "The Ender Dragon is here. A 13x13 end stone arena rose under you and a boss kit chest is on the block. Shoot it when it perches, run when it breathes.", "color": "white"}]))

fn("boss/tick", f"""
execute if entity @a[scores={{ob.dragonkill=1..}}] run function lucky:boss/win
execute if score #boss ob.flag matches 1 if entity @e[type=minecraft:ender_dragon] run scoreboard players set #dragon_gone ob.flag 0
execute if score #boss ob.flag matches 1 store result score #ddt ob.flag run data get entity @e[type=minecraft:ender_dragon,limit=1] DragonDeathTime
execute if score #boss ob.flag matches 1 if score #ddt ob.flag matches 1.. run scoreboard players set #dragon_dying ob.flag 1
execute if score #boss ob.flag matches 1 unless entity @e[type=minecraft:ender_dragon] run scoreboard players add #dragon_gone ob.flag 1
execute if score #boss ob.flag matches 1 if score #dragon_dying ob.flag matches 1 if score #dragon_gone ob.flag matches 40.. run function lucky:boss/win
""")

fn("boss/win", f"""
scoreboard players set #boss ob.flag 2
scoreboard players reset @a ob.dragonkill
title @a times 10 120 30
title @a title {{"text":"DRAGON SLAIN!","color":"gold","bold":true}}
title @a subtitle {{"text":"You beat One Block: Lucky Block Edition!","color":"yellow"}}
playsound minecraft:ui.toast.challenge_complete master @a 0 64 0 1 1
playsound minecraft:entity.ender_dragon.death master @a 0 64 0 1 1
{firework("0.5", "66", "0.5", [16766720, 16777215])}
{firework("4.5", "66", "4.5", [11141290, 16766720], "star")}
{firework("-3.5", "66", "4.5", [43775, 16777215], "burst")}
{firework("4.5", "66", "-3.5", [16711680, 65280], "large_ball")}
{firework("-3.5", "66", "-3.5", [16711935, 16766720], "star")}
execute positioned {TOP} run give @a[distance=..64] minecraft:dragon_egg 1
execute positioned {TOP} run give @a[distance=..64] minecraft:dragon_head 1
execute positioned {TOP} run give @a[distance=..64] minecraft:elytra 1
execute positioned {TOP} run give @a[distance=..64] minecraft:firework_rocket 64
execute positioned {TOP} run xp add @a[distance=..64] 5000 points
""" + tell([{"text": "YOU WIN! ", "color": "gold", "bold": True},
            {"text": "Dragon egg, dragon head, elytra and 64 rockets for everyone. The block keeps going forever in Lucky Chaos, so keep building your sky island.", "color": "white"}]))

# ---------------------------------------------------------------------------
# Loot tables
# ---------------------------------------------------------------------------
TOOLS_WOOD = [item("wooden_pickaxe", 4), item("wooden_axe", 3), item("stone_pickaxe", 2), item("wooden_sword", 2)]

loot("chest/phase_1", table([
    ((3, 6), [
        item("oak_sapling", 12, 1, 3), item("birch_sapling", 6, 1, 2), item("spruce_sapling", 5, 1, 2),
        item("wheat_seeds", 10, 2, 5), item("bone_meal", 8, 2, 6), item("string", 8, 2, 5), item("apple", 8, 1, 3),
        item("bread", 8, 1, 3), item("torch", 8, 4, 10), item("coal", 6, 2, 6), item("stick", 6, 4, 10),
        item("pumpkin_seeds", 4, 1, 3), item("melon_seeds", 4, 1, 3), item("sugar_cane", 5, 1, 4),
        item("carrot", 5, 1, 4), item("potato", 5, 1, 4), item("beetroot_seeds", 3, 1, 3), item("sweet_berries", 4, 2, 5),
        item("leather", 4, 1, 3), item("feather", 4, 1, 3), item("egg", 4, 1, 4), item("flint", 4, 1, 3),
        item("white_wool", 4, 1, 4), item("iron_ingot", 4, 1, 2), item("bucket", 3), item("water_bucket", 2),
        item("cocoa_beans", 2, 1, 3), item("bamboo", 3, 1, 4), item("cactus", 2, 1, 2), item("kelp", 2, 1, 3),
    ] + TOOLS_WOOD),
]))

loot("chest/phase_2", table([
    ((3, 6), [
        item("iron_ingot", 10, 1, 4), item("coal", 10, 3, 8), item("raw_copper", 8, 2, 6), item("raw_iron", 8, 1, 3),
        item("gold_ingot", 5, 1, 3), item("lapis_lazuli", 6, 2, 6), item("redstone", 6, 3, 8), item("torch", 8, 6, 12),
        item("iron_pickaxe", 4), item("iron_sword", 3), item("iron_axe", 3), item("shield", 3), item("rail", 4, 4, 10),
        item("minecart", 2), item("tnt", 3, 1, 2), item("string", 5, 2, 5), item("arrow", 6, 4, 12), item("bow", 3),
        item("diamond", 2, 1, 2), item("emerald", 3, 1, 3), item("bucket", 4), item("water_bucket", 4), item("lava_bucket", 4),
        item("amethyst_shard", 4, 2, 5), item("glow_berries", 4, 2, 5), item("moss_block", 3, 2, 4),
        item("book", 2, 1, 1, rand_ench()), item("cooked_porkchop", 6, 2, 5), item("bread", 6, 2, 4), item("oak_sapling", 5, 1, 2),
        item("iron_helmet", 2), item("iron_boots", 2), item("golden_apple", 1), item("name_tag", 1),
    ]),
]))

loot("chest/phase_3", table([
    ((3, 6), [
        item("cocoa_beans", 6, 2, 5), item("bamboo", 6, 3, 8), item("melon_slice", 6, 3, 8), item("cherry_sapling", 5, 1, 2),
        item("jungle_sapling", 5, 1, 2), item("mangrove_propagule", 4, 1, 2), item("acacia_sapling", 4, 1, 2),
        item("snowball", 5, 4, 12), item("prismarine_shard", 5, 2, 6), item("prismarine_crystals", 4, 1, 4),
        item("nautilus_shell", 2), item("heart_of_the_sea", 1), item("cod", 5, 2, 4), item("salmon", 5, 2, 4),
        item("tropical_fish", 3, 1, 2), item("kelp", 4, 2, 5), item("sea_pickle", 3, 1, 3), item("honey_bottle", 4, 1, 2),
        item("honeycomb", 4, 1, 3), item("slime_ball", 4, 2, 5), item("emerald", 5, 1, 4), item("gold_ingot", 5, 1, 4),
        item("saddle", 3), item("lead", 3, 1, 2), item("name_tag", 2), item("book", 3, 1, 1, rand_ench()),
        item("trident", 1), item("diamond", 3, 1, 2), item("iron_ingot", 6, 2, 5), item("water_bucket", 3),
        item("sweet_berries", 4, 3, 6), item("glow_berries", 4, 3, 6), item("mud", 3, 3, 8), item("turtle_egg", 2),
        item("iron_chestplate", 2), item("iron_leggings", 2), item("golden_carrot", 3, 2, 5), item("cookie", 4, 3, 8),
    ]),
]))

loot("chest/phase_4", table([
    ((3, 6), [
        item("gold_ingot", 10, 2, 6), item("gold_nugget", 8, 4, 12), item("quartz", 8, 3, 8), item("blaze_rod", 5, 1, 3),
        item("blaze_powder", 5, 2, 5), item("ghast_tear", 3, 1, 2), item("magma_cream", 5, 2, 4), item("nether_wart", 6, 2, 5),
        item("crimson_fungus", 4, 1, 3), item("warped_fungus", 4, 1, 3), item("netherite_scrap", 2, 1, 2), item("ancient_debris", 1),
        item("potion", 4, 1, 1, potion("fire_resistance")), item("potion", 2, 1, 1, potion("long_fire_resistance")),
        item("golden_helmet", 3), item("golden_chestplate", 2), item("golden_boots", 3), item("golden_leggings", 2),
        item("obsidian", 5, 2, 5), item("glowstone_dust", 5, 2, 6), item("soul_torch", 4, 4, 10), item("crying_obsidian", 3, 1, 3),
        item("lantern", 3, 1, 3), item("music_disc_pigstep", 1), item("piglin_banner_pattern", 1), item("iron_ingot", 6, 2, 5),
        item("diamond", 3, 1, 2), item("golden_apple", 2), item("flint_and_steel", 3), item("fire_charge", 3, 2, 4),
        item("diamond_pickaxe", 1), item("bow", 2, 1, 1, ench(10, 20)), item("arrow", 6, 8, 16), item("cooked_porkchop", 6, 3, 6),
    ]),
]))

loot("chest/phase_5", table([
    ((3, 6), [
        item("ender_pearl", 8, 2, 5), item("chorus_fruit", 6, 2, 6), item("popped_chorus_fruit", 4, 2, 4), item("end_rod", 4, 2, 5),
        item("purpur_block", 4, 3, 8), item("shulker_shell", 2, 1, 2), item("echo_shard", 3, 1, 3), item("sculk", 3, 3, 6),
        item("music_disc_otherside", 1), item("amethyst_shard", 4, 2, 6), item("diamond", 5, 1, 3), item("ender_eye", 3, 1, 2),
        item("experience_bottle", 6, 4, 10), item("dragon_breath", 2, 1, 2), item("phantom_membrane", 3, 1, 3),
        item("elytra", 1), item("book", 4, 1, 1, ench(20, 35)), item("diamond_helmet", 2, 1, 1, ench(15, 25)),
        item("diamond_chestplate", 1, 1, 1, ench(15, 25)), item("diamond_leggings", 1, 1, 1, ench(15, 25)),
        item("diamond_boots", 2, 1, 1, ench(15, 25)), item("golden_apple", 4, 1, 2), item("enchanted_golden_apple", 1),
        item("netherite_ingot", 1), item("end_crystal", 2), item("heavy_core", 1), item("mace", 1), item("wind_charge", 4, 4, 8),
        item("breeze_rod", 3, 1, 3), item("obsidian", 4, 2, 6), item("golden_carrot", 5, 3, 8), item("cooked_beef", 5, 3, 6),
        item("diamond_sword", 2, 1, 1, ench(15, 25)), item("bow", 2, 1, 1, ench(15, 30)), item("arrow", 6, 8, 20),
    ]),
]))

loot("chest/phase_6", table([
    ((4, 7), [
        item("diamond", 8, 2, 5), item("emerald", 8, 2, 6), item("gold_ingot", 8, 3, 8), item("iron_ingot", 8, 4, 10),
        item("netherite_ingot", 2), item("netherite_scrap", 3, 1, 2), item("nether_star", 1), item("beacon", 1),
        item("totem_of_undying", 2), item("diamond_block", 2), item("emerald_block", 2), item("gold_block", 3), item("iron_block", 3),
        item("golden_apple", 5, 1, 3), item("enchanted_golden_apple", 2), item("experience_bottle", 6, 6, 16),
        item("book", 5, 1, 1, ench(25, 40)), item("diamond_sword", 2, 1, 1, ench(20, 35)), item("diamond_pickaxe", 2, 1, 1, ench(20, 35)),
        item("diamond_helmet", 2, 1, 1, ench(20, 30)), item("diamond_chestplate", 2, 1, 1, ench(20, 30)),
        item("diamond_leggings", 2, 1, 1, ench(20, 30)), item("diamond_boots", 2, 1, 1, ench(20, 30)),
        item("netherite_sword", 1, 1, 1, ench(25, 35)), item("netherite_pickaxe", 1, 1, 1, ench(25, 35)),
        item("elytra", 1), item("saddle", 3), item("wolf_spawn_egg", 2), item("cat_spawn_egg", 2), item("horse_spawn_egg", 2),
        item("villager_spawn_egg", 2), item("cow_spawn_egg", 2), item("sheep_spawn_egg", 2), item("bee_spawn_egg", 2),
        item("music_disc_pigstep", 1), item("music_disc_otherside", 1), item("music_disc_relic", 1), item("firework_rocket", 4, 8, 16),
        item("ender_pearl", 5, 3, 8), item("end_crystal", 2, 1, 2), item("tnt", 4, 4, 10), item("oak_sapling", 4, 2, 4),
        item("water_bucket", 4), item("lava_bucket", 4), item("obsidian", 4, 4, 10), item("glass", 4, 8, 16),
        item("sea_lantern", 3, 2, 6), item("shroomlight", 3, 2, 6), item("wither_skeleton_skull", 1),
    ]),
]))

# phase kits (the chest that spawns when you enter a phase)
loot("chest/kit_2", table([
    (1, [item("iron_pickaxe", 1, 1, 1, named("Cave Cracker", "aqua"))]),
    (1, [item("torch", 1, 16, 16)]), (1, [item("bread", 1, 8, 8)]), (1, [item("water_bucket", 1)]), (1, [item("lava_bucket", 1)]),
    (1, [item("oak_sapling", 1, 2, 2)]), (1, [item("bone_meal", 1, 6, 6)]), (1, [item("iron_ingot", 1, 5, 5)]), (1, [item("shield", 1)]),
]))
loot("chest/kit_3", table([
    (1, [item("diamond", 1, 3, 3)]), (1, [item("book", 1, 1, 1, rand_ench())]), (1, [item("cooked_beef", 1, 8, 8)]),
    (1, [item("saddle", 1)]), (1, [item("name_tag", 1)]), (1, [item("bamboo", 1, 4, 4)]), (1, [item("cherry_sapling", 1)]),
    (1, [item("jungle_sapling", 1)]), (1, [item("iron_chestplate", 1)]), (1, [item("bow", 1)]), (1, [item("arrow", 1, 24, 24)]),
]))
loot("chest/kit_4", table([
    (1, [item("diamond_pickaxe", 1, 1, 1, named("Nether Nibbler", "red"))]), (1, [item("potion", 1, 1, 1, potion("long_fire_resistance"))]),
    (1, [item("obsidian", 1, 10, 10)]), (1, [item("flint_and_steel", 1)]), (1, [item("golden_apple", 1, 2, 2)]),
    (1, [item("blaze_rod", 1, 2, 2)]), (1, [item("nether_wart", 1, 4, 4)]), (1, [item("iron_helmet", 1)]), (1, [item("iron_boots", 1)]),
    (1, [item("cooked_porkchop", 1, 8, 8)]),
]))
loot("chest/kit_5", table([
    (1, [item("diamond_sword", 1, 1, 1, ench(25, 30) + named("Voidsplitter", "dark_purple"))]), (1, [item("ender_pearl", 1, 8, 8)]),
    (1, [item("bow", 1, 1, 1, ench(20, 25))]), (1, [item("arrow", 1, 32, 32)]), (1, [item("golden_carrot", 1, 16, 16)]),
    (1, [item("enchanted_golden_apple", 1)]), (1, [item("experience_bottle", 1, 16, 16)]), (1, [item("diamond_leggings", 1)]),
    (1, [item("shield", 1)]),
]))
loot("chest/kit_6", table([
    (1, [item("netherite_ingot", 1, 2, 2)]), (1, [item("totem_of_undying", 1)]),
    (1, [item("diamond_chestplate", 1, 1, 1, ench(25, 30) + named("Chaos Plate", "gold"))]), (1, [item("diamond_helmet", 1, 1, 1, ench(20, 30))]),
    (1, [item("diamond_boots", 1, 1, 1, ench(20, 30))]), (1, [item("golden_apple", 1, 4, 4)]), (1, [item("firework_rocket", 1, 16, 16)]),
    (1, [item("end_crystal", 1, 2, 2)]), (1, [item("water_bucket", 1)]), (1, [item("lava_bucket", 1)]),
]))

loot("boss/kit", table([
    (1, [item("bow", 1, 1, 1, ench(30, 30) + named("Dragonbane", "dark_purple"))]), (1, [item("arrow", 1, 64, 64)]), (1, [item("arrow", 1, 64, 64)]),
    (1, [item("golden_apple", 1, 8, 8)]), (1, [item("enchanted_golden_apple", 1, 2, 2)]),
    (1, [item("potion", 1, 1, 1, potion("strong_strength"))]), (1, [item("potion", 1, 2, 2, potion("long_slow_falling"))]),
    (1, [item("potion", 1, 1, 1, potion("strong_regeneration"))]), (1, [item("shield", 1)]), (1, [item("cooked_beef", 1, 16, 16)]),
    (1, [item("ender_pearl", 1, 8, 8)]), (1, [item("totem_of_undying", 1)]), (1, [item("cobblestone", 1, 64, 64)]),
]))

# lucky event tables
loot("lucky/gear", table([
    (1, [
        item("diamond_sword", 10, 1, 1, ench(20, 39) + named("Lucky Blade")), item("diamond_pickaxe", 10, 1, 1, ench(20, 39) + named("Lucky Pick")),
        item("diamond_axe", 6, 1, 1, ench(20, 39) + named("Lucky Chopper")), item("diamond_shovel", 3, 1, 1, ench(20, 39)),
        item("diamond_helmet", 6, 1, 1, ench(20, 39)), item("diamond_chestplate", 6, 1, 1, ench(20, 39)),
        item("diamond_leggings", 6, 1, 1, ench(20, 39)), item("diamond_boots", 6, 1, 1, ench(20, 39)),
        item("bow", 6, 1, 1, ench(20, 39) + named("Lucky Shot")), item("crossbow", 4, 1, 1, ench(20, 39)),
        item("trident", 2, 1, 1, ench(20, 39)), item("mace", 2, 1, 1, ench(20, 39) + named("Lucky Smash")),
        item("netherite_sword", 1, 1, 1, ench(30, 39) + named("Jackpot Blade")), item("netherite_pickaxe", 1, 1, 1, ench(30, 39) + named("Jackpot Pick")),
    ]),
]))
loot("lucky/books", table([((1, 2), [item("book", 1, 1, 1, ench(20, 39))])]))
loot("lucky/starter", table([
    (1, [item("oak_sapling", 1, 3, 3)]), (1, [item("wheat_seeds", 1, 4, 4)]), (1, [item("bone_meal", 1, 8, 8)]),
    (1, [item("bread", 1, 6, 6)]), (1, [item("water_bucket", 1)]), (1, [item("carrot", 1, 3, 3)]), (1, [item("potato", 1, 3, 3)]),
    (1, [item("sugar_cane", 1, 3, 3)]), (1, [item("torch", 1, 8, 8)]),
]))
loot("lucky/treasure", table([
    ((5, 8), [
        item("diamond", 10, 2, 6), item("emerald", 10, 2, 8), item("gold_ingot", 10, 3, 10), item("iron_ingot", 10, 4, 12),
        item("lapis_lazuli", 6, 4, 12), item("golden_apple", 6, 1, 3), item("enchanted_golden_apple", 2), item("experience_bottle", 6, 6, 16),
        item("book", 5, 1, 1, ench(20, 39)), item("totem_of_undying", 2), item("netherite_scrap", 2, 1, 2), item("ender_pearl", 5, 2, 6),
        item("diamond_block", 1), item("gold_block", 2), item("music_disc_cat", 1), item("name_tag", 3), item("saddle", 3),
        item("water_bucket", 4), item("lava_bucket", 4), item("oak_sapling", 4, 2, 4), item("cooked_beef", 5, 4, 8),
    ]),
]))

# ---------------------------------------------------------------------------
# datapack meta + tags
# ---------------------------------------------------------------------------
files[DP / "pack.mcmeta"] = json.dumps({"pack": {
    "pack_format": DATAPACK_FORMAT,
    "supported_formats": {"min_inclusive": DATAPACK_FORMAT, "max_inclusive": 9999},
    "min_format": [DATAPACK_FORMAT, 0],
    "max_format": [9999, 9999],
    "description": "One Block: Lucky Block Edition - by Echoes in the Dark",
}}, indent=2) + "\n"
files[DP / "data" / "minecraft" / "tags" / "function" / "load.json"] = json.dumps({"values": ["lucky:load"]}) + "\n"
files[DP / "data" / "minecraft" / "tags" / "function" / "tick.json"] = json.dumps({"values": ["lucky:tick"]}) + "\n"


# ---------------------------------------------------------------------------
# Resource pack (embedded as resources.zip): lucky block texture on sponge
# ---------------------------------------------------------------------------
LUCKY_ART = [
    "BBBBBBBBBBBBBBBB",
    "BYYYYYYYYYYYYYYB",
    "BYYYYYKKKKKYYYYB",
    "BYYYKKKYYYKKKYYB",
    "BYYYKKYYYYYKKYYB",
    "BYYYYYYYYYKKKYYB",
    "BYYYYYYYYKKKYYYB",
    "BYYYYYYYKKKYYYYB",
    "BYYYYYYKKKYYYYYB",
    "BYYYYYYKKYYYYYYB",
    "BYYYYYYYYYYYYYYB",
    "BYYYYYYKKYYYYYYB",
    "BYYYYYYKKYYYYYYB",
    "BYYYYYYYYYYYYYYB",
    "BYYYYYYYYYYYYYYB",
    "BBBBBBBBBBBBBBBB",
]


def lucky_texture(bright: bool) -> Image.Image:
    pal = {
        "B": (122, 85, 10, 255),
        "Y": (255, 214, 48, 255) if not bright else (255, 236, 110, 255),
        "K": (28, 22, 16, 255),
    }
    img = Image.new("RGBA", (16, 16))
    rnd = random.Random(7)
    for y, row in enumerate(LUCKY_ART):
        for x, ch in enumerate(row):
            r, g, b, a = pal[ch]
            if ch == "Y":  # subtle noise so it reads like a block texture
                d = rnd.randint(-10, 10)
                r, g, b = max(0, min(255, r + d)), max(0, min(255, g + d)), max(0, min(255, b))
            if ch == "B" and (x in (0, 15)) != (y in (0, 15)):
                r, g, b = 150, 105, 20
            img.putpixel((x, y), (r, g, b, a))
    return img


def png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def build_resource_pack() -> bytes:
    frames = Image.new("RGBA", (16, 32))
    frames.paste(lucky_texture(False), (0, 0))
    frames.paste(lucky_texture(True), (0, 16))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("pack.mcmeta", json.dumps({"pack": {
            "pack_format": RESOURCEPACK_FORMAT,
            "supported_formats": {"min_inclusive": RESOURCEPACK_FORMAT, "max_inclusive": 9999},
            "min_format": [RESOURCEPACK_FORMAT, 0],
            "max_format": [9999, 9999],
            "description": "One Block: Lucky Block Edition textures"}}, indent=2))
        z.writestr("pack.png", png_bytes(lucky_texture(False).resize((64, 64), Image.NEAREST)))
        z.writestr("assets/minecraft/textures/block/sponge.png", png_bytes(frames))
        z.writestr("assets/minecraft/textures/block/sponge.png.mcmeta",
                   json.dumps({"animation": {"frametime": 12, "interpolate": True}}))
        z.writestr("assets/minecraft/lang/en_us.json", json.dumps({
            "block.minecraft.sponge": "Lucky Block",
            "block.minecraft.yellow_shulker_box": "Lucky Box",
        }, indent=2))
    return buf.getvalue()


# ---------------------------------------------------------------------------
# level.dat
# ---------------------------------------------------------------------------
def build_level_dat(seed: int) -> bytes:
    def dim(kind: str, generator: Compound) -> Compound:
        return Compound({"type": String(kind), "generator": generator})

    overworld = Compound({
        "type": String("minecraft:flat"),
        "settings": Compound({
            "biome": String("minecraft:plains"),
            "features": Byte(0),
            "lakes": Byte(0),
            "layers": List[Compound]([Compound({"block": String("minecraft:air"), "height": Int(1)})]),
            "structure_overrides": List[String]([]),
        }),
    })
    nether = Compound({
        "type": String("minecraft:noise"),
        "settings": String("minecraft:nether"),
        "biome_source": Compound({"type": String("minecraft:multi_noise"), "preset": String("minecraft:nether")}),
    })
    end = Compound({
        "type": String("minecraft:noise"),
        "settings": String("minecraft:end"),
        "biome_source": Compound({"type": String("minecraft:the_end")}),
    })
    now_ms = int(time.time() * 1000)
    data = Compound({
        "allowCommands": Byte(1),
        "BorderCenterX": Double(0.0), "BorderCenterZ": Double(0.0), "BorderDamagePerBlock": Double(0.2),
        "BorderSafeZone": Double(5.0), "BorderSize": Double(59999968.0), "BorderSizeLerpTarget": Double(59999968.0),
        "BorderSizeLerpTime": Long(0), "BorderWarningBlocks": Double(5.0), "BorderWarningTime": Double(15.0),
        "clearWeatherTime": Int(0),
        "CustomBossEvents": Compound(),
        "DataPacks": Compound({
            "Enabled": List[String]([String("vanilla"), String(f"file/{PACK_ID}")]),
            "Disabled": List[String]([]),
        }),
        "DataVersion": Int(DATA_VERSION),
        "DayTime": Long(1000),
        "DragonFight": Compound({
            "NeedsStateScanning": Byte(1), "DragonKilled": Byte(0), "PreviouslyKilled": Byte(0),
            "IsRespawning": Byte(0), "Gateways": List[Int]([Int(i) for i in range(20)]),
        }),
        "Difficulty": Byte(2), "DifficultyLocked": Byte(0),
        "GameRules": Compound({k: String(v) for k, v in GAMERULES.items()}),
        "GameType": Int(0),
        "hardcore": Byte(0),
        "initialized": Byte(1),
        "LastPlayed": Long(now_ms),
        "LevelName": String(WORLD_NAME),
        "raining": Byte(0), "rainTime": Int(120000),
        "ScheduledEvents": List[Compound]([]),
        "ServerBrands": List[String]([String("vanilla")]),
        "SpawnAngle": Float(0.0), "SpawnX": Int(0), "SpawnY": Int(64), "SpawnZ": Int(0),
        "Time": Long(0),
        "thundering": Byte(0), "thunderTime": Int(120000),
        "version": Int(19133),
        "Version": Compound({"Id": Int(DATA_VERSION), "Name": String(VERSION_NAME), "Series": String("main"), "Snapshot": Byte(0)}),
        "WanderingTraderSpawnChance": Int(25), "WanderingTraderSpawnDelay": Int(24000),
        "WasModded": Byte(0),
        "WorldGenSettings": Compound({
            "bonus_chest": Byte(0),
            "seed": Long(seed),
            "generate_features": Byte(0),
            "dimensions": Compound({
                "minecraft:overworld": dim("minecraft:overworld", overworld),
                "minecraft:the_nether": dim("minecraft:the_nether", nether),
                "minecraft:the_end": dim("minecraft:the_end", end),
            }),
        }),
        "enabled_features": List[String]([String("minecraft:vanilla")]),
    })
    root = nbtlib.File(Compound({"Data": data}), gzipped=True)
    buf = io.BytesIO()
    root.write(buf)  # uncompressed NBT
    import gzip
    return gzip.compress(buf.getvalue())


# ---------------------------------------------------------------------------
# write everything
# ---------------------------------------------------------------------------
def main() -> None:
    if WORLD_DIR.exists():
        shutil.rmtree(WORLD_DIR)
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")

    (WORLD_DIR / "level.dat").write_bytes(build_level_dat(seed=20261014))
    (WORLD_DIR / "resources.zip").write_bytes(build_resource_pack())
    (WORLD_DIR / "icon.png").write_bytes(png_bytes(lucky_texture(False).resize((64, 64), Image.NEAREST)))

    # zip for sharing (folder name preserved inside the zip)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(WORLD_DIR.rglob("*")):
            if p.is_file():
                z.write(p, Path(WORLD_NAME) / p.relative_to(WORLD_DIR))

    n_fn = sum(1 for p in files if p.suffix == ".mcfunction")
    n_lt = sum(1 for p in files if p.suffix == ".json" and "loot_table" in p.parts)
    print(f"built {WORLD_DIR}")
    print(f"  {n_fn} functions, {n_lt} loot tables, {len(GOOD)} good / {len(BAD)} bad / {len(WEIRD)} weird lucky events")
    print(f"  zip: {ZIP_PATH} ({ZIP_PATH.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
