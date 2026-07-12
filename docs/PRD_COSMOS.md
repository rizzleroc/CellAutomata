# PRD — Part III · The Constructors: Quantum Lifeforms, Plasma, Multiverse & the Element Studio

**Status:** Draft · proposed for the v6.0 cycle (Part III)
**Author:** project owner (with agent research)
**Last updated:** 2026-07-12

---

## 1. Vision

> *"The lab shows how life began here, and how a person begins. Now go one level
> under both: the base constructors of what life could even be, anywhere in the
> universe. Show me quantum lifeforms, plasma, the multiverse — and give me an
> element studio where I can combine everything and watch existence transform."*

cellauto tells two origin stories today. **Part I — abiogenesis** (`web7/web8/web9`)
is the thirteen-stage descent from a reducing atmosphere to the first cell.
**Part II — ontogeny** (`ontogeny/`) is the second origin every person lived —
gamete to zygote to an individual. Both are stories of *matter organising itself
into life*, told at Earth scale.

**Part III — the Constructors** goes one level beneath both. If Part I asks *how
did our life begin* and Part II asks *how does an individual begin*, Part III
asks the widest question the project can honestly hold: **what are the base
constructors from which any life, anywhere, at any epoch, could be built?** It is
a guided tour of the substrate itself — the **four states of matter** taken past
solid/liquid/gas into **plasma**, the **quantum** layer under all chemistry, and
the **multiverse** frame in which the constants that permit life are themselves
variables. And it ends not with a fixed pipeline but with an open one: **the
Element Studio**, a sandbox where every constructor the lab has introduced can be
combined, reacted, and transformed — *a sandbox of existence*.

This is a **science-education** feature about the frontier of what "life" could
mean. The frontier is genuinely speculative, and the project's honesty ethic
(REAL / REPRESENTATIONAL, "no overclaiming") is *more* important here, not less.
Part III therefore adds a third honesty tier — **SPECULATIVE** — and labels every
plate with which tier it stands on. The wonder is real; so is the disclosure.

The arc, stated once: **chemistry → an individual → the universe itself.**

---

## 2. Goals & non-goals

### In scope (v6.0)
1. A new **Part III client** — a fourth catalogue beside Lab / Instrument /
   Ontogeny, forked from **web9** (the newest client, which already carries the
   guide + observables measurement layer).
2. **Three new constructor plates**, each a real cellular-automaton/field
   simulation rendered as a photoreal 3-D apparatus beside its live micrograph,
   exactly like every existing stage: **Plasma**, **Quantum lifeforms**,
   **Multiverse**.
3. **The Element Studio** — a free-form sandbox plate where a palette of
   constructors (real elements + the exotic states this client introduces) can
   be painted, combined, and transmuted, with the transformations driven by a
   real reaction table.
4. **Honest tiering** — every plate declares REAL / REPRESENTATIONAL /
   SPECULATIVE, and the copy never presents speculation as settled fact.
5. Full reuse of the existing contracts: the **Parameters panel**, the **SEM
   micrograph pipeline**, and the **web9 observables** (sparkline / CSV / run
   link) all ride *free* on the standard rule contract — no per-stage plumbing.

### Explicitly NOT in scope (yet)
- **Any claim that quantum, plasma, or multiverse life is established.** These
  are labelled hypotheses and mathematical models, presented as such.
- **A physically exact quantum simulator.** We render honest *quantum-cellular-
  automaton* dynamics (unitary local update, probability density), not a
  full many-body Schrödinger solve. Labelled REPRESENTATIONAL.
- **Real quantum hardware, VR, or a WebGPU compute rewrite.** Part III runs on
  the same zero-dependency ES-module + CDN-Three.js stack every client uses.
- **A full chemistry engine.** The Element Studio's reactions are a curated,
  sourced table (real where real), not an ab-initio quantum-chemistry solver.
- **Replacing the abiogenesis or ontogeny stories.** Part III is additive; the
  canonical thirteen-stage pipeline is untouched.

---

## 3. Scientific grounding & honesty tiers

The project already labels output **REAL** (a genuine simulation of the named
science) vs **REPRESENTATIONAL** (an honestly-labelled guided depiction). Part
III adds **SPECULATIVE** — a named hypothesis or a mathematical toy model that is
*not* claimed to describe anything observed. Every plate wears its tier.

### 3.1 Plasma — the fourth state of matter

