#!/usr/bin/env bash
# Regenerate the real simulation footage used by build_progress_video.py and
# build_reels.py. Produces GIFs in exports/ (gitignored). Requires the package
# installed (`pip install -e .`). Every clip is genuine headless simulator output.
set -euo pipefail
mkdir -p exports
gen () { # name  rule  "extra-args"  steps
  cellauto export --rule "$2" $3 --grid 120 --steps "${4:-100}" --fps 16 \
    --canvas 600 --out "exports/$1.gif"
  echo "  wrote exports/$1.gif"
}
# Gray-Scott regimes
gen grayscott_mitosis   abiogenesis-stage1-grayscott "--rule-config preset=mitosis"   110
gen grayscott_spots     abiogenesis-stage1-grayscott "--rule-config preset=spots"      100
gen grayscott_waves     abiogenesis-stage1-grayscott "--rule-config preset=waves"      100
gen grayscott_labyrinth abiogenesis-stage1-grayscott "--rule-config preset=labyrinth"  100
# Pipeline stages
gen soup          abiogenesis-stage0-soup       "" 100
gen vent          abiogenesis-hydrothermal-vent "" 110
gen raf           abiogenesis-stage2-raf        "" 100
gen homochirality abiogenesis-homochirality     "" 110
gen rna_world     abiogenesis-rna-world         "" 110
gen genetic       abiogenesis-genetic-code      "" 100
gen coacervate    abiogenesis-coacervate        "" 110
gen minerals      abiogenesis-mineral-catalysis "" 100
gen vesicles      abiogenesis-stage3-vesicles   "" 100
gen selection     abiogenesis-stage4-selection  "" 100
gen luca          abiogenesis-luca              "" 100
# Reference automata
gen conway     conway   ""                              100
gen wolfram110 wolfram1d "--rule-config rule_number=110" 118
echo "Footage ready. Build the long reel with build_progress_video.py or the"
echo "30-pack with: python3 marketing/social/build_reels.py"
