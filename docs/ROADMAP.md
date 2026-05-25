# cellauto — Feature Inventory, Honest Status & Roadmap

This document is the project's **regression guard** and its **honest
self-status**. Before shipping any change, check the Feature Inventory
— nothing listed should silently disappear. Cross-reference status
against [`PUNCHLIST.md`](PUNCHLIST.md) for the active work cycle.

Last updated: 2026-05-24 (post brutal-audit pass — **all 19 punchlist
items closed or de-scoped** in v3.5).

> ⚠ **Audit note:** A consolidated brutal honesty audit lives at
> [`PUNCHLIST.md`](PUNCHLIST.md). This roadmap has been updated to
> reflect the audit's findings — items previously listed as "shipped"
> that turned out to be partial implementations are now marked
> accordingly (✅ real / ◻ toy-with-real-concept / ⚠ overclaim).
>
> **v3.5 cycle (2026-05-24):** All 19 PUNCHLIST items addressed.
> Closed outright: P0-1, P1-3, P1-4, P2-2..P2-8, P3-1..P3-7, P4-1..P4-3
> (15 items). Honestly re-framed where the real implementation was
> out-of-scope: P1-1, P1-2 (path C — gating added but no full
> hypercycle ODE), P1-5 (path B — "tours" not "walks"). Partial: P2-1
> (active_rule/active_state factored; full app.py decomposition is
> on the v4 roadmap).

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

**Previously-overclaimed, now closed in v3.5 (see PUNCHLIST Tier 1):**

- ◻ **Stage 3 lipid vesicles** — still Gray-Scott on a relabeled field,
  but docstring / tutorial / README now disclose this honestly. Real
  lipid-physics implementation deferred. ([PUNCHLIST P1-1](PUNCHLIST.md))
- ◻ **Stage 4 protocell selection** — fitness is still a cyclic-coupling
  proxy, but the Eigen `error_threshold` now actually **gates mutation
  drift** — above ε_c the genome melts (visible via the new
  `error_catastrophe` population stat, pinned by regression test).
  ([PUNCHLIST P1-2](PUNCHLIST.md))
- ✅ **Genetic-code coevolution** — VWG 2006's horizontal gene
  transfer between similar-coded cells is now implemented; an
  `hgt_rate` slider lets you toggle it off as a vertical-only
  control. Regression test pins HGT-vs-vertical convergence.
  ([PUNCHLIST P1-3](PUNCHLIST.md))
- ✅ **Vent** — synthesis rate now scales with local free-energy
  availability (per-cell ΔG), not just `|∇H|`. Reversing the
  gradient (alkaline outside / acidic inside) makes ΔG positive
  and synthesis vanishes. Regression test pins this.
  ([PUNCHLIST P1-4](PUNCHLIST.md))
- ◻ **12-stage pipeline narrative** — each stage still re-inits from
  scratch (no chemical carry-over), but README / tutorial copy now
  honestly call this a "curated slideshow" / "tours" rather than
  "walks every process". Real continuity work is on the roadmap.
  ([PUNCHLIST P1-5](PUNCHLIST.md))

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

### Tier 0 — Security

- [x] **P0-1** Replaced `pickle.loads(user_input)` in snapshot load
  with a JSON-safe `Random.getstate()` round-trip. Snapshot format
  bumped 2 → 3. Regression tests pin both the structural validation
  and an actual RCE-attempt-doesn't-execute scenario.

### Tier 1 — Scientific honesty

- [x] **P1-1** Stage 3 vesicles — re-framed as "concentration-regime
  proxy" in docstring + tutorial + README; CMC table acknowledged as
  readout-only. Real lipid-physics implementation deferred (v4).
- [x] **P1-2** Stage 4 selection — `error_threshold` now gates
  mutation drift (above ε_c the genome melts); new `error_catastrophe`
  population stat; three regression tests. Full hypercycle ODE
  deferred (v4).
