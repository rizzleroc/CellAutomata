# Reel voiceovers (VibeVoice)

Adds spoken narration to the 30 reels using **[microsoft/VibeVoice](https://github.com/microsoft/VibeVoice)**,
Microsoft's open-source long-form TTS model.

## Why generation is a separate step

VibeVoice runs its inference code from PyPI/GitHub, but the **acoustic model
weights are only distributed on HuggingFace**. This build environment's network
policy **blocks huggingface.co** (and the hf-mirror / ModelScope mirrors), and
has **no GPU** — so the weights can't be downloaded or run here. The narration
*scripts*, the *generator*, and the *muxer* all live here; the ~minute of
actual synthesis happens wherever HuggingFace is reachable (a GPU box, or the
official Colab notebook), then the WAVs come back and get muxed in locally.

## Pipeline

```
scripts.json ──(VibeVoice, on a GPU/HF-reachable host)──► voiceover/wav/reel_NN.wav
                                                                  │
                          add_voiceover.py (ffmpeg, runs anywhere) ▼
                                              marketing/social/reels_voiced/reel_NN_*.mp4
```

### 1. Generate the WAVs — `generate_vibevoice.sh`

On a GPU machine or Colab (HuggingFace reachable):

```bash
git clone https://github.com/microsoft/VibeVoice /tmp/VibeVoice
pip install -e /tmp/VibeVoice
bash marketing/social/voiceover/generate_vibevoice.sh   # -> voiceover/wav/reel_NN.wav
```

Knobs (env vars): `VIBEVOICE_MODEL` (default `microsoft/VibeVoice-Realtime-0.5B`;
`microsoft/VibeVoice-1.5B` for the larger TTS model), `VIBEVOICE_SPEAKER`
(a preset under `demo/voices/streaming_model`), `VIBEVOICE_DEVICE`
(`cuda`/`mps`/`cpu`). Make sure each output lands as `reel_NN.wav`.

### 2. Mux into the reels — `add_voiceover.py`

Runs **here** (uses the bundled ffmpeg, no GPU/HF needed):

```bash
python3 marketing/social/voiceover/add_voiceover.py          # all reels with a WAV
python3 marketing/social/voiceover/add_voiceover.py --only 0,5
```

It lowers the original ambient bed under a loudness-normalised voice, and holds
the final frame if the narration runs past the video — so nothing is cut.
Output: `marketing/social/reels_voiced/`.

## Status / validation

The muxer was validated end-to-end on reels 00 and 29 using a throwaway offline
voice (espeak-ng) — the ducking, normalisation, and frame-hold all work. Swap in
the VibeVoice WAVs and re-run for the final, production-quality voiced reels.

WAVs and voiced MP4s are gitignored (large/regenerable). `scripts.json` is the
source of truth for the narration copy.

## Productionizing: VibeVoice as a GPU service

For a durable setup, host VibeVoice on a local GPU (e.g. an RTX 5090) as a
persistent service exposed through the whipgen MCP, so any consumer can request
synthesis without touching HuggingFace at call time. Design:
**[docs/PRD_VIBEVOICE_MCP.md](../../../docs/PRD_VIBEVOICE_MCP.md)**.
