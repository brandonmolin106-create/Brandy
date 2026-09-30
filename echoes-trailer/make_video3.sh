#!/usr/bin/env bash
# Render the v3 (8:00) trailer in parallel segments, then join them losslessly.
set -euo pipefail
cd "$(dirname "$0")"
export TRAILER_TIMELINE=timeline3
export GLIBC_TUNABLES=glibc.malloc.mmap_threshold=4294967296:glibc.malloc.trim_threshold=17179869184
TOTAL=$(python3 -c "import timeline3 as T; print(int(T.DURATION*T.FPS))")
SEGS=${SEGS:-16}
JOBS=${JOBS:-4}
mkdir -p out3/seg out3/logs
STEP=$(( (TOTAL + SEGS - 1) / SEGS ))
for i in $(seq 0 $((SEGS-1))); do
  s=$((i*STEP)); e=$(( (i+1)*STEP )); [ $e -gt $TOTAL ] && e=$TOTAL
  printf "%02d %d %d\n" "$i" "$s" "$e"
done | xargs -P "$JOBS" -L 1 bash -c '
  f=out3/seg/seg$0.mp4
  if [ -s "$f.done" ]; then echo "skip $0"; exit 0; fi
  nice -n 5 python3 render2.py --start $1 --end $2 --out $f > out3/logs/seg$0.log 2>&1 && echo ok > $f.done'
ls out3/seg/seg*.mp4 | sort | sed "s|^out3/seg/|file '|; s|$|'|" > out3/seg/list.txt
FF=$(python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -y -loglevel error -f concat -safe 0 -i out3/seg/list.txt -c copy out3/video_4k_silent.mp4
echo "video done: out3/video_4k_silent.mp4"
