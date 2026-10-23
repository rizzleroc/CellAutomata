# Render + delivery

## Animate on twos, deterministically
- 24 fps output, 12 drawings/s: each drawing is rendered once and written twice. All boil/jitter/twinkle is a pure
  function of (seed, drawing index) → any drawing renders identically in any process → split work freely.
- A drawing = `new_surface()` → shot function draws → `finish(surface, d)` (paper, grain, dust) → optional per-shot
  pixel post → fades → raw RGB piped into ffmpeg (`-f rawvideo -pixel_format rgb24 -video_size 1920x1080
  -framerate 24 -i - -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p`).
- Budget ≈1 s per drawing per worker at 1080p with dense scenes (keep shots under ~1.2 s/drawing; cache static
  layers as skia Images). 10 min = 7,200 drawings ≈ 35–60 min on 4 workers.

## Resumable segments (do this instead of one monolithic render)
- Render per shot: drawings `[ceil(t0·12), ceil(t1·12))` → `segs/seg_<d0>.mp4` (written to `.part.mp4`, renamed on
  success). Skip segments that exist; re-render only shots you changed; run at `nice 15` while other work continues.
- Start with your finished shots while subagents are still writing theirs. Concat with the concat demuxer and
  `-c copy` (same encoder params everywhere) → `video.mp4`.
- Wipes/transitions that straddle a cut are fine: each drawing knows its own time.
- Never bake a placeholder into a delivered segment: the range renderer refuses a range owned by a shot with no
  function yet (a broken module only warns at import). Before the concat, list segments older than the code and data
  they were rendered from and re-render them; a container restart kills running renders, so re-run what they hadn't
  reached (BOXED `stale.py`, `segcheck.py`).
- To change a delivered video without re-rendering it (insert or replace a beat), shift by whole drawings and map each
  output drawing to its source cut: the BOXED pipeline's §13 (Ep13's re-cut kept 73 of 76 shots' segments bit for bit).

## Encode for delivery (SendUserFile caps every file at 30 MiB)
- **Where to cut — `scripts/plan_parts.py timeline.json --video video.mp4`.** Never cut while a line is running: the
  voice-over usually continues across shot cuts, and a line split between two files sounds broken. Clean points are
  shot starts in a dialogue gap, or (with `--video`) isolated hard cuts inside music-only montages (ffmpeg scene
  detection; strobes and flashes are skipped). Cuts land on drawing boundaries. The planner picks the fewest parts
  that keep every part >= ~1.95 Mbps video, makes the longest part as short as possible, then prefers shot starts and
  even lengths. Ep4 (11:00): 7 parts of 73–110 s, two of the six cuts inside montages. More parts beat starved bits.
- Per part: `vbr_kbps = (29.2e6 × 8 / duration − 128000 − 30000) / 1000`, 2-pass libx264 `-tune animation -preset slow`,
  maxrate 2×, bufsize 4×, AAC 128k stereo, `+faststart` → each lands ≈ 28–29 MB. `scripts/split_parts.sh`.
- **Audio safety:** limit the mix's true peak to −3.5 dBFS (4× oversampled `alimiter`, `level=0` so the loudness does not
  change) before the AAC encode (it overshoots transients by up to ~2.3 dB), and give every part 20 ms audio fades
  at its edges (no click; a hard start mid-scream also made the encoder spike +2 dB in its first frame).
- Short pieces (≤ 60 s): one file; if a first encode is over the cap, re-encode at a computed bitrate (the 60 s
  cover went 34.1 MiB → 26.98 MiB at 3.6 Mbps).
- Verticals (1080×1920): render natively with a vertical layout rather than cropping when text/composition matter.
- QC the ENCODED parts with `scripts/qc_parts.py out_dir prefix`: every file < 30 MiB, durations add up, loudness on
  target, true peak <= −1 dBTP measured on the AAC, no dead air; then READ its contact sheets (start / 25 / 50 / 75 / end
  of every part: clean first and last frames, nothing cut mid-transition you didn't intend). When a fix changes the mix,
  re-encode every part (loudnorm carries state). A longer re-cut may need one more part to keep the bitrate floor.

## Sending
- `SendUserFile(files=[...parts, .srt], status, display="attach" for the srt)` with a one-line caption; send parts
  together in order. Report: runtime, what's in each part, anything still placeholder, offer revisions.
- If the user asks for "links": these are attachments in the chat; for public links you need a host (ask first).
