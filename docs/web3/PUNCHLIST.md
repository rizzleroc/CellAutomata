# cellauto · web 3.0 — goal punchlist

**Goal.** *"Explain the building blocks of life and show how they are
controlled."*

This file tracks the gap between the canonical `docs/web3/` client and
that goal. It is updated every time we ship a change touching the web
client — each round, items move between sections. (web2 / web1 are
preserved as historical bundles; web3 is the live root redirect.)

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

What is shipped on `main` — web3 is the live canonical client
(`https://rizzleroc.github.io/CellAutomata/web3/`) as of this commit:

| Rule | Building block represented | Control surfaces today | Explanation depth today |
|---|---|---|---|
| `grayscott` | Reaction-diffusion → first emergent pattern (Turing morphogenesis) | F, k, Pearson preset | Formula only (PDE); citation in marginalia. ⚠ no narrative |
| `soup` | Brownian primordial chemistry (Stage 0) | count, D, evap, drift | Light citation. ⚠ no "this is Oparin-Haldane soup" framing |
| `natural-selection` | Prebiotic mixing → first compartmentalisation (amoeba) | amoeba lifespan | Citation only. ⚠ Miller-Urey weighting not surfaced to user |
| `chirality` | Homochirality — symmetry-breaking of L vs D | α, β, D, noise | Frank citation. ⚠ ee% in readout but no "why this matters" copy |
| `coacervate` | Membrane-less proto-cells (Oparin / LLPS) | M, κ, substeps | Cahn-Hilliard formula. ⚠ no link to "this is a proto-cell" |
| `vents` | Energy source + porous compartment (Russell-Lane) | D, drift, decay, src | PDE formula. ⚠ no "this is where chemistry meets thermodynamics" |
| `vesicles` | True bilayer compartment (Helfrich curvature) | D, κ, γ, substeps + regimes | aboutStage + marginalia claim + regime row. ✔ |
| `raf` | Autocatalysis as self-control (Kauffman RAF) | catalysis, food, decay, substeps + regimes | aboutStage + claim + regime row. ✔ |
| `rna` | Information control (Eigen quasispecies / error catastrophe) | μ, σ, L, substeps + regimes | aboutStage + claim + live μc readout + regime row. ✔ |
| `code` | The controller — self-organising genetic code (VWG) | β, HGT, mutation, K, sweeps + regimes | aboutStage + claim + regime row. ✔ |
| `luca` | Descent control — consensus last universal ancestor (Woese) | μ, selection, transfer, core thr., substeps + regimes | aboutStage + claim + regime row. ✔ |
| `conway` | *Reference automaton* — not a building block of life | density, wrap | Honest citation. ✔ correctly framed as canonical CA |
| `wolfram1d` | *Reference automaton* — not a building block of life | rule number, seed | Honest citation. ✔ correctly framed as canonical CA |

**Thirteen rules ship today** (eleven on-arc building blocks + two off-arc
reference automata).

**Building blocks represented today:** prebiotic chemistry · pattern
formation · compartmentalisation (amoeba + coacervate) · true bilayer
vesicles · homochirality · hydrothermal-vent energy capture · autocatalysis
(RAF) · information control (RNA world) · the genetic code · descent /
LUCA. The full chemistry-to-life arc now runs live in the browser.

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

- [x] **P0-A1** Each rule gets a 1-sentence "what this is" line directly
  under the formula caption. Shipped 2026-05-30 in "Goal-Legibility Pass."
- [—] **P0-A2** Per-slider hover tooltip. Superseded by **P0-G2**
  (per-control consequence sentence) — same content, biology-first
  framing, displayed in the persistent control-hint area instead of a
  hover tooltip so it's always visible. Jury verdict 2026-05-30.
- [x] **P0-A3** Marginalia ticker's first card per rule is the
  building-block claim. Shipped 2026-05-30 in "Goal-Legibility Pass."
- [x] **P1-A4** A persistent "About this stage" expandable panel under
  the readout — a ~50-word origin-of-life paragraph per rule, collapsed
  by default. Shipped 2026-05-31 in the web3 production round; the nine
  `aboutStage` strings are the vetted web2 prose. Closes §3-A — the
  explanation layer is complete on web3.

