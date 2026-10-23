---
name: boxed-episode
description: Make a new episode of BOXED — the psychedelic Adult-Swim-style animated late-night talk show with the TV-headed host, Zee the violet simulant and Gary the eyeball — or fix, re-render, extend, cut down, re-cut, rebuild or re-deliver an existing one. Covers the bundled Python+skia BOXED engine, the series bible with its locked episode format and content rules, ElevenLabs cast voices/music/SFX through the whip MCP plus the repo's sound library, take checks and word timings with a local speech recogniser, lip-sync + acting tracks, parallel shot-author subagents, rendering on twos, mixing and size-capped delivery, and saving an episode so it restores bit-identical. Use this whenever the user says BOXED, "episode N", "next episode", "do episode 15", mentions the host / Zee / Gary / the planet, wants a viral talk or idea adapted into the show, or asks for the cartoon "in the BOXED style" — even if they never say "skill".
---

# BOXED — episode production (the skill lives in rizzleroc/boxed)

The BOXED skill — the series bible and its content rules, the pipeline, every lesson of season one, the templates and
tools, the engine snapshot, the source of every finished episode (Ep4–14) and the sound library with every voice, cue
and effect — lives in the **rizzleroc/boxed** repository. This folder only points there, so the copy you work from is
never stale (an Ep4-era copy lived here until season one ended).

## Before anything else
1. Attach the repo: `add_repo` with owner `rizzleroc`, repo `boxed` (access `push` if you will save an episode), clone it
   to `/home/user/boxed` with the command the tool returns, and `register_repo_root` it so its CLAUDE.md, skills and
   agents load.
2. Read `/home/user/boxed/.claude/skills/boxed-episode/SKILL.md` and follow it from there (engine setup, the locked
   format, the pipeline, the references), together with `.claude/skills/video-production/SKILL.md`.
3. Shot authors: the `boxed-shot-author` agent definition in this repo is a copy of the boxed repo's
   (`/home/user/boxed/.claude/agents/boxed-shot-author.md`); point the briefs at the boxed checkout's absolute paths.
4. Save finished episodes, sounds, lessons and engine changes to the boxed repo (feature branch + draft PR there), not
   here.

If the boxed repo can't be attached, say so and stop rather than working from memory: the engine, the house sound
library and the season's kit are only there.
