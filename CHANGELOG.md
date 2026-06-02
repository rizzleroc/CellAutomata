# Changelog

All notable changes to cellauto are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [4.1.1] — 2026-06-01

**Generated protagonist art lands in Channel B.** The "Day in the Life"
protagonist is no longer only procedural: a generated scanning-electron-
micrograph protocell body bundle now ships in `cellauto/assets/narrative/`, and
the optional sprite bridge composites it *under* the procedural face.

### Added — narrative protagonist art bundle (`cellauto/assets/narrative/`)
Eight SEM protocell body plates — a shared `cell_protagonist_idle` plus one per
narrative mood (`protagonist_{curious,calm,excited,triumphant,struggling,weary,
reborn}`) — generated on a flat `#FF00FF` chroma field and trimmed to ≤768 px.
Each beat now resolves to its mood-matched body, while
`character.render_character` still draws the per-mood face/expression on top, so
the generated art lifts the whole dawn → rebirth arc. With no art on disk the
channel stays fully procedural, so the shipped behaviour degrades gracefully.

### Changed — alpha-aware sprite bridge (`cellauto/sprites.py`)
`load_body_sprite` now honours a genuine alpha channel directly (new
`has_real_alpha`): a true-transparency cutout is used as-is, skipping the magenta
chroma key, while flat-key plates still key (with feathered de-spill) as before.
So both keyable magenta plates and real-alpha PNGs drop into the asset dir
without code changes. Three regression tests added — **276 total, all green**.

---

## [4.1.0] — 2026-05-30

**Two channels and hi-res.** cellauto's render path is now explicitly
two-channel: Channel A is the grounded SEM micrograph (unchanged — every pixel
still traces to a real `render_rgb(state)` value), and Channel B is a new,
additive, *toggleable* narrative layer — the anthropomorphized "Day in the Life
of a Cell." The renderer also decouples render resolution from display
resolution, so the live canvas can supersample and a single frame can export at
up to 4K.

### Added — Channel B narrative layer (`cellauto/channel.py`, `narrative.py`, `character.py`)
A new `NarrativeChannel` composites, over a finished SEM frame: a procedural
protagonist cell (`render_character`, seven moods, with its own breathe/blink
animation), a typeset narration ribbon carrying a day-clock + title + a
typewriter-revealed line, a gentle vignette-weighted time-of-day grade, and a
small "STORY · DAY IN THE LIFE" tag so the layer never masquerades as instrument
truth. The script (`cellauto/narrative.py`) maps the twelve abiogenesis pipeline
stages onto twelve day beats, dawn → rebirth (`beat_for` also collapses the
canonical 5-stage pipeline onto the arc). Channel B has its **own animation
clock**, independent of the simulation step loop and of the SEM badge pulse, so
the protagonist keeps breathing and the ribbon keeps typing even while the sim
is paused.

It plugs in as a pure *post-compositor*: `SemRenderer.post_compositor` is invoked
on the finished (chrome'd) frame inside `compose()`, and is the identity when
unset — so Channel A is never altered and the layer is fully reversible.

### Added — hi-res render + export (`cellauto/hires.py`)
`SemRenderer` gained a `render_size` field: when set above the canvas size the
live frame is composed at `factor×600` and LANCZOS-downsampled to the display,
for crisper, anti-aliased on-screen output. `cellauto/hires.py` adds
`supersample`, `export_frame_png`, `export_hires_png`, and `export_hires_gif`,
all renderer-agnostic (they take a `compose_at(size)` callable). The narrative
post-compositor runs at the compose resolution, so the story overlay exports
crisp too.

### Added — app integration (`cellauto/app.py`)
- View ▸ **Story · Day in the Life** toggle (installs/removes Channel B; persists).
- View ▸ **Render scale (supersample)** → 1× / 2× / 3× (persists).
- File ▸ **Export hi-res PNG…** (composes the current frame, with the story
  overlay if enabled, at a hi-res edge length).
- Channel B's clock is driven from the existing ~20 Hz `_animate` tick and
  re-blits via a new cheap `SemRenderer.reanimate_overlay()` that re-applies the
  overlay to a cached pre-overlay frame *without* re-running the SEM shade
  pipeline — so the character animates while paused at negligible cost.
- Stage, palette, and reduced-motion preferences propagate to Channel B; reduced
  motion freezes its clock. All new prefs persist alongside the SEM config.

### Added — narrative art bundle (`tools/render_narrative_art.py`)
Renders all twelve day beats (each a real headless run of the corresponding
pipeline stage → SEM → Channel B) plus a 4×3 contact-sheet poster into
`docs/generated/narrative/`. Doubles as an end-to-end Channel-A → Channel-B
smoke test at hi-res.

---

## [4.0.9] — 2026-05-30

**Closed the two remaining confirmed-deferred punchlist items — B8 (Stage 0
SEM sprites) and E2 (control-experiment A/B view) — plus a size-robustness
bug-class fix surfaced while building E2.** Both features were carried as
"deferred" in the ROADMAP; this release ships them, verified visually against
rendered output rather than by assertion alone.

### Fixed — SEM sprite tint + contact shadow (B8) in `cellauto/renderer_sem.py`
`load_sprite` previously tinted sprites so opaque shadow pixels floored at pure
black, which read as hard cut-out holes on the warm micrograph. Sprites are now
ramped through the palette LUT (`black=lut[110]`, `white=lut[250]`) so the
darkest body pixel lands on a mid stop, the source alpha is pulled back to 0.9,
and `composite_sprites` lays a blurred, down-right-offset contact shadow under
each pasted sprite so bodies sit *on* the substrate instead of floating.

### Fixed — Stage 0 SEM no longer renders a "wall of balls" (B8)
Re-enabling Stage 0 (primordial soup) sprites naïvely (one protocell per
`is_ameba` cell) tiled the entire frame with overlapping spheres — `is_ameba`
is the *dominant* cell state here (~90% of the grid), not a rare body.
`AbiogenesisStage0Soup.render_sprites` now emits a sparse, SEM-honest set: a
handful (≤5) of distinct protocell bodies placed via a coarse lattice +
nearest-candidate spread (so they read as separate compartments, not a grid),
plus a light scatter (≤26) of particulate granules (freshly-reacted `is_new`
sites first, then a strided slice of settled cells). Deterministic; `[]` for an
empty grid. Stage 0 opts into the SEM field renderer via `sem_eligible = True`,
gated in `app.py` so it activates only when SEM mode is on (the discrete render
path is byte-identical when SEM is off). Stage 3 vesicles verified unregressed.

### Added — control-experiment A/B view (E2) in `cellauto/diagrams.py`
`render_control(stage_index, …, rule_name=…)` mirrors `render_apparatus`:
`_CONTROL_RENDERERS_BY_RULE_NAME` maps all 12 abiogenesis rule names to a
matching null-experiment panel (with index fallback for the canonical 0–4).
Each panel strikes through the disabled driver and shows the null outcome —
flat histogram (Miller-Urey priors off), empty dish (Gray-Scott feed → 0),
uniform-noise melt (RNA error catastrophe), zero droplets (coacervate), etc. —
built on a shared `_control_plate` helper in the Catalytic Silence grammar.
The "How it works" dialog now embeds the apparatus and its control
side-by-side (`_show_how_it_works`), captioned EXPERIMENT / CONTROL.

### Fixed — apparatus/control diagrams clipped fixed-position text when shrunk
The diagrams are authored at a 640×320 design size with non-reflowing text. The
A/B dialog originally rendered them directly at the smaller embed width, which
clipped right-edge labels ("self-replic[ation]", "error catastrop[he]", …).
The dialog now renders each diagram at native 640×320 (where text fits) and
LANCZOS-downscales the *image* into the embed box. Separately, four renderers
(`render_rna_world`, `render_coacervate`, `render_homochirality`,
`render_genetic_code`) raised `ValueError: x1 must be >= x0` at narrow widths
because of hardcoded pixel coordinates; all four now scale their coordinates to
width/height fractions with `max()` clamps, preserving the 640×320 look while
rendering correctly at any size (covered by parametrized size-robustness tests).

### Tests
`tests/test_b8_sprites.py` (7) pins the sprite tint ramp, contact shadow, and
Stage 0 sprite emission; `tests/test_e2_control.py` (43) pins the control
registry, A/B divergence, determinism, and size-robustness across all 12
renderers × 3 small sizes. Full suite: 262 passed, mypy clean, ruff clean.

## [4.0.8] — 2026-05-29

**Brutal full-app review — finished the half-finished "How it works" feature
across the *whole* pipeline.** A ground-up audit asked: what is documented as
done but only partially built? The answer was the apparatus / "How it works" /
connected-narrative feature (E1/E3/E4, shipped in v4.0.6–v4.0.7). It was
complete for the canonical 5-stage pipeline but silently degraded for 7 of the
12 stages of the extended pipeline — and the apparatus dispatch had a latent
correctness bug. All three gaps are now closed.

### Fixed — apparatus-diagram dispatch was index-keyed and collided (A2)
`app.py:_show_how_it_works` resolved the diagram with `render_apparatus(
info.index)`. The extended pipeline's `StageInfo.index` values **collide** with
the canonical indices: the alkaline vent has `index=1` (same as Gray-Scott) and
mineral catalysis has `index=3` (same as vesicles). So opening "How it works"
on the vent showed the Gray-Scott *reactor*, and minerals showed the *CMC
bilayer* — the wrong experiment entirely. Dispatch is now keyed on each rule's
unique `name`: `_RENDERERS_BY_RULE_NAME` maps all 12 abiogenesis rule names to
their renderers, `render_apparatus` prefers `rule_name` over the index map, and
`_show_how_it_works` passes the inner rule's name
(`engine.state.inner_rule.name`). Verified: all 12 extended-pipeline stages now
resolve to the correct diagram.

### Added — 6 missing apparatus diagrams (A3) in `cellauto/diagrams.py`
The extended pipeline's other 6 stages had no diagram at all (the dialog quietly
skipped the section). Added procedural PIL renderers in the established
Catalytic Silence grammar (title + sub-caption, labelled schematic, bottom
`Control:` line), each grounded in `docs/science.md`:

