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

Each compositor honours three modes so you can preview before a full encode (HANDOFF Lesson 8):

```bash
python3 tools/morphogenesis/terra_film.py test  470   # the live window only  → /tmp/terra_test.png
python3 tools/morphogenesis/terra_film.py testc 470   # window + chrome       → /tmp/terra_testc.png
python3 tools/morphogenesis/terra_film.py             # full render           → /tmp/web8_terra.mp4
```

Generators accept `MORPH_NF` to shrink the frame count for smoke tests:
`MORPH_NF=600 node tools/morphogenesis/terra_gen.mjs`.

## Requirements
`node` (for the engine), `python3` with `numpy`, `Pillow`, `imageio_ffmpeg` (ffmpeg is bundled — no
system ffmpeg needed). The fonts live in `docs/web8/assets/fonts/`.

## Before any change, read these three lines
1. Stay in the **alive band**, seed **sparse**, step **slow** — or the field dies or sits still.
2. Scale camera pan to the **margin** and **ease** everything — or it jerks.
3. Differ on **all four axes** every time — path, palette, camera, theme.
