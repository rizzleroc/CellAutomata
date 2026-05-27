# cellauto · web 2.0

The follow-on to the original `docs/web/` Gray–Scott-only demo. Where v1
showed one stage on one canvas, v2.0 is a **multi-rule sandbox**: four
automata share the same canvas, controls, brush, and URL-state encoder.

No build step. No Python. Vanilla JS, opens straight from `file://`.

## Run

```
# Locally:
open docs/web2/index.html        # macOS
xdg-open docs/web2/index.html    # Linux

# Or serve with anything:
python3 -m http.server -d docs   # then visit /web2/
```

GitHub Pages: same root as v1 (`/docs`). The demo lives at
`https://<user>.github.io/<repo>/web2/`; v1 stays at `/web/`.

## What's in the box

| Rule | Description | Per-rule controls |
|---|---|---|
| **Conway** | Game of Life (B3/S23), toroidal. | density, wrap |
| **Wolfram 1D** | Elementary 1D CA, scrolling history. | rule number (0–255), random seed |
| **Gray–Scott** | Stage 1 PDE — same numerics as v1. | F, k, Pearson preset |
| **Primordial soup** | Stage 0 Brownian tracers with fading trails. | count, diffusion, evaporation, drift |

## What's new vs. v1

- **Rule switcher.** Pick any of the four from the dropdown or `1`–`4`.
- **Brush painting.** Click-drag to paint live cells / drop perturbation
  patches / inject particles. Right-click or shift-click to erase. Works
  on touch.
- **Speed control.** Steps-per-second slider; the RAF loop catches up.
- **Live readout bar.** Rule, generation, population, FPS.
- **URL hash state.** Every parameter is mirrored into the URL hash.
  "COPY LINK" copies the full URL — paste it into another browser, get
  the same rule at the same parameters.
- **Keyboard.** `space` play/pause, `s` step, `r` reset, `c` clear,
  `n` randomize, `1`–`4` rule.
- **Fullscreen.** Canvas-only fullscreen for projection.
- **Toast notifications.** Quiet confirmations on reset / clear / copy.
- **Responsive 2-column layout** that collapses to single-column below
  900 px.

## Files

- `index.html` — semantic structure.
- `styles.css` — Catalytic Silence palette + 2-column layout.
- `main.js`    — RAF loop, rule swap, URL state, brush, FPS, toast.
- `rules/conway.js`     — Game of Life (B3/S23).
- `rules/wolfram1d.js`  — elementary 1D CA, scrolling history.
- `rules/grayscott.js`  — Gray–Scott PDE + Pearson presets.
- `rules/soup.js`       — Brownian particles + fading trail field.
- `viridis.js`  — 32-entry viridis LUT shared with v1.

## Rule contract (for adding a fifth rule)

Each rule is a zero-arg factory registered on `CA.RULES`. The expected
object shape is documented in the footer comment of `main.js`. Drop a
new file in `rules/`, append a `<script>` tag in `index.html`, and add
the id to `RULE_ORDER` in `main.js`.

## What didn't make it

The other eight origin-of-life stages — alkaline vents, autocatalytic
sets, mineral catalysis, RAFs, homochirality, the RNA world, the genetic
code, coacervates, vesicles, LUCA distillation — are *not* JS ports.
Each is hundreds to thousands of lines of Python with NumPy / SciPy
dependencies. They remain Python-only:

```
pip install -e .
cellauto gui --rule abiogenesis-pipeline-extended
```

The gallery row at the bottom of the page links museum plates rendered
from the Python build for each missing stage.
