#!/bin/bash
# two-pass linear loudness normalisation: loud.sh in.wav out.wav [I=-14]
FF=$(python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
IN=$1; OUT=$2; TGT=${3:--14}
J=$($FF -hide_banner -nostats -i "$IN" -af loudnorm=I=$TGT:TP=-1.0:LRA=20:print_format=json -f null - 2>&1 | sed -n '/{/,/}/p')
mi=$(echo "$J" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['input_i'], d['input_tp'], d['input_lra'], d['input_thresh'], d['target_offset'])")
read II ITP ILRA ITH OFF <<< "$mi"
$FF -y -v error -i "$IN" -af loudnorm=I=$TGT:TP=-1.0:LRA=20:measured_I=$II:measured_TP=$ITP:measured_LRA=$ILRA:measured_thresh=$ITH:offset=$OFF:linear=true -ar 48000 "$OUT"
echo "loudness: in $II LUFS -> target $TGT"
