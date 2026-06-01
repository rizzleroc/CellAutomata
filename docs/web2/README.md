# cellauto · web 2.0

The follow-on to the original `docs/web/` Gray–Scott-only demo. Where v1
showed one stage on one canvas, v2.0 is a **multi-rule sandbox**: nine
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

Two reference automata frame seven abiogenesis building blocks. Digit
hotkeys `1`–`9` follow this order:

| # | Rule | Description | Per-rule controls |
|---|---|---|---|
| 1 | **Conway** | Game of Life (B3/S23), toroidal. *Reference automaton.* | density, wrap |
| 2 | **Wolfram 1D** | Elementary 1D CA, scrolling history. *Reference automaton.* | rule number (0–255), random seed |
| 3 | **Gray–Scott** | Reaction–diffusion morphogenesis — same numerics as v1. | F, k, Pearson preset |
| 4 | **Primordial soup** | Brownian tracers with fading trails. | count, diffusion, evaporation, drift |
| 5 | **Natural selection** | 16-species soup; same-species pairs condense into amoeba compartments. | amoeba lifespan, regime presets |
| 6 | **Homochirality** | Frank kinetics — L/R autocatalysis + mutual inhibition break mirror symmetry. | α, β, diffusion, noise |
| 7 | **Coacervate** | Cahn–Hilliard liquid–liquid phase separation into droplets. | mobility M, interface stiffness κ, substeps |
| 8 | **Alkaline vents** | Buoyant acetate plume from a hydrothermal vent source. | diffusion D, updraft, decay, source rate |
| 9 | **Vesicle** | Helfrich-type membrane flow — a lipid bilayer enclosing a lumen (*true* compartmentalisation, vs. coacervate's membrane-less kind). | membrane bending κ_b, relaxation M, substeps |

## What's new vs. v1

- **Rule switcher.** Pick any of the nine from the dropdown or `1`–`9`.
- **Guided tour.** `t` (or the TOUR button) auto-walks the chemistry-to-life
  arc — soup → vents → Gray–Scott → selection → chirality → coacervate →
  vesicle — skipping the two off-arc reference automata.
- **Brush painting.** Click-drag to paint live cells / drop perturbation
  patches / inject particles. Right-click or shift-click to erase. Works
  on touch.
- **Speed control.** Steps-per-second slider; the RAF loop catches up.
- **Live readout bar.** Rule, generation, population, FPS.
- **About this stage.** A collapsed-by-default panel under the readout
  expands to a ~50-word, origin-of-life explainer for the current rule.
- **URL hash state.** Every parameter (rule, SEM mode, palette, per-rule
  sliders) is mirrored into the URL hash. "COPY LINK" copies the full
  URL — paste it into another browser, get the same rule at the same
  parameters in the same palette.
- **Keyboard.** `space` play/pause, `s` step, `r` reset, `c` clear,
  `n` randomize, `1`–`9` rule, `m` SEM mode, `p` palette, `t` tour,
  `?` about/help, `esc` close.
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
- `rules/conway.js`            — Game of Life (B3/S23). *Reference automaton.*
- `rules/wolfram1d.js`         — elementary 1D CA, scrolling history. *Reference automaton.*
- `rules/grayscott.js`         — Gray–Scott PDE + Pearson presets.
- `rules/soup.js`              — Brownian particles + fading trail field.
- `rules/natural_selection.js` — 16-species soup → amoeba compartments.
- `rules/chirality.js`         — Frank kinetics, L/R symmetry-breaking.
- `rules/coacervate.js`        — Cahn-Hilliard liquid–liquid phase separation.
- `rules/vents.js`             — alkaline-vent acetate plume.
- `rules/vesicles.js`          — area-preserving Helfrich-type membrane flow.
- `viridis.js`  — 32-entry viridis LUT shared with v1 (legacy mode only).
- `tests/smoke.mjs` — zero-dependency node harness exercising every rule.

## Tests

```
node docs/web2/tests/smoke.mjs
```

Loads each rule module against a `window` stub and runs it through
seed → step → render → renderHeight → paint, asserting no method throws
and no buffer goes non-finite. Also checks the data contracts:
`controlConsequence` keys must name real params, and every `presets`
value must fall inside its slider range. The GitHub Pages workflow runs
this as a gate before deploying, so a broken rule can't ship.

## Rule contract (for adding a rule)

Each rule is a zero-arg factory registered on `CA.RULES`. The expected
object shape is documented in the footer comment of `main.js`. Drop a
new file in `rules/`, append a `<script>` tag in `index.html`, and add
the id to `RULE_ORDER` in `main.js`.

To get a rule into SEM mode, also implement `renderHeight(out:
Float32Array)` — write your primary scalar field (anything in [0, 1])
into `out`; the SEM renderer does the rest. If you skip it, the rule
falls back to its flat-colour `render(pixels)` path even with SEM mode
on. Optional: a `presets` array of `{ label, hint, values, reseed? }`
regimes renders a one-click regime row above the sliders.

## What didn't make it

Nine rules ship as JS ports: the two reference automata (Conway,
Wolfram 1D) plus seven building blocks — primordial soup, natural
selection, Gray–Scott morphogenesis, alkaline vents, homochirality,
coacervates, and lipid vesicles.

Four further building blocks remain Python-only — autocatalytic sets
(Kauffman), the RNA world (Eigen quasispecies), the genetic code
(Vetsigian–Woese–Goldenfeld), and LUCA. Each is several hundred lines
of NumPy / SciPy and resists a faithful JS port:

```
pip install -e .
cellauto gui --rule abiogenesis-pipeline-extended
```
