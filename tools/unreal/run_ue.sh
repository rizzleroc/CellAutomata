#!/usr/bin/env bash
# =============================================================================
# run_ue.sh — headless orchestration for the protocell UE 5.8 hero render.
#
# Runs the stage scripts in order through UnrealEditor-Cmd, then muxes the PNG
# frames to mp4 with ffmpeg. For a UE 5.8 + GPU workstation (not the sandbox).
#
# Required env:
#   UE_ENGINE   path to UnrealEditor-Cmd
#   UPROJECT    path to the .uproject hosting the render
# Optional env (forwarded via pcfg.py):
#   PIPELINE=mesh|heightfield   (default mesh — the true 3D cleavage)
#   UE_MESH_SEQ_DIR / UE_HEIGHT_PNG / UE_HEIGHT_SEQ_DIR / UE_OUTPUT_DIR
#   UE_RES_X(1080) UE_RES_Y(1920) UE_FPS(24) UE_DURATION(3.0)
#   UE_RENDER_MODE(mrq|flipbook)
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${UE_ENGINE:?set UE_ENGINE to UnrealEditor-Cmd}"
: "${UPROJECT:?set UPROJECT to your .uproject}"

OUT_DIR="${UE_OUTPUT_DIR:-$HERE/render_out}"
FPS="${UE_FPS:-24}"
PIPELINE="${PIPELINE:-mesh}"

run_py () {
  local script="$1"
  echo ">>> [run_ue] $script"
  "$UE_ENGINE" "$UPROJECT" \
    -ExecutePythonScript="$HERE/$script" \
    -unattended -nop4 -nosplash -NullRHI 2>&1 | sed 's/^/    /' || {
      echo "!!! $script failed (see log above)"; exit 1; }
}

run_render () {
  echo ">>> [run_ue] render.py (GPU)"
  "$UE_ENGINE" "$UPROJECT" \
    -ExecutePythonScript="$HERE/render.py" \
    -unattended -nop4 -nosplash 2>&1 | sed 's/^/    /' || {
      echo "!!! render.py failed"; exit 1; }
}

echo "=== protocell UE 5.8 hero render (pipeline=$PIPELINE) ==="
if [ "$PIPELINE" = "heightfield" ]; then
  run_py import_heightfield.py
else
  run_py import_mesh_sequence.py
fi
run_py  build_scene.py
run_py  make_sequence.py
run_render

echo ">>> [run_ue] muxing frames -> protocell_hero.mp4"
ffmpeg -y -framerate "$FPS" \
  -i "$OUT_DIR/protocell.%04d.png" \
  -c:v libx264 -pix_fmt yuv420p -crf 16 \
  -vf "scale=1080:1920:flags=lanczos" \
  "$OUT_DIR/protocell_hero.mp4"

echo "=== DONE -> $OUT_DIR/protocell_hero.mp4 ==="
echo "Next: run the viral_cut pass for the THIS ISN'T A CELL hook + HUD + loop + audio."
