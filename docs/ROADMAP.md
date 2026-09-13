# cellauto — Feature Inventory, Punchlist & Roadmap

This document is the project's **regression guard**. Before shipping any
change, check it against the Feature Inventory: nothing listed there should
silently disappear. The Punchlist tracks the current work cycle; the Roadmap
captures what's deliberately deferred.

Last updated: 2026-05-30.

> **⚑ Review correction (2026-06-03, v4.1.1).** A full-application review
> re-measured the project against running code: **13 abiogenesis stages**
> (Stage XIII digital life shipped), **≈318 tests collected** (279 fns;
> 316 passed / 1 env-failure / 1 skipped), **91 % coverage**, and **six CI
> checks + a security job** (not "four gates"). The G1–G5 items below remain
> shipped, but two are real-but-overclaimed (G3 Helfrich, G4 Miyazawa-Jernigan)
> and the coupling is via `extract_signal`/`seed_field`, not an `inherit_from`
> adapter. Stale counts/phrasing in the historical entries below are preserved
> as record; the live numbers and 36 documented issues are in
> **[docs/review/](review/)** (`APPLICATION_REVIEW_v4.1.md` + `ISSUE_REGISTER.md`),
> tracked as the §7 punchlist at the end of this file.

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
> **v4.0.0a1 SHIPPED — SEM-grade live rendering, Phase 1.** Eight of
> twelve S items closed (S1, S2, S3, S4, S5, S8, S9, S12); four
> deferred to v4.0.1+ (S6, S7 sprite library — Phases 2 + 3; S10
> optional GPU path — Phase 4; S11 AI image-to-image refinement —
> Phase 5). The alpha designation reflects the deferred Phase 2 / 3
> sprite libraries; the rendering pipeline itself is feature-complete
> for Phase 1. The v3.6 simulation engine, constants, dynamics, and
> snapshot format are unchanged — every SEM pixel still traces back
> to a real engine value via `render_rgb(state)`. See §6 below and
> the full PRD at [PRD_SEM_VISUALIZATION.md](PRD_SEM_VISUALIZATION.md).
>
> **v4.1.0 SHIPPED — two-channel render + hi-res.** The render path is now
> explicitly two-channel: **Channel A** is the unchanged grounded SEM
> micrograph; **Channel B** (`cellauto/channel.py`) is a new additive,
> toggleable narrative layer — "A Day in the Life of a Cell" — with a
> procedural mood-driven protagonist (`cellauto/character.py`), a narration
> ribbon + day-clock (`cellauto/narrative.py`), a time-of-day grade, and its
> own animation clock independent of the sim loop. It installs as a pure
> `SemRenderer.post_compositor`, so Channel A is never altered and the layer is
> fully reversible (`View ▸ Story · Day in the Life`). Hi-res
> (`cellauto/hires.py`) decouples render from display resolution:
> `View ▸ Render scale` supersamples the live canvas 1×/2×/3× and
> `File ▸ Export hi-res PNG…` writes a composed frame up to 4K. The narrative
> art bundle + smoke test lives at `tools/render_narrative_art.py`. The
> simulation engine, constants, and snapshot format remain unchanged.

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
  `abiogenesis-pipeline-extended` (now 13 stages, incl. Stage XIII digital
  life). G1 is **closed**: promotion hands state across stages via
  `extract_signal`/`seed_field`, so the pipeline is a coupled narrative
  (verified 2026-06-03, spatial corr ≈ 0.99). *(Stale "until G1 is closed"
  wording corrected — see review REV-15.)*
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

## 6. v4.0 — SEM-grade visualization cycle (v4.0.0a1 SHIPPED)

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

