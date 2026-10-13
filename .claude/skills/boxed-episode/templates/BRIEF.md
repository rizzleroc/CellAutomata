# BOXED Ep.{{N}} "{{TITLE}}" — production brief for shot-module authors

Root: `B={{ABSOLUTE PATH OF $B}}`
(always `cd $B` and run python with `LD_LIBRARY_PATH=$B/lib`; use `python3` = /usr/local/bin/python3)

## The show
BOXED is a psychedelic Adult-Swim-style animated late-night talk show. Host: a lanky TV-headed MC in a magenta
tux (phosphor line-art face on a CRT screen). Guest: ZEE, a violet "simulant" with a round head, enormous turquoise
eyes, magenta fringe, two antennae, cream turtleneck with a triangle-eye emblem, orange bell-bottoms. Recurring
cast: GARY (a big eyeball in a striped cream sweater with a red "G" — he sits in the eyeball audience), the ringed
sky planet with a sleepy face, a skull moon, eye-bats, a wizard, a pyramid with an eye, a mushroom.

Episode {{N}} adapts **{{SOURCE}}**: {{3–5 sentence synopsis of the arc, including who plays what (e.g. "Gary plays
the freed prisoner; the sun is the show's ringed planet")}}. Running gags in play: {{...}}. Runtime {{mm:ss}}.

**STYLE FORMULA (non-negotiable):** psychedelic adult-animation concept art with flat cel colours, loose black ink
outlines (the engine's boiling brush), surreal cosmic collage composition, bizarre cute creatures, 1970s
underground-comic energy, dream logic, saturated neon colours (magenta, violet, electric blue, orange, blood red,
turquoise, acid green, cream, yellow), hand-painted analog imperfections, dense backgrounds behind simple
characters, oversized heads, rubbery limbs, huge graphic eyes. It must look INSANELY high quality: considered
composition, strong silhouettes, readable staging, everything animating (boil + motion), no dead frames.
{{Episode-specific look notes, e.g. "Even the cave is psychedelic: violet rock with magenta/orange rim light, glowing
crystals, a hot orange wall, neon fire — never brown/grey/realistic."}}

## Engine (read these files before writing — they are the API)
- `eng/core.py`, `eng/world.py`, `eng/sets.py`, `eng/letters.py`, `eng/zee.py` (`draw_zee`), `eng/cast.py`
  (`draw_host`), `eng/acting.py` (`ik`), `eng/shots_a.py`, `eng/shots_ep2.py` (seated Gary = `eyeball_creature`,
  `audience_rows`), `eng/gary.py` (`draw_gary`: the standard full-body Gary with legs, turns, arms, expressions). A one-page API summary: `.claude/skills/boxed-episode/references/engine-api.md` in the repo.
- The acting dict A["HOST"]/A["GUEST"] already has lip-sync + gestures for every line: when you draw the host or Zee
  in your own set, start from it (`dict(A["HOST"])`) and override x/y/s/legs etc so mouths stay in sync.
  For extra arm poses: `sh, el, _ = ik(SH_GUEST[side], (wx, wy), *L_GUEST, side)` (feet origin, y negative up,
  side −1 = screen-left arm aL). Elbows low/outward unless the hand is overhead.
- **`eng/shots_ep{{N}}_base.py`** (`from .shots_ep{{N}}_base import *`): `TL, LINES, SLOTS, SHOTS`, `loud_at`, `vis_at`,
  `line_at`, `spk_loud(spk, T)`, `gary(cv, x, y, s, T, mic, wave)` (seated, mouth auto-synced), `gary_full(cv, x,
  floor_y, s, T, **pose)` (standing / walking / emoting Gary, mouth auto-synced; never build your own), `studio(cv, T, A, cam, t,
  host={...}, guest={...})`, `caption`, `thought_bubble`, `vignette`, `darkness`, `firelight`, CAM_* / *_POS, `R()`.
  **THE {{WORLD}} KIT — use it so every {{world}} shot matches:** {{list the kit functions with one-line descriptions}}.
- Look at `eng/shots_ep2.py` and `.claude/skills/boxed-episode/episodes/ep4/eng/shots_ep4.py` (and the Ep4 montage modules beside it) for idioms (camera moves,
  text pops, light masks, layering, INKMUL compensation for scaled sub-scenes).

## Your shots
`ep{{N}}/timeline.json` → `shots[]` and `lines[]`; your owner's sheet with every line inside each shot (shot-relative
times) is in **`ep{{N}}/SHOTS_BY_OWNER.md`**. Implement every shot whose owner is yours as a module-level function
**named exactly the shot id**, signature `fn(cv, t, T, A)` (t = seconds since shot start, T = episode time, A = acting
dict). Put them in `eng/shots_ep{{N}}_<owner>.py` starting with `from .shots_ep{{N}}_base import *`. Dialogue audio exists;
host/Zee mouths come from A; Gary / planet / announcer mouths: `spk_loud`, `vis_at`, `loud_at`. Time visual beats
to the words. Music and SFX are added later. Optional: `POST = {shot_id: fn(img, lt, dur, T) -> img}`.

## Rules
- Edit ONLY your own module (+ scratch files under `ep{{N}}/out/<owner>/`). Copy/extend kit code inside your module if
  needed; never touch timeline/acting/cues/lipsync, the base module or other modules.
- Performance: keep every drawing under ~1.2 s (the stills command prints times); cache static layers per process.
- Deterministic: no unseeded randomness (hsh / rngs keyed on core.D or t).
- 5% title-safe margin; legible text (ink outline + shadow), never over faces.
- Hard cuts are fine; never start/end a shot on a blank or black frame unless the sheet says so.
- Test constantly: `LD_LIBRARY_PATH=$B/lib python3 render.py --stills <t1> <t2> ... --out ep{{N}}/out/<owner>`, tile 4 stills
  per 1920×1080 contact sheet (`ep{{N}}/tools/sheet.py`), LOOK at them, check start/middle/end of every shot, fix
  anything off-model, cluttered, illegible or broken.
- When done, reply with: the shot functions implemented, render time per drawing for each, anything not achieved.
