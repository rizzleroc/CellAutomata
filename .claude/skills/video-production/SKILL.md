---
name: video-production
description: The house playbook for making finished videos in this workspace — animated cartoon episodes (BOXED), cellular-automata / morphogenesis social reels, animated album covers and posters, explainers — from idea to delivered MP4s. Covers Python+skia drawing engines, ElevenLabs voices / music / sound effects through the whip MCP, lip sync and acting, splitting work across parallel shot-author subagents, rendering on twos in resumable segments, ffmpeg mixing with ducking and loudness normalisation, contact-sheet QC, and delivery as files under the 30 MiB upload cap with subtitles. Use this skill whenever the user asks for any video, episode, reel, short, trailer, animation, "make it 10 mins", a vertical cut, subtitles, a voiceover, a soundtrack, or to re-render, fix, shorten, extend or re-deliver a video — even if they never say "video production". It routes BOXED work to the boxed-episode skill and CA reels to tools/morphogenesis.
---

# Video production

## 1. Pick the pipeline
| The ask | Pipeline | Read |
|---------|----------|------|
| BOXED (TV-headed host, Zee, Gary), "episode N", a viral idea as a cartoon talk show | Python+skia BOXED engine, ElevenLabs cast, parallel shot authors | `.claude/skills/boxed-episode/SKILL.md` |
| A reel of the CellAutomata simulations (Gray–Scott morphogenesis, ontogeny, slime...) | Node generator → Python compositor, vertical 1080×1920 | in the CellAutomata repo: `tools/morphogenesis/README.md`, `docs/web8/SOCIAL_MEDIA_HANDOFF.md` |
| Animate a still (album cover, poster) | upscale (ONNX Real-ESRGAN via onnxruntime, no torch) → rectify/segment → 2.5D parallax layers + procedural motion → audio bed | `references/stills-to-motion.md` |
| Anything else animated (explainer, short) | reuse the BOXED engine's drawing kit (`core`, `letters`, `world`, `sets.Cam`) without the cast | `.claude/skills/boxed-episode/references/engine-api.md` |

## 2. Non-negotiables
- **Quality bar:** the user wants "insanely high quality". Considered composition, dense backgrounds, strong
  silhouettes, everything moving, legible text, no dead frames. You LOOK at stills of every shot before rendering.
