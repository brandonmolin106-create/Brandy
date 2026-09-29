#!/bin/bash
# Concatenate rendered chunks, mux the mastered soundtrack, and export deliverables.
#   ./assemble.sh WORK OUTDIR
set -e
WORK="$1"
OUT="$2"
mkdir -p "$OUT"
ls "$WORK"/chunks/chunk_*.mp4 | grep -v tmp | sort | sed "s/^/file '/; s/$/'/" > "$WORK/chunks/list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$WORK/chunks/list.txt" -c copy "$WORK/video_master.mp4"

# master: untouched render + 320k AAC
ffmpeg -v error -y -i "$WORK/video_master.mp4" -i "$WORK/audio/mix.wav" -map 0:v -map 1:a -c:v copy \
  -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart "$OUT/EchoesInTheDark_FishInTheCup_MASTER.mp4"

# TikTok upload: 1080x1920, H.264 High 4.2, ~16 Mbps VBV-capped, 30 fps
ffmpeg -v error -y -i "$WORK/video_master.mp4" -i "$WORK/audio/mix.wav" -map 0:v -map 1:a \
  -c:v libx264 -preset slow -profile:v high -level 4.2 -pix_fmt yuv420p -crf 17 -maxrate 16M -bufsize 32M \
  -tune grain -r 30 -g 60 -c:a aac -b:a 256k -ar 48000 -shortest -movflags +faststart \
  "$OUT/EchoesInTheDark_FishInTheCup_TikTok.mp4"

# quick-view preview (small file for phones / chat)
ffmpeg -v error -y -i "$OUT/EchoesInTheDark_FishInTheCup_TikTok.mp4" -vf scale=720:1280:flags=lanczos \
  -c:v libx264 -preset medium -crf 24 -maxrate 4M -bufsize 8M -pix_fmt yuv420p -c:a aac -b:a 160k \
  -movflags +faststart "$OUT/EchoesInTheDark_FishInTheCup_preview720.mp4"
ls -la "$OUT"
