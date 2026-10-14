#!/bin/bash
# Upgrade the generated 1.21-format world to the newest Minecraft save format by
# booting it once on a vanilla dedicated server, then stage it as the shipped world.
#
#   tools/upgrade_world.sh <path/to/java25> <path/to/server.jar>
#
# The server jar must be the Minecraft version you want the world saved as
# (26.3 was used for the shipped build). Get it from the Mojang version manifest:
#   https://piston-meta.mojang.com/mc/game/version_manifest_v2.json
#
# Why: newer game versions changed the world folder layout. A world saved in the
# old layout opens fine, but the game shows "This world needs to be upgraded,
# create a backup?" first. Shipping the upgraded layout removes that screen.
set -euo pipefail
JAVA=$1; JAR=$(realpath "$2")
ROOT=$(cd "$(dirname "$0")/.." && pwd)
SRC="$ROOT/legacy-1.21/OneBlock Lucky Block"
DEST="$ROOT/world/OneBlock Lucky Block"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

cp -r "$SRC" "$WORK/world"
echo "eula=true" > "$WORK/eula.txt"
printf 'level-name=world\nonline-mode=false\nserver-port=25597\nview-distance=4\nsimulation-distance=4\nmax-players=1\ndifficulty=normal\n' > "$WORK/server.properties"

# boot, wait for "Done", stop
(cd "$WORK" && { sleep 1; while ! grep -q "Done (" logs/latest.log 2>/dev/null; do sleep 1; done; sleep 3; echo stop; } | "$JAVA" -Xmx1500M -jar "$JAR" nogui > "$WORK/console.log" 2>&1)
grep -q "Saving chunks" "$WORK/console.log" || { echo "server did not save the world; see $WORK/console.log"; exit 1; }

rm -rf "$DEST"
mkdir -p "$ROOT/world"
cp -r "$WORK/world" "$DEST"
rm -rf "$DEST/session.lock" "$DEST/level.dat_old" "$DEST/players"
cp "$SRC/icon.png" "$DEST/icon.png"

# main zip (folder name preserved inside)
(cd "$ROOT/world" && rm -f "$ROOT/OneBlock_Lucky_Block.zip" && zip -q -r "$ROOT/OneBlock_Lucky_Block.zip" "OneBlock Lucky Block")
echo "upgraded world staged at: $DEST"
echo "zip: $ROOT/OneBlock_Lucky_Block.zip ($(du -k "$ROOT/OneBlock_Lucky_Block.zip" | cut -f1) KB)"
