#!/usr/bin/env bash
# Loudness-normalise the soundtrack to streaming level and mux it with the 4K picture.
set -euo pipefail
cd "$(dirname "$0")"
FF=$(python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -y -loglevel error -i out/soundtrack_raw.wav -af loudnorm=I=-14:TP=-1.0:LRA=18 -ar 48000 out/soundtrack.wav
"$FF" -y -loglevel error -i out/video_4k_silent.mp4 -i out/soundtrack.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 320k -shortest -movflags +faststart out/Echoes_in_the_Dark_Trailer_4K.mp4
# 1080p share copy (small enough to send anywhere)
"$FF" -y -loglevel error -i out/Echoes_in_the_Dark_Trailer_4K.mp4 -vf scale=1920:1080:flags=lanczos \
  -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -c:a copy -movflags +faststart out/Echoes_in_the_Dark_Trailer_1080p.mp4
ls -la out/*.mp4