### B · Missing building blocks — CLOSED 2026-06-01

The four formerly-Python-only stages covered four building blocks the web
client could not demonstrate live. All four now ship as JS rules (see the
web3 Building-Blocks Round in §4), so this section is complete — every
building block in the canonical arc now runs in-browser:

- [x] **P1-B1** `raf` — Reflexively-autocatalytic-and-food-generated sets
  (Kauffman 1971; Hordijk & Steel 2004). Shipped 2026-06-01 in the web3
  Building-Blocks round. Graph-on-canvas: 16 species on a fixed reaction
  graph, edges = catalysed reactions, the core ring glows mint when the
  set ignites. A near-zero base rate makes catalysis genuinely
  load-bearing — at catalysis 0 the food feeders can't out-pump decay and
  the set goes dark. Demonstrates **autocatalysis as self-control**.
- [x] **P1-B2** `rna` — Eigen quasispecies on a 128² distance lattice
  (Eigen 1971; Eigen & Schuster 1977). Shipped 2026-06-01 in the web3
  Building-Blocks round. Distance-only reduction (Hamming distance to a
  master sequence) keeps it NaN-proof; below μc a bright master domain +
  mutant halo, above μc the dish collapses to the random-sequence floor.
  Demonstrates **information control** — the error catastrophe at
  μc = 1 − σ^(−1/2L) for this spatial lattice.
- [x] **P1-B3** `vesicles` — Helfrich-curvature lipid bilayer. Shipped
  2026-05-31 in web3 / v4.1. Implements
  ∂φ/∂t = D ∇²φ − γ φ(1−φ)(½−φ) − κ (∇²)²φ + noise, with
  vesicle-bilayer ring sprites at local maxima of φ above the vesicle
  threshold. The biharmonic (∇²)²φ term is the Helfrich bending energy
  that closes the membrane into a sphere — the distinguishing property
  of a real vesicle vs coacervate's liquid-liquid droplet.
- [x] **P2-B4** `code` — 8×8 codon → amino-acid-class lattice with a
  β-weighted Glauber relaxation + horizontal-gene-transfer of fitter
  sub-codes (Vetsigian-Woese-Goldenfeld 2006). Shipped 2026-06-01 in the
  web3 Building-Blocks round. A scrambled confetti map crystallises into
  smooth chemically-graded blocks; HGT merges rival domains into one
  shared universal code. Demonstrates **the controller** (the literal
  genetic code) coming into being.
- [x] **P2-B5** `luca` — 120² lattice of 16-bit genomes under divergence
  (mutation), selection toward a fixed environmental optimum, and
  horizontal transfer (Woese 1998; Weiss et al. 2016). Shipped 2026-06-01
  in the web3 Building-Blocks round. A per-locus majority consensus IS the
  reconstructed last universal common ancestor — a genome no single cell
  holds. Demonstrates **descent control** — push divergence past selection
  and transfer and the core shatters (no LUCA).

### C · Narrative arc

The 8 rules sit side-by-side in a dropdown; there's no story connecting
them. The Python build has a `pipeline` rule that runs the whole arc
end-to-end.

- [x] **P1-C1** TOUR button — auto-advances rules every 30 s through
  the canonical chemistry-to-life arc (`soup` → `vents` → `grayscott` →
  `natural-selection` → `chirality` → `coacervate`). Skips conway /
  wolfram1d (off-arc). Hotkey `t`. Stops on manual rule change.
  Shipped 2026-05-30 in "The Arc Round."
- [ ] **P2-C2** Add a small horizontal "chapter" rail above the canvas
  showing where the viewer is in the arc, with completed stages dimmed
  and current stage lit.

### D · Control surfaces — labelling & affordance

- [x] **P0-D1** Every parameter label across all 8 rules carries the
  physical name (`feed rate F`, `mobility M`, `interface stiffness κ`,
  `acetate decay`, …). Shipped 2026-05-30 in "Goal-Legibility Pass."
