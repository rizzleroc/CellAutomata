# cellauto — Feature Inventory, Punchlist & Roadmap

This document is the project's **regression guard**. Before shipping any
change, check it against the Feature Inventory: nothing listed there should
silently disappear. The Punchlist tracks the current work cycle; the Roadmap
captures what's deliberately deferred.

Last updated: 2026-05-25.

> **v3.5 status:** all G1–G12 punchlist items from the v3.4 gap audit
> are CLOSED. The 12-stage pipeline is genuinely coupled; Stage XI runs
> the real Eigen-Schuster ODE; Stage X has Helfrich bending; Stage VIII
> uses a Miyazawa-Jernigan landscape; Stage XII derives LUCA core from a
> co-occurrence pathway graph. 141 tests / 88 % coverage / four CI gates
> green. The §0 audit below is preserved as the historical record of the
> gap closure; the live punchlist is in §0a.
>
> **v3.6 status:** local-vs-web UX parity SHIPPED. Nine of eleven L
> items closed; L2 (tabbed panels) + L10 (background grain) deferred
> with rationale in §5.
>
> **Web track status:** the canonical user-facing client is now
> **`docs/web3/`** (on branch `origin/claude/zealous-meitner-SrX1L`,
> not yet merged to `main`). Web3 implements the v4.0 SEM PRD + the
> v4.1 §F3 bioform sprite-overlay layer + Stage 3 (Helfrich vesicles,
> B3 from the punchlist). Web3's authoritative punchlist lives at
> [`docs/web3/PUNCHLIST.md`](web3/PUNCHLIST.md). Root `docs/index.html`
> redirects `/` → `/web3/`. The earlier `docs/web2/` (Control Round /
> The Arc Round / production deploy 2026-05-31) is preserved at
> `/web2/`; the original Gray-Scott-only museum plate at `/web/`.
>
> **v4.0 status (PROPOSED):** SEM-grade live rendering. See §6 below and
> the full PRD at [PRD_SEM_VISUALIZATION.md](PRD_SEM_VISUALIZATION.md).
> Twelve S items (S1–S12) span four phases — CPU rasteriser → sprite
> library → full stage catalogue → optional GPU shader → opt-in AI
> refinement. The goal is photographic instrument-grade rendering of
> every frame the engine produces, without changing the underlying
> simulation. **Web side already half-shipped on web3** — the SEM
> substrate (sem.js) + sprite overlay (sprites.js) are live; what
> remains for the desktop side is the Python `SemRenderer` port.
>
> **v5.0 status (PROPOSED):** LIFE — virtual-CPU digital organisms
> after LUCA. See §7 and the full PRD at
> [PRD_LIFE_DIGITAL_ORGANISMS.md](PRD_LIFE_DIGITAL_ORGANISMS.md).
> Inspired by the user's 400× Brachionus reference: post-LUCA, the
> simulator extends into a thirteenth stage where digital organisms
> with virtual-CPU genomes have **visible internal anatomy**, ingest
> substrate, excrete waste, divide with mutation, and form lineages.
> Draws on Tierra, Avida, Polyworld. Twelve V items (V1–V12) span
> five phases.

---

## 0. v3.4 honest gap analysis — historical record (gaps closed in v3.5)

A self-audit performed immediately after the v3.4 release. The project ships
twelve scientifically-themed stages, a real-data CHANGELOG, and an "every
panel is real simulator output" hero plate. Most of that is true. The
following gaps are also true and need to be closed before v4 can honestly be
called an *end-to-end* abiogenesis simulator.

### A. Showstopper gap — pipeline coupling is theatre

`AbiogenesisPipelineRule.promote()` (`cellauto/rules/abiogenesis/pipeline.py`,
line 189–195) hard-resets the inner state on every stage transition:

```python
def promote(self, state):
    state.current_stage = min(state.current_stage + 1, ...)
    new_rule = self._make_stage(state.current_stage)
    state.inner_rule = new_rule
    state.inner_state = new_rule.init_state(state.width, state.height)  # <-- !
```

Consequence: the moment you promote from Stage I → Stage II, the Stage I
field is **thrown away** and Stage II starts from its own random `init_state`.
The 12-stage "extended pipeline" is therefore not a continuous chemistry-to-life
arc; it is **twelve isolated simulations concatenated on a timer**, sharing
only the engine seed. A learner asking "what RAF would form from the
products of Stage I's Gray-Scott spots?" cannot find out from this software,
because Stage II never sees Stage I's `u`/`v` fields.

This is the single biggest honesty gap in the project. Closing it is **G1
below**.

### B. Self-confessed toy — Stage 4 protocell selection

`stage4_selection.py` lines 23–27 explicitly admit:

> This implementation is a TOY. Real protocell evolution involves membrane
> mechanics, internal RAF dynamics, and stochastic mutation rates that
> collectively determine the error threshold. … this stage demonstrates the
> *concept* on top of Stage 3's vesicles, not the rigorous biophysics.

