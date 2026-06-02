# PRD — Photoreal Interactive Lab Experiments (web4)

**Status:** Draft / definition phase
**Branch:** `claude/zealous-johnson-o7HNz`
**Supersedes/extends:** the web3 "microscope plate" view (`docs/web3/`)
**Date:** 2026-06-01

---

## 0. One-paragraph thesis

web3 shows each origin-of-life stage as a **microscope view** — a depth-shaded
SEM substrate with procedural bioform sprites over a colour-mapped scalar
field. That is the *specimen under the lens*. What it does **not** show is the
**experiment that produced the specimen** — the actual bench, the glassware,
the apparatus a real origin-of-life lab would run. web4 closes that gap: each
stage becomes a **photoreal, interactive 3D laboratory environment** you can
orbit, inspect, and *run*, with the existing cellauto simulation playing out
as the result *inside the apparatus* (inside the spark flask, the Petri dish,
the vent reactor, on the microscope slide).

**Hard requirement (from the brief):** nothing may look "generated." Every
surface must read as real laboratory equipment — borosilicate glass, steel
clamps, rubber tubing, ground-glass joints, meniscus on liquids — lit like a
real photograph. The reference quality bar is **Figure 4.6 (Miller–Urey
apparatus)** from *Evolution* (Cold Spring Harbor, 2007): a NASA recreation of
real glassware. If a panel looks like clip-art or a low-poly toy, it has failed.

---

## 1. How we hit "photoreal, nothing generated-looking"

Procedural primitives (spheres, tori) look generated — they are explicitly
**out of scope** for the apparatus. The pipeline is:

```
  real reference figure / photoreal concept image
            │
            ▼
   [touch-app  →  Tripo  image→3D]      our own backend (rizzleroc/touch-app)
            │   GLB + PBR textures      reachable via whipgen_touch_generate
            ▼
   per-part GLB asset (glass / steel / liquid named parts)
            │
            ▼
   Three.js lab scene:  HDRI image-based lighting + ACES tone-map
                        physical glass material (transmission, IOR 1.5,
                        roughness, thickness), real shadows, depth-of-field
            │
            ▼
   interactive hotspots → "Run experiment" → live cellauto sim renders
                          ON the apparatus (flask contents, dish surface…)
```

Three pillars make it photoreal rather than "generated":

1. **Asset source = Tripo (touch-app), seeded from real references.** Tripo
   produces real reconstructed meshes with PBR texture maps, not parametric
   blobs. We seed it from the *actual* published apparatus figures (e.g.
   Miller–Urey Fig 4.6) and photoreal concept renders, in `image→3D` mode so
   the silhouette matches real equipment.
2. **Physically based rendering.** Three.js `MeshPhysicalMaterial` with
   `transmission` for glass, real **HDRI** environment map for reflections,
   ACES Filmic tone-mapping, soft contact shadows, subtle DOF and bloom on
   the spark only. Glass that refracts the bench behind it is the single
   biggest "this is real" cue.
3. **No flat colours, no emissive cartoon glows** except where physically
   justified (the spark discharge, the orange vent glow). Liquids get a
   meniscus, bubbles, and Fresnel; metals get anisotropic roughness.

### Render-tech decision

| Option | Verdict |
|---|---|
| **glTF/GLB + Three.js PBR + HDRI** | ✅ **Chosen.** Real-time, interactive, runs on GitHub Pages, no plugin. Best photoreal-per-effort with `KHR_materials_transmission`. |
| Gaussian-splat scans | ❌ Photoreal but not editable/interactive enough; huge files; can't "run" a sim inside. |
| Pre-rendered video/turntable | ❌ Not interactive — fails the "fully interactive" requirement. |
| Procedural primitives | ❌ Looks generated — fails the hard requirement. |

---

## 2. The generation backend (our own — touch-app)

We are **not** using Nova3D's hosted service (closed, OAuth-gated). We use
**`rizzleroc/touch-app`** — your Next.js + Tripo backend — driven through the
whipgen MCP:

- `whipgen_touch_generate` — `image|text|multiview|refine → GLB/GLTF/USDZ` via Tripo.
- `whipgen_touch_health` — reachability probe.

**Current status (2026-06-01):** backend is **DOWN** — `whipgen_touch_health`
returns `503 reachable:false` at `http://localhost:3000`. To enable asset
baking:

```bash
cd e:/touch/touch-app
npm run dev          # serves :3000; needs TRIPO_API_KEY in .env.local
```

