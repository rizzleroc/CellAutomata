# cellauto · web7 — "Catalytic Silence"

A catalogue page from a discipline that does not yet exist. web7 takes web6's
proven engine — the photoreal Three.js **laboratory apparatus** and the **live
web3 SEM physics** running beside it — and reuses it **byte-identical** beneath a
brand-new museum-vitrine shell. The shell sets the specimen against a deep
**obsidian** void; the apparatus glasswork and the live micrograph become the
only luminous things in the room. Colour is information here, so it is rationed:
a single **luminous teal** carries structure and the playback "breath", a rarer
**magenta** marks the catalyst landing, and everything else is **bone-white**
text floating with the restraint of a museum caption printed in 1962. The
typography is the laboratory's own grammar — a high-contrast didone
(**Italiana**) for the one titular gesture, a reading serif italic (**Crimson
Pro**) for the wall labels, and a geometric monospace (**IBM Plex Mono**) at
near-microscopic sizes for plate numbers, specimen identifiers and scale-bar
metadata. The composition follows the logic of the vitrine and the scientific
journal: one dominant specimen given the dignity of breath, framed by deep
negative space and held together by the geometry of the page rather than by
ornament. The shell is new; the experiment engine (reused from web6) has since
been deepened — see [`PUNCHLIST.md`](PUNCHLIST.md).

Design language: [`../design/catalytic-silence.md`](../design/catalytic-silence.md)
· [`../design/UX_SPEC_WEB7.md`](../design/UX_SPEC_WEB7.md).

No build step. Vanilla ES modules + Three.js via importmap (CDN). Opens from
`file://` or any static server.

```bash
python3 -m http.server -d docs   # then visit /web7/
```

## What ships

**All 13 stages are built** — Stage 0 + the 11-stage pipeline + the stromatolite
capstone — each a photoreal apparatus you can orbit, take apart (exploded-view
slider), and *run*. Every apparatus exposes named parts and an anim contract;
beside it the web3 physics + SEM pipeline runs the matching
origin-of-life simulation in real time. The apparatus modules and the
camera/run/explode semantics are carried over from web6; the `experiment/`
rules began as web6's copies but have since been **deepened in web7** — real
per-stage controls, a genuine mineral-catalysis model, and a proton-gradient
vent (see [`PUNCHLIST.md`](PUNCHLIST.md) for the full audit).

| # | Stage | Apparatus |
|---|---|---|
| 0 | Primordial soup | Miller–Urey spark-discharge rig (hero) |
| 1 | Reaction–diffusion | Belousov–Zhabotinsky Petri dish |
| 2 | Autocatalytic sets | Reaction flask + magnetic stir plate |
| 3 | Vesicles | Phase-contrast microscope + slide |
| 4 | Hydrothermal vent | Alkaline-vent bench reactor (PMF/ΔG readout) |
| 5 | Mineral catalysis | Montmorillonite clay reactor |
| 6 | Homochirality | Soai reaction + polarimeter |
| 7 | RNA world | PCR thermocycler + gel-doc |
| 8 | Genetic code | In-vitro translation bench |
| 9 | Coacervates | Oparin droplets under the microscope |
| 10 | Protocell selection | Microfluidic culture chip |
| 11 | LUCA | Genomics console + tree-of-life hologram |
| — | Capstone | Stromatolite hand specimen (~3.5 Ga) |

### The museum shell

- **Top register** — the museum header: the didone wordmark `cellauto` with its
  italic subtitle, a breathing **status dot**, and a monospace meta-line that
  tracks the live **plate number** (`PL. 0`, then Roman numerals `PL. I…XI`, `PL.
  ✦` for the capstone), the current **mode** (`LAB` / `SPLIT` / `LIVE · SEM`), and
  the catalogue mark `cat. — Catalytic Silence`.
- **Stage index** (left) — the catalogue of plates, one entry per stage, each
  showing its numeral, name and apparatus subtitle. The active plate is marked by
  a teal hairline and a glowing numeral; placeholder stages read as `pending`.
- **Specimen** (centre) — the dominant subject, framed as a vitrine with corner
  ticks. A **Lab | Split | Micrograph** radiogroup composes it: Lab shows the
  apparatus alone, Micrograph the live plate alone, Split a 50/50 with a divider.
  Beneath it sit the **wall label** (`Stage N — …`, the title, and a blurb) and
  the **instrument bar**: a single **Run/Stop** control, the **Exploded view**
  slider, a teal per-stage **readout** (e.g. `organics collected · 42%`), and the
  view toggle.
- **SEM scientific-plate framing** — the live micrograph is a `figure.plate`
  letterboxed at `aspect-ratio: 1 / 1` (never anisotropically stretched), matted
  with corner **registration ticks**, a `LIVE · SEM` badge with a recording dot, a
  `50 µm` **scale bar**, and an italic caption. A stage with no mapped rule shows a
  tasteful **"specimen pending"** state instead of crashing.
