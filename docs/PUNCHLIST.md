# cellauto · Brutal Punchlist

A consolidated honesty audit of cellauto v3.4.0, synthesized from three
independent deep-dives (scientific accuracy, engineering quality,
claims-vs-delivery). The user asked for the brutal truth. This is it.

**Bottom line:** This is not vibe code. The bones are solid — a real
`Rule` Protocol with 17 conforming implementations, tests that pin
*quantitative* scientific claims (not just smoke), a web layer with
real concurrency primitives and a JS frontend that's vanilla and clean,
CI that actually runs. Three of the abiogenesis stages
(Gray-Scott, Frank chirality, Cahn-Hilliard coacervates) are textbook
correct, RNA quasispecies is correct in the qualitative regime, and the
Hordijk-Steel RAF closure is genuinely the *correct* version
(documented bug-fix from v3.1's false-positive one-pass closure).

What the project over-promises:
- **The hero claim** that "every constant traces to a published
  measurement" is CHARITABLE — some constants do, every *dynamical*
  parameter does not. `docs/science.md` is honest about this; the
  README hero copy isn't.
- **Three stages (vesicles / selection / genetic code) and one
  thermodynamic readout (vent ΔG)** are "real-concept toys" that the
  README markets as direct implementations of cited papers.
- **The 12-stage pipeline** is a chained slideshow with no chemical
  carry-over between stages.
- **The "Catalytic Silence" visual identity** only fully ships on
  Windows.
- **One genuine security hole** (`pickle.loads(user_input)` on a
  Flask handler the README publicly points to).

Below: issues by tier with the smoking gun, the fix, and an effort
estimate. Tier 0 should ship this week.

---

## Tier 0 · Security — fix this week

### P0-1 · Arbitrary code execution via snapshot load

**Smoking gun:** `cellauto/web/server.py:582` (and `cellauto/engine.py:121`)
unconditionally `pickle.loads()` the `rng_state` field of a user-posted
snapshot JSON. The web sandbox is deployed at a public Railway URL
the README directly advertises. A crafted snapshot can execute arbitrary
Python on the server.

**Fix:** `Random.getstate()` returns a `(int, tuple-of-624-ints, int|None)`
tuple. Serialize that directly to a JSON list, restore via
`tuple(state_list[0:1] + [tuple(state_list[1])] + state_list[2:])`.
Drop pickle from the snapshot path entirely. Bump snapshot `version`
from 2 → 3 and add a `version` check in `Engine.load`.

**Effort:** 1 hour + a regression test that a malicious pickle payload
no longer executes.

**Files:** `cellauto/engine.py`, `cellauto/web/server.py`, `tests/test_engine.py`,
`tests/test_web.py`.

---

## Tier 1 · Scientific honesty — close or recant

These are stages where the marketing reads "real implementation of
[cited paper]" but the code is a toy with the paper's label. **Either
make the code match the claim, or rewrite the claim to match the code.**
Both are honest. The current state is not.

### P1-1 · Stage 3 vesicles is Gray-Scott with relabeled fields

**Smoking gun:** `cellauto/rules/abiogenesis/stage3_vesicles.py:86–94`.
The simulation is `gray_scott_step` on `(u, v)` with the `v` field
renamed "lipid concentration" and thresholded at a unitless 0.3 to
mark "membrane" pixels. The `AMPHIPHILE_CMC_MM` table (decanoic 85 mM,
oleic 0.1 mM, etc.) is real but only surfaces as a *display string*
(`cmc_mM` readout). **Changing `amphiphile` from C10 to oleic doesn't
change any dynamics.** No Helfrich curvature, no surface tension, no
self-assembly kinetics.

**Two honest paths:**
- **A (real implementation):** Couple `cmc_threshold` to the chosen
  amphiphile (table-driven), add a curvature term, add a connected-
  component cost that biases toward closed bilayers. Real work,
  multi-day.
- **B (honest re-framing):** Rename to "Lipid concentration regime
  (Gray-Scott proxy)" in the rule's docstring + tutorial copy + README
  table; explicitly disclose that the CMC values are *labels*, not
  drivers; remove the implication that switching amphiphile changes
  the physics. 30 min.

**Recommendation:** Ship B today, file A as a roadmap item.

### P1-2 · Stage 4 selection is not the hypercycle, and the error threshold doesn't gate anything

**Smoking gun:** `cellauto/rules/abiogenesis/stage4_selection.py:62–88,
163–169`. The file's *own docstring* admits "This is a scalar *proxy*,
not the hypercycle itself" and that the ODE isn't integrated. The
`error_threshold` property returns `1/n_species` but is **never used
to gate dynamics** — mutation is `rng.gauss(0, mutation_rate)`
regardless of where ε sits relative to ε_c. The threshold is a
readout, not a switch.

**Fix:**
- **A:** Integrate even a minimal hypercycle ODE (2-replicator Eigen-
  Schuster). Reasonable mid-effort.
- **B:** Re-label as "Fitness-driven protocell selection (cyclic-
  coupling proxy)" and document the threshold as a Δ display only.
