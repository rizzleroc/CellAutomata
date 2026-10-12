# BOXED — lessons learned (each one cost a render)

## Characters + acting
1. **Arms must move like arms.** (User feedback on Ep2: "arms are not moving right".) Causes: IK always picked the
   same bend sign (elbows flipped above the hands) and 0.38 s transitions made 160° jumps. Fix (now in `acting.py`):
   natural-elbow IK (low/outward unless the hand is overhead) with the bend sign fixed per gesture, interpolation in
   joint-angle space with `_move()` (anticipation → main move → overshoot → settle), duration scaled 0.36–0.9 s by
   the size of the move, absolute hand directions per gesture (`HAND_ABS`; add entries for new gestures via the cue
   sheet's `hand_abs`). After every cue edit, scan `acting.json` for joint jumps > 40° (modulo 360) between drawings.
2. **Keep the cast on-model**: always draw from the acting dict (`dict(A["HOST"])`, `G(A, t)`, `Hh(A, t)`) and only
   override placement/scale/extras, so lip sync, blinks and gestures survive. Gary = `gary()` seated, `gary_full()`
   (eng/gary.py) for everything else; never redesign him or write a private copy.
3. **One Gary.** Ep4's five montage authors each built a private Gary: five kinds of legs (blue jeans, cream, none,
   custom dancing legs), different arms and eyes; the showrunner had to patch the mismatches. The full-body Gary is
   now `eng/gary.py` (`draw_gary`; `gary_full()` lip-syncs it): cream legs + red sneakers, walk, turns, posable arms,
   every expression. When a shot needs something new for a shared character, add it there (and copy it back into
   this skill), not in one module.
4. **Pen weight**: when you scale a sub-scene, compensate `core.INKMUL` (≈ zoom^-0.5); the Cam layers and
   draw_zee/draw_host/draw_gary already do. Thin hairline ink = something forgot.
5. **Listener behaviour** sells the conversation: give the non-speaker reactions (`REACT`: pupil, brows, smile, lid,
   face modes, glitch) on the jokes.

## Staging + look
6. **Text never on faces**, inside 5% title-safe, ink + shadow always; reveal with `reveal`/`stagger`; check
   overlaps on every contact sheet (labels under circles, captions under hopping props...).
7. **Darkness = multiplied light map** (`light_mask`): ambient ~5–15 plus radial pools on the light sources (the CRT
   screen, faces). A black overlay just makes mud. A **shadow on a wall needs a lit spot behind it** to read.
8. **Dense backgrounds, simple characters**: every new environment gets a kit with layered parallax, rim light in
   magenta/orange/teal, glowing accents (crystals, mushrooms), stipple + strata texture, drips. Never brown/grey.
9. **Frame the cast with the camera maths**, not by eye: `sets.Cam(None, cam).to_screen(...)`, `host_screen`,
   `zee_eyes`. To put the host on the left third with insets on the right, solve `960 + z·(640 − 960 − cam_x) = 600`.
   Check the frame edges on every sheet: Ep4's game show clipped the host's TV head (fixed by re-keying the cameras
   and checking every drawing with a script against the 96 px title-safe line).
10. Clouds/props behind the sun-planet's face, never across it; small props read as slabs unless they have clear
    features (frame, light, knob, sign).

## Audio
11. **Speech budget:** eleven_v3 with tags ≈ 2.3–2.5 words/s; 93 lines / 1,233 words = 527 s raw. Plan the runtime
    from the word count before recording; tighten inner pauses (> 0.75 s → 0.6 s) rather than cutting jokes.
12. **Short lines** (< ~3.5 s as mp3) return inline instead of spilling — request `outputFormat="pcm_24000"` so they
    spill (grab.py wraps PCM at 24 kHz). **SFX PCM comes back at 48 kHz** (`--rate 48000`). `pcm_44100` → 403 (Pro).
