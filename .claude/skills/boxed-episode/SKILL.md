---
name: boxed-episode
description: Make a new episode of BOXED — the psychedelic Adult-Swim-style animated late-night talk show with the TV-headed host, Zee the violet simulant and Gary the eyeball — or fix, re-render, extend, cut down or re-deliver an existing one. Covers the bundled Python+skia BOXED engine, the series bible, ElevenLabs cast voices/music/SFX through the whip MCP, lip-sync + acting tracks, parallel shot-author subagents, rendering on twos, mixing and size-capped delivery. Use this whenever the user says BOXED, "episode N", "next episode", "do episode 5", mentions the host / Zee / Gary / the planet, wants a viral talk or idea adapted into the show, or asks for the cartoon "in the BOXED style" — even if they never say "skill".
---

# BOXED — episode production

BOXED is "the only talk show broadcast from inside the box": a psychedelic, Adult-Swim-style animated late-night
talk show. Each episode adapts one viral idea (simulation theory, Musk's "one in billions", Alan Watts' "Dream of
Life", Plato's Cave...) into ~10–11 minutes of talk-show comedy plus big montage set pieces. The cast, look, voices
and running gags are fixed — read `references/series-bible.md` before writing anything.

This skill is the BOXED-specific layer of the general **video-production** skill (`.claude/skills/video-production/`),
which holds the shared audio / render / delivery / QC know-how. Read that one too if you have not this session.

## The style formula (non-negotiable — the user's words)
> psychedelic adult-animation concept art with flat cel colors, loose black ink outlines, surreal cosmic collage
> composition, bizarre cute creatures, 1970s underground-comic energy, dream logic, saturated neon colors, and
> hand-painted analog imperfections.

Simple cartoon characters with oversized heads, rubbery limbs and huge graphic eyes in front of DENSE backgrounds;
extremely saturated clashing palette (magenta, violet, electric blue, orange, blood red, turquoise, acid green, cream,
yellow); flat cel colour with dots/grain; analog grain + paper; hand-painted irregular lettering. "Insanely high
quality": considered composition, strong silhouettes, readable staging, everything animating, no dead frames.

## Step 0 — get the engine (it lives in the scratchpad and dies with the container)
```bash
bash .claude/skills/boxed-episode/engine/setup.sh          # -> $B (= <scratchpad>/boxed), fonts, lib symlinks, deps, import check
export B=<the path it printed>; cd $B                      # run python as: LD_LIBRARY_PATH=$B/lib python3 ...
```
The snapshot in `engine/eng/` is the canonical engine (core, letters, world, zee, cast, sets, shots_a, acting, lipsync,
shots_ep2 helpers). If you improve an engine module during an episode, copy it back into `engine/eng/` so the next
episode starts from it, and ask the user before committing. `engine/examples/` holds Ep4's main-unit shots and base
module as worked examples of the idioms (cameras, light masks, an episode "world kit").

## The pipeline (details + exact commands: `references/pipeline.md`)
1. **Pick the idea** — something viral, public-domain or properly attributed, with a clear arc and quotable lines.
   Check facts and quotes against the source; credit it on the endcard.
2. **Script** (`templates/make_script.py` → `ep<N>/script.json`): ~90 lines, ~1,100–1,250 words for 10–11 min.
   Structure, voices, tag usage and jokes: see the bible. Every `tts` gets eleven_v3 audio tags.
3. **Voices** — ElevenLabs `eleven_v3` via whip, one call per line, cast voice IDs from the bible, harvest the
   spills with `video-production/scripts/grab.py`. Verify count + no duplicate md5s.
4. **Timeline** (`templates/build_timeline.py`) — lines + gaps + named montage slots; flexible slots stretch to TARGET;
   over-long inner pauses are tightened. If speech alone exceeds ~520 s, target 11:00 rather than cutting jokes.
5. **Lip sync + acting** — `eng.lipsync.build(...)`, then a cue sheet (`templates/make_cues.py`: gestures per line,
   listener reactions, extra gestures + hand directions) and `eng.acting.precompute(...)` → `acting.json`.
6. **Shot list** (`templates/shotlist.py`) — every second owned by a shot (`T###_slug`, owner, desc); write
   `SHOTS_BY_OWNER.md` (each owner's shots with the lines inside them, shot-relative times).
7. **Episode base module** (`templates/shots_epN_base.py` → `eng/shots_ep<N>_base.py`) — generic helpers + a shared
   **world kit** for the episode's new environment (Ep4: the cave kit) so every author's shots match.
8. **Shot authors in parallel** — fill `templates/BRIEF.md`, then spawn one `boxed-shot-author` subagent per montage
   owner (background, ≤7 at once, 45–80 s of screen time each, detailed per-shot creative direction in the prompt).
9. **Main unit (you)** — cold open, title, every talk-show beat, the host's big moment, tag, endcard, stinger
   (`eng/shots_ep<N>.py`). Check stills of every shot (start/mid/end) on contact sheets; fix until they sing.
10. **Audio** — ElevenLabs music cues (house prompts in the bible) placed by `templates/music.py`; SFX samples placed
    by `templates/sfx.py`; `templates/mix.py` → `mix.wav` (per-voice chains, ducking, loudnorm −15 LUFS) + `.srt`.
11. **Render** — `templates/render_segs.py` renders shot-by-shot segments in the background (resumable), then
    `--concat` → `video.mp4`. Start the main unit early; render agent shots as soon as each module is approved.
12. **Deliver** — cut list from `video-production/scripts/plan_parts.py` (never mid-line, hard cuts only, >= ~2 Mbps
    per part: Ep4 = 7 parts), then `templates/finalize.sh` (true-peak-limited mix, each part < 29.5 MB: SendUserFile
    caps files at 30 MiB), then `video-production/scripts/qc_parts.py` (sizes, durations, loudness, true peak on the
    encoded audio, contact sheets you READ); send the parts + the `.srt`, and tell the user the runtime and what changed.

## Hard-won rules (the full list with fixes: `references/lessons.md`)
- **Arms:** natural-elbow IK with a fixed bend sign per gesture and duration-scaled moves; never snap a joint >40°
  between drawings. Check `acting.json` for jumps after every cue edit. (The user noticed bad arms in Ep2.)
- **Characters stay on-model** — use `draw_zee` / `draw_host` from the acting dict (`dict(A["HOST"])` then override
  placement) so mouths stay in sync; Gary = `gary()` seated or `gary_full()` (`eng/gary.py`: legs, turns, arms, every
  expression) — never redraw the cast from scratch or let a shot author build a private copy.
- **Text never covers a face**, stays inside the 5% title-safe margin, always has ink + shadow.
- **Darkness is a multiplied light map** (`light_mask`), not a black overlay — a silhouette on a wall needs a lit spot
  behind it to read.
- **Persistence:** the container resets without warning. Keep the engine in this skill, keep `ep<N>/` data small and
  reproducible, and offer to commit engine/skill changes (only with the user's OK; never push to `main`).
- **Verify agents, don't trust their reports:** render your own stills of every montage module before rendering it.
- **Delivery:** every file < 30 MiB; never cut a part mid-line; true peak <= −1 dBTP measured on the encoded parts;
  always include the `.srt`.

## References
- `references/series-bible.md` — show format, cast designs + voice IDs, sets, palette, fonts, running gags, episode log.
- `references/pipeline.md` — directory layout, exact commands and expected outputs for every step, timings.
- `references/engine-api.md` — the engine modules and every function you will call.
- `references/lessons.md` — the gotchas that cost renders, and their fixes.
- `templates/` — copy into `$B` / `$B/ep<N>/` and edit (each file says what to change).
- Agent definition for montage authors: `.claude/agents/boxed-shot-author.md`; QC: `.claude/agents/video-qc-reviewer.md`.
