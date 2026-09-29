#!/bin/bash
# Composite the whole cut in parallel chunks, mux the thriller soundtrack, export the deliverables.
#   ./assemble.sh WORK/cine OUTDIR [JOBS]
set -e
CINE="$1"; OUT="$2"; JOBS="${3:-4}"
HERE="$(cd "$(dirname "$0")" && pwd)"
FPS=24; TOTAL=$((365 * FPS))
mkdir -p "$OUT" "$CINE/comp_chunks"
per=$(( (TOTAL + JOBS - 1) / JOBS ))
pids=()
for ((j = 0; j < JOBS; j++)); do
  a=$((j * per)); b=$(( (j + 1) * per )); (( b > TOTAL )) && b=$TOTAL
  f=$(printf "%s/comp_chunks/c_%02d.mp4" "$CINE" "$j")
  (cd "$HERE" && python3 cinema.py render "$CINE" $a $b "$f") &
  pids+=($!)
done
for p in "${pids[@]}"; do wait "$p"; done
ls "$CINE"/comp_chunks/c_*.mp4 | sort | sed "s/^/file '/; s/$/'/" > "$CINE/comp_chunks/list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$CINE/comp_chunks/list.txt" -c copy "$CINE/picture.mp4"
# upload master: H.264 High, CRF 17 capped at 12 Mbps, AAC 320k
ffmpeg -v error -y -i "$CINE/picture.mp4" -i "$CINE/audio/thriller_mix.wav" -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 17 -maxrate 12M -bufsize 24M -profile:v high -level 4.2 -pix_fmt yuv420p -g 48 \
  -c:a aac -b:a 320k -ar 48000 -movflags +faststart -shortest "$OUT/EchoesInTheDark_FishInTheCup_Thriller_1080p.mp4"
# phone-size preview in two halves (<30 MiB each)
for part in 1 2; do
  ss=$(( (part - 1) * 183 )); dur=183
  ffmpeg -v error -y -ss $ss -t $dur -i "$OUT/EchoesInTheDark_FishInTheCup_Thriller_1080p.mp4" \
    -vf scale=720:1280:flags=lanczos -c:v libx264 -preset medium -crf 25 -maxrate 1100k -bufsize 2200k \
    -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart "$OUT/EchoesInTheDark_Thriller_preview_part$part.mp4"
done
ls -la "$OUT"
