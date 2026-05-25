# PRD — SEM-grade visualization (v4.0)

**Status:** Draft · proposed for v4.0 cycle
**Author:** project owner (with audit)
**Last updated:** 2026-05-25

---

## 1. Vision

> *"It should look like a real electron-microscope image of the chemistry
> we're simulating — not a viridis heat-map on a 80×80 pixel grid."*

The v3.x line earned scientific credibility (real Eigen-Schuster ODE,
Helfrich bending, Miyazawa-Jernigan landscape, pathway-graph LUCA,
coupled 12-stage pipeline). The next jump is *representational*: the
output should look like an actual scientific instrument view — a live
SEM feed of the chemistry — so the visual story matches the
mathematical truth underneath it.

The reference image (`docs/ideal_sem_view.png`, the user-supplied
target) shows what we're aiming for:

- A monochrome / warm-sepia "instrument" palette — not coloured heat maps.
- **Depth-shaded textured surfaces** — every pixel reads as a 3-D
  micrograph fragment with directional lighting and ambient occlusion.
- **Recognisable biological forms** — spherical protocell-like blobs
  catching light, fibrous networks, granular substrate.
- A "LIVE SEM FEED" frame around the canvas, scale-bar microcopy
  underneath, the existing 3-column layout (wall-label · canvas · controls).
- A bottom marginalia ticker walking through the chemistry-to-life story.

The goal is for a viewer to look at the screen and *believe* they are
watching a microscope view of real abiotic chemistry.

---

## 2. Goals & non-goals

### In scope (v4.0)
1. SEM-grade rendering of **all 12 stages** of the extended pipeline.
2. Maintains scientific fidelity — the underlying simulation is unchanged.
   Every pixel of the SEM image is still driven by real
   reaction-diffusion / hypercycle ODE / pathway-graph values.
3. Runs on **the same hardware** the desktop client already targets
   (CPU + Tk + numpy + PIL; no mandatory GPU).
4. A **GPU acceleration path** is wired in but optional — the project
   stays installable with the existing minimal dependency set.
5. The "LIVE SEM FEED" framing extends to the web client too, so both
   clients share the same instrument aesthetic.

### Explicitly NOT in scope (yet)
- **Volumetric / true 3-D ray-traced rendering.** We're producing
  SEM-*style* 2.5-D depth-shaded imagery, not a volumetric simulation.
- **Online AI image-to-image post-processing.** Stable-Diffusion-style
  refinement is a stretch goal (Phase 5), not the baseline.
- **Replacing the underlying simulation.** Every visible feature must
  still be derivable from the engine's existing fields and entities.
  No "decorative" structures that aren't in the math.
- **Photo-real microbiology of extant cells.** The look is *abiotic*
  chemistry, not modern biology — protocells and chemistry, not E. coli.

---

## 3. Personas & use cases

| Persona | Need | What v4.0 buys them |
|---|---|---|
| **Educator** showing the origin-of-life arc to a class | A demo that's not obviously a "toy" so the science lands | Photographic SEM view that students immediately recognise as a real instrument feed |
| **Researcher** validating the science model | Visual confirmation that the chemistry is doing what it should | Depth-shaded view surfaces real spatial structure (vesicle thickness, protocell membrane curvature, RNA-cloud density gradients) that the viridis colourmap was flattening |
| **Outreach team** demoing the project at conferences | A piece that holds a viewer's attention for > 5 seconds | Living SEM feed + chapter-card story narrative + AAA poster identity |
| **Scientific illustrator / author** licencing imagery | A piece they can put in a textbook caption without disclaiming "schematic" | Output that reads as instrument-grade |

---

## 4. Functional requirements

### F1 — depth-shaded scalar fields
Every continuous field stage (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12) must
render its primary scalar field as a **height-mapped, lit, textured
surface**, not a flat colourmap.

  - Input: the stage's chosen scalar field (e.g. Gray-Scott `v`,
    coacervate `φ`, vent acetate, mineral polymer, LUCA fitness).
  - Process: compute gradients → surface normals → Lambertian +
    ambient + specular shading under a fixed directional light → add a
    procedural micro-texture (multi-octave noise) → tone-map to a warm
    sepia / cool monochrome ramp → upscale with edge-aware
    interpolation (LANCZOS).
  - Output: an 8-bit RGB image that reads as a 3-D micrograph.

### F2 — instrument identity
The canvas is reframed as an **instrument feed**, not a "viewport":

  - **Crosshair / reticle** overlay in 1-px hairline teal at the canvas
    centre, with tick marks at the four quadrant midpoints — gives the
    image the look of a microscope field.
  - **"LIVE SEM FEED · Stage N — name"** badge in the upper-right
    corner, monospace microcaps, tracked.
  - **Scale-bar microcopy** below the canvas: "1 μm" with a hairline
    bar (the bar length is scaled to the grid extent so it stays
    physically plausible across grid resizes).
  - **Vignette** at the corners (~10 % darkening) to suggest a curved
    instrument aperture.

