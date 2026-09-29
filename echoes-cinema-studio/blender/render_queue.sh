#!/bin/bash
# Render a list of shots sequentially (resumable).  ./render_queue.sh OUTROOT shot1 shot2 ...
OUT="$1"; shift
B=${BLENDER:-/opt/blender/blender-4.5.14-linux-x64/blender}
HERE="$(cd "$(dirname "$0")" && pwd)"
for s in "$@"; do
  echo "=== $s $(date +%T)"
  "$B" -b --factory-startup --python "$HERE/run_shot.py" -- "$s" "$OUT/$s" 2>&1 | grep -E "^SHOT|Error|Traceback" | awk -v s="$s" 'NR%12==1 || /Error|Traceback/'
  echo "=== $s done $(date +%T) $(ls "$OUT/$s" | wc -l) frames"
done
