# tools/morphogenesis — vertical reaction–diffusion reels

Production scripts for the web8 "morphogenesis" social videos (1080×1920, 24 fps, ~2 min,
H.264 + ambient drone). **Full playbook + lessons learned:
[`docs/web8/SOCIAL_MEDIA_HANDOFF.md`](../../docs/web8/SOCIAL_MEDIA_HANDOFF.md).**

## Pipeline
Two stages per reel: a Node **generator** runs the Gray–Scott sim at 1000² and dumps the height
field to a flat `uint16` binary; a Python **compositor** crops/relief-shades/captions it and encodes
the vertical video + a calm sine-drone bed.

```
<stem>_gen.mjs  →  /tmp/<stem>_field.bin + /tmp/<stem>_meta.json  →  <stem>_film.py  →  /tmp/web8_<stem>.mp4
```

Run from the **repo root** (the generators read `docs/web8/experiment/**` by relative path):

```bash
# one reel:
node tools/morphogenesis/noctiluca_gen.mjs && python3 tools/morphogenesis/noctiluca_film.py

# a whole batch, unattended (survives session drop):
nohup bash tools/morphogenesis/run_batch.sh noctiluca argentum terra > /tmp/batch_main.log 2>&1 &
```

## Reels in this folder
Each differs from the others — and from the earlier catalogue (morphogenesis / void / forge / cryst /
mito-switch) — on **all four axes**: simulation path, palette family, camera language, structural theme.

| stem        | theme | path | palette | camera |
|-------------|-------|------|---------|--------|
| `noctiluca` | deep-sea bioluminescence — living light in black water | turbulent → worms → labyrinth → u-skate → negaton | cyan abyss → viridian → chartreuse-gold (non-inverted) | slow lateral submersible **drift** |
| `argentum`  | scanning-electron-micrograph plate (the only colourless reel) | spots → mitosis → coral → labyrinth → coral → spots | pure false-grey + faint detector grain | stepped **magnification** zoom with dwell |
| `terra`     | morphogenetic cartography — the field as living terrain | labyrinth → coral → spots → stripes → labyrinth | hypsometric satellite tint + contour isolines | steady diagonal **survey** pan |
| `opalescence` | structural colour — a living iridescent membrane | spots → mitosis → coral → labyrinth → u-skate → coral | **no palette**: thin-film interference, hue from thickness × curvature, drifting | slow **orbital** push-in |
| `zebra`     | Turing's stripe — animal coat morphogenesis | stripes ↔ labyrinth | bold black-&-cream hide | vertical **scroll** |
| `cheetah`   | the predator's coat — dark spots on gold | spots ↔ mitosis | golden hide, dark spots | prowling **push-in** |
| `crystals`  | an amethyst geode (distinct from the ice `cryst` reel) | labyrinth → stripes → coral → labyrinth | violet facets, extreme relief | orbiting **zoom-in** |
| `peacock`   | iridescent ocelli (feather eyes) | spots ↔ mitosis | concentric gold→emerald→peacock-blue→pupil by dome height | tight **drift** among eyes |
| `feathers`  | iridescent plumage (starling/grackle) | worms ↔ stripes | structural-colour barbs under raking light | combing **drift** |
| `radiating` | a chromatic mandala | spots → mitosis → coral → mitosis → spots | screen-space radial hue rings flowing outward | centred gentle **zoom** |
| `fungal`    | the mycelial life cycle — one spore to fruiting body | germination(coral) → hyphae(worms) → mycelium(labyrinth) → anastomosis → primordia(u-skate) → fruiting(mitosis) → sporulation(negatons) → humus | dark humus → ivory mycelium → amber fruiting → foxfire-green spores | travelling diagonal **push-in** to the fruiting climax, then ease back |

Each compositor honours three modes so you can preview before a full encode (HANDOFF Lesson 8):

```bash
python3 tools/morphogenesis/terra_film.py test  470   # the live window only  → /tmp/terra_test.png
python3 tools/morphogenesis/terra_film.py testc 470   # window + chrome       → /tmp/terra_testc.png
python3 tools/morphogenesis/terra_film.py             # full render           → /tmp/web8_terra.mp4
```

