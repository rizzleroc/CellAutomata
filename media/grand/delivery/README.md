# The Grand Cross-Rule Search — full-spectrum discovery, rendered BIG

A single **universal** search ran across **all 17 rules** in the engine (not just Gray-Scott), at grid **140** ("more cells / bigger picture"). Every candidate was scored on its *own* native `render_rgb` with one rule-agnostic complexity metric:

> complexity = entropy x edge-density x structure x chroma x temporal-motion, weighted by coverage (how much of the frame is alive) and liveness (fraction of frames still changing).

**Searched 658 candidates** (16-way parallel, 0 errors); **569 alive**; **all 17 rules** represented. Champions were curated best-per-rule, then each rendered full-field at a large grid (up to **420 cells**).

## Champions (one per rule)

| # | hero file | rule | score | class | config |
|---|-----------|------|-------|-------|--------|
| 0 | `hero_00_luca.mp4` | LUCA | 0.903 | chaotic | mutation_rate=0.02, core_prevalence=0.5, seed_fraction=0.3 |
| 1 | `hero_01_s0-soup.mp4` | Primordial Soup | 0.898 | chaotic | amoeba_lifespan=40 |
| 2 | `hero_02_natural-selection.mp4` | Natural Selection | 0.897 | chaotic | defaults |
| 3 | `hero_03_rna-world.mp4` | RNA World | 0.894 | chaotic | error_rate=0.06, superiority=5 |
| 4 | `hero_04_genetic-code.mp4` | Genetic Code | 0.870 | chaotic | strand_mutation=0.08, code_mutation=0.02, seed_fraction=0.2 |
| 5 | `hero_05_coacervate.mp4` | Coacervates | 0.849 | chaotic | kappa=0.5, mean_composition=0.0, noise=0.3 |
| 6 | `hero_06_s3-vesicles.mp4` | Vesicles | 0.836 | chaotic | cmc_threshold=0.2, kappa_bend=0.015, F=0.025, k=0.055 |
| 7 | `hero_07_s4-selection.mp4` | Protocell Selection | 0.806 | chaotic | n_species=6, mutation_rate=0.005, dynamics=proxy |
| 8 | `hero_08_homochirality.mp4` | Homochirality | 0.758 | chaotic | k_auto=0.5, k_cross=3.0, noise=0.03 |
| 9 | `hero_09_wolfram1d.mp4` | Elementary CA | 0.641 | chaotic | rule_number=75 |
| 10 | `hero_10_conway.mp4` | Game of Life | 0.606 | chaotic | initial_density=0.55 |
| 11 | `hero_11_s1-grayscott.mp4` | Reaction-Diffusion | 0.579 | chaotic | F=0.038, k=0.063 |
| 12 | `hero_12_mineral-catalysis.mp4` | Mineral Catalysis | 0.559 | living | k_clay=0.15, clay_patches=16, feed=0.08 |
| 13 | `hero_13_pipeline-extended.mp4` | Extended Pipeline | 0.541 | chaotic | stage_duration=40 |
| 14 | `hero_14_hydrothermal-vent.mp4` | Hydrothermal Vent | 0.312 | living | vent_alkalinity=0.03, k_synth=6, decay=0.08 |
| 15 | `hero_15_s2-raf.mp4` | Autocatalytic Sets | 0.228 | living | n_species=8, n_reactions=16, food_fraction=0.3 |
| 16 | `hero_16_pipeline.mp4` | The Pipeline | 0.112 | chaotic | stage_duration=70 |

## Also in this folder
- `everything_wall.mp4` — all 17 champions animating at once (one tile per rule).
- `grand_reel.mp4` — a tour stitching every hero together.
- `grand_hero.gif` — looping preview of the top champion (LUCA).

## Reproduce
```
# 16-way search across all rules at grid 140
for i in $(seq 0 15); do PYTHONPATH=tools python3 tools/grand_search.py --worker $i/16 & done; wait
PYTHONPATH=tools python3 tools/grand_search.py --curate     # -> discovery/grand_top.json
PYTHONPATH=tools python3 tools/grand_search.py --wall        # everything wall
PYTHONPATH=tools python3 tools/grand_search.py --hero N      # one champion, big
PYTHONPATH=tools python3 tools/grand_search.py --assemble    # reel + gif
```