- [x] **P1-D2** Preset-regime row for every continuous-parameter arc
  rule (soup, natural-selection, chirality, coacervate, vents,
  vesicles) — a one-click row of named biological regimes that snaps the
  sliders, reseeds the PDE-field rules, and lights the active regime;
  moving a slider de-highlights it. grayscott keeps its Pearson
  dropdown; conway/wolfram1d (off-arc) get none. Shipped 2026-06-01 in
  the web3 Control Round, porting web2's mechanism. *Shows control* by
  demonstrating the response to known parameter changes.
- [ ] **P2-D3** Cross-rule param coupling badge: when a rule's params
  cross a published threshold (Pearson F=k boundary, Frank ee critical
  point, Eigen error catastrophe), surface a small "regime: X"
  indicator in the readout bar.

### E · Honesty

- [x] **P1-E1** Conway and Wolfram 1D's marginalia BUILDING-BLOCK CLAIM
  cards now lead with "Off-arc reference automaton — not a building
  block of life." Closed organically as part of the "Goal-Legibility
  Pass" 2026-05-30 (the A1 / A3 work both surfaced this honestly).
- [x] **P1-E2** Footer carries an honesty paragraph on port status.
  Shipped 2026-05-30 in "The Arc Round" listing the five then-Python-only
  stages. Updated 2026-06-01 in the web3 Building-Blocks round: all
  thirteen building blocks now run live in JS, so the paragraph (and the
  welcome-modal footer) was reworded to drop the Python-only claim — the
  full chemistry-to-life arc now runs in-browser.

### G · Goal framing (added 2026-05-28 by single-judge pass; see §7)

The judging pass surfaced three gaps the original A–F sections didn't
capture, all directly demanded by the goal statement.

- [x] **P0-G1** Subtitle now reads *"the building blocks of life, and
  how each is controlled."* Shipped 2026-05-30 in "Goal-Legibility Pass."
- [x] **P0-G2** Per-control consequence sentence wired up — focus or
  hover any slider and the `control-hint` line under the rule-controls
  says what raising/lowering does to the biology. Shipped 2026-05-30
  in "Goal-Legibility Pass." Subsumes the earlier P0-A2 tooltip idea.
- [x] **P0-G3** First-visit welcome modal explains the arc in plain
  English, dismissable, persists via `localStorage`
  (`cellauto-web2.welcomeDismissed`). Deep-link visits skip it so
  shared URLs aren't intercepted. Hotkey `?` re-opens. Shipped
  2026-05-30 in "The Arc Round."
- [x] **P0-G4** Control-mechanism legend table inside the welcome
  modal — each shipped stage paired with the type of control it
  demonstrates (chemistry without organisation · compartment-from-
  mixing · pattern self-organisation · geological compartment + energy
  · symmetry-breaking · membrane-less proto-cell). Shipped 2026-05-30
  in "The Arc Round."

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

- [x] **web3 Building-Blocks Round — all 13 stages live** (2026-06-01) —
  closes the four remaining missing building blocks (**P1-B1** RAF,
  **P1-B2** RNA world, **P2-B4** genetic code, **P2-B5** LUCA) by
  integrating `rules/raf.js`, `rules/rna.js`, `rules/code.js`, and
  `rules/luca.js` into the web3 client. Each is a faithful, NaN-hardened
  JS simplification of its desktop stage that passes the smoke harness.
  Wiring: four `<script>` tags in `index.html` (after vesicles, before
  main.js); four ids appended to `RULE_ORDER` (raf, rna, code, luca) and
  threaded into `TOUR_ORDER` at arc points (raf after grayscott, rna
  after chirality, code + luca last); a 5-card MARGINALIA block per rule
  (first card = BUILDING-BLOCK CLAIM with citation); a SCALE_BAR_UNITS
  entry per rule; the welcome legend gains four stage rows; lede rule
  count "Nine → Thirteen"; keymap "1–9 → 1–0". **Hotkeys:** `Digit0` now
  maps to the 10th rule (raf); `Digit1`–`Digit9` keep the first nine
  rules; rules 11–13 (rna, code, luca) have NO digit hotkey — reachable
  via the dropdown or the tour only, and don't crash. The footer +
  welcome-modal honesty paragraphs were reworded: nothing is Python-only
  anymore — the full chemistry-to-life arc, from primordial soup to LUCA,
  now runs in-browser. `tests/smoke.mjs` RULE_FILES gains raf/rna/code/luca.
  web3 smoke 368 → 631 checks / 0 failures across 13 rules; web2 smoke
  unchanged at 359 / 0 (web2 untouched).