Generators accept `MORPH_NF` to shrink the frame count for smoke tests:
`MORPH_NF=600 node tools/morphogenesis/terra_gen.mjs`.

## Companion reel — `ontogeny` (the *other* origin story)

`ontogeny_gen.mjs` + `ontogeny_film.py` don't use Gray–Scott at all — they render the real
**[`docs/ontogeny/`](../../docs/ontogeny/)** app (the human-development simulation) as a vertical
reel, driving its own engine end to end: `sim.js` `conceive()` for the outcome, `render.js`
`buildHeight()` for the specimen height field, and `sem.js` for the warm-sepia micrograph. The
Python side rebuilds the app's **vitrine UI** — register · SEM stage (corner-mats · LIVE·SEM ·
live count) · caption · diagnosis (verdict · membranes · stats · timeline) — at 1080×1920. The
showcased scenario is the app's own default: identical **MCDA twins** (seed 7), so the embryo
visibly *splits* mid-reel. Same two-stage contract:

```bash
node tools/morphogenesis/ontogeny_gen.mjs && python3 tools/morphogenesis/ontogeny_film.py
# smoke (resample the whole timeline, then preview a vitrine frame):
ONTO_NF=300 node tools/morphogenesis/ontogeny_gen.mjs && python3 tools/morphogenesis/ontogeny_film.py testc 150
```

## Grand arc — `origins` (Conway → abiogenesis → ontogeny)

`origin_film.py` stitches the whole story into one reel, as seventeen SEM specimen plates under
one microscope, in three numbered acts: **Conway's Game of Life** (a new
[`conway.js`](../../docs/web8/experiment/rules/conway.js) rule — life as a pure rule) → the
**twelve-stage origin-of-life lab** (reusing the `gen.mjs` SEM/native plates) → **ontogeny**
(the singleton specimen — life as a person). Each act gets its own accent (digital teal-green ·
amber chemistry · ontogeny teal).

```bash
# sources:
node tools/morphogenesis/gen.mjs conway 0 130 1 n
for s in soup:n grayscott:w raf:n vesicles:w vents:n minerals:n chirality:n rna:n code:w natural_selection:n luca:n life:n; do
  node tools/morphogenesis/gen.mjs ${s%:*} 200 130 1 ${s#*:}; done
ONTO_PRESET=singleton node tools/morphogenesis/ontogeny_gen.mjs
python3 tools/morphogenesis/origin_film.py     # -> /tmp/web8_origins.mp4
```

## Wild outcomes gallery — `wild_film.py`

`wild_film.py` is a gallery of the ontogeny engine's most dramatic *outcomes*, eight to a reel:
identical MCMA, conjoined, 2+1 triplets, quintuplets, triploidy, trisomy 21, chimerism, the
vanishing twin. Each plate develops the **real** specimen for that scenario (per-scenario bins via
`ONTO_OUT`) under its verdict + the flags that make it wild (amber for non-viable/warn, magenta
otherwise).

```bash
for p in mz-mcma conjoined triplets-2-1 quints triploidy trisomy chimerism vanishing; do
  ONTO_PRESET=$p ONTO_OUT=/tmp/onto_$p ONTO_NF=240 node tools/morphogenesis/ontogeny_gen.mjs; done
python3 tools/morphogenesis/wild_film.py        # -> /tmp/web8_wild_outcomes.mp4
```

## Wild spectrum — `wild_spectrum_film.py`

The *whole lab* driven to its extremes, one wild outcome per stage: Conway overpopulation collapse,
Gray–Scott u-skate solitons, a Miller–Urey lightning storm, runaway autocatalysis, violent vesicle
budding, a proton flood, runaway polymerisation, shattered chirality, the RNA & digital-life **error
catastrophes**, a dissolving genetic code, boom-and-bust selection, a LUCA that never converges — and
quintuplets as life's human extreme. Each plate is the **real** sim at wild parameters, fed in via a
new `gen.mjs` `GEN_PARAMS` env (JSON of `{param:value}`):