**v4.0.1 status.** Phases 1 + 2 of the cycle have shipped: S1, S2, S3,
S4, S5, S6, S8, S9, S12 are closed. The alpha designation has been lifted.
Phase 1 (v4.0.0a1) delivered `cellauto/renderer_sem.py` as the depth-shaded
numpy rasteriser with warm-sepia + cool-mono palettes, `View ▸ SEM mode`
toggle and palette picker, persistence via `~/.cellauto/config.json`, LIVE
SEM FEED badge / scale bar / vignette / crosshair framing, the Stage 1
hero pass, Pillow-LANCZOS fallback, regression test pins, and the v4.0
documentation. Phase 2 (v4.0.1) added the sprite-compositing layer in
`SemRenderer.compose(..., sprites=...)`, the `load_sprite()` / `set_sprite_dir()`
helpers, sprite assets at `cellauto/assets/sprites/` (generated by
`tools/render_sprites.py`), and per-stage `render_sprites()` methods on
`AbiogenesisStage1GrayScott` (local-max v-field peaks) and
`AbiogenesisStage3Vesicles` (connected-component centroids).
158 / 158 tests pass; ruff + mypy clean; the wheel ships sprite assets and
installs cleanly into a fresh site-packages. Stage 0 sprites are in the
asset library but not yet wired (Stage 0 runs through `DiscreteRenderer`,
which is v4.0.2 work). The remaining deferred items (S7 — full 12-stage
sprite catalogue, S10 — GPU, S11 — AI refinement) are tracked below.

### Punchlist (open until each phase ships)

- [x] **S1 — `SemRenderer` core (Phase 1).** New module
  `cellauto/renderer_sem.py` implementing the depth-shaded numpy
  rasteriser: height-field → gradients → normals → Lambertian +
  ambient + specular shading → procedural noise overlay → sepia /
  mono LUT → LANCZOS upscale → vignette + crosshair + scale-bar
  overlay. Same `render(state)` signature as `FieldRenderer` so app.py
  stays agnostic. Target: 20 FPS @ 60×60 grid on CPU.
- [x] **S2 — Palette modes.** `warm-sepia` (matches the reference image)
  and `cool-mono` (extends the existing Catalytic Silence palette into
  3-D shading). Picker under `View ▸ SEM palette`. Both verified
  colourblind-safe via `colorspacious`.
- [x] **S3 — `View ▸ SEM mode` toggle.** Checkbox flips between
  viridis (legacy v3.6) and SEM rendering. Persists in the existing
  config (`~/.cellauto/config.json` via `_load_sem_config()` /
  `_save_sem_config()` in `cellauto/app.py`). Both render paths share
  step counts on the same seed (regression-pinned).
- [x] **S4 — Instrument framing.** Centred crosshair reticle (1-px
  hairline teal), "LIVE SEM FEED · Stage N — name" microcaps badge
  upper-right, scale-bar microcopy below the canvas, ~10 % corner
  vignette. Pulse-syncs the badge opacity with the v3.6 playback dot;
  reduced-motion mode freezes the pulse.
- [x] **S5 — Stage 1 hero pass.** Stage 1 (Gray-Scott) under SEM mode
  reads as the reference image; the hero shots are committed at
  `docs/generated/sem_stage1.png` (warm-sepia) and
  `docs/generated/sem_stage1_cool-mono.png`, with the v3.6 viridis
  baseline at `docs/generated/viridis_stage1.png` for the README
  before/after plate.
- [x] **S6 — Sprite library, stages 0 / 1 / 3 (Phase 2).** Sprite
  compositing wired into `SemRenderer.compose(..., sprites=...)` via the
  new `load_sprite()` / `composite_sprites()` helpers. Stage 1 (Gray-Scott)
  and Stage 3 (vesicles) both ship `render_sprites(state)` emitters and
  hero shots at `docs/generated/sem_stage{1,3}_sprites*.png`. Sprite
  assets at `cellauto/assets/sprites/{stage0,stage1,stage3}/*.png`,
  generated deterministically by `tools/render_sprites.py` and shipped in
  the wheel via `[tool.setuptools.package-data]`. 8 sprite-layer pins in
  `tests/test_sem_sprites.py`. **Stage 0 sprites** (granule + protocell)
  are in the library but not yet wired into the app — Stage 0 runs through
  `DiscreteRenderer`; routing SEM-aware rendering through the discrete
  path is v4.0.2 work.
- [ ] **S7 — Full stage catalogue (Phase 3).** Sprite library extended
  to all 12 stages of the extended pipeline. `docs/generated/sem_<stage>.png`
  committed for each. *Deferred to v4.0.1+.* Depends on S6.
