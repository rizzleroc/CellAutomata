# cellauto · web 2.0

The follow-on to the original `docs/web/` Gray–Scott-only demo. Where v1
showed one stage on one canvas, v2.0 is a **multi-rule sandbox**: four
automata share the same canvas, controls, brush, and URL-state encoder.
v4.0 added SEM-grade rendering — depth-shaded, lit, tone-mapped through
a warm-sepia or cool-mono LUT, framed as a live instrument feed.

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
- **URL hash state.** Every parameter (rule, SEM mode, palette, per-rule
  sliders) is mirrored into the URL hash. "COPY LINK" copies the full
  URL — paste it into another browser, get the same rule at the same
  parameters in the same palette.
- **Keyboard.** `space` play/pause, `s` step, `r` reset, `c` clear,
  `n` randomize, `1`–`4` rule, `m` SEM mode, `p` palette.
- **Fullscreen.** Canvas-only fullscreen for projection.
- **Toast notifications.** Quiet confirmations on reset / clear / copy.
- **Responsive 2-column layout** that collapses to single-column below
  900 px.

## v4.0 additions — SEM-grade rendering

Mirrors `docs/PRD_SEM_VISUALIZATION.md` Phase 1 in pure JS, no server
round-trip:

- **Depth-shaded surface rendering.** Each rule exposes a scalar
  `renderHeight(out)` method. The renderer treats the field as a height
  map: separable Gaussian blur → Sobel gradients → normals →
  Lambertian + ambient + Blinn-Phong specular → ambient occlusion via
  laplacian → procedural noise → tone-mapped through a 256-entry LUT.
- **Two palettes.** *Warm-sepia* (default — matches the PRD reference
  image) and *cool-mono* (the existing Catalytic Silence palette
  extended into 3-D shading). Picker in the configuration sidebar or
  `p` cycles.
- **Instrument identity.** Live SEM-feed badge (upper-right, 2.2 s
  opacity pulse), centred crosshair reticle, quadrant tick marks,
  corner vignette, scale-bar microcopy below the canvas.
- **Marginalia ticker.** Per-rule citations and notes cycle every
  6.5 s — Gardner/Conway, Wolfram/Cook, Turing/Pearson, Oparin/Haldane.
- **A/B toggle.** `View ▸ SEM mode` checkbox (or `m`) flips between
  v4.0 SEM rendering and the v3.x flat-colour path; SEM mode is on by
  default per the PRD F7 acceptance criterion.
- **Reduced-motion respect.** `prefers-reduced-motion: reduce`
  disables the badge pulse, the marginalia fade, the toast slide-in.

## Files

- `index.html` — semantic structure.
- `styles.css` — Catalytic Silence palette + 2-column layout.
- `main.js`    — RAF loop, rule swap, URL state, brush, FPS, toast,
                 SEM toggle, palette picker, marginalia ticker.
- `sem.js`     — v4.0 depth-shading pipeline + warm-sepia / cool-mono
                 LUTs. Pure JS, no allocations in the hot loop.
- `rules/conway.js`     — Game of Life (B3/S23).
- `rules/wolfram1d.js`  — elementary 1D CA, scrolling history.
- `rules/grayscott.js`  — Gray–Scott PDE + Pearson presets.
- `rules/soup.js`       — Brownian particles + fading trail field.
- `viridis.js`  — 32-entry viridis LUT shared with v1 (legacy mode only).

## Rule contract (for adding a fifth rule)

Each rule is a zero-arg factory registered on `CA.RULES`. The expected
object shape is documented in the footer comment of `main.js`. Drop a
new file in `rules/`, append a `<script>` tag in `index.html`, and add
the id to `RULE_ORDER` in `main.js`.

To get a rule into SEM mode, also implement `renderHeight(out:
Float32Array)` — write your primary scalar field (anything in [0, 1])
into `out`; the SEM renderer does the rest. If you skip it, the rule
falls back to its flat-colour `render(pixels)` path even with SEM mode
on.

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
