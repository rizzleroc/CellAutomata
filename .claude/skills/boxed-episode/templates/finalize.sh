#!/bin/bash
# finalize.sh EPN "a b part1" "b c part2" ... : encode <EPN>/out/video.mp4 + mix.wav into parts, each < 29.5 MB
# (2-pass, split at shot cuts; choose ~6 parts of ~110 s for an 11-minute episode)
set -e
EPN=${1:?usage: finalize.sh EPN "start end name" ...}; shift
cd "$(dirname "$0")/$EPN/out"
FF=$(python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
# Ep4 example: bash finalize.sh ep4 "0 113.66 part1" "113.66 219.35 part2" "219.35 347.57 part3" "347.57 451.05 part4" "451.05 553.11 part5" "553.11 660 part6"
for spec in "$@"; do
  read A Bt P <<< "$spec"
  DUR=$(awk -v a="$A" -v b="$Bt" 'BEGIN{print b-a}')
  VBR=$(awk -v d="$DUR" 'BEGIN{printf "%d", (29.2e6*8/d - 128000 - 30000)/1000}')
  echo "$P: $A -> $Bt (${DUR}s) vbr=${VBR}k"
  $FF -y -v error -ss $A -t $DUR -i video.mp4 -c:v libx264 -tune animation -b:v ${VBR}k -maxrate $((VBR*2))k -bufsize $((VBR*4))k -pass 1 -passlogfile p_$P -preset slow -an -f null /dev/null
  $FF -y -v error -ss $A -t $DUR -i video.mp4 -ss $A -t $DUR -i mix.wav -map 0:v -map 1:a -c:v libx264 -tune animation -b:v ${VBR}k -maxrate $((VBR*2))k -bufsize $((VBR*4))k -pass 2 -passlogfile p_$P -preset slow \
      -c:a aac -b:a 128k -ac 2 -pix_fmt yuv420p -movflags +faststart -shortest boxed_${EPN}_$P.mp4
  rm -f p_$P*
done
ls -la boxed_${EPN}_part*.mp4
