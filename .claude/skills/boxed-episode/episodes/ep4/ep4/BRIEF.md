# BOXED Ep.4 "THE CAVE" — production brief for shot-module authors

Root: `B=<scratchpad>/boxed` (the path `engine/setup.sh` printed)
(always `cd $B` and run python with `LD_LIBRARY_PATH=$B/lib`; use `python3` = /usr/local/bin/python3 (3.11))

## The show
BOXED is a psychedelic Adult-Swim-style animated late-night talk show. Host: a lanky TV-headed MC in a magenta
tux (phosphor line-art face on a CRT screen). Guest: ZEE, a violet "simulant" with a round head, enormous turquoise
eyes, magenta fringe, two antennae, cream turtleneck with a triangle-eye emblem, orange bell-bottoms. Recurring
cast: GARY (a big eyeball in a striped cream sweater with a red "G" — he sits in the eyeball audience), the ringed
sky planet with a sleepy face, a skull moon, eye-bats, a wizard, a pyramid with an eye, a mushroom.

Episode 4 adapts **Plato's Allegory of the Cave** (Republic VII): prisoners chained since childhood see only shadows
cast by a fire; one is freed, blinded by the fire, dragged up into the sun, slowly learns to see, understands the sun
is behind everything; returns to free the others, can't see in the dark any more, is laughed at — and if they could,
they'd kill him (Socrates, 399 BC). Then: the host realises HE is a flickering rectangle (the cave wall!), Zee: learning
is "turning the whole soul around" toward the light; finale: everyone walks out into a psychedelic sunrise.
Gary plays the freed prisoner. The sun is the show's ringed planet (voice: PLANET, one line "Oh. Hey, Gary.").
Running gag: a hand-shadow BUNNY (the host made one on the wall in the cold open; Gary loves it).
Runtime 11:00 (660 s).