- [x] **web3 Control Round — P1-D2 parity** (2026-06-01) — closes the
  parity gap flagged in the production round: web3 forked before web2's
  Control Round, so it lacked preset-regime rows. Ported web2's
  preset-row mechanism (`buildPresetRow` / `applyPreset` / active-
  highlight) into web3 `main.js` + `styles.css`, and authored three
  named biological regimes per arc rule (soup, natural-selection,
  chirality, coacervate, vents, vesicles), each validated against web3's
  actual params — web3's vesicles is a Helfrich PDE (κ/γ params), so its
  regimes were designed fresh, distinct from web2's. web3 smoke 188 →
  368 checks / 0 failures (new preset-range + apply-then-render
  assertions). Verified live: the regime row renders, clicking snaps
  params, the active button highlights exclusively, no console errors.
  Also folds in a CI-hygiene commit bumping the Pages workflow actions to
  Node-24 majors (checkout@v6, setup-node@v6, upload-pages-artifact@v5,
  deploy-pages@v5; tags verified to exist).

- [x] **web3 production round** (2026-05-31) — web3 promoted to the live
  canonical client: PR #9 merged to `main`, root `docs/index.html` now
  redirects to `/web3/`, Pages deploy green. Three production-readiness
  items shipped together: (1) **P1-A4** About-this-stage panel ported
  from web2 — an `aboutStage` field on all nine rules (the vetted web2
  prose), a collapsed-by-default accessible panel under the readout,
  reduced-motion respected; (2) new `docs/web3/tests/smoke.mjs` (adapted
  from web2's harness) — 188 checks / 0 failures across 9 rules; (3) the
  Pages CI `test` job now gates BOTH `docs/web2` and `docs/web3` smoke
  before build/deploy, so a broken canonical client can't ship. Verified
  live: page loads with no console errors, all 9 rules register + render,
  the About panel toggles, every web3 asset serves HTTP 200. NOTE — a
  real open gap surfaced: web3 forked before web2's "Control Round", so
  it lacks the **P1-D2** preset-regime rows web2 has (web3 rules carry no
  `presets`); tracked open in §3-D. (Closed 2026-06-01 — see the web3
  Control Round entry above.)

- [x] **web3 / v4.1 PRD round** (2026-05-31) — new `docs/web3/` bundle
  alongside web2; root `docs/index.html` redirect promoted to web3.
  Implements the v4.0 PRD §F3 sprite layer in JS: every continuous-
  field rule renders in three composed passes (SEM substrate →
  bioform sprite overlay → instrument chrome). Seven sprite kinds
  procedurally drawn on canvas — protocell-sphere, amoeba, granule,
  chirality-glyph (L/D), coacervate-droplet, mineral-cell (hex
  honeycomb), vesicle-bilayer (concentric rings). Each rule grew a
  `sprites(w, h)` method driven by its simulation state. Sprite-mode
  toggle persisted in URL hash + `x` hotkey. Also closes **P1-B3**
  by porting vesicles as the 9th rule with a real Helfrich-curvature
  PDE.

- [x] **The Arc Round** (2026-05-30) — four items shipped as one batch,
  giving the eight rules a narrative spine. Items: P0-G3 first-visit
  welcome modal with arc-summary lede, P0-G4 control-mechanism legend
  table inside the same modal, P1-C1 TOUR button (auto-advances rules
  every 30 s through the canonical chemistry-to-life order, hotkey
  `t`), P1-E2 footer honesty paragraph listing the five Python-only
  stages. Adds two hotkeys: `t` (tour), `?` (about). No new simulation
  code; pure DOM + JS + CSS.
- [x] **Goal-Legibility Pass** (2026-05-30) — six items shipped as one
  batch following the three-provider MCP jury verdict (see §7):
  P0-G1 subtitle = goal, P0-A1 per-rule "what this is" line,
  P0-D1 physical-name slider labels across all 8 rules,
  P0-G2 per-control consequence hint (focus a slider to see what the
  knob does to the biology), P0-A3 marginalia leads with the
  BUILDING-BLOCK CLAIM, P1-E1 conway / wolfram1d explicitly marked
  off-arc reference automata. Pure text + minor CSS; no new
  simulation code.
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
  4. If goal alignment is uncertain or the punchlist has materially
     changed, run a judgment pass via `whipgen_fanout_with_judge`
     (prompt template in §7) and append the verdict to §7.

The file is plain Markdown so `grep '\[ \]'` gives a punchlist of open
items at any time.

---

## 7 · Judgment log

Each entry below is a prioritisation pass against the GOAL. The goal is
the single criterion: *"Explain the building blocks of life and show
how they are controlled."*

The **preferred** judging route is `whipgen_fanout_with_judge` — fan out
the open punchlist to ChatGPT / Claude / Kimi / OpenLLM in parallel, let
a judge LLM pick the strongest analysis with confidence. When the
whipgen MCP server is reachable, every entry below should ideally carry
a `judge: …  confidence: …` line from that route. Single-judge entries
are interim and explicitly marked so.

### 2026-05-28 · interim · single-judge (Claude, in-session)

#### TOP 5 ranked (highest goal-lift per unit work)

1. **P0-A1** — one-sentence "what this is" line per rule. Smallest
   possible change that turns each rule from "pretty math on a canvas"
   into "explained building block." This is the *Explain* half of the
   goal in one paragraph of work.
2. **P0-D1** — physical-name slider labels for every rule (only
   chirality has them today). Cheapest possible win for the
   *how-they're-controlled* half — costs less than an hour, every
   slider stops being a Greek letter.
3. **P0-A2** — per-slider hover tooltip with the physical
   interpretation. The natural depth-up from D1: D1 names the knob, A2
   says what the knob does to the biology. Pair them in one PR.
4. **P0-A3** — marginalia first-card = the building-block claim
   ("This shows X; it matters because Y."). Completes the explanation
   triad with A1+A2; uses the existing ticker infrastructure, no new
   UI surface.
5. **P1-B3** — `vesicles` rule. Of the five missing stages, this is
   the easiest port and adds the most goal-relevant building block:
   *true* membrane compartmentalisation (Helfrich curvature), as
   distinct from coacervate's liquid-liquid kind. The other four
   missing stages (B1, B2, B4, B5) are higher-effort and lower-lift
   per hour.

#### Deprioritise / cut

- **P2-C2** chapter rail — superseded by **P1-C1** TOUR; pick one.
- **P2-F1** marginalia side-card — pure UX rearrangement, no
  goal-lift.
- **P2-F2** localStorage persistence — URL hash already covers the
  share/restore use-case; the bare-URL re-entry is a niche.
- **P2-F3** surface reduced-motion to user — the CSS already respects
  it; advertising it doesn't advance the goal.
- **P2-D3** regime-boundary badges — interesting but advanced; only
  the small fraction of viewers who already know the param physics
  would notice. Park for a later "depth" pass.

#### Missing from the punchlist (the goal demands these, list doesn't capture them)

- **NEW · P0-G1** *Goal subtitle on the page.* The current subtitle
  reads "a multi-rule observation bench — four automata, one canvas"
  — mechanics, not goal. A viewer lands without knowing what the page
  is *for*. Replace with: "the building blocks of life, and how each
  is controlled." One-line edit; clarifies intent for every visitor.
- **NEW · P0-G2** *Per-control consequence sentence.* Slider tooltips
  (A2) explain what the parameter *is*; this item explains what it
  *does to behaviour* — e.g. "F: how much fresh substrate is fed.
  Raise it and spots replicate faster; below ~0.02 the system goes
  extinct." A2 + G2 together fulfil the *show how they're controlled*
  half of the goal.
- **NEW · P0-G3** *Orientation lede shown at boot, dismissable.* A
  50-word card overlaying the canvas on first visit, explaining the
  arc (chemistry → compartmentalisation → information). Dismissed
  forever in localStorage. Without this, the viewer lands mid-arc on
  whatever rule the URL points to.

#### Ship-next batch — "The Explanation Round"

Ordered: **P0-G1 → P0-A1 → P0-D1 → P0-A2 → P0-A3 → P1-E1**

Why ship these together as one unit: this batch closes the *Explain*
half of the goal in a single PR. The page (G1) declares what it's
for; every rule (A1) tells the viewer what building block it is;
every slider (D1+A2) is named and explained; the marginalia ticker
(A3) leads with the building-block claim instead of a citation; and
the two reference automata (E1) stop pretending to be on the arc.
After this round the page can pass the test *"does a first-time
visitor understand what each canvas means without leaving the page?"*

Estimated effort: 2–3 hours. No new rules; no rendering changes;
copy + a tooltip system + one CSS pass.

#### Next-batch-after-that

The natural follow-on is **"The Control Round"** — P1-D2 (preset
rows, *show* the parameter response) and P0-G2 (per-control
consequence sentences). After Explanation + Control are both shipped,
the goal is structurally satisfied for the 8 currently-shipped rules,
and the remaining work is purely additive (more rules: B1–B5).

### 2026-05-28 · MCP fanout attempt — partial · diagnostic only

**Why partial:** the user re-authorised the whipgen MCP and requested
the full `fanout_with_judge` jury. After the OAuth handshake the tool
catalog came back and `whipgen_health` reported every provider
`available: true`, but the actual LLM browser tabs the daemon drives
were almost all dormant:

  - **chatgpt** — responded to a short ping in 10 s; timed out on the
    full punchlist prompt under the MCP's 60 s call cap.
  - **claude** — 60 s timeout on a one-word ping; tab dormant.
  - **kimi** — 60 s timeout on a one-word ping; tab dormant.
  - **gemini** — 60 s timeout (even on `model: fast`); tab dormant.
  - **openllm** — `OpenLLM connect failed at http://127.0.0.1:1234`,
    i.e. LMStudio was not listening on the Windows host.

`whipgen_connect` returned `connected: true` but the underlying browser
sessions were still asleep — connect re-attaches the daemon to *existing*
tabs, it can't revive ones that have lost their auth. A real multi-LLM
verdict needs the user to wake the dormant tabs (re-log into Claude.ai
/ Kimi / Gemini in the daemon's debug Chrome window and re-start
LMStudio). The interim Claude-in-session ranking above stands as the
operative verdict until that happens.

**Operational implication for THIS round:** ship the "Explanation
Round" batch named in the interim verdict (G1 → A1 → D1 → A2 → A3 →
E1). When the MCP jury is reachable again, run it on the *post-batch*
state, not the pre-batch state — we won't waste a fanout asking
"should we still ship the batch we just shipped".

