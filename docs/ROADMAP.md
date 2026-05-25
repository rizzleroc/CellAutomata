# cellauto — Feature Inventory, Honest Status & Roadmap

This document is the project's **regression guard** and its **honest
self-status**. Before shipping any change, check the Feature Inventory
— nothing listed should silently disappear. Cross-reference status
against [`PUNCHLIST.md`](PUNCHLIST.md) for the active work cycle.

Last updated: 2026-05-24 (post brutal-audit pass).

> ⚠ **Audit note:** A consolidated brutal honesty audit lives at
> [`PUNCHLIST.md`](PUNCHLIST.md). This roadmap has been updated to
> reflect the audit's findings — items previously listed as "shipped"
> that turned out to be partial implementations are now marked
> accordingly (✅ real / ◻ toy-with-real-concept / ⚠ overclaim).

---

## 1. Feature Inventory (must not regress)

### Simulation science — by honest classification

**Real implementations (would survive a domain-expert review):**

- ✅ **Conway** (B3/S23, Gardner 1970). Textbook.
- ✅ **Wolfram 1D** (elementary CA, Wolfram 2002). Textbook.
- ✅ **Gray-Scott reaction-diffusion** (Pearson 1993). Canonical
  forward-Euler PDE, 5-pt Laplacian, CFL-stable, Pearson's preset
  table verbatim. `stage1_grayscott.py`.
- ✅ **Frank homochirality** (Frank 1953). Real 2D reaction-diffusion
  Frank model with autocatalysis + mutual antagonism.
  `stage_chirality.py`.
- ✅ **Cahn-Hilliard coacervates** (Oparin 1924; Cahn-Hilliard 1958).
  Correct conservative discretisation, Ostwald ripening emerges.
  `stage_coacervate.py`.
- ✅ **Hordijk-Steel RAF closure** (Hordijk & Steel 2004). The
  *correct* layered closure with mandatory catalysis. Fixes a v3.1
  false-positive bug; regression test pins the fix. `science.py
  find_raf`.
- ✅ **Spatial Eigen RNA quasispecies** (Eigen 1971; Gilbert 1986).
  Per-base mutation, single-peak fitness, ε_c = ln(σ)/L threshold.
  Spatial Moran dynamics (not the Eigen ODE), but the error-catastrophe
  transition is real and tested. `stage_rna.py`.

**Real-concept toys (the concept is honest, the implementation is
phenomenological — usable as educational visualization, not as a
substitute for the cited model):**

- ◻ **Stage 0 primordial soup** — Miller-Urey-weighted initial
  distribution (real data) over a random Moore-neighbor color
  propagation rule (toy chemistry). `stage0_soup.py` /
  `natural_selection.py`.
- ◻ **Stage 2 RAF dynamics** — RAF *detection* is real; the on-grid
  *firing* is generic mass-action A+B→C with a catalyst multiplier.
  No stoichiometry, no conservation. The narrative "RAFs ignite"
  qualitatively holds. `stage2_raf.py`.
- ◻ **Alkaline vents** — Two-domain proton field + diffusion +
  gradient-magnitude-coupled synthesis. PMF (mV) and ΔG (kJ/mol)
  readouts are *thermodynamically correct* (Nernst, Faraday).
  ⚠ The synthesis rate uses `|∇H|`, not the ΔG. See
  [`PUNCHLIST.md`](PUNCHLIST.md) P1-4. `stage_vents.py`.
- ◻ **Mineral catalysis** — Static clay-disc mask gates a first-order
  monomer→polymer rate. Polymer is a scalar, not a length distribution.
  Qualitative localization claim does hold. `stage_minerals.py`.
- ◻ **LUCA distillation** — Per-cell genome bitset with per-gene
  additive fitness + 70% prevalence threshold. Gene names are labels;
  the fitness values are hand-tuned. The "luca_size converges to
  essential_target" claim does hold numerically. `stage_luca.py`.

**Overclaim — needs to be fixed or recanted (see PUNCHLIST Tier 1):**

