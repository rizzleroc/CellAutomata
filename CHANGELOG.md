# Changelog

All notable changes to cellauto are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
