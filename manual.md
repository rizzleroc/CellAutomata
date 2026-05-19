# cellauto — User Manual

cellauto is a sandbox for cellular automata. It ships three rule sets, a Tk GUI,
a headless CLI, and animated-GIF export.

## Install

```bash
pip install -e .
```

Python 3.10+ is required. Tk ships with Python on Windows and macOS; on Linux
install `python3-tk` from your package manager.

## Running it

### GUI

```bash
cellauto gui
cellauto gui --rule conway --grid 100 --seed 42
```

### Headless

```bash
# Run 200 steps of Conway, print final population, save snapshot.
cellauto simulate --rule conway --grid 80 --steps 200 --seed 7 --save snapshots/life.json

# Resume from a snapshot in the GUI.
cellauto gui --load snapshots/life.json
```

### GIF export

```bash
cellauto export --rule wolfram1d --grid 120 --steps 80 --fps 12 --out exports/rule30.gif
```

## GUI controls

| Control | What it does |
|---|---|
| Rule dropdown | Switch rule set (`natural-selection`, `conway`, `wolfram1d`). Resets the grid. |
| Grid dropdown | 30, 60, 100, or 150 cells per edge. Larger grids are slower. |
| Reseed | Re-roll the RNG seed; the new seed appears in the status bar. |
| Step | Advance one tick. Disabled while Play is running. |
| Play / Stop | Toggle continuous stepping at the rate set by the FPS slider. |
| FPS slider | Target steps per second, 1–60. |
| Tutorial | Step through an in-window explanation of the natural-selection rules. |
| Record GIF | Start capturing live frames; click again to save the GIF. |
| File ▸ Save / Open | Persist the current state to JSON and reload it later. |
| File ▸ Export GIF | Run 60 steps from current state and save as a GIF. |

The status bar at the bottom always shows the current rule, seed, step count,
recent FPS, and a population breakdown.

## Rule reference

### natural-selection (the original v1 sim, fixed)

1. **Color propagation.** Every non-amoeba cell takes the color of a random
   Moore-neighborhood (8-cell) neighbor.
2. **Combination.** Two adjacent cells that just changed color *and* share that
   color combine, taking a new palette color.
3. **Newness.** Only cells whose color shifted this step are eligible to
   combine. Settled cells must wait for color flow to reach them.
4. **Amoeba lifecycle.** A combined pair turns into a pair of amoebas (drawn as
   ovals). Amoebas stop changing color and die after 25 steps, freeing space.

Uses a 16-color palette so combination events fire on a human timescale —
the v1 code used random 24-bit colors and combinations effectively never
happened.

### conway — Conway's Game of Life

Standard B3/S23: a dead cell with exactly 3 live neighbors comes alive; a live
cell with 2 or 3 live neighbors survives. Toroidal wrap on by default.

### wolfram1d — Elementary 1D automaton

The bottom row is the current 1D generation. Each step computes the next
generation from the rule number (0–255) and scrolls history upward. Defaults
to rule 30. Try rule 110 for Turing-complete chaos, rule 90 for the Sierpiński
triangle.

## Reproducibility

Every run is deterministic from its seed. Two runs with the same `--seed`
produce bit-identical evolution. Saved snapshots round-trip the seed.

## Troubleshooting

- **GUI won't open on Linux:** install `python3-tk` (`apt install python3-tk`).
- **GIF is huge:** drop `--canvas` (default 600 px) or `--steps`. Pillow
  optimizes the palette automatically.
- **Simulation is slow at grid 150:** that's 22,500 cells per step. The renderer
  is fine up to ~200 px; computation is the bottleneck. Drop the FPS or grid.
