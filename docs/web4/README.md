# cellauto · web4 — the lab

The next view layer after web3. web3 shows each origin-of-life stage as a
**microscope plate** (SEM substrate + procedural sprites). web4 shows the
**experiment that produced the specimen** — a photoreal, interactive 3D
**laboratory apparatus** you can orbit, take apart, and *run*.

Full design: [`docs/PRD_LAB_EXPERIMENTS.md`](../PRD_LAB_EXPERIMENTS.md).

No build step. Vanilla ES modules + Three.js via importmap (CDN). Opens from
`file://` or any static server.

```bash
python3 -m http.server -d docs   # then visit /web4/
```

## What ships

**All 13 stages are built** — Stage 0 + the 11-stage pipeline + the
stromatolite capstone — each a hand-built photoreal apparatus (no Tripo
needed; lab glassware/equipment is mostly revolved primitives that a physical
glass/metal material renders convincingly). Every apparatus exposes named
parts, an exploded view, and a "Run experiment" animation.

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

- **Lab shell** — Three.js scene with image-based lighting (RoomEnvironment),
  ACES Filmic tone-mapping, and UnrealBloom tuned so only the electric spark
  blooms. OrbitControls, a 13-entry stage nav, a named-parts panel, an
  "exploded view" slider, and a "Run experiment" toggle.
- **Stage 0 — Miller–Urey (hero), hand-built.** Photoreal borosilicate
  glassware matching the 1953 apparatus and the period reference photo:
  - upper **spark chamber** with two angled tungsten **electrodes** + a
    flickering **purple plasma arc** (jagged emissive arcs + point light),
  - the tall **glass riser** arching over from the boiling flask,
  - a water-jacket **condenser** with side arms, copper hoses, and a stopcock,
  - a **collection flask** whose liquid **rises and darkens** as organics
    accumulate (live `organics collected: N%` readout),
  - a **boiling flask** bubbling on a black **heating mantle**,
  - a **steel ring-stand** with clamps, and a `MILLER–UREY EXPERIMENT 1953`
    chalkboard backdrop.

  Why hand-built and still photoreal: this apparatus is all spheres, cylinders
  and swept tubes — exactly what a physical glass material (transmission, IOR
  1.5, HDRI reflections) renders convincingly. Organic shapes are not, which
  is why the *other* stages use Tripo (below).

- **`apparatus/placeholder.js`** stays as the fallback (museum pedestal +
  label card) for any future stage stubbed before its apparatus exists.

## The generation pipeline (Tripo, optional upgrade)

The organic / equipment-heavy apparatus are baked from real reference images
via **our own backend** — `rizzleroc/touch-app` (Next.js + **Tripo**) — driven
through the whipgen MCP (`whipgen_touch_generate`, `image|text → GLB`), then
dropped into this same scene as named-part GLBs and lit with the same PBR.

**Backend status:** as of writing, `whipgen_touch_health` reports the touch-app
backend **down** (`503` at `localhost:3000`). To enable baking:

```bash
cd e:/touch/touch-app && npm run dev    # needs TRIPO_API_KEY in .env.local
```

Once a stage's GLB is baked, replace its `ph(...)` entry in `main.js` with a
real apparatus module exporting `{ id, label, title, blurb, build }`, where
`build()` returns a `THREE.Group` of named parts with a
`group.userData.anim = { setRunning, getProgress, reset, update }`.

## Files

```
docs/web4/
├── index.html                 importmap + 3-pane lab layout
├── styles.css                 vintage-lab / museum aesthetic
├── main.js                    controller: registry, framing, parts, run/explode, loop
├── scene.js                   renderer + IBL + ACES + bloom + bench/chalkboard
├── apparatus/
│   ├── lib.js                 shared materials, geometry helpers, anim contract
│   ├── miller_urey.js         Stage 0 hero — hand-built photoreal glassware
│   ├── grayscott_dish.js      Stage 1 · raf_flask.js Stage 2 · …            (13 total)
│   ├── … (one module per stage, each exporting { meta, build })
│   └── placeholder.js         fallback pedestal + label for future stubs
├── tests/
│   ├── smoke.mjs              structural CI gate (zero-dependency)
│   └── runtime.mjs            runtime gate (executes every apparatus vs real three)
└── README.md                  this file
```

## Tests

```bash
node docs/web4/tests/smoke.mjs                       # structural, zero-dep
npm install three@0.162.0 --no-save                  # for the runtime gate
node docs/web4/tests/runtime.mjs                      # executes all 13 apparatus
```

Both gate CI (`.github/workflows/pages.yml`) alongside the web2/web3 smoke
tests:

- **smoke.mjs** — structural, no GL: importmap validity, module resolution,
  `node --check` on every module, registry shape, and each apparatus's
  `meta` + anim-contract presence.
- **runtime.mjs** — installs three and actually runs `build()` + 60 animation
  ticks for all 13 apparatus (geometry construction needs no WebGL), asserting
  named meshes, finite positions, and a finite progress value. Skips cleanly
  if three isn't installed.
