# cellauto — Roadmap: from teaching sandbox to scientific instrument

**Status:** PLAN · **Baseline:** v4.2.0 · **Sources:** this plan is grounded in
three audits of the *running* code — the application review + 36-issue register
([`docs/review/`](../review/)), the per-stage `science.md` faithfulness audit,
and an engineering/instrumentation survey. It supersedes nothing in
[`ROADMAP.md`](../ROADMAP.md); it sets the next *arc*.

---

## 0. Where we actually are (honest baseline)

Not a toy engine — and we shouldn't pretend the starting point is worse than it
is. What's genuinely strong today:

- **A clean engine + Rule API** (`rules/base.py` 10-method protocol, `REGISTRY`),
  deterministic seeding, and lossless snapshot round-trip (`engine.py`).
- **Unusually strong quantitative chemistry tests** — the Eigen error threshold
  `ε_c = ln(σ)/L`, the Eigen–Schuster fixed point, Cahn–Hilliard Ostwald
  ripening, Wood–Ljungdahl thermodynamics in the Lane–Martin window, Miyazawa–
  Jernigan packing, Ferris clay localisation, and Miller's measured 1953 yields
  are all *asserted against published numbers*.
- **A genuine RAF closure** (Hordijk–Steel) and a faithful Tierra/Avida ALife VM.
- **Honest self-documentation** — `science.md` "Honest limitations," the SEM
  "not a microscope image" disclaimer, and the 36-issue register itself.

**What keeps it a sandbox rather than an instrument** (the gaps this roadmap
closes), distilled from the three audits:

| # | Gap | Evidence |
|---|---|---|
| G‑A | **Claims overclaim the code.** Named models are hand-tuned proxies: the "Miyazawa–Jernigan" matrix is an invented 4×4; "Helfrich bending" is a dimensionless smoother with SI units attached; the "genuine Eigen–Schuster ODE" runs uniform-`k`, mass-renormalised, while population dynamics are a radius heuristic. | REV-02/08/09; science audit gap #2 |
| G‑B | **No real units.** The whole pipeline is non-dimensional ("steps aren't seconds, cells aren't µm"); some readouts (vent PMF/ΔG) are *restated config inputs*, not measured from the field. | science.md §"Honest limitations"; gap #1, #3 |
| G‑C | **Measurement is decoration.** The SEM render measures nothing (uncalibrated scale bar); observables are integer-scaled hacks (`*_x1000`); no plots, no fitted metrics. | `renderer_sem.py`; `stage_rna.py` population |
| G‑D | **No data capture or provenance.** Headless emits only a final-population JSON; no CSV/HDF5/NetCDF time-series; snapshots carry no version/git-sha/timestamp/argv. | `__main__.py`; `engine.to_dict` |
| G‑E | **No parameter sweeps / ensembles.** Single-run only; no sweep runner, no replicate aggregation. | `__main__.py`, `tools/` |
| G‑F | **No comparison-to-data / reachable controls.** Tests pin *internal* behaviour but no stage compares an output to a measurement; some advertised controls (RAF catalysis=0) are unreachable; some tests are tautological. | REV-03/04/06; gap #6 |
| G‑G | **Performance & scale.** Pure CPU; field rules vectorised but the discrete-agent rules (Conway, RNA, LUCA, code, life) are Python `for` loops; 2-D only; "GPU path" is aspirational. | `field.py`, `stage_rna.py`, `grid.py` |
| G‑H | **Not citable / not headless-portable.** No `CITATION.cff`/DOI/PyPI/`py.typed`; the suite goes red without Tk (`app.py` hard-imports tkinter). | REV-01; packaging survey |
| G‑I | **Pipeline coupling is narrative glue.** Stage hand-off is a normalised 2-D field reused as a generic seed on a step timer, not causal chemistry. | `pipeline.py`; gap #7 |

---

## 1. Definition of "real lab" (acceptance thesis)

An instrument, not a demo, means **every stage** can answer: *what are the units,
what does it measure, what published result does it reproduce, what can you
sweep, and can someone else re-run it and cite it?* Concretely, each stage ships:

1. documented **units / non-dimensionalisation** and an honest **faithful-vs-illustrative** label;
2. ≥1 **observable** exported as real-valued time-series (not a decorated render);
3. ≥1 **quantitative test that reproduces a published number**;
4. ≥1 **reachable control** (a sweepable parameter with a falsifiable readout);
5. embedded **provenance** (version + git SHA + params + seed) on every output.

