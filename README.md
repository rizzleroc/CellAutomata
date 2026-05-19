# cellauto

[![CI](https://github.com/rizzleroc/CellAutomata/actions/workflows/ci.yml/badge.svg)](https://github.com/rizzleroc/CellAutomata/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

A pluggable cellular-automata sandbox with a Tk GUI, headless CLI, and animated-GIF export.

![cellauto natural-selection rule after 20 steps on a 60x60 grid, seed 42](docs/hero.png)

Ships three rule sets:

- **`natural-selection`** — the original 4-rule simulator from v1.0, this time actually implemented. Neighbor-color propagation, quantized 16-color palette so combinations fire regularly, real `is_new` and amoeba lifecycles.
- **`conway`** — Conway's Game of Life (B3/S23, optional toroidal wrap).
- **`wolfram1d`** — elementary 1D automaton (any rule number 0–255) drawn as a scrolling 2D history.

## Install

```bash
pip install -e .
# or, for development:
pip install -e ".[dev]"
```

Requires Python 3.10+. The Tk GUI uses the stdlib `tkinter`; GIF export uses Pillow.

## Quick start

```bash
# launch the GUI
cellauto gui --rule natural-selection --grid 60 --seed 42

# headless: run 100 steps, print final population
cellauto simulate --rule conway --grid 80 --steps 100 --seed 1

# render an animated GIF
cellauto export --rule wolfram1d --grid 100 --steps 60 --fps 12 --out run.gif
```

## GUI controls

- **Rule / Grid dropdowns** — pick a rule set and grid size.
- **Reseed** — start a new run with a fresh RNG seed (shown in the status bar).
- **Step / Play / Stop** — advance one step, or run continuously at the FPS slider's rate.
- **Tutorial** — walk through what each of the 4 natural-selection rules does.
- **Record GIF** — capture live frames and save when you stop.
- **File ▸ Save snapshot / Open snapshot** — freeze a state to JSON and reload it later.

## Reproducibility

Every run is fully deterministic from its seed. The status bar shows the current seed; saved snapshots round-trip the seed alongside the cell state.

## Project layout

```
cellauto/
  engine.py          # Grid + Rule driver, seed, save/load
  grid.py            # generic 2D grid container
  app.py             # Tk GUI
  export.py          # animated-GIF rendering (Pillow)
  __main__.py        # `cellauto` CLI
  rules/
    base.py          # Rule protocol
    natural_selection.py
    conway.py
    wolfram1d.py
tests/               # pytest suite (14 tests, runs in <1s)
docs/                # screenshots
exports/, snapshots/ # GIF + JSON outputs (gitignored)
```

## Development

```bash
pytest                 # unit tests
ruff check cellauto    # lint
cellauto gui --seed 1  # poke at the UI
```

## History

The original v1.0 (March–April 2024) advertised four interlocking rules but implemented none of them correctly — see [PRD.md](PRD.md) for the full gap analysis. v2.0 is the fix: actual neighbor-color propagation, a 16-color palette that lets combinations happen on a human timescale, real amoeba lifecycles, a pluggable rule engine, headless mode, save/load, GIF export, tests, CI.

## License

MIT — see [LICENSE](LICENSE).