- **C (recommended):** Either path A or B, AND make mutation actually
  gate on `mutation_rate > error_threshold`: above the threshold,
  population entropy melts (the demo the README promises but the code
  doesn't deliver).

**Effort:** A = 2 days, B = 1 hour, C-with-B = 4 hours.

### P1-3 · Genetic-code stage doesn't implement Vetsigian-Woese-Goldenfeld

**Smoking gun:** `cellauto/rules/abiogenesis/stage_code.py:138–145, 147–189`.
VWG 2006's central mechanism is **horizontal gene transfer between
lineages with similar codes** — that's the actual claim of the paper
the rule cites. This implementation has only *vertical* mutation:
child copies parent's code with per-codon flip mutation. The
"code_consensus" stat measures how dominant a single lineage's code
becomes, which is just selection-driven fixation on a target peptide.

**Fix:**
- **A:** Add a per-step inter-cell exchange step where two adjacent
  cells with code-similarity > τ swap a fraction of their code entries.
  Real VWG mechanism, ~80 lines.
- **B:** Re-label as "Code evolution under selection (vertical only;
  VWG horizontal exchange not yet implemented)" in docstring + README.

**Recommendation:** A. This is the one stage where the gap from
"cited" to "implemented" is closable in a single day.

**Effort:** A = 1 day, B = 30 min.

### P1-4 · Vent ΔG° is a hard-coded display number, not a thermodynamic driver

**Smoking gun:** `cellauto/rules/abiogenesis/stage_vents.py:175–184,
99–122`. The README says "Wood-Ljungdahl carbon fixation models the
actual chemistry (2 CO₂ + 4 H₂ → acetate, ΔG° = −95 kJ/mol)". The
synthesis rate is `k_synth · |∇H| · [H₂] · [CO₂]` — a mass-action
heuristic that uses the gradient *magnitude*. The `−95 kJ/mol`
constant exists as `wl_delta_G_kJmol` but is **never used in the
rate law**. Flip the gradient direction and synthesis doesn't switch
from exergonic to endergonic — it just sees a smaller `|∇H|`.

