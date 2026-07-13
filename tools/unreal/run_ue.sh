#!/usr/bin/env bash
# run_ue.sh — drive the UE 5.8 hero build headless. EDIT the three paths below for your machine.
# Asset ops (import/build/sequence) run reliably headless via -ExecutePythonScript. The Movie Render Queue
# render is most reliable from the OPEN editor (run render.py there); the headless MRQ cmdline is also given.
set -e
UE="${UE:-/opt/UnrealEngine/Engine/Binaries/Linux/UnrealEditor-Cmd}"   # or .../Win64/UnrealEditor-Cmd.exe
PROJ="${PROJ:-$HOME/Protocell/Protocell.uproject}"
HERE="$(cd "$(dirname "$0")" && pwd)"
COMMON="-unattended -nosplash -nop4 -stdout -FullStdOutLogOutput"

export UE_HEIGHT_PNG="${UE_HEIGHT_PNG:-/tmp/protocell_height.png}"      # from export_height.mjs (copy to the UE box)
export UE_OUT_DIR="${UE_OUT_DIR:-{project_dir}/Saved/MovieRenders/protocell}"

echo "[1/4] import sim heightmap"; "$UE" "$PROJ" -ExecutePythonScript="$HERE/import_heightfield.py" $COMMON
echo "[2/4] build scene + material";"$UE" "$PROJ" -ExecutePythonScript="$HERE/build_scene.py"        $COMMON
echo "[3/4] build sequence";       "$UE" "$PROJ" -ExecutePythonScript="$HERE/make_sequence.py"        $COMMON
echo "[4/4] render (MRQ)";         "$UE" "$PROJ" -ExecutePythonScript="$HERE/render.py"               $COMMON
# Headless MRQ alternative (if render.py's PIE executor exits early in your build):
#   "$UE" "$PROJ" /Game/Protocell/Map_Protocell -game \
#     -MoviePipelineLocalExecutorClass=/Script/MovieRenderPipelineCore.MoviePipelinePythonHostExecutor \
#     -ExecutorPythonClass=/Engine/PythonTypes.MoviePipelineExampleRuntimeExecutor \
#     -LevelSequence=/Game/Protocell/SEQ_Protocell -windowed -resx=1080 -resy=1920 $COMMON
echo "Done. Mux the PNG sequence -> MP4 (24fps, vertical):"
echo '  ffmpeg -framerate 24 -i protocell.%04d.png -c:v libx264 -pix_fmt yuv420p -crf 17 -movflags +faststart protocell_hero.mp4'
