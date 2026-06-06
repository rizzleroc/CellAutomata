# CONTINUE — CellAutomata generative-art session

Working branch: `claude/cool-shannon-Sa9Tu` · PR #7 (draft, repo `rizzleroc/cellautomata`).
This file preserves session context + the plan for the next task so nothing is lost.

## What this session built (all in `tools/`)
Discovery / search:
- `discover.py`, `discover_complex.py` — Gray-Scott F/k sweeps scored for life-like / sustained complexity.
- `monkeys.py` — Conway random-soup methuselah search (fast numpy B3/S23, toroidal).
- `sustained.py` — longest continuous-change window search.
- `anim_hunt.py` — search + render best animated mandalas.
- `colony_hunt.py` — search 1000s of GS sims for creative FULL-FIELD colonies + "wall of colonies".
- `grand_search.py` — **NEW (this task)**: universal cross-rule search (see plan below).

Renderers / art:
- `make_progress_video.py` — espeak TTS + ambient_bed helpers (reused everywhere).
- `showcase.py`, `showcase_complex.py`, `showcase_winners.py` — complex-reaction reels.
- `deep_time.py` + `render_deeptime.py` — accelerate to 100k "days", DAY counter.
- `mandala.py`, `mandala_morph.py`, `mandala_film.py`, `mandala_hires.py`, `mandala_x.py` — kaleidoscope mandalas (compound + multi-octave fractal folds, 4K, films).
- `beauty_loop.py`, `beauty_ultra.py` — seamless 4K crystal-journey loops.
- `relit.py`, `relit_mandala.py` — normal-map 3D relighting (molten gold/jade/ice).
- `life_reel.py`, `concepts.py` — microscopy life reels; brainstorm concepts.
- `explainer.py` — 64s explainer (square + vertical).
- `series.py` + `series_scripts.py` — the **10-part explainer series** (data-driven).
- `spectrum.py` — "Full Spectrum" grand tour of ALL 17 visualizations.

Media lives in `media/`, `media/series/`, `media/colonies/`. Manifests in `discovery/*_top.json`.

## Hard-won conventions & gotchas (DO NOT relearn these)
- **ffmpeg**: only the bundled one — `imageio_ffmpeg.get_ffmpeg_exe()`. It has **no `drawtext`** (no freetype) → render all text with **Pillow**, overlay PNGs, or `pad`. Has libx264 + aac.
- **TTS**: `espeak-ng` (offline, robotic). gTTS is network-blocked. No better local TTS.
- **Engine API**: `Engine(width,height,rule=REGISTRY[name](**cfg),seed=s)`; `eng.step()`; field rules expose `eng.state.v`/`.u`; **`rule.render_rgb(eng.state)` returns RGB uint8 and works for ALL 17 rules** (universal footage path).
- **Gray-Scott**: scatter-seed ~`grid//11` patches (u=0.5,v=0.25) to FILL the field; central seed for `preset=mitosis` (it thrives, scatter kills it). For mandala loops, FREEZE the field at its intricate state + rotate (live RD drifts to a solid disk = the recurring bug).
- **Delivery**: the user's chat **cannot download `.mp4`** → always package as **`.zip`** (store, `zip -0`). **Each download must be < 25 MB** → re-encode heavy/noisy parts (CRF 27–31) and/or bin-pack. The true-4K masters are gitignored (>100 MB) and delivered as split `.zip` parts (`copy /b` / 7-Zip to reassemble; verify md5).
- **gitignore**: `discovery/*/`, `*.zip`, big masters. Catalogs: `media/series/README.md`, `MEDIA_INDEX` etc.
- **whipgen MCP (flaky)**: daemon wedges intermittently; **ChatGPT provider hangs the whole daemon** ("Node is detached") — NEVER include it. Reliable: **claude + kimi via `whipgen_fanout`, gemini via `whipgen_chat_text`**. Always `async:true` + poll `whipgen_fanout_status`/`whipgen_job_status` (60s MCP call ceiling). `whipgen_help`/`whipgen_health` are in-process. Reconnect/auth is a user-side action.
- **Accurate rule/param reference** lives in `tools/series_scripts.py` + Part-by-part TRY-IT cards (grounded in code + literature: Miller, Turing, Pearson, Kauffman, Helfrich, Eigen-Schuster, Lane-Martin, Ferris, Frank, Gilbert, Vetsigian-Woese, Cahn-Hilliard, Weiss, Wolfram/Cook).

