# Changelog

All notable changes to cellauto are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added — browser sandbox

- **`cellauto web` subcommand.** A Flask server (`cellauto/web/server.py`)
  wraps the existing `Engine` and exposes every rule in the registry over a
  small JSON API; a single-page vanilla-JS frontend (`cellauto/web/static/`)
  drives it. Rule picker, grid size, seed input, play/pause/step, speed
  slider, per-rule tutorial copy, live population stats — same engine the
  desktop GUI uses, no Pyodide, no per-rule reimplementation. Frames are
  rendered server-side via each rule's existing `render_rgb` and shipped
  as PNGs. Flask is opt-in: `pip install -e ".[web]"`.

---

## [3.4.0] — 2026-05-23

The "closing the honest gaps" release. The v3.2/v3.3 cycles fixed correctness
and built out the *qualitative* coverage of the origin-of-life story; this
release closes the remaining science gaps the honest assessment had flagged
as loop-iteration-sized.

### Added — closing the science gaps
- **Genetic-code emergence stage** (`abiogenesis-genetic-code`). Each cell
  carries an RNA-like strand *and* its own private codon→amino-acid table;
  both mutate; fitness is peptide match against a target catalyst.
  Selection on the code itself drives convergence toward a shared universal
  code — the Vetsigian-Woese-Goldenfeld (2006) coevolution mechanism, the
  conceptual hand-off from chemistry to biology.
- **LUCA distillation stage** (`abiogenesis-luca`). A spatial population of
  evolving cells with gene-presence bitsets; selection on a benefit-vs-cost
  gene economy distills a shared core genome = the inferred Last Universal
  Common Ancestor (Weiss et al. 2016 methodology, threshold-relaxed at 70%
  prevalence to handle non-zero mutation). `luca_size` converges to the
  essential-gene count.
- The auto-promoting **extended pipeline now spans 12 stages**:
  soup → vent → reaction-diffusion → mineral catalysis → autocatalytic sets →
  homochirality → RNA world → genetic code → coacervates → vesicles →
  protocell selection → LUCA distillation.
- **Real thermodynamic readouts in the vent stage.** The abstract proton
  field maps to actual pH via configurable `pH_alkaline` / `pH_acidic`
  (defaults 10.0 / 5.5 — Krissansen-Totton et al. 2018 early-Earth ocean
  estimate). The population dict now reports **ΔpH** (×10), **PMF in mV**
  (Nernst factor 2.303 RT/F ≈ 59.16 mV/pH unit at 25 °C; default ≈ 266 mV),
  and **ΔG in kJ/mol per proton** (Faraday × PMF; default ≈ −25.7) — exactly
  the Lane-Martin range for driving abiotic carbon fixation.
- **Wood-Ljungdahl carbon-fixation chemistry in the vent stage.** VentState
  gained `h2` and `co2` arrays; H₂ is replenished inside the alkaline
  chimney by serpentinisation, CO₂ is fed globally to model the CO₂-rich
  Hadean ocean (Krissansen-Totton 2018). Synthesis rate = mass-action
  `k_synth × PMF × [H₂] × [CO₂]` capped by the 2:1 stoichiometry of
  `2 CO₂ + 4 H₂ → acetate + 2 H₂O` (ΔG° = −95 kJ/mol). Tests prove the
  stoichiometric constraint: cutting H₂ *or* CO₂ kills the yield even when
  PMF stays at 266 mV.
- **Real-molecule labels** at the code level: `RNA_BASES = (A, U, G, C)`
  in `stage_rna.py`; `CODON_BASES` + `AMINO_ACIDS = (Gly, Ala, Asp, Val)`
  in `stage_code.py` (Ikehara 2002 GADV proto-code); `MONOMER_LABEL` /
  `POLYMER_LABEL` / `MINERAL_LABEL` in `stage_minerals.py` (Ferris 1996
  ImpA + Na-montmorillonite); `LUCA_GENE_NAMES` in `stage_luca.py` —
  16 well-attested LUCA-core gene families (rpoB, rpsC, rplB, fdhA, codhC,
  mrpA, atpA, hypE, nifH, gltB, dnaK, trpB, oxyR, gyrB, photolyase, mutS)
  aligned with the essential / accessory / deleterious gene-value tiers.
