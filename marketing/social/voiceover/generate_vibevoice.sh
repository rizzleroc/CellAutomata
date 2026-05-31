#!/usr/bin/env bash
# Synthesise one narration WAV per reel with microsoft/VibeVoice.
#
# RUN THIS WHERE HUGGINGFACE IS REACHABLE (a GPU box or Colab is ideal; CPU
# works but is slow). This container blocks huggingface.co, so the model
# weights cannot be fetched here — that is why generation is a separate step.
#
# Setup (once):
#   git clone https://github.com/microsoft/VibeVoice /tmp/VibeVoice
#   pip install -e /tmp/VibeVoice            # pulls torch + transformers
#
# Then, from the CellAutomata repo root:
#   bash marketing/social/voiceover/generate_vibevoice.sh
#   python3 marketing/social/voiceover/add_voiceover.py   # mux into voiced reels
set -euo pipefail

REPO="${VIBEVOICE_REPO:-/tmp/VibeVoice}"
MODEL="${VIBEVOICE_MODEL:-microsoft/VibeVoice-Realtime-0.5B}"   # or microsoft/VibeVoice-1.5B
SPEAKER="${VIBEVOICE_SPEAKER:-Wayne}"                            # see demo/voices/streaming_model
DEVICE="${VIBEVOICE_DEVICE:-cuda}"                               # cuda | mps | cpu
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/wav"
TXT="$(mktemp -d)"
mkdir -p "$OUT"

# 1) explode scripts.json into one txt per reel
python3 - "$HERE/scripts.json" "$TXT" <<'PY'
import json, os, sys
data = json.load(open(sys.argv[1])); out = sys.argv[2]
for r in data["reels"]:
    with open(os.path.join(out, f"reel_{r['index']:02d}.txt"), "w") as f:
        f.write("Speaker 1: " + r["script"] + "\n")
print(f"wrote {len(data['reels'])} scripts to {out}")
PY

# 2) synth each with the official VibeVoice demo entrypoint
for f in "$TXT"/reel_*.txt; do
  n="$(basename "$f" .txt)"
  echo ">> $n"
  python3 "$REPO/demo/realtime_model_inference_from_file.py" \
    --model_path "$MODEL" --txt_path "$f" \
    --speaker_name "$SPEAKER" --device "$DEVICE" --output_dir "$OUT"
done

# The demo writes into --output_dir; make sure each file lands as reel_NN.wav
# (rename if the demo adds a suffix). Then run add_voiceover.py.
echo "Done. WAVs in $OUT — now run: python3 marketing/social/voiceover/add_voiceover.py"