13. Byte-identical result sizes across different lines are normal (durations quantise to 40 ms); verify with md5.
14. Ducking: music sidechain threshold 0.05 ratio 3.5, SFX 0.06/2.2; voices level-matched per speaker; loudnorm
    I=−15 TP=−1.5. Whispered cold opens: trim the music cue (−5 dB) instead of boosting whispers.
15. ElevenLabs SFX was down (503) for all of Ep3 — keep a synth fallback or a placeholder plan; Ep4 had it back.
16. **The delivered true peak is not the mix's.** ffmpeg's AAC encoder overshot Ep4's −1.5 dBTP mix to +0.8 dBTP in
    the host's meltdown part. `finalize.sh` now limits the mix at 4× oversampling to −3.5 dBFS (`alimiter level=0`:
    loudness unchanged) into `mix_tp.wav` and fades each part's audio edges by 20 ms (a hard start mid-scream made
    the encoder spike +2 dB in its first frame); every part then measured −2.3 to −3.0 dBTP. Measure the ENCODED
    parts (`qc_parts.py`), not the WAV.
17. **Subtitle cues must not overlap**: the +0.2 s tail made one Ep4 cue run 1 ms into the next ("Turn around.");
    `mix.py` now ends each cue 50 ms before the next one starts.
18. **Music-synced shots must use the cue's real placement.** Ep4's parade bounced to a 108 BPM clock anchored at the
    OUTSIDE slot, but `music.py` places that cue 0.05 s earlier; derive any beat origin from the music PLAN
    (cue start + the track's first-beat offset), not from the slot.

## Production
19. **The container resets without warning** and the scratchpad dies with it (Ep3's montage modules were lost).
    The session transcript JSONL survives in `~/.claude/projects/...`: tool calls and results can be replayed to
    recover files (Write/Edit inputs, heredocs, Read outputs, images for reference frames). Whip/ElevenLabs spills
    stay in `tool-results/_done/` next to it (all 145 of Ep4's audio files did) and can be re-harvested. Prevention:
    the engine lives in this skill — copy improvements back, and offer to commit (with the user's OK, feature branch
    only).
20. **Parallel shot authors**: give each a self-contained brief + per-owner shot sheet + a shared world kit tested
    BEFORE they start; one module per author; ≤7 agents on 4 cores; background; detailed per-shot direction keyed to
    line timings. They all render stills at once — expect ~2× slower stills while they work.
21. **Verify every agent's report yourself** before rendering its shots: your own stills at start / 25 / 50 / 75 /
    end and each key beat, on contact sheets. Ep4 caught a clipped host (sent back with exact timestamps, pixel
    amounts and the fix), Gary's legs drifting between modules, and a music-sync offset; it also showed that three
    "broken-looking" frames were deliberate (a white flash in a fall, a near-black ending, a squinting POV). Ask
    before changing a deliberate beat; fix small cross-module mismatches yourself.
22. **Render early and resumable**: per-shot segments (`render_segs.py`) at `nice 15` while agents work; re-render
    only the shots that change; concat with stream copy. Pixel POST hooks (`POST = {shot_id: fn}` in a module) are
    registered by `render_range` / `stills` via `register_posts`: a custom harness that only calls `load()` won't
    apply them, which is not a render bug.
23. **Wait loops**: `while pgrep -f "<pattern>"` also matches the waiting shell (its own command line contains the
    pattern) and never ends. Wait on a PID (`wait $pid`, `kill -0 $pid`) or a done-file instead.
24. **Delivery**: SendUserFile rejects files > 30 MiB → 2-pass encode per part with `vbr = (29.2e6·8/dur − 158k)` bps.
    Cut with `plan_parts.py`: never mid-line (42 of Ep4's 54 shot boundaries fall inside a line, because the VO runs
    across cuts), only on hard cuts (shot starts in a dialogue gap, or isolated cuts inside music-only montages),
    with the fewest parts that keep >= ~2 Mbps video. Ep4's 11:00 went out as 7 parts of 73–110 s, not 6 starved ones.
25. **Never** put model names/IDs in commits, PRs or code comments; commit/push only when the user asks.
