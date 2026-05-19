# cellauto

[![CI](https://github.com/rizzleroc/CellAutomata/actions/workflows/ci.yml/badge.svg)](https://github.com/rizzleroc/CellAutomata/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

A scientifically-grounded cellular sandbox exploring the **chemistry-to-life
transition** — the abiogenesis problem — across five stages, plus the two
canonical reference cellular automata (Conway, Wolfram 1D) for comparison.

![Gray-Scott reaction-diffusion at step 400 — self-replicating spots](docs/hero.png)

*Stage 1 — Gray-Scott reaction-diffusion at step 400. Pearson (1993)
"spots" preset (F=0.035, k=0.065). The self-replicating spots are the
project's hero result: a four-parameter PDE producing emergent
protocell-like division.*

## What this project actually is

The original v1.0 README called this a "natural-selection simulator." It
isn't. Read carefully, the four rules sketched in v1.0 describe the
prebiotic-chemistry chapter of the origin-of-life story: random mixing,
condensation, activated intermediates, compartmentalization. v3.0 honors
that intuition by implementing each stage with real (or toy-but-real-
concept) scientific machinery and citing the canonical literature.

See [docs/science.md](docs/science.md) for the full citation list and the
math behind each stage. The short version:

| Stage | Concept | Science |
|---|---|---|
| 0 — primordial soup | Discrete molecules mixing, condensing into protocells | Oparin (1924), Haldane (1929), Miller-Urey (1953) |
| 1 — reaction-diffusion | Gray-Scott PDE producing self-replicating spots | Turing (1952), Gray-Scott (1985), Pearson (1993) |
| 2 — autocatalytic sets | Kauffman RAFs — closed catalytic cycles in random networks | Kauffman (1986), Hordijk & Steel (2004) |
| 3 — vesicle formation | Lipid self-assembly above the critical micelle concentration | Helfrich (1973), Deamer, Szostak Lab |
| 4 — protocell selection | Hypercycle dynamics: variation, inheritance, selection | Eigen & Schuster (1977), Szostak |

The `abiogenesis-pipeline` rule walks all five stages end to end.

## Install

```bash
pip install -e .
# or, for development:
pip install -e ".[dev]"
```

Python 3.10+ required. Stdlib `tkinter` for the GUI; `numpy` for the
continuous-field stages; `Pillow` for GIF export.

## Quick start

```bash
# Launch the GUI with the full abiogenesis pipeline.
cellauto gui

# Pick a specific stage to study in isolation.
cellauto gui --rule abiogenesis-stage1-grayscott --grid 100

# Headless: run 200 steps of stage 2 with a fixed seed.
cellauto simulate --rule abiogenesis-stage2-raf --grid 80 --steps 200 --seed 7

# Render an animated GIF — Pearson's "mitosis" preset, 60 frames.
cellauto export --rule abiogenesis-stage1-grayscott \
    --rule-config preset=mitosis --grid 100 --steps 60 --out exports/mitosis.gif

# Wolfram rule 110 (Turing-complete) — pick a specific rule number.
cellauto simulate --rule wolfram1d --rule-config rule_number=110 --grid 80 --steps 50

# Resume a run from a snapshot.
cellauto gui --load snapshots/my-run.json
```

## Performance

The honest perf story for the v3.0 renderer:

| Renderer | Used by | 80×80 / 30 frames | 200×200 / 30 frames |
|---|---|---|---|
| FieldRenderer (numpy → PhotoImage blit) | Stages 1–4 | 0.39 s | 0.08 s |
| DiscreteRenderer (canvas items) | Stage 0, Conway, Wolfram | 0.60 s | (slow, not recommended) |
| v1 `canvas.delete("all")` (baseline) | (was used by v2.0) | 2.87 s | dies |

So: **~7× speedup for the continuous-field stages**, which are the new ones.
The discrete-cell renderer is comparable to v1 — Tk Canvas items are
inherently slow per item; the fix in v3.0 was correcting v2.0's claim and
removing a buggy per-cell `canvas.type()` roundtrip that made it *slower*
than v1 in practice.

## Rule registry

| Rule name | Renderer | What it is |
|---|---|---|
| `abiogenesis-pipeline` | mixed | All 5 stages, auto-promoting |
| `abiogenesis-stage0-soup` | discrete | Primordial soup with rules 1–4 |
| `abiogenesis-stage1-grayscott` | field | Gray-Scott reaction-diffusion |
| `abiogenesis-stage2-raf` | field | Kauffman RAF autocatalytic chemistry |
| `abiogenesis-stage3-vesicles` | field | Lipid bilayer self-assembly |
| `abiogenesis-stage4-selection` | field | Protocell selection / hypercycle |
| `conway` | discrete | Conway's Game of Life (B3/S23) |
| `wolfram1d` | discrete | Elementary 1D automaton, rule 0–255 |
| `natural-selection` | discrete | **Legacy alias** — same mechanics as Stage 0 |

## GUI controls

- **Rule / Grid dropdowns** — pick a rule and grid size.
- **Reseed** — fresh RNG seed (shown in the status bar).
- **Promote stage** — for the pipeline rule, manually advance to the next stage.
- **Step / Play / Stop** — single-step or run at the FPS slider's rate.
- **Tutorial** — per-rule walkthrough with citations.
- **Record GIF** — capture live frames + save.
- **File ▸ Save / Open snapshot** — persist state to JSON (RNG state + rule
  config round-trip exactly — load-then-step matches continuous run).
- **File ▸ Export GIF** — render N frames headlessly to a GIF.

## Reproducibility

Every run is deterministic from its seed *including* across save/load.
v2.0 had a bug where `Engine.load` reset the RNG; v3.0 serializes the RNG
state alongside the cell state so a snapshot + continuation matches a
continuous run bit-for-bit.

## History

The project's history is its own gap analysis:

- **v1.0** (2024): "natural-selection simulator" that didn't implement
  any of its four rules correctly. See the original
  [PRD.md](PRD.md) for the brutal gap analysis.
- **v2.0** (2026-05-18): a working sandbox with pluggable rules, headless
  CLI, GIF export, tests, CI. Three of the headline claims didn't survive
  a careful read; see [PHASE2_BRUTAL.md](../PHASE2_BRUTAL.md) (the self-audit).
- **v3.0** (2026-05-19): the science-based rebuild. Reframed as
  abiogenesis (the project's true premise). Stage 0 fixes the Rule 3 bug
  v2.0 left as a no-op. Stages 1–4 add real reaction-diffusion (Turing /
  Gray-Scott), Kauffman RAFs, lipid self-assembly, and hypercycle-based
  protocell selection with citations to the original literature.

45 tests, all passing. See [docs/science.md](docs/science.md) for the math
and citations.

## License

MIT — see [LICENSE](LICENSE).