The fitness is a scalar genome-product proxy `Σ g[i]·g[(i+1)%n]`, gating
growth/division. The genuine Eigen-Schuster ODE
`dx_i/dt = x_i(k_i x_{i-1} − Φ)` is not implemented. The README + CHANGELOG
should not be marketing this as the hypercycle without that caveat.

### C. Named-but-toy scientific dynamics

| Stage | What it claims | What it actually does | Verdict |
|---|---|---|---|
| **Stage 3 — vesicles** | Helfrich CMC physics | Threshold + connected-component labelling on a Gray-Scott-like field; no curvature elasticity, no surface tension dynamics | PARTIAL |
| **Stage VIII — genetic code** | Vetsigian-Woese-Goldenfeld code coevolution | Toy codon → amino-acid → fixed target peptide match; no translation thermodynamics, no protein folding | PARTIAL |
| **Stage XII — LUCA** | Weiss et al. comparative-genomics distillation | Hand-shaped benefit-cost gene-presence landscape; "core" is recovered by 70 % prevalence threshold (this part is real methodology), but the underlying selection landscape is bespoke, not derived | PARTIAL |

These are **scientifically suggestive demonstrations**, not the published
models. The CHANGELOG / README should soften the phrasing from "implements
X" to "demonstrates the concept of X". Closing the dynamics is G3–G5.

### D. Vacuous test — `test_code_consensus_signal_present`

`tests/test_genetic_code.py` line 45–51:

```python
def test_code_consensus_signal_present():
    """The exact universal-code convergence takes many more steps than a unit
    test can run; here we just confirm the consensus metric is well-defined
    and inside a sensible range under active selection."""
    rule = AbiogenesisStageGeneticCode(rng=random.Random(7))
    _, _, final = _run(rule)
    assert 0 <= final["code_consensus_x100"] <= 100
```

The metric is bounded to `[0, 100]` by construction. This is a tautological
assertion — it cannot fail and verifies nothing. The honest comment makes it
*even worse* because we knowingly shipped a test that asserts nothing. Two
fixes: either run the rule long enough to assert convergence above the
random baseline (`consensus > 1/n_amino + δ`), or delete it and replace with
a behavioural test that exercises mutation knobs.

### E. Other tests that pass without pinning the scientific claim

- **CMC gate test missing.** No test verifies that Stage 3 produces *zero*
  vesicles below the CMC threshold and a positive count above it. The
  threshold is the central scientific claim of the stage — it should be
  pinned.
- **Eigen error-catastrophe transition.** The RNA-world stage exposes the
  Eigen threshold `ε_c = ln(σ)/L`. No test verifies that crossing this
  threshold collapses the master-sequence population — the predicted phase
  transition isn't pinned.
- **Wood-Ljungdahl feedstock dependency.** `test_vents.py` does check that
  PMF and ΔG track pH, but does *not* assert that setting H₂=0 zeroes the
  acetate yield (the chemistry-not-just-gradient claim).

### F. Doc drift after v3.4

- ROADMAP §1 still lists "Five abiogenesis stages" and "(currently 72
  tests)" — the project now has 12 stages and 120 tests.
- ROADMAP §3 marks the extended pipeline as shipped but doesn't carry the
  gap-A caveat.
- README's "twelve observations on the coalescence of chemistry into life"
  poster phrasing implies a coupled narrative; reword to match the reality
  while gap A is open.

---

## 0a. Punchlist — v3.5 honest-gap closure

These items close the gaps audited above, in priority order.

