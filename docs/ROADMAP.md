# cellauto — Feature Inventory, Punchlist & Roadmap

This document is the project's **regression guard**. Before shipping any
change, check it against the Feature Inventory: nothing listed there should
silently disappear. The Punchlist tracks the current work cycle; the Roadmap
captures what's deliberately deferred.

Last updated: 2026-05-22.

---

## 1. Feature Inventory (must not regress)

Every feature below is implemented and expected to keep working. A change that
removes or breaks one of these is a regression, not a simplification.

### Simulation science
- **Five abiogenesis stages**, each an independently runnable rule:
  - Stage 0 — primordial soup (discrete four-rule mixing/condensation).
  - Stage 1 — Gray-Scott reaction-diffusion (forward-Euler, 5-pt Laplacian, CFL-stable).
  - Stage 2 — Kauffman autocatalytic sets via the **correct Hordijk-Steel RAF closure** (layered food-generated closure; catalysis mandatory).
  - Stage 3 — lipid vesicle self-assembly (CMC threshold + connected-component vesicle counting).
  - Stage 4 — protocell selection (hypercycle-flavoured fitness, growth/division/death, mutation).
- **Pipeline rule** (`abiogenesis-pipeline`) — walks all five stages end-to-end with auto-promotion.
- **Reference automata**: Conway's Game of Life, Wolfram 1D (rules 0–255).
- **Legacy alias** `natural-selection` → Stage 0 (kept for old snapshots/CLI).
- **Real published data** backing the constants:
  - Stage 0 soup sampled by **Miller's 1953 measured product yields** (`MILLER_UREY_SPECIES`).
  - Stage 3 named fatty acid + **measured CMCs** (`AMPHIPHILE_CMC_MM`: decanoic C10 ≈ 85 mM, etc.).
  - Stage 2 reports **Kauffman catalysis level** (n_reactions/n_species).
  - Stage 4 exposes **Eigen error threshold** (≈ 1/L) + mutation-rate stat.
  - Gray-Scott Du:Dv grounded against real ~10⁻⁹ m²/s diffusion coefficients (docs).

### Engine & reproducibility
- Deterministic from `--seed`, **including across save/load** (RNG state serialized).
- Stage 2 serializes its **full reaction network** so resumed runs use the same chemistry.
- Headless `simulate` and `export` subcommands.

### GUI (Tk, "Catalytic Silence" museum aesthetic)
- **Scrollable content** inside the fixed 720×1000 window — every section reachable on any screen.
- Rule + Grid dropdowns; **Reseed**; **Promote stage**.
- **Live parameter sliders** per stage (F/k/Du/Dv, CMC, mutation rate, etc.) + Stage 1 Pearson preset picker; the panel swaps as the pipeline promotes.
- **On-canvas colour legend** — viridis colorbar (field stages) / red→green fitness key (Stage 4).
- Transport: **Step / Play / Stop**, FPS slider.
- **Live on-canvas specimen caption** — names the current stage + decodes the colour legend.
- **Transition announcements** — entering a stage shows its principle + detail + citations in the marginalia.
- **Tutorial** walkthrough with citations.
- **Record GIF** (threaded, progress bar + Cancel) and **File ▸ Export GIF**.
- **File ▸ Save / Open snapshot** (JSON, exact RNG + config round-trip).
- **Gallery** — 9 museum plates (5 stage heroes + full-arc poster + hero/pipeline/prima).
- Animated **mascot**; bundled Italiana / Crimson Pro / IBM Plex Mono fonts; window icon.

### Assets
- `docs/generated/` — 6 whipgen-generated "Catalytic Silence" plates (stage0–4 + pipeline poster).
- `docs/hero.png`, `docs/pipeline.png`, `docs/prima-materia.png`, `docs/icon.png`, `cellauto/assets/icon.png`.

### Quality gates
- Test suite (currently **72 tests**) green.
- CI: Windows + Ubuntu matrix, ruff format/check, mypy, coverage threshold, pip-audit.

---

## 2. Punchlist (current cycle — v3.2 scientific-rigor + AAA overhaul)