### 2026-05-28 · MCP async fanout attempt — no settled answers

Async fanout `fanout_mpr78lxi_54481c` over `[chatgpt, claude, kimi]`
with `perProviderTimeoutMs: 120000`. All three settled as
`per-provider-timeout`:

  - **chatgpt**  durationMs: 120010, errorCode: per-provider-timeout
  - **claude**   durationMs: 120003, errorCode: per-provider-timeout
  - **kimi**     durationMs: 120002, errorCode: per-provider-timeout

The ChatGPT tab had answered a one-word "pong" prompt in 10s
immediately beforehand, so the daemon-to-tab path is alive but the
tab cannot complete a long-prompt generation in 2 min — typical sign
of a stuck conversation, an unfinished captcha, or an expired session
that lets you type but never responds.

**No usable jury verdict came out of this attempt.** The interim
Claude-in-session ranking remains operative; the "Explanation Round"
batch is still the recommended ship-next.

**To unblock for next round:** on the Windows host running the
whipgen daemon, in the debug-Chrome window —

  1. Open `chat.openai.com`, `claude.ai`, `kimi.com`,
     `gemini.google.com` tabs and confirm each shows a working composer
     (type "hi" and hit send; should get an answer).
  2. If any tab shows a captcha, expired session, or "rate limited"
     banner, log in / dismiss it; whipgen drives the existing tab and
     can't fix the auth state.
  3. Start LMStudio (or any OpenAI-compatible server) on
     `127.0.0.1:1234` if you want the `openllm` provider in the jury
     pool — optional, three other providers are enough.

