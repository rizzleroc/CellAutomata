#!/usr/bin/env bash
# Regenerate the real simulation footage used by build_progress_video.py.
# Produces GIFs in exports/ (gitignored). Requires the package installed
# (`pip install -e .`). Each clip is genuine headless simulator output.
set -euo pipefail
mkdir -p exports
gen () { # rule  "extra-args"  steps  name
  cellauto export --rule "$1" $2 --grid 120 --steps "$3" --fps 16 --canvas 600 \
    --out "exports/$4.gif"
}
gen abiogenesis-stage1-grayscott "--rule-config preset=mitosis" 110 grayscott_mitosis
gen abiogenesis-coacervate          ""                          110 coacervate
gen abiogenesis-homochirality       ""                          110 homochirality
gen abiogenesis-rna-world           ""                          110 rna_world
gen abiogenesis-hydrothermal-vent   ""                          110 vent
echo "Footage written to exports/. Now run: python3 marketing/social/build_progress_video.py"
