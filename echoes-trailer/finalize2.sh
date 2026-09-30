#!/usr/bin/env bash
# v2: loudness-normalise the score, mux with the 4K picture, and make share copies.
set -euo pipefail
cd "$(dirname "$0")"
FF=$(python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -y -loglevel error -i out2/soundtrack_raw.wav -af loudnorm=I=-14:TP=-1.0:LRA=20 -ar 48000 out2/soundtrack.wav
"$FF" -y -loglevel error -i out2/video_4k_silent.mp4 -i out2/soundtrack.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 320k -shortest -movflags +faststart out2/Echoes_in_the_Dark_v2_4K.mp4
"$FF" -y -loglevel error -i out2/Echoes_in_the_Dark_v2_4K.mp4 -vf scale=1920:1080:flags=lanczos \
  -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -c:a copy -movflags +faststart out2/Echoes_in_the_Dark_v2_1080p.mp4
# phone-friendly full-length HEVC copy under 30 MB
P=/tmp/hevc2pass
"$FF" -y -loglevel error -i out2/Echoes_in_the_Dark_v2_4K.mp4 -vf "scale=1920:1080:flags=lanczos,hqdn3d=2:2:4:4" \
  -c:v libx265 -preset slow -b:v 560k -x265-params "pass=1:stats=$P.log:aq-mode=3:log-level=error" -an -f mp4 /dev/null
"$FF" -y -loglevel error -i out2/Echoes_in_the_Dark_v2_4K.mp4 -vf "scale=1920:1080:flags=lanczos,hqdn3d=2:2:4:4" \
  -c:v libx265 -preset slow -b:v 560k -x265-params "pass=2:stats=$P.log:aq-mode=3:log-level=error" -tag:v hvc1 \
  -c:a aac -b:a 96k -movflags +faststart out2/Echoes_in_the_Dark_v2_share_1080p_hevc.mp4
ls -la out2/*.mp4
