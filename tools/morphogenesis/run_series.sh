#!/usr/bin/env bash
# ABIOGENESIS — THE SERIES: render all four ~2-minute episodes and trim each to a <25 MB web cut.
# Sources must exist first (bash tools/morphogenesis/abio_gen.sh). Run from the repo root.
#   bash tools/morphogenesis/run_series.sh            # all four
#   EPS="1 3" bash tools/morphogenesis/run_series.sh  # a subset
# Output: /tmp/web8_abio_ep<N>.mp4 (master, crf18) + /tmp/web8_abio_ep<N>_web.mp4 (<25 MB, delivered).
set -e
cd "$(dirname "$0")/../.."
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
EPS="${EPS:-1 2 3 4}"
for ep in $EPS; do
  echo "=== [ep $ep] compositing ==="
  python3 tools/morphogenesis/abio_series.py "$ep"
  src=/tmp/web8_abio_ep${ep}.mp4
  out=/tmp/web8_abio_ep${ep}_web.mp4
  echo "=== [ep $ep] trimming to web cut (2-pass denoise) ==="
  # light temporal denoise crushes the per-frame grain the encoder chokes on; 1550k keeps each <25 MB
  $FF -y -hide_banner -loglevel error -i "$src" -vf hqdn3d=2:1:3:3 -c:v libx264 -b:v 1550k -pass 1 -passlogfile /tmp/ff2p_ep${ep} -an -preset slow -f mp4 /dev/null
  $FF -y -hide_banner -loglevel error -i "$src" -vf hqdn3d=2:1:3:3 -c:v libx264 -b:v 1550k -pass 2 -passlogfile /tmp/ff2p_ep${ep} -preset slow -c:a aac -b:a 96k -movflags +faststart "$out"
  echo "=== [ep $ep] done: $(du -h "$out" | cut -f1) ==="
done
echo "=== ALL EPISODES DONE ==="
ls -la /tmp/web8_abio_ep*_web.mp4