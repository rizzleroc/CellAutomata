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

## Requirements
`node` (for the engine), `python3` with `numpy`, `Pillow`, `imageio_ffmpeg` (ffmpeg is bundled — no
system ffmpeg needed). The fonts live in `docs/web8/assets/fonts/`.

## Before any change, read these three lines
1. Stay in the **alive band**, seed **sparse**, step **slow** — or the field dies or sits still.
2. Scale camera pan to the **margin** and **ease** everything — or it jerks.
3. Differ on **all four axes** every time — path, palette, camera, theme.
