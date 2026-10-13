#!/bin/bash
# split_parts.sh VIDEO AUDIO OUT_PREFIX "start end name" ["start end name" ...]
# 2-pass libx264 (-tune animation) + AAC 128k; each part's video bitrate is chosen so the file lands < ~29.5 MB
# (SendUserFile rejects files over 30 MiB). Pick the cuts with plan_parts.py (never mid-line, on hard cuts, the fewest
# parts that keep >= ~2 Mbps video), then QC the result with qc_parts.py.
#   bash split_parts.sh out/video.mp4 out/mix.wav out/boxed_ep04 "0 91.166667 part1" "91.166667 195.916667 part2"
# True-peak safety: ffmpeg's AAC encoder overshoots sharp transients by up to ~2.3 dB, so the audio is limited first
# (4x oversampled; ceiling TP_CEIL_DB, default -3.5 dBFS; TP_CEIL_DB=off skips it, e.g. for already-mastered music).
set -e
V=$1; A=$2; PRE=$3; shift 3
FF=$(python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
TP=${TP_CEIL_DB:--3.5}
if [ "$TP" != "off" ]; then
  LIM=$(awk -v d="$TP" 'BEGIN{printf "%.4f", 10^(d/20)}')
  ATP="${PRE}_audio_tp.wav"
  [ "$ATP" -nt "$A" ] || $FF -v error -y -i "$A" -vn \
      -af "aresample=192000,alimiter=limit=$LIM:attack=5:release=60:level=0,aresample=48000" -c:a pcm_s16le "$ATP"
  A="$ATP"
fi
for spec in "$@"; do
  read S E P <<< "$spec"
  DUR=$(awk -v a="$S" -v b="$E" 'BEGIN{print b-a}')
  VBR=$(awk -v d="$DUR" 'BEGIN{printf "%d", (29.2e6*8/d - 128000 - 30000)/1000}')
  EDGE="afade=t=in:st=0:d=0.02,afade=t=out:st=$(awk -v d="$DUR" 'BEGIN{print d-0.02}'):d=0.02"   # 20 ms edges: no click, no AAC onset spike
  echo "$P: $S -> $E (${DUR}s) video ${VBR}k"
  $FF -y -v error -ss $S -t $DUR -i "$V" -c:v libx264 -tune animation -b:v ${VBR}k -maxrate $((VBR*2))k -bufsize $((VBR*4))k \
      -pass 1 -passlogfile "${PRE}_$P" -preset slow -an -f null /dev/null
  $FF -y -v error -ss $S -t $DUR -i "$V" -ss $S -t $DUR -i "$A" -map 0:v -map 1:a -c:v libx264 -tune animation -b:v ${VBR}k \
      -maxrate $((VBR*2))k -bufsize $((VBR*4))k -pass 2 -passlogfile "${PRE}_$P" -preset slow -af "$EDGE" -c:a aac -b:a 128k -ac 2 \
      -pix_fmt yuv420p -movflags +faststart -shortest "${PRE}_$P.mp4"
  rm -f "${PRE}_$P"*.log "${PRE}_$P"*.mbtree
  ls -la "${PRE}_$P.mp4"
done