## The 17 rules (REGISTRY) + key tunables (for searching "across all of it")
- `wolfram1d` — `rule_number` 0–255 (discrete; 30 chaos / 90 fractal / 110 universal).
- `conway` — `initial_density` (0.35), `wrap` (true) (discrete).
- `abiogenesis-stage0-soup` (=`natural-selection`) — `amoeba_lifespan` (25), species weights (discrete).
- `abiogenesis-stage1-grayscott` — `preset`/`F`/`k`/`Du`/`Dv` (field). Presets: spots(.035,.065) stripes(.04,.06) mitosis(.0367,.0649) waves(.014,.045) labyrinth(.039,.058).
- `abiogenesis-stage2-raf` — `n_species`(8) `n_reactions`(16) `food_fraction`(.4) `diffusion_rate`(.05).
- `abiogenesis-stage3-vesicles` — `amphiphile` `cmc_threshold`(.3) `kappa_bend`(.025) F/k.
- `abiogenesis-stage4-selection` — `n_species`(4) `mutation_rate`(.02) `dynamics` F/k (error catastrophe past 1/n).
- `abiogenesis-rna-world` — `seq_length`(16) `error_rate`(.02) `superiority`(10) (catastrophe past ln(σ)/L).
- `abiogenesis-homochirality` — `k_auto`(1) `k_cross`(2) `feed`(.1).
- `abiogenesis-hydrothermal-vent` — `vent_alkalinity`(.05) `ocean_acidity`(.95) `k_synth`(6).
- `abiogenesis-coacervate` — `kappa`(.3) `mobility`(.8) `mean_composition`(-.4).
- `abiogenesis-mineral-catalysis` — `k_clay`(.25) `k_bulk`(.002) `clay_patches`(9).
- `abiogenesis-genetic-code` — `seq_length`(16) `mutation_rate`(.01) `code_swap_rate`(1e-4).
- `abiogenesis-luca` — `n_genes`(16) `per_gene_mutation`(.01).
- `abiogenesis-pipeline` / `-extended` — `starting_stage` `stage_duration` `auto_promote` / `--stage`.

## PLAN — "full simulations across ALL of it, more cells / bigger picture"
Goal: stop focusing only on the Gray-Scott field; run a **universal cross-rule discovery search** at **larger grids**, find the most striking finds across EVERY rule, then render them BIG.

1. **`tools/grand_search.py`** (universal, rule-agnostic):
   - Scores on the **rendered RGB** (luminance) so it works for any rule: complexity = histogram-entropy × edge-density × structure(std) × temporal-motion, with a flatness/dead penalty.
   - **Candidate space across all rules**: Wolfram (curated interesting rule_numbers), Gray-Scott (F/k grid + seeds), Conway (densities + seeds), and a parameter sweep per abiogenesis stage (raf, rna, chirality, vent, coacervate, minerals, selection, genetic-code, luca, vesicles, soup) × seeds. ~1500–2500 candidates.
   - **Bigger grid**: search at grid ≈ 140 (vs 80 before) for a bigger picture; early-exit dead runs.
   - 16-way parallel shards → `discovery/grand/g_NN.jsonl`.
2. **Curate**: best-per-rule + global top, deduped, diverse → `discovery/grand_top.json`.
3. **Render BIG** (`grand_search.py --render`): each champion at a **large grid (≈ 320–420 cells)** as a full-field animation (native render_rgb), plus an **"everything wall"** montage (one champion per rule) + reel + GIF — all zoomed out, < 25 MB bundles.

Status when this file was written: grand_search built + 16-way search launching. Next: curate + big-grid render + deliver.