**Pipeline coupling**
- [x] **G1 — state hand-off across stage transitions.** Replace
  `init_state(W, H)` in `promote()` / `set_stage()` with a per-pair
  `inherit_from(prev_rule, prev_state)` adapter. For each promotion pair
  define at minimum *what fraction of the previous field's mass survives*
  into the next stage's relevant species. Minimal viable handoffs:
  - Stage I (Gray-Scott `v` field) → Stage II (RAF concentrations seeded
    from the `v` field's spatial distribution)
  - Stage II (RAF products) → Stage III (vesicle amphiphile field seeded
    from the modal RAF product concentration)
  - Stage III (vesicle mask) → Stage IV (protocell positions seeded from
    vesicle centroids)
  - Pipeline-level test: stepping `pipeline → pipeline.promote → step`
    must produce a state correlated with the pre-promotion state, not
    independent.

**Science depth**
- [x] **G2 — hypercycle dynamics in Stage 4.** Add an optional
  `dynamics: Literal["proxy", "hypercycle"]` field. Under `"hypercycle"`,
  evolve genome concentrations by the Eigen-Schuster replicator ODE
  (Euler-step, mean-field Φ) and gate growth/division on the largest
  replicator's `x_i`. Keep the proxy as the default until parity is proven.
  Remove the "TOY" disclaimer once `hypercycle` is the default.
- [x] **G3 — Helfrich curvature term in Stage 3.** Add a curvature-elastic
  penalty `κ_b · (∇²φ)²` to the Stage 3 evolution so vesicle shape is set by
  bending modulus, not just by the CMC threshold. Calibrate `κ_b` to
  Helfrich's 1973 measurement range (~10⁻¹⁹ J).
- [x] **G4 — protein-fitness landscape in Stage 8.** Replace the fixed
  target peptide with a Miyazawa-Jernigan-style residue-pair energy table
  so the fitness of a peptide depends on its sequence composition, not on
  matching a hard-coded answer key.
- [x] **G5 — selection-derived essential gene set in Stage 12.** Currently
  the benefit-cost landscape is hand-shaped. Switch the essential-gene
  bitmask to be derived from a static co-occurrence matrix (a small toy
  KEGG-like pathway graph) so the "core" recovered is genuinely the
  invariant of the network rather than a tuned parameter.

**Test pins**
- [x] **G6 — pin CMC gate.** Test: with `cmc_threshold` set above the
  field's peak, `vesicle_count == 0`; with it well below, `vesicle_count > 0`.
- [x] **G7 — pin Eigen error catastrophe.** Test: with ε = 0.5·ε_c the
  master-sequence frequency stays > 0.5 of initial; with ε = 1.5·ε_c it
  decays to < 0.1 within 200 steps.
- [x] **G8 — pin Wood-Ljungdahl stoichiometry.** Test: setting
  `h2_feed_level=0` (or `co2_feed_level=0`) drives the acetate yield to
  zero. Setting both non-zero gives a positive yield. Setting H₂ to twice
  the CO₂ feed doesn't *exceed* the 2:1 stoichiometric cap.
- [x] **G9 — fix `test_code_consensus_signal_present`.** Either run long
  enough to assert `consensus > random_baseline + δ`, or delete and replace
  with a mutation-knob test (e.g. `code_mutation=0` ⇒ consensus rises
  monotonically; `code_mutation=1.0` ⇒ consensus stays near random).
- [x] **G10 — pipeline-handoff regression test.** After G1: assert that
  stepping a 2-stage pipeline through one promotion produces a Stage II
  state whose initial field correlates with the Stage I final field
  (spatial correlation coefficient > 0).

**Honesty in messaging**
- [x] **G11 — README / CHANGELOG phrasing pass.** While gaps A and C are
  open, reword "implements" → "demonstrates" for stages 3, 4, 8, 12; add a
  one-line disclaimer under "Try it" linking back to §0 of this file.
- [x] **G12 — fix ROADMAP doc-drift.** Update §1's stage count
  (5 → 12), test count (72 → 120), and add the v3.4 gap section here as
  authoritative.

---

---

## 1. Feature Inventory (must not regress)

Every feature below is implemented and expected to keep working. A change that
removes or breaks one of these is a regression, not a simplification.

### Simulation science
- **Twelve abiogenesis stages**, each an independently runnable rule (verdicts
  per §0.C — REAL = published dynamics implemented; PARTIAL = scientifically
  suggestive demonstration):
  - Stage 0 — primordial soup (discrete four-rule mixing/condensation). REAL.
  - Stage I — Gray-Scott reaction-diffusion (forward-Euler, 5-pt Laplacian, CFL-stable). REAL.
  - Stage II — alkaline hydrothermal vent — pH gradient, Nernst PMF (mV), Faraday ΔG (kJ/mol), Wood-Ljungdahl carbon fixation (2 CO₂ + 4 H₂ → acetate). REAL.
  - Stage III — Gray-Scott reaction-diffusion (cont.) (legacy slot used by some pipelines).
  - Stage IV — mineral catalysis on a Na-montmorillonite mask (Ferris-style localisation). REAL.
  - Stage V — Kauffman autocatalytic sets via the **correct Hordijk-Steel RAF closure**. REAL.
  - Stage VI — Frank-model homochirality (autocatalysis + mutual antagonism). REAL.
  - Stage VII — spatial Eigen quasispecies; threshold ε_c = ln(σ)/L. REAL.
  - Stage VIII — genetic-code coevolution (toy codon → amino → fixed-target peptide match). PARTIAL — concept only; G4 to deepen.
  - Stage IX — Cahn-Hilliard coacervates (conserved-order-parameter LLPS). REAL.
  - Stage X — lipid vesicle self-assembly (CMC threshold + connected-component vesicle counting). PARTIAL — threshold gate, no Helfrich curvature dynamics; G3 to deepen.
  - Stage XI — protocell selection (genome-product fitness proxy gating growth/division/death). PARTIAL — **self-confessed TOY** in docstring; G2 to deepen.
  - Stage XII — LUCA distillation (gene-presence bitsets; 70 %-prevalence core). PARTIAL — methodology real, landscape hand-shaped; G5 to deepen.
- **Pipeline rules** — `abiogenesis-pipeline` (5 stages) and
  `abiogenesis-pipeline-extended` (12 stages). **NB:** until G1 is closed,
  promotion resets the inner state — the "pipeline" is a sequence of
  isolated runs, not a coupled narrative.
- **Reference automata**: Conway's Game of Life, Wolfram 1D (rules 0–255).
- **Legacy alias** `natural-selection` → Stage 0 (kept for old snapshots/CLI).
- **Real published data** backing the constants:
  - Stage 0 soup sampled by **Miller's 1953 measured product yields** (`MILLER_UREY_SPECIES`).
  - Stage X named fatty acid + **measured CMCs** (`AMPHIPHILE_CMC_MM`: decanoic C10 ≈ 85 mM, etc.).
  - Stage V reports **Kauffman catalysis level** (n_reactions/n_species).
  - Stage XI exposes **Eigen error threshold** (≈ 1/L) + mutation-rate stat.
  - Gray-Scott Du:Dv grounded against real ~10⁻⁹ m²/s diffusion coefficients.
  - Vent stage exposes live **PMF (mV)** and **ΔG (kJ/mol)** via the Nernst equation.
  - Stage XII names 16 LUCA gene families (`LUCA_GENE_NAMES`).

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
- Test suite (currently **120 tests**) green; **87 % coverage** on the
  science / engine / data modules (Tk-dependent integration code omitted
  per `pyproject.toml`).
- CI: Windows + Ubuntu matrix, ruff format/check, mypy, coverage threshold, pip-audit.

### Assets (v3.4 AAA bundle)
- `docs/genesis.png` — magnum-opus poster (2400×3700), every panel real simulator output.
- `docs/generated/cellauto_twelve_tableaux.png` — 12-panel museum atlas plate, generated via the whipgen MCP.
- `docs/generated/stage7_genetic_code_plate.png`, `stage11_luca_plate.png` — per-stage Catalytic Silence triptychs.
- `docs/icon.png` — protocell-fission identity mark (1024×1024).
- `docs/web/banner.png` — web-port hero banner.
- `tools/render_aaa_visuals.py` — deterministic PIL renderer for the five non-MCP pieces.
- Six legacy whipgen-generated stage plates from v3.2 in `docs/generated/`.

---

## 2. Punchlist (closed cycles — v3.2 / v3.3 / v3.4)

This section is historical — see §0a for the current v3.5 work. The items
below are *closed*; their entry here is the record of what shipped.

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

### Closed in v3.3 / v3.4
- [x] Structural parameter controls + reset-to-defaults — `ParamSpec.reinit=True` triggers `_reinit_param_target`; `RESET` button restores dataclass defaults.
- [x] **#7 Missing origin-of-life processes** — all shipped (RNA world, vents, homochirality, mineral catalysis, coacervates, genetic code, LUCA). Caveats per §0.C.

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
- [x] Step-back / timeline scrubber — bounded ring buffer of serialized state per step (cap 120) with a `SCRUB` Scale in TRANSPORT; drag back to restore any captured frame. Stepping after a scrub-back **truncates the future** so timelines branch rather than overwrite.

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
- [x] Colourblind-safe palette option — `View ▸ Colour-blind safe palette` checkbox swaps Stage 4's red→green disc colour (the audit's flagged CVD offender) for a blue→yellow ramp; the legend bar follows. Other diverging maps in the project (chirality teal↔magenta, vents blue↔orange, viridis) are already CVD-friendly.
- [x] Text-scaling / zoom control — `View ▸ Small/Default/Large/Extra-large text` calls `_apply_font_scale(scale)`, which recomputes every font tuple and re-applies the ttk styles uniformly; canvas overlays refresh via `_sync_stage_caption`. Clamped to [0.6, 2.0].

