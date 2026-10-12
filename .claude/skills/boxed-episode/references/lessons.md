# BOXED — lessons learned (each one cost a render)

## Characters + acting
1. **Arms must move like arms.** (User feedback on Ep2: "arms are not moving right".) Causes: IK always picked the
   same bend sign (elbows flipped above the hands) and 0.38 s transitions made 160° jumps. Fix (now in `acting.py`):
   natural-elbow IK (low/outward unless the hand is overhead) with the bend sign fixed per gesture, interpolation in
   joint-angle space with `_move()` (anticipation → main move → overshoot → settle), duration scaled 0.36–0.9 s by
   the size of the move, absolute hand directions per gesture (`HAND_ABS`; add entries for new gestures via the cue
   sheet's `hand_abs`). After every cue edit, scan `acting.json` for joint jumps > 40° (modulo 360) between drawings.
2. **Keep the cast on-model**: always draw from the acting dict (`dict(A["HOST"])`, `G(A, t)`, `Hh(A, t)`) and only
   override placement/scale/extras, so lip sync, blinks and gestures survive. Gary = `gary()`; extend his expressions
   inside your module, never redesign him.
3. **Pen weight**: when you scale a sub-scene, compensate `core.INKMUL` (≈ zoom^-0.5); the Cam layers and
   draw_zee/draw_host already do. Thin hairline ink = something forgot.
4. **Listener behaviour** sells the conversation: give the non-speaker reactions (`REACT`: pupil, brows, smile, lid,
   face modes, glitch) on the jokes.

## Staging + look
5. **Text never on faces**, inside 5% title-safe, ink + shadow always; reveal with `reveal`/`stagger`; check
   overlaps on every contact sheet (labels under circles, captions under hopping props...).
6. **Darkness = multiplied light map** (`light_mask`): ambient ~5–15 plus radial pools on the light sources (the CRT
   screen, faces). A black overlay just makes mud. A **shadow on a wall needs a lit spot behind it** to read.
7. **Dense backgrounds, simple characters**: every new environment gets a kit with layered parallax, rim light in
   magenta/orange/teal, glowing accents (crystals, mushrooms), stipple + strata texture, drips. Never brown/grey.
8. **Frame the cast with the camera maths**, not by eye: `sets.Cam(None, cam).to_screen(...)`, `host_screen`,
   `zee_eyes`. To put the host on the left third with insets on the right, solve `960 + z·(640 − 960 − cam_x) = 600`.
9. Clouds/props behind the sun-planet's face, never across it; small props read as slabs unless they have clear
   features (frame, light, knob, sign).

## Audio
10. **Speech budget:** eleven_v3 with tags ≈ 2.3–2.5 words/s; 93 lines / 1,233 words = 527 s raw. Plan the runtime
    from the word count before recording; tighten inner pauses (> 0.75 s → 0.6 s) rather than cutting jokes.
11. **Short lines** (< ~3.5 s as mp3) return inline instead of spilling — request `outputFormat="pcm_24000"` so they
    spill (grab.py wraps PCM at 24 kHz). **SFX PCM comes back at 48 kHz** (`--rate 48000`). `pcm_44100` → 403 (Pro).
12. Byte-identical result sizes across different lines are normal (durations quantise to 40 ms); verify with md5.
13. Ducking: music sidechain threshold 0.05 ratio 3.5, SFX 0.06/2.2; voices level-matched per speaker; loudnorm
    I=−15 TP=−1.5. Whispered cold opens: trim the music cue (−5 dB) instead of boosting whispers.
14. ElevenLabs SFX was down (503) for all of Ep3 — keep a synth fallback or a placeholder plan; Ep4 had it back.

## Production
15. **The container resets without warning** and the scratchpad dies with it (Ep3's montage modules were lost).
    The session transcript JSONL survives in `~/.claude/projects/...`: tool calls and results can be replayed to
    recover files (Write/Edit inputs, heredocs, Read outputs, images for reference frames). Prevention: the engine
    lives in this skill — copy improvements back, and offer to commit (with the user's OK, feature branch only).
16. **Parallel shot authors**: give each a self-contained brief + per-owner shot sheet + a shared world kit tested
    BEFORE they start; one module per author; ≤7 agents on 4 cores; background; detailed per-shot direction keyed to
    line timings. They all render stills at once — expect ~2× slower stills while they work.
17. **Render early and resumable**: per-shot segments (`render_segs.py`) at `nice 15` while agents work; re-render
    only the shots that change; concat with stream copy.
18. **Delivery cap**: SendUserFile rejects files > 30 MiB → 2-pass encode per part with
    `vbr = (29.2e6·8/dur − 158k)` bps, split at shot cuts, ~110 s per part for 11 minutes.
19. **Never** put model names/IDs in commits, PRs or code comments; commit/push only when the user asks.
