# web7 — experiments & controls punchlist

A brutal, evidence-based review of every web7 experiment and its controls,
prompted by the observation that the experiments were *"only partially completed —
you can turn off parts but there are no controls."*

Method: two fan-out code audits over all 12 live rules + the controller
(`main.js`), the responsive CSS, and the UX spec, cross-checked against
`docs/ROADMAP.md` (§7 REV-* punchlist; per-stage REAL/PARTIAL verdicts) and
`docs/design/UX_SPEC_WEB7.md`.

The README/PR #46 headline — *"all 13 stages built, every control genuinely
wired"* — was **overstated**: the per-stage sliders were mostly real, but the
richest control surface shipped dead, the whole control panel vanished on narrow
screens, and several stages were scientifically hollow or faked.

## Per-stage verdict (live SEM rule)

| # | Stage | Rule | Verdict | Note |
|---|-------|------|---------|------|
| 0 | Miller–Urey | `soup` | REAL | particle + spatial-Strecker chemistry; 4 live knobs |
| 1 | Reaction–diffusion | `grayscott` | REAL | fully wired; surfaces presets as an enum param |
| 2 | Autocatalytic sets | `raf` | REAL | 16-species mass-action ODE; topology frozen |
| 3 | Vesicles | `vesicles` | REAL | Allen–Cahn + Helfrich; **claim fixed** (see below) |
| 4 | Hydrothermal vent | `vents` | ~~PARTIAL~~ → **REAL** | **rebuilt** with a real proton gradient (see below) |
| 5 | Mineral catalysis | ~~`grayscott` dup~~ → `minerals` | ~~FAKE~~ → **REAL** | **REV-18 closed** (see below) |
| 6 | Homochirality | `chirality` | REAL | Frank 1953; **β floor fixed** (see below) |
| 7 | RNA world | `rna` | REAL | Eigen quasispecies; careful |
| 8 | Genetic code | `code` | REAL | Glauber dynamics; abstract codon topology |
| 9 | Coacervates | `coacervate` | PARTIAL | only κ changes the result; 2 knobs rescale time |
| 10 | Protocell selection | `natural-selection` | REAL | genuine; single slider |
| 11 | LUCA | `luca` | REAL | consensus model; not phylogeny |
| — | Capstone | `life` | PARTIAL | real Avida core; metabolism hardcoded; visual cap |

## Closed in this cycle

- [x] **Dead presets surfaced.** Every rule shipped a curated `presets` array
  (named regimes + teaching hints); the controller never read it (~10 stages of
  dead science). Added a first-class **Regime** picker in `buildParamPanel`
  (`main.js`) that applies a preset's params, fires `onParamChange`, optionally
  reseeds, re-syncs sliders, and shows the hint; a manual edit drops to *custom*.
- [x] **Controls survive every screen.** `styles.css` did `.key{display:none}`
  ≤1180px, hiding **both** Parameters and the parts panel with no fallback —
  violating UX_SPEC §4.2 (*"collapse without losing any control"*). The rail is
  now a slide-in **drawer** (launcher + scrim + ✕, Esc/scrim to close, focus
  managed).
- [x] **REV-18 — real mineral catalysis.** Stage 5 was a Gray-Scott stand-in.
  Replaced with `experiment/rules/minerals.js`, a faithful port of
  `stage_minerals.py` (Ferris 1996; Cairns-Smith 1982): monomer→polymer on a
  montmorillonite clay mask, `k_clay` ≫ `k_bulk`. Polymer localises on the clay;
  the "no catalysis" regime erases it.
- [x] **Vents — real proton gradient.** Was an advection-diffusion plume that
  *admitted in its own code* it had "NO proton field". Rebuilt with a simulated
  pH gradient across the mineral membrane; acetate is fixed in proportion to the
  **proton-motive force** (`pmf` control). PMF=0 ⇒ ΣA=0 (no gradient, no
  chemistry) — the chemiosmotic mechanism the stage is actually about.
- [x] **Chirality β floor.** Slider min 0.05 → 0, so the tooltip's own
  "β=0 → racemic forever" demonstration is reachable.
- [x] **Vesicle overclaim.** Dropped the unsimulated "selectively permeable"
  caption to match the curvature-only model.
- [x] **Guard test.** `tests/controls.mjs` (zero-dep, in CI) asserts every
  preset sets real params within slider bounds, minerals localises on clay, and
  vents fixes carbon only under a proton gradient.

## Open follow-ups (not yet done)

- [ ] **Coacervate — one real knob.** `mobility` and `substeps` only rescale
  time; only `kappa` changes the steady-state. Add mean composition φ̄ (controls
  droplet number/area, independent of κ's size) and surface its presets.
- [ ] **Life — expose the metabolism.** The energy economy that decides survival
  (`ingestGain`, `eDiv`, `instructionCost`, …) is hardcoded in `cfgFromParams`;
  expose the load-bearing constants. Also the photoreal feed renders only the top
  ~30 organisms, so `population`/`maxPopulation` have little visible effect —
  decouple or raise the cap.
- [ ] **Code — real codon topology.** "single-mutation neighbours" are lattice
  neighbours, not 4×4×4 codon-table adjacency; model the real table to make it
  genetic-code-as-error-minimization rather than abstract chemical smoothing.
- [ ] **RAF — graph rewiring.** One frozen 16-node graph; add a rewire/coreSize
  control so RAF *emergence* (the actual scientific question) is explorable.
- [ ] **Vesicles — a real lumen.** Add an encapsulated-solute field the closed
  domain actually traps, so "inside vs outside" is modelled, not asserted.
- [ ] **LUCA — naming vs model.** The "tree of life" preset implies phylogeny the
  consensus model doesn't compute; implement clade tracking or rename.

## ROADMAP REV-* mapping (web-scope items)

- **REV-18** (web canonicalisation) — *port `stage_minerals.py` → JS* — **done**.
- REV-19/20/21/22/23 — web2/web3 CI gating, web rename, Three.js vendoring — out
  of scope for this experiments-and-controls cycle; tracked in `docs/ROADMAP.md` §7.
