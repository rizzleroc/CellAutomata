# cellauto — the hero film

**`cellauto_hero.mp4`** — a ~66 s landscape (1920×1080, 30 fps) flagship film,
*"Catalytic Silence"*. Built for the website overture and as a social
centerpiece. Rendered by [`tools/hero_film.py`](../../tools/hero_film.py).

It walks the chemistry-to-life arc as a museum instrument: a **live**,
on-palette Gray-Scott hero beat (the four-parameter PDE that divides like a
protocell) intercut with live vesicle and selection sims and the photoreal
specimen plates, wrapped in the *Catalytic Silence* aesthetic — obsidian
ground, a teal → bone → magenta specimen ramp, hairline lower-thirds, corner
registration ticks, and a low ambient drone.

## Beats

| # | Beat | Source | Citation |
|---|------|--------|----------|
| 0 | Opening title — *an origin-of-life instrument* | type card | — |
| 1 | Primordial Soup | `stage0_soup` plate (Ken-Burns) | Miller · Urey 1953 |
| 2 | **The First Division** | **live Gray-Scott**, brand ramp | Turing 1952 · Pearson 1993 |
| 3 | The First Membranes | **live vesicles** sim | Helfrich 1973 |
| 4 | Chemistry That Competes | **live selection** sim | Eigen · Schuster 1977 |
| 5 | Chemistry Into Life | `pipeline_poster` panorama (pan) | cellauto MMXXVI |
| 6 | Closing title | type card | — |

## Render

```bash
python tools/hero_film.py            # full 1080p -> media/hero/cellauto_hero.mp4
python tools/hero_film.py --test     # fast, low-res pipeline check
```

The bundled imageio-ffmpeg has no `drawtext` (no freetype), so all titling is
rendered with Pillow and overlaid as full-frame RGBA. The two cutout specimen
plates (`stage3_vesicles`, `stage4_selection`) are white-studio shots, so those
beats are rendered as **live sims** through the brand ramp instead — keeping
every frame on the obsidian ground.

## Narration (authored — synthesize + mux offline)

This container blocks huggingface.co, so VibeVoice weights can't be fetched
here (see `marketing/social/voiceover/generate_vibevoice.sh`). The narration is
written and timed to the beats; synthesize one WAV on a GPU/Colab box and mux:

> What you're watching is cell division, with no biology at all. Just four
> numbers in a reaction-diffusion equation, splitting like living protocells.
> Before life, there was soup, seeded from the real yields of the 1953
> Miller-Urey experiment. Then the first membranes close around it. Chemistry
> begins to compete, and to copy. Twelve stages, one apparatus, from primordial
> soup to the last universal common ancestor. This is cellauto, watching
> chemistry remember how to become.

```bash
# 1) synthesize (where huggingface is reachable):
#    VibeVoice -> narration.wav   (voice: warm science-communicator)
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
