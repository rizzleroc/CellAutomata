# cellauto · web demo

A single-page in-browser live Gray–Scott reaction–diffusion explorer — ported
from Stage 1 of the cellauto abiogenesis sandbox. Loads in ~150 KB (HTML +
CSS + a few hundred lines of vanilla JS; Google Fonts streamed externally).
No Python, no Pyodide, no build step.

## Run

Just open `index.html` in a browser, or deploy to GitHub Pages from
`docs/web/`:

1. **Repo Settings → Pages**: set the source to *deploy from a branch*, branch
   `main`, folder `/docs`.
2. The demo lives at `https://<user>.github.io/<repo>/web/`.
3. The empty `docs/.nojekyll` ensures Pages serves files starting with `_`
   unmodified (insurance — we don't actually have any here).

## What it shows

The headline result of cellauto's Stage 1: the Gray–Scott PDE

    ∂u/∂t = Du ∇²u − uv² + F(1 − u)
    ∂v/∂t = Dv ∇²v + uv² − (F + k)v

manufactures emergent self-replicating spots from a featureless initial
state — the core argument the full simulator builds around. The five
Pearson (1993) regimes — `spots`, `stripes`, `mitosis`, `waves`,
`labyrinth` — are one combobox click away.

## What it doesn't

The other eleven origin-of-life rules in the desktop build (soup, alkaline
vents, autocatalytic sets, mineral catalysis, RAFs, homochirality, RNA
world, genetic code, coacervates, vesicles, protocell selection, LUCA
distillation) are *not* ported — they would be a JS rewrite of about 4,000
lines of Python apiece. Instead, the page exhibits a static museum-plate
gallery of each one rendered by the desktop build (`docs/generated/*.png`).
For everything past Stage 1, install the Python build:

    pip install -e .
    cellauto gui --rule abiogenesis-pipeline-extended

## Files

- `index.html` — semantic structure, ~115 lines.
- `styles.css` — Catalytic Silence palette + typography.
- `sim.js`     — Gray–Scott PDE port + RAF loop + UI wiring.
- `viridis.js` — 64-entry viridis lookup table.
- `presets.js` — the five Pearson (F, k) pairs.
- `assets/`    — none on disk (gallery images are loaded from
  `../generated/`).