- [x] **S8 — Graceful fallback (F6).** If Pillow / numpy / Tk capability
  detection fails (notably Pillow without LANCZOS), drop to v3.6 viridis
  rendering with a one-time toast explaining why. No crashes.
- [x] **S9 — Regression tests.** `tests/test_sem_renderer.py` ships
  ≥ 8 SEM pins:
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
  CPU path (golden-image regression). *Deferred to v4.0.1+.* The
  Phase-1 CPU rasteriser hits the 20 FPS @ 60×60 budget; GPU is for
  the larger grids that arrive with the sprite library.
- [ ] **S11 — Stretch: AI image-to-image refinement (Phase 5).**
  `tools/sem_refine.py` runs SEM output through a fine-tuned diffusion
  model at strength 0.35 for hero-shot quality. `File ▸ Export refined
  PNG…` menu entry. Slow, opt-in, never the default. *Deferred to
  v4.0.1+.* Stretch goal — gated on the sprite library landing first
  so the input to refinement is already representationally faithful.
- [x] **S12 — Documentation.** README + CHANGELOG carry a before/after
  comparison plate (`docs/generated/viridis_stage1.png` →
  `docs/generated/sem_stage1.png` / `sem_stage1_cool-mono.png`).
  `docs/science.md` carries a new section noting that SEM mode is
  purely a rendering choice; the underlying physics is unchanged.

## §6a — Brutal-feedback audit findings (v4.0.5)

A multimodal whipgen-claude critique loop (four rounds, fed live SEM
renders + the renderer source each time) drove twelve concrete deltas.
All shipped in v4.0.5; reference shots at `docs/generated/audit/`.

- [x] **V1** — flip substrate height-sign so v-peaks render as domes not craters.
- [x] **V2** — disable the Stage 1 sprite layer (the v4.0.1 sprites read as floating "strange balls" stickers).
- [x] **V3** — round-1 MCP verification.
- [x] **B1** — sparsify Stage 1 init_state to Poisson-disk scatter of 6-10 seed patches (was a single central perturbation that tiled to carrying capacity).
- [x] **B3** — Voronoi (F2-F1 cellular) substrate noise mixed 50/50 with value-noise for fine salt-crystal grain on a smooth bed.
- [x] **B4** — non-linear height remap (`np.where(h>0.15, 0.15+(h-0.15)*2.5, h*0.3)`) crushes substrate range, stretches dome range.
- [x] **B5** — `_contact_shadow` ramp-darkening in the foot-ring band (post-R4 thresholds 0.18–0.45) anchors raised features to the substrate.
- [x] **B6** — `_build_lut(stops, gamma=2.2)` gamma-biased LUT mapping; substrate lands in dark stops 0-1, apices reach bone-cream stops 4-5.
- [x] **B7** — `_sprinkle_pink_variety` tints ~0.8% of top-quartile (q92+) intensity pixels toward dusty pink for Miller-Urey colour variety.
- [x] **R5** — `specular_hardness` 24 → 12 widens the specular spot; kills the apex horizontal-slash artifact.
- [x] **R7** — Lambertian un-gated (only specular is height-gated); restores dome flank body without re-brightening substrate.
- [x] **R8** — `height_bias_exponent` 1.6 → 1.2 softens the apex hotspot from a hard speck to a curved highlight.

Out of scope for the audit cycle (subsequent versions):

- [x] **B8** — sprite tint + contact-shadow fix for the asset compositing
  path. **Shipped v4.0.9.** Kept disabled for Stage 1 (depth-shaded substrate
  alone is the hero — see V2); re-enabled for Stage 0 via `sem_eligible`
  opt-in + SEM-on-discrete-renderer routing, with a sparse protocell-body +
  granule-scatter sprite set that avoids the "wall of balls". See §6c.
- [x] **Stage 3 vesicle audit** — confirmed B1-B8 did NOT regress Stage 3
  (lipid-bilayer rule). v4.0.8: Stage 3 under SEM mode composes a rich
  depth-shaded image (variance ≈ 3.7 k, 6.4 k unique colours, 398 membrane
  cells). Closed as item A4 in §6b.

