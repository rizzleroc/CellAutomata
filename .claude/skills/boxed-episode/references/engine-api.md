# BOXED engine API (Python + skia-python, 1920×1080, 24 fps on twos)

Everything draws into a skia raster canvas `cv`. Animation is **on twos**: 12 drawings/s, each written twice.
`core.set_drawing(d)` sets the drawing index `core.D`; all boil/jitter/twinkle is a pure function of (seed, D), so any
drawing renders identically in any worker. Never use unseeded randomness (use `hsh(...)` or rngs keyed on `core.D`/t).

## eng/core.py — the drawing kit
- `PAL` (palette dict), `INK`, `W, H`, `D`, `INKMUL` (pen-weight multiplier; cameras/characters set it ≈ zoom^-0.5).
- `hsh(x)` hash noise 0..1 · `jit(P, amp, seed)` per-drawing control-point boil · `snoise(u, seed, k)` smooth 1-D noise.
- Shapes: `ell(cx, cy, rx, ry, n, rot, phase)`, `rect_pts(pts, per_edge)` (keeps polygon edges straight under
  Catmull-Rom), `cr_closed(P, n)`, `cr_open(P, n)`, `rot(P, deg, cx, cy)`, `poly_path(P)`, `open_path(P)`, `mix(a, b, t)`.
- Ink + paint: `paint(rgb, a, stroke, blend)` (cached skia.Paint), `brush(cv, pts, w, rgb, taper, var, seed, closed)`
  variable-width ink, `line(cv, ctrl, w, rgb, seed, boil, n, taper)` boiling stroke,
  `blob(cv, ctrl, fill, w, ink, seed, boil, n, misreg, shade=fn(c), a)` off-register cel fill + ink outline (`shade`
  draws clipped inside the fill; `fill=None` = outline only), `tube(cv, ctrl, width, rgb, w)` rubber-hose limb,
  `dots(cv, pts, r, rgb, a)`, `stipple(cv, rgb, box, spacing, r, seed, fn=lambda X,Y: 0..1)` printed dots,
  `sparkle(cv, x, y, r, rgb)` twinkling 4-point star.
- Frame: `new_surface()` → skia surface cleared to night; `finish(surface, d)` → uint8 HxWx3 with paper texture,
  per-drawing grain and dust.

## eng/letters.py — hand-painted lettering
`paint_text(cv, text, x, y_baseline, font, size, fill, ink_w, shadow=(dx,dy)|None, shadow_rgb, seed, wobble,
rot_jit, scale_jit, base_jit, align='center'|'left'|'right', spacing, reveal 0..1, stagger, fills=[...], streaks,
drips, outline_rgb, a)` → width. `measure(text, font, size)`, `wrap_lines(text, font, size, maxw)`.
Fonts: shrik, londrina, londrina_r, marker, bagel, chewy, bangers, titan, wet, caveat (files in `$B/fonts`).

## eng/world.py — the psychedelic set dressing
Sky: `field(cv, rgb)`, `sunburst(cv, x, y, r, n, colors, rot_deg)`, `halo(cv, x, y, radii, colors)`,
`stars(cv, seed, box, n, big)`, `wavy_band(cv, y, height, rgb, amp, freq)`, `hills(cv, y, amp, colors, freq, spacing)`,
`ribbon(cv, ctrl, width, stripes, flow, starband, wav)`, `floaters(cv, seed, box, n, t)`,
`planet(cv, x, y, r, base, bands=[(pos, width, rgb)], tilt, ring=dict(rx, ry, rgb, rgb2, tilt),
face=dict(look, smile, lids, lid_rgb), crater)`, `skull_moon(cv, x, y, r)`.
Creatures: `pyramid(..., look, rays)`, `eye_glyph`, `eyeball_walker(cv, x, y, s, phase)`, `eye_bat`, `ghost`, `worm`,
`mushroom(cv, x, y, s, cap, face)`, `wizard`, `jelly`.
Props: `rug`, `tv(cv, x, y, s, screen=fn(c, (cx, cy, wd, ht)), body)`, `lamp`, `couch(..., part='all'|'back'|'front')`,
`plant`, `box(cv, x, y, w, h, open_amt, label)`, `padlock`, `door(cv, x, y_bottom, s, open_amt, rgb, light)`,
`island(cv, x, y, rx, ry, top, strata, depth, drips)`.

## eng/sets.py — camera + sets
- `Cam(cv, dict(x, y, z[, rot]))`: `with C.layer(parallax):` draws a parallax layer (moves by p·(x, y), zooms by
  1+(z−1)p, sets INKMUL); `C.to_screen(X, Y, p)` world → screen (cv may be None for maths).
- `cosmos(cv, T, cam, palette='dusk'|'deep'|'acid', seed, planet_xy, extras)` the shared sky (4 parallax layers).
- `talkshow(cv, T, cam, host=dict|None, guest=dict|None, sign=0..1)` the full studio incl. performers;
  parts: `desk(cv, x, y_bottom, s)`, `mug(cv, x, y, s, T)`, `side_table`, `lava(cv, x, y, s, T)`.