- **`render_mineral_clay()`** — montmorillonite clay band (hatched/stippled tan,
  charge ticks), bulk-water monomers, teal polymer chains rooted on the surface.
- **`render_homochirality()`** — Frank-1953 reaction scheme (`A+L→2L`, `A+R→2R`,
  `L+R→inert`) + a 2-D field split into teal L-domains / magenta R-domains.
- **`render_rna_world()`** — Hamming-distance grid, fitness-weighted
  colonisation arrow, error-threshold box `ε_c = ln(σ)/L ≈ 0.14`.
- **`render_genetic_code()`** — a cell carrying both a codon strand and a private
  codon→amino-acid table, decode→peptide→target-compare loop, `code_consensus`.
- **`render_coacervate()`** — gold Cahn-Hilliard droplets coarsening (Ostwald
  ripening) with the conserved-φ equations `μ = φ³−φ−κ∇²φ`, `∂φ/∂t = M∇²μ`.
- **`render_luca()`** — gene-presence matrix across lineages with the ≥70 %-
  prevalence core highlighted; `luca_size` readout.

Reference shots committed at `docs/generated/audit/apparatus_{minerals,chirality,
rna,code,coacervate,luca}.png`.

### Added — E3/E4 metadata for the 7 extended `StageInfo` entries (A1)
`_STAGE_VENT_INFO`, `_STAGE_MINERAL_INFO`, `_STAGE_CHIRALITY_INFO`,
`_STAGE_RNA_INFO`, `_STAGE_CODE_INFO`, `_STAGE_COACERVATE_INFO`, and
`_STAGE_LUCA_INFO` left all seven of the v4.0.6 fields
(`apparatus`/`methods`/`control`/`expect`/`caveats`/`consumes`/`produces`)
empty, so the "How it works" panel printed "(not yet documented…)" and the
chapter card had no narrative line for them. All seven are now populated from
`docs/science.md`, with each `control` keyed to the actual knob/stat the rule
exposes (vent → `pmf_mV`; minerals → `polymer_on_clay_x100`; chirality →
`k_cross`; RNA → `error_threshold_x1000`; code → `code_mutation`; coacervate →
`kappa`/`droplets`; LUCA → `luca_size`/`core_prevalence`), and `consumes`/
`produces` following the extended-pipeline order.

### Verified — Stage 3 vesicle SEM render (A4, closes the deferred V4 audit)
The v4.0.5 audit deferred confirming the B1–B8 substrate changes didn't regress
the Stage 3 lipid-bilayer rendering. Confirmed: Stage 3 under SEM mode composes
a rich depth-shaded image (variance ≈ 3.7 k, 6.4 k unique colours, 398 membrane
cells) — no regression.

### Notes
- The 5 *shared* canonical `StageInfo` entries keep their canonical-neighbour
  `consumes`/`produces` prose; in the extended pipeline their narrative line
  still references the canonical neighbour rather than the extended one. A
  per-pipeline narrative override is tracked as a v4.1 nicety, not a gap.
- 158 / 158 tests green; ruff + mypy clean. No engine/physics change — every SEM
  pixel still traces to a real `render_rgb(state)` value.

---

## [4.0.7] — 2026-05-27

**E1 — apparatus diagrams shipped.** The v4.0.6 honesty audit deferred E1
(visible apparatus diagrams) as "highest cost, lowest honesty-per-hour."
User pushback after v4.0.6 was direct: "did we add all the experiments
like the Miller-Urey for the primordial soup yet?" — answer was no, only
the prose lived in the "How it works" dialog. v4.0.7 adds the visual
diagrams alongside the prose so the user sees the apparatus, not just
hears it described.

### Added — `cellauto/diagrams.py`
Procedural PIL renderers for the canonical 5-stage pipeline:

- **`render_miller_urey()`** — Stage 0: boiling-water flask with flame,
  vapour-tube with directional arrows, spark-gap chamber labelled
  CH₄/NH₃/H₂/H₂O with teal electrical-arc between electrodes, condenser
  coil, product trap with stippled amino-acid solution. Caption names
  the outcome (glycine, alanine, formic acid) and pins it to
  `MILLER_UREY_SPECIES`.
- **`render_gray_scott_reactor()`** — Stage 1: continuous-flow reactor
  with u feed reservoir, F (feed rate) labelled, gel-stage box containing
  cartoon spots, F+k waste outlet, teal v-autocatalyst return loop.
  Control caption: "F = 0 ⇒ v decays exponentially → no spots ever form."
- **`render_raf_vessel()`** — Stage 2: round Kauffman vessel with
  continuously-fed food-set arrow, species inventory as labelled nodes,
  teal RAF-closure cycle highlighting a self-sustaining loop, RHS legend
  listing the three RAF rules (every reaction catalysed; catalyst is in
  the set; reactants from food set) and the connectivity threshold
  n_reactions / n_species ≳ 1.0.
- **`render_cmc_bilayer()`** — Stage 3: solution column with mM
  concentration axis, dashed teal CMC threshold at 85 mM, vesicle rings
  nucleating above threshold, scattered amphiphiles (head + tail) below,
  centre-right zoomed bilayer cross-section showing hydrophilic-head /
  hydrophobic-tail arrangement.
- **`render_protocell_selection()`** — Stage 4: three generations of
  protocells (N → N+1 → N+2) showing growth, division, selection;
  per-cell genome bars; fitness colour mapping in a legend (teal = high /
  selected, dim bone = low / purged).
- **`render_vent_chimney()`** — Standalone (extended-pipeline stage II):
  Lost-City alkaline hydrothermal vent cross-section. Porous chimney wall
  in centre with pore texture, ocean on both sides labelled (pH ≈ 5.5
  acidic, CO₂-rich), vent interior labelled (pH ≈ 10 alkaline), H₂ feed
  arrow rising from serpentinisation below, CO₂ feed arrows from the
  ocean into the wall, Wood-Ljungdahl reaction box (`2 CO₂ + 4 H₂ →
  CH₃COOH`), thermodynamic readout (PMF ≈ 266 mV, ΔG ≈ −25.7 kJ/mol).
- **`render_apparatus(stage_index, *, rule_name=None)`** — dispatch
  wrapper. Stages 0-4 return a populated diagram; `rule_name` is checked
  for standalone rules (`abiogenesis-hydrothermal-vent` → vent); other
  cases return `None` and the dialog quietly skips the diagram section.

### Wired into `app.py:_show_how_it_works`
Above the prose APPARATUS section, the dialog now embeds the rendered
diagram via `tk.PhotoImage(format="PPM")` (no ImageTk dependency).
Falls back to prose-only when the diagram returns `None` (extended-
pipeline stages 6-11 ship without diagrams until the v4.1 catalogue).

### Quality gates
- 158 / 158 tests still pass (no new test regressions).
- `ruff check` + `ruff format` clean on `cellauto/diagrams.py` and the
  updated `app.py`.
- `mypy cellauto/diagrams.py` clean.
- Five reference shots committed at
  `docs/generated/audit/apparatus_stage{0..4}.png` and a live UI capture
  at `docs/generated/audit/post_e1_howitworks_stage1.png`.