- [x] **P1-3** Genetic-code — VWG horizontal gene transfer
  implemented (`hgt_rate`/`hgt_similarity_threshold` knobs in
  PARAM_SPECS + on the rule); regression test shows HGT-vs-vertical
  convergence delta.
- [x] **P1-4** Vent — synthesis rate now coupled to local free-energy
  factor; reversing the pH gradient zeroes synthesis. Regression
  test pins this.
- [x] **P1-5** Pipeline narrative — README + tutorial + rule cards
  re-framed as "tours" / "curated slideshow"; explicit no-carry-over
  caveat. Real chemical continuity is a v4 roadmap item.

### Tier 2 — Engineering quality

- [◻] **P2-1** `app.py` god-object — *partial*. `active_rule` /
  `active_state` properties extracted to `Engine`, eliminating the
  duplicated `getattr(state, "inner_rule", None) or rule` pattern.
  Full Recorder/Timeline/Stats extraction → v4.
- [x] **P2-2** Per-cell Python loops in RNA / LUCA / code rules
  vectorised via per-call numpy `Generator` seeded from `self.rng`.
  ~2-3× speedup measured.
- [x] **P2-3** Catalytic Silence fonts now best-effort install on
  Linux (`~/.local/share/fonts/cellauto/` + `fc-cache`) and macOS
  (`~/Library/Fonts/cellauto/`).
- [x] **P2-4** `Engine.load` uses `cls.__new__` + manual init to
  skip the wasteful `rule.init_state` call.
- [x] **P2-5** Snapshot schema `version` field now read on load
  (rolled into P0-1).
- [x] **P2-6** `test_protocol.py::test_every_rule_can_init_state_and_step`
  rewritten — asserts non-empty Mapping[str, number] population,
  step advances, render_rgb returns (H, W, 3) uint8.
- [x] **P2-7** Canvas-click 2-px borderwidth offset fixed.
- [x] **P2-8** Discrete-rule frame capture (web GIF export) now uses
  `render_rgb` for every rule — eliminates 57k Python calls per
  240² frame.

### Tier 3 — Documentation drift

- [x] **P3-1** README test-count number removed (was "120", actual
  151+); replaced with "Test suite passes in CI on the matrix".
- [x] **P3-2** Extended-pipeline tutorial copy enumerates all 12
  stages with the no-carry-over caveat.
- [x] **P3-3** `--stage` CLI help reflects 0-4 / 0-11 ranges.
- [x] **P3-4** Four broken refs to `PHASE2_BRUTAL.md` replaced with
  links to `docs/PUNCHLIST.md` (this is now the self-audit doc).
- [x] **P3-5** Hardcoded `C:/Users/guru8/…` font paths in render
  scripts replaced with `Path(__file__).resolve().parents[N] /
  "cellauto" / "assets" / "fonts"`.
- [x] **P3-6** About dialog now mentions both pipelines (5 + 12).
- [x] **P3-7** README "Every constant traces to a published
  measurement" softened to match `docs/science.md`'s caveats.

### Tier 4 — CI / build hygiene

- [x] **P4-1** `pip-audit` now installs `.[web,dev]` and audits the
  full resolved environment.
- [x] **P4-2** Dropped `mypy --no-error-summary`; added advisory
  `mypy --strict` continue-on-error job.
- [x] **P4-3** README "87% coverage" annotated to clarify it's the
  science layer only; pytest CI step has a comment + PUNCHLIST link.

### Carried forward to v4 roadmap

- Full `cellauto/app.py` decomposition (extract Recorder, Timeline,
  Stats, Gallery into modules and put them under coverage).
- Stage 3 real lipid physics: curvature term + amphiphile-specific
  CMC coupling so switching amphiphile changes dynamics.
- Stage 4 full hypercycle ODE (minimal 2-replicator Eigen-Schuster).
- Pipeline chemical carry-over between stages (real continuity, not
  just narrative).

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
