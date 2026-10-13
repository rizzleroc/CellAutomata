#!/bin/bash
# BOXED engine setup — recreate the working engine after a fresh container / reset.
#   bash .claude/skills/boxed-episode/engine/setup.sh [B]
# B = the working root (default: $B, else <session scratchpad>/boxed if a scratchpad exists, else ./boxed).
# Never clobbers newer work: engine files are copied with -n (delete $B/eng/<file> first to refresh from the skill).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
if [ -n "$1" ]; then B="$1"; elif [ -z "$B" ]; then
  SP=$(ls -d /tmp/claude-*/*/*/scratchpad 2>/dev/null | head -1); B="${SP:+$SP/boxed}"; B="${B:-$PWD/boxed}"; fi
mkdir -p "$B/eng" "$B/fonts" "$B/lib" "$B/test"
cp --update=none "$HERE"/eng/*.py "$B/eng/" 2>/dev/null || cp -n "$HERE"/eng/*.py "$B/eng/"
# 10 Google Fonts used by the hand-painted lettering (OFL / Apache-2.0)
cd "$B/fonts"
for p in ofl/shrikhand/Shrikhand-Regular.ttf ofl/londrinasolid/LondrinaSolid-Black.ttf ofl/londrinasolid/LondrinaSolid-Regular.ttf \
         apache/permanentmarker/PermanentMarker-Regular.ttf ofl/bagelfatone/BagelFatOne-Regular.ttf apache/chewy/Chewy-Regular.ttf \
         ofl/bangers/Bangers-Regular.ttf ofl/titanone/TitanOne-Regular.ttf ofl/rubikwetpaint/RubikWetPaint-Regular.ttf ofl/caveatbrush/CaveatBrush-Regular.ttf; do
  [ -s "$(basename $p)" ] || curl -sSL --max-time 60 -o "$(basename $p)" "https://raw.githubusercontent.com/google/fonts/main/$p" || echo "FONT FAIL $p"
done
# skia-python needs EGL/GLES: borrow them from the pre-installed Playwright chromium
CH=$(ls -d /opt/pw-browsers/chromium-*/chrome-linux 2>/dev/null | head -1)
[ -n "$CH" ] && ln -sf "$CH/libEGL.so" "$B/lib/libEGL.so.1" && ln -sf "$CH/libGLESv2.so" "$B/lib/libGLESv2.so.2"
# python deps — ALWAYS `python3 -m pip` (bare `pip` belongs to a different interpreter in these containers)
LD_LIBRARY_PATH="$B/lib" python3 -c "import skia, soundfile, imageio_ffmpeg, PIL, numpy" 2>/dev/null || \
  python3 -m pip install -q "skia-python==144.0.post2" numpy soundfile pillow imageio-ffmpeg 2>&1 | tail -2
cd "$B"
LD_LIBRARY_PATH="$B/lib" python3 -c "from eng import core, letters, world, zee, cast, sets, acting, lipsync, shots_ep2, gary; print('BOXED engine OK')" 2>&1 | grep -v Fontconfig
echo "B=$B"
echo "ffmpeg: $(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"
echo "Next: mkdir -p \$B/ep<N>/{tools,audio,vo,out} and copy .claude/skills/boxed-episode/templates/* into place (see references/pipeline.md)."
