# cellauto · web 2.0 — goal punchlist

**Goal.** *"Explain the building blocks of life and show how they are
controlled."*

This file tracks the gap between the current `docs/web2/` sandbox and
that goal. It is updated every time we ship a change touching the web
client — each round, items move between sections.

Status legend:
  `[ ]` TODO &nbsp; · &nbsp; `[~]` IN-PROGRESS &nbsp; · &nbsp; `[x]` DONE
  &nbsp; · &nbsp; `[—]` OUT-OF-SCOPE (rationale required)

---

## 1 · What the goal actually asks for

| Aspect | Concrete requirement |
|---|---|
| **Explain** | The page must communicate, in plain prose, which "building block of life" each rule represents. The viewer should leave knowing what a coacervate is and why it matters, not just that the canvas has pretty bubbles. |
| **Building blocks** | The atomic units the page is trying to expose: prebiotic chemistry, monomers, autocatalysis, compartmentalisation, chirality, replication, the genetic code, selection, descent. |
| **Show** | Live, manipulable rendering — not static plates. A reader should be able to *move the controls* and see the building block behave. |
| **How they're controlled** | The page must surface *which knob controls what mechanism* — F, k, κ, mobility, lifespan etc. labelled with their physical meaning, not just the symbol. |

---

## 2 · Current state inventory