### Still deferred
- **E2** — split-canvas A/B control view (live + null-parameter twin).
  Highest scientific value, highest implementation cost; deferred to
  v4.0.8.
- **On-canvas callout arrows** — annotated labels pointing at features
  in the live render. Stuck behind E2 because the canvas layout is in flux.
- **Extended-pipeline apparatus** — diagrams for stages 6-11 (vents,
  minerals, chirality, RNA world, genetic code, coacervates, LUCA).
  Deferred to v4.1.

---

## [4.0.6] — 2026-05-27

**Scientific-honesty audit closure (E0, E3, E4)** — user critique caught
that the app had become "results-only science": gorgeous SEM renders with
no apparatus, no controls, no plain-English explanation, and no causal
narrative connecting the stages. A whipgen-claude audit confirmed every
gap and identified the most damning finding — **all of this content
already lived in `docs/science.md`, and the UI actively threw it away,
referencing the file only as a dead string in the About dialog.** v4.0.6
ships E0 + E3 + E4 from that audit; E1 (apparatus diagrams) and E2 (A/B
control view) remain in the punchlist as separate cycles.

### Added — E0: SEM badge honesty
- Badge text changed `LIVE SEM FEED · Stage N — name` → `SEM RENDER · Stage N — name`.
  The old "LIVE SEM FEED" implied an instrument feed; this is a depth-shaded
  interpretation of a simulation, not a measurement.
- New centred footer below the scale bar: "Render of simulated chemistry — not a microscope image." in dim bone.

### Added — E3: "How does this stage work?" panel
- **`StageInfo` extended** with five optional prose fields per stage:
  `apparatus`, `methods`, `control`, `expect`, `caveats` — all sourced
  from existing `docs/science.md` per-stage notes.
- **`?` button** beside the wall-label title and **`Help ▸ How does this
  stage work?…`** menu item open a scrollable `Toplevel` dialog showing
  every field as a labelled section: APPARATUS · METHODS · CONTROL ·
  EXPECT TO SEE · HONEST LIMITATIONS · CONSUMES FROM PREVIOUS STAGE ·
  PRODUCES FOR NEXT STAGE.
- All five canonical pipeline stages (0–4) ship with the full prose:
  Miller-Urey spark gap, Gray-Scott flow reactor, Kauffman reaction
  vessel + RAF closure, fatty-acid CMC bilayer, Eigen-Schuster replicator
  population. Each has a NAMED control variant (F=0 for Stage 1, h2=0
  for the vent, catalysis_level=0 for RAF, cmc_threshold above peak for
  vesicles, mutation_rate above ε_c for protocell error catastrophe).
- Stages without populated prose show "(not yet documented for this stage
  — see docs/science.md)" per missing field instead of crashing.

### Added — E4: Connected-narrative chapter card
- `StageInfo` gained `consumes` + `produces` fields naming what each
  stage hands off to the next.
- `_show_chapter_card` now renders an extra narrative line under the
  principle when both are populated: "From last stage: X → Now: Y" — so
  entering Stage 2 tells you what Stage 1 produced and what Stage 2 will
  produce, rather than treating each stage as a disconnected demo.
- Falls back to principle-only for stages where the connective tissue
  isn't populated yet (legacy + non-pipeline rules).

### Changed
- Badge font size kept; only the leading word + footer added.
- Chapter card grows from 460×170 to 520×220 only when the narrative
  line is populated (preserves the existing layout for fallback stages).

### Not changed
- Engine, rules, science — every pixel still traces back to a rule's
  `render_rgb(state)`. SEM is a rendering choice; science.md still owns
  the canonical reference.
- 158 / 158 tests still pass. Lint + format clean.

### Deferred (subsequent cycles)
- **E1** — per-stage apparatus diagrams (Miller-Urey flask sketch, vent
  chimney cross-section, RAF reactor vessel). Highest cost, deferred to
  v4.1 once E2 stabilises.
- **E2** — split-canvas A/B control view: live experiment + a null-
  parameter twin running on the same seed. Scientifically the highest-
  value, technically the bug-prone-est; deferred to v4.0.7.
- **On-canvas callout arrows** — annotated labels pointing at features
  in the live render. Stuck behind E2 because the layout is in flux.

---

## [4.0.5] — 2026-05-27

**Brutal-feedback audit closure** — a multimodal whipgen-claude critique loop
(four rounds, fed live SEM renders + the renderer source each time) drove
twelve concrete deltas labelled V1–V5, B1–B8, R1–R8. The result: Stage 1
under SEM mode now reads as scattered isolated protocell spheres on a dark
crystalline substrate with visible contact-shadow rings and rare pink
granules — a substantial step closer to the user's Stage 0 SEM reference.

### Round-by-round verdicts (whipgen-claude judge)
- **V1+V2 (pre-audit baseline)** — flipped height-sign so v-peaks render as
  domes not craters; disabled the Stage 1 sprite layer that read as floating
  "strange balls" stickers.
- **Round-1 audit (5/10)** — "STILL BAD: hex-packed lattice, velvet substrate,
  amputated dome bodies." Filed B1, B3–B8.
- **Round-2 (5/10)** — substrate fixed but R1 over-corrected. Filed R1–R5.
- **Round-3 (4/10)** — Lambertian gating amputated dome flanks. Filed R6.
- **Round-4 (4/10)** — soft floor still gating Lambertian on flanks. Filed R7.
- **Round-5 (7/10)** — bodies and contact shadows present. "SHIP after one
  more fix — soften the apex hotspot." Filed R8.
- **Round-6 (ship)** — apex hotspots spread across the upper third of each
  dome via height_bias_exponent 1.6 → 1.2.

### Added — shading pipeline upgrades (closes B1, B3, B4, B5, B6, B7, R1, R2, R3, R4, R5, R6, R7, R8)
- **`_voronoi_noise(h, w, density=220)`** in `renderer_sem.py` — F2-F1
  cellular noise for crystalline salt-crystal substrate texture; cached by
  shape + density.
- **`_contact_shadow(h, foot_threshold=0.45, base_threshold=0.18)`** —
  ramp-darkening in the foot-ring band so domes visibly anchor to substrate.
- **`_sprinkle_pink_variety(rgb, intensity, fraction=0.008)`** — tints
  ~0.8% of top-quartile-intensity (q92+) pixels toward dusty pink
  `(0xC8, 0x9A, 0x9A)` for the "Miller-Urey product class" variety read.
- **`_build_lut(stops, gamma=2.2)`** — gamma-biased LUT mapping so dark
  substrate sits in stops 0-1 and only dome apices reach the bone-cream
  stops 4-5.
- **Non-linear height remap** in `shade_height` — `np.where(h > 0.15,
  0.15 + (h-0.15)*2.5, h*0.3)` crushes substrate range, stretches dome range.
- **Soft height_gate on specular only** (`0.25 + 0.75*clip(h*2.5, 0, 1)`) —
  Lambertian stays full-strength on dome flanks (R7), specular is
  height-gated so substrate doesn't show specular hotspots.
- **`AbiogenesisStage1GrayScott.init_state` Poisson-disk scatter** — 6-10
  random seed patches with min-spacing rejection so the hero frame shows
  scattered isolated spheres rather than a hex-packed lattice. Degenerate
  fallback preserved for tiny grids (≤ 9 px wide).

### Changed
- Default `SemRenderer.specular_hardness` 24 → 12 (widens specular spot,
  kills the apex horizontal-slash artifact).
- Default `SemRenderer.height_bias_exponent` 1.6 → 1.2 (spreads height
  contribution across the upper third of each dome).
- Default `SemRenderer.substrate_kind` = `"crystalline"`; under that path
  the substrate texture is `0.5 * voronoi(d=1400) + 0.5 * value_noise(...)`
  — fine grain on a smooth bed.
- Default `SemRenderer.pink_variety` = 0.008 (~6-10 visible granules).
- `Stage1.render_sprites` permanently returns `[]` — depth-shaded substrate
  is the topography (v4.0.2 / V2 audit verdict, preserved).
- `tests/test_sem_sprites.py` updated: the Stage 1 sprite-count assertion
  is replaced with a contract-pin that `render_sprites()` returns `[]`.

### Not changed
- Engine, rules, science modules — every pixel still traces back to a
  rule's `render_rgb(state)` output. SEM is purely a rendering choice.
- 158 / 158 tests still pass; ruff + mypy clean.

### Deferred (subsequent cycles)
- **B8** — sprite tint + contact-shadow fix for the asset compositing path.
  Kept disabled for Stage 1; reserved for Stage 0 (which needs SEM-on-
  discrete-renderer routing — v4.0.6 work).
- **S7** — sprite libraries for the remaining nine stages (v4.1).
- **S10** — optional `moderngl` GPU acceleration (v4.2).
- **S11** — AI image-to-image refinement (v4.3).