- **Right rail — tabbed: Parameters | Apparatus** (`role="tablist"`).
  - **Parameters** — the live experiment's *own* tunable knobs, read straight from
    the running rule's `params` schema (the same controls web2/web3 exposed):
    Gray–Scott feed-rate **F** / kill-rate **k** / Pearson **preset**, soup
    gas-density/spark/reducing, RAF catalysis/decay, vent **proton-motive force**,
    mineral **clay catalysis** (k_clay/k_bulk), LIFE mutation rate, … — plus a
    per-stage **Regime** picker that applies each rule's named presets (e.g.
    minerals' "surface catalysis" vs its "no catalysis" control), two global
    controls (**Speed** in steps · s⁻¹ and SEM **Palette**), and **Step** /
    **Reset** transport. Every control is genuinely wired — PDE rules read
    `params.X.value` live each step so a slider takes effect mid-run, and
    `rule.onParamChange()` handles cascades. Per-knob `controlConsequence` text is
    surfaced as the control's tooltip; the Regime picker shows each preset's hint.
    On narrow screens the rail becomes a slide-in drawer so **no control is lost**.
  - **Specimen key** — the named apparatus parts as a monospace list. Hover or
    focus illuminates a part (emissive lift); selecting it veils that part
    (toggles `mesh.visible`), with `aria-pressed` reflecting the state.
- **Self-hosted brand fonts** — Italiana, Crimson Pro (regular + italic), and IBM
  Plex Mono (regular + bold) are shipped in `assets/fonts/` and declared via
  `@font-face` with `font-display: swap`. The three hero faces are `<link
  rel="preload">`-ed. **No runtime network dependency** for type; the page renders
  in the intended grammar offline.
- **Full accessibility** — a skip-link to the specimen; a polite `aria-live`
  region that announces meaningful state (stage changes) but never the per-frame
  telemetry; the index is a proper vertical menu (Up/Down move focus, Home/End
  jump, Enter/Space activate) with the active plate exposed via `aria-current`;
  the view toggle is a `role="radiogroup"` with `aria-checked`; Run carries
  `aria-pressed`; a visible `:focus-visible` ring throughout; a
  `prefers-reduced-motion` block that freezes the breath, the caption rise and all
  transitions (honoured in CSS **and** in the controller); and a `forced-colors`
  fallback that keeps the structure legible.
- **Responsive** — three-column vitrine on the desktop; at ≤1180px the control
  rail (Parameters + specimen key) becomes a slide-in **drawer** opened from a
  `⚙ Controls` launcher (so no control is lost — UX_SPEC §4.2), and the stage
  index drops at ≤860px, where the page goes to a single scrolling column with the
  panes stacked and the instrument bar made sticky.

### Live SEM experiment (the engine, reused)

Beside the apparatus the **same web3 physics + SEM depth-shading pipeline** runs
the matching simulation. `experiment/` holds the web3 SEM engine (`viridis.js`,
`sem.js`, `sprites.js`) plus the mapped rule files — several of which web7 has
since extended (real controls, `minerals.js`, the proton-gradient `vents.js`;
see [`PUNCHLIST.md`](PUNCHLIST.md)) —
loaded as **classic `<script>` tags before the ES-module `main.js`**, so
`window.SEM`, `window.CA.RULES`, and the bare `VIRIDIS_LUT` global all exist when
`main.js` runs (the globals bridge the module / classic-script worlds, with no
build step; `viridis.js` loads before its readers). `main.js` maps each stage id
to a web3 rule via `STAGE_MAP`, instantiates `CA.RULES[id]()`, `reset()`s, and
drives a fixed-timestep loop (`EXP_STEPS_PER_SEC = 30`) that `step()`s, then
`renderHeight()` → `SEM.render(…, { palette: 'warm-sepia' })` → `putImageData` —
the **exact** web3 render convention. A single `apparatusRunning` flag is the
source of truth, so the Run button can't desync the apparatus animation from the
live sim. The capstone runs the photoreal `life` feed (its `renderPhotoreal`
path and the sprite atlas in `assets/life/`, the one rule that skips the SEM
pipeline) and keeps the Run button so it stays pausable.

## Files

```
docs/web7/
├── index.html                 importmap + vitrine markup + classic-script loads
├── styles.css                 Catalytic Silence shell (obsidian/teal/magenta, fonts, a11y, responsive)
├── main.js                    controller: registry, plates, run/explode/view, SEM driver, keyboard nav
├── scene.js                   renderer + IBL + ACES + bloom + obsidian backdrop
├── apparatus/
│   ├── lib.js                 shared materials, geometry helpers, anim contract
│   ├── miller_urey.js         Stage 0 hero — hand-built photoreal glassware
│   ├── … (one module per stage, each exporting { meta, build })   (13 total)
│   └── placeholder.js         fallback pedestal + label for future stubs
├── experiment/                live SEM feed — byte-identical copies of the web3 physics
│   ├── viridis.js             web3 LUT (loaded first; defines VIRIDIS_LUT)
│   ├── sem.js                 web3 SEM depth-shading pipeline (window.SEM)
│   ├── sprites.js             web3 procedural sprite library (composited over the SEM substrate)
│   └── rules/*.js             the mapped web3 rule IIFEs (window.CA.RULES)
├── assets/
│   ├── fonts/                 self-hosted Italiana · Crimson Pro · IBM Plex Mono (.ttf)
│   └── life/                  capstone photoreal cell atlas (atlas.json, cells.png, cell_div.png)
├── tests/
│   ├── smoke.mjs              structural CI gate (zero-dep) + live-SEM integration
│   ├── design.mjs             Catalytic Silence design-contract gate (zero-dep)
│   └── runtime.mjs            runtime gate (executes every apparatus vs real three)
└── README.md                  this file
```

