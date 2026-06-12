#!/usr/bin/env bash
# Unattended batch: for each reel, generate the field then composite the video, sequentially.
# Survives session drop via nohup. Run from the repo root:
#   nohup bash tools/morphogenesis/run_batch.sh > /tmp/batch_main.log 2>&1 &
# Each pair writes /tmp/<x>_field.bin + /tmp/<x>_meta.json, then /tmp/web8_<x>.mp4.
set -u
cd "$(dirname "$0")/../.." || exit 1
HERE="tools/morphogenesis"

run_one () {            # $1 = stem (void|forge|cryst|lo|...)
  local s="$1"
  echo "=== $s generator ==="   >  "/tmp/${s}_gen.log"
  node "$HERE/${s}_gen.mjs"      >> "/tmp/${s}_gen.log" 2>&1
  echo "$s GEN DONE"            >> "/tmp/${s}_gen.log"
  python3 "$HERE/${s}_film.py"  >> "/tmp/${s}_gen.log" 2>&1
  echo "$s FILM DONE"          >> "/tmp/${s}_gen.log"
  # Field bins are ~5.8 GB each; the mp4 is the deliverable. Free the bin so a
  # multi-reel batch can't fill /tmp (HANDOFF Lesson 7).
  rm -f "/tmp/${s}_field.bin" "/tmp/${s}_silent.mp4"
}

for stem in "$@"; do
  run_one "$stem"
done
echo "ALL DONE: $*" > /tmp/batch_done.log
