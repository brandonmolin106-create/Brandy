#!/bin/bash
# Third wave: re-render shots whose first pass predates a fix (waits for the other queues).
#   ./render_queue3.sh OUTROOT shot...
OUT="$1"; shift
B=${BLENDER:-/opt/blender/blender-4.5.14-linux-x64/blender}
HERE="$(cd "$(dirname "$0")" && pwd)"
while pgrep -f "[r]ender_queue.sh|[r]ender_queue2.sh" > /dev/null; do sleep 30; done
for s in "$@"; do
  echo "=== $s $(date +%T)"
  mkdir -p "$OUT/${s}_v2"
  "$B" -b --factory-startup --python "$HERE/run_any.py" -- "$s" "$OUT/${s}_v2" 2>&1 | grep --line-buffered -E "Error|Traceback" | head -5
  n=$(ls "$OUT/${s}_v2" | wc -l)
  echo "=== $s done $(date +%T) $n frames"
done
