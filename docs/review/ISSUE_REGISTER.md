# CellAutomata v4.1.1 — Issue Register (Full-Application Review)

**Review date:** 2026-06-03 · **Product version reviewed:** 4.1.1 (`cellauto/__init__.py`, `pyproject.toml`, `CHANGELOG.md` all agree)
**Method:** 6-stream parallel read-only audit (science/engine · GUI/UX · web · tests/CI · docs · assets) + headless verification run (full pytest+coverage, mypy, ruff, 17-rule render harness) + literature spot-check of load-bearing claims. Two audit streams (docs-drift, assets) were cut short by a usage limit; their scope was back-filled by the orchestrator and the science/web streams.

This register is the authoritative, numbered list of every issue found. The narrative analysis with screenshots is in [`APPLICATION_REVIEW_v4.1.md`](APPLICATION_REVIEW_v4.1.md). Every item here is mirrored into the ROADMAP punchlist (`docs/ROADMAP.md` §7, `REV-*` ids).

**Severity key:** BLOCKER = breaks a shipped guarantee / data integrity · MAJOR = honesty gap, broken claim, or real defect · MINOR = hygiene, drift, or polish.
**Status:** all items are `DOCUMENTED` (this review's deliverable is to document + punchlist, not to fix). Doc-honesty fixes applied in the same PR are marked `DOC-FIX-APPLIED`.

---

## A. Correctness & test integrity

| ID | Sev | Title | Evidence (file:line) | Fix direction | Status |
|---|---|---|---|---|---|
| REV-01 | MAJOR | **Suite is red in any Tk-less environment.** `test_sem_palette_round_trips_through_config` fails because `app.py` hard-imports `tkinter` at module top, yet the logic under test (`_save_sem_config`/`_load_sem_config`) is pure JSON. CI is green only because ubuntu runners ship Tk. | `cellauto/app.py:29` (`import tkinter as tk`); `tests/test_sem_renderer.py:150`; `/tmp/pytest_full.log` (exit 1) | Move config I/O to a Tk-free module (`cellauto/config.py`) or lazy-import `tkinter` inside the functions that need it, so the persistence logic is testable headlessly. | DOCUMENTED |
| REV-02 | MAJOR | **Genetic-code stage doesn't model the mechanism its docstring claims.** Prose says "a cell can only use a donor's strand if the donor's code is compatible" → drives universal-code convergence. No compatibility gate exists; MJ fitness rewards peptide *composition* only (max = all-V homopolymer, reachable by any code). Consensus rises only incidentally. | `cellauto/rules/abiogenesis/stage_code.py:28-31` (docstring), `:204-230` (fitness), `:249-291` (colonisation) | Implement donor↔recipient code-agreement gate (real Vetsigian-Woese-Goldenfeld innovation-sharing), or downgrade prose to "selection on peptide fitness; consensus is an emergent side-effect." | DOCUMENTED |
| REV-03 | MAJOR | **RAF "null experiment" control is unreachable; advertised stat is a constant.** `random_reaction_network` catalyses *every* reaction, so `catalysis_level_x100` is hardwired (200 at defaults) and the StageInfo "set catalysis_level=0 → RAF disappears" control cannot be performed. | `cellauto/rules/abiogenesis/science.py:141-147`; `stage2_raf.py:184-191`; `pipeline.py:206-212` | Add a `catalysis_fraction` parameter (leave some reactions uncatalysed) so the Kauffman threshold is sweepable, or remove the control claim. | DOCUMENTED |
| REV-04 | MAJOR | **Tautological tests pass even if the feature is broken.** `assert alive_count >= 0` (structurally non-negative), `assert pop["amoebas"] >= 0`, `assert new_state is not None or state is not None` (always true). | `tests/test_hypercycle.py:147`; `tests/test_export_and_edges.py:107`; `tests/test_protocol.py:35` | Assert real invariants (≥1 survivor; population sums to grid; `new_state is not None`). | DOCUMENTED |
| REV-05 | MAJOR | **Flagship Stage XIII renderer (`life_sem.py`) has no targeted test.** Only an indirect shape/brightness smoke via `render_plate`; none of `_blur/_normals/_fbm/_body_fields/_organism_tile/_division_tile/_overlay` is pinned. | `cellauto/rules/abiogenesis/life_sem.py`; `tests/test_life.py:376` | Add `tests/test_life_sem.py`: dividing cell → teal pixels; empty state → valid dim substrate; body size scales with energy. | DOCUMENTED |
| REV-06 | MINOR | **Permanently-skipped placeholder + over-tolerant thresholds.** `test_web_python_vm_parity` is a `pass`-body `@skip`. LUCA core floor `>= essential//2`, pipeline-handoff `max>0.15`, zero-cost bloat `>=` (no margin) can pass on no-signal. | `tests/test_life_vm_parity.py:15`; `tests/test_luca.py:37,54`; `tests/test_pipeline_handoff.py:170` | Implement/`xfail` the parity stub; add positive margins / `min()` floors. | DOCUMENTED |
| REV-07 | MINOR | **Untested modules / unpinned constants.** `tutorial.py` 0% coverage (no test); `params.py` has no spec-vs-attribute test (a typo'd `field` only fails at GUI runtime); Miller-Urey species ordering, Gray-Scott Du:Dv grounding, and `LUCA_GENE_NAMES` length are unpinned. | `cellauto/tutorial.py` (0% in coverage report); `cellauto/rules/params.py` | Add a per-rule `tutorial_for()` smoke; a `getattr(rule, spec.field)` existence test; pin the published constants. | DOCUMENTED |

## B. Scientific honesty (claim vs. implementation)

The *cited* science is sound (Helfrich κ≈10⁻¹⁹ J, Eigen ε_c≈ln σ/L, Wood-Ljungdahl ΔG°′≈−95 kJ/mol all independently confirmed). These items are about the **code under-delivering the prose**, or stale numbers.

| ID | Sev | Title | Evidence | Fix direction | Status |
|---|---|---|---|---|---|
| REV-08 | MAJOR | **science.md Stage 4 fitness contradicts the code.** Doc: "Shannon entropy × total concentration." Code: cyclic-coupling proxy `Σ g[i]·g[(i+1)%n]` + Eigen-Schuster ODE health. No Shannon entropy anywhere. Section still calls it "a TOY" though ROADMAP says G2 removed the disclaimer. | `docs/science.md:223,612`; `cellauto/rules/abiogenesis/stage4_selection.py:63-92` | Rewrite §Stage 4 to describe the hypercycle ODE + proxy. | DOCUMENTED |
| REV-09 | MINOR | **"Helfrich bending is real (κ_b≈10⁻¹⁹ J)" overclaims a dimensionless smoother.** The biharmonic `−κ_b∇⁴v` exists but `kappa_bend` is an admitted "normalised dimensionless analogue" — no bending modulus, no interface, no curvature energy. (The cited 10⁻¹⁹ J value is itself correct.) | `pipeline.py:269-270`; `stage3_vesicles.py:81-83,139-142` | Re-word caveat to "curvature-suppressing biharmonic regulariser (dimensionless), not a calibrated Helfrich modulus." | DOCUMENTED |
| REV-10 | MINOR | **LUCA "core = network invariant" is loose + stale number.** `accessory_bonus=0.08>0` gives non-pathway genes positive fitness, so recovered core (≈10) ≠ essential set (12). `science.md` says core "locks at ≈6 by default"; code's `essential_count` is 12. | `cellauto/rules/abiogenesis/stage_luca.py:119,135-146,223-233`; `docs/science.md:533` | Set `accessory_bonus=0` (or document "pathway genes minus drift"); update the doc number 6→12. | DOC-FIX-APPLIED (number) |
| REV-11 | MAJOR (honesty) | **Stage XIII is under-documented vs every other stage.** All seven E3/E4 StageInfo fields (`apparatus/methods/control/expect/caveats/produces/consumes`) are empty, so "How it works" + chapter card show nothing for the flagship new stage. | `cellauto/rules/abiogenesis/pipeline.py:859-874` (`_STAGE_LIFE_INFO`) | Author the five+two fields from `docs/PRD_LIFE_DIGITAL_ORGANISMS.md`, matching the other 12. | DOCUMENTED |

## C. Documentation drift & dead references

| ID | Sev | Title | Evidence | Fix direction | Status |
|---|---|---|---|---|---|
| REV-12 | MAJOR | **PRD.md is ~2 versions stale.** Header "Reviewed at commit `7c705f6` (2024-04-02)", presents **v3.2** as the live roadmap, links to a **missing** `PHASE2_BRUTAL.md`; product is 4.1.1. | `PRD.md:4-5,160,208` | Add an accurate status banner + repoint dead links. | DOC-FIX-APPLIED (banner) |
| REV-13 | MAJOR | **`docs/PRD_LAB_EXPERIMENTS.md` referenced but missing.** web6 README + `main.js` cite it as the "Full design" doc. | `docs/web6/README.md:13`; `docs/web6/main.js:6` | Create the PRD or repoint to `PRD_SEM_VISUALIZATION.md`/`PRD_LIFE_DIGITAL_ORGANISMS.md`. | DOCUMENTED |
| REV-14 | MAJOR | **Pervasive, self-inconsistent count drift.** README "12 stages / 141 tests / 88%"; ROADMAP says "120 tests" *and* "141 tests" *and* "262/262" in different places; "Twelve abiogenesis stages." Actual: **13 stages, ≈318 collected (279 functions), 91% coverage**. | `README.md:389,428,444`; `docs/ROADMAP.md:14,146,233,288,393` | Reconcile every count to the real numbers; add Stage XIII to the Feature Inventory. | DOC-FIX-APPLIED (counts) |
| REV-15 | MINOR | **ROADMAP describes a non-existent `inherit_from` adapter** and self-contradicts on coupling. Coupling is real but via `extract_signal`/`seed_field`; no `inherit_from` exists. §1 still warns "until G1 is closed, promotion resets" while §3 says G1 shipped. | `docs/ROADMAP.md:162,250-252` | Re-describe the real mechanism; remove the stale "until G1 is closed" caveat. | DOC-FIX-APPLIED |
| REV-16 | MINOR | **Missing `PHASE2_BRUTAL.md`** referenced by PRD.md and ROADMAP §0a. | `PRD.md:160,208`; `docs/ROADMAP.md` (§0a header) | Restore the file or convert links to the live ROADMAP/this review. | DOCUMENTED |
| REV-17 | MINOR | **"four CI gates" claim is wrong** — `ci.yml` runs six checks + a security job. | `docs/ROADMAP.md:14`; `.github/workflows/ci.yml:33-66` | Reconcile the count. | DOC-FIX-APPLIED |

## D. Web client

| ID | Sev | Title | Evidence | Fix direction | Status |
|---|---|---|---|---|---|
| REV-18 | MAJOR | **web6 `stage5-minerals` silently maps to `grayscott`** — no mineral-catalysis experiment; two stages render an identical Gray-Scott field (no clay mask, no Ferris localisation). | `docs/web6/main.js:57` | Port `stage_minerals.py` → `experiment/rules/minerals.js`, or label the panel a placeholder. | DOCUMENTED |
| REV-19 | MAJOR | **web2/web3 JS smoke tests are not gated in CI** — only web6 runs in `pages.yml`. A regression in 9 web2 rules / web3's digital-life rule deploys silently. | `.github/workflows/pages.yml:36-41` | Add `node docs/web2/tests/smoke.mjs` + `docs/web3/tests/smoke.mjs`, or declare web2/web3 frozen-legacy and remove. | DOCUMENTED |
| REV-20 | MINOR | **web6 directory is named "web6" but all internal strings say "web4"** (rename artifact). | `docs/web6/README.md:1`; `main.js:1`; `tests/smoke.mjs:1,30` | Global rename web4→web6 in comments/strings. | DOCUMENTED |
| REV-21 | MINOR | **railway.toml stale after web6 canonicalisation** — comment + `healthcheckPath = "/web2/"`. | `railway.toml:8-9` | Update to `/web6/`. | DOCUMENTED |
| REV-22 | MINOR | **web6 hard-depends on a CDN** (Three.js importmap from jsdelivr) with no vendored fallback — breaks offline / strict-CSP. | `docs/web6/index.html:7-14` | Vendor `three@0.162.0` under `web6/vendor/` or document the requirement. | DOCUMENTED |
| REV-23 | MINOR | **web2/web3 PUNCHLIST still self-describe as "live canonical"** and list raf/rna/code/luca as missing though web6 ships them. | `docs/web3/PUNCHLIST.md:31`; `docs/web2/PUNCHLIST.md` | Mark "superseded by web6"; reconcile the building-block punchlist. | DOCUMENTED |

## E. GUI / UX (desktop Tk)

All ROADMAP §2 "Mandated UI toolset" controls (A–G) and 10/12 web-parity items were verified genuinely wired — **zero false "shipped" claims**. These are real UX defects on top of that.

| ID | Sev | Title | Evidence | Fix direction | Status |
|---|---|---|---|---|---|
| REV-24 | MAJOR | **Blocking `grab_set()` modals freeze the running sim; GIF export races the engine.** Gallery/About/Tutorial-all/GIF dialogs grab input while `_animate` keeps firing; GIF capture steps `engine` directly while `_loop` may still be running → two step pumps on one engine, and scrub/stat buffers desync. | `cellauto/app.py` ~`2250-2296`, `2616`, `2654`, `2350` | `self._stop()` at the top of `_export_gif`; drop `grab_set` for the read-only panels; snapshot/restore engine around export. | DOCUMENTED |
| REV-25 | MAJOR | **Transport bar sits below the fold** in the fixed, non-resizable 720×1000 window — Play/Stop/Step/FPS are off-screen at launch and require scrolling. Poor for a kiosk. | `cellauto/app.py:140-142`, `_build_widgets:640-646` | Move transport above the canvas, or pin a compact non-scrolling transport strip. | DOCUMENTED |
| REV-26 | MINOR | **Inconsistent error surfaces** — `messagebox.showinfo("Not found")` for a missing plate violates the L12 non-blocking-toast policy; `_toast(kind="warn")` has no colour mapping (falls back to neutral). | `cellauto/app.py:2607`; `_toast:911-915` (calls at `231`, `947`) | Route the error through `_toast(kind="error")`; add a `"warn"` amber colour. | DOCUMENTED |
| REV-27 | MINOR | **Menu/state divergence** — Render-scale + SEM-palette cascades aren't gated on `_sem_available`; Story checkbox stays checked while no-op in viridis; hi-res PNG export hardcodes 1440² (1080/2160 presets unreachable); click-to-inspect has no affordance and is silent off-target. | `cellauto/app.py:975,1009,1026,1448,1469,2488` | Gate dependent menu items on SEM state; expose an export-size picker; add a Stage-4 "click a disc" hint. | DOCUMENTED |
| REV-28 | MINOR | **Polish** — two sections both numbered "I"; font-scale isn't persisted and overflows the fixed chip pixel-budget; `_loop` high-FPS batch swallows step exceptions silently. | `cellauto/app.py:749,657,548,1905` | Renumber sections; persist `font_scale` + factor it into chip budget; log/toast on caught batch exceptions. | DOCUMENTED |

## F. Code hygiene

| ID | Sev | Title | Evidence | Fix direction | Status |
|---|---|---|---|---|---|
| REV-29 | MINOR | **Stage XIII not in the rule REGISTRY** — reachable only via the extended pipeline, not the rule selector/CLI, despite shipping tests + committed art (`stage13_life.png`, `v5_life_ui_mockup.png`). | `cellauto/rules/__init__.py` (REGISTRY has 17, no `abiogenesis-life`) | Register `abiogenesis-life` (or document the deliberate exclusion). | DOCUMENTED |
| REV-30 | MINOR | **Dead code** `_v401_sprites` (defined, never called; `render_sprites` returns `[]`). | `cellauto/rules/abiogenesis/stage1_grayscott.py:175-210` | Delete or clearly archive. | DOCUMENTED |
| REV-31 | MINOR | **genetic-code `render_cell` ≠ `render_rgb`** — discrete path scores by `target_peptide`, field path uses the MJ landscape (latent inconsistency; field path is canonical). | `cellauto/rules/abiogenesis/stage_code.py:309-320` vs `322-326` | Make `render_cell` use the MJ field too. | DOCUMENTED |
| REV-32 | MINOR | **Stage XIII `_division_site` docstring/behaviour mismatch** — says "least-occupied empty neighbour", picks a uniformly-random one. | `cellauto/rules/abiogenesis/stage_life.py:333-345` | Align code to docstring or fix the docstring. | DOCUMENTED |

## G. CI / infra

| ID | Sev | Title | Evidence | Fix direction | Status |
|---|---|---|---|---|---|
| REV-33 | MINOR | **Action-version inconsistency** (NOT a broken deploy — corrected). `pages.yml` pins `actions/checkout@v6` + `setup-node@v6` (verified to exist and be stable as of 2026); `ci.yml` pins `@v4`/`@v5`. `pages.yml` also pins `node-version: "20"` (Node 20 EOL Apr 2026; runners default Node 24 from 2026-06-16). | `.github/workflows/pages.yml:32-33,50`; `ci.yml:21,24,59-60` | Pin both workflows to the same major; bump pages node to 22/24. | DOCUMENTED |
| REV-34 | MINOR | **Coverage gate too low** — `--cov-fail-under=80` vs real 91%; won't catch a regression to 81%. | `.github/workflows/ci.yml:43` | Raise to ~88. | DOCUMENTED |
| REV-35 | MINOR | **pip-audit scans `requirements.txt` only** — installed transitive deps (Pillow/numpy) aren't audited. | `.github/workflows/ci.yml:63-66` | `pip install -e ".[dev]" && pip-audit` (audit the environment). | DOCUMENTED |
| REV-36 | MINOR | **mypy non-strict** (`--ignore-missing-imports`, no `--disallow-untyped-defs`) — misses missing annotations in the science modules; Python 3.13 absent from the matrix. | `.github/workflows/ci.yml:40,19` | Add `--disallow-untyped-defs` as a work queue; add 3.13 to the matrix. | DOCUMENTED |

---

### Tally
**36 issues** — 0 blocker · 11 major · 25 minor. Plus 5 doc-honesty fixes applied in-PR (REV-10/12/14/15/17 partial). Full evidence and screenshots: [`APPLICATION_REVIEW_v4.1.md`](APPLICATION_REVIEW_v4.1.md).