## §6b — Brutal full-app review (v4.0.8)

A ground-up audit asked the question the user posed: *what is documented as
complete but only partially built, or just documented?* The dominant finding
was that the apparatus / "How it works" / connected-narrative feature
(E1/E3/E4, shipped v4.0.6–v4.0.7) was complete for the canonical 5-stage
pipeline but **silently degraded for 7 of the 12 stages** of the extended
pipeline — plus a latent correctness bug in the diagram dispatch. All resolved
in v4.0.8. 158/158 tests green, ruff + mypy clean.

- [x] **A1 — extended `StageInfo` metadata.** The 7 extended-only entries
  (`_STAGE_VENT_INFO`, `_STAGE_MINERAL_INFO`, `_STAGE_CHIRALITY_INFO`,
  `_STAGE_RNA_INFO`, `_STAGE_CODE_INFO`, `_STAGE_COACERVATE_INFO`,
  `_STAGE_LUCA_INFO`) left all 7 v4.0.6 fields empty, so "How it works" showed
  "(not yet documented…)" and chapter cards had no narrative line for them.
  Populated from `docs/science.md`; each `control` keyed to the real knob/stat
  the rule exposes.
- [x] **A2 — apparatus dispatch correctness bug.** `render_apparatus(info.index)`
  collided: extended `StageInfo.index` reuses canonical indices, so the vent
  (index=1) rendered the Gray-Scott reactor and minerals (index=3) rendered the
  CMC bilayer. Re-keyed dispatch on each rule's unique `name`
  (`_RENDERERS_BY_RULE_NAME` now maps all 12 abiogenesis rules);
  `_show_how_it_works` passes `engine.state.inner_rule.name`. All 12 stages now
  resolve to the correct diagram.
- [x] **A3 — 6 missing apparatus diagrams.** Added `render_mineral_clay`,
  `render_homochirality`, `render_rna_world`, `render_genetic_code`,
  `render_coacervate`, `render_luca` (Catalytic Silence grammar, control-footer
  caption, grounded in `docs/science.md`). Reference shots at
  `docs/generated/audit/apparatus_{minerals,chirality,rna,code,coacervate,luca}.png`.
- [x] **A4 — Stage 3 vesicle SEM regression check** (closes the deferred §6a
  Stage 3 audit). No regression — see above.

Confirmed-deferred (documented future work, *not* partial gaps): S7 (full
12-stage sprite catalogue), S10 (GPU path), S11 (AI refinement). The 5 shared
canonical `StageInfo` entries keep canonical-neighbour `consumes`/`produces`
prose; per-pipeline narrative override is a v4.1 nicety. *(E2 and B8, listed
here as deferred in v4.0.8, were both shipped in v4.0.9 — see §6c.)*

## §6c — Closed the last two deferred punchlist items (v4.0.9)

The two items carried as "confirmed-deferred" in §6b — **E2** and **B8** — are
both shipped, verified by reading the actual rendered output (not assertions
alone). 262/262 tests green, ruff + mypy clean.

- [x] **B8 — SEM sprite tint + contact shadow + Stage 0 re-enable.**
  `load_sprite` ramps sprites through the palette LUT (`black=lut[110]`,
  `white=lut[250]`) so opaque pixels floor at a mid stop instead of pure black;
  alpha pulled to 0.9; `composite_sprites` lays a blurred down-right contact
  shadow. Stage 0 opts into the SEM field renderer (`sem_eligible=True`, gated
  so the discrete path is byte-identical when SEM is off) and emits a *sparse*
  sprite set — ≤5 spatially-spread protocell bodies + ≤26 granule specks —
  fixing the naïve "one sprite per `is_ameba` cell" wall-of-balls (≈90% of the
  grid is `is_ameba`). Stage 3 vesicles verified unregressed.
