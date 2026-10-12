#!/bin/bash
# split_parts.sh VIDEO AUDIO OUT_PREFIX "start end name" ["start end name" ...]
# 2-pass libx264 (-tune animation) + AAC 128k; each part's video bitrate is chosen so the file lands < ~29.5 MB
# (SendUserFile rejects files over 30 MiB). Split at shot cuts; ~110 s per part keeps ~2 Mbps at 1080p24.
#   bash split_parts.sh out/video.mp4 out/mix.wav out/boxed_ep04 "0 113.66 part1" "113.66 219.35 part2"
set -e
V=$1; A=$2; PRE=$3; shift 3
FF=$(python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
for spec in "$@"; do
  read S E P <<< "$spec"
  DUR=$(awk -v a="$S" -v b="$E" 'BEGIN{print b-a}')
  VBR=$(awk -v d="$DUR" 'BEGIN{printf "%d", (29.2e6*8/d - 128000 - 30000)/1000}')
  echo "$P: $S -> $E (${DUR}s) video ${VBR}k"
  $FF -y -v error -ss $S -t $DUR -i "$V" -c:v libx264 -tune animation -b:v ${VBR}k -maxrate $((VBR*2))k -bufsize $((VBR*4))k \
      -pass 1 -passlogfile "${PRE}_$P" -preset slow -an -f null /dev/null
  $FF -y -v error -ss $S -t $DUR -i "$V" -ss $S -t $DUR -i "$A" -map 0:v -map 1:a -c:v libx264 -tune animation -b:v ${VBR}k \
      -maxrate $((VBR*2))k -bufsize $((VBR*4))k -pass 2 -passlogfile "${PRE}_$P" -preset slow -c:a aac -b:a 128k -ac 2 \
      -pix_fmt yuv420p -movflags +faststart -shortest "${PRE}_$P.mp4"
  rm -f "${PRE}_$P"*.log "${PRE}_$P"*.mbtree
  ls -la "${PRE}_$P.mp4"
done