Reference images to seed Tripo can be produced with whipgen image-gen
(`whipgen_generate_image` / `whipgen_gemini_generate_image`) or supplied
directly (the Miller–Urey figure is our first seed).

Cost note: whipgen rates list `touch-3d` at ~$0.04/gen — cheap; budget a few
iterations per apparatus.

---

## 3. The experiments — definition

Each stage is defined as: **the real experiment**, **what the scene looks
like** (the apparatus to model), **interactive elements**, **the "result"**
(which existing cellauto sim renders inside it), and **named GLB parts** (so
the apparatus is separately inspectable, à la a real exploded lab diagram).

> Numbering follows the 12-stage extended pipeline. Stages marked ★ are the
> highest-value first builds (most iconic apparatus, clearest "run" payoff).

### ★ Stage 0 — Primordial soup · *Miller–Urey spark-discharge apparatus*

- **Real experiment:** Miller & Urey 1953 — spark a reducing atmosphere
  (CH₄, NH₃, H₂, H₂O vapour), condense, collect amino acids in a trap.
- **Scene (ref: Fig 4.6):** borosilicate rig on a steel stand against a
  stainless backsplash. Upper **spherical spark chamber** with two **tungsten
  electrodes** at ~90°; a tungsten/violet **spark discharge** arcing across the
  gas. Vertical **condenser** (water-in / water-out side arms) dripping
  condensate. Lower **round-bottom boiling flask** over a heating mantle,
  bubbling. **U-trap** at the base pooling tea-coloured "water containing
  organic compounds." Glass elbows, ground-glass joints, ring-stand clamps,
  rubber tubing, a stopcock to the vacuum line.
- **Interactive:** orbit; toggle the spark (arc SFX + flicker light);
  watch condensate droplets fall; the trap liquid **darkens over time** as
  organics accumulate; click the trap → cutaway shows the soup.
- **Result inside:** the **Stage 0 soup** sim runs as the trap contents (the
  16 Miller-yield species, weighted by his measured yields).
- **GLB parts:** `spark-chamber`, `electrode-L`, `electrode-R`, `condenser`,
  `boiling-flask`, `heating-mantle`, `u-trap`, `trap-liquid`, `tubing`,
  `ring-stand`, `stopcock`.

### ★ Stage 1 — Reaction-diffusion · *Belousov–Zhabotinsky Petri dish*

- **Real experiment:** a thin BZ-reagent layer in a Petri dish self-organises
  into travelling target/spiral waves — the lab embodiment of Turing/Gray-Scott
  reaction-diffusion.
- **Scene:** a glass **Petri dish** on a white lab bench under a ring light,
  shallow reagent film with a real meniscus and dish reflections; a pipette
  resting beside it; faint condensation on the lid (set aside).
- **Interactive:** top-down "into the dish" camera or free orbit; pipette a
  drop → seeds a new spiral; the **Gray-Scott field renders as the reagent
  surface** (real refraction through the film).
- **Result inside:** the existing **grayscott** rule, mapped onto the dish
  liquid as an animated, lightly-refractive texture.
- **GLB parts:** `petri-base`, `petri-lid`, `reagent-film`, `pipette`, `bench`.

### Stage 2 — Autocatalytic sets (RAF) · *reaction-flask + stir plate*

- **Real experiment:** a well-stirred flask of mutually-catalysing species
  (Kauffman/Hordijk-Steel RAF). The "apparatus" is the chemistry, so we stage
  a believable bench reactor.
- **Scene:** Erlenmeyer/round-bottom flask on a **magnetic stir plate**, stir
  bar vortexing a faintly opalescent solution; thermometer; tubing.
- **Interactive:** stir-speed knob changes the vortex; click flask → the RAF
  **reaction network** overlays as glowing nodes/edges suspended in the liquid.
- **Result inside:** the **raf** network view, rendered as in-liquid graph.
- **GLB parts:** `flask`, `stir-plate`, `stir-bar`, `thermometer`, `solution`.

### ★ Stage 3 — Vesicles · *inverted microscope + slide*

- **Real experiment:** fatty acids above their CMC self-assemble into lipid
  vesicles (Deamer/Hanczyc/Szostak), observed by phase-contrast microscopy.
- **Scene:** a **research microscope** (objective turret, stage clips, coarse/
  fine knobs, illuminator) with a **glass slide + coverslip**; a second
  "eyepiece view" inset showing the field.
- **Interactive:** focus knob racks the depth-of-field; objective swap changes
  magnification; the **vesicle field renders in the eyepiece inset**.