- **Deliver files, not promises:** every deliverable is an MP4 < 30 MiB (SendUserFile's cap) — split long videos into
  parts at hard cuts where no line is running (`scripts/plan_parts.py`) — plus an `.srt` when there is dialogue. Send
  drafts early when they are meaningful.
- **Persist the toolchain:** the container resets without warning and wipes the scratchpad. Keep reusable engines and
  scripts inside a skill folder; offer to commit them (only with the user's OK, feature branch, never `main`).
- **Facts and people:** every fact and quote comes from a checked source (BOXED keeps one `FACTS.md` per episode);
  never draw a real person's likeness, a logo or a brand unless the user asks for it (BOXED's content rules are stricter).
- **Write things down when they happen:** every generation prompt goes to a file when the call is made, every subagent's
  full prompt before it is spawned — the session log can be compacted and the container reset at any time.
- **Honesty:** report the real runtime, what is placeholder, what failed. No model names/IDs in commits or PRs.

## 3. The production line (each stage has a concrete output)
1. **Brief + script** → script source (`make_script.py` → `script.json`): speakers, subtitle text, TTS text with tags.
   Budget speech at ≈2.3–2.5 words/s (eleven_v3 with tags); plan the runtime from the word count.
2. **Audio assets** → `vo/`, `music_el/`, `sfx_el/` via the whip MCP (ElevenLabs), every take checked with a local
   speech recogniser, every prompt written down. → `references/audio-elevenlabs.md`
3. **Timeline** → `timeline.json` (lines + gaps + named visual slots stretched to a target length; slots that sit on a
   measured music cue — a title hit, a finale grid — keep fixed lengths).
4. **Performance** → `lipsync.json` (visemes/openness/emphasis at 24 fps) and `acting.json` (gestures, blinks, gaze).
5. **Shot list** → `timeline.json["shots"]` + per-owner sheets; a shared world kit for any new environment.
6. **Shots** → shot functions `T###_slug(cv, t, T, A)` in modules (you + parallel subagents, see §4).
7. **Stills QC** → contact sheets of start/mid/end of every shot; fix; repeat. → `references/qc-checklist.md`
8. **Render** → per-shot segments in the background (resumable), concat → `video.mp4`. → `references/render-and-delivery.md`
9. **Mix** → `mix.wav` (per-voice chains, music + SFX ducked under dialogue, loudnorm −15 LUFS) + `.srt`. The stems
   are in by default (a voices-only mix once shipped); check a music-only window.
10. **Encode + deliver** → `plan_parts.py` cut list, `split_parts.sh` (true-peak-limited audio, parts < 29.5 MB),
    `qc_parts.py` on the encoded parts (sizes, loudness, true peak, dead air, contact sheets), SendUserFile, short
    report. A fix that changes the mix means re-encoding every part.

## 4. Multi-agent shot production
Use parallel subagents when the video has more than ~3 minutes of distinct set pieces:
- Prepare FIRST: timeline, acting, measured word timings, shot list, per-owner sheet, a written brief (style formula,
  engine API, content rules, exact on-screen strings, one placement per shared prop, every hand-off between authors in
  numbers, the music clocks), and a shared kit for any new world — test-rendered — so all authors match. Save each
  author's full prompt to a file before spawning.
- One module per author, one owner name per author, 35–80 s of screen time each, ≤7 authors on 4 cores, all spawned in
  one message with `run_in_background: true` (an explicit lighter model when cost matters); authors render stills
  through a shared slot wrapper (`flock`), a few at a time. Agent definitions: `.claude/agents/video-shot-author.md` (generic),
  `.claude/agents/boxed-shot-author.md` (BOXED); QC pass: `.claude/agents/video-qc-reviewer.md`.
- Put per-shot creative direction in each prompt (what happens on which words). Authors must test their own stills and
  report render time per drawing.
- While they work: write your own shots, the audio, the mix, and start rendering your finished shots at low priority.
- When each reports back: review its stills yourself (contact sheets of every shot and both sides of every hand-off),
  request fixes via SendMessage if needed, then render its segments. An author stopped by a usage limit resumes with
  SendMessage; if authors stop for good (a spend limit), their saved modules can still be complete — import, review,
  and finish what's missing yourself.

## 5. Environment essentials (details: `references/environment-gotchas.md`)
- `python3 -m pip ...` (bare `pip` is another interpreter); skia needs `LD_LIBRARY_PATH=$B/lib` with libEGL/libGLESv2
  symlinked from `/opt/pw-browsers/chromium-*/chrome-linux/`; ffmpeg = `imageio_ffmpeg.get_ffmpeg_exe()`.
- whip MCP: call `whipgen_help` first; results spill to `tool-results/*.txt`; harvest with `scripts/grab.py`
  (Windows daemon paths, PCM rates handled).
- Render on twos: 12 drawings/s, each written twice at 24 fps; deterministic per drawing so workers can split ranges.
- `pgrep -f` / `pkill -f` match their own shell: wait on or kill PIDs. Hugging Face is blocked: fetch models from
  GitHub releases.

## Scripts
- `scripts/grab.py <dest> <prefix> [--rate 24000|48000]` — harvest whip/ElevenLabs spills into mp3/wav files.
- `scripts/sheet.py <dir> <out_prefix> [files...]` — 2×2 labelled contact sheets of stills.
- `scripts/plan_parts.py <timeline.json> [--video video.mp4]` — choose delivery cut points: never mid-line, on hard
  cuts (shot starts, or isolated cuts inside music-only montages), the fewest parts that keep >= ~2 Mbps video.
- `scripts/split_parts.sh <video> <audio> <out_prefix> "a b name" ...` — true-peak-limits the audio, then 2-pass
  encodes into parts < 29.5 MB (20 ms audio edge fades).
- `scripts/qc_parts.py <out_dir> <prefix>` — size vs cap, durations, loudness + true peak of the ENCODED parts, and
  frames from each part on contact sheets; exits 1 on a failure.
