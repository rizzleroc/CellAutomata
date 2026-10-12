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
python3 scripts/grab.py <dest_dir> <name_prefix> --rate 48000   # SFX PCM comes back at 48 kHz
```
grab.py names files after the daemon's `savedTo` basename (Windows paths handled with ntpath) and moves processed
spills to `tool-results/_done/`. Results small enough to come back inline (short mp3s) are a pain — avoid them by
requesting `outputFormat: "pcm_24000"` for anything under ~3.5 s (PCM is ~4× bigger, so it spills).

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

## Music
`whipgen_elevenlabs_music(prompt, musicLengthMs, name, returnBytes=true)` — synchronous, ~8–40 s per call; 100 s
cues work. Prompt = "Instrumental <genre/mood>: <instruments>, <arc: builds to / ends with ...>. No vocals."
Generate every cue for an episode in 4–5 parallel calls per message; harvest with grab.py. Place cues with a PLAN
(cue, start, hard end, fade-in, fade-out, trim dB) after RMS-matching each cue to −20 dBFS.

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
- Write an `.srt` from the timeline (speaker-labelled lines, +0.2 s tail).