```bash
GEN_PARAMS='{"mutation":0.3}'   node tools/morphogenesis/gen.mjs rna 120 130 3 n   # error catastrophe
GEN_PARAMS='{"density":0.5}'    node tools/morphogenesis/gen.mjs conway 0 130 1 n  # overpopulation
node tools/morphogenesis/gen.mjs grayscott 220 130 1 w 0.062 0.0609                # u-skate solitons
# …then:
python3 tools/morphogenesis/wild_spectrum_film.py    # -> /tmp/web8_wild_spectrum.mp4
```

## Deep dive — searching F/k space with an agent swarm

`gs_sweep.mjs` combs a rectangle of Gray–Scott (F,k) space, scores each point for
structure/complexity/motion, and emits a 6-up montage + ranked JSON for an agent to judge **by eye**.
A swarm of agents (one per region) sweeps the whole plane in parallel; `gs_curate.mjs` re-renders the
champions honestly (full SEM) to drop the per-tile-normalisation artefacts; `gs_deepdive_gen.mjs`
matures the finalists and captures their living dynamics; `gs_deepdive_film.py` renders them as an
aurora-relief reel.

```bash
# one region (each swarm agent runs one):
node tools/morphogenesis/gs_sweep.mjs s11 0.030 0.050 0.052 0.059 8 8 100 2800
# finalists -> reel:
node tools/morphogenesis/gs_deepdive_gen.mjs && python3 tools/morphogenesis/gs_deepdive_film.py
# premium cut — 8 best at 512², a slow eased descent into the texture + bloom glow:
node tools/morphogenesis/gs_deepdive2_gen.mjs && python3 tools/morphogenesis/gs_deepdive2_film.py
```

### Deeper search (motion-weighted)

A second swarm pass adds a **sustained-motion** term to `gs_sweep.mjs` (favouring solitons / waves /
chaos) over a finer 11×11 grid focused on the alive band (~1,900 points). It surfaced a fresh seam of
**defect / hole / coexistence** regimes — and, honestly, also showed that the low-kill (k≈0.052)
"spiral / target-wave" picks are *per-tile-normalisation artifacts* that saturate to a flat field at
full resolution (caught by re-rendering). `gs_deepsearch_gen.mjs` + `gs_deepsearch_film.py` render the
ten real champions as a premium deep-dive reel.

```bash
node tools/morphogenesis/gs_deepsearch_gen.mjs && python3 tools/morphogenesis/gs_deepsearch_film.py
```

## Unique animations — `anim_probe.mjs` + `unique_anim_film.py`

A 15-agent swarm probed **every** rule in the lab to find each one's single most *unique animation*
(distinctive motion, not a static pattern). `anim_probe.mjs` runs any rule and emits a time-filmstrip
(K snapshots) + a motion score so an agent can judge the dynamics by eye; `gen.mjs` gained a `GEN_OUT`
env so several regimes of one rule (Gray–Scott chaos vs mitosis) can coexist; `unique_anim_film.py`
plays the ten most distinct ones frame-by-frame (native colour — the motion is the star).

```bash
node tools/morphogenesis/anim_probe.mjs gsmito grayscott 200 900 6   # a time-filmstrip + motion score
GEN_OUT=/tmp/g_gschaos node tools/morphogenesis/gen.mjs grayscott 100 130 3 n 0.026 0.051 60
python3 tools/morphogenesis/unique_anim_film.py     # -> /tmp/web8_unique_animations.mp4
```

## Requirements
`node` (for the engine), `python3` with `numpy`, `Pillow`, `imageio_ffmpeg` (ffmpeg is bundled — no
system ffmpeg needed). The fonts live in `docs/web8/assets/fonts/`.

## Before any change, read these three lines
1. Stay in the **alive band**, seed **sparse**, step **slow** — or the field dies or sits still.
2. Scale camera pan to the **margin** and **ease** everything — or it jerks.
3. Differ on **all four axes** every time — path, palette, camera, theme.