Then re-run `whipgen_fanout_with_judge` (sync) with the same prompt;
it should land in ~30-60 s of wall-clock.

### 2026-05-30 · MCP fanout — three-provider jury verdict (operative)

Async fanout `fanout_mpru0g40_b15e1b` over `[chatgpt, claude, kimi]`
settled cleanly: 3/3 in 67 s wall-clock (perProviderTimeoutMs:
180000). All three providers returned full structured responses.

**This entry supersedes both interim entries above.** It is the
operative MCP-mediated verdict.

#### Cross-provider consensus

  - **Unanimous in top 5:** P0-A1, P0-G2.
  - **Two of three:** P0-G1 (Claude + Kimi), P0-D1 (Claude + ChatGPT),
    P0-A3 (Claude + ChatGPT).
  - **One vote each:** P1-B1 (Kimi — RAF), P1-B2 (ChatGPT — RNA),
    P1-C1 (Kimi — TOUR).

  - **Unanimous cut:** P2-F1, P2-F2, P2-F3 (all three call these
    layout/UX-only, off-goal).
  - **Two-of-three cut:** P2-D3 (ChatGPT + Kimi — "too technical
    before the plain-English layer exists"), P2-C2 (ChatGPT + Claude
    — redundant with TOUR).

#### Meta-judge verdict