### Done
- [x] **Correctness:** `find_raf` rewritten to the real Hordijk-Steel layered closure; catalysis made mandatory; false-positive-RAF regression test added.
- [x] **Correctness:** Stage 2 serializes its full reaction network (was fabricating a random one on load).
- [x] **Accuracy:** Stage 4 hypercycle docstring corrected to "fitness proxy"; Gray-Scott CFL/rescaling documented; mitosis preset harmonized; Stage 3 coacervate/vesicle conflation fixed.
- [x] **Real data:** Miller-Urey yields, fatty-acid CMC table, catalysis level, Eigen error threshold, diffusion-coefficient grounding.
- [x] **UI narrative:** per-stage `StageInfo` metadata; live stage caption + legend; transition announcements with citations.
- [x] **AAA assets:** 6 stage plates generated via whipgen MCP and wired into the Gallery.
- [x] **Regression fix:** scrollable content container so the controls are never pushed off the fixed-height window.

### Done (cont.)
- [x] **#6 Live parameter controls (live-applicable knobs)** — `cellauto/rules/params.py` `PARAM_SPECS` + a dynamic PARAMETERS panel in the GUI; sliders set the rule's dataclass fields live (read each step, no re-init), and the pipeline swaps the slider set per stage. Includes the Stage 1 Pearson preset picker. Structural params deferred (see group C).

### Done (cont.)
- [x] **#9 Visual colorbar + RAF graph** — on-canvas viridis colorbar / red→green fitness key for the field stages, AND the Stage 2 reaction-network / RAF graph view (Gallery ▸ Reaction network): a PIL-rendered node-edge diagram highlighting the Hordijk-Steel RAF with magenta catalyst links and amber food species. `cellauto/netviz.py`; tests in `tests/test_netviz.py`.

### In progress / next
- [ ] Structural parameter controls (re-init plumbing) + reset-to-defaults.
- [ ] **#7 Missing origin-of-life processes** (RNA world, hydrothermal vents, homochirality, mineral catalysis, error-catastrophe demo, coacervates) — see Roadmap §3.

### Mandated UI toolset (REQUIRED — every control below must exist in the GUI)

This is the contract for the GUI. The simulator is not considered complete
until every tool here is present and working. `[x]` = shipped, `[ ]` = owed.
Build new controls into existing sections or the scroll container — never in a
way that clips other controls (see [[cellauto-fixed-window-layout]]).

**A. Run control / transport**
- [x] Play / Pause (Play + Stop)
- [x] Single Step
- [x] Stop
- [x] Speed (FPS) control
- [x] Reseed / new run
- [x] Restart-to-step-0 — `RESTART` button: re-inits the state under the current rule and seed (preserves slider edits) and clears the stats buffer.
- [ ] Step-back / timeline scrubber (requires frame-history buffer)

**B. Stage navigation**
- [x] Rule selector (incl. each stage individually)
- [x] Grid-size selector
- [x] Promote stage (manual, forward)
- [x] Jump-to-stage picker (direct select 0–4) — `JUMP` combobox in the pipeline row.
- [x] Auto-promote toggle + stage-duration control — `AUTO-PROMOTE` checkbox and `DUR` spinbox in the pipeline row.

