# cellauto — the hero film

**`cellauto_hero.mp4`** — a ~70 s landscape (1920×1080, 30 fps) flagship film,
*"Catalytic Silence"*. Built for the website overture and as a social
centerpiece. Rendered by [`tools/hero_film.py`](../../tools/hero_film.py).

It walks the chemistry-to-life arc through **three visual registers**:

1. **The Search** — the everything-wall of all 17 engine rules and the
   thousands of simulations scored to find the most alive configurations
   (`media/grand/everything_wall.mp4`). The scale of the hunt.
2. **SEM** — live specimens rendered as a true instrument view: the `v`-field
   as a heightfield, normal-mapped + Blinn-Phong relit into a monochrome /
   warm-sepia micrograph, wrapped in "LIVE SEM FEED" chrome (scale bar,
   HV/WD/MAG microcopy). Per [`docs/PRD_SEM_VISUALIZATION.md`](../../docs/PRD_SEM_VISUALIZATION.md)
   — an electron-microscope look, **not** a viridis heat-map.
3. **Paintings** — the photoreal stage plates (`docs/generated/*.png`), the V1
   art layer. Light-studio cut-outs (vesicles, selection) are keyed onto the
   obsidian ground.

## Beats

| # | Beat | Register | Source | Citation |
|---|------|----------|--------|----------|
| 0 | Opening title | — | type card | — |
| 1 | **The Search** | search | `everything_wall.mp4` | 658 configs · grid 140 |
| 2 | Primordial Soup | painting | `stage0_soup` | Miller · Urey 1953 |
| 3 | **The First Division** | **SEM** | live Gray-Scott, relit | Turing 1952 · Pearson 1993 |
| 4 | The First Membranes | painting | `stage3_vesicles` (keyed) | Helfrich 1973 |
| 5 | Chemistry That Competes | **SEM** | live selection, relit | Eigen · Schuster 1977 |
| 6 | Chemistry Into Life | painting | `pipeline_poster` | cellauto MMXXVI |
| 7 | Closing title | — | type card | — |

## Render

```bash
python tools/hero_film.py            # full 1080p -> media/hero/cellauto_hero.mp4
python tools/hero_film.py --test     # fast, low-res pipeline check
```

The bundled imageio-ffmpeg has no `drawtext` (no freetype), so all titling is
Pillow, overlaid as full-frame RGBA. `sim_beat` freezes a sim if any single
step exceeds 1.5 s (stage-4 selection's cost explodes past ~550 steps at large
grids), so no rule can hang the render — the beat finishes on its last state.

## Narration (authored — synthesize + mux offline)

This container blocks huggingface.co, so VibeVoice weights can't be fetched
here (see `marketing/social/voiceover/generate_vibevoice.sh`). The narration is
written and timed to the beats; synthesize one WAV on a GPU/Colab box and mux:

> We searched. Seventeen rules, six thousand primordial soups, six hundred
> configurations of a reaction-diffusion equation — every one scored for how
> alive it looked, and the most alive were kept. This is what the instrument
> found. Before life, there was soup, seeded from the real yields of the 1953
> Miller-Urey experiment. Then four numbers begin to divide, like protocells.
> Membranes close around the chemistry. Bounded chemistry begins to compete,
> and to copy. From primordial soup to the last universal common ancestor —
> this is cellauto, watching chemistry remember how to become.

```bash
# 1) synthesize (where huggingface is reachable):  VibeVoice -> narration.wav
# 2) mux over the film, ducking the ambient bed:
ffmpeg -i media/hero/cellauto_hero.mp4 -i narration.wav -filter_complex \
  "[0:a]volume=0.45[bed];[1:a]adelay=6000|6000,loudnorm[vo];\
   [bed][vo]amix=inputs=2:duration=first[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -movflags +faststart \
  media/hero/cellauto_hero_voiced.mp4
```

## Outputs

- `cellauto_hero.mp4` — quality master (git-ignored; delivered as a `.zip`).
- `docs/hero_film.mp4` — web-optimized copy for the site overture.