| Claim | Tier | Basis |
|---|---|---|
| Plasma is the fourth state of matter; >99% of visible baryonic matter is plasma | **REAL** | standard physics |
| **Dusty/complex plasmas self-organise into ordered "Coulomb crystals"** | **REAL** | Thomas & Morfill, Chu & I, Hayashi — lab-observed 1994 |
| Debye shielding, sheath formation, filamentary self-focusing | **REAL** | standard plasma physics |
| **"Plasma life": helical dust structures that store information & replicate** | **SPECULATIVE** | Tsytovich, Morfill, Fortov et al. (2007) — a hypothesis, disputed |

The plasma plate simulates a **2-D complex-plasma layer**: charged dust grains in
a Debye-screened Yukawa potential that crystallise into a hexagonal lattice and
melt with drive — a real, load-bearing simulation. The "could this order become
alive?" question is raised as the labelled SPECULATIVE frontier, not asserted.

### 3.2 Quantum lifeforms — the layer under chemistry

| Claim | Tier | Basis |
|---|---|---|
| Quantum coherence appears in biology (FMO photosynthetic transport; radical-pair avian magnetoreception) | **REAL / DEBATED** | Engel et al. 2007; Ritz–Schulten radical-pair model |
| **Quantum Cellular Automata / quantum walks are well-defined dynamics** | **REAL** (math) | Meyer 1996; quantum-walk literature |
| Decoherence destroys superposition on contact with a warm environment | **REAL** | standard QM |
| **A self-replicating, evolving "quantum lifeform"** | **SPECULATIVE** | thought-experiment; no known instance |

The quantum plate runs a **Quantum Cellular Automaton** (a discrete quantum walk
on the grid): a complex amplitude field evolves by a **local unitary** update;
the micrograph renders the **probability density |ψ|²** as the height field.
Interference, coherent spreading, and **decoherence** (a tunable coupling that
collapses the walk toward classical diffusion) are all real behaviours of the
model. Whether such coherent, self-maintaining patterns could constitute "life"
is the labelled SPECULATIVE frontier.

### 3.3 Multiverse — where the constants are variables

| Claim | Tier | Basis |
|---|---|---|
| Eternal inflation generates causally-disconnected "bubble" universes | **THEORETICAL** | Guth, Linde, Vilenkin |
| Many-Worlds: unitary QM branches without collapse | **THEORETICAL** | Everett 1957 |
| A "landscape" of vacua with different physical constants | **SPECULATIVE** | string landscape; anthropic reasoning |
| Life is possible only in a narrow band of constants (fine-tuning) | **REPRESENTATIONAL** | the observation we dramatise |

The multiverse plate simulates **bubble nucleation in an inflating false vacuum**:
a field where true-vacuum bubbles nucleate, grow, and collide, each bubble
carrying its own randomly-drawn "constants" that make it life-permitting or not.
It is a real nucleation-and-percolation CA; the *interpretation* as literal
parallel universes is labelled THEORETICAL/SPECULATIVE.

### 3.4 The Element Studio — real chemistry as the sandbox floor

| Claim | Tier | Basis |
|---|---|---|
| The periodic table; bonding; common reactions | **REAL** | chemistry |
| Reaction/transmutation rules in the studio's curated table | **REAL** where sourced | e.g. H+O→H₂O, fusion chains, ionisation → plasma |
| **Exotic constructors** (plasma-state, quantum-coherent, dark, void) as combinable "elements" | **SPECULATIVE** | sandbox pieces, labelled |

---

## 4. The new plates (constructor stages)

Each plate is, exactly like every existing stage, a **CA rule** (the live
science) + a **3-D apparatus** (the photoreal instrument) + its **SEM micrograph**
(the live feed). The rule/apparatus contracts are unchanged (see §9).

### 4.1 Plasma · complex-plasma Coulomb crystal
- **Rule** (`rules/plasma.js`): charged dust grains (or a density field) in a
  screened Yukawa potential; order parameter crystallises/melts with drive and
  screening length. `renderHeight` = grain density / potential well depth, so
  the micrograph shows a hexagonal lattice under the electron beam.
- **Apparatus:** a **dusty-plasma discharge cell** — an RF-electrode vacuum
  chamber, a glowing sheath, a suspended dust cloud catching the ring light.

### 4.2 Quantum lifeforms · the coherent automaton
- **Rule** (`rules/quantum.js`): a Quantum Cellular Automaton / discrete-time
  quantum walk. Complex amplitude `ψ` on the grid; local unitary "coin + shift"
  update; a **decoherence** knob interpolates coherent→classical.
  `renderHeight` = `|ψ|²`. Interference fringes and coherent self-organising
  packets are the visible "lifeforms."
- **Apparatus:** a **cryostat / ion-trap interferometer** — a cold-finger,
  mirror paths, a trapped-ion glow, beam-splitter optics.