## eng/zee.py, eng/cast.py — the performers (channel dicts; see DEFAULTS / HOST_DEFAULTS)
`draw_zee(cv, P)` / `draw_host(cv, P)` with: x, y (feet), s, legs, lean, breath, hip, head_tilt, head_dy, squash,
blinkL/R, px/py (gaze −1..1), browL/R, brow_ang, vis (viseme X M A E I O U F L), mo (0..1), smile, aL_sh/aL_el/
aL_hand/aL_pose + aR_* (degrees; poses open, flat, spread, point, fist, pinch, hold, peace), antL/antR spring offsets,
prop (callable `fn(cv, hands)` drawn between arms and hands). Zee extras: lid, head_turn, blush, sweat.
Host extras: face (normal|sleep|static|heart|me|spiral|x|grid|knife|wave|chord), glitch, mic.
Helpers: `zee._hand(cv, wx, wy, ang, pose, mirror, seed, rgb, cuff)`, `zee.arm_points(...)`, `zee.MOUTHS`,
`cast.head_anchor(P)` (local TV centre), `cast.HEAD_S`, `cast.HEAD_Y`, `cast.PHOS`.
Extras in cast.py: `agent` (tiny walking sim person), `alien`, `ai_blob`, `cosmic_hand`, `gauge`, `melting_clock`.

## eng/acting.py — performances
`ik(shoulder, wrist, l1, l2, side, sgn=None)` → (shoulder°, elbow°, sgn) natural-elbow IK (`SH_GUEST/L_GUEST`,
`SH_HOST/L_HOST`, local coords: feet origin, y up negative, side −1 = screen-left arm aL).
`load_cues(path)` merges an episode cue sheet (`initial`, `cues`, `react`, `gestures`, `hand_abs`).
`precompute(timeline, lipsync, out, cues)` → per-drawing dicts `[{"HOST": {...}, "GUEST": {...}}]` with lip sync,
gestures (anticipation/overshoot, duration-scaled), blinks, saccades, nods, emphasis brows, antenna springs, reactions.

## eng/lipsync.py
`build(vo_dir, timeline, out)` → `{line_id: {n, vis[], open[], loud[], emph[], t0, spk}}` at 24 fps from RMS +
3 spectral bands; closures for M/B/P, ≥2-frame holds, emphasis peaks.

## eng/shots_a.py — shot helpers
`ease`, `pop(t, t0, dur)` springy 0→1, `lerp`, `HOST_POS`, `GUEST_POS`, `CAM_HOST`, `CAM_ZEE`, `G(A, t, **kw)` /
`Hh(A, t, **kw)` (acting dict + standard position + overrides; string props → callables), `tag(cv, text, sub, x, y,
t, t0, t1, color, align)` lower-third name tag, `ribbon_wipe(cv, u)` full-frame striped wipe, `page`, `jar`,
`small_box`, `thought_bubble`, `cosmic_brain`.

## eng/shots_ep2.py — reusable helpers inside Ep2's module
`eyeball_creature(cv, x, y_eye, s, t, loud, seed, mic, wave)` (GARY), `audience_rows(cv, t, raise_k, hi_x, loud)`
(foreground eyeball audience), `glow_square`, `pixel_text`, `social_glyph`, `screen_sea`, `mini_world`, `bezel`,
`wireframe`, `hud`.

## Episode base module (`templates/shots_epN_base.py` → `eng/shots_ep<N>_base.py`)
`TL, LINES, SLOTS, SHOTS` from the timeline · `loud_at(line, T)`, `vis_at(line, T)`, `line_at(T)`,
`spk_loud(spk, T)` · `gary(cv, x, y, s, T, mic, wave)` · `studio(cv, T, A, cam, t, host={...}, guest={...})` ·
`caption(cv, text, x, y, t, t0, size, fill, font)` · `thought_bubble` · `vignette(cv, a, inner)` · `darkness(cv, a)` ·
`firelight(cv, x, y, r, T, a, rgb)` · `R(x0, y0, x1, y1)` · `CAM_WIDE`, `CAM_TWO` · plus the episode's world kit
(Ep4: `cave_side`, `cave_wall_view`, `prisoner`, `carrier`, `statue`, `shadow_shape`, `cave_fire`, `rock_mass`,
`chain`, `crystal`, `glow_mushroom`, `handprint`, `sun_rays`, `wall_surface`).

## Main-unit idioms (see `engine/examples/shots_ep4.py`)
`cam_lerp(a, b, u)` eased camera moves · `shake(cam, amt, T)` · `host_screen(A, cam)` / `zee_eyes(A, cam)` screen
positions · `light_mask(cv, [(x, y, r, k, rgb)], ambient)` multiplied light map (darkness that keeps faces readable) ·
`glow(cv, x, y, r, rgb, a)` screen-blend glow · `dark_stage(...)` the set with the backdrop off · `audience_cu(...)`
Gary among the audience with a spotlight · `sunny_set(...)` daytime outdoor set · `shades(...)` Gary's sunglasses ·
`cartoon_door(...)`.

## Renderer contract (`templates/render.py`)
Shot functions `T###_slug(cv, t, T, A)` are collected from `eng.shots_<EPN>` + `eng.shots_<EPN>_<owner>`; a missing
shot renders as a labelled placeholder; `WIPES` = shot ids that get a `ribbon_wipe` at their start; optional module
`POST = {shot_id: fn(img, lt, dur, T) -> img}` pixel effects. `--stills t1 t2 ... --out dir`, `--range a b path`.
