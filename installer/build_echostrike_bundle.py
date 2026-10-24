#!/usr/bin/env python3
"""
Packages Echo Strike for download. Run from the repo root after `./gradlew build` in echo-strike/
and after generating the arena world (echo-strike/run/saves/Echo Strike):

    python3 installer/build_echostrike_bundle.py

Writes into download/:
  Echo-Strike-ResourcePack.zip   the mod's textures, 3D gun models and language file as a normal
                                 Minecraft resource pack (drop into .minecraft/resourcepacks)
  Echo-Strike-World.zip          the arena world, with the resource pack embedded as resources.zip
                                 (Minecraft offers a world's own pack when you open it)
  Echo-Strike-AllInOne.zip       mods/ + saves/ + resourcepacks/ ready to unzip over .minecraft

The resource pack only carries art. The guns, movement, enemies and game modes are Java code,
so the mod jar (mods/echostrike-1.0.0.jar) is always required. (The mod's recipes and damage
types live in the jar too; shipping them again as a world datapack makes Minecraft flag the world
as "experimental", so the world carries no datapack.)
"""
import io
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, "echo-strike")
RES = os.path.join(MOD, "src", "main", "resources")
DOWNLOAD = os.path.join(ROOT, "download")
JAR = os.path.join(DOWNLOAD, "echostrike-1.0.0.jar")
WORLD_SRC = os.path.join(MOD, "run", "saves", "Echo Strike")
WORLD_NAME = "Echo Strike"

RESOURCE_PACK = os.path.join(DOWNLOAD, "Echo-Strike-ResourcePack.zip")
WORLD_ZIP = os.path.join(DOWNLOAD, "Echo-Strike-World.zip")
ALL_IN_ONE = os.path.join(DOWNLOAD, "Echo-Strike-AllInOne.zip")

PACK_FORMAT = 15  # Minecraft 1.20.1

SKIP_DIRS = {"playerdata", "stats", "advancements"}
SKIP_FILES = {"session.lock", "level.dat_old"}


def add_tree(z, src_dir, arc_prefix):
    for root, dirs, files in os.walk(src_dir):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(root, f)
            z.write(p, os.path.join(arc_prefix, os.path.relpath(p, src_dir)))


def resource_pack_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("pack.mcmeta", '{\n  "pack": {\n    "pack_format": %d,\n    "description": "Echo Strike - guns, gear and operatives (Echoes in the Dark)"\n  }\n}\n' % PACK_FORMAT)
        z.write(os.path.join(RES, "echostrike_logo.png"), "pack.png")
        add_tree(z, os.path.join(RES, "assets"), "assets")
    return buf.getvalue()


def write_world(z, prefix, pack):
    """Write the arena world into z under prefix (e.g. 'Echo Strike/' or 'saves/Echo Strike/')."""
    count = 0
    for root, dirs, files in os.walk(WORLD_SRC):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            if f in SKIP_FILES:
                continue
            p = os.path.join(root, f)
            z.write(p, prefix + os.path.relpath(p, WORLD_SRC))
            count += 1
    z.writestr(prefix + "resources.zip", pack)
    return count


README = """ECHO STRIKE - BloodStrike-style shooter inside Minecraft Java 1.20.1
An Echoes in the Dark original.

WHAT'S IN THIS ZIP
  mods/echostrike-1.0.0.jar            the mod (REQUIRED - the guns, movement, enemies and game modes are code)
  saves/Echo Strike/                   the arena world, with the resource pack already inside it
  resourcepacks/Echo-Strike-ResourcePack.zip   the same art as a normal resource pack, in case you want it everywhere

INSTALL (3 steps)
  1. Install Forge or NeoForge for Minecraft 1.20.1 (the Play-Echo-Strike.bat installer does this for you on Windows).
  2. Unzip this file over your .minecraft folder so you end up with .minecraft/mods/echostrike-1.0.0.jar
     and .minecraft/saves/Echo Strike/.
  3. Start the Forge profile, open the "Echo Strike" world. You spawn in the arena with a G18.

CONTROLS
  Left click shoot (hold for full auto)   Right click aim   R reload
  Sprint + crouch = slide                 Run at a block = vault / mantle
  /strike kit     /strike waves start     /strike br start [minutes] [bots]     /strike stop

GUNS: G18, Desert Eagle, MP5, UMP45, Vector, AK-47, M4A1, M870, AWM, M249. All ours, nothing copied.
"""


def main():
    os.makedirs(DOWNLOAD, exist_ok=True)
    if not os.path.isfile(JAR):
        raise SystemExit("missing " + JAR + " (run ./gradlew build in echo-strike and copy build/libs/echostrike-1.0.0.jar)")
    if not os.path.isfile(os.path.join(WORLD_SRC, "level.dat")):
        raise SystemExit("missing world at " + WORLD_SRC + " (run ./gradlew runClient -Pdevtest=\"Echo Strike\" -PdevtestMode=world)")

    pack = resource_pack_bytes()
    with open(RESOURCE_PACK, "wb") as f:
        f.write(pack)
    with zipfile.ZipFile(WORLD_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        n = write_world(z, WORLD_NAME + "/", pack)

    with zipfile.ZipFile(ALL_IN_ONE, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(JAR, "mods/" + os.path.basename(JAR))
        write_world(z, "saves/" + WORLD_NAME + "/", pack)
        z.writestr("resourcepacks/Echo-Strike-ResourcePack.zip", pack)
        z.writestr("README.txt", README)

    for p in (RESOURCE_PACK, WORLD_ZIP, ALL_IN_ONE):
        print(f"{os.path.relpath(p, ROOT)}: {os.path.getsize(p) / 1024 / 1024:.2f} MB")
    print(f"world files: {n}")


if __name__ == "__main__":
    main()