Plus, project-wide: a headless suite, a sweep/ensemble runner, benchmarked
performance, a citable release (DOI), and a reproduce-the-figure notebook.

---

## 2. Workstreams

Each: **goal · key deliverables · acceptance · closes**.

**W1 — Truth-in-labeling (honesty first).** Make every named claim true *or*
re-worded, since the brand is scientific honesty.
- Deliverables: per-stage **faithful/illustrative matrix** (docs + a UI "fidelity" line); reword proxy claims ("implements Helfrich" → "dimensionless biharmonic regulariser") or commit to calibrating in W8; reconcile `science.md` Stage-4 with the code; couple vent PMF/ΔG to the *simulated* field.
- Acceptance: no doc/UI claim contradicts the source; the review's honesty items close.
- Closes: REV-02, 08, 09, 10, 31; G‑A, G‑B(partial), G‑I(labeling).

**W2 — Validation & test rigor.** Turn "it runs" into "it's correct, vs the literature."
- Deliverables: kill tautological/over-tolerant asserts; make the **RAF null control reachable** (`catalysis_fraction`); **test the flagship Stage-XIII renderer**; a dedicated **validation suite** with ≥1 comparison-to-published-data per stage (Pearson F–k regime, Eigen ε_c crossing, Soai ee-amplification, Ferris length distribution, LUCA core size…); single-source-of-truth for stage/test/coverage counts.
- Acceptance: every advertised observable + control is test-pinned; validation suite green in CI.
- Closes: REV-03, 04, 05, 06, 07, 14, 19; G‑F.

**W3 — Real units & dimensional framework.** A units layer + per-stage calibration.
- Deliverables: declare units/scales per stage; calibrate the proxies that can be cheaply calibrated (Helfrich κ in `k_BT`, real 20×20 MJ table) or document the rescaling explicitly; dimensional `dx/dt` where a named real chemistry exists.
- Acceptance: every quantity displayed has a unit or an explicit "dimensionless" tag.
- Closes: G‑B; feeds W8.

**W4 — Measurement & observables.** Make the instrument *measure*.
- Deliverables: a float/units-aware `observables()` channel (retire the `*_x1000` hack); real observables per stage (pattern wavelength, enantiomeric excess ee(t), error-threshold crossing, droplet-size distribution, RAF size vs connectivity, core-set size); live **plots** of observables vs time; a calibrated scale bar where meaningful, else clearly interpretive.
- Acceptance: every stage surfaces ≥1 measured, exportable observable.
- Closes: G‑C.

**W5 — Data, provenance & reproducibility.** Instrument-grade capture.
- Deliverables: headless **time-series export** (CSV/HDF5/NetCDF) of all observables + fields; a **run manifest** embedded in every output (version, git SHA, timestamp, full params, seed, argv, platform); a declarative **experiment config** (YAML/TOML); `CITATION.cff` + Zenodo DOI + PyPI + `py.typed` + a semver/API-stability policy.
- Acceptance: any output is fully reproducible from its manifest; the software is citable.
- Closes: G‑D, G‑H.

**W6 — Parameter sweeps & ensembles.** First-class experiment driver.
- Deliverables: a headless **sweep runner** (param grid × seed replicates → tidy dataframe + per-run manifests), parallel + resumable; aggregation/summary stats; worked sweeps that **reproduce a published phase diagram** (Pearson F–k map; the error catastrophe vs ε).
- Acceptance: a one-command sweep produces a publishable phase-diagram figure + data.
- Closes: G‑E.

**W7 — Performance & scale.** Make real sizes feasible.
- Deliverables: vectorise/`numba`/GPU the discrete-agent rules (Conway/RNA/LUCA/code/life); an optional **3-D field**; **benchmarks + a perf-regression CI gate** (the currently-untracked "Performance" theme); documented grid/step ceilings; real-time vs batch modes.
- Acceptance: 256²+ (and a 3-D demo) run interactively; perf gate guards regressions.
- Closes: G‑G.

