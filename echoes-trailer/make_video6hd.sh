#!/usr/bin/env bash
# Render the v6 1080p (8:00) trailer in parallel segments, then join them losslessly.
set -euo pipefail
cd "$(dirname "$0")"
export TRAILER_TIMELINE=timeline6
export GLIBC_TUNABLES=glibc.malloc.mmap_threshold=4294967296:glibc.malloc.trim_threshold=17179869184
TOTAL=$(python3 -c "import timeline6 as T; print(int(T.DURATION*T.FPS))")
SEGS=${SEGS:-48}
JOBS=${JOBS:-4}
mkdir -p out6hd/seg out6hd/logs
STEP=$(( (TOTAL + SEGS - 1) / SEGS ))
for i in $(seq 0 $((SEGS-1))); do
  s=$((i*STEP)); e=$(( (i+1)*STEP )); [ $e -gt $TOTAL ] && e=$TOTAL
  printf "%02d %d %d\n" "$i" "$s" "$e"
done | xargs -P "$JOBS" -L 1 bash -c '
  f=out6hd/seg/seg$0.mp4
  if [ -s "$f.done" ]; then echo "skip $0"; exit 0; fi
  nice -n 5 python3 render2.py --scale 0.5 --crf 16 --start $1 --end $2 --out $f > out6hd/logs/seg$0.log 2>&1 && echo ok > $f.done'
ls out6hd/seg/seg*.mp4 | sort | sed "s|^out6hd/seg/|file '|; s|$|'|" > out6hd/seg/list.txt
FF=$(python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -y -loglevel error -f concat -safe 0 -i out6hd/seg/list.txt -c copy out6hd/video_4k_silent.mp4
echo "video done: out6hd/video_4k_silent.mp4"