**C. Scientific parameters (the core teaching tools)**
- [x] Live parameter sliders for each stage's live-applicable knobs *(#6)* — Stage 0 amoeba lifespan; Stage 1 F/k/Du/Dv; Stage 2 food supply/diffusion; Stage 3 CMC/F/k; Stage 4 mutation rate/division radius/decay age. Pipeline swaps the slider set as stages promote.
- [x] Pearson regime preset picker for Stage 1 *(#6)*
- [x] Structural parameters with auto re-init — `ParamSpec.reinit=True` triggers `_reinit_param_target` (deterministic reseed from `engine.seed`). Shipped sliders: Stage 2 `n_species` / `n_reactions` / `food_fraction`, Wolfram1D `rule_number`. Grid size remains the GRID picker (already full-engine re-init via `_on_rule_change`).
- [x] Reset-parameters-to-defaults — `RESET` button in the PARAMETERS header.

**D. Observation, legends & plots**
- [x] Main simulation canvas
- [x] Live stage caption + colour legend (canvas overlay)
- [x] Visual colorbar (viridis ramp with hi/lo) for field stages *(#9)*
- [x] Fitness key (red→green) for Stage 4 *(#9)*
- [x] Reaction-network / RAF graph view (highlight RAF members) *(#9)* — Gallery ▸ Reaction network
- [x] Population / fitness time-series plot (sparkline) — live canvas overlay tracing the first non-meta population key with `min..max` annotation.

**E. Data & export**
- [x] Save / Open snapshot (JSON, exact round-trip)
- [x] Export GIF (threaded, progress + cancel)
- [x] Export current frame as PNG — `File ▸ Export frame as PNG…`.
- [x] Export run statistics as CSV — `File ▸ Export stats as CSV…` writes the recorded per-step population samples (bounded to 5000).

**F. Pedagogy & information**
- [x] Tutorial walkthrough with citations
- [x] Per-stage principle + citations (marginalia on transition)
- [x] Gallery of museum plates
- [x] About dialog
- [x] Status register (rule / seed / step / FPS / population stats)

**G. Accessibility**
- [ ] Colourblind-safe palette option (Stage 4 red→green is the worst offender)
- [ ] Text-scaling / zoom control

---

## 3. Roadmap (deferred / future)

### Missing origin-of-life processes (to fully tell the story)
- [x] **RNA world** (Gilbert 1986) — SHIPPED as the `abiogenesis-rna-world` rule: a spatial Eigen quasispecies with a tunable per-base error rate that crosses the threshold ε_c = ln(σ)/L to show the error catastrophe live. `stage_rna.py`; tests in `test_rna_world.py`. *Still to do: weave it into the auto-promoting pipeline.*
- [x] **Metabolism-first / alkaline hydrothermal vents** (Russell, Martin & Lane) — SHIPPED as `abiogenesis-hydrothermal-vent`: an alkaline chimney vs acidic ocean proton gradient (Dirichlet sources) whose steepness (proton-motive force) drives interface-localised organic synthesis; flattening the gradient stops all synthesis. `stage_vents.py`; `test_vents.py`.
- [x] **Homochirality** (Frank 1953; Soai 1995) — SHIPPED as `abiogenesis-homochirality`: a 2D Frank model (autocatalysis + mutual antagonism) that spontaneously breaks mirror symmetry into teal/magenta chiral domains; turning antagonism k_x→0 restores the stable racemic state. `stage_chirality.py`; `test_homochirality.py`.
- [x] **Mineral-surface catalysis** (Cairns-Smith; Ferris) — SHIPPED as `abiogenesis-mineral-catalysis`: a static montmorillonite clay mask where monomer→polymer condensation is catalysed, so polymer accumulates on the clay (~12× the bulk); equalising the bulk and clay rates removes the localisation. `stage_minerals.py`; `test_minerals.py`.
- **Error catastrophe demo** — make Eigen's 1/L threshold a visible, sweepable regime in Stage 4.
- [x] **Oparin coacervates** — SHIPPED as `abiogenesis-coacervate`: Cahn-Hilliard liquid-liquid phase separation; gold droplets nucleate from a near-uniform mix and coarsen (Ostwald ripening), a membraneless alternative to Stage 3's vesicles. `stage_coacervate.py`; `test_coacervate.py`.

### Platform & polish
- Web port (Pyodide / JS) so no Python install is needed.
- Accessibility: colourblind-safe palettes, text scaling, keyboard navigation.
- Per-vesicle / per-protocell inspectors (click a cell to see its genome / fitness).
- In-app concentration / population time-series plots (sparklines).
- Story mode: chaptered narration with per-stage dwell + transition cards.

---

## 4. How to use this doc
- **Adding a feature?** Add it to the Feature Inventory.
- **Starting work?** Move the item from Roadmap → Punchlist "in progress."
- **Shipping?** Re-read the Feature Inventory and confirm nothing on it broke.