- ⚠ **Stage 3 lipid vesicles** — Gray-Scott on a relabeled field.
  `AMPHIPHILE_CMC_MM` is a display string; the simulation ignores
  it. ([PUNCHLIST P1-1](PUNCHLIST.md))
- ⚠ **Stage 4 protocell selection** — File's own docstring admits
  "scalar proxy, not the hypercycle". The Eigen `error_threshold`
  is shown but doesn't gate any dynamic. ([PUNCHLIST P1-2](PUNCHLIST.md))
- ⚠ **Genetic-code coevolution** — VWG 2006's central mechanism
  (horizontal gene transfer between lineages with similar codes) is
  *not implemented*. Only vertical mutation. ([PUNCHLIST P1-3](PUNCHLIST.md))
- ⚠ **12-stage pipeline narrative** — Each stage re-inits from scratch;
  no chemical carry-over between stages. ([PUNCHLIST P1-5](PUNCHLIST.md))

### Engine & reproducibility

- ✅ Deterministic from `--seed`, including across save/load
  (RNG state serialized).
- ✅ Stage 2 RAF serializes its full reaction network so resumed runs
  use the same chemistry.
- ✅ Headless `simulate` and `export` subcommands.
- ⚠ Snapshot load uses `pickle.loads()` on user-supplied data
  — RCE on the public Railway URL.
  See **[PUNCHLIST P0-1](PUNCHLIST.md)**. Fix this week.
- ◻ Snapshot writes `version: 2` but never reads it on load.
  ([PUNCHLIST P2-5](PUNCHLIST.md))

### GUI (Tk, "Catalytic Silence" museum aesthetic)

- ✅ All mandated controls present (transport, stage nav, parameters,
  observation, export, pedagogy, accessibility — see §3).
- ⚠ **Visual identity only fully ships on Windows** — bundled
  Cormorant/Plex fonts are registered via `gdi32` on Windows and
  fall back to system serifs on Linux/macOS.
  ([PUNCHLIST P2-3](PUNCHLIST.md))
- ⚠ `cellauto/app.py` is 2121 lines on one class, 0% coverage by
  design. Dispatch logic for pipeline vs. standalone rules is
  duplicated 5× across methods. ([PUNCHLIST P2-1](PUNCHLIST.md))
- ◻ About dialog still says "five stages" — predates the 12-stage
  extended pipeline. ([PUNCHLIST P3-6](PUNCHLIST.md))

### Web sandbox

- ✅ Flask server + vanilla-JS frontend; per-session `threading.Lock`
  with a real lock-identity test (`test_web.py`).
- ✅ Hard caps on grid (≤240), steps-per-request (≤50), GIF steps
  (≤240), sessions (≤64). LRU eviction.
- ✅ Deploys via Dockerfile + railway.toml; `/api/health` endpoint;
  public URL at https://cellautomata-production.up.railway.app/.
- ⚠ **RCE via `pickle.loads(user_input)` on `/api/sessions/<sid>/load`.**
  ([PUNCHLIST P0-1](PUNCHLIST.md))

### Tests & CI

- ✅ 147 tests pass (README says "120" — stale by 27).
- ✅ Tests pin *quantitative* scientific claims, not just smoke:
  RAF closure correctness, Eigen ε_c transition, LUCA convergence,
  Cahn-Hilliard coarsening, Frank symmetry breaking.
- ◻ "87% coverage" reflects the science layer only — ~55% of total
  Python LOC (GUI + web + CLI + renderer) is omitted from coverage
  measurement. ([PUNCHLIST P4-3](PUNCHLIST.md))
- ◻ `pip-audit` audits only Pillow + numpy (the contents of
  `requirements.txt`); Flask, gunicorn, pytest, etc. are not audited.
  ([PUNCHLIST P4-1](PUNCHLIST.md))
- ◻ One tautological test (`test_protocol::test_every_rule_can_init_state_and_step`).
  ([PUNCHLIST P2-6](PUNCHLIST.md))

