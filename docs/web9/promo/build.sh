#!/usr/bin/env bash
# Assemble the web9 promo: protocell clip (intro) + web9 UI capture + ElevenLabs voiceover.
# Needs: ffmpeg, and the three inputs below. Run where ffmpeg + network exist.
set -euo pipefail

CLIP="${CLIP:-protocell.mp4}"        # the rendered protocell clip
WEB9="${WEB9:-capture/web9.webm}"    # Playwright capture (see capture.mjs)
VO="${VO:-narration.mp3}"            # ElevenLabs voiceover of narration.txt
OUT="${OUT:-promo.mp4}"
INTRO="${INTRO:-6}"                   # seconds of the clip to open on
CLIP_URL="https://s.asim.sh/videos/3d89a86a-1b9b-463b-b48f-89361bc766c3.mp4"

command -v ffmpeg >/dev/null || { echo "need ffmpeg on PATH"; exit 1; }
[ -f "$CLIP" ] || { echo "fetching protocell clip..."; curl -fsSL "$CLIP_URL" -o "$CLIP"; }
[ -f "$WEB9" ] || { echo "missing $WEB9 -- run: node capture.mjs (see README)"; exit 1; }
[ -f "$VO" ]   || { echo "missing $VO -- ElevenLabs voiceover of narration.txt (see README)"; exit 1; }

# normalize both video inputs to 1080x1920/30fps, concat them, lay the VO underneath.
# tweak the filtergraph to intercut more segments (e.g. the #origin clip again at the end).
FILT="[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p[intro];[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p[walk];[intro][walk]concat=n=2:v=1:a=0[v]"

ffmpeg -y -t "$INTRO" -i "$CLIP" -i "$WEB9" -i "$VO" -filter_complex "$FILT" -map "[v]" -map 2:a -af apad -shortest -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "$OUT"

echo "wrote $OUT"