Winner: **Claude's "Goal-Legibility Pass"** —
`P0-G1 → P0-A1 → P0-D1 → P0-G2 → P0-A3`.

Reasoning: strictest ordering, most actionable framing, and the only
provider that surfaces the single strongest missing item (a
control-mechanism legend mapping each building block to the
*type* of control it demonstrates — autocatalysis, information,
compartmentalisation). ChatGPT and Kimi converge on a near-identical
batch but with weaker ordering rationale.

Confidence: **0.85** — three independent providers converging on the
same 5-item shape from different angles is high signal; the only
delta is whether `P0-G3` (orientation lede) belongs in this batch
(ChatGPT + Kimi yes; Claude leaves it for round 2).

#### Items the jury surfaced that the punchlist lacked

All three providers, in different vocabulary, named the same gap:
the page never synthesises *what "control" means across rules*.
Folded into §3-G as a new P0:

  - **P0-G4** *Control-mechanism legend* — a single small artifact
    (one paragraph + a table) listing the building blocks the
    sandbox demonstrates and the type of control each one represents
    (Stage 1 = pattern self-control; Stage 2 = thermodynamic
    compartment; Stage 6 = chiral symmetry-breaking; Stage 9 =
    membraneless droplet formation; etc.). Without this the viewer
    sees eight rules but never sees the cross-rule organising
    principle.

ChatGPT also flagged secondary candidates worth tracking but not in
the immediate batch: an *input → output causality readout* per
slider (a richer cousin of P0-G2), a canonical life-arc ordering
(subsumed by P1-C1), and a *stage success criterion* per rule
(subsumed by P0-A3 with stricter wording).

#### Action