---

## 3. Roadmap (deferred / future)

### Cycle direction
**v3.5 SHIPPED — honest-gap closure done.** G1–G12 from §0a are all closed:
the 12-stage pipeline is now genuinely coupled (state flows across every
promotion), Stage XI integrates the real Eigen-Schuster replicator ODE,
Stage X has Helfrich bending elasticity, Stage VIII uses a
Miyazawa-Jernigan-style residue-contact landscape, and Stage XII derives
its essential gene set from a pathway co-occurrence graph rather than a
hand-shaped vector. 141 tests, 88 % coverage. The deferred items below are
the v3.6+ direction.

### Missing origin-of-life processes (to fully tell the story)
- [x] **RNA world** (Gilbert 1986) — SHIPPED as the `abiogenesis-rna-world` rule: a spatial Eigen quasispecies with a tunable per-base error rate that crosses the threshold ε_c = ln(σ)/L to show the error catastrophe live. `stage_rna.py`; tests in `test_rna_world.py`. *Still to do: weave it into the auto-promoting pipeline.*
- [x] **Metabolism-first / alkaline hydrothermal vents** (Russell, Martin & Lane) — SHIPPED as `abiogenesis-hydrothermal-vent`: an alkaline chimney vs acidic ocean proton gradient (Dirichlet sources) whose steepness (proton-motive force) drives interface-localised organic synthesis; flattening the gradient stops all synthesis. `stage_vents.py`; `test_vents.py`.
- [x] **Homochirality** (Frank 1953; Soai 1995) — SHIPPED as `abiogenesis-homochirality`: a 2D Frank model (autocatalysis + mutual antagonism) that spontaneously breaks mirror symmetry into teal/magenta chiral domains; turning antagonism k_x→0 restores the stable racemic state. `stage_chirality.py`; `test_homochirality.py`.
- [x] **Mineral-surface catalysis** (Cairns-Smith; Ferris) — SHIPPED as `abiogenesis-mineral-catalysis`: a static montmorillonite clay mask where monomer→polymer condensation is catalysed, so polymer accumulates on the clay (~12× the bulk); equalising the bulk and clay rates removes the localisation. `stage_minerals.py`; `test_minerals.py`.
- **Error catastrophe demo** — make Eigen's 1/L threshold a visible, sweepable regime in Stage 4.
- [x] **Oparin coacervates** — SHIPPED as `abiogenesis-coacervate`: Cahn-Hilliard liquid-liquid phase separation; gold droplets nucleate from a near-uniform mix and coarsen (Ostwald ripening), a membraneless alternative to Stage 3's vesicles. `stage_coacervate.py`; `test_coacervate.py`.