- **Web port MVP** at `docs/web/` — a single static page with a live JS
  port of the Gray-Scott PDE (Stage 1) running on an HTMLCanvas, F/k
  sliders, the five Pearson presets, and the Catalytic Silence palette.
  Vanilla JS, ~400 lines total, no Pyodide, deployable to GitHub Pages
  from `/docs`. Other stages exhibited as the existing static plate
  gallery (`docs/generated/*.png`).
- **AAA release poster** rendered via the whipgen MCP
  (`docs/generated/release_poster_v3_4_mcp.png`) and the deterministic PIL
  version (`docs/generated/release_poster_v3_4.png`) — 4×3 specimen grid of
  the 12 origin-of-life stages, Italiana + CrimsonPro + IBM Plex Mono
  typography, obsidian + bone + hairline-teal palette. Reproducible via
  `tools/render_release_poster.py`.
- **Six new pytest files** covering the new behaviour:
  `test_genetic_code.py`, `test_luca.py`, and additional vent / Wood-
  Ljungdahl assertions in `test_vents.py`. Test count: 95 → **120 (+25)**.

### Fixed — CI cleanup
- **mypy clean across the package**. Closed 24 type errors: name collision
  in `mascot.py` between the right-pupil canvas ID and the pupil-radius
  variable (renamed the radius to `_eye_pupil_r`); canvas-ID Optional
  fields narrowed to `int` with a `-1` sentinel; `Image.NEAREST` →
  `Image.Resampling.NEAREST` (Pillow ≥10); `_renderer` typed as the proper
  union; `_section` return type; font tuples normalised to 3-element
  `(family, size, style)` for the `create_text` overload; `Label.image` GC
  pin annotated; lambda-default `# type: ignore[misc]` where the idiom
  defeats inference; `create_text` anchor-Literal narrowed by unrolling a
  2-iteration loop.
- **Coverage gate fixed and lifted**: `pyproject.toml` now carries
  `[tool.coverage.run]` omitting the Tk-display-dependent modules (`app`,
  `mascot`, `__main__`, `renderer`). Coverage went **47 % → 87 %**, well
  above the 80 % floor the CI enforces.
- **Sim too fast / chapter titles sticking around**: `_animate` now ticks
  the chapter-card fade timer *before* any code that could raise a
  transient TclError, so a card can't get pinned indefinitely. RESEED /
  RESTART explicitly clear the card. **Escape dismisses an active card.**
  Default FPS lowered 8 → 5; extended pipeline `stage_duration` raised
  50 → 90 so transitions don't blow past the card; header subtitle no
  longer says "five observations" on a 12-stage pipeline.

### Changed
- Version bumped to `3.4.0` in `pyproject.toml` and `cellauto/__init__.py`.

---

## [3.3.0] — 2026-05-22

### Added
- **Extended 10-stage pipeline** (`abiogenesis-pipeline-extended`) — auto-promotes
  through every shipped origin-of-life process in scientific order: soup →
  alkaline vent → reaction-diffusion → mineral catalysis → autocatalytic sets →
  homochirality → RNA world → coacervates → vesicles → protocell selection.
  `AbiogenesisPipelineRule` was parameterised with `stage_classes`/`stage_infos`
  fields so the original 5-stage rule keeps its identical default behaviour.
- **Story-mode chapter transition cards.** When the pipeline promotes, a
  centred overlay shows "CHAPTER N · TITLE", the governing principle, and the
  citations; fades after ~4.5 s via the animate-tick countdown.
- **Per-protocell inspector.** Click any Stage 4 disc to open a Toplevel
  showing the protocell's position, radius, age, fitness, and full genome
  vector, plus a caption explaining the hypercycle-coupling fitness. Works
  for the direct stage rule and the pipeline-wrapped case.
- **Timeline scrubber.** Bounded ring buffer (cap 120) snapshots
  `engine.rule.serialize_state(...)` every step; the `SCRUB` Scale in
  TRANSPORT restores any captured frame. Stepping after scrub-back truncates
  the future so timelines branch rather than overwriting.
