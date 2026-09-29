#!/bin/bash
# Render the full piece in 30 s chunks with 2 parallel workers (2 numba threads each).
set -e
WORK="$1"
OUT="$WORK/chunks"
mkdir -p "$OUT"
TOTAL=10950
STEP=900
jobs=()
for ((f=0; f<TOTAL; f+=STEP)); do
  e=$((f+STEP)); [ $e -gt $TOTAL ] && e=$TOTAL
  jobs+=("$f $e")
done
printf '%s\n' "${jobs[@]}" | xargs -P 2 -L 1 bash -c '
  f=$0; e=$1; n=$(printf "%05d" $f)
  if [ -s "'"$OUT"'/chunk_$n.mp4" ]; then echo "skip $n"; exit 0; fi
  NUMBA_NUM_THREADS=2 OMP_NUM_THREADS=2 python3 render.py "'"$WORK"'" chunk $f $e "'"$OUT"'/chunk_$n.tmp.mp4" > "'"$OUT"'/log_$n.txt" 2>&1 \
    && mv "'"$OUT"'/chunk_$n.tmp.mp4" "'"$OUT"'/chunk_$n.mp4" && echo "done $n"
'