- **Result inside:** the **vesicles** (Helfrich) rule in the microscope view.
- **GLB parts:** `microscope-body`, `objective-turret`, `stage`, `slide`,
  `coverslip`, `focus-knob`, `illuminator`, `eyepiece`.

### ★ Stage 4 — Alkaline hydrothermal vent · *bench-top vent reactor*

- **Real experiment:** Lane/Martin chemiosmosis — a lab reactor mimicking an
  alkaline vent: alkaline fluid percolating through an FeS chimney across a
  proton gradient, driving Wood–Ljungdahl chemistry.
- **Scene:** a sealed **glass/steel reactor column** packed with a mineral
  **chimney**, warm orange glow from below, gas bubbles rising, pH probes and
  tubing; live **PMF (mV)** and **ΔG (kJ/mol)** readouts on a small panel.
- **Interactive:** dial vent vs ocean pH → the gradient/readouts change; click
  the chimney → cutaway of the micro-pores.
- **Result inside:** the **vents** rule on the chimney wall; live Nernst PMF/ΔG.
- **GLB parts:** `reactor-column`, `chimney`, `ph-probe`, `gas-line`,
  `readout-panel`, `heater`.

### Stage 5 — Mineral catalysis · *montmorillonite clay flask*

- Ferris 1996 clay-surface polymerisation. Scene: flask with a settled
  **Na-montmorillonite** clay layer, activated-monomer solution above.
  Result: the **mineral-catalysis** rule on the clay mask.
- **GLB parts:** `flask`, `clay-bed`, `supernatant`, `stopper`.

### Stage 6 — Homochirality · *Soai-reaction flask + polarimeter*

- Frank/Soai chiral symmetry breaking. Scene: reaction flask beside a
  **polarimeter** whose dial swings to + or − as one handedness wins.
  Result: the **chirality** rule (teal/magenta domains) in the flask.
- **GLB parts:** `flask`, `polarimeter`, `dial`, `light-source`.

### ★ Stage 7 — RNA world · *ribozyme self-replication assay*

- **Real experiment / hypothesis:** the **RNA World** bridges the gap between
  prebiotic amino acids and complex self-replicating DNA. RNA is shown to be
  **dual-role** — it both *stores genetic information* (like DNA) and *acts as
  a catalyst* (**ribozymes**). Lab demonstrations show RNA can spontaneously
  form and **replicate** under prebiotic conditions (e.g. template-directed
  ribozyme replicases; Gilbert 1986; Eigen 1971). The simulation models the
  **spatial Eigen quasispecies** and the **error catastrophe** at ε_c = ln(σ)/L.
- **Scene:** a **PCR thermocycler** with a tube strip (replication assay), a
  **gel-doc** beside it showing migrating bands, heat-block glow; optional
  eyepiece inset of replicating strands forming and copying.
- **Interactive:** ε (error-rate) slider sweeps the strand population across
  the **error catastrophe** — below ε_c information persists, above it the
  quasispecies melts down; σ (superiority) knob; click gel → band readout.
- **Result inside:** the **rna-world** rule as the assay/eyepiece readout.
- **GLB parts:** `thermocycler`, `tube-strip`, `lid`, `gel-doc`, `display`.

### Stage 8 — Genetic-code coevolution · *translation bench / ribosome rig*

- Vetsigian-Woese-Goldenfeld code convergence. Scene: a stylised-but-real
  **in-vitro translation** setup (tubes, codon-table card) converging.
  Result: the **genetic-code** rule (codon→amino-acid table converging).
- **GLB parts:** `bench`, `tube-rack`, `codon-card`, `readout`.

### Stage 9 — Coacervates · *Oparin droplets under microscope*

- Oparin LLPS / Cahn-Hilliard. Scene: microscope (reuse Stage 3 body) with a
  slide of **coacervate droplets** coalescing in the eyepiece inset.
  Result: the **coacervate** rule.
- **GLB parts:** reuse `microscope-*`; `coacervate-slide`.

### Stage 10 — Protocell selection · *microfluidic culture chip*

- Eigen error threshold; hypercycle selection. Scene: a **microfluidic chip**
  on a stage, droplet array, fitness heat overlay; click a droplet → the
  existing per-protocell inspector (genome/fitness/age).
  Result: the **selection** rule across the droplet array.
- **GLB parts:** `chip`, `droplet-array`, `inlet`, `outlet`, `heat-overlay`.

### Stage 11 — LUCA distillation · *genomics / tree-of-life console*