### Quality gates (CI)
- `pytest -q` — **158 / 158 pass** (no test count regression vs v4.0.1).
- `ruff check` + `ruff format --check` — clean on every v4.0.x source file.
- `mypy cellauto/renderer_sem.py` — clean.
- Audit hero shots committed at
  `docs/generated/audit/post_r8_stage1_warm.png` and `_cool.png`.

---

## [4.0.1] — 2026-05-26

**Phase 2 sprite library** — closes S6 from the v4.0 punchlist. The depth-
shaded substrate from v4.0.0a1 now carries a stage-specific sprite layer:
each frame, the active rule's `render_sprites(state)` emits a list of sprite
positions which `SemRenderer.compose()` alpha-composites over the SEM
background before the instrument chrome overlay. Lifts Stage 1 (Gray-Scott)
and Stage 3 (vesicles) to "recognisable biological form" reading per PRD
§F3. Lifts the prerelease alpha designation; v4.0 is now a full release.

### Added — sprite compositing (closes S6 for stages 1 and 3)
- **Sprite library architecture** in `cellauto/renderer_sem.py`:
  `composite_sprites(img, sprites, palette, grid_w, grid_h)` alpha-composites
  a list of `(sim_x, sim_y, name, scale)` tuples over the depth-shaded
  background using PIL `alpha_composite`. `load_sprite(name, palette)` opens
  the asset PNG, tints it to the current palette's mid-tone via
  `ImageOps.colorize`, and caches by `(name, palette)`. `set_sprite_dir(path)`
  test hook overrides the asset root.
- **Sprite assets** at `cellauto/assets/sprites/`:
  - `stage0/granule.png` (48 px) and `stage0/protocell.png` (96 px)
  - `stage1/spot.png` (80 px) — bone-cream depth-shaded sphere with
    upper-left specular highlight
  - `stage3/vesicle.png` (112 px) — translucent membrane with phospholipid
    bilayer ring + sheen
- **Deterministic generator script** at `tools/render_sprites.py`. Re-running
  the script produces byte-for-byte identical PNGs; sprites are committed
  alongside the source so installations don't need PIL at import time.
- **Per-stage `render_sprites()` methods**:
  - `AbiogenesisStage1GrayScott.render_sprites` — local-maximum filter on the
    v-field, one bone-cream spot per peak above threshold 0.30, scaled by
    field magnitude.
  - `AbiogenesisStage3Vesicles.render_sprites` — connected-component
    labelling on the membrane mask, one vesicle sprite per centroid, scaled
    by component area.
