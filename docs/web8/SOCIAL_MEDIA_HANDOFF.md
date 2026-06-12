# Social Media Video Handoff — CellAutomata / web8 Morphogenesis Reels

**Owner before you:** the previous operator (see git history on `claude/cool-shannon-Sa9Tu`).
**What this covers:** how the vertical "morphogenesis" videos are produced — the ones where a
reaction–diffusion field grows, divides, and reorganizes through different forms, with a relief-lit
3D look, drifting palettes, a moving camera, and an ambient drone. Everything you need to make new
ones, plus the mistakes already paid for so you don't repeat them.

---

## 1. The 30-second mental model

We are **not** filming a screen recording of the web app. We render bespoke videos from the same
simulation engine the web8 experiment uses, in two stages:

```
  Stage A — GENERATOR (Node .mjs)      Stage B — COMPOSITOR (Python .py)
  ┌───────────────────────────┐        ┌────────────────────────────────┐
  │ load the JS sim rule       │        │ read the raw field per frame    │
  │ seed it, step it N times   │ ─────▶ │ crop+zoom (camera)              │
  │ dump the height field to    │  .bin  │ relief-shade with a palette LUT │
  │ a flat binary, one frame    │        │ draw chrome (titles/HUD)        │
  │ per simulation step         │        │ encode H.264 + ambient audio    │
  └───────────────────────────┘        └────────────────────────────────┘
        *_field.bin + *_meta.json              web8_*.mp4  (1080×1920)
```

**Why two stages?** The simulation is the slow part and is deterministic. We dump it once to a `.bin`,
then we can re-composite (new palette, new camera, new HUD) in ~30 min without re-running the sim.
When you only want a *look* change, **edit the Python and re-run it — do not regenerate the field.**

The engine is Gray–Scott reaction–diffusion (and 11 sibling rules) living in
`docs/web8/experiment/rules/`. Every rule exposes the same interface:
`reset()`, `step()`, `renderHeight(h)`, `render(px)`, `population()`, `width`, `height`.

---

## 2. The canonical output format (don't change without reason)

| Property        | Value                                  | Why |
|-----------------|----------------------------------------|-----|
| Resolution      | **1080×1920** (9:16 vertical)          | IG Reels / TikTok / Shorts native |
| Sim grid        | **1000×1000**                          | big enough that colonies read as structure, not noise |
| Display window  | 1000 px square, centered, top at y=380 | leaves room for title above, HUD below |
| FPS             | 24                                     | filmic; keeps file size sane |
| Length          | 2 min (2880 frames) for long-form      | "covers much more time / complex structure" brief |
| Codec           | libx264, yuv420p, crf 20, +faststart   | universal playback, streams on mobile |
| Audio           | 3 stacked sine drones, lowpassed, −0.12 gain, 3s fades | calm ambient bed, no copyright risk |

The compositor writes a silent `*_silent.mp4`, then muxes the audio in a second ffmpeg pass.
ffmpeg is provided by the `imageio_ffmpeg` python package (`imageio_ffmpeg.get_ffmpeg_exe()`), so you
never need a system ffmpeg.

---

## 3. The Gray–Scott "regime map" (your palette of behaviors)

Gray–Scott has two knobs: **F** (feed) and **k** (kill). Tiny changes = completely different life.
These presets are **calibrated to stay alive on a dense 1000² field** (see Lesson 1):

| Name        | F       | k       | Looks like |
|-------------|---------|---------|------------|
| mitosis     | 0.0367  | 0.0649  | spots that divide — one→two→four. **Best opener.** |
| spots       | 0.030–0.034 | 0.062–0.063 | stable dots |
| turbulent   | 0.026   | 0.052–0.054 | roiling chaos, never settles |
| worms       | 0.028–0.032 | 0.056–0.058 | wandering filaments |
| labyrinth   | 0.039–0.040 | 0.058–0.059 | maze / fingerprint |
| stripes     | 0.040–0.042 | 0.059–0.060 | parallel bands |
| coral       | 0.0545–0.055 | 0.062–0.063 | branching reef |
| u-skate     | 0.060   | 0.064   | gliding solitons, living turbulence |
| holes       | 0.046   | 0.0635  | negative spots (voids) |
| negatons    | 0.039   | 0.0645  | inverse blobs that swim |

**To make a video, you string these into a path** and interpolate F/k continuously between
waypoints during the sim. That's the "odyssey." Order them so each transition is plausible
(adjacent regimes morph smoothly; jumping mitosis→u-skate looks like a cut, not a morph).

---

## 4. The video catalogue (what's been shipped + the recipe each used)