**STYLE FORMULA (non-negotiable):** psychedelic adult-animation concept art with flat cel colours, loose black ink
outlines (the engine's boiling brush), surreal cosmic collage composition, bizarre cute creatures, 1970s
underground-comic energy, dream logic, saturated neon colours (magenta, violet, electric blue, orange, blood red,
turquoise, acid green, cream, yellow), hand-painted analog imperfections, dense backgrounds behind simple
characters, oversized heads, rubbery limbs, huge graphic eyes. It must look INSANELY high quality: considered
composition, strong silhouettes, readable staging, everything animating (boil + motion), no dead frames.
Even the cave is psychedelic: violet/indigo rock with magenta/orange rim light, glowing crystals and mushrooms, a hot
orange wall, neon fire — never brown/grey/realistic.

## Engine (read these files before writing — they are the API)
- `eng/core.py`: PAL palette, INK, W=1920 H=1080, `paint`, `blob(cv, ctrl_pts, fill, w=ink, seed, boil, n, misreg, shade=fn)`,
  `line(cv, pts, width, rgb, seed, boil, n, taper)`, `brush`, `tube` (rubber-hose limbs), `dots`, `stipple`, `sparkle`,
  `ell(cx,cy,rx,ry,n)`, `rect_pts(pts, per_edge)` (keeps polygon edges straight), `cr_closed/cr_open`, `jit`, `hsh(x)`
  (hash noise), `mix`, `core.D` (current drawing index; animation is on twos at 12 drawings/s), `core.INKMUL`
  (pen-weight multiplier — compensate when you scale the canvas: see `sets.Cam`).
- `eng/world.py`: field, sunburst, halo, stars, planet(face=dict(look, smile, lids, lid_rgb), ring=dict(rx, ry, rgb, rgb2, tilt)),
  ribbon, hills, wavy_band, pyramid, eye_glyph, eyeball_walker, eye_bat, ghost, worm, skull_moon, mushroom, wizard, jelly,
  rug, tv(screen=fn(c, (cx, cy, wd, ht))), lamp, couch, floaters, plant, box, padlock, door, island.
- `eng/sets.py`: `Cam(cv, cam).layer(parallax)` context manager (cam = dict(x, y, z)), `Cam.to_screen(X, Y, p)`,
  `cosmos(cv, T, cam, palette "dusk"|"deep"|"acid", seed, planet_xy, extras)` = the shared psychedelic sky,
  `talkshow(cv, T, cam, host, guest, sign)` = the studio set with both performers; `desk`, `mug`, `side_table`, `lava`.
- `eng/letters.py`: `paint_text(cv, text, x, y(baseline), font, size, fill, ink_w, shadow, shadow_rgb, seed, wobble,
  reveal 0..1, stagger, fills=[...], drips, streaks, align, a)`. Fonts: shrik, londrina, londrina_r, marker, bagel,
  chewy, bangers, titan, wet, caveat.
- `eng/zee.py` `draw_zee(cv, P)` and `eng/cast.py` `draw_host(cv, P)`: channel dicts (see DEFAULTS / HOST_DEFAULTS):
  x, y (feet), s (scale), lean, head_tilt, head_dy, squash, blinkL/R, px/py (gaze -1..1), brows, smile, vis/mo
  (mouth viseme/openness), aL_sh/aL_el/aL_hand/aL_pose and aR_* (arm angles in degrees + hand pose: open, flat,
  spread, point, fist, pinch, hold, peace), antL/antR, legs, prop. Host extras: face = normal|sleep|static|heart|
  me|spiral|x|grid|knife|wave|chord, glitch 0..1. Zee extras: head_turn, sweat, blush, lid.
  For natural arm poses from a desired wrist position use `from eng.acting import ik, SH_GUEST, L_GUEST, SH_HOST,
  L_HOST`: `sh, el, _ = ik(SH_GUEST[side], (wx, wy), *L_GUEST, side)` (local coords: feet origin, y negative up,
  side -1 = screen-left arm aL, +1 = aR). Elbows must sit low/outward unless the hand is overhead.
  The acting dict A["HOST"]/A["GUEST"] already has lip-sync + gestures for every line: when you draw the host or Zee
  in your own set, start from it (`dict(A["HOST"])`) and override x/y/s/legs etc so mouths stay in sync.
- `eng/cast.py` also: cosmic_hand, melting_clock, alien, agent (tiny walking sim person), ai_blob, gauge.
- **`eng/shots_ep4_base.py` (import with `from .shots_ep4_base import *`)** — ep4 helpers:
  `TL, LINES, SLOTS, SHOTS`, `loud_at(line_id, T)`, `vis_at(line_id, T)`, `line_at(T)`, `spk_loud(spk, T)`,
  `gary(cv, x, y, s, T, mic=False, wave=0.0)` (Gary with his mouth auto-synced to his AUD lines; y = centre of his eye,
  his sweater hangs ~360*s below), `studio(cv, T, A, cam, t, host={...}, guest={...})`, `caption(...)`, `thought_bubble(...)`,
  `vignette(cv)`, `darkness(cv, a)`, CAM_WIDE / CAM_HOST / CAM_ZEE / CAM_TWO, HOST_POS / GUEST_POS, `R(x0,y0,x1,y1)`.
  **THE CAVE KIT** — use it so all cave shots match: `cave_side(cv, T, cam, fire, carriers, prisoners, shadows,
  mouth_light, wall_shadows)` (the classic cross-section), `cave_wall_view(cv, T, cam, fire, shadows, prisoners, heads_y)`
  (prisoners' POV), and the parts: `prisoner(cv, x, y, s, T, view='side'|'back'|'front', face, look, chained, glow, mouth, anchor)`,
  `carrier(cv, x, y, s, T, holding=kind)`, `statue(cv, kind, x, y, s, T)`, `shadow_shape(cv, kind, x, y, s, T)` with kinds
  bunny, horse, tree, person, bird, fish, jug, star, hand_bunny, `cave_fire(cv, x, y, s, T)`, `firelight(cv, x, y, r, T, a, rgb)`,
  `rock_mass(cv, pts, rgb, rim)`, `chain(cv, p0, p1)`, `crystal`, `glow_mushroom`, `handprint`, `sun_rays`, `wall_surface`,
  colours CV_ROCK, CV_ROCK2, CV_ROCK_DK, CV_WALL, CV_WALL2, CV_SHADOW, CV_FIRE.
  The prisoners ARE the BOXED eyeball audience (squat eyeball creatures); Gary is the one in the striped sweater.
- Look at `eng/shots_ep2.py`, `eng/shots_ep3.py` (finished shots from earlier episodes: camera moves, text pops,
  layering, INKMUL compensation for scaled sub-scenes) for idioms.

## Your shots
`ep4/timeline.json` → `shots[]` (id, t0, t1, owner, desc) and `lines[]` (id, spk, t0, t1, text). A per-owner sheet with
every line inside each shot (with shot-relative times) is in **`ep4/SHOTS_BY_OWNER.md`**. Implement every shot whose
owner is yours as a module-level function **named exactly the shot id**, signature `fn(cv, t, T, A)` (t = seconds since
shot start, T = episode time, A = acting dict with A["HOST"] / A["GUEST"] for this drawing). Put them in your own
module `eng/shots_ep4_<owner>.py` starting with `from .shots_ep4_base import *`. Dialogue audio exists already;
host/Zee mouths come from A (vis/mo); Gary / planet / announcer mouths: `spk_loud`, `vis_at`, `loud_at`.
Time your visual beats to the words (timings in the sheet). Music and SFX are added later in the mix.
Optional: a module-level dict `POST = {shot_id: fn(img_rgb_uint8, lt, dur, T) -> img}` for pixel effects.

## Rules
- Do NOT edit any file except your own module (and scratch files under `ep4/out/<owner>/`). If you need a helper,
  write it in your module (you may copy/extend kit code inside your module). Do not touch timeline/acting/cues/lipsync,
  the base module or other modules.
- Performance budget: 7920 drawings on 4 cores. Keep every drawing under ~1.2 s (check the time printed by the stills
  command). Cache expensive static layers per process if needed (e.g. render once to a skia.Image and drawImage).
- Deterministic: no unseeded randomness (use hsh / seeded numpy rngs keyed on core.D or t).
- Keep important content inside a 5% title-safe margin; text must be legible (ink outline + shadow), never over faces.
- Hard cuts are fine; shots must not start or end on a blank/black frame unless the brief says so.
- Test constantly: `LD_LIBRARY_PATH=$B/lib python3 render4.py --stills 100.0 105.5 ... --out ep4/out/<owner>`
  then LOOK at the PNGs (Read tool; tile 4 stills into one 1920x1080 contact sheet with PIL to save tokens). Check
  several times per shot (start / middle / end) and fix anything off-model, cluttered, illegible or broken.
- When done, reply with: the shot functions implemented, approx render time per drawing for each, and anything
  you could not achieve.