The Nernst PMF (mV) and Faraday ΔG (kJ/mol) readouts *are* computed
correctly — verified by direct execution (PMF=266.22 mV, ΔG=−25.69
kJ/mol at default config, matches README's "≈ 266 mV / ≈ −26 kJ/mol").
But they're decorative — they're not coupled to the rate law.

**Fix:**
- **A:** Couple rate to a real free-energy term: `k_synth · max(0,
  −ΔG/RT) · [H₂] · [CO₂]` so the rate vanishes when the gradient
  flips. Real chemistry, ~30 lines.
- **B:** Re-label "Wood-Ljungdahl ΔG°" as a "thermodynamic envelope
  display" and the rate law as a "phenomenological gradient coupling".

**Recommendation:** A. The Nernst/Faraday infrastructure is already
there; using it to gate the rate is small.

**Effort:** A = 4 hours, B = 30 min.

### P1-5 · The 12-stage pipeline is a slideshow, not a chemical narrative

**Smoking gun:** `cellauto/rules/abiogenesis/pipeline.py:189–209`.
Each stage's `init_state` runs fresh on promotion — the soup's
molecules don't seed the vent's CO₂, the RAF's products don't seed
Stage 3's lipid field, Stage 3's vesicles aren't Stage 4's protocells.
The README says the pipeline "walks every major origin-of-life process
in scientific order"; reading the user thinks "continuous simulation",
gets "twelve disconnected runs glued together".

**Fix:**
- **A:** Add a `seed_from(prev_state)` hook to each `Rule` (default:
  no-op) that lets stage N+1's `init_state` bias its initial
  conditions from stage N's `population()` stats. Real continuity,
  significant work.
- **B:** Change README and pipeline tutorial copy from "walks every
  major origin-of-life process in scientific order" to "tours" /
  "exhibits". Add a one-line note in `docs/science.md` § "How to
  read the pipeline".

**Recommendation:** B today, A as a roadmap item — A is multi-week.

**Effort:** A = 2 weeks, B = 30 min.

---

## Tier 2 · Engineering quality

### P2-1 · `cellauto/app.py` is a 2121-line god-object with 0% coverage

**Smoking gun:** One `App` class, ~60 methods, all explicitly omitted
from coverage (`pyproject.toml:51-58`). Half the time it reads from
`engine.state.inner_rule`, half from `engine.rule`; the dispatch is
replicated across `_param_target`, `_init_renderer`, `_sync_pipeline_row`,
`_render`, `_export_png`, `_snapshot_frame` — five hand-rolled
copies of the same `getattr(state, "inner_rule", None) or rule`
pattern. The `_GALLERY_ITEMS` dict is 108 lines of *data* embedded
in the class body.

**Fix:** Extract `_GifRecorder`, `_TimelineRing`, `_StatsRing`, and
the `_active_rule_for(engine)` dispatch into their own modules.
Move `_GALLERY_ITEMS` to `cellauto/gallery.toml`. Add headless
`App` instantiation tests via `tk.Tk()` + `withdraw()` (Linux CI
runners can use xvfb).

**Effort:** 2-3 days.

### P2-2 · Per-cell Python loops in RNA / LUCA / code rules

**Smoking gun:** `stage_rna.py:114–145`, `stage_luca.py:176–207`,
`stage_code.py:156–189`. Three nested `for y in range(H): for x in
range(W):` loops with `rng.choices` per cell. Fine at 24-48 grids,
~10× slower than necessary above 60×60.

**Fix:** Vectorize via `np.random.Generator.choice(p=...)` over the
neighbor offsets in one pass. Same pattern as RAF rate computation
already in the code.

**Effort:** 1 day for all three.

### P2-3 · Catalytic Silence fonts only ship on Windows

**Smoking gun:** `cellauto/app.py` font registration via
`gdi32.AddFontResourceExW` early-returns when `sys.platform != "win32"`.
The TTFs are bundled (`cellauto/assets/fonts/*.ttf`) but not loaded
into Tk on Linux/macOS — those platforms get system serifs. The
"design philosophy" only fully ships on one of three major platforms.

**Fix:** Use Tk's `font.Font(file=…)` (Tk 8.6.10+) or copy the TTFs
into a per-user font cache on first run via fontconfig (Linux) /
ATSUI (macOS).

**Effort:** 4 hours (Linux), +4 hours (macOS) — testable in CI on
Linux at minimum.

### P2-4 · `Engine.__post_init__` wastes a `rule.init_state` call on every `Engine.load`

**Smoking gun:** `engine.py:43`. `Engine.load` immediately overwrites
`engine.state` after construction, so the `init_state` call in
`__post_init__` is wasted work — ~5–10ms per load on an 80×80 RAF
snapshot. Trivial but architecturally untidy.

**Fix:** Add an `_eager_init: bool = True` field; `Engine.load` sets it
False before constructing.

**Effort:** 15 min.

### P2-5 · Snapshot schema version never checked on load

**Smoking gun:** `engine.py:83` writes `"version": 2`. `engine.py:103-117`
never reads it. A future format change has no migration path.

**Fix:** Read `data.get("version")` in `Engine.load`, route through
a version-specific deserializer if/when ≥3 ships.

**Effort:** 30 min, plus future-proofs every subsequent schema bump.

### P2-6 · `test_protocol.py::test_every_rule_can_init_state_and_step` is a tautology

**Smoking gun:** Asserts `new_state is not None or state is not None`,
which is `True` whenever either is non-None — i.e. always after
`init_state` runs. Doesn't actually test that stepping changes
anything.

**Fix:** Per-rule shape invariants + a "stepping advances population
counter" claim that some rule must satisfy.

**Effort:** 1 hour.

### P2-7 · Canvas click-to-inspect has a 2-pixel borderwidth offset

**Smoking gun:** `app.py:1718` scales `event.x / (CANVAS_SIZE / w)`
to grid-space without accounting for the canvas widget's
`borderwidth=2` (set at `app.py:543`). Stage 4 protocell hit-testing
near the canvas edge misses by 1-2 cells.

**Fix:** Subtract 2px from `event.x` and `event.y` before scaling.

**Effort:** 5 minutes.

### P2-8 · `_session_load` discrete-rule frame capture is 57k Python calls

**Smoking gun:** `web/server.py:284` `_capture_frame` for discrete
rules calls `rule.render_cell(...)` H×W times per frame. At 240×240,
that's 57,600 Python calls per frame. A 60-frame GIF = 3.5M calls.

**Fix:** Add `Rule.render_rgb` paths for the discrete rules
(Conway and Wolfram already have it). For `natural_selection` and
`abiogenesis-stage0-soup`, build the RGB array from the cells in
one numpy pass.

**Effort:** 2 hours.

---

## Tier 3 · Documentation drift

### P3-1 · README claims 120 tests; actual is 147

**Smoking gun:** README line ≈140 says "120 tests, all passing".
Actual: 147 pass.

**Fix:** Replace static numbers with a `tests/passing` and `codecov`
badge, or remove the number entirely and reference CI.

**Effort:** 5 min.

### P3-2 · Extended-pipeline tutorial copy lists 10 stages; code has 12

**Smoking gun:** `cellauto/tutorial.py:22-25` enumerates "0 Soup → 1
Alkaline vent → 2 Reaction-diffusion → 3 Mineral catalysis → 4 RAFs
→ 5 Homochirality → 6 RNA world → 7 Coacervates → 8 Vesicles →
9 Protocell selection". The actual `EXTENDED_STAGE_CLASSES` at
`pipeline.py:353–366` has 12 stages including genetic code and LUCA.

**Fix:** Update `tutorial.py["abiogenesis-pipeline-extended"]` second
line to enumerate all 12.

**Effort:** 5 min.

### P3-3 · CLI `--stage 0-4` help wrong for extended pipeline

**Smoking gun:** `cellauto/__main__.py:155` advertises `--stage 0-4`
but the extended pipeline has 12 stages (0-11).

**Fix:** Update help text to "0-11 (extended pipeline) or 0-4 (canonical)".

**Effort:** 5 min.

### P3-4 · Four broken references to `PHASE2_BRUTAL.md`

**Smoking gun:** README (2x), CHANGELOG (1x), PRD (2x) reference
`PHASE2_BRUTAL.md` as the project's self-audit document. The file
does not exist in the repo or any parent directory. The project is
broken-link-shaming itself.

**Fix:**
- **A:** Restore the file from git history if it was deleted; or
- **B:** Replace cross-refs with a link to *this* `PUNCHLIST.md`
  (which is the actual self-audit). The audit identity transfers.

**Recommendation:** B. This document is now the brutal-self-audit
artifact the repo was implicitly referencing.

**Effort:** 15 min.

### P3-5 · Render scripts hardcode the author's Windows path

**Smoking gun:** `tools/render_aaa_visuals.py:55` and
`docs/design/render_prima_materia.py:42` both set
`FONT_DIR = "C:/Users/guru8/AppData/Roaming/Claude/local-agent-mode-sessions/skills-plugin/.../canvas-design/canvas-fonts"`.
The same fonts are bundled at `cellauto/assets/fonts/`. The README
invites readers to "see the render script" but anyone not named
guru8 on Windows gets `ImageFont.truetype` crash.

**Fix:**
```python
FONT_DIR = Path(__file__).resolve().parents[1] / "cellauto" / "assets" / "fonts"
```
(or `parents[2]` from `docs/design/`).

**Effort:** 10 min, including verifying the render still produces
the same poster.

### P3-6 · About dialog still says "five stages"

**Smoking gun:** `cellauto/app.py:1899` "five stages: primordial soup
· reaction-diffusion · autocatalytic sets · vesicles · protocell
selection". The 12-stage extended pipeline is unmentioned.

**Fix:** Update About text to reference both the 5-stage canonical
pipeline and the 12-stage extended one.

**Effort:** 10 min.

### P3-7 · README hero copy oversells beyond docs/science.md

**Smoking gun:** README line ≈80 says "Every constant traces to a
published measurement". `docs/science.md` has an "Honest limitations"
section that explicitly admits toy time/length scales, no real
thermodynamics, phenomenological constants. The hero copy isn't as
careful as the science doc that backs it.

**Fix:** Soften README to "Many constants trace to published measurements
(see docs/science.md for the full breakdown of real-data-backed vs
phenomenological values)."

**Effort:** 15 min.

---

## Tier 4 · CI / build hygiene

### P4-1 · `pip-audit` only audits Pillow + numpy

**Smoking gun:** `.github/workflows/ci.yml` `security` job runs
`pip-audit -r requirements.txt`. `requirements.txt` is two lines
(`Pillow>=10.0`, `numpy>=1.26`). Flask, gunicorn, pytest, ruff,
mypy — none audited. The security job is partial cover.

**Fix:** Run `pip-audit` against the resolved environment (`pip-audit`
with no `-r` audits installed packages) or against `pyproject.toml`
extras.

**Effort:** 15 min.

### P4-2 · `mypy --no-error-summary` hides what's checked

**Smoking gun:** CI runs `mypy cellauto --ignore-missing-imports
--no-error-summary`. The summary line ("Success: no issues found
in N source files") is suppressed. A regression to "0 errors over
0 files" is undetectable.

**Fix:** Drop `--no-error-summary`. Add a `mypy --strict` job that's
`continue-on-error: true` so contributors see the strict-mode gap.

**Effort:** 15 min.

### P4-3 · Coverage threshold theater

**Smoking gun:** CI requires `--cov-fail-under=80`. `pyproject.toml:51-58`
omits `app.py`, `mascot.py`, `renderer.py`, `web/server.py`, `web/wsgi.py`,
`__main__.py` from coverage measurement. That's ~2.7k of 4.9k Python
lines, ~55% of the codebase. The "89% covered" number is meaningful
for the science modules but misleading as a project-wide stat.

**Fix:**
- **A:** Add a second coverage job with no omits and a lower threshold
  (e.g. 50%) so the omitted modules get *some* visibility.
- **B:** In README, replace "87% coverage" with "87% on the science
  layer; GUI / web / CLI verified by smoke tests in CI".

**Recommendation:** B today, A as a roadmap item.

**Effort:** B = 10 min, A = 1 hour.

---

## Verdict (one paragraph)

This is the kind of project you can put on a CV. The discipline of
*Rule abstraction → 17 implementations → tests-with-claims → CI gating*
is real and rare. Three abiogenesis stages, one closure algorithm, and
the web layer are work to be proud of. The remaining stages are
"real-concept toys" with citations attached — fine as educational
visualization, *but the README markets them as direct paper
implementations and that is the gap*. The biggest engineering weakness
is the GUI shell: 2121 lines on one class, 0% coverage, and one
genuine RCE in the snapshot loader. None of this requires a rewrite.
**Three weeks of focused work — Tier 0 + Tier 1 + the worst of Tier 2 —
would turn this from "honestly mid-tier with overclaim-shaped trim"
into "actually as good as the README says it is".**