| File                          | Theme | Palette | Camera | Path |
|-------------------------------|-------|---------|--------|------|
| `web8_morphogenesis.mp4`      | the original long odyssey | warm-bone→jade→violet | sine-breathing | 12-waypoint full tour |
| `web8_void.mp4`               | dark voids in a luminous field (inverted) | electric-blue / plum / azure | slow pull-back | spots→labyrinth→coral→holes→negatons |
| `web8_forge.mp4`              | magma / volcanic chaos | black→crimson→amber→white-hot | energetic eased breathing | turbulent↔worms↔stripes |
| `web8_crystallogenesis.mp4`   | ice-crystal mineral growth | navy→cobalt→ice→silver | deep slow zoom-in | mitosis→labyrinth→coral, high relief |
| `web8_mitosis_switch_1000.mp4`| live "flip the switch" rule change | per-phase | zoom-punch on flip | mitosis → labyrinth → waves |
| `web8_noctiluca.mp4`          | deep-sea bioluminescence (living light) | cyan-abyss→viridian→chartreuse-gold (non-inverted) | slow lateral submersible drift | turbulent→worms→labyrinth→u-skate→negaton |
| `web8_argentum.mp4`           | scanning-electron micrograph — the only colourless reel | pure false-grey + faint detector grain | stepped magnification zoom w/ dwell | spots→mitosis→coral→labyrinth→coral→spots |
| `web8_terra.mp4`              | morphogenetic cartography (the field as terrain) | hypsometric satellite tint + contour isolines | steady diagonal survey pan | labyrinth→coral→spots→stripes→labyrinth |
| `web8_opalescence.mp4`        | structural colour — a living iridescent membrane | none — thin-film interference (hue from thickness × curvature), drifting | slow orbital push-in | spots→mitosis→coral→labyrinth→u-skate→coral |

**The differentiation rule:** every new reel must differ on *all four axes* —
**(1) simulation path, (2) palette family, (3) camera motion language, (4) structural theme.**
Same engine, but it must not *look* like a sibling. That's the whole brief: "all visually
different, fully."

---

## 5. How to make a NEW reel (step by step)

1. **Pick a concept** and decide its 4 axes (path / palette / camera / theme).
2. **Copy a generator** (`tools/morphogenesis/<x>_gen.mjs`). Edit the `WP` waypoint list and the
   seeding. Output names: `/tmp/<x>_field.bin`, `/tmp/<x>_meta.json`.
3. **Copy a compositor** (`tools/morphogenesis/<x>_film.py`). Edit: the palette LUTs, `palette_at()`
   sequence, `relief()` light direction/strength, `camera()`, accent colors, title text, audio freqs.
4. **Generate** (≈5–8 min for 2880 frames at 1000²):
   `cd /home/user/CellAutomata && node tools/morphogenesis/<x>_gen.mjs`
5. **Preview a single frame before the full encode** — every compositor honors a test mode or you can
   add one. Cheap insurance against a 30-min render of a black screen.
6. **Composite** (≈25–35 min): `python3 tools/morphogenesis/<x>_film.py` → `/tmp/web8_<x>.mp4`.
7. **Deliver** the mp4.

Run generators and compositors **chained in one `nohup bash -c '...'` background job** so the whole
batch survives your session and runs unattended (see `tools/morphogenesis/run_batch.sh`).

---

## 6. LESSONS LEARNED (these were paid for in failed renders — read them)

**1. Low-feed wave regimes STARVE a dense field to black.**
Classic Gray–Scott "waves" (F<0.020, e.g. F0.016/k0.044) look great on a sparse field but, dropped
onto an already-dense labyrinth, eat everything to zero in seconds. Every waypoint must sit in the
"alive band." Calibrated substitute for waves/chaos: **F0.026/k0.051–0.054** (genuine u-skate
turbulence, ~58% coverage, stays alive). Verify a path by watching the `Σv` (population) printout in
the generator log — if it trends toward 0, the path has a death zone.

**2. Painting the WHOLE field uniformly collapses to zero.**
Reaction–diffusion needs *spatial gradients* to do anything. A fully-saturated or perfectly-uniform
start has no edges, so the reaction has nothing to work on and decays. **Seed sparsely** (dozens of
small nuclei), and let it grow to fill. (This killed the first VOID attempt: pop printed `0, 0, 0…`.)

**3. Seed density controls whether you see MOVEMENT or a static result.**
Big/dense seed patches organize in <1 second, then the rest of the video is a still image. For "chaos
organizing into structure," use **many small, scattered seeds at the finest step rate** so the growth
front takes the *whole* segment to sweep the field. Sparse + slow = the drama is visible.

**4. Camera bumpiness has two causes — both now fixed in the templates.**
   - *High-frequency overlapping sines* (e.g. `sin(f/37)+sin(f/43)`) = visible jitter. Use **one or two
     low-frequency components** instead.
   - *Hitting the hard `np.clip` boundary*: when the desired crop center exceeds what the zoom window
     allows, `clip()` pins it to the edge, then it lurches free — a bump. **Fix: scale pan amplitude to
     a fraction (≤0.82) of the available margin `(1000−cs)/2`,** so the center can never reach the clip.
   - Ease the zoom with **smootherstep** `t³(t(6t−15)+10)` (zero 1st & 2nd derivative at the ends), and
     wrap pan in a `sin(πp)` envelope so motion eases in at the start and out at the end.
   - Sanity check: max per-frame center motion should be **well under ~8 px** and **clip-violations = 0**.