What is shipped on `claude/zealous-meitner-SrX1L` (PR #6) as of this
commit:

| Rule | Building block represented | Control surfaces today | Explanation depth today |
|---|---|---|---|
| `grayscott` | Reaction-diffusion → first emergent pattern (Turing morphogenesis) | F, k, Pearson preset | Formula only (PDE); citation in marginalia. ⚠ no narrative |
| `soup` | Brownian primordial chemistry (Stage 0) | count, D, evap, drift | Light citation. ⚠ no "this is Oparin-Haldane soup" framing |
| `natural-selection` | Prebiotic mixing → first compartmentalisation (amoeba) | amoeba lifespan | Citation only. ⚠ Miller-Urey weighting not surfaced to user |
| `chirality` | Homochirality — symmetry-breaking of L vs D | α, β, D, noise | Frank citation. ⚠ ee% in readout but no "why this matters" copy |
| `coacervate` | Membrane-less proto-cells (Oparin / LLPS) | M, κ, substeps | Cahn-Hilliard formula. ⚠ no link to "this is a proto-cell" |
| `vents` | Energy source + porous compartment (Russell-Lane) | D, drift, decay, src | PDE formula. ⚠ no "this is where chemistry meets thermodynamics" |
| `conway` | *Reference automaton* — not a building block of life | density, wrap | Honest citation. ✔ correctly framed as canonical CA |
| `wolfram1d` | *Reference automaton* — not a building block of life | rule number, seed | Honest citation. ✔ correctly framed as canonical CA |

**Building blocks represented today:** prebiotic chemistry · pattern
formation · compartmentalisation (amoeba + coacervate) · homochirality ·
hydrothermal-vent energy capture.

**Control surfaces today:** every rule has parameter sliders, but the
labels are physics symbols (F, k, α, β, κ, M) — the page does not yet
say *what each slider controls in the biology*.

---

## 3 · Gap analysis

### A · Explanation layer (highest priority)

The page renders pretty SEM-grade frames but the prose layer is thin:
marginalia is rotating citations, not a narrative. A first-time viewer
sees "STAGE 9 · COACERVATE / Cahn-Hilliard" and learns nothing about why
coacervates matter for the origin of life.

- [ ] **P0-A1** Each rule gets a 1-sentence "what this is" line directly
  under the formula caption — separate from the formula and from the
  rotating marginalia. Plain English, no jargon.
- [ ] **P0-A2** Each parameter slider gets a tooltip on hover with the
  physical interpretation — e.g. `F` → "feed rate of fresh substrate"; `k`
  → "kill rate of the catalyst v"; `κ` → "interface stiffness — high
  values give fewer, larger droplets". Drives the "how they're
  controlled" requirement directly.
- [ ] **P0-A3** Marginalia ticker grows a *first* card per rule that is
  the **building-block claim** ("This shows X. The reason it matters
  for the origin of life is Y."), distinct from the citation cards.
- [ ] **P1-A4** A persistent "About this stage" expandable panel under
  the readout — 50-word paragraph per rule, written from the
  origin-of-life perspective.

### B · Missing building blocks

The four Python-only stages cover four building blocks the web client
cannot yet demonstrate live. The previous PR's commit message said
"vesicles + LUCA are the next-easiest"; the punchlist captures all four:

- [ ] **P1-B1** `raf` — Reflexively-autocatalytic-and-food-generated sets
  (Kauffman 1971). Graph-on-canvas: nodes = molecules, edges = catalysed
  reactions, glow if part of an active RAF. Demonstrates **autocatalysis
  as self-control**.
- [ ] **P1-B2** `rna-world` — Eigen quasispecies on a 1-D sequence
  lattice. Demonstrates **information control** (replication fidelity →
  error catastrophe at ε_c = ln(σ)/L). Hardest of the four; needs a
  careful simplification.
- [ ] **P1-B3** `vesicles` — Lipid-bilayer membrane sphere under
  Helfrich curvature. Demonstrates **true compartmentalisation** (as
  opposed to coacervate's liquid-liquid one). Easier than RAF.
- [ ] **P2-B4** `genetic-code` — 4×4 codon → amino-acid table with
  selection feedback (Vetsigian-Woese-Goldenfeld). Demonstrates **the
  controller** (the literal genetic code) coming into being.
- [ ] **P2-B5** `luca` — Pathway-graph parsimony over the lineage tree.
  Demonstrates **descent control** — the last universal common ancestor
  as a control surface for everything downstream.

### C · Narrative arc

The 8 rules sit side-by-side in a dropdown; there's no story connecting
them. The Python build has a `pipeline` rule that runs the whole arc
end-to-end.

- [ ] **P1-C1** Add a "TOUR" button that auto-advances rules every ~30 s
  in the canonical order (`grayscott` → `vents` → `soup` →
  `natural-selection` → `chirality` → `coacervate` → … → `vesicles` →
  `luca`), with the marginalia narrating each chapter transition.
- [ ] **P2-C2** Add a small horizontal "chapter" rail above the canvas
  showing where the viewer is in the arc, with completed stages dimmed
  and current stage lit.

### D · Control surfaces — labelling & affordance

- [ ] **P0-D1** Parameter labels carry the physical name, not the
  Greek-letter symbol alone. E.g. `α growth` exists today on chirality;
  extend to every rule.
- [ ] **P1-D2** Add a "default / typical / extreme" three-button
  preset row for every continuous-parameter rule (currently only
  grayscott has presets). This *shows control* by showing the response
  to known parameter changes.
- [ ] **P2-D3** Cross-rule param coupling badge: when a rule's params
  cross a published threshold (Pearson F=k boundary, Frank ee critical
  point, Eigen error catastrophe), surface a small "regime: X"
  indicator in the readout bar.

### E · Honesty

- [ ] **P1-E1** Note in the marginalia that `conway` / `wolfram1d` are
  *not* building blocks of life — they're reference automata for
  sanity-checking the engine. Currently their cards talk only about CA
  history; a viewer might miss that those two are off-arc.
- [ ] **P1-E2** Footer copy: state which of the 12 Python stages are
  ported and which aren't, with a one-line explanation of why
  (NumPy/SciPy density).

### F · Layout & UX

- [ ] **P2-F1** Move marginalia from a full-width band into a vertical
  side-card beside the canvas — gains vertical space, keeps prose
  always-visible.
- [ ] **P2-F2** Persist the last-selected rule + palette + SEM mode in
  `localStorage` so a return visit lands in the same place (URL hash
  already encodes it but typing the bare URL drops it).
- [ ] **P2-F3** Reduced-motion mode tested + documented (the CSS
  respects `prefers-reduced-motion`, but nothing in the page tells the
  user it does).

---

## 4 · Done so far (history)

- [x] Multi-rule sandbox (4 rules: conway, wolfram1d, grayscott, soup).
- [x] v4.0 SEM port — depth-shaded rendering, warm-sepia / cool-mono
  palettes, LIVE SEM FEED badge with pulse, reticle, vignette,
  scale-bar.
- [x] +4 rules: natural-selection, chirality, coacervate, vents.
- [x] Compressed layout — sandbox fits a single ~900 px viewport;
  bottom gallery removed; `main img { background: transparent }`
  defensive rule.
- [x] URL hash state for rule + SEM mode + palette + per-rule params.
- [x] Marginalia ticker (rotating citations per rule, 6.5 s cadence).
- [x] Brush painting + touch input.
- [x] Keyboard shortcuts (space, s, r, c, n, 1–8, m, p).
- [x] Railway Dockerfile deploy — `python -m http.server` on `docs/`.

## 5 · Explicit out-of-scope

- [—] **Full Python engine in the browser via Pyodide.** Rationale: the
  v1 README already covers this — 4 000+ lines of NumPy per stage; the
  bundle would dwarf the rest of the page. Keep the JS ports.
- [—] **Volumetric / true-3D rendering.** Rationale: PRD §8 says v4 is
  2.5-D depth shading; volumetric is a v5 conversation.
- [—] **GPU shader path on the web.** Rationale: 8 rules at ≤ 256² is
  comfortably CPU-bound; WebGL adds shader-source surface that would
  drift from the desktop Python build.

---

## 6 · How this file is maintained

Every PR that touches `docs/web2/` should:
  1. Tick off items in §3 that the PR closes (move `[ ]` → `[x]` and
     migrate the line into §4).
  2. Add any new gap the PR surfaces as a fresh `[ ]` item with a
     priority tag.
  3. Update §2's *Explanation depth* column if a rule's framing
     changed.

The file is plain Markdown so `grep '\[ \]'` gives a punchlist of open
items at any time.
