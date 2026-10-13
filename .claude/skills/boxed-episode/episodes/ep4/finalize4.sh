#!/bin/bash
# finalize4.sh : encode ep4/out/video.mp4 + ep4/out/mix.wav into 7 parts, each < 29.5 MB (2-pass, split at shot cuts)
set -e
cd "$(dirname "$0")/ep4/out"
FF=/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2
# true-peak limit the mix first (4x oversampled, -3.5 dBFS ceiling): ffmpeg's AAC encoder overshoots sharp transients
# by up to ~2.3 dB, which put part 6 at +0.8 dBTP; limited, every part lands at -2.3..-3.0 dBTP with loudness unchanged
[ -f mix_tp.wav ] || $FF -v error -y -i mix.wav -af "aresample=192000,alimiter=limit=0.668:attack=5:release=60:level=0,aresample=48000" -c:a pcm_s16le mix_tp.wav
# every cut is a hard cut with no dialogue running across it (a line split between two files sounds broken):
#   91.17 / 195.92 / 385.08 / 586.75 = shot starts inside dialogue gaps; 287.08 = cut to the cave mouth inside the
#   ASCENT montage (T029); 495.33 = cut to the night city inside the MODERN montage (T044). Video >= ~1.96 Mbps everywhere.
# cold open+intro | the cave + game-show idea | game show + escape + ascent | the light + sunrise + ad | bumper + return + Socrates | modern caves + crisis + education | the turn + finale + endcard
set -- "0 91.166667 part1" "91.166667 195.916667 part2" "195.916667 287.083333 part3" "287.083333 385.083333 part4" \
       "385.083333 495.333333 part5" "495.333333 586.75 part6" "586.75 660 part7"
for spec in "$@"; do
  read A Bt P <<< "$spec"
  DUR=$(awk -v a="$A" -v b="$Bt" 'BEGIN{print b-a}')
  VBR=$(awk -v d="$DUR" 'BEGIN{printf "%d", (29.2e6*8/d - 128000 - 30000)/1000}')
  echo "$P: $A -> $Bt (${DUR}s) vbr=${VBR}k"
  $FF -y -v error -ss $A -t $DUR -i video.mp4 -c:v libx264 -tune animation -b:v ${VBR}k -maxrate $((VBR*2))k -bufsize $((VBR*4))k -pass 1 -passlogfile p_$P -preset slow -an -f null /dev/null
  $FF -y -v error -ss $A -t $DUR -i video.mp4 -ss $A -t $DUR -i mix_tp.wav -map 0:v -map 1:a -c:v libx264 -tune animation -b:v ${VBR}k -maxrate $((VBR*2))k -bufsize $((VBR*4))k -pass 2 -passlogfile p_$P -preset slow \
      -c:a aac -b:a 128k -ac 2 -pix_fmt yuv420p -movflags +faststart -shortest boxed_ep04_$P.mp4
  rm -f p_$P*
done
ls -la boxed_ep04_part*.mp4
