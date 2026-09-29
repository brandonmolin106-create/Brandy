#!/bin/bash
# Concatenate rendered chunks, burn in captions + brand mark, mux the soundtrack, export deliverables.
#   ./assemble.sh WORK OUTDIR
set -e
WORK="$1"
OUT="$2"
HERE="$(cd "$(dirname "$0")" && pwd)"
PROD="$HERE/productions/fish-in-the-cup"
mkdir -p "$OUT"
ls "$WORK"/chunks/chunk_?????.mp4 | sort | sed "s/^/file '/; s/$/'/" > "$WORK/chunks/list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$WORK/chunks/list.txt" -c copy "$WORK/video_master.mp4"

# captions + brand overlay, encodes MASTER (CRF 15) and TikTok (CRF 18, 12 Mbps cap) in one pass
(cd "$HERE" && python3 overlay.py "$WORK" "$PROD/captions.txt" "$PROD/words.json" "$OUT")

# quick-view preview (small file for phones / chat)
ffmpeg -v error -y -i "$OUT/EchoesInTheDark_FishInTheCup_TikTok.mp4" -vf scale=720:1280:flags=lanczos \
  -c:v libx264 -preset medium -crf 23 -maxrate 3500k -bufsize 7M -pix_fmt yuv420p -c:a aac -b:a 160k \
  -movflags +faststart "$OUT/EchoesInTheDark_FishInTheCup_preview720.mp4"
ls -la "$OUT"