### Platform & polish
- [x] Extended auto-promote pipeline weaving every shipped origin-of-life process — SHIPPED as `abiogenesis-pipeline-extended` (10 stages: soup → vent → RD → mineral → RAF → chirality → RNA → coacervate → vesicles → selection). `AbiogenesisPipelineRule` was parameterised with `stage_classes`/`stage_infos`, so the original 5-stage default is unchanged.
- [x] Web port (Pyodide / JS) so no Python install is needed — **SHIPPED as an MVP**: vanilla-JS Gray-Scott reaction-diffusion explorer in `docs/web/` (~400 lines: `index.html` + `styles.css` + `sim.js` + `viridis.js` + `presets.js`). Deployable to GitHub Pages from `/docs`. Other stages exhibited as static museum-plate gallery; the full 12-rule sandbox remains the Python build. No Pyodide — direct JS port of `gray_scott_step`.
- [x] Accessibility: colourblind-safe palettes, text scaling.
- [x] Accessibility: keyboard navigation — Space (play/pause), → (step), R (restart), P (promote), [ / ] (prev/next pipeline stage), with text-entry focus guard so Spinbox/Combobox typing isn't hijacked. Help ▸ Keyboard shortcuts lists them.
- [x] Per-protocell inspector — `Button-1` on the canvas hit-tests Stage 4 `Protocell` discs (direct rule or pipeline-wrapped) and opens a Toplevel showing position, radius, age, fitness, and the genome vector, plus a caption explaining the hypercycle-coupling fitness.
- [x] In-app concentration / population time-series plot (sparkline overlay).
- [x] Story-mode chapter transition cards — when the pipeline promotes, a centered overlay shows "CHAPTER N · TITLE" + principle + citation, fades after ~4.5 s via `_animate` countdown. Works for both 5- and 10-stage pipelines.

---

## 6. v4.0 — SEM-grade visualization cycle (proposed)

Full PRD: **[docs/PRD_SEM_VISUALIZATION.md](PRD_SEM_VISUALIZATION.md)**.

### One-line vision
The v3.x line earned scientific *credibility* (real Eigen-Schuster ODE,
Helfrich bending, Miyazawa-Jernigan landscape, pathway-graph LUCA,
coupled 12-stage pipeline). The v4.0 line earns scientific
**representation** — every frame the engine produces should look like a
live SEM (scanning-electron-microscope) feed of real abiotic chemistry,
not a viridis heat-map on a pixel grid.

### Cycle direction
The reference target is the user-supplied ideal-state image: a warm-sepia
SEM micrograph of granular substrate with spherical protocell-like forms
catching directional light, framed by a "LIVE SEM FEED" badge, scale bar,
and the v3.6 three-column composition. We get there by adding a new
**depth-shading renderer** alongside the existing viridis one and
toggling between them from `View ▸ SEM mode`. Underlying simulation
stays unchanged — the win is purely visual.

### Punchlist (open until each phase ships)

- [ ] **S1 — `SemRenderer` core (Phase 1).** New module
  `cellauto/renderer_sem.py` implementing the depth-shaded numpy
  rasteriser: height-field → gradients → normals → Lambertian +
  ambient + specular shading → procedural noise overlay → sepia /
  mono LUT → LANCZOS upscale → vignette + crosshair + scale-bar
  overlay. Same `render(state)` signature as `FieldRenderer` so app.py
  stays agnostic. Target: 20 FPS @ 60×60 grid on CPU.
- [ ] **S2 — Palette modes.** `warm-sepia` (matches the reference image)
  and `cool-mono` (extends the existing Catalytic Silence palette into
  3-D shading). Picker under `View ▸ SEM palette`. Both verified
  colourblind-safe via `colorspacious`.
- [ ] **S3 — `View ▸ SEM mode` toggle.** Checkbox flips between
  viridis (legacy v3.6) and SEM rendering. Persists in the existing
  config. Both render paths share step counts on the same seed
  (regression-pinned).