### Documentation

- ✅ `docs/science.md` has an "Honest limitations" section that
  acknowledges toy time scales, no real thermodynamics, phenomenological
  constants — more honest than the README hero copy.
- ⚠ README hero claim ("every constant traces to a published
  measurement") is CHARITABLE. ([PUNCHLIST P3-7](PUNCHLIST.md))
- ⚠ README test count stale (120 → 147). ([PUNCHLIST P3-1](PUNCHLIST.md))
- ⚠ Extended-pipeline tutorial copy enumerates 10 stages; code has 12.
  ([PUNCHLIST P3-2](PUNCHLIST.md))
- ⚠ Four broken references to a non-existent `PHASE2_BRUTAL.md`
  self-audit document. ([PUNCHLIST P3-4](PUNCHLIST.md))
- ⚠ `tools/render_aaa_visuals.py` and `docs/design/render_prima_materia.py`
  hardcode `C:/Users/guru8/...` paths — render scripts crash on any
  machine but the author's. ([PUNCHLIST P3-5](PUNCHLIST.md))

---

## 2. Active work cycle (linked to PUNCHLIST.md)

### Tier 0 — Security · ship this week

- [ ] **P0-1** Replace `pickle.loads(user_input)` in snapshot load
  with a JSON-safe `Random.getstate()` round-trip. Bump snapshot
  format to v3. Add regression test that a malicious pickle payload
  no longer executes.

### Tier 1 — Scientific honesty (close or recant)

For each item below, pick path A (real implementation) or path B
(re-frame in README/docstring/tutorial). Both are honest. Mixing
"keep marketing, ship toy" is what got us here.

- [ ] **P1-1** Stage 3 vesicles — either implement real lipid physics
  (curvature term + amphiphile-specific CMC coupling) or rewrite
  README/docstring to disclose it's a Gray-Scott proxy.
- [ ] **P1-2** Stage 4 selection — either integrate a minimal
  hypercycle ODE *or* make the displayed `error_threshold` actually
  gate dynamics *or* rename to "fitness-driven selection (cyclic-
  coupling proxy)".
- [ ] **P1-3** Genetic-code — implement VWG horizontal gene transfer
  (best path; ~80 lines), or re-label.
- [ ] **P1-4** Vent — couple synthesis rate to ΔG (not `|∇H|`), or
  re-label `−95 kJ/mol` as a "thermodynamic envelope display".
- [ ] **P1-5** Pipeline carry-over — implement product-bias seeding
  between stages (multi-week), or change "walks every major origin-
  of-life process" to "tours / exhibits" in README + tutorial.

### Tier 2 — Engineering quality

- [ ] **P2-1** Decompose `app.py` god-object (Recorder / Timeline /
  Stats / Gallery into their own modules; put under coverage).
- [ ] **P2-2** Vectorize the per-cell Python loops in RNA / LUCA /
  code (~10× speedup expected).
- [ ] **P2-3** Make Catalytic Silence fonts register on Linux/macOS.
- [ ] **P2-4** Skip wasteful `init_state` call in `Engine.__post_init__`
  when `Engine.load` will overwrite.
- [ ] **P2-5** Read snapshot `version` field on load (enables future
  schema migrations).
- [ ] **P2-6** Replace tautological `test_protocol` smoke with real
  shape/monotonicity invariants per rule.
- [ ] **P2-7** Fix canvas-click 2-px borderwidth offset.
- [ ] **P2-8** Vectorize discrete-rule `_capture_frame` for GIF
  export at large grids.

### Tier 3 — Documentation drift

- [ ] **P3-1** Update README test count (or replace with badges).
- [ ] **P3-2** Update extended-pipeline tutorial to enumerate all 12
  stages.
- [ ] **P3-3** Update `--stage` CLI help to reflect 0-11 range.
- [ ] **P3-4** Decide on `PHASE2_BRUTAL.md`: restore or replace refs
  with links to `PUNCHLIST.md`.
