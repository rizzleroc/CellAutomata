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

## Encode for delivery (SendUserFile caps every file at 30 MiB)
- Split at shot cuts into parts of ~100–120 s (6 parts for 11 minutes). Per part:
  `vbr_kbps = (29.2e6 × 8 / duration − 128000 − 30000) / 1000`, 2-pass libx264 `-tune animation -preset slow`,
  maxrate 2×, bufsize 4×, AAC 128k stereo, `+faststart` → each lands ≈ 27–29 MB. `scripts/split_parts.sh`.
- Short pieces (≤ 60 s): one file; if a first encode is over the cap, re-encode at a computed bitrate (the 60 s
  cover went 34.1 MiB → 26.98 MiB at 3.6 Mbps).
- Verticals (1080×1920): render natively with a vertical layout rather than cropping when text/composition matter.
- QC the ENCODED parts: pull one frame from the middle of each into a contact sheet and look; check durations add up.

## Sending
- `SendUserFile(files=[...parts, .srt], status, display="attach" for the srt)` with a one-line caption; send parts
  together in order. Report: runtime, what's in each part, anything still placeholder, offer revisions.
- If the user asks for "links": these are attachments in the chat; for public links you need a host (ask first).
