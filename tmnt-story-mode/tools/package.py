#!/usr/bin/env python3
"""
Makes the downloads in ../download:

  turtlepower-<version>.jar             the mod (put in .minecraft/mods)
  TMNT-Story-Mode-World.zip             the pre-built world (unzip into .minecraft/saves)
  TMNT-Story-Mode-CurseForge.zip        mod + world + Forge in ONE file: import it in the CurseForge app
                                        (or Prism Launcher / ATLauncher) and hit Play
  TMNT-Story-Mode.mrpack                the same thing for the Modrinth App / Prism Launcher

Before running: build the jar (./gradlew build) and build the world with the dev server
(./gradlew runServer with level-type=turtlepower:new_york, wait for "TMNT story world built", then stop it).

Needs: pip install nbtlib
"""
import json
import os
import shutil
import sys
import tempfile
import zipfile

import nbtlib

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
OUT = os.path.join(os.path.dirname(PROJECT), "download")
WORLD_NAME = "TMNT Story Mode"
MC = "1.20.1"
FORGE = "47.4.10"


def props():
    p = {}
    with open(os.path.join(PROJECT, "gradle.properties")) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                p[k] = v
    return p


def prepare_world(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("session.lock", "playerdata", "stats", "advancements", "*.old"))
    level = nbtlib.load(os.path.join(dst, "level.dat"))
    data = level["Data"]
    data["LevelName"] = nbtlib.String(WORLD_NAME)
    data["allowCommands"] = nbtlib.Byte(1)  # cheats on, so /tmnt chapter, /tmnt skip etc. work
    data["GameType"] = nbtlib.Int(0)
    data["Difficulty"] = nbtlib.Byte(2)
    if "Player" in data:
        del data["Player"]
    level.save()
    for junk in ("level.dat_old",):
        path = os.path.join(dst, junk)
        if os.path.exists(path):
            os.remove(path)


def zip_dir(zf, folder, arc_prefix):
    for root, _, files in os.walk(folder):
        for name in files:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, folder)
            zf.write(full, os.path.join(arc_prefix, rel))


def main():
    p = props()
    version = p["mod_version"]
    jar = os.path.join(PROJECT, "build", "libs", f"turtlepower-{version}.jar")
    world = os.path.join(PROJECT, "run", "world")
    if not os.path.exists(jar) or not os.path.exists(os.path.join(world, "level.dat")):
        sys.exit("Build the jar and the world first (see the top of this file).")
    os.makedirs(OUT, exist_ok=True)

    jar_name = f"turtlepower-{version}.jar"
    shutil.copy(jar, os.path.join(OUT, jar_name))

    with tempfile.TemporaryDirectory() as tmp:
        wdir = os.path.join(tmp, WORLD_NAME)
        prepare_world(world, wdir)

        with zipfile.ZipFile(os.path.join(OUT, "TMNT-Story-Mode-World.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
            zip_dir(zf, wdir, WORLD_NAME)

        manifest = {
            "minecraft": {"version": MC, "modLoaders": [{"id": f"forge-{FORGE}", "primary": True}]},
            "manifestType": "minecraftModpack",
            "manifestVersion": 1,
            "name": "TMNT Story Mode",
            "version": version,
            "author": "Echoes in the Dark",
            "files": [],
            "overrides": "overrides",
        }
        with zipfile.ZipFile(os.path.join(OUT, "TMNT-Story-Mode-CurseForge.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.write(jar, f"overrides/mods/{jar_name}")
            zip_dir(zf, wdir, f"overrides/saves/{WORLD_NAME}")

        index = {
            "formatVersion": 1,
            "game": "minecraft",
            "versionId": version,
            "name": "TMNT Story Mode",
            "summary": "Fan-made TMNT story mode: you are Raphael. Mod + pre-built world.",
            "files": [],
            "dependencies": {"minecraft": MC, "forge": FORGE},
        }
        with zipfile.ZipFile(os.path.join(OUT, "TMNT-Story-Mode.mrpack"), "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("modrinth.index.json", json.dumps(index, indent=2))
            zf.write(jar, f"overrides/mods/{jar_name}")
            zip_dir(zf, wdir, f"overrides/saves/{WORLD_NAME}")

    for f in sorted(os.listdir(OUT)):
        print(f"{os.path.getsize(os.path.join(OUT, f)) / 1024 / 1024:6.2f} MB  {f}")


if __name__ == "__main__":
    main()