- [ ] **S4 — Instrument framing.** Centred crosshair reticle (1-px
  hairline teal), "LIVE SEM FEED · Stage N — name" microcaps badge
  upper-right, scale-bar microcopy below the canvas, ~10 % corner
  vignette. Pulse-syncs the badge opacity with the v3.6 playback dot.
- [ ] **S5 — Stage 1 hero pass.** Tune the height-map derivation +
  shading parameters until Stage 1 (Gray-Scott) reads as the
  reference image. This is the *demo gate* for the cycle — if Stage 1
  doesn't look like an SEM, ship nothing.
- [ ] **S6 — Sprite library, stages 0 / 1 / 3 (Phase 2).** Each stage's
  characteristic forms (protocell granules, Gray-Scott spots, vesicle
  bilayers) pre-rendered as alpha PNGs and composited over the
  shaded background per the per-stage sim state.
- [ ] **S7 — Full stage catalogue (Phase 3).** Sprite library extended
  to all 12 stages of the extended pipeline. `docs/generated/sem_<stage>.png`
  committed for each.
- [ ] **S8 — Graceful fallback (F6).** If Pillow / numpy / Tk capability
  detection fails, drop to v3.6 viridis rendering with a one-time toast
  explaining why. No crashes.
- [ ] **S9 — Regression tests.** ≥ 8 new pins:
    - SemRenderer produces non-trivial image for each stage
    - SEM and viridis renderers produce same step count on the same seed
    - Zero-field input → near-uniform background
    - Palette mode persists across init
    - Reduced-motion mode disables the badge pulse
    - PNG export under SEM mode matches the on-screen view byte-for-byte
    - SEM mode falls back cleanly when Pillow LANCZOS isn't available
    - Performance budget: 20 FPS @ 60×60 on CI hardware
- [ ] **S10 — Optional GPU path (Phase 4).** `cellauto[gpu]` extra
  brings `moderngl`; auto-select if importable. GLSL fragment shader
  port of the Phase-1 pipeline. Maintains exact pixel parity with
  CPU path (golden-image regression).
- [ ] **S11 — Stretch: AI image-to-image refinement (Phase 5).**
  `tools/sem_refine.py` runs SEM output through a fine-tuned diffusion
  model at strength 0.35 for hero-shot quality. `File ▸ Export refined
  PNG…` menu entry. Slow, opt-in, never the default.
- [ ] **S12 — Documentation.** README + CHANGELOG carry a before/after
  comparison image. `docs/science.md` notes that SEM mode is purely a
  rendering choice; the underlying physics is unchanged.

### Out of scope for v4.0
- Replacing Tk with PyQt / Electron / web-only (the v3.6 audit settled
  this — Tk stays).
- Volumetric / true-3-D ray-traced rendering (SEM imagery is 2.5-D
  depth-mapped; a volumetric chemistry sim is a v5.0 conversation).
- Mandatory GPU dependency (GPU is an opt-in extra).
- Replacing the underlying simulation. Every SEM pixel must still trace
  to a real engine value. No "decorative" structures.

### Acceptance criteria for v4.0.0 (the first ship)
See PRD §9. Headlines:
1. `cellauto gui --rule abiogenesis-pipeline` shows the 5-stage pipeline
   in SEM mode by default.
2. `View ▸ SEM mode` toggles cleanly between SEM and viridis.
3. Stage 1 under SEM mode reads as a microscope view, not a screenshot.
4. Four CI gates green; ≥ 8 new tests.
5. v4.0 entry in CHANGELOG with a before/after comparison image.

---

## 7. v5.0 — LIFE: Digital Organisms (proposed)

Full PRD: **[docs/PRD_LIFE_DIGITAL_ORGANISMS.md](PRD_LIFE_DIGITAL_ORGANISMS.md)**.

### One-line vision
After LUCA distillation, real digital organisms. Inspired by the
user-supplied 400× DIC reference of *Brachionus plicatilis* — a living
rotifer with visible internal motion. A new Stage XIII populates the
post-LUCA world with **virtual-CPU genomes** that execute instructions,
ingest substrate, excrete waste, divide, mutate, and form lineages
under selection. Draws from Tierra (Ray 1991), Avida (Ofria 1999), and
the broader artificial-life canon.

### Cycle direction
The v3.x line stopped at the *recipe* for life (LUCA distillation).
v5.0 walks one step further: from "the lineage that emerged" to "the
lineages that lived." Every behaviour visible in the rendered organism
maps to a real instruction or state in the virtual machine — no
decorative motion. The Brachionus reference is the visual target:
translucent body wall + visible internal compartments + cytoplasmic
shimmer at instruction-execution rate.

### Punchlist (open until each item ships)

- [ ] **V1 — Virtual CPU + opcode set.** ~20 opcodes (load, store,
  add, jump, copy, ingest, excrete, sense, move, …); ≤ 512-instruction
  genome cap. Tierra-derived, Avida-flavoured. Per-organism private
  memory (Tierra-shared variant comes later in V11).