### F3 — recognisable biological forms (sprite layer)
Each stage has a **stage-specific sprite library** that's composited
on top of the depth-shaded background:

| Stage | Sprite | Driven by sim |
|---|---|---|
| 0 — Soup | tiny coloured granules + larger spherical protocell blobs | NaturalSelectionRule cells (amoeba flag → bigger sphere, is_new → fresher edge) |
| 1 — Gray-Scott | self-replicating spots as bone-white circular forms catching light | the v-field thresholded |
| 2 — Vents | a vertical mineral-honeycomb chimney slice | chimney column mask + porous overlay |
| 3 — Vesicles | translucent membrane spheres with phospholipid bilayer rings | the lipid field thresholded + Helfrich curvature |
| 4 — Protocell selection | filled spheres with internal genome dots | the Protocell list |
| 5 — RAF | a fibrous reaction-network with glowing autocatalytic loops | RAF graph nodes + edges |
| 6 — Chirality | left-handed / right-handed helical pairs (L bone-filled, D outlined) | left vs right field arg-max |
| 7 — RNA world | concentric isobars of replicator density around the master | seq-field Hamming-binned |
| 8 — Genetic code | 4×4 codon matrix dots embossed onto a translation table surface | code field consensus |
| 9 — Coacervates | liquid-liquid droplet blobs with proper internal contrast | φ-field thresholded with Cahn-Hilliard ridges |
| 10 — Vesicles | re-uses Stage 3 sprite library | lipid field |
| 11 — Selection | re-uses Stage 4 sprite library | Protocell list |
| 12 — LUCA | a rooted phylogenetic tree etched into the surface, plus the 12 essential-gene nodes lit | LUCA core constellation + genome-derived tree |

The sprites are **rendered once at startup** (or lazy-loaded), tinted
to match the stage's SEM palette, then alpha-composited per frame.