**5. A 1000² field viewed whole reads as fine texture, not "big colonies."**
The fix is the **zoomed, panning crop**: show a 150–900-cell window blown up to 1000 px, with a
scalebar reading the true cell count. Individual structures then appear large and legible.

**6. Some sibling rules don't render well — don't waste time on them.**
   - `coacervate`, `vesicles` (native) → un-equilibrated checkerboard. `vesicles` *does* work in SEM
     relief mode (smooth membrane ridges); `coacervate` was dropped.
   - `rna` → flat uniform field. Replaced with `code` (genetic-code quilt) when a distinct look was needed.
   - Viridis-rendered `labyrinth` is **very dark** — multiply the array by ~1.7 before display.

**7. The container is ephemeral — `/tmp` is wiped on cycle.**
A 2880-frame generator takes ~8 min; the container can recycle mid-run and you lose it. Therefore:
**(a)** keep the canonical scripts committed in the repo (this folder), not just in `/tmp`;
**(b)** run long jobs under `nohup` so a dropped session doesn't kill them;
**(c)** if a `.bin` is short (size ≠ `frames×1000×1000×2`), it was interrupted — regenerate.
**(d)** `pkill -f <script>` can kill your own shell (exit 144) — target PIDs, or just let nohup finish.

**8. Always preview ONE frame before a full encode.** A typo in a palette or an off-by-one in the
camera produces 2 min of black at the cost of 30 minutes. The test-frame path is one command.

**9. Audio: three low sine tones (e.g. 52/78/156 Hz), `amix`, `lowpass`, low gain, long fades.**
It reads as a calm "scientific instrument" hum, costs nothing, and is copyright-clean. Pick the triad
to match the mood (deep 43/65/86 for the void; tense 64/96/128 for the forge; pure fifths 55/82/165
for crystal).

---

## 7. Style invariants (the house look — keep these consistent across reels)

- **Fonts** live in `docs/web8/assets/fonts/`: `Italiana-Regular` (display/serif),
  `IBMPlexMono-Regular`/`-Bold` (labels/HUD). The compositors fall back to PIL default if missing.
- **Letter-spaced uppercase** mono for all small labels (`"  ".join(s.upper())`).
- **A corner reticle** framing the live window + a **scalebar** (lower-left) + **F/k + generation
  readout** (lower-right). An accent color drifts with the palette and tints the reticle/F-k text.
- **Title beat** (~3.5 s) fades in over a dimmed first frame: kicker / big serif name / one-line
  subtitle / mono provenance line. **Sign-off** line pinned at the very bottom throughout.
- **Vignette** on the live window to seat it in the black field.
- Keep it **calm, clinical, premium** — "annals of a microscope," not a music video. The motion is
  slow and eased; the chrome is sparse and precise.

---

## 8. File map

```
tools/morphogenesis/
  README — this folder's quick index
  gen.mjs            generic single-rule generator (warmup/frames/steps/modes [F k scatter])
  void_gen.mjs       + void_film.py        → web8_void.mp4
  forge_gen.mjs      + forge_film.py       → web8_forge.mp4
  cryst_gen.mjs      + cryst_film.py       → web8_crystallogenesis.mp4
  lo_gen.mjs         + lo_film.py          → web8_morphogenesis.mp4 (the 12-waypoint odyssey)
  mito_switch_big.mjs + mito_switch_film.py → live "flip the switch" reel
  noctiluca_gen.mjs  + noctiluca_film.py   → web8_noctiluca.mp4 (deep-sea bioluminescence)
  argentum_gen.mjs   + argentum_film.py    → web8_argentum.mp4  (grayscale SEM plate)
  terra_gen.mjs      + terra_film.py       → web8_terra.mp4     (topographic cartography)
  opalescence_gen.mjs + opalescence_film.py → web8_opalescence.mp4 (thin-film iridescence)
  run_batch.sh       nohup chain: gen→film for each, sequentially, unattended
                     (compositors also take `test <f>` / `testc <f>` preview modes; gens take MORPH_NF)
SOCIAL_MEDIA_HANDOFF.md   ← you are here (in docs/web8/)
```

The simulation engine itself is in `docs/web8/experiment/rules/*.js` and the renderers in
`docs/web8/experiment/{viridis.js,sem.js}` — the generators `eval()` these directly and patch the
grid size from 220 to 1000 with a string replace.

---

## 9. If you only remember three things

1. **Stay in the alive band, seed sparse, step slow** — or the field dies or sits still.
2. **Scale camera pan to the margin and ease everything** — or it jerks.
3. **Differ on all four axes every time** — path, palette, camera, theme — or the reels blur together.