- Weiss et al. 2016 comparative-genomics parsimony. The only abstract stage:
  a **sequencer + console** whose screen distils the conserved core gene set;
  a glowing **tree of life** converging on LUCA.
  Result: the **luca** rule as the console readout.
- **GLB parts:** `sequencer`, `console`, `screen`, `tree-hologram`.

### ★ Capstone specimen — Stromatolite hand sample · *the result, fossilised*

- **Why it matters:** stromatolites are layered structures built by microbial
  mats — the **oldest physical evidence of life** (~3.5 Ga). They are the
  payoff exhibit: after the 12-stage pipeline, *this* is what life leaves in
  the rock record. Not an apparatus — a **museum hand specimen** on a stand.
- **Scene (ref: the supplied cut-and-polished slab):** a sawn stromatolite
  block, glossy polished face showing **wavy ochre/cream/grey laminations**
  and a pale crystalline (calcite) vein, rough crust on top, **1 cm scale bar**;
  on a felt museum mount under gallery lighting, deep black backdrop.
- **Why it's the perfect photoreal seed:** real banded rock with rich PBR
  detail (gloss face vs matte crust) — an ideal Tripo `image→3D` subject from
  the provided photograph; nothing about it can read as "generated."
- **Interactive:** orbit the slab; raking light rakes across the laminae;
  zoom to read the bands; toggle a label card with the 3.5 Ga citation.
- **Result inside:** none — this is the terminal *specimen*, closing the arc
  from Miller–Urey soup (Stage 0) to fossil life. Optional: a faint overlay of
  the **luca** core gene set "read" from the rock.
- **GLB parts:** `slab-polished-face`, `slab-crust`, `calcite-vein`,
  `museum-mount`, `scale-bar`.

---

## 4. Interaction model (shared across stages)

- **Lab-bench shell:** a single photoreal bench/room (one HDRI, one floor,
  one backsplash) hosting the active apparatus; stage selector swaps apparatus.
- **Orbit + inspect:** OrbitControls, zoom limits, focus framing per apparatus.
- **Exploded / cutaway:** a slider explodes the named GLB parts (real
  lab-diagram feel) and a cutaway reveals interior contents.
- **Run experiment:** a primary action that starts the apparatus animation
  *and* the corresponding cellauto sim rendered onto the relevant surface
  (flask/dish/slide/chimney). This is the bridge from "real lab" to "our
  science engine" — the experiment's *result* is a real cellauto run.
- **Readouts:** per-stage instrument panel (PMF/ΔG, ε vs ε_c, polarimeter
  angle, population sparkline) reusing web3's stat plumbing.
- **Accessibility / perf:** quality tiers (drop transmission + DOF on low-end),
  lazy-load GLBs per stage, target 60 fps with one apparatus on screen.

---

## 5. Build phases

1. **P0 — definition (this doc).** ✅
2. **P1 — lab shell + viewer.** `docs/web4/`: Three.js scene, HDRI/ACES,
   OrbitControls, GLB loader, stage selector, quality tiers. Loads a
   placeholder apparatus until assets bake.
3. **P2 — first hero apparatus: Stage 0 Miller–Urey.** Bake via touch-app from
   Fig 4.6, wire spark/condensate/trap interactions, render Stage 0 soup in
   the trap. Proves the whole pipeline end-to-end.
4. **P3 — the other three ★ apparatus** (Gray-Scott dish, vesicle microscope,
   vent reactor). Shared microscope body reused for Stage 9.
5. **P4 — remaining stages, exploded/cutaway, readouts, polish.**
6. **P5 — docs, smoke test, CI gate, Pages deploy at `/web4/`.**

**Blocked-on-you:** P2+ asset baking needs touch-app running (`npm run dev`,
`TRIPO_API_KEY`). P1 (the shell) can proceed now with placeholders.

---

## 6. Open questions

1. **Bench style** — clean modern white lab, vintage 1950s bench (matches the
   Miller–Urey era), or sci-fi astrobiology lab? Drives every HDRI/material choice.
2. **"Run" semantics** — should the sim play *photoreal inside the glass*
   (refracted texture) or pop a clean inset panel? (Default: inside the glass.)
3. **Scope of first ship** — Stage 0 alone as a polished hero, or all four ★
   stages before showing anyone?
4. **Asset licence** — generated GLBs committed to the repo under MIT like the
   rest, plus a note that Tripo-generated meshes seeded from the CSH figure are
   for educational use.
</content>
</invoke>