- **Text-scaling control** (`View ▸ Small/Default/Large/Extra-large text`) —
  `_apply_font_scale` recomputes every font tuple and re-applies the ttk
  styles uniformly; canvas overlays refresh on the same tick. Clamped
  `[0.6, 2.0]`.
- **Colour-blind-safe palette toggle** (`View ▸ Colour-blind safe palette`) —
  swaps Stage 4's red→green disc colour (the audit's flagged CVD offender)
  for a Wong blue→yellow ramp; the legend bar follows. Other diverging maps
  (chirality teal↔magenta, vents blue↔orange, viridis) are already CVD-friendly.
- **Keyboard navigation** — Space (play/pause), → (step), R (restart),
  P (promote), `[` / `]` (previous / next pipeline stage), all guarded
  against text-entry focus so Spinbox/Combobox editing isn't hijacked.
  New `Help ▸ Keyboard shortcuts…` dialog lists every binding.
- New tests: `test_extended_pipeline.py` (10-stage init / auto-promote /
  set_stage / registration); test count 95 → **102**.

### Changed
- Live stage caption on the canvas now shows the **live `current_stage`**
  rather than the StageInfo's own `index`, so the extended pipeline's labels
  match the position the JUMP combobox reads.
- JUMP combobox values now size dynamically from `len(rule.stage_classes)`,
  so the 5-stage and 10-stage pipelines both work without hardcoding.
- Version bumped to `3.3.0` in `pyproject.toml` and `cellauto/__init__.py`.

---

## [3.2.0] — 2026-05-22

### Added — research-backed origin-of-life simulator
- **Six new origin-of-life processes** (each a selectable rule with its own
  sliders, tests, tutorial, and `docs/science.md` section):
  - `abiogenesis-rna-world` — spatial Eigen quasispecies (Gilbert 1986;
    Eigen 1971). Watch the master sequence dissolve into the error
    catastrophe when the per-base error rate crosses `ε_c = ln(σ)/L`.
  - `abiogenesis-homochirality` — Frank (1953) autocatalysis + mutual
    antagonism. Tiny fluctuations break mirror symmetry into teal/magenta
    chiral domains.
  - `abiogenesis-hydrothermal-vent` — proton/pH gradient across a chimney
    wall drives organic synthesis (Russell & Hall 1997; Lane & Martin 2012).
    Flatten the gradient and synthesis stops entirely.
  - `abiogenesis-coacervate` — Cahn-Hilliard liquid-liquid phase separation
    (Oparin 1924; Banani et al. 2017). Gold droplets nucleate and coarsen
    (Ostwald ripening), a membraneless counterpart to Stage 3's vesicles.
  - `abiogenesis-mineral-catalysis` — montmorillonite clay mask (Ferris 1996;
    Cairns-Smith 1982). Polymer accumulates on the clay surface at ~12× the
    bulk-water rate; equalising the rates removes the localisation.
- **AAA visual identity.** Six "Catalytic Silence" stage plates generated via
  the whipgen MCP and wired into the Gallery menu
  (`docs/generated/stage{0..4}_*.png` + `pipeline_poster.png`).
- **`cellauto/netviz.py`** — PIL-rendered Stage 2 reaction network with the
  Hordijk-Steel RAF highlighted (teal edges, magenta catalyst links, amber
  food species). Accessible via `Gallery ▸ Reaction network (Stage 2 RAF)`.
- **Live scientific-parameter controls** (`cellauto/rules/params.py`) —
  every rule's dataclass knobs are exposed as live GUI sliders that take
  effect on the next step. Includes the Stage 1 Pearson preset picker and
  structural sliders (Stage 2 species/reaction counts + food fraction,
  Wolfram rule number) that auto-reinit deterministically on change.
- **Stage caption + colour legend on the canvas.** Drawn as zero-layout
  overlays (`_sync_stage_caption`, `_draw_legend_bar`) — the stage title +
  legend, an on-canvas viridis colorbar (red→green for Stage 4 fitness;
  diverging variants for chirality, vents, coacervates, minerals).