- **App integration.** `App._render` calls `rule.render_sprites(state)` (or
  the pipeline's `inner_rule.render_sprites(inner_state)`) when the active
  renderer is `SemRenderer`. Discrete and `FieldRenderer` paths ignore the
  sprite layer — they remain byte-equivalent to v3.6 / v4.0.0a1.
- **Tests.** `tests/test_sem_sprites.py` (8 pins): sprite cache + tint round-
  trip, sprite compose differs from sprite-free, sensible per-stage counts,
  deterministic output, missing-asset graceful skip, empty-list noop.
- **Hero shots.** `docs/generated/sem_stage1_sprites_{warm-sepia,cool-mono}.png`,
  `docs/generated/sem_stage3_sprites.png`, plus the no-sprite baseline
  `docs/generated/sem_stage3.png`.

### Changed
- `cellauto-4.0.1` (was 4.0.0a1). The alpha tag is dropped now that Phase 2
  has shipped; the deferred items (S7, S10, S11) are subsequent cycles
  rather than pre-release blockers.
- `SemRenderer.compose(rgb_array, *, sprites=None)` gains the optional
  `sprites` kwarg. Existing callers that pass no sprites get the v4.0.0a1
  behaviour byte-for-byte.
- `SemRenderer.render(rgb_array, sprites=None)` mirrors the new kwarg so the
  Tk render path stays a thin wrapper around `compose`.

### Not changed
- Engine, rules, science modules, all 141 v3.6 + 9 v4.0.0a1 SEM tests.
- `FieldRenderer` (viridis path) — sprite layer is SEM-only. Toggling SEM
  off still uses the v3.6 viridis pipeline unchanged.
- The v3.6 web client. Sprite layer is desktop-only in this release.

### Deferred (subsequent cycles, scope unchanged from v4.0.0a1)
- **S7** — sprite libraries for the remaining nine stages (Phase 3, v4.1).
- **S10** — optional `moderngl` GPU acceleration (Phase 4, v4.2).
- **S11** — AI image-to-image refinement (Phase 5, v4.3).
- **Stage 0 sprites** — `stage0/granule.png` + `stage0/protocell.png` ship
  in the asset library but are not yet wired, because Stage 0 (the soup
  rule) runs on `DiscreteRenderer` not `SemRenderer`. Routing SEM-aware
  rendering through the discrete path is v4.0.2 work.

### Quality gates (CI)
- `pytest -q` — **158 / 158 pass** (141 v3.6 + 9 SEM renderer + 8 SEM sprites).
- `ruff check` + `ruff format --check` — clean on all v4.0.x source files.
- `mypy cellauto/renderer_sem.py cellauto/app.py` — clean.
- `python -m build --wheel` produces a working
  `cellauto-4.0.1-py3-none-any.whl`; smoke-installed via
  `pip install --force-reinstall --no-deps dist/*.whl`.

---

## [4.0.0a1] — 2026-05-25

The **SEM-grade rendering** release, Phase 1 of the v4.0 cycle. The v3.x line
earned scientific credibility (real Eigen-Schuster ODE, Helfrich bending,
Miyazawa-Jernigan landscape, pathway-graph LUCA, coupled 12-stage pipeline);
this release earns scientific **representation** — depth-shaded warm-sepia
micrograph rendering replaces the viridis heat-map as the default field
renderer. The simulation engine, constants, dynamics, and tests from v3.6
are unchanged. The alpha designation reflects the deferred Phase 2 / 3 sprite
libraries (see "Deferred" below); the rendering pipeline itself is feature-
complete for Phase 1.

### Added — Phase 1 SEM rendering (closes S1–S5, S8, S9, S12)
- **`cellauto/renderer_sem.py`** — a depth-shaded numpy rasteriser exposing
  the same `render(rgb_array)` interface as `FieldRenderer`. The per-stage
  rule's `render_rgb(state)` output is reinterpreted as a height field;
  gradients → Lambertian + ambient + specular shading → value-noise
  micro-texture → sepia/mono LUT → LANCZOS upscale → vignette + crosshair
  + LIVE SEM FEED badge + scale bar overlay. Same signature as the v3.6
  renderer, so `app.py` swaps between them with a single attribute flip.
- **Two palette modes.** `warm-sepia` (default — matches the user-supplied
  reference SEM micrograph) and `cool-mono` (extends the Catalytic Silence
  obsidian + bone + teal palette into 3-D shading).
- **`View ▸ SEM mode` toggle** (default ON when SEM rendering is available)
  and **`View ▸ SEM palette` submenu** in `cellauto/app.py`. Both fire
  immediate re-renders without restarting the engine.
- **Config persistence.** SEM mode + palette persist across launches via
  `~/.cellauto/config.json`, read/written by `_load_sem_config()` /
  `_save_sem_config()` in `cellauto/app.py`.
- **Graceful fallback.** If Pillow lacks LANCZOS or `SemRenderer` cannot
  initialise, the app falls back to the v3.6 `FieldRenderer` and surfaces
  a one-time non-blocking toast explaining why. No crashes; the rest of
  the GUI continues to work.
- **Reduced-motion integration.** The v3.6 `View ▸ Reduced motion`
  preference propagates to the LIVE SEM FEED badge pulse — the badge dot
  freezes when reduced motion is on, satisfying WCAG 2.2.2 / 2.3.3.
- **Hero shots.** `docs/generated/sem_stage1.png` (warm-sepia) and
  `docs/generated/sem_stage1_cool-mono.png`. The v3.6 viridis baseline
  for the same seed and step count is preserved at
  `docs/generated/viridis_stage1.png` for the README before/after plate.
- **`tests/test_sem_renderer.py`** — the regression-pin file for S9
  (≥ 8 SEM pins: non-trivial output per stage, SEM/viridis step-count
  parity on the same seed, zero-field → near-uniform background, palette
  persists across init, reduced-motion disables the pulse, PNG export
  matches the on-screen view, LANCZOS-missing fallback, performance
  budget).

### Changed
- The default field renderer for the GUI is now `SemRenderer` (when
  available). The v3.6 `FieldRenderer` is preserved as the A/B baseline and
  the fallback — toggle from `View ▸ SEM mode`. Headless `cellauto export`
  and `cellauto simulate` are unchanged.
- Version bumped to `4.0.0a1` in `pyproject.toml` and `cellauto/__init__.py`.

### Not changed (and that's the point)
- Simulation maths, constants, RNG handling, snapshot format, rule
  registry, pipeline coupling, hypercycle ODE, Helfrich term,
  Miyazawa-Jernigan landscape, pathway-graph LUCA — all identical to
  v3.6.0. Every SEM pixel still traces back to a real engine value via
  the rule's `render_rgb(state)`; the depth shading is interpretive
  (height-from-luminance), not measurement. See `docs/science.md` for
  the explicit framing.

### Deferred (to v4.0.1+)
- **S6, S7 — stage-specific sprite library (Phases 2 + 3).** Each stage's
  characteristic forms (protocell granules, Gray-Scott spots, vesicle
  bilayers, …) pre-rendered as alpha PNGs and composited over the shaded
  background. Phase 1 ships only the height-from-luminance interpretation
  of the existing `render_rgb` output.
- **S10 — optional GPU path (Phase 4).** `cellauto[gpu]` extra bringing
  `moderngl` + a GLSL port of the Phase-1 pipeline. Maintains pixel parity
  with the CPU path (golden-image regression).
- **S11 — AI image-to-image refinement (Phase 5).** `tools/sem_refine.py`
  running SEM output through a fine-tuned diffusion model at strength
  ≈ 0.35 for hero-shot quality. Opt-in, never the default.
- **`render_height(state)` per-rule overrides.** v4.0 derives the height
  field from the luminance of the existing `render_rgb` output; a future
  release will let stages expose a dedicated height map.

### Quality gates
- All four v3.6 CI gates still green: ruff, ruff-format, mypy, pytest.
  The v3.6 test suite (141/141) is unaffected by the SEM additions;
  the new `tests/test_sem_renderer.py` adds ≥ 8 SEM pins on top.

---

## [3.6.0] — 2026-05-24

The **local-vs-web parity** release. The project ships two clients running
the same Python engine: the desktop Tk app (the rich, mature one) and the
Flask web client at `cellauto/web/` (on a feature branch). A side-by-side
audit found that while the Tk app is feature-RICHER functionally (Gallery,
scrubber, protocell inspector, RAF network view, sparkline, keyboard
shortcuts, CSV export, font scaling), the web client has a set of
specific UX qualities the Tk app lacked. v3.6 closes nine of those gaps.

### Tk UX upgrades — closes L1, L3-L9, L11, L12 from the parity punchlist
- **L1: always-visible stage wall-label.** A dedicated panel above
  CONFIGURATION always shows the active pipeline stage's title,
  citation, principle, and legend. Hides for non-pipeline rules.
- **L3: Pearson preset chips.** The Gray-Scott regime preset
  combobox is now a row of toggle-button chips (spots / stripes /
  mitosis / waves / labyrinth) so all five regimes are visible at
  once with the active one highlighted in the accent style.
- **L4: debounced parameter slider updates** (250 ms for reinit
  params, 60 ms for live params). Dragging a structural slider no
  longer triggers five `init_state()` rebuilds per second.
- **L5: batch stepping at high FPS.** When the requested FPS exceeds
  30 Hz, the playback loop now batches N engine steps per Tk tick
  and renders once at the end — smooth high-throughput playback
  instead of clamping at the Tk scheduler ceiling.
- **L6: reduced-motion preference toggle** (View ▸ Reduced motion).
  Caps FPS at 10 Hz, freezes the playback pulse animation, and
  suppresses chapter-card fades — for users with vestibular or
  photosensitive disorders (WCAG 2.2.2 / 2.3.3).
- **L7: population stats as wrap-friendly chips.** Stage-II vent's
  10+ stat fields now flow as `key = value` chip-labels that wrap
  across multiple rows instead of crowding a single line.
- **L8 + L9: pulsing playback animations.** A small teal status dot
  next to the title and the canvas-rim colour both pulse in sync
  (2.2-second cycle) while the sim is live; both freeze when
  paused or when reduced-motion is on.
- **L11: tutorial-as-modal-listing** (Help ▸ Tutorial — all steps…).
  Modal Toplevel lists every tutorial step with click-to-jump
  navigation; complements the existing one-step-at-a-time mode.
- **L12: non-blocking toast notifications.** Snapshot saved /
  GIF exported / no frames captured / etc. now show as a 6-second
  auto-fading strip above the header instead of blocking
  `messagebox.showinfo` modals.

### Deferred (with rationale documented in ROADMAP §5)
- **L2: tabbed control panels** — Tk's vertical-scroll layout already
  reaches every control with one interaction; a tab refactor would
  touch 600+ lines for an aesthetic change. Not a parity gap.
- **L10: background grain texture** — Tk has no CSS-equivalent
  background-image support; achieving the 1 % noise overlay would
  require a Canvas behind every Frame for nearly-imperceptible
  effect. Not worth the complexity.

### Other
- The full audit report (web features Tk lacks, Tk features web
  lacks, aesthetic/UX differences, behavioural/scientific
  differences, web's HTTP API surface) is captured in
  `docs/ROADMAP.md` §5.
- All four CI gates still green: ruff, ruff-format, mypy, pytest
  (141/141, 88 % coverage).

---

## [3.5.0] — 2026-05-24

The **honest-gap closure** release. v3.4 shipped 12 named origin-of-life
stages and an AAA visual identity, but a self-audit found four genuine
integrity gaps: the 12-stage pipeline reset state on every promotion (so
it was twelve isolated sims on a timer, not a coupled narrative); Stage XI
admitted "TOY" in its own docstring; Stage X used a CMC switch instead of
real curvature physics; Stages VIII and XII relied on hand-shaped fitness
vectors instead of derived dynamics. v3.5 closes all of them.

### Pipeline coupling — the showstopper fix
- **State flows across stage transitions (G1).** Every stage now exposes
  `extract_signal(state) -> np.ndarray` returning a 2D float summary of
  its main output, and every stage's `init_state(W, H)` accepts a
  `seed_field` kwarg that biases initial conditions by the upstream
  signal. `AbiogenesisPipelineRule.promote()` extracts the upstream
  signal before discarding the previous state and threads it into the new
  stage's init. Forward `set_stage()` jumps carry the signal; backward
  jumps reset (rewind semantics). The chemistry-to-life arc is now a
  genuinely *coupled* simulation.
- New helpers in `cellauto/rules/abiogenesis/science.py`:
  `normalise_signal()`, `seed_from_signal()`.
- Regression test `tests/test_pipeline_handoff.py` (7 tests) pins that
  spatial correlation flows from upstream final state to downstream
  initial state with Pearson r > 0.3; pins the seeded-vs-unseeded
  difference directly; tests the full extended pipeline arc.

### Real scientific dynamics — replacing the toy bits
- **G2: Eigen-Schuster hypercycle ODE in Stage XI.** The protocell
  genome now evolves under
  `dx_i/dt = x_i ( k_i · x_{(i-1) mod n} − Φ )` with the mean-field
  dilution Φ holding Σx_i constant. The "TOY" disclaimer in the
  docstring is gone. Legacy `dynamics="proxy"` mode kept for A/B
  comparison; `dynamics="hypercycle"` is the default. Six new tests in
  `tests/test_hypercycle.py` pin the equal-concentration fixed point,
  the broken-cycle collapse, and per-step mass conservation.
- **G3: Helfrich (1973) bending elasticity in Stage X.** Added a
  biharmonic regularisation `∂φ/∂t += −κ_b · ∇²(∇²φ)` (the variational
  derivative of `E_b ∝ (∇²φ)²`). Vesicle interfaces now have a real
  bending modulus — fluid membranes resist sharp bends. Default κ_b is
  the dimensionless analogue of Helfrich's measured 2–10 × 10⁻²⁰ J.
  Pinned by a same-seed comparison: κ_b > 0 reduces total bending
  energy of the lipid field while preserving CMC pattern formation.
- **G4: Miyazawa-Jernigan-style fitness landscape in Stage VIII.**
  Replaced the fixed-target-peptide match score with a sequence-
  composition-dependent score using a published-pattern 4×4 residue-pair
  contact-energy table (`MJ_CONTACT_ENERGY`) projected to the Ikehara
  GADV proto-code: hydrophobic packing (V-V, A-V) favourable, like-charge
  contacts (D-D) unfavourable. `fitness_mode="mj_landscape"` is the
  default; the legacy `"target_match"` is kept for backward-compatibility.
  Pinned by `test_mj_landscape_prefers_hydrophobic_packing`.
- **G5: pathway-graph essentiality in Stage XII LUCA.** Replaced the
  hand-shaped 16-vector `gene_values` with a static co-occurrence
  pathway graph (5 toy pathways covering 12 of 16 genes — translation
  core, Wood-Ljungdahl, chemiosmotic ATP, H₂ chemistry, DNA
  maintenance). Fitness now rewards complete pathways and penalises
  partial machinery; essentiality is the topological invariant
  `pathway_genes`. The recovered LUCA core (≥70 % prevalence) is now
  pinned to be a subset of the network-essential set, not just a
  match-the-config-vector exercise.

### Test pins
- **G6: CMC gate.** Stage X with `cmc_threshold` set above any
  reachable lipid value produces zero vesicles; below it, positive.
- **G7: Eigen error catastrophe at ε_c = ln(σ)/L.** Below 0.5·ε_c the
  master sequence holds; above 1.5·ε_c it collapses to near-zero.
- **G8: Wood-Ljungdahl stoichiometric cap.** Flooding H₂ while
  starving CO₂ does NOT exceed the 2:1 stoichiometric limit — the
  reaction can't run faster than its limiting reagent.
- **G9: replaced the vacuous tautological `0 <= x <= 100` test** with
  a real behavioural pin: `code_mutation=0` ⇒ consensus rises above
  random baseline; `code_mutation=1.0` ⇒ consensus stays near random.
- **G10: pipeline-handoff regression pin** (described above under G1).

### Other
- **G11: CHANGELOG + README phrasing pass.** Since the science gaps
  are closed, "implements" is now honest. The v3.4 README's "every
  panel is real simulator output" claim and the magnum-opus poster
  framing are now backed by genuine coupled dynamics, not theatre.
- **G12: ROADMAP doc-drift fix.** `docs/ROADMAP.md` updated to
  reflect the 12-stage pipeline (was stuck on 5), 141 tests (was 72),
  88 % coverage, and the AAA asset bundle. The audit's §0 brutal-gap
  analysis is committed as the authoritative record of what v3.5 fixed.
- **Test count 120 → 141.** New files: `test_pipeline_handoff.py` (7
  tests), `test_hypercycle.py` (6 tests). Test rewrites in
  `test_genetic_code.py` (added G4 + G9 pins), `test_vesicles.py`
  (added G3 + G6 pins), `test_rna_world.py` (added G7 pin),
  `test_vents.py` (added G8 stoichiometric cap), `test_luca.py`
  (added G5 pathway-graph pins). Coverage: 87.09 % → 88.13 %.

---

## [3.4.0] — 2026-05-23

The "closing the honest gaps" release. The v3.2/v3.3 cycles fixed correctness
and built out the *qualitative* coverage of the origin-of-life story; this
release closes the remaining science gaps the honest assessment had flagged
as loop-iteration-sized.

### Added — closing the science gaps
- **Genetic-code emergence stage** (`abiogenesis-genetic-code`). Each cell
  carries an RNA-like strand *and* its own private codon→amino-acid table;
  both mutate; fitness is peptide match against a target catalyst.
  Selection on the code itself drives convergence toward a shared universal
  code — the Vetsigian-Woese-Goldenfeld (2006) coevolution mechanism, the
  conceptual hand-off from chemistry to biology.
- **LUCA distillation stage** (`abiogenesis-luca`). A spatial population of
  evolving cells with gene-presence bitsets; selection on a benefit-vs-cost
  gene economy distills a shared core genome = the inferred Last Universal
  Common Ancestor (Weiss et al. 2016 methodology, threshold-relaxed at 70%
  prevalence to handle non-zero mutation). `luca_size` converges to the
  essential-gene count.
- The auto-promoting **extended pipeline now spans 12 stages**:
  soup → vent → reaction-diffusion → mineral catalysis → autocatalytic sets →
  homochirality → RNA world → genetic code → coacervates → vesicles →
  protocell selection → LUCA distillation.
- **Real thermodynamic readouts in the vent stage.** The abstract proton
  field maps to actual pH via configurable `pH_alkaline` / `pH_acidic`
  (defaults 10.0 / 5.5 — Krissansen-Totton et al. 2018 early-Earth ocean
  estimate). The population dict now reports **ΔpH** (×10), **PMF in mV**
  (Nernst factor 2.303 RT/F ≈ 59.16 mV/pH unit at 25 °C; default ≈ 266 mV),
  and **ΔG in kJ/mol per proton** (Faraday × PMF; default ≈ −25.7) — exactly
  the Lane-Martin range for driving abiotic carbon fixation.
- **Wood-Ljungdahl carbon-fixation chemistry in the vent stage.** VentState
  gained `h2` and `co2` arrays; H₂ is replenished inside the alkaline
  chimney by serpentinisation, CO₂ is fed globally to model the CO₂-rich
  Hadean ocean (Krissansen-Totton 2018). Synthesis rate = mass-action
  `k_synth × PMF × [H₂] × [CO₂]` capped by the 2:1 stoichiometry of
  `2 CO₂ + 4 H₂ → acetate + 2 H₂O` (ΔG° = −95 kJ/mol). Tests prove the
  stoichiometric constraint: cutting H₂ *or* CO₂ kills the yield even when
  PMF stays at 266 mV.
- **Real-molecule labels** at the code level: `RNA_BASES = (A, U, G, C)`
  in `stage_rna.py`; `CODON_BASES` + `AMINO_ACIDS = (Gly, Ala, Asp, Val)`
  in `stage_code.py` (Ikehara 2002 GADV proto-code); `MONOMER_LABEL` /
  `POLYMER_LABEL` / `MINERAL_LABEL` in `stage_minerals.py` (Ferris 1996
  ImpA + Na-montmorillonite); `LUCA_GENE_NAMES` in `stage_luca.py` —
  16 well-attested LUCA-core gene families (rpoB, rpsC, rplB, fdhA, codhC,
  mrpA, atpA, hypE, nifH, gltB, dnaK, trpB, oxyR, gyrB, photolyase, mutS)
  aligned with the essential / accessory / deleterious gene-value tiers.
- **Web port MVP** at `docs/web/` — a single static page with a live JS
  port of the Gray-Scott PDE (Stage 1) running on an HTMLCanvas, F/k
  sliders, the five Pearson presets, and the Catalytic Silence palette.
  Vanilla JS, ~400 lines total, no Pyodide, deployable to GitHub Pages
  from `/docs`. Other stages exhibited as the existing static plate
  gallery (`docs/generated/*.png`).
- **AAA release poster** rendered via the whipgen MCP
  (`docs/generated/release_poster_v3_4_mcp.png`) and the deterministic PIL
  version (`docs/generated/release_poster_v3_4.png`) — 4×3 specimen grid of
  the 12 origin-of-life stages, Italiana + CrimsonPro + IBM Plex Mono
  typography, obsidian + bone + hairline-teal palette. Reproducible via
  `tools/render_release_poster.py`.
- **Six new pytest files** covering the new behaviour:
  `test_genetic_code.py`, `test_luca.py`, and additional vent / Wood-
  Ljungdahl assertions in `test_vents.py`. Test count: 95 → **120 (+25)**.

### Fixed — CI cleanup
- **mypy clean across the package**. Closed 24 type errors: name collision
  in `mascot.py` between the right-pupil canvas ID and the pupil-radius
  variable (renamed the radius to `_eye_pupil_r`); canvas-ID Optional
  fields narrowed to `int` with a `-1` sentinel; `Image.NEAREST` →
  `Image.Resampling.NEAREST` (Pillow ≥10); `_renderer` typed as the proper
  union; `_section` return type; font tuples normalised to 3-element
  `(family, size, style)` for the `create_text` overload; `Label.image` GC
  pin annotated; lambda-default `# type: ignore[misc]` where the idiom
  defeats inference; `create_text` anchor-Literal narrowed by unrolling a
  2-iteration loop.
- **Coverage gate fixed and lifted**: `pyproject.toml` now carries
  `[tool.coverage.run]` omitting the Tk-display-dependent modules (`app`,
  `mascot`, `__main__`, `renderer`). Coverage went **47 % → 87 %**, well
  above the 80 % floor the CI enforces.
- **Sim too fast / chapter titles sticking around**: `_animate` now ticks
  the chapter-card fade timer *before* any code that could raise a
  transient TclError, so a card can't get pinned indefinitely. RESEED /
  RESTART explicitly clear the card. **Escape dismisses an active card.**
  Default FPS lowered 8 → 5; extended pipeline `stage_duration` raised
  50 → 90 so transitions don't blow past the card; header subtitle no
  longer says "five observations" on a 12-stage pipeline.

### Changed
- Version bumped to `3.4.0` in `pyproject.toml` and `cellauto/__init__.py`.

---

## [3.3.0] — 2026-05-22

### Added
- **Extended 10-stage pipeline** (`abiogenesis-pipeline-extended`) — auto-promotes
  through every shipped origin-of-life process in scientific order: soup →
  alkaline vent → reaction-diffusion → mineral catalysis → autocatalytic sets →
  homochirality → RNA world → coacervates → vesicles → protocell selection.
  `AbiogenesisPipelineRule` was parameterised with `stage_classes`/`stage_infos`
  fields so the original 5-stage rule keeps its identical default behaviour.
- **Story-mode chapter transition cards.** When the pipeline promotes, a
  centred overlay shows "CHAPTER N · TITLE", the governing principle, and the
  citations; fades after ~4.5 s via the animate-tick countdown.
- **Per-protocell inspector.** Click any Stage 4 disc to open a Toplevel
  showing the protocell's position, radius, age, fitness, and full genome
  vector, plus a caption explaining the hypercycle-coupling fitness. Works
  for the direct stage rule and the pipeline-wrapped case.
- **Timeline scrubber.** Bounded ring buffer (cap 120) snapshots
  `engine.rule.serialize_state(...)` every step; the `SCRUB` Scale in
  TRANSPORT restores any captured frame. Stepping after scrub-back truncates
  the future so timelines branch rather than overwriting.
- **Text-scaling control** (`View ▸ Small/Default/Large/Extra-large text`) —
  `_apply_font_scale` recomputes every font tuple and re-applies the ttk
  styles uniformly; canvas overlays refresh on the same tick. Clamped
  `[0.6, 2.0]`.
- **Colour-blind-safe palette toggle** (`View ▸ Colour-blind safe palette`) —
  swaps Stage 4's red→green disc colour (the audit's flagged CVD offender)
  for a Wong blue→yellow ramp; the legend bar follows. Other diverging maps
  (chirality teal↔magenta, vents blue↔orange, viridis) are already CVD-friendly.
- **Keyboard navigation** — Space (play/pause), → (step), R (restart),
  P (promote), `[` / `]` (previous / next pipeline stage), all guarded
  against text-entry focus so Spinbox/Combobox editing isn't hijacked.
  New `Help ▸ Keyboard shortcuts…` dialog lists every binding.
- New tests: `test_extended_pipeline.py` (10-stage init / auto-promote /
  set_stage / registration); test count 95 → **102**.

### Changed
- Live stage caption on the canvas now shows the **live `current_stage`**
  rather than the StageInfo's own `index`, so the extended pipeline's labels
  match the position the JUMP combobox reads.
- JUMP combobox values now size dynamically from `len(rule.stage_classes)`,
  so the 5-stage and 10-stage pipelines both work without hardcoding.
- Version bumped to `3.3.0` in `pyproject.toml` and `cellauto/__init__.py`.

---

## [3.2.0] — 2026-05-22

### Added — research-backed origin-of-life simulator
- **Six new origin-of-life processes** (each a selectable rule with its own
  sliders, tests, tutorial, and `docs/science.md` section):
  - `abiogenesis-rna-world` — spatial Eigen quasispecies (Gilbert 1986;
    Eigen 1971). Watch the master sequence dissolve into the error
    catastrophe when the per-base error rate crosses `ε_c = ln(σ)/L`.
  - `abiogenesis-homochirality` — Frank (1953) autocatalysis + mutual
    antagonism. Tiny fluctuations break mirror symmetry into teal/magenta
    chiral domains.
  - `abiogenesis-hydrothermal-vent` — proton/pH gradient across a chimney
    wall drives organic synthesis (Russell & Hall 1997; Lane & Martin 2012).
    Flatten the gradient and synthesis stops entirely.
  - `abiogenesis-coacervate` — Cahn-Hilliard liquid-liquid phase separation
    (Oparin 1924; Banani et al. 2017). Gold droplets nucleate and coarsen
    (Ostwald ripening), a membraneless counterpart to Stage 3's vesicles.
  - `abiogenesis-mineral-catalysis` — montmorillonite clay mask (Ferris 1996;
    Cairns-Smith 1982). Polymer accumulates on the clay surface at ~12× the
    bulk-water rate; equalising the rates removes the localisation.
- **AAA visual identity.** Six "Catalytic Silence" stage plates generated via
  the whipgen MCP and wired into the Gallery menu
  (`docs/generated/stage{0..4}_*.png` + `pipeline_poster.png`).
- **`cellauto/netviz.py`** — PIL-rendered Stage 2 reaction network with the
  Hordijk-Steel RAF highlighted (teal edges, magenta catalyst links, amber
  food species). Accessible via `Gallery ▸ Reaction network (Stage 2 RAF)`.
- **Live scientific-parameter controls** (`cellauto/rules/params.py`) —
  every rule's dataclass knobs are exposed as live GUI sliders that take
  effect on the next step. Includes the Stage 1 Pearson preset picker and
  structural sliders (Stage 2 species/reaction counts + food fraction,
  Wolfram rule number) that auto-reinit deterministically on change.
- **Stage caption + colour legend on the canvas.** Drawn as zero-layout
  overlays (`_sync_stage_caption`, `_draw_legend_bar`) — the stage title +
  legend, an on-canvas viridis colorbar (red→green for Stage 4 fitness;
  diverging variants for chirality, vents, coacervates, minerals).
- **Live population time-series sparkline** under the canvas (zero layout).
- **Mandated UI toolset** (full checklist in `docs/ROADMAP.md §2`):
  - `JUMP` combobox for direct pipeline stage navigation.
  - `AUTO-PROMOTE` checkbox + `DUR` spinbox.
  - `RESET` parameter defaults; `RESTART`-to-step-0 preserving slider edits.
  - `File ▸ Export frame as PNG…`; `File ▸ Export stats as CSV…`.
- **`docs/ROADMAP.md`** — feature inventory + punchlist + mandated UI toolset
  contract (groups A-G).
- Test count 66 → 95 across `test_realdata.py`, `test_rna_world.py`,
  `test_homochirality.py`, `test_vents.py`, `test_coacervate.py`,
  `test_minerals.py`, `test_netviz.py`, `test_stage2_roundtrip.py`.

### Fixed — scientific correctness
- **`find_raf` rewritten to the real Hordijk-Steel layered closure.** The
  v3.1 one-pass implementation collapsed the inner closure into a single
  non-iterative step that declared every candidate's product producible
  unconditionally — reporting **false-positive RAFs**. The rewrite uses the
  formal Algorithms 1 + 2 from Hordijk (2023) arXiv:2303.01809: a
  food-generated closure that only adds a reaction's product once both
  reactants are producible, wrapped in an outer prune-and-recompute loop.
- **Catalysis is now mandatory** for RAF-viability — the "R" in RAF requires
  it. `_viable` rejects any reaction with `catalyst is None`. `random_reaction_network`
  now catalyses every reaction (previously left ~50% uncatalysed → dead weight).
- **Stage 2 serialises its full reaction network.** Previously
  `deserialize_state` fabricated a fresh random network on load, so resumed
  runs evolved under a different chemistry than the one that produced the
  saved field. The network is now part of the snapshot.
- Stage 4 hypercycle docstring softened from "simulates the hypercycle" to
  "fitness proxy" — the implementation does not integrate the Eigen-Schuster
  ODE. Gray-Scott CFL bound now documented; mitosis preset harmonised
  between `science.py` and `docs/science.md`.

### Changed — toy → real data
- **Stage 0 soup** is sampled weighted by Miller's 1953 measured yields
  (formic acid ≈ 49 %, glycine ≈ 13 %, glycolic acid ≈ 12 %, alanine ≈ 7 %)
  via `MILLER_UREY_SPECIES` — a real soup is *not* a uniform rainbow.
- **Stage 3 vesicles** carry a named amphiphile; `AMPHIPHILE_CMC_MM` lists
  measured CMCs (decanoic acid C10 ≈ 85 mM, oleic ≈ 0.1 mM, …) from the
  Szostak/Deamer protocell literature. The population dict reports `cmc_mM`.
- **Stage 4** exposes the Eigen quasispecies error threshold `1/L` as
  `error_threshold_x1000` alongside `mutation_rate_x1000`, so crossing it
  is observable.
- **Stage 2** reports Kauffman's catalysis connectivity
  `catalysis_level_x100 = n_reactions / n_species` — the metric the threshold
  bounds (~1-2 per species per Hordijk-Steel polymer-model results).
- The whole repo brought to `ruff check` + `ruff format --check` clean; dev
  visual-audit screenshots and the local MCP config moved into `.gitignore`.

---

## [3.1.0] — 2026-05-20

### Added
- **Catalytic Silence visual pass for the GUI.** The cards-and-filled-buttons
  dark theme was replaced with the museum-plate aesthetic the Prima Materia
  plate is built from:
  - Bundled `Italiana-Regular`, `CrimsonPro-Italic`, `CrimsonPro-Regular`,
    `IBMPlexMono-Regular`, and `IBMPlexMono-Bold` into
    `cellauto/assets/fonts/`. `_register_bundled_fonts()` registers them on
    Windows via `gdi32.AddFontResourceExW` (`FR_PRIVATE`) so they're visible
    to Tk for this process. Non-Windows falls back through Constantia /
    Cambria / Georgia / Cascadia Mono.
  - New palette: obsidian `#0a0e16`, warm bone `#e6e0d0`, desaturated-teal
    hairlines `#1f4f4c`, accent teal `#39d4c8`, magenta only on record,
    restrained brick only on stop.
  - LabelFrame cards removed. Sections are now Italiana Roman-numeral +
    tracked-mono labels (`I · OBSERVATION`, `II · CONFIGURATION`,
    `III · TRANSPORT`, `IV · REGISTER`, `V · MARGINALIA`) with thin teal
    hairlines beneath.
  - Outlined museum-card buttons (border-only, no fill) — `Primary` (teal
    Play), `Danger` (brick Stop), `Record` (magenta).
  - About dialog and GIF-export progress dialog rebuilt in the same voice
    (eyebrow / Italiana title / italic caption / hairline rule).
  - `[tool.setuptools.package-data]` now includes `assets/fonts/*.ttf`.
- **Stable window geometry.** The 1990-era reflow on every iteration is
  fixed: locked **720×1000** window, `resizable(False, False)`, tutorial
  is an always-present caption (no `pack_forget`), status uses a
  fixed-width monospace grid.
- **Prima Materia plate.** A museum-style observational plate
  ([`docs/prima-materia.png`](docs/prima-materia.png)) composed from real
  cellauto simulations under the **Catalytic Silence** design philosophy
  ([`docs/design/catalytic-silence.md`](docs/design/catalytic-silence.md)).
  Hero specimen: Stage 1 Gray-Scott at step 600 with the canonical Pearson
  "spots" pattern. Four supporting specimens: Stages 0, 2, 3, 4. Typography
  set in Italiana (display), CrimsonPro Italic (caption), and IBM Plex Mono
  (apparatus). Reproducible via
  [`docs/design/render_prima_materia.py`](docs/design/render_prima_materia.py).
- **AAA visual identity.** Three new commissioned assets generated via the
  whipgen MCP pipeline:
  - [`docs/hero.png`](docs/hero.png) — cinematic close-up of Gray-Scott
    self-replicating spots (replaces the prior step-400 screenshot).
  - [`docs/pipeline.png`](docs/pipeline.png) — five-panel infographic strip
    showing the abiogenesis pipeline left → right.
  - [`docs/icon.png`](docs/icon.png) / `cellauto/assets/icon.png` — modern
    app icon (protocell mid-division), shipped as package data.
- **Tk window icon.** `App._apply_window_icon()` loads
  `cellauto/assets/icon.png` and applies it via `iconphoto(True, …)`, so
  every Toplevel (incl. the new GIF-export progress dialog) inherits it.
- **About dialog redesign.** Replaces the bare `messagebox.showinfo` with a
  proper `Toplevel` that displays the icon, version, and pipeline summary.
- `[tool.setuptools.package-data]` entry so `assets/icon.png` ships in the
  installed wheel.

### Fixed
- **GIF export no longer freezes the GUI.** Export now captures frames one at a
  time via non-blocking `after()` callbacks, showing a modal progress bar with a
  Cancel button; the final Pillow rendering runs in a background thread.
- **Stage 4 fitness function replaced.** Shannon-entropy × concentration
  (acknowledged placeholder in PHASE2_BRUTAL §29) is replaced with the
  Eigen-Schuster hypercycle coupling: `Σ g[i]·g[(i+1)%n]`. This is zero when
  any species is absent and maximised at equal concentrations — the
  cooperatively stable state from Eigen & Schuster (1977). Growth/shrink
  threshold and colour scale updated to match the new units.
- `avg_fitness_x100` stat renamed `avg_fitness_x1000` to reflect the new
  (smaller) hypercycle scale.

### Changed
- **CI matrix now includes Windows.** `windows-latest` added alongside
  `ubuntu-latest`; `fail-fast: false` so one OS failure doesn't cancel the other.
- **CI: concurrency group cancels in-progress runs** on new push to the same ref.
- **CI: `ruff format --check`** added (was only `ruff check`).
- **CI: `mypy --ignore-missing-imports`** added as a type-check gate.
- **CI: `--cov-fail-under=80`** coverage threshold enforced.
- **CI: `cellauto export` smoke test** added (GIF export path now covered in CI).
- **CI: `pip-audit` security job** added for dependency vulnerability scanning.
- `mypy>=1.10` added to `[project.optional-dependencies] dev`.
- Version bumped to `3.1.0` in `pyproject.toml` and `cellauto/__init__.py`.

---

## [3.0.0] — 2026-05-19

### Added
- **Abiogenesis pipeline** — 5-stage chemistry-to-life simulation with citations:
  - Stage 0: primordial soup (Oparin/Haldane, Miller-Urey)
  - Stage 1: Gray-Scott reaction-diffusion (Turing 1952, Pearson 1993) — hero result
  - Stage 2: Kauffman RAF autocatalytic sets (Hordijk & Steel 2004)
  - Stage 3: lipid bilayer self-assembly (Helfrich, Deamer, Szostak)
  - Stage 4: protocell selection / hypercycle (Eigen & Schuster 1977-79)
- `abiogenesis-pipeline` rule: orchestrator that auto-promotes through all stages.
- `FieldRenderer`: numpy → `tk.PhotoImage` PPM blit — **7.4× faster** than
  `DiscreteRenderer` at 80×80, runs 200×200 in 0.08 s.
- `DiscreteRenderer`: tracks `(item_id, shape)` in `_items` — eliminates the
  per-cell `canvas.type()` Tk roundtrip that made v2.0 0.74× *slower* than v1.
- Per-rule tutorials: `tutorial_for(rule_name)` returns rule-specific walkthrough text.
- `Rule.to_config()` / `from_config()` protocol: rule parameters round-trip through
  snapshots.
- RNG state serialized via `pickle+base64` in snapshots — `Engine.load` + continue
  now matches a continuous run bit-for-bit.
- `docs/science.md` — full citation list and math for all 5 stages.
- 49 pytest tests (was 14); full coverage of abiogenesis stages.

### Fixed
- **F3 — Rule 3 `is_new` is no longer a no-op.** `is_new` reset to `False` at
  start of each step; only cells whose colour genuinely changed become `True`.
  `settled` count in the status bar is now reachable.
- **`_distinct_palette_color` crash on a 1-element palette** — validated in
  `__post_init__`.
- Wolfram1D stats: `population()` now returns `live_now`, `history_on`,
  `history_off` separately, not a misleading total-history count.
- `Rule.init_grid(grid)` replaces the `isinstance(rule, Wolfram1DRule)` branch in
  `Engine.__post_init__` (Protocol leak closed).
- `tests/test_protocol.py` asserts `isinstance(rule, Rule)` for every registered
  rule — the `@runtime_checkable` contract is now verified.

### Changed
- Project reframed from "natural-selection simulator" to **abiogenesis** (the
  project's true premise). Legacy `natural-selection` kept as alias of Stage 0.
- README rewritten: honest perf table, abiogenesis-first framing, history section.
- `requirements.txt` now single-sources from `pyproject.toml` (`pip install -e .`
  is the canonical install path).

---

## [2.0.0] — 2026-05-18

### Added
- Pluggable rule engine with `Rule` protocol.
- Conway's Game of Life (`conway`) and Wolfram 1D elementary automata (`wolfram1d`).
- Headless CLI: `cellauto simulate`, `cellauto export`.
- GIF export via Pillow.
- Save / load snapshots (JSON).
- GitHub Actions CI (Ubuntu, Python 3.10–3.12).
- 14 pytest tests.

### Known issues (closed in v3.0)
- Rule 3 `is_new` was still a no-op.
- Rendering was benchmarked as 0.74× (i.e. *slower* than v1) despite the "10×
  faster" README claim.
- `Engine.load` re-seeded the RNG from scratch, breaking the determinism guarantee.
- Rule config not serialised in snapshots.

---

## [1.0.0] — 2024-03

### Added
- Initial sketch: four rules described as "natural selection."
- Tkinter GUI with canvas rendering.

### Known issues (closed in v2.0 / v3.0)
- Rules F1–F4 not mechanically implemented.
- Zero tests, no CI, no packaging.
