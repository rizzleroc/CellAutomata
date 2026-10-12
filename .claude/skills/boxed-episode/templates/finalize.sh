#!/bin/bash
# finalize.sh EPN "a b part1" "b c part2" ... : encode <EPN>/out/video.mp4 + mix.wav into parts, each < 29.5 MB
# (2-pass). Get the cut list from the planner: it cuts only where no line of dialogue is running (shot starts, or
# hard cuts inside music-only montages), on drawing boundaries, with the fewest parts that keep >= ~2 Mbps video:
#   python3 .claude/skills/video-production/scripts/plan_parts.py $B/$EPN/timeline.json --video $B/$EPN/out/video.mp4
# Ep4 (the planner's plan, 7 parts for 11:00):
#   bash finalize.sh ep4 "0 91.166667 part1" "91.166667 195.916667 part2" "195.916667 287.083333 part3" \
#     "287.083333 385.083333 part4" "385.083333 495.333333 part5" "495.333333 586.75 part6" "586.75 660 part7"
# Then QC the encoded parts: python3 .claude/skills/video-production/scripts/qc_parts.py $B/$EPN/out boxed_$EPN
set -e
EPN=${1:?usage: finalize.sh EPN "start end name" ...}; shift
cd "$(dirname "$0")/$EPN/out"
FF=$(python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
# True-peak limit the mix first (4x oversampled, -3.5 dBFS ceiling): ffmpeg's AAC encoder overshoots sharp transients
# by up to ~2.3 dB, which put Ep4's loudest part at +0.8 dBTP; limited, every part landed at -2.3..-3.0 dBTP with the
# loudness unchanged. Rebuilt automatically whenever mix.wav is newer.
[ mix_tp.wav -nt mix.wav ] || $FF -v error -y -i mix.wav \
    -af "aresample=192000,alimiter=limit=0.668:attack=5:release=60:level=0,aresample=48000" -c:a pcm_s16le mix_tp.wav
for spec in "$@"; do
  read A Bt P <<< "$spec"
  DUR=$(awk -v a="$A" -v b="$Bt" 'BEGIN{print b-a}')
  VBR=$(awk -v d="$DUR" 'BEGIN{printf "%d", (29.2e6*8/d - 128000 - 30000)/1000}')
  EDGE="afade=t=in:st=0:d=0.02,afade=t=out:st=$(awk -v d="$DUR" 'BEGIN{print d-0.02}'):d=0.02"   # 20 ms edges: no click, no AAC onset spike
  echo "$P: $A -> $Bt (${DUR}s) vbr=${VBR}k"
  $FF -y -v error -ss $A -t $DUR -i video.mp4 -c:v libx264 -tune animation -b:v ${VBR}k -maxrate $((VBR*2))k -bufsize $((VBR*4))k -pass 1 -passlogfile p_$P -preset slow -an -f null /dev/null
  $FF -y -v error -ss $A -t $DUR -i video.mp4 -ss $A -t $DUR -i mix_tp.wav -map 0:v -map 1:a -c:v libx264 -tune animation -b:v ${VBR}k -maxrate $((VBR*2))k -bufsize $((VBR*4))k -pass 2 -passlogfile p_$P -preset slow \
      -af "$EDGE" -c:a aac -b:a 128k -ac 2 -pix_fmt yuv420p -movflags +faststart -shortest boxed_${EPN}_$P.mp4
  rm -f p_$P*
done
ls -la boxed_${EPN}_part*.mp4