- **Live population time-series sparkline** under the canvas (zero layout).
- **Mandated UI toolset** (full checklist in `docs/ROADMAP.md §2`):
  - `JUMP` combobox for direct pipeline stage navigation.
  - `AUTO-PROMOTE` checkbox + `DUR` spinbox.
  - `RESET` parameter defaults; `RESTART`-to-step-0 preserving slider edits.
  - `File ▸ Export frame as PNG…`; `File ▸ Export stats as CSV…`.
- **`docs/ROADMAP.md`** — feature inventory + punchlist + mandated UI toolset
  contract (groups A-G).
- Test count 66 → 95 across `test_realdata.py`, `test_rna_world.py`,
  `test_homochirality.py`, `test_vents.py`, `test_coacervate.py`,
  `test_minerals.py`, `test_netviz.py`, `test_stage2_roundtrip.py`.

### Fixed — scientific correctness
- **`find_raf` rewritten to the real Hordijk-Steel layered closure.** The
  v3.1 one-pass implementation collapsed the inner closure into a single
  non-iterative step that declared every candidate's product producible
  unconditionally — reporting **false-positive RAFs**. The rewrite uses the
  formal Algorithms 1 + 2 from Hordijk (2023) arXiv:2303.01809: a
  food-generated closure that only adds a reaction's product once both
  reactants are producible, wrapped in an outer prune-and-recompute loop.
- **Catalysis is now mandatory** for RAF-viability — the "R" in RAF requires
  it. `_viable` rejects any reaction with `catalyst is None`. `random_reaction_network`
  now catalyses every reaction (previously left ~50% uncatalysed → dead weight).
- **Stage 2 serialises its full reaction network.** Previously
  `deserialize_state` fabricated a fresh random network on load, so resumed
  runs evolved under a different chemistry than the one that produced the
  saved field. The network is now part of the snapshot.
- Stage 4 hypercycle docstring softened from "simulates the hypercycle" to
  "fitness proxy" — the implementation does not integrate the Eigen-Schuster
  ODE. Gray-Scott CFL bound now documented; mitosis preset harmonised
  between `science.py` and `docs/science.md`.

### Changed — toy → real data
- **Stage 0 soup** is sampled weighted by Miller's 1953 measured yields
  (formic acid ≈ 49 %, glycine ≈ 13 %, glycolic acid ≈ 12 %, alanine ≈ 7 %)
  via `MILLER_UREY_SPECIES` — a real soup is *not* a uniform rainbow.
- **Stage 3 vesicles** carry a named amphiphile; `AMPHIPHILE_CMC_MM` lists
  measured CMCs (decanoic acid C10 ≈ 85 mM, oleic ≈ 0.1 mM, …) from the
  Szostak/Deamer protocell literature. The population dict reports `cmc_mM`.
- **Stage 4** exposes the Eigen quasispecies error threshold `1/L` as
  `error_threshold_x1000` alongside `mutation_rate_x1000`, so crossing it
  is observable.
- **Stage 2** reports Kauffman's catalysis connectivity
  `catalysis_level_x100 = n_reactions / n_species` — the metric the threshold
  bounds (~1-2 per species per Hordijk-Steel polymer-model results).
- The whole repo brought to `ruff check` + `ruff format --check` clean; dev
  visual-audit screenshots and the local MCP config moved into `.gitignore`.

---

## [3.1.0] — 2026-05-20

