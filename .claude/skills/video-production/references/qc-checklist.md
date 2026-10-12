# QC checklist (stills → contact sheets → fixes)

Render stills at the start, middle and end of every shot (`render.py --stills t1 t2 ... --out dir`), tile them 2×2
per 1920×1080 sheet (`scripts/sheet.py dir dir/sheet`), and READ the sheets. Fix, re-render, re-look.

## Picture
- [ ] Characters on-model (colours, proportions, eyes, outfit); nobody redrawn from scratch.
- [ ] Mouth shapes plausible for the line at that moment; blinks/gaze not frozen across a long shot.
- [ ] Arms natural: elbows low/outward, hands pointing where the gesture means; no single-drawing snaps
      (scan the acting track for joint jumps > 40° modulo 360).
- [ ] Text legible (ink + shadow), inside the 5% title-safe margin, never over a face or an important prop,
      not overlapping other labels; spelled right; proper nouns and dates correct.
- [ ] Composition: clear focal point, strong silhouettes, dense but readable background, nothing cropped badly at
      frame edges (characters, props, captions).
- [ ] Lighting reads: dark scenes keep faces/sources visible (multiplied light map), silhouettes have a lit ground.
- [ ] Every shot moves (boil + camera drift + character motion); no dead frames, no blank/black frames except
      intended fades; shots start/end on usable frames.
- [ ] Continuity across agents' shots (same world kit, same character scale conventions, consistent palette).
- [ ] Render time per drawing within budget (~1.2 s).

## Sound (inspect levels/plots; you cannot listen)
- [ ] Every line present once, in order; nothing clipped (peaks < −1 dBTP); speakers level-matched.
- [ ] Music under dialogue ducked; music not wall-to-wall where silence plays better; cue boundaries faded.
- [ ] SFX timed to the visual beats; beds not masking speech.
- [ ] Integrated loudness at target (−15 LUFS episodes / −14 music-led).
- [ ] Subtitles match the dialogue text and timing.

## Delivery
- [ ] Each file < 30 MiB; parts split at cuts; durations sum to the runtime; one frame from each encoded part checked.