Punchlist §3-G has been updated with **P0-G4** as a new item.
**Operative ship-next batch:** P0-G1 → P0-A1 → P0-D1 → P0-G2 →
P0-A3 (Claude's "Goal-Legibility Pass"). Estimated effort: 2–3 h.
No new simulation code; pure text + tooltip + minor CSS.

The interim Claude-in-session ranking (which had A1/D1/A2/A3/B3 in
its top 5) is **overridden** on two items:
  - P0-G2 promoted into the batch (jury 3/3 votes).
  - P0-A2 (hover tooltip) drops out — superseded by P0-G2's
    "consequence sentence" which subsumes the tooltip idea with a
    biology-first framing the tooltip lacked.
  - P1-B3 (vesicles) drops out of *this* batch — still a strong
    item, but the jury is unanimous that explanation layer ships
    first, new rules ship second.

### 2026-05-30 (round 2) · "The Arc Round" — shipped without jury

User said "keep improving" after the Goal-Legibility Pass landed.
Attempted `whipgen_fanout` async over `[chatgpt, claude, kimi]` for a
fresh ranking; the call timed out at 60 s and a follow-up
`whipgen_status` probe also timed out — the whipgen daemon got stuck
on lingering in-flight jobs after the previous round.

Shipped without a fresh jury verdict, using the previous round's
guidance: of round 1's unanimous "next-round" candidates, the
**P0-G3 / P0-G4 / P1-C1 / P1-E2** quartet was the strongest coherent
batch — gives the eight rules a narrative spine (welcome lede → arc
in canonical order → control-type legend → honest port-status). No
new simulation code; pure DOM + JS + CSS.

**Items shipped:**
  - **P0-G3** first-visit welcome modal (dismissable, localStorage
    persists, deep-link visits skip it).
  - **P0-G4** control-mechanism legend table inside the same modal —
    closes the gap all three round-1 providers surfaced.
  - **P1-C1** TOUR button + hotkey `t`, walks the 6 on-arc rules at
    30 s cadence; skips conway/wolfram1d; stops on manual override.
  - **P1-E2** footer honesty paragraph naming the 5 Python-only
    stages with the install command.

Hotkeys added: `t` (tour toggle), `?` (about modal), `Esc` (close
modal / stop tour). All 5 round-2 items remaining (P1-A4, B1, B2, B3,
B4, B5, C2, D2, D3, F1, F2, F3) are unaffected.

**Re-run the MCP jury** at next opportunity so round-3 starts from a
real verdict not the previous round's stale next-step advice. The
likely next batch — pending jury — is "Add a Rule": port P1-B3
(vesicles) or P1-B1 (RAF) as the first additive building block to
follow the explanation-layer + arc-spine rounds.

### 2026-05-31 · web3 / v4.1 PRD round — shipped without jury

User asked for "the newest updates from 4.1" (PRD v4.0 §6 Phase 2/3
sprite library). MCP jury was not consulted this round — the operative
batch was determined by the PRD itself rather than a fresh fanout
verdict, which is appropriate when the user is following the existing
roadmap.

**Scope of the round:**

  1. **New bundle `docs/web3/`** — bootstrapped from web2, all v2
     functionality carried forward. Root `docs/index.html` redirect
     promoted from `/web2/` to `/web3/`. v2 and v1 remain reachable
     at their canonical paths.
  2. **PRD §F3 sprite layer in JS** — `docs/web3/sprites.js` ships
     seven procedural canvas painters (protocell-sphere, amoeba,
     granule, chirality-glyph, coacervate-droplet, mineral-cell,
     vesicle-bilayer). The compositor runs after the SEM blit; each
     rule's `sprites(w, h)` method returns descriptors driven by the
     simulation state (local maxima of the height field for the PDE
     rules, every amoeba cell for natural-selection, every particle
     for soup, every chimney wall cell for vents).
  3. **Sprite-mode A/B toggle** — checkbox in the sidebar + `x`
     hotkey + URL-hash persistence. Allows direct comparison of
     substrate-only vs substrate+sprites.
  4. **P1-B3 vesicles** ported as the 9th rule (real Helfrich-
     curvature PDE with biharmonic term, scale-bar `200 nm`,
     marginalia ticker, tour-order insertion after vents).
  5. **Welcome modal updated** — legend gains the Stage 3 vesicles
     row; lede mentions "nine simulations" and the sprite layer;
     localStorage key versioned to `cellauto-web3.welcomeDismissed`
     so v2 dismissals don't suppress the updated v3 lede.

**Re-run the MCP jury** for round 4 to pick the next batch from the
remaining open items (P1-A4, B1, B2, B4, B5, C2, D2, D3, F1, F2, F3).
The natural follow-on is one of:
  - "Add another rule" — P1-B1 RAF (autocatalytic sets) is the most
    goal-critical of the remaining missing building blocks per the
    jury's round-1 vote breakdown.
  - "Preset Round" — P1-D2 default/typical/extreme buttons per rule
    to *show* control by demonstrating response curves.
  - "Polish Round" — P1-A4 about-this-stage panel + P2-D3 regime
    badges + P2-F3 reduced-motion advertising.