### Added
- **Catalytic Silence visual pass for the GUI.** The cards-and-filled-buttons
  dark theme was replaced with the museum-plate aesthetic the Prima Materia
  plate is built from:
  - Bundled `Italiana-Regular`, `CrimsonPro-Italic`, `CrimsonPro-Regular`,
    `IBMPlexMono-Regular`, and `IBMPlexMono-Bold` into
    `cellauto/assets/fonts/`. `_register_bundled_fonts()` registers them on
    Windows via `gdi32.AddFontResourceExW` (`FR_PRIVATE`) so they're visible
    to Tk for this process. Non-Windows falls back through Constantia /
    Cambria / Georgia / Cascadia Mono.
  - New palette: obsidian `#0a0e16`, warm bone `#e6e0d0`, desaturated-teal
    hairlines `#1f4f4c`, accent teal `#39d4c8`, magenta only on record,
    restrained brick only on stop.
  - LabelFrame cards removed. Sections are now Italiana Roman-numeral +
    tracked-mono labels (`I · OBSERVATION`, `II · CONFIGURATION`,
    `III · TRANSPORT`, `IV · REGISTER`, `V · MARGINALIA`) with thin teal
    hairlines beneath.
  - Outlined museum-card buttons (border-only, no fill) — `Primary` (teal
    Play), `Danger` (brick Stop), `Record` (magenta).
  - About dialog and GIF-export progress dialog rebuilt in the same voice
    (eyebrow / Italiana title / italic caption / hairline rule).
  - `[tool.setuptools.package-data]` now includes `assets/fonts/*.ttf`.
- **Stable window geometry.** The 1990-era reflow on every iteration is
  fixed: locked **720×1000** window, `resizable(False, False)`, tutorial
  is an always-present caption (no `pack_forget`), status uses a
  fixed-width monospace grid.
- **Prima Materia plate.** A museum-style observational plate
  ([`docs/prima-materia.png`](docs/prima-materia.png)) composed from real
  cellauto simulations under the **Catalytic Silence** design philosophy
  ([`docs/design/catalytic-silence.md`](docs/design/catalytic-silence.md)).
  Hero specimen: Stage 1 Gray-Scott at step 600 with the canonical Pearson
  "spots" pattern. Four supporting specimens: Stages 0, 2, 3, 4. Typography
  set in Italiana (display), CrimsonPro Italic (caption), and IBM Plex Mono
  (apparatus). Reproducible via
  [`docs/design/render_prima_materia.py`](docs/design/render_prima_materia.py).
- **AAA visual identity.** Three new commissioned assets generated via the
  whipgen MCP pipeline:
  - [`docs/hero.png`](docs/hero.png) — cinematic close-up of Gray-Scott
    self-replicating spots (replaces the prior step-400 screenshot).
  - [`docs/pipeline.png`](docs/pipeline.png) — five-panel infographic strip
    showing the abiogenesis pipeline left → right.
  - [`docs/icon.png`](docs/icon.png) / `cellauto/assets/icon.png` — modern
    app icon (protocell mid-division), shipped as package data.
- **Tk window icon.** `App._apply_window_icon()` loads
  `cellauto/assets/icon.png` and applies it via `iconphoto(True, …)`, so
  every Toplevel (incl. the new GIF-export progress dialog) inherits it.
- **About dialog redesign.** Replaces the bare `messagebox.showinfo` with a
  proper `Toplevel` that displays the icon, version, and pipeline summary.
- `[tool.setuptools.package-data]` entry so `assets/icon.png` ships in the
  installed wheel.

### Fixed
- **GIF export no longer freezes the GUI.** Export now captures frames one at a
  time via non-blocking `after()` callbacks, showing a modal progress bar with a
  Cancel button; the final Pillow rendering runs in a background thread.
- **Stage 4 fitness function replaced.** Shannon-entropy × concentration
  (acknowledged placeholder in PHASE2_BRUTAL §29) is replaced with the
  Eigen-Schuster hypercycle coupling: `Σ g[i]·g[(i+1)%n]`. This is zero when
  any species is absent and maximised at equal concentrations — the
  cooperatively stable state from Eigen & Schuster (1977). Growth/shrink
  threshold and colour scale updated to match the new units.
- `avg_fitness_x100` stat renamed `avg_fitness_x1000` to reflect the new
  (smaller) hypercycle scale.

### Changed
- **CI matrix now includes Windows.** `windows-latest` added alongside
  `ubuntu-latest`; `fail-fast: false` so one OS failure doesn't cancel the other.
