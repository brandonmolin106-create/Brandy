#!/bin/bash
# Final build: wait for the close-up re-renders, swap them in, composite what's left on all cores, encode deliverables.
#   ./finish.sh WORK/cine OUTDIR
set -e
CINE="$1"; OUT="$2"
R="$CINE/renders"
HERE="$(cd "$(dirname "$0")" && pwd)"
while pgrep -f "[r]ender_queue3.sh" > /dev/null; do sleep 20; done
declare -A N=([fish_macro_turn]=96 [hit_glass]=84 [flare]=72 [eye_macro]=96)
for s in "${!N[@]}"; do
  if [ -d "$R/${s}_v2" ] && [ "$(ls "$R/${s}_v2" | grep -c png)" -ge "${N[$s]}" ]; then
    rm -rf "${R:?}/${s}_old"; mv "$R/$s" "$R/${s}_old"; mv "$R/${s}_v2" "$R/$s"; touch "$R/$s/.ready"
    echo "swapped in clean $s"
  else
    echo "WARNING: $s re-render incomplete - keeping first pass"; touch "$R/$s/.ready"
  fi
done
cd "$HERE"
for j in 0 1 2 3; do python3 cinema.py segs "$CINE" "$CINE/segs" $j 4 > "$CINE/final_part$j.log" 2>&1 & done
wait
grep -h "missing" "$CINE"/final_part*.log
python3 cinema.py concat "$CINE" "$CINE/segs" "$CINE/picture.mp4"
mkdir -p "$OUT"
M="$OUT/EchoesInTheDark_FishInTheCup_Thriller_1080p.mp4"
ffmpeg -v error -y -i "$CINE/picture.mp4" -i "$CINE/audio/thriller_mix.wav" -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 17 -maxrate 12M -bufsize 24M -profile:v high -level 4.2 -pix_fmt yuv420p -g 48 \
  -c:a aac -b:a 320k -ar 48000 -movflags +faststart -shortest "$M"
for part in 1 2; do
  ss=$(( (part - 1) * 183 ))
  ffmpeg -v error -y -ss $ss -t 183 -i "$M" -vf scale=720:1280:flags=lanczos -c:v libx264 -preset medium -crf 23 \
    -maxrate 1150k -bufsize 2300k -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart \
    "$OUT/EchoesInTheDark_Thriller_preview_part$part.mp4"
done
ls -la "$OUT"
echo FINISHED
