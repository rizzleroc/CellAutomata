# Cellular Automata Natural Selection Simulator — PRD & Brutal Gap Analysis

**Repo:** `rizzleroc/CellAutomata`
**Reviewed at:** commit `7c705f6` (2024-04-02)
**Reviewer date:** 2026-05-18 (~2 years after last commit)
**Scope (original):** 4 Python files, 7 tracked files, ~300 LOC total
**Scope (v2.0):** package `cellauto/` (8 modules), CLI, GUI, headless mode, GIF export, 14 tests, CI workflow

---

## 0. Build Status (2026-05-19) — shipped

Everything in §4 below is shipped on `main`. Summary of what landed in v2.0:

| PRD item | Status | Where |
|---|---|---|
| F1 — Rule 1 neighbor-color propagation | ✅ Done | [cellauto/rules/natural_selection.py](cellauto/rules/natural_selection.py) |
| F2 — Rule 2 fires (quantized palette) | ✅ Done | 16-color PALETTE at [natural_selection.py:29](cellauto/rules/natural_selection.py#L29). Headless run shows ~830 amoebas / 900 cells by step 50. |
| F3 — Rule 3 `is_new` has teeth | ✅ Done | Only set on cells that just changed color; combine sets it false. |
| F4 — Rule 4 amoeba lifecycle | ✅ Done | Amoebas age + die at 25 steps. |
| F5 — "Natural selection" framing honest | ⚠️ Improved, not solved | Still no fitness/inheritance, but the four rules now actually do what the README says. v2.0 README reframes as "sandbox" rather than literal natural-selection claim. |
| C1 — Delete `main_new.py` | ✅ Deleted |
| C2 — Speed slider mislabeled | ✅ Fixed — now an FPS slider. |
| C3 — Window close handler broken | ✅ Fixed — `_quit` destroys window. |
| C4 — Step button racy during play | ✅ Fixed — disabled while running. |
| C5 — `logging` not configured | ✅ Fixed — `basicConfig` in CLI and `app.run`. |
| C6 — `canvas.delete("all")` every frame | ✅ Fixed — persistent item IDs + `itemconfigure`. |
| C7 — No seed / no reproducibility | ✅ Fixed — `--seed` flag, Engine seeds rule RNG, shown in status bar. |
| D1 — `requirements.txt` was markdown | ✅ Fixed |
| D2 — Conflicting Python versions | ✅ Fixed — 3.10+ everywhere |
| D3 — Personal email in README | ✅ Removed |
| D4 — No screenshot | ✅ Added [docs/hero.png](docs/hero.png) |
| D5 — No LICENSE | ✅ MIT — see [LICENSE](LICENSE) |
| Tests | ✅ 14 pytest tests, all pass |
| CI | ✅ GitHub Actions matrix (3.10, 3.11, 3.12) — see [.github/workflows/ci.yml](.github/workflows/ci.yml) |
| `.gitignore` | ✅ Added |
| `pyproject.toml` | ✅ Added, installs as `cellauto` console script |
| Type hints | ✅ Throughout |
| Save/load JSON | ✅ Engine.save/load + GUI File menu |
| Headless mode | ✅ `cellauto simulate` subcommand |
| Stats overlay | ✅ Status bar shows rule/seed/step/FPS/population |
| Pluggable rule engine | ✅ `Rule` Protocol + `REGISTRY`; ships NaturalSelection, Conway, Wolfram1D |
| Tutorial overlay | ✅ Help ▸ Start tutorial, 7 steps |
| GIF export | ✅ `cellauto export` + GUI "Record GIF" + Pillow renderer |

**Not done (deliberate skip):** v3.0 web port (Pyodide / JS rewrite). That's a platform change, not a feature — flagged out of scope at the start.

---

## 1. Product Vision (what the README/manual *claim*)

> "A cellular automaton that simulates natural selection."

Four rules:
1. Each cell takes on a random color (of a neighbor).
2. Two adjacent same-color cells combine into a new color.
3. A "new" cell can only combine with other new cells.
4. When a new cell combines, it evolves into an "amoeba" — a step in cellular complexity.

Goal: an **interactive, visually engaging evolutionary simulation** with play/stop/step controls and a speed slider.

---

## 2. What Was Actually Built

| Component | File | LOC | Status |
|---|---|---|---|
| `Cell` model | [cell.py](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/cell.py) | 32 | Functional, has bugs |
| `CellularAutomaton` grid | [cellular_automaton.py](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/cellular_automaton.py) | 39 | Functional, has bugs |
| Tk GUI | [main.py](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/main.py) | 77 | Functional, has bugs |
| Tk GUI (duplicate) | [main_new.py](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/main_new.py) | 77 | **Dead duplicate** |
| README | [README.md](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/README.md) | 9 | Exposes author email |
| Manual | [manual.md](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/manual.md) | 59 | Contradicts requirements.txt |
| Requirements | [requirements.txt](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/requirements.txt) | 4 | **Not a real requirements file** |

Total git history: 4 commits across 7 days in March–April 2024. No tests, no CI, no `.gitignore`, no LICENSE, no `pyproject.toml`/`setup.py`, no issues, no branches, no tags.

---

## 3. Brutal Gap Analysis

### 3.1 Functional gaps — the simulation does not do what the README says

#### **Gap F1: Rule 1 is implemented wrong**
README says "cell takes on a random color **around itself**" (i.e., from a neighbor). Code at [cell.py:13](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/cell.py#L13) generates a **fully random 24-bit hex color** with no reference to neighbors. There is no neighbor-color propagation anywhere in the code. The headline rule of the simulation isn't implemented.

#### **Gap F2: Rule 2 is mathematically dead**
[cellular_automaton.py:38](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/cellular_automaton.py#L38) gates combination on `cell1.color == cell2.color` — exact-equality of two **randomly generated 24-bit hex strings**. Probability of two independent random colors matching: **1 in 16,777,216**. With a 50×50 grid checking ~4 neighbors per cell per step, you'd need ~1,700 steps on average to see a *single* combination event. The "natural selection" effectively never fires. There is no color quantization, no distance threshold, no buckets.

#### **Gap F3: Rule 3 is a no-op**
[cellular_automaton.py:13–15](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/cellular_automaton.py#L13) resets `is_new = True` on **every cell at the start of every step**. The "only new cells can combine" check at [cell.py:22](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/cell.py#L22) is therefore always true. The `is_new` flag is dead state — it could be deleted with zero behavior change.

#### **Gap F4: "Amoeba" is a cosmetic flag, not a state**
Once `is_ameba=True` it's never reset, but `change_color()` still runs on amoebas every step — they keep randomly recoloring while drawn as ovals instead of rectangles. There's no amoeba lifecycle, no reproduction, no death, no fitness, no movement, no resource. "Evolution into complexity" is a one-bit shape swap.

#### **Gap F5: There is no selection pressure**
"Natural selection" implies fitness, reproduction, inheritance, and differential survival. This sim has none of those — it's random recolor + adjacency match. Calling it natural selection is marketing.

### 3.2 Code-quality gaps

#### **Gap C1: `main.py` and `main_new.py` are 99% identical**
The only difference: speed slider max is `10.0` in main, `1.0` in main_new. No README explains which to run. Pick one and delete the other.

#### **Gap C2: Speed slider is inverted**
The slider value is used as a **delay** in `canvas.after(int(slider * 1000))` at [main.py:42](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/main.py#L42). Higher value = slower simulation. Label says "Speed", behavior is "Delay". UX bug.

#### **Gap C3: Window close handler is broken**
[main.py:74](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/main.py#L74) binds `WM_DELETE_WINDOW` to `app.stop` — which only sets `self.running = False`. Clicking the X stops the animation but does not destroy the window. Should be `lambda: (app.stop(), root.destroy())`.

#### **Gap C4: Step button is not disabled during play**
Clicking Step while Play is running races with the scheduled callback — cells get an extra mutation between frames, animation stutters.

#### **Gap C5: `logging` is imported but never configured**
[cell.py:5](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/cell.py#L5) imports `logging` and emits `logging.info(...)`. Without `logging.basicConfig(level=INFO)` somewhere, every log message is silently discarded.

#### **Gap C6: O(W·H) full canvas rebuild every step**
[main.py:56](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/main.py#L56) calls `canvas.delete("all")` then redraws every cell. For 50×50 = 2,500 shapes/frame. Works at 50×50, dies above ~200×200. Should reuse canvas item IDs with `itemconfigure`.

#### **Gap C7: No seed / no reproducibility**
`random` is never seeded. Same simulation cannot be re-run. No way to share an interesting state.

### 3.3 Documentation gaps

#### **Gap D1: `requirements.txt` is not a requirements file**
[requirements.txt](https://github.com/rizzleroc/CellAutomata/blob/7c705f6/requirements.txt) contains markdown headings (`# README.md`, `## System Requirements`) instead of pip dependency lines. `pip install -r requirements.txt` would error out. Either delete it or put real content.

#### **Gap D2: Conflicting Python version claims**
- `requirements.txt` says `Python >= 3.6`
- `manual.md:7` says `Python 3.1 and above`
Python 3.1 is from 2009 and is not supported. Pick one — 3.9+ is reasonable for new work.

#### **Gap D3: README exposes a personal email**
`Justin@futurcraft.ai` is in the README. Use a GitHub issues link instead.

#### **Gap D4: No screenshot, no GIF, no demo link**
A visual project with no visual in the README. First-time visitors can't tell what it does without cloning and running.

#### **Gap D5: No LICENSE**
Repo is public with no license. Legally, nobody can use, fork, or contribute to it. Add MIT/Apache-2.0.

### 3.4 Engineering-hygiene gaps

| Missing | Impact |
|---|---|
| Tests (any kind) | Cannot refactor with confidence. Rules F1–F3 above would be caught by 3 unit tests. |
| CI (GitHub Actions) | No automated lint/test on PR. |
| `.gitignore` | First contributor will commit `__pycache__/`. |
| `pyproject.toml` | Can't `pip install .` Can't publish. No tool config (ruff/black/mypy). |
| Type hints | Zero. `Cell`, `CellularAutomaton` are dynamically typed. |
| Save/load state | Cannot persist or share simulations. |
| Headless mode | Cannot run as a benchmark or generate data — Tk is mandatory. |
| Metrics/stats panel | No "amoeba count", "step #", "FPS" — user can't observe what the sim is doing. |
| Pause-and-edit | Cannot paint cells, seed initial conditions, or set rules at runtime. |
| Presets | No "Conway's Life", "Wolfram Rule 30" — the project name promises a class of automata, ships one. |

---

## 4. Recommended Product Roadmap

> **Status (2026-05-21):** v1.1 → v3.1 are **shipped**. v3.0's original "web build" stretch was deliberately descoped (platform change, not a feature). The live roadmap is now **v3.2 — Living colony & visual identity**, below. See [PHASE2_BRUTAL.md §POST2](../PHASE2_BRUTAL.md) for the verified punch-list checkoff.

### v1.1 — Honesty release ✅ shipped
- Delete `main_new.py`.
- Fix `requirements.txt` (either remove or make valid).
- Add LICENSE, `.gitignore`, screenshot in README.
- Replace personal email with issue tracker link.
- Fix window-close bug, speed slider label, disable Step during Play.
- Configure `logging.basicConfig`.
- Reconcile Python version claims (commit to 3.9+).

### v1.2 — Make the simulation actually do what it claims ✅ shipped
- **F1:** Implement neighbor-color propagation (sample from 8-neighborhood).
- **F2:** Quantize colors to a ~16-color palette so "same color" actually happens.
- **F3:** Decide whether `is_new` means anything; if yes, gate it correctly; if no, delete.
- **F4:** Give amoebas a real lifecycle — stop recoloring them, give them a lifespan or reproduction rule.
- Add `--seed` CLI flag; show seed in UI.

### v2.0 — Real cellular-automata sandbox ✅ shipped
- Pluggable rule engine (`Rule` interface; ship Wolfram 1D, Conway's Life, and the current "natural selection" rule as three of N).
- Stats overlay: step count, FPS, population counts per state.
- Save/load `.json` snapshots.
- Headless `simulate` subcommand for batch runs / data export.
- Replace per-frame `canvas.delete("all")` with persistent item IDs + `itemconfigure` (10× speedup, supports 200×200+).
- Unit tests for each rule; CI on push.
- Optional: swap Tk for `pygame` or web-based (HTML canvas) so it's actually shareable.

### v3.0 — Educational artifact ✅ shipped (web build descoped)
- Inline per-rule tutorial mode. ✅
- Export run as GIF for sharing (non-blocking, progress + cancel). ✅
- Abiogenesis pipeline (5 stages, citation-backed origin-of-life concepts). ✅
- ~~Web build (Pyodide / JS rewrite)~~ — descoped: platform change, not a feature.

### v3.1 — Honest infrastructure ✅ shipped (2026-05-20)
- Eigen-Schuster hypercycle fitness replaces the Stage-4 placeholder.
- Windows+Ubuntu CI matrix, mypy, ruff format, `--cov-fail-under=80`, pip-audit.
- Catalytic Silence visual identity: bundled fonts, museum-plate sections, app icon, About dialog.
- CHANGELOG.md, version 3.1.0.

### v3.2 — Living colony & visual identity ✅ shipped (v4.2.0, 2026-06-03)
> Shipped: organic blob amoebas that breathe / ripple / look around and show
> faces at the default grid, an amoeba hero baked from the colony geometry, web
> favicons, a Catalytic-Silence chrome cleanup, and the Stage-4 / Rule-110 / CLI
> test+doc nits. Full spec + Definition of Done:
> [docs/design/V3_2_LIVING_COLONY.md](docs/design/V3_2_LIVING_COLONY.md).
The infrastructure is honest but the *experience* is unfinished. The signature "cuddly cartoon amoeba" exists only as the header mascot; the colony renders as flat colored dots with faces that never appear at the default grid. And we surface only 4 of ~16 generated art assets.
- **Living colony:** port the mascot's wobble / blink / 3D-highlight / blobby-body animation into the colony renderer, driven by a continuous tick so it's alive even when paused.
- **Visible faces by default:** fix the `FACE_MIN_CELL_PX` vs default-grid mismatch so the amoebas read as characters out of the box.
- **Organic bodies:** smoothed blob polygons with subtle membrane motion instead of perfect circles.
- **Use the art we generated:** surface orphaned `whipgen-out` plates, pick one canonical icon, generate the missing amoeba hero/sprite.
- **UI polish:** apply Catalytic Silence consistently to the canvas frame; review spacing/typography.
- **Residual test/doc nits:** Wolfram rule-110 test, CLI-subprocess tests, fix the stale Stage-4 fitness string in the tutorial.

See [PHASE2_BRUTAL.md §POST2](../PHASE2_BRUTAL.md) for the prioritized V0–V2 punch list.

---

## 5. Brutal Bottom Line

What you built: a **50×50 Tk grid that randomly recolors every step and rarely (statistically: never) draws an oval instead of a rectangle.** ~300 LOC, two copies of the main file, broken requirements file, broken window close, mislabeled slider, an "evolutionary" mechanic that fires once per ~1,700 frames by accident.

What the README sells: a **natural-selection simulator** with four interlocking rules.

**The gap between the marketing and the code is the entire product.** Rules 1, 3, and 4 are not implemented or are dead state. Rule 2 is implemented in a way that mathematically never fires. There is no selection, no fitness, no inheritance — the four words "simulates natural selection" do not survive contact with the source.

This isn't a code-quality problem you fix with linting. The simulation needs to be **rebuilt from the rule definitions down**, with the color-matching mechanic changed to make Rule 2 fire at a meaningful rate, and Rules 1/3/4 actually wired up. Until then, it's a screensaver, not a simulator.

The good news: the GUI shell, the Cell/CellularAutomaton split, and the play/step/stop control flow are a fine scaffold. The fix is ~100 lines, not a rewrite. v1.2 is a weekend.
