# One Block: Lucky Block Edition

A Minecraft: Java Edition world by **Echoes in the Dark**. You spawn in the void on a single
block. Break it and it comes back as something new: a random block, a loot chest, a mob, or a
**Lucky Block** that can make your day or wreck it. Survive six phases, build a sky island out of
whatever you pull, and at 800 blocks the **Ender Dragon** shows up for the final boss fight.

No mods. Everything runs on a vanilla datapack packed inside the world, plus a tiny built-in
resource pack that makes the Lucky Block look like a Lucky Block.

## Install (2 minutes)

1. Download `OneBlock_Lucky_Block.zip` from this folder and unzip it. You get a folder called
   `OneBlock Lucky Block`.
2. Put that folder inside your Minecraft `saves` folder:
   - **Windows:** press `Win + R`, type `%appdata%\.minecraft\saves`, Enter.
   - **Mac:** in Finder press `Cmd + Shift + G`, paste `~/Library/Application Support/minecraft/saves`.
   - **Linux:** `~/.minecraft/saves`
3. Start **Minecraft: Java Edition 1.21 or newer** (tested on 1.21.1 and the latest 26.3) and
   open the world from Singleplayer. If the game asks to back up or convert the world, say yes.
4. You are standing on the block. Punch it.

Works in LAN multiplayer too: Open to LAN, friends join, everyone shares the one block.

## How it plays

| Phase | Starts at | Theme | What shows up |
| --- | --- | --- | --- |
| 1 | block 0 | The Plains | grass, logs, leaves, stone, coal, animals |
| 2 | block 60 | The Caves | ores, deepslate, amethyst, zombies, skeletons, a rare spawner |
| 3 | block 150 | The Wild | jungle, cherry, ice, mud, prismarine, pandas, drowned, witches |
| 4 | block 260 | The Nether | netherrack, quartz, ancient debris, piglins, blazes, ghasts |
| 5 | block 400 | The End & Deep Dark | end stone, purpur, sculk, endermen, shulkers, breezes, a rare warden |
| 6 | block 560 | Lucky Chaos | everything, diamond ore, netherite, beacons, every mob |
| Boss | block 800 | THE DRAGON | a 13x13 arena rises from the void, a boss kit chest spawns, the dragon lands |

Every time you enter a new phase you get a **kit chest** on the block with the stuff you need
next (pickaxe, buckets, saplings, potions, gear).

Each block you break rolls:

- **Plain block** from the phase table (most of the time).
- **Loot chest or barrel** (10%) filled from a phase-specific loot table.
- **Mob** (10 to 14%) spawned right on top of you. Hold on.
- **Lucky Block** (6% in Phase 1, rising to 13% in Phase 6). Break it to roll an event:
  - **50% good:** diamonds, enchanted gear, enchanted books, golden apples, XP, a totem, a
    starter farm pack, water + lava buckets, a 3x3 land platform, an ore pillar, traders,
    pets, a treasure chest, a Lucky Box, a beacon kit, an iron golem, and a very rare elytra.
  - **30% bad:** TNT, creepers, anvils from the sky, lightning, hordes that scale with your
    phase, witches, skeleton squads, cobweb traps, levitation, poison clouds, silverfish, a fake
    diamond, a lava trap that clears after 5 seconds, midnight with phantoms, blazes, illagers,
    and two ultra-rare nightmares: the Warden (phase 5+) and the Wither (phase 6).
  - **20% weird:** chicken rain, rainbow sheep, a fireworks show, a pumpkin on your head,
    blindness, zoomies, tiny slimes, a jukebox and disc, bats, a Giant, a villager rave, frogs,
    snow golems, a pig parade, bees.

Drops pop **up** onto the block instead of falling into the void. If you fall, **void rescue**
teleports you back (you can turn it off). Inventory is kept on death. If the block turns into
something you can't mine yet, wait 2 minutes and it becomes dirt, or use the reroll command.

Beat the dragon and everyone gets a dragon egg, a dragon head, an elytra and 64 rockets. The
block keeps going forever after that in Lucky Chaos.

## Commands (type in chat)

| Command | Needs cheats? | What it does |
| --- | --- | --- |
| `/trigger ob.help` | no | shows the rules |
| `/trigger ob.rescue` | no | toggles void rescue on/off |
| `/trigger ob.reroll` | no | replaces a stuck block with dirt |
| `/function lucky:admin/stats` | yes | blocks, phase, lucky blocks, chests, mobs so far |
| `/function lucky:admin/skip_phase` | yes | jump to the next phase |
| `/function lucky:admin/reset` | yes | start over at block 0 |

Cheats are already enabled in the world for the admin commands.

## What's in this folder

```
oneblock-lucky-block/
  OneBlock_Lucky_Block.zip        <- the world, ready to share or sell
  world/OneBlock Lucky Block/     <- the same world, unzipped
    level.dat                     <- void superflat world, spawn on the block, gamerules
    icon.png                      <- lucky block icon in the world list
    resources.zip                 <- built-in texture pack (lucky block texture + names)
    datapacks/lucky_oneblock/     <- the whole game: 113 functions, 16 loot tables
  tools/build_oneblock_world.py   <- generates everything above
```

## Changing the game

Everything is generated from `tools/build_oneblock_world.py`. Edit the block tables, mob lists,
phase thresholds, lucky odds or events there, then run:

```
pip install nbtlib pillow
python3 tools/build_oneblock_world.py
```

It rewrites the `world/` folder and the zip. The datapack uses only vanilla commands, so it keeps
working across game updates: the world was booted on both a 1.21.1 and a 26.3 vanilla server and
every event, loot table and the boss fight were exercised from the console.

## Credits

Made by Echoes in the Dark. Minecraft is a trademark of Mojang/Microsoft. This is a fan-made
world; it does not include any Mojang assets.
