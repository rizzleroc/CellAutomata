# Audio with ElevenLabs (through the whip MCP)

## Session start
1. `mcp__whip__whipgen_help` once (no args) — required before other whip tools; `whipgen_status` to confirm the
   daemon (it runs on a Windows host: `outDir F:\whipgen-mcp\whipgen-out`, paths with backslashes).
2. Load schemas with ToolSearch `select:mcp__whip__whipgen_elevenlabs_speak,...music,...sound_effects`.
3. Do NOT pass `saveTo` (must be inside the daemon's allowed roots); use `name` + `returnBytes: true`.

## How bytes reach you
Every audio result is base64 in JSON. Results bigger than the MCP output cap (~70k characters) are written by the
harness to `~/.claude/projects/<project>/<session>/tool-results/mcp-whip-whipgen_elevenlabs_*.txt` and the call
"errors" with "exceeds maximum allowed tokens" — that is the success path. Harvest:
```bash
python3 scripts/grab.py <dest_dir> <name_prefix>            # TTS: mp3 kept, PCM wrapped as 24 kHz WAV
python3 scripts/grab.py <dest_dir> <name_prefix> --rate 48000 --ch 2   # SFX PCM (pcm_48000) comes back 48 kHz STEREO
```
SFX requested as `pcm_48000` arrive as interleaved stereo: wrapped as mono they play at half speed and twice as long
(BOXED Ep12 caught it when a 6 s bed measured 12 s). Check `duration ≈ durationSeconds` after every harvest.
grab.py names files after the daemon's `savedTo` basename (Windows paths handled with ntpath) and moves processed
spills to `tool-results/_done/`. Results small enough to come back inline (short mp3s) are a pain — avoid them by
requesting `outputFormat: "pcm_24000"` for anything under ~3.5 s (PCM is ~4× bigger, so it spills).

## Size every request to its spill, and write the prompt down
- Music: up to ~60 s per call (longer calls hit the MCP's 230 s timeout); effects: request 2.6 s or more (shorter ones
  come back inline, tens of KB in context, invisible to grab.py) and trim with `dur=` when placing; short voice lines:
  `outputFormat="pcm_24000"` so they spill.
- Write every music and effect prompt to the project folder when you make the call (BOXED: `ep<N>/audio/PROMPTS.md`,
  then `prompts.json` for the sound catalog). A prompt that lives only in the session log is lost when the log is
  compacted; recovering it from the transcript JSONL works only while that survives.

## Voices (TTS)
`whipgen_elevenlabs_speak(text, voiceId, modelId="eleven_v3", stability=0.5, similarityBoost=0.75, name, returnBytes=true)`
- eleven_v3 audio tags in square brackets steer delivery: `[whispering]`, `[excited]`, `[deadpan]`, `[giggles]`,
  `[sniffles, sad]`, `[game show announcer, booming]`, `[very fast disclaimer]`, `[pause]`, `[slow dread]`, ...
  Tags are spoken as performance, not words. "..." creates pauses (they can run long — tighten later).
- Spell numbers/dates for TTS ("three ninety-nine B.C."), keep the readable form in the subtitle text.
- `pcm_44100` is Pro-tier only (403). `pcm_24000` and the default `mp3_44100_128` work.
- 6–8 calls per message, then harvest; ~2–3 s per call. Verify count and `md5sum | uniq -d` (identical sizes for
  different lines are normal: durations quantise to 40 ms).
- Budget: ≈2.3–2.5 words/s with tags. BOXED cast voice IDs live in the boxed-episode series bible.

## Check every take with a local speech recogniser
A take can babble, drop or add words, or end cut off. Transcribe each one locally — whip's transcribe runs on the
remote daemon and can't read local files, and Hugging Face is blocked (403) — with NeMo Parakeet TDT int8 from the
sherpa-onnx GitHub releases in a venv, and score it against the script by word error rate (BOXED
`templates/check_takes.py`: flag WER > 0.15 or a loud last 50 ms). Re-record what fails, check the retakes the same way,
and keep the rejected takes aside. The same recogniser gives word onsets for a timeline (BOXED `asr_words.py`: its
stamps run ~90 ms early, so add 0.05 s and snap words after punctuation to the measured pause ends).

## Music
`whipgen_elevenlabs_music(prompt, musicLengthMs, name, returnBytes=true)` — synchronous, ~8–40 s per call; 100 s
cues work. Prompt = "Instrumental <genre/mood>: <instruments>, <arc: builds to / ends with ...>. No vocals."
Generate every cue for an episode in 4–5 parallel calls per message; harvest with grab.py. Place cues with a PLAN
(cue, start, hard end, fade-in, fade-out, trim dB, optional offset into the cue) after RMS-matching each cue to −20 dBFS.
Measure a cue before keying pictures to it: ElevenLabs doesn't always deliver the prompted BPM (a "120 BPM" bed ran
125), and a full-band onset scan locks onto the hats on the "and", so take the tempo by autocorrelation and the beat
phase from the kick's low band (BOXED `templates/tempo.py`, `kick_grid.py`). Lengthen or shorten a cue by cutting whole
bars on its grid, just before a kick, with a 12 ms crossfade.