- [ ] **P3-5** Fix hardcoded Windows font paths in render scripts.
- [ ] **P3-6** Update About dialog to mention extended pipeline.
- [ ] **P3-7** Soften README "every constant traces to a published
  measurement" to match `docs/science.md`'s caveats.

### Tier 4 — CI / build hygiene

- [ ] **P4-1** Audit the full resolved environment, not just `requirements.txt`.
- [ ] **P4-2** Drop `mypy --no-error-summary`; add `--strict` continue-on-error job.
- [ ] **P4-3** Add a non-omitted coverage job at a lower threshold OR
  explain the headline number in the README.

---

## 3. Mandated GUI controls (regression contract — all shipped)

The simulator is not considered complete unless every control here is
present and working. `[x]` = shipped, `[ ]` = owed.

**A. Run control / transport**
- [x] Play / Pause, Step, Stop
- [x] Speed (FPS) control
- [x] Reseed, Restart-to-step-0
- [x] Step-back / timeline scrubber (bounded ring buffer; truncate-future on edit)

**B. Stage navigation**
- [x] Rule selector (each stage individually + pipelines)
- [x] Grid-size selector
- [x] Promote stage (manual)
- [x] Jump-to-stage picker
- [x] Auto-promote toggle + duration

**C. Scientific parameters**
- [x] Live parameter sliders for each stage's live-applicable knobs
- [x] Pearson regime preset picker for Gray-Scott
- [x] Structural parameters with auto re-init (`reinit=True` flag)
- [x] Reset-parameters-to-defaults button

**D. Observation, legends & plots**
- [x] Main simulation canvas
- [x] Live stage caption + colour legend
- [x] Visual colorbar (viridis) for field stages
- [x] Fitness key (red→green or CVD-safe blue→yellow) for Stage 4
- [x] Reaction-network / RAF graph view (Gallery)
- [x] Population sparkline overlay

**E. Data & export**
- [x] Save / Open snapshot (JSON, exact round-trip) ⚠ (P0-1: pickle path needs replacement)
- [x] Export GIF (threaded, progress + cancel)
- [x] Export current frame as PNG
- [x] Export run statistics as CSV

**F. Pedagogy & information**
- [x] Tutorial walkthrough with citations
- [x] Per-stage principle + citations (marginalia on transition)
- [x] Chapter-card overlay on stage promotion
- [x] Gallery of museum plates (5 stage heroes + composite posters)
- [x] About dialog ⚠ (P3-6: mentions only 5 stages, not 12)
- [x] Status register (rule / seed / step / FPS / population stats)

**G. Accessibility**
- [x] Colourblind-safe palette toggle (View menu)
- [x] Text-scaling / zoom (View menu, four presets)
- [x] Keyboard navigation (Space / → / R / P / [ / ]) with text-entry guard

---

## 4. Web sandbox (the parallel deliverable)

The Python desktop GUI ships alongside two web artifacts:

- ✅ **`cellauto web`** — Flask + vanilla JS, every rule playable in
  any browser. Per-session lock, hard caps, snapshot/PNG/GIF download.
  Deploys via the bundled Dockerfile / `railway.toml`. ⚠ Pickle RCE in
  snapshot load (P0-1).
- ✅ **`docs/web/`** — Static JS Gray-Scott explorer, deployable to
  GitHub Pages from `/docs`. Vanilla JS port of `gray_scott_step`,
  identical math to Python. Stage 1 only.

---

## 5. How to use this doc

- **Adding a feature?** Add it to the Feature Inventory under the
  honest classification (✅ / ◻ / ⚠).
- **Starting work?** Pick an item from the Active Work Cycle and
  link it to a PUNCHLIST entry.
- **Shipping?** Re-read the Feature Inventory and confirm nothing
  regressed; add a CHANGELOG entry; update PUNCHLIST status; do not
  silently bump claim severity.
- **Disagreeing with an audit verdict?** Open a PR that either fixes
  the gap or rewrites the marketing. Both are honest. Stale
  marketing + toy implementation is what this doc exists to prevent.