### F4 — palette modes
Two factory presets, picker in `View ▸ SEM palette`:

  - **`warm-sepia`** (default — matches the reference image). Background
    is desaturated dark brown (#2a221c → #4a3b30); highlights bone-cream
    (#e6dcc5); single teal accent reserved for the "LIVE SEM FEED" badge
    and the on-canvas reticle.
  - **`cool-mono`** (alternative). Background near-black (#0a0e16);
    highlights bone-white (#e6e0d0); accent teal (#39d4c8). This is the
    existing Catalytic Silence palette extended into 3-D shading.

Both must be colourblind-safe — verified by simulating CVD palettes
via `colorspacious`.

### F5 — performance budget
- **60 × 60 grid**, default settings, sustains **20 FPS** on a 2020
  ThinkPad-class laptop (Intel UHD, no discrete GPU) without batching.
- **120 × 120 grid**, default settings, sustains **20 FPS** on the
  same hardware via Phase-2 numpy vectorisation OR Phase-4 GL
  acceleration if the user opts in.
- The rendering pipeline must never block the engine step loop —
  rendering runs in a worker thread with a single-frame buffer to keep
  the UI responsive even at slow grids.

### F6 — fallback gracefully
If the user has a Pillow version without LANCZOS, or no `scipy` for
fast Gaussian blur, or a Tk too old for high-bit-depth `PhotoImage`,
the renderer must **degrade to the v3.6 viridis path** rather than
crash. Detection is done at startup; a one-time toast informs the
user that SEM mode is unavailable and why.

### F7 — A/B toggle
A `View ▸ SEM mode` checkbox lets the user flip between v3.6 viridis
rendering and v4.0 SEM rendering. Both produce scientifically
equivalent imagery; SEM is just a different rendering path. Default
is **SEM mode on**.

### F8 — export integrity
PNG, GIF, and snapshot exports work identically under SEM mode. A
PNG export under SEM mode produces a frame indistinguishable from
the on-screen view (no "watermarked" or "preview-only" overlays).

---

## 5. Visual requirements

### Composition
- The web client's 3-column layout, also imported into the Tk client
  via the v3.6 wall-label work, is the canonical composition.
- Canvas dominates the centre, 720 × 720 fixed in Tk, fluid in web.
- Left column: stage wall-label · configuration · readout (per v3.6).
- Right column: parameters · stage · export — as tabs in web, as the
  scrollable column in Tk (per v3.6 deferred-L2 rationale).
- Bottom: transport bar (PLAY · STOP · STEP · RESET · RECORD GIF) +
  FPS slider + scrub bar + marginalia ticker.

### Typography
- Display serif (Italiana / Cormorant Garamond) for stage title.
- Italic serif (Crimson Pro / Cormorant italic) for citations.
- Monospace (IBM Plex Mono / JetBrains Mono) for all apparatus marks
  (LIVE SEM FEED, scale-bar, stat readouts).
- All caps tracked microcopy (`P L A T E  I  ·  M M X X V I`) for
  section labels.

### Animation
- The "LIVE SEM FEED" badge has a slow 2.2-s opacity pulse (matches
  the v3.6 status-dot pulse) tied to the playback state.
- The crosshair reticle is static.
- The scale-bar updates only when the grid resizes.
- The marginalia ticker advances on chapter transitions (existing v3.6
  chapter-card mechanism stays).

---

## 6. Technical approach — phased implementation

### Phase 1 — depth-shaded numpy rasteriser (no new dependencies)
Targets F1, F2, F4, F6, F7 on existing hardware.

  1. **New module** `cellauto/renderer_sem.py`. Class
     `SemRenderer` with the same `render(state)` interface
     `FieldRenderer` has so the existing app.py + GUI doesn't
     need to know which renderer is active.
  2. **Inputs**: the rule's existing `render_rgb(state)` output OR a
     new `render_height(state)` method returning a single-channel
     float field; `SemRenderer` prefers the latter when available.
  3. **Shading pipeline** in numpy:
       - Gaussian-blur the height-field at σ = 0.7 to suppress
         single-pixel artefacts.
       - Sobel-filter the smoothed field for ∂H/∂x, ∂H/∂y.
       - Build a normals tensor N = normalise((-∂H/∂x, -∂H/∂y, 1)).
       - Lambertian: I = clip(N · L, 0, 1) with light direction
         L = normalise((0.4, 0.3, 0.85)).
       - Ambient: I += 0.2.
       - Specular: add (N · H)^32 with H = halfway-vector for a
         small highlight.
       - Ambient occlusion: subtract α * laplacian(H) clipped to
         non-negative to darken creases.
       - Multi-octave Perlin / value noise overlay at 6 % opacity.
       - Tone-mapped through a 256-entry warm-sepia (or cool-mono)
         LUT.
       - LANCZOS upscale from grid resolution to 720×720.
       - Composited with the stage's sprite library (F3) via PIL
         alpha-compositing.
       - Vignette pass and crosshair / scale-bar overlay (F2).
  4. **Performance** target verified by `tools/bench_sem_renderer.py`:
     20 FPS @ 60×60 grid on CPU.

### Phase 2 — sprite library
Targets F3 across all 12 stages.

  1. Generate the sprite library once via PIL + procedural shapes
     (or via the whipgen MCP for the hero forms). Save to
     `cellauto/assets/sprites/<stage>/<form>.png`.
  2. `SemRenderer` lazy-loads sprites; tints them to the current
     palette via PIL `ImageEnhance.Color` + a colour-multiply.
  3. Spatial placement comes from the simulation state (which we
     already track per-stage).
  4. Add `tests/test_sem_renderer.py` pinning that (a) every stage
     produces a non-trivial image, (b) zeroing the sim field
     produces a near-uniform background, (c) the SEM and viridis
     renderers produce the same step count.

### Phase 3 — full stage catalogue
Tune the sprite library + height-field interpretation per stage
until every one is recognisably "its own kind of microscopy"
(crystal mineral surfaces for Stage IV, liquid droplets for Stage IX,
lipid bilayer interferograms for Stages III + X, etc.).

### Phase 4 — optional GPU acceleration
Targets F5 at higher grid sizes.

  1. Add an optional `moderngl` extra (`pip install cellauto[gpu]`).
  2. Re-implement the Phase-1 shading pipeline as a single GLSL
     fragment shader.
  3. The renderer auto-selects GPU if `moderngl` is importable AND
     the user hasn't opted out via `View ▸ SEM mode ▸ Force CPU`.
  4. Maintains exact pixel parity (golden-image regression test) so
     screenshot tests don't break.

### Phase 5 — stretch — AI image-to-image refinement
Optional, opt-in, never required.

  1. Add a `tools/sem_refine.py` script that takes a CPU/GPU SEM
     render and runs it through a fine-tuned image-to-image diffusion
     model with the prompt "scanning electron micrograph, abiotic
     chemistry, monochrome, depth-shaded" at strength 0.35.
  2. Available via `File ▸ Export refined PNG…` for hero shots only
     (too slow for live playback).
  3. Documented as a research feature; not part of the default UX.

---

## 7. Phased roadmap

| Cycle | Deliverable | Acceptance |
|---|---|---|
| **v4.0.0** | Phase 1 — `SemRenderer` shipped, `View ▸ SEM mode` toggle, palette picker, all 12 stages render in depth-shaded sepia | 20 FPS @ 60×60 CPU, all four CI gates green, screenshot regression on Stage 1 demo |
| **v4.0.1** | Phase 2 — sprite library for stages 0, 1, 3 | Side-by-side comparison: each of those three stages reads as a microscope view, not a screenshot |
| **v4.1** | Phase 3 — sprite libraries for the remaining nine stages | Full 12-stage SEM gallery committed to `docs/generated/sem_<stage>.png` |
| **v4.2** | Phase 4 — optional `moderngl` GPU path | 20 FPS @ 240×240 grid on GPU; CPU fallback unchanged |
| **v4.3** | Phase 5 — opt-in AI refinement | One Stage 1 hero shot exported at fine-tuned diffusion quality |

---

## 8. Out-of-scope creep guard

These have come up in conversation and are deliberately NOT v4.0 work:

- **Replacing Tkinter** with PyQt or a web-only client. The existing Tk
  app is shipped, tested, and accessible; the SEM renderer is a backend
  swap, not a UI rewrite.
- **Voxel-grid 3-D simulation.** The chemistry stays 2-D; the rendering
  is 2.5-D (height-mapped) for cost reasons. A volumetric upgrade is
  a v5.0 conversation.
- **Mandatory GPU.** No user gets locked out because they're on a
  laptop without a discrete graphics card.

---

## 9. Acceptance criteria for v4.0.0

1. `cellauto gui --rule abiogenesis-pipeline` shows the canonical 5-
   stage pipeline running in SEM mode by default.
2. `View ▸ SEM mode` toggles between viridis (legacy) and SEM rendering;
   both paths produce the same step count on the same seed.
3. The toggle persists across restarts via the existing config file.
4. Stage 1 (Gray-Scott) under SEM mode produces an image where:
     - the background reads as a textured granular substrate,
     - the self-replicating spots read as bone-coloured spheres with
       directional shading and shadow,
     - a crosshair reticle and "LIVE SEM FEED · Stage 1" badge are
       overlaid.
5. The four CI gates (ruff, ruff-format, mypy, pytest) stay green.
6. Test count grows by at least 8 (4 SEM renderer pins + 4 palette /
   fallback pins).
7. `docs/generated/sem_<stage>.png` exists for at least Stage 1, the
   canonical demo. Generated by `tools/render_aaa_visuals.py` rerun
   under SEM mode.
8. `CHANGELOG.md` and `README.md` carry the v4.0 entry with a
   side-by-side "before / after" comparison image.

---

## 10. Open questions

These are flagged for resolution during v4.0 design:

- **Sprite library generation:** procedurally with PIL, or via the
  whipgen MCP, or via a static-asset pack downloaded on first launch?
  The MCP route gives photographic quality but adds a network
  dependency at first-render; the PIL route is deterministic but
  shallower. Likely answer: PIL for v4.0.0, MCP-generated as an
  upgrade in v4.0.1.
- **Height-map source per stage:** should every stage expose a new
  `render_height(state)` method (cleaner, more work), or should the
  renderer derive height from the existing `render_rgb` luminance
  (less clean, no rule changes needed)? Likely answer: start with
  luminance derivation; allow rules to override with `render_height`
  for finer control.
- **Animation cadence under SEM mode:** the CPU shading pipeline at
  60×60 may not sustain 20 FPS on the lowest-end target hardware. If
  it can't, do we drop to 12 FPS, or do we keep 20 FPS by skipping
  shading every other frame? Likely answer: a `View ▸ SEM mode ▸
  Reduced quality` checkbox that drops the shading pipeline to 1/3
  of its work (single-octave noise, smaller Gaussian sigma).
- **Web client coherence:** does the web client get an HTML5 Canvas
  shader port of the same pipeline, or does it stay viridis until the
  Python server can ship rendered SEM frames at frame-buffer rate?
  Likely answer: the server renders SEM frames and streams them
  exactly as it currently does for viridis; no changes needed on
  the client.

---

## Appendix A — relationship to prior work

- **v3.0–v3.3:** built the simulation core (12 stages, real dynamics).
- **v3.4:** AAA visual identity for *static* assets (Genesis poster,
  Twelve Tableaux, stage plates).
- **v3.5:** honest-gap closure for the simulation correctness
  (Eigen-Schuster ODE, Helfrich curvature, MJ landscape, pathway-graph
  LUCA, pipeline coupling).
- **v3.6:** parity between the Tk client and the Flask web client on
  UX qualities (wall-label, debounced sliders, batched stepping,
  toast notifications, pulse animations, reduced-motion mode).
- **v4.0 (THIS PRD):** SEM-grade *live* rendering — the visual identity
  the static v3.4 assets earned, applied to every frame the engine
  produces.

The arc: real science (v3.0–v3.3) → real visual identity (v3.4) →
real coupled science (v3.5) → real UX parity (v3.6) → real
**rendered** science (v4.0).
