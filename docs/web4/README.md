# cellauto · web 4.0 — canonical current

The forward-merge of `docs/web3/` (v4.1 SEM + sprite layer) carrying the
**v5.0 LIFE** cycle: the post-LUCA **Stage XIII — Digital Life** rule
(`rules/life.js`) — virtual-CPU organisms that ingest, divide, and mutate
under selection — alongside the depth-shaded SEM substrate and bioform
**sprite layer** so each rule reads as a microscope view of the chemistry
rather than a colour-mapped scalar field. `/` redirects here; `web3/`,
`web2/`, `web/` are preserved for the record.

No build step. No Python. Vanilla JS, opens straight from `file://`.

## Run

```
# Locally:
open docs/web3/index.html        # macOS
xdg-open docs/web3/index.html    # Linux

# Or serve with anything:
python3 -m http.server -d docs   # then visit /web3/
```

Railway / GitHub Pages: lives at `https://<host>/web3/` alongside the
preserved `/web2/` and `/web/` bundles. `docs/index.html` redirects
the root URL to `/web3/`.

## What's new vs. v2.0

### v4.1 PRD §F3 — sprite-overlay layer

Every continuous-field rule renders in three composed passes:

1. **SEM depth-shaded substrate** (v4.0) — height field → Sobel
   gradients → Lambertian + specular + AO → tone-map LUT.
2. **Sprite layer** (v4.1, NEW) — biologically-recognisable shapes
   placed at simulation-derived coordinates: bone-cream protocell
   spheres for Gray-Scott spots, lipid-bilayer rings for vesicles,
   coacervate droplet outlines, mineral honeycomb cells for vents,
   L/D chirality glyphs, amoeba blobs for natural selection,
   coloured granules for soup tracers.
3. **Instrument chrome** (v4.0) — LIVE SEM FEED badge, reticle,
   vignette, scale-bar.

The sprite layer is procedural (canvas drawing primitives, no PNG
asset pipeline) so the bundle stays small and the sprites are tinted
to whatever SEM palette is active. Each rule's `sprites()` method
returns descriptors driven by its simulation state — local maxima of
the field for grayscott / vesicles / coacervate / chirality, every
amoeba cell for natural-selection, every particle for soup, every
mineral wall cell for vents. Conway and Wolfram 1D supply no sprites
(off-arc reference automata).

Toggle via the **sprites** checkbox in the configuration sidebar or
the `x` hotkey — flips between substrate-only and substrate +
sprites for direct comparison.

**Sprite mode is OFF by default** (v4.1.1 calm-overlay revision —
the v4.1.0 launch defaulted sprites on and the layer dominated the
SEM substrate; the layer is now an opt-in annotation, not the
default view). Painters are outline-and-core-dot rather than filled
gradient blobs, composited at `globalAlpha 0.72` so the substrate
shows through. Densities (per-rule local-max thresholds, stride
sizes) are tuned so a saturated grid emits ~100-300 sprites, not
~1000+.

### Ninth building block: lipid vesicles (Stage 3)

```
∂φ/∂t = D ∇²φ − γ φ(1−φ)(½−φ) − κ (∇²)²φ + noise
```

`rules/vesicles.js` ports the Helfrich-curvature lipid bilayer
described in `cellauto/rules/abiogenesis/stage3_vesicles.py`. The
`(∇²)²φ` biharmonic term is the bending energy that closes the
membrane into a sphere — the defining property of a real vesicle
(distinct from coacervate's liquid-liquid droplets, which have no
membrane). Sprites are concentric bilayer rings at local maxima of
φ above the vesicle threshold.

## What's in the box

| Rule | Building block | Sprite | Description |
|---|---|---|---|
| Conway | — (reference) | — | Game of Life (B3/S23) |
| Wolfram 1D | — (reference) | — | Elementary 1D CA |
| Gray–Scott | pattern | protocell-sphere | Reaction-diffusion spots |
| Soup | matter | granule | Brownian primordial soup |
| Natural selection | identity | amoeba | 16-species amoeba formation |
| Chirality | symmetry-breaking | chirality-glyph (L/D) | Frank kinetics |
| Coacervate | membrane-less compartment | coacervate-droplet | Cahn-Hilliard LLPS |
| Vents | place + power | mineral-cell honeycomb | Alkaline-vent chimney |
| **Vesicles** *(new)* | true bilayer compartment | vesicle-bilayer | Helfrich-curvature lipid sphere |
| **Digital life** *(new)* | open-ended evolving lineage | digital-organism | Stage XIII Tierra/Avida virtual-CPU organisms |

## Files

```
docs/web3/
├── README.md             this file
├── PUNCHLIST.md          tracks the gap to GOAL (carried fwd from v2)
├── index.html            v3 branding, sprite-mode checkbox, vesicles wired in
├── styles.css            unchanged from v2
├── main.js               v3.0 controller — sprite compose pass, sprite-mode
│                         toggle persisted in URL hash, "x" hotkey,
│                         "1-9" rule keys (vesicles is rule 9)
├── sem.js                v4.0 SEM rendering pipeline (unchanged)
├── sprites.js            NEW — bioform sprite library (7 sprite kinds)
├── viridis.js            32-entry viridis LUT (legacy mode only)
└── rules/
    ├── conway.js
    ├── wolfram1d.js
    ├── grayscott.js          sprites: protocell-sphere @ local maxima of v
    ├── soup.js               sprites: granule per tracer
    ├── natural_selection.js  sprites: amoeba per amoeba cell (stride-2)
    ├── chirality.js          sprites: chirality-glyph L/D @ |L−R| maxima
    ├── coacervate.js         sprites: coacervate-droplet ring @ φ maxima
    ├── vents.js              sprites: mineral-cell honeycomb on chimney walls
    ├── vesicles.js           NEW — Helfrich PDE + vesicle-bilayer ring sprites
    └── life.js               NEW — Stage XIII digital-life virtual CPU + organisms
```

## Rule contract (for adding a tenth rule)

Each rule is a zero-arg factory registered on `CA.RULES`. The full
contract is documented in the footer comment of `main.js`. New in
v3.0: an optional `sprites(width, height) → [{kind, x, y, scale, …}]`
method that the renderer composites over the SEM substrate. See
`docs/web3/sprites.js` for the available sprite kinds and their
descriptor shapes; adding a new kind is one painter function +
one registry entry.

## What's still Python-only

Four building blocks remain unported — autocatalytic sets (Kauffman),
the RNA world (Eigen quasispecies), the genetic code
(Vetsigian–Woese–Goldenfeld), and LUCA. Each is several hundred
lines of NumPy / SciPy and needs careful per-stage simplification.
`pip install -e .` then `cellauto gui` for those.