### 4.3 Multiverse · the inflating bubble chamber
- **Rule** (`rules/multiverse.js`): false-vacuum field with stochastic
  true-vacuum bubble nucleation, growth, and collision; each bubble draws a
  "constants" vector → life-permitting or sterile. `renderHeight` = field
  value / bubble age.
- **Apparatus:** an **eternal-inflation bubble chamber / branching-timeline
  wall** — a volume of nucleating domains, filaments between colliding bubbles.

---

## 5. The Element Studio — the sandbox of existence (centrepiece)

The Element Studio is the plate the request is really about: *"combine all
elements to create and transform in a sandbox of existence."* It is the open
counterpart to the fixed pipeline — a free-form editor rather than a scripted
stage.

**Model.** A grid of cells, each holding an **element/constructor id** and a
small state (energy, charge, phase). A curated **reaction table** maps
`(A, B, conditions) → products`, applied every step where two constructors are
adjacent or a cell crosses an energy threshold — so painted matter **reacts,
transmutes, and self-organises** on its own. The palette spans four bands:
1. **Real elements** — a working subset of the periodic table (H, He, C, N, O,
   Na, Cl, Fe, U…), with real reactions (H+O→H₂O; Na+Cl→salt; ionise→plasma;
   fusion chains under pressure).
2. **States of matter** — solid / liquid / gas / **plasma** (ties to §4.1).
3. **The lab's constructors** — a **quantum-coherent** cell, a **replicator**
   (borrowing the abiogenesis engine's self-copy), a **membrane**.
4. **Exotic/speculative** — dark matter, vacuum/void, antimatter (annihilation),
   clearly SPECULATIVE sandbox pieces.

**Interaction (new UI surface — the one genuinely new build).** Beyond the
existing schema-driven Parameters panel, the studio adds an **element palette**:
a selectable tray of constructors, a brush that paints the active element via the
rule's `paint(gx, gy, radius, mode)` hook, an **energy/temperature/pressure**
global (real `params` sliders, so it stays panel-driven), and a **legend** of
what reacts with what. Presets seed classic scenarios: *"water world," "ignite a
star," "ionise to plasma," "antimatter annihilation," "quantum garden."*

**Honesty.** Real reactions are labelled REAL; exotic constructors and their
"reactions" are labelled SPECULATIVE in the legend. The studio is a *sandbox*,
and says so.

---

## 6. Controls (wired to the Parameters panel)

Every plate declares its knobs in the standard `params` schema and its regimes in
`presets`; the existing `buildParamPanel` renders the whole panel — regime
picker, speed, palette, and per-param sliders/enums — with **zero per-stage UI
code**. Representative knobs:

| Plate | Params | Regime presets |
|---|---|---|
| **Plasma** | `screeningLength` (Debye), `drive` (RF power), `dustDensity`, `temperature` | crystal · liquid · gas · void-melt |
| **Quantum** | `coinAngle` (unitary), `decoherence`, `packets`, `barrier` | coherent walk · double-slit · decohering · tunnelling |
| **Multiverse** | `nucleationRate`, `expansion`, `constantsSpread`, `collisionMode` | eternal inflation · sparse bubbles · dense collisions · fine-tuned |
| **Element Studio** | `activeElement` (enum), `temperature`, `pressure`, `energy`, `brushRadius` | water world · ignite a star · ionise to plasma · antimatter · quantum garden |

Each `preset` is `{ label, hint, values:{param:value}, reseed? }`; each param may
carry a `controlConsequence[key]` tooltip explaining what it does.

---

## 7. Visualisation & UI

- **New client** forked from `docs/web9/` (working name `web10/` · "the Cosmos"
  or "the Substrate") so it inherits the guide layer and the observables /
  sparkline / CSV / run-link measurement layer for free.
- **Catalytic Silence** design language throughout: obsidian ground, luminous
  teal, magenta spent only as events, museum typography (Italiana / Crimson Pro
  / IBM Plex Mono, self-hosted), the vitrine composition — not a dashboard.
- **LAB / SPLIT / LIVE·SEM** views in lockstep, exactly as web7/8/9.
- The **micrograph and the observables sparkline ride free on `renderHeight`** —
  a new rule that fills the height field gets the depth-shaded SEM feed *and* the
  ⟨h⟩ / σ² / peak sparkline + CSV export with no extra wiring.
- The **hub** (`docs/index.html`) gains a Part III entry: a new stage-grid cell
  ("◆ Part III · The Constructors") and an ecosystem card, continuing the
  Part I → Part II → Part III narrative bridge.

---

## 8. Feasibility & honesty summary

| Capability | Verdict |
|---|---|
| Complex-plasma Coulomb-crystal formation/melting | **REAL** (Yukawa CA) |
| Quantum-walk / QCA dynamics, interference, decoherence | **REAL** math, **REPRESENTATIONAL** as "quantum life" |
| Bubble nucleation / collision / percolation | **REAL** CA; multiverse *interpretation* **THEORETICAL** |
| "Plasma life" / "quantum lifeform" as living systems | **SPECULATIVE** (labelled hypotheses) |
| Element Studio real reactions (water, ionisation, fusion) | **REAL** (curated table) |
| Element Studio exotic constructors (dark, void, antimatter) | **SPECULATIVE** sandbox pieces |
| Fine-tuning / life-permitting constants dramatised | **REPRESENTATIONAL** |
| New 3-D apparatus models (plasma cell, cryostat, bubble chamber) | **TO BUILD** |
| Element-palette editor UI | **TO BUILD** (only genuinely new UI surface) |

---

## 9. Architecture & integration

Part III reuses the existing contracts verbatim. A new plate = **two files + two
registry edits + script tags**, plus (for the studio) one new UI surface.

### 9.1 CA rule — classic-script IIFE
Template: `docs/web7/experiment/rules/grayscott.js`. Each rule file is a classic
`<script>` (not a module) that registers a factory:

```js
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };
  function make() { /* closure state */ return { /* rule object */ }; }
  CA.RULES.plasma = make;   // key must match a STAGE_MAP value
})();
```

The returned object must expose: `id`, caption strings (`label`, `formula`,
`shortCaption`, `whatThisIs`, `aboutStage`), `paletteBg`/`paletteFg`, integer
`width`/`height`, a `params` schema, `reset()`, `step()` (reads
`this.params.X.value` live), **`renderHeight(out)`** (fills a `width*height`
Float32 height field — this is what feeds the SEM micrograph *and* the web9
observables), and a `render(pixels)` RGBA fallback. Optional but recommended:
`presets`, `onParamChange(key)`, `controlConsequence`, `population()`,
`generation()`, `paint(gx,gy,radius,mode)` (the Element Studio brush).

### 9.2 3-D apparatus — ES module
Contract in `docs/web7/apparatus/lib.js:8-18`. Each apparatus module exports
`build(): THREE.Group` (named child meshes for the parts panel; installs
`group.userData.anim = { setRunning, getProgress, reset, update }`) and
`meta = { id, label:"Stage N — …", title, blurb, build }`. Reuse `lib.js`
helpers (`glassMat`, `steelMat`, `part`, `tube`, `makeDynamicTexture`,
`makeAnim`). A plate with no apparatus falls back to `placeholder.js`.

### 9.3 Registries & load order (in the new client's `main.js`)
- Import each apparatus `meta` and add it to the `STAGES` array.
- Add the `stageId → ruleKey` pair to `STAGE_MAP`.
- In `index.html`, load each rule `<script>` **before** the module `main.js`
  (and after `viridis.js` if the rule reads `VIRIDIS_LUT`).
- **Bump the hard-coded stage-count assertions** in the client's
  `tests/smoke.mjs` (the `STAGES` length and `STAGE_MAP` length are asserted
  against an exact number — today 13).

### 9.4 What comes free
Because the Parameters panel, the SEM shader, and the observables layer all
derive from `params` / `presets` / `renderHeight`, a correctly-authored rule gets
its control panel, its depth-shaded micrograph, and its sparkline + CSV export
with **no** stage-specific UI or measurement code. The **only** genuinely new UI
is the Element Studio's element-palette tray.

---

## 10. Test gates

New work must keep every existing zero-dependency Node gate green and extend
them (honouring standing requirement #67 — *gates must verify the science, not
pass on blank output*):

1. **smoke.mjs (runtime gate):** for every mapped rule — instantiate → assert
   integer `width`/`height` → `reset()` → 12× `step()` → `renderHeight` →
   `SEM.render` → output must be **fully opaque** and **not a single flat
   colour**. Update the stage-count assertions for the new plates.
2. **controls.mjs (preset integrity):** every new rule's `presets` set real
   params within their slider bounds; the regime picker moves something.
3. **design.mjs (Catalytic Silence):** the new client's fonts, palette tokens,
   landmarks, SEM framing, accessibility scaffold, and Parameters-panel wiring.
4. **Science gates (new, per plate):** assert *structure*, not just non-blank —
   e.g. **plasma** crystal order parameter rises under low temperature and
   collapses on melt; **quantum** total probability is conserved (Σ|ψ|² ≈ 1) and
   the decoherence knob measurably reduces interference contrast; **multiverse**
   bubble count grows with `nucleationRate`; **Element Studio** a seeded H+O
   region actually **transforms** into water (state changes), and an antimatter
   contact annihilates.
5. **observables:** the new rules' `renderHeight` produces a non-degenerate
   ⟨h⟩ / σ² series (the sim evolves).

---

## 11. Ethical & educational framing

Part III teaches the *frontier* of what life could be — necessarily speculative
territory. The framing rules:
- **Every plate declares its tier** (REAL / REPRESENTATIONAL / SPECULATIVE) in
  its wall label; speculation is never rendered as settled fact.
- **Named sources** for the real science and the named hypotheses (Thomas &
  Morfill; Tsytovich et al.; Meyer; Engel et al.; Guth/Linde/Vilenkin; Everett)
  — to be cited inline in `docs/science.md` at implementation.
- **The Element Studio is a sandbox and says so** — its exotic constructors are
  labelled imaginative pieces, not claims about nature.
- Awe is welcome; overclaiming is not. The disclosure *is* the education.

---

## 12. Acceptance criteria (v6.0.0)

1. A new Part III client ships beside Lab / Instrument / Ontogeny, forked from
   web9, in the Catalytic Silence language, linked from `docs/index.html`.
2. Four new plates exist — **Plasma**, **Quantum lifeforms**, **Multiverse**,
   **Element Studio** — each with a live micrograph and a wired Parameters panel.
3. Every plate's wall label declares its honesty tier; no speculative claim is
   presented as established fact.
4. Every new rule passes the smoke runtime gate (opaque, non-flat, evolving) and
   the controls preset-integrity gate; the stage-count assertions are updated.
5. Per-plate **science gates** pass: plasma crystallises/melts, quantum conserves
   probability and decoheres, multiverse bubbles scale with nucleation, and the
   Element Studio performs at least one real transformation (H+O→water) and one
   speculative one (antimatter annihilation).
6. The SEM micrograph and the web9 observables sparkline + CSV export work for
   every new plate **through the standard `renderHeight` contract**, with no
   stage-specific wiring.
7. `CLAUDE.md` is updated in the same PR (new client, new PRD, new standing
   direction), per its own maintenance rule.

---

## 13. Phased roadmap

| Phase | Deliverable | Acceptance gate |
|---|---|---|
| **P1 — the sandbox + the most-real pillar** | Fork web9 → Part III client; ship the **Element Studio** (palette UI + reaction table) and the **Plasma** plate (most load-bearing REAL science); hub link; smoke + controls + plasma/studio science gates | Studio transforms matter (H+O→water; ionise→plasma); plasma crystallises/melts; all gates green |
| **P2 — the quantum & multiverse pillars** | **Quantum lifeforms** (QCA + decoherence) and **Multiverse** (bubble nucleation) plates + apparatus; per-plate science gates; observables verified | Σ\|ψ\|² conserved + decoherence reduces contrast; bubbles scale with nucleation; micrograph + sparkline live |
| **P3 — apparatus & polish** | Bespoke 3-D models (dusty-plasma cell, cryostat/interferometer, bubble chamber), curatorial copy, `docs/science.md` citations, expanded Element Studio palette | anim gate green (visibly animates while running, calms when stopped); copy reviewed; sources cited |

---

## Appendix A — relationship to prior work

| Part | Client | Story | Scale |
|---|---|---|---|
| **I — Abiogenesis** | `web7` / `web8` / `web9` | dead chemistry → the first cell → LUCA → digital life | Earth, ~4.0–3.5 Ga |
| **II — Ontogeny** | `ontogeny/` | gamete → zygote → an individual → the stages of life | one human life |
| **III — The Constructors** | `web10` (proposed) | plasma · quantum · multiverse · the Element Studio | the universe / the substrate itself |

**The arc: chemistry → an individual → the universe itself.** Part III is the
outermost frame the project can hold honestly — the base constructors of
life-as-it-could-be — and the Element Studio is where the viewer stops reading
the catalogue and starts writing in it.

*Sources (to be cited inline in `docs/science.md` at implementation): Thomas &
Morfill (plasma crystals, 1994); Tsytovich, Morfill, Fortov et al. (plasma-life
hypothesis, 2007); Meyer (quantum cellular automata / lattice-gas, 1996); Engel
et al. (FMO quantum coherence, 2007); Ritz–Schulten (radical-pair
magnetoreception); Guth / Linde / Vilenkin (eternal inflation); Everett
(Many-Worlds, 1957); the string landscape & anthropic literature.*