- [x] **E2 — control-experiment A/B view.** `render_control` + 12 null-experiment
  panels mirror the apparatus diagrams (struck-through driver, null outcome,
  shared `_control_plate` grammar). "How it works" embeds EXPERIMENT | CONTROL
  side-by-side. Diagrams are rendered at native 640×320 and image-downscaled
  into the embed box to avoid clipping non-reflowing text; four renderers that
  crashed/clipped at narrow widths (`render_rna_world`, `render_coacervate`,
  `render_homochirality`, `render_genetic_code`) were made size-robust
  (fractional coords + clamps) with parametrized tests.

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

---

## 7. v4.2 — Full-application review closure (REV-*) — CURRENT punchlist

A full-application review on **2026-06-03** (build v4.1.1) audited engine, GUI,
web, tests/CI, docs, and assets; verified every headline claim against running
code + rendered output; and confirmed the load-bearing science against the
literature (Helfrich κ≈10⁻¹⁹ J, Eigen ε_c≈ln σ/L, Wood-Ljungdahl ΔG°′≈−95 kJ/mol
all check out). Write-up + screenshots: **[docs/review/APPLICATION_REVIEW_v4.1.md](review/APPLICATION_REVIEW_v4.1.md)**;
all 36 issues with evidence + fix direction: **[docs/review/ISSUE_REGISTER.md](review/ISSUE_REGISTER.md)**.

Headline: the cited science is accurate; debt is in claim-vs-code overreach,
doc drift, test/CI hygiene, one Tk-coupled test failure, and web
canonicalisation. **0 blocker · 11 major · 25 minor.**

### P0 — honest-green + brand-risk (do first)
- [ ] **REV-01** Decouple SEM-config I/O from `tkinter` so the suite is green headless (red without Tk today; CI passes only because ubuntu ships Tk).
- [ ] **REV-08/09/10/15** Close the 3 overclaims with prose: science.md Stage-4 fitness (entropy → hypercycle ODE + proxy); soften "Helfrich real"; LUCA "core = invariant" + 6→12 *(done)*; drop the non-existent `inherit_from` wording *(done)*.
- [ ] **REV-11** Author Stage XIII `_STAGE_LIFE_INFO` (7 fields) so the flagship stage has "How it works" + chapter card.
- [ ] **REV-02** Genetic-code: implement the donor-code-compatibility gate the docstring claims, or downgrade the prose.

### P1 — doc reconciliation (mostly mechanical)
- [ ] **REV-12** PRD.md status banner + repoint dead `PHASE2_BRUTAL.md` links *(banner applied)*.
- [ ] **REV-13/16** Create or repoint `docs/PRD_LAB_EXPERIMENTS.md` and `PHASE2_BRUTAL.md`.
- [x] **REV-14/17** Counts reconciled and the drift-prone one locked: the canonical stage count (13) is now derived from `len(EXTENDED_STAGE_CLASSES)` and pinned to the README by `tests/test_stage_count.py`. Brittle test/coverage numbers were removed from current-state prose (they belong in CI output, not docs); dated changelog entries were left intact.
- [ ] **REV-29** Register `abiogenesis-life` in `rules/__init__.py`, or document the deliberate exclusion.

### P2 — web canonicalisation
- [ ] **REV-18** Port `stage_minerals.py` → `experiment/rules/minerals.js` (today it's a Gray-Scott stand-in).
- [ ] **REV-19** Gate web2/web3 smokes in CI, or declare them frozen-legacy and remove.
- [ ] **REV-20/21/22/23** web4→web6 rename; railway healthcheck `/web6/`; vendor Three.js; update web2/web3 PUNCHLISTs.

### P3 — tests / CI / UX hygiene
- [ ] **REV-04/05/06/07** De-tautologise tests; add `test_life_sem.py`; cover `tutorial.py`/`params.py`; pin published constants.
- [ ] **REV-33/34/35/36** Pin action versions consistently + bump node; raise coverage gate to ~88; audit the installed env; mypy `--disallow-untyped-defs` + add py3.13.
- [ ] **REV-24/25/26/27/28** UX: stop-before-export + non-modal panels; transport above the fold; toast for the plate-not-found error; menu/state gating; polish.
- [ ] **REV-30/31/32** Delete dead `_v401_sprites`; align genetic-code `render_cell` with `render_rgb`; fix `_division_site` docstring.