**W8 — Scientific depth (research-grade, per stage).** Replace proxies with
published models + real data + comparison-to-data, **prioritised by overclaim
severity**:
1. **Genetic code** — real 20×20 MJ matrix + the actual VWG code-compatibility gate (REV-02).
2. **Vesicles** — calibrate Helfrich κ to `k_BT` (or relabel) + osmotic growth/division (Hanczyc–Szostak) + CVC vs CMC (REV-09).
3. **Protocell selection** — couple the genome to the Stage-2 RAF so fitness *emerges*; non-uniform measured `k_i`; validate vs Adamala–Szostak.
4. **RAF** — run on a curated *real* reaction network with measured constants (REV-03).
5. **Gray–Scott** — a named real RD chemistry (CIMA/BZ), measured `D`, dimensional `dx/dt`, Turing-wavelength validation.
6. **Vents** — reactive-transport (Nernst–Planck) with ΔG from the live field + FeS kinetics.
7. **Chirality / minerals / coacervates / LUCA** — Soai rates + bias source; adsorption isotherms + Ferris kinetics; Voorn–Overbeek electrostatics + partitioning; real gene-presence matrix + ancestral-state reconstruction (recover ~355 families).
8. **Pipeline coupling** — causal hand-off (a stage's real product field seeds the next chemistry), closing the "twelve concatenated sims" gap (G‑I).
- Acceptance: each upgraded stage ships a published-number validation test (W2) and real units (W3).

**W9 — Platform & dissemination.** Make it usable + citable beyond the repo.
- Deliverables: the web client as a **reproducible tool** (in-browser compute via WASM/worker, parameter UI, **data download**, shareable run-URLs); a **reproduce-the-figure Jupyter notebook** per stage; a **methods/validation report → preprint** + Zenodo DOI; a gallery of validated results.
- Acceptance: a visitor can run a stage, download its data, and cite it.

---

## 3. Phasing

| Phase | Theme | Workstreams | Effect |
|---|---|---|---|
| **A — Honest & headless** (≈ weeks) | Trust | W1 + W2-core (controls, flagship test, kill tautologies, gate web, single-source counts) + W5-lite (run manifest, `CITATION.cff`, fix the Tk headless import) | "overclaiming demo" → **honest, reproducible sandbox**; closes most of the 36 issues |
| **B — Instrument** (≈ 1–2 months) | Capability | W3 units + W4 observables + W5 data export + W6 sweeps | produces **quantitative, exportable, reproducible measurements with provenance** |
| **C — Validated science & scale** (quarters) | Depth | W7 perf/3-D + W8 (top-3 overclaimed stages first: code, vesicles, protocell) | each upgraded stage **reproduces a published result**; real sizes feasible |
| **D — Citable platform** (ongoing) | Reach | W9 web tool + notebooks + preprint + DOI + PyPI; finish W8 | a **citable instrument** others use and reference |

Phase A is deliberately cheap and high-trust, and it's **non-negotiable first** —
a project branded on honesty must close the claim/label gaps before adding depth.

---

## 4. Risks, scope honesty & non-goals

- Some stages are genuinely **separate research projects** (full Helfrich
  membrane MD; real Wood–Ljungdahl reactive transport). For each W8 item the fork
  is explicit: **calibrate-to-a-real-number, or relabel honestly** — never leave a
  proxy wearing a published model's name.
- **Don't over-reach into a chemistry engine it can't be.** Pick a few stages to
  make truly publishable; be explicit (and tested) about the rest being
  illustrative. Breadth-of-honesty beats faux-depth.
- Performance work (W7) must not change results — guard with the existing
  quantitative tests + the new perf gate.

---

## 5. Decisions needed (forks for the user)

1. **Ambition target** — stop at **A (honest sandbox)**, **A+B (instrument)**, or go **A→D (research-grade, citable)**?
2. **Depth vs breadth (W8)** — make **2–3 stages truly publishable** (recommended: genetic code, vesicles, protocell — the worst overclaims) or lightly improve all 13?
3. **Units** — pursue **real SI units everywhere**, or **documented non-dimensional + per-stage calibration** of the headline numbers (cheaper, still honest)?
4. **Academic route** — pursue **PyPI + Zenodo DOI + a preprint** (credibility for citation), or keep it a polished teaching tool?
5. **Performance target** — what scale matters: bigger 2-D (256²–512²), **3-D**, real-time, or large **batch/ensemble** throughput?
