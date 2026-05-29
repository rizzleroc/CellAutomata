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

### G · Goal framing (added 2026-05-28 by single-judge pass; see §7)

The judging pass surfaced three gaps the original A–F sections didn't
capture, all directly demanded by the goal statement.

- [ ] **P0-G1** Replace the subtitle "a multi-rule observation bench —
  four automata, one canvas" with the goal itself: *"the building blocks
  of life, and how each is controlled."* One-line edit; tells every
  visitor what the page is *for* before they touch a control.
- [ ] **P0-G2** Per-control *consequence* sentence (distinct from the
  A2 tooltip explaining what the parameter *is*). E.g. *"F: how much
  fresh substrate is fed. Raise it and spots replicate faster; below
  ~0.02 the system goes extinct."* A2 + G2 jointly fulfil the
  *show how they're controlled* half of the goal.
- [ ] **P0-G3** First-visit orientation lede — 50-word dismissable
  card explaining the arc (chemistry → compartmentalisation →
  information). Dismissed forever via localStorage so returning
  visitors aren't nagged.

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