- **CI: concurrency group cancels in-progress runs** on new push to the same ref.
- **CI: `ruff format --check`** added (was only `ruff check`).
- **CI: `mypy --ignore-missing-imports`** added as a type-check gate.
- **CI: `--cov-fail-under=80`** coverage threshold enforced.
- **CI: `cellauto export` smoke test** added (GIF export path now covered in CI).
- **CI: `pip-audit` security job** added for dependency vulnerability scanning.
- `mypy>=1.10` added to `[project.optional-dependencies] dev`.
- Version bumped to `3.1.0` in `pyproject.toml` and `cellauto/__init__.py`.

---

## [3.0.0] — 2026-05-19

### Added
- **Abiogenesis pipeline** — 5-stage chemistry-to-life simulation with citations:
  - Stage 0: primordial soup (Oparin/Haldane, Miller-Urey)
  - Stage 1: Gray-Scott reaction-diffusion (Turing 1952, Pearson 1993) — hero result
  - Stage 2: Kauffman RAF autocatalytic sets (Hordijk & Steel 2004)
  - Stage 3: lipid bilayer self-assembly (Helfrich, Deamer, Szostak)
  - Stage 4: protocell selection / hypercycle (Eigen & Schuster 1977-79)
- `abiogenesis-pipeline` rule: orchestrator that auto-promotes through all stages.
- `FieldRenderer`: numpy → `tk.PhotoImage` PPM blit — **7.4× faster** than
  `DiscreteRenderer` at 80×80, runs 200×200 in 0.08 s.
- `DiscreteRenderer`: tracks `(item_id, shape)` in `_items` — eliminates the
  per-cell `canvas.type()` Tk roundtrip that made v2.0 0.74× *slower* than v1.
- Per-rule tutorials: `tutorial_for(rule_name)` returns rule-specific walkthrough text.
- `Rule.to_config()` / `from_config()` protocol: rule parameters round-trip through
  snapshots.
- RNG state serialized via `pickle+base64` in snapshots — `Engine.load` + continue
  now matches a continuous run bit-for-bit.
- `docs/science.md` — full citation list and math for all 5 stages.
- 49 pytest tests (was 14); full coverage of abiogenesis stages.

### Fixed
- **F3 — Rule 3 `is_new` is no longer a no-op.** `is_new` reset to `False` at
  start of each step; only cells whose colour genuinely changed become `True`.
  `settled` count in the status bar is now reachable.
- **`_distinct_palette_color` crash on a 1-element palette** — validated in
  `__post_init__`.
- Wolfram1D stats: `population()` now returns `live_now`, `history_on`,
  `history_off` separately, not a misleading total-history count.
- `Rule.init_grid(grid)` replaces the `isinstance(rule, Wolfram1DRule)` branch in
  `Engine.__post_init__` (Protocol leak closed).
- `tests/test_protocol.py` asserts `isinstance(rule, Rule)` for every registered
  rule — the `@runtime_checkable` contract is now verified.

### Changed
- Project reframed from "natural-selection simulator" to **abiogenesis** (the
  project's true premise). Legacy `natural-selection` kept as alias of Stage 0.
- README rewritten: honest perf table, abiogenesis-first framing, history section.
- `requirements.txt` now single-sources from `pyproject.toml` (`pip install -e .`
  is the canonical install path).

---

## [2.0.0] — 2026-05-18

### Added
- Pluggable rule engine with `Rule` protocol.
- Conway's Game of Life (`conway`) and Wolfram 1D elementary automata (`wolfram1d`).
- Headless CLI: `cellauto simulate`, `cellauto export`.
- GIF export via Pillow.
- Save / load snapshots (JSON).
- GitHub Actions CI (Ubuntu, Python 3.10–3.12).
- 14 pytest tests.

### Known issues (closed in v3.0)
- Rule 3 `is_new` was still a no-op.
- Rendering was benchmarked as 0.74× (i.e. *slower* than v1) despite the "10×
  faster" README claim.
- `Engine.load` re-seeded the RNG from scratch, breaking the determinism guarantee.
- Rule config not serialised in snapshots.

---

## [1.0.0] — 2024-03

### Added
- Initial sketch: four rules described as "natural selection."
- Tkinter GUI with canvas rendering.

### Known issues (closed in v2.0 / v3.0)
- Rules F1–F4 not mechanically implemented.
- Zero tests, no CI, no packaging.
