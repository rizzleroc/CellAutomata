# tools/morphogenesis — vertical reaction–diffusion reels

Production scripts for the web8 "morphogenesis" social videos.
**Full playbook + lessons learned: [`docs/web8/SOCIAL_MEDIA_HANDOFF.md`](../../docs/web8/SOCIAL_MEDIA_HANDOFF.md).**

## Pipeline
Two stages per reel: a Node **generator** dumps the simulation height field to a flat binary, then a
Python **compositor** crops/relief-shades/captions it and encodes 1080×1920 H.264 + ambient audio.

```
<x>_gen.mjs  →  /tmp/<x>_field.bin + /tmp/<x>_meta.json  →  <x>_film.py  →  /tmp/web8_<x>.mp4
```

Run from the **repo root** (the generators read `docs/web8/experiment/**` by relative path):

```bash
# one reel:
node tools/morphogenesis/void_gen.mjs && python3 tools/morphogenesis/void_film.py

# a whole batch, unattended (survives session drop):
nohup bash tools/morphogenesis/run_batch.sh void forge cryst > /tmp/batch_main.log 2>&1 &
```

## Reels
| stem    | look | output |
|---------|------|--------|
| `lo`    | warm-bone odyssey, 12-waypoint full tour | `web8_morphogenesis.mp4` |
| `void`  | dark voids in a luminous field (inverted), slow pull-back | `web8_void.mp4` |
| `forge` | magma/volcanic chaos, energetic eased camera | `web8_forge.mp4` |
| `cryst` | ice-crystal mineral growth, deep zoom-in, high relief | `web8_crystallogenesis.mp4` |
| `mito_switch_big` | live "flip the switch" rule change | `web8_mitosis_switch_1000.mp4` |

`gen.mjs` is a generic single-rule generator:
`node gen.mjs <ruleid> <warmup> <frames> <steps> <modes> [F] [k] [scatterN]`.

## Requirements
`node` (for the engine), `python3` with `numpy`, `Pillow`, `imageio_ffmpeg` (ffmpeg is bundled — no
system ffmpeg needed).

## Before any change, read these three lines
1. Stay in the **alive band**, seed **sparse**, step **slow** — or the field dies or sits still.
2. Scale camera pan to the **margin** and **ease** everything — or it jerks.
3. Differ on **all four axes** every time — path, palette, camera, theme.