- [ ] **V2 — Energy + metabolism loop.** Every instruction costs
  1 unit of energy; INGEST replenishes from the substrate field;
  EXCRETE adds to waste. Energy = 0 → death; energy ≥ E_div → division.
- [ ] **V3 — Stage XIII rule (`abiogenesis-life`).** Registered in
  `cellauto/rules/`; appears as the thirteenth stage of the extended
  pipeline. Pipeline hand-off (G1) from Stage XII seeds the initial
  population at LUCA pathway-graph hot-spots.
- [ ] **V4 — Substrate + waste grid.** 60 × 60 default grid; substrate
  replenishes linearly; waste accumulates and increases nearby
  death probability.
- [ ] **V5 — Mutation + lineage tracking.** Per-instruction ε mutation
  at copy time; per-organism parent pointer; ancestry chain
  reconstructible to the founder.
- [ ] **V6 — Per-organism inspector.** Click-to-inspect Toplevel
  (Tk) / drawer (web) showing genome strip, energy, instruction
  pointer, ancestry tree.
- [ ] **V7 — V3.6 viridis rendering.** Default render: filled
  energy-coloured discs on the substrate field; this is the v5.0.0
  ship target. Internal anatomy (V9) requires SEM mode and waits for
  v4.0.
- [ ] **V8 — Twelve regression tests.** VM opcodes, energy → death,
  energy → division, mutation gates lineage diversity, ε > ε_c →
  catastrophe, distinct lineage within 10k steps at default seed,
  substrate depletion → crash, ancestry tracked, pipeline hand-off,
  no per-step allocation, serialisation round-trip, web/Python VM
  parity (deferred).
- [ ] **V9 — Translucent body sprite (Phase 5.1).** Each organism
  rendered with a translucent ellipse body — no internal anatomy yet,
  just the membrane. Requires SEM mode.
- [ ] **V10 — Internal anatomy (Phase 5.1).** Gut compartment with
  drifting ingested particles + genome strip + nucleus
  visible inside each organism. Cytoplasmic shimmer at execution
  rate. Brachionus-style preview shipped to
  `docs/generated/stage13_life.png`.
- [ ] **V11 — Ecology mechanics (Phase 5.2).** Predation between
  lineages; cross-cell substrate gradients; self-organised
  predator-prey cycle visible in the population sparkline within
  20k steps.
- [ ] **V12 — Tierra shared-memory variant (Phase 5.4).** Optional
  `dynamics="tierra"` rule config puts all organisms in one shared
  instruction tape so parasites can emerge as in Tierra 1991.
  Pinned by a parasite-emergence regression.