## Tests

```bash
node docs/web7/tests/smoke.mjs                       # structural + live-SEM, zero-dep
node docs/web7/tests/design.mjs                      # Catalytic Silence design contract, zero-dep
npm install three@0.162.0 --no-save                  # for the runtime gate
node docs/web7/tests/runtime.mjs                     # executes all 13 apparatus
```

- **smoke.mjs** — structural, no GL: importmap validity, module resolution,
  `node --check` on every module, registry shape (exactly 13 stages), and each
  apparatus's `meta` + anim-contract presence. **Also gates the live SEM
  integration**: every `STAGE_MAP` key is a real meta id, every value has a copied
  rule file loaded as a classic script before `main.js` (with `viridis.js` before
  its readers), and a `vm` harness loads the classic scripts the browser way and
  drives all 13 mapped rules through the real `SEM.render` to a painted,
  fully-opaque, non-blank RGBA buffer.
- **design.mjs** — the Catalytic Silence design contract: the self-hosted fonts
  exist and are `@font-face`-d with `font-display: swap`; the palette tokens are
  present (obsidian, `--teal: #3fe0d0`, `--ink: #ece7da`, magenta) **and the web6
  brass/amber identity is gone** (`#caa86a` must not appear); the vitrine landmarks
  (register / index / specimen / key), the SEM plate framing (badge, scale bar,
  pending state), and the full accessibility scaffolding (skip-link, polite live
  region, radiogroup, focus-visible, reduced-motion, `.sr-only`) are all in place;
  and the controller wires the presentation layer (Roman numerals, `aria-current`,
  announcements, keyboard nav, reduced-motion awareness).
- **runtime.mjs** — installs three and actually runs `build()` + 60 animation
  ticks for all 13 apparatus (geometry construction needs no WebGL), asserting
  named meshes, finite positions, and a finite progress value. Skips cleanly if
  three isn't installed.

CI lives in [`.github/workflows/pages.yml`](../../.github/workflows/pages.yml),
which gates on push to `main` and on `docs/**` pull requests and then deploys
`docs/` to GitHub Pages. (The workflow currently invokes the **web6** smoke +
runtime gates; web7 ships the equivalent `smoke.mjs` / `design.mjs` / `runtime.mjs`
so it can be added to the same gate.)

## What changed from web6

The engine is identical; the room is rebuilt. web7 swaps web6's **vintage-lab
brass/amber** identity for **Catalytic Silence**:

- **Palette** — a deep **obsidian** ground (`#07090d`) with **luminous teal**
  (`#3fe0d0`) and a counterpoint **magenta** (`#d77bff`) used sparingly as events,
  in place of web6's warm brass/amber. Hairlines are teal at low alpha — a whisper
  of structure, not a fence.
- **Typography** — **Italiana** (didone display) / **Crimson Pro** (reading serif,
  italic) / **IBM Plex Mono** (apparatus monospace), self-hosted, replacing web6's
  type.
- **Composition** — a **museum vitrine**: top register, catalogue **stage index**,
  a single dominant **specimen** with corner ticks and a wall label, and a
  **specimen key** — held together by deep negative space and the geometry of the
  page.
- **SEM framing** — the micrograph is reframed as a **scientific plate**:
  registration ticks, `LIVE · SEM` badge, a `50 µm` scale bar, an italic caption,
  and a tasteful "specimen pending" empty state, all at a fixed 1:1 letterbox.
- **Accessibility + reduced-motion** — an AAA pass new in web7: skip-link, polite
  live-region announcements, full keyboard navigation of the index, ARIA on every
  control, a visible focus ring, a forced-colors fallback, and a
  `prefers-reduced-motion` path that freezes the playback "breath" and the caption
  rise (in both CSS and the controller).
- **3D scene, rethemed to obsidian** — `scene.js` reuses web6's renderer (PBR
  glass, RoomEnvironment IBL, ACES Filmic tone-mapping, UnrealBloom tuned so only
  the spark blooms) but recomposes the **environment**: the scene background and
  bench/wall are cooled into the same obsidian darkness as the shell, and web6's
  hardcoded green `MILLER–UREY 1953` chalkboard — which only suited Stage 0 — is
  replaced by a quiet, **stage-agnostic backdrop** (an obsidian field with one teal
  hairline and a near-microscopic monospace mark). Composition, not decoration.