## Sound effects
`whipgen_elevenlabs_sound_effects(text, durationSeconds 0.5–22, name, returnBytes=true)`. Describe the sound
concretely ("Studio audience applause and cheering in a TV talk show, enthusiastic clapping and a few whoops, then dies
down"). Normalise each sample's RMS per category (beds −29/−30 dBFS, crowd −21/−23, spot effects −20/−25), then place
cues `c(name, t, dur, gain, pan, fade)` and loop beds `bed(name, a, b)` with crossfades. It was 503 for a whole
episode once — keep a fallback (synth, or simply fewer effects) rather than blocking.

## Voice prep + timeline
Trim each clip (−42 dB threshold, 40 ms head, 120 ms tail, micro-fades), resample to 48 kHz mono, tighten inner pauses
> 0.75 s to 0.6 s (crossfaded cuts). Lay lines out with per-line gaps and named visual slots; stretch flexible slots to
the target length.

## Lip sync data
Per line at 24 fps: RMS loudness → openness, three spectral bands (150–900, 900–2600, 2600–7000 Hz) → viseme
(X M A E I O U F L), short dips → M/B/P closures, ≥2-frame holds, emphasis = loudness above the local mean. Drives
mouths, nods and brows; `vis_at` / `loud_at` drive characters without acting tracks.

## Mix (ffmpeg)
- Per speaker chain, then level-match each speaker's line RMS to a target (−16 dB): host "TV speaker" (HP 140, LP 8.5k,
  presence +3 dB, compressor, short echo); clean guest; audience mic (HP/LP + room echo); announcer (heavy broadcast
  compression); cosmic voice (pitch down 10%, long echoes).
- Music sidechain-ducked under dialogue (threshold 0.05, ratio 3.5, attack 25, release 600); SFX ducked lightly
  (0.06 / 2.2 / 8 / 220); `amix normalize=0`; `loudnorm=I=-15:TP=-1.5:LRA=11` (episodes) or two-pass linear loudness
  (`scripts/loud.sh`, −14 LUFS for music-led pieces).
- Write an `.srt` from the timeline (speaker-labelled lines, +0.2 s tail, clamped to end 50 ms before the next cue
  so cues never overlap). Since BOXED Ep10 a long line is split into readable cues of at most 2 rows × 42 characters
  (wrap-aware, broken at sentence and clause ends, never mid-thought), each timed from its first word's measured onset
  (the BOXED `templates/mix.py`).
- The stems are in the mix by default and a missing one is an error (a voices-only mix once passed every check and
  shipped); print which stems went in and measure a music-only window.
- The loudnorm true-peak target is not the delivered peak: ffmpeg's AAC encoder overshoots sharp transients (Ep4: a
  −1.5 dBTP mix encoded to +0.8 dBTP; a squeak or a click by up to ~5 dB; a music cue entering as a step under a crash
  by +6.7 dB). Delivery therefore limits the mix at 4× oversampling to −3.5 dBFS before encoding (`split_parts.sh` /
  the BOXED `finalize.sh`) and you measure the encoded parts. Prevent it at the source too: bright transients at gain
  ≤ 0.45, every music cue with ≥ 30 ms of fade-in, every normalised effect capped at full scale; test-encode the hottest
  and brightest windows before encoding everything.
- loudnorm's single pass carries state: a fix late in the programme shifts the gain after it by hundredths of a dB, so
  after any mix fix re-encode every part, not only the one that failed.
- A per-line filter before the speaker chain sells a gag cheaply (BOXED Ep14: a voice from inside a cardboard box —
  two 950 Hz low-passes, +5 dB at 380 Hz, a 9 ms echo; `LINE_FX` in the BOXED `templates/mix.py`).
