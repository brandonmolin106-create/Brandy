#!/bin/bash
# Second wave (underwater, surface, shelf, space) - waits for the first queue to finish.
#   ./render_queue2.sh OUTROOT
OUT="$1"
B=${BLENDER:-/opt/blender/blender-4.5.14-linux-x64/blender}
HERE="$(cd "$(dirname "$0")" && pwd)"
while pgrep -f "[r]ender_queue.sh" > /dev/null; do sleep 30; done
run() {  # shot step
  echo "=== $1 (step $2) $(date +%T)"
  STEP=$2 "$B" -b --factory-startup --python "$HERE/run_any.py" -- "$1" "$OUT/$1" 2>&1 | grep --line-buffered -E "Error|Traceback" | head -5
  echo "=== $1 done $(date +%T) $(ls "$OUT/$1" | wc -l) frames"
}
run cup_sinks 1
run fish_free 1
run ocean_vast 1
run ghost_circles 1
run sunrise 2
run ocean_storm 2
run tree_storm 2
run sunrise_wide 2
run shelf 2
run earth_turn 2
run galaxy 2