### Out of scope for v5.0
- Multicellular organisms with differentiated tissues (v5.x+).
- Neural-network controllers à la Polyworld.
- 3-D bodies / physical morphology à la Framsticks.
- Replacing the v4.0 SEM renderer (LIFE feeds it; doesn't replace it).

### Acceptance criteria for v5.0.0
See PRD §7. Headlines:
1. New rule `abiogenesis-life` (or `digital-life`) registered;
   thirteen-stage extended pipeline.
2. Self-sustaining population for ≥ 10k steps at default seed.
3. Per-organism click inspector shows genome, energy, ancestry.
4. ≥ 12 new tests; four CI gates green.
5. v5.0 entry in CHANGELOG; README updated to "13-stage pipeline".

### Cycle direction recommendation
See PRD §10. The recommended path is to **pair v4.0 SEM (S1–S5) with
v5.0 LIFE (V1–V8)** on a shared cycle — the SEM substrate gives LIFE
the rendering vocabulary the Brachionus reference demands, and LIFE
provides content that exercises SEM in ways the existing 12 stages
don't. Shipping them together is the cleanest story.

---

## 5. Local-vs-Web parity punchlist (v3.6 candidate cycle)

The project ships two clients running the same Python engine: the **Tk
desktop app** (`cellauto/app.py`, on `main`) and the **Flask web client**
(`cellauto/web/` on branch `origin/claude/web-version-o6ZxW`). A side-by-side
audit found that while the Tk client is feature-richer functionally
(Gallery, scrubber, protocell inspector, RAF network view, sparkline,
keyboard shortcuts, CSV export, font scaling), the web client has a
distinct set of UX qualities the Tk app lacks. v3.6 closes those gaps.

### Punchlist (open until each item ships)

- [x] **L1 — Always-visible stage wall-label.** Web shows the active pipeline
  stage as a left-column "wall label" (title + citation + detail) that's
  always visible. Tk currently puts the stage caption as a canvas overlay
  that competes with playback rendering. **Fix:** add a dedicated stage-info
  panel above the parameter sliders that always shows the current stage's
  title, principle one-liner, citation, and "what the colours mean" legend.
  Hide it for non-pipeline rules.
- [ ] **L2 — Tabbed control panels.** *(deferred — see "Deferred" below.)*  Web groups controls into three
  tabs: Parameters / Stage / Export. Tk uses one long scrolling column.
  **Fix:** use `ttk.Notebook` to group the existing controls — Configuration
  + Pipeline on one tab, Parameters on a second, Export/Snapshot on a
  third. Keep transport bar always visible above the tabs.
- [x] **L3 — Preset chips.** Web renders Pearson regime presets as
  inline toggle-button chips (spots / stripes / mitosis / waves /
  labyrinth). Tk uses a dropdown. **Fix:** replace the preset combobox
  with a row of `ttk.Radiobutton`-styled chip buttons that stay visible
  so users can see the full menu at once.
- [x] **L4 — Debounced parameter slider updates.** Web debounces param
  changes (250 ms for reinit, 60 ms for live) so dragging a slider
  doesn't trigger five state rebuilds per second. Tk currently rebuilds
  state on every slider tick when a "reinit" param changes. **Fix:**
  wrap `_on_param_change` with a 250-ms `after()` debouncer for reinit
  params and 60 ms for live params.
- [x] **L5 — Batch stepping at high FPS.** Web requests up to 20 steps
  per fetch when the user cranks FPS above the wire latency. Tk steps
  one engine.step() per Tk `after()` tick, so FPS is capped by the Tk
  scheduler. **Fix:** if the requested FPS is above a threshold (say
  30 Hz), do N steps per tick where N = requested_fps / actual_fps.
- [x] **L6 — Reduced-motion preference toggle.** Web honours OS-level
  `prefers-reduced-motion`. Desktop has no equivalent OS signal. **Fix:**
  add a `View ▸ Reduced motion` checkbox that caps FPS at 10 Hz when
  enabled, suppresses chapter-card fade, freezes the mascot animation,
  and persists in a small config file.
- [x] **L7 — Population stats as wrap-friendly chips.** Web wraps the
  Stage-II vent readout (10+ stats) into key:value chips that flow on
  multiple lines. Tk shows them on one line and clips. **Fix:** render
  population as a `ttk.Frame` of label pairs that wrap, not a single
  `Label` with a long string.
- [x] **L8 — Pulsing brand-mark animation while playing.** Web pulses
  its small brand-mark dot while the sim is live (2.2-s cycle). Tk has
  a mascot but no playback-tied animation. **Fix:** add a small teal
  status dot near the title that pulses opacity when `_running == True`.
- [x] **L9 — Canvas glow during playback.** Web brightens a teal
  box-shadow around the canvas while playing. Tk has a static 2-pixel
  rim. **Fix:** animate the canvas border colour from `HAIRLINE`
  (#1f4f4c) to `ACCENT` (#39d4c8) and back at the same 2.2-s cycle.
- [ ] **L10 — Background grain texture.** *(deferred — see "Deferred" below.)*  Web overlays a 1%-opacity
  SVG noise texture for tactile feel. Tk's frame is flat obsidian.
  **Fix:** generate a small Perlin or white-noise PNG at startup,
  composite it onto the background `Frame` via a `Canvas` underlay
  at low alpha. Disable when L6 reduced-motion is on.
- [x] **L11 — Tutorial modal listing.** Web offers a modal with all
  tutorial steps listed (jumpable). Tk advances one line at a time
  through the marginalia. **Fix:** add `Help ▸ Tutorial — all steps`
  that opens a `Toplevel` listing every step with click-to-jump.
- [x] **L12 — Non-blocking error toast.** Web shows errors as an
  auto-clearing in-page banner (6 s timeout). Tk uses blocking
  `messagebox.showerror`. **Fix:** add a thin status strip at the
  top of the window that shows the most-recent error/info message,
  fades after 6 s, and is replaced by the next one.

### Out of scope for the parity cycle
- Server-side session management (L4 in the audit) — desktop is
  single-process, no equivalent need.
- Batch API + frame.png + GIF endpoints — desktop already has Export
  PNG / Export GIF; the wire format doesn't matter to a local user.
- 3-column responsive layout — desktop is fixed-geometry by design.
- Web fonts — Tk already ships an embedded font pack (Italiana,
  Crimson Pro, IBM Plex Mono) that fills the same role as Cormorant
  Garamond + Inter + JetBrains Mono on the web.

### Deferred from v3.6 (closed cycle) — rationale
- **L2 (tabbed control panels)**: the web uses tabs because horizontal
  space is constrained; Tk uses a scrolling vertical column. Both
  designs let the user reach every control with one interaction. A
  tab refactor in Tk would touch 600+ lines of layout code with real
  regression risk for a purely aesthetic change. Not a parity gap.
- **L10 (background grain texture)**: Tk has no CSS-equivalent
  background-image support; achieving a 1 %-opacity noise overlay
  would require putting a Canvas behind every Frame and stacking the
  widgets over it — high implementation complexity for an effect
  that's nearly imperceptible at 1 % opacity. Not worth the risk.

---

## 4. How to use this doc
- **Adding a feature?** Add it to the Feature Inventory.
- **Starting work?** Move the item from Roadmap → Punchlist "in progress."
- **Shipping?** Re-read the Feature Inventory and confirm nothing on it broke.
