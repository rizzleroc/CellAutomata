# Web sandbox · asset spec for whipgen

Assets needed to elevate the `cellauto` web sandbox from "well-built app"
to "world-class". Style is locked to the project's **Catalytic Silence**
design philosophy — see `docs/design/catalytic-silence.md`. Every asset
should read as if it were part of a museum-quality scientific monograph,
not a SaaS dashboard.

**Universal style notes** (apply to every prompt unless stated):

- Palette: obsidian ground `#05070b`, warm bone `#ece6d6`, desaturated
  teal hairlines `#1f4f4c`, accent teal `#5ee0d4`, counterpoint magenta
  `#e26ab9` used sparingly.
- No flat illustrations, no gradients-as-decoration, no glassmorphism.
  Think hand-engraved scientific plates, Diderot's *Encyclopédie*,
  Audubon, Ernst Haeckel's *Kunstformen der Natur*, vintage MIT lab
  diagrams, Stewart Brand's *Whole Earth Catalog* line art.
- Composition values restraint over decoration. A single specimen
  against generous void; no crowding.
- Where text appears in an asset, use Cormorant Garamond italic or
  IBM Plex Mono — never sans.

Deliverables organised by priority. Top tier first.

---

## 1 · Per-stage scientific etchings  ⭐ HIGHEST IMPACT

A tiny ink-etched illustration for each of the 12 pipeline stages,
displayed inside the wall-label beside the canvas. Replaces "no
illustration" with a museum-card botanical-plate feel.

- **Format:** SVG (preferred) or transparent PNG @ 256×256 logical px
  (delivered @ 1024×1024 for retina).
- **Style:** monochrome ink-etched line art on transparent background,
  ~1px hairline weight at 256px, slight stipple shading allowed, no
  fills. Think Audubon plate cropped tight on a single specimen.
- **Mood:** scientifically literal but slightly archaic — like an
  18th-century naturalist's specimen card.
- **Placement:** rendered in the wall-label below the stage title at
  ~120×120 display size, opacity 0.85, color-matched to `--text-mid`
  (`#a8a59c`).

| Slug | Concept | Etching prompt |
|---|---|---|
| `stage0-soup.svg` | Primordial soup, Oparin–Haldane | "Miller-Urey spark-discharge flask, glass apparatus with two bulbs and a coil of tubing, faint electrical arc between electrodes, 1953 laboratory drawing style, monochrome ink etching, transparent background" |
| `stage1-grayscott.svg` | Gray-Scott reaction-diffusion | "Cluster of self-replicating Turing spots at the moment of division, six concentric ringed cells in mid-fission, scientific plate, monochrome ink hatching, transparent background" |
| `stage2-raf.svg` | Kauffman autocatalytic set | "Hand-drawn reaction-network diagram: 8 circular molecule nodes connected by directed arrows forming a closed catalytic loop, mathematical-monograph style, monochrome line art, transparent background" |
| `stage3-vesicles.svg` | Lipid vesicle | "Cross-section of a single lipid bilayer vesicle, double-walled circle with radial amphiphile head-and-tail glyphs marking the membrane, technical biology textbook etching, monochrome ink, transparent background" |
| `stage4-selection.svg` | Protocell selection | "Single protocell undergoing division, two daughter cells emerging from a parent membrane, with a tiny inner genome sketched as a knotted ribbon, naturalist plate style, monochrome etching, transparent background" |
| `stage5-vents.svg` | Alkaline hydrothermal vent | "Cross-section of a serpentine vent chimney rising from the ocean floor, mineral lattice in the wall, ascending bubbles, geological-survey diagram, monochrome etching, transparent background" |
| `stage6-minerals.svg` | Mineral-surface catalysis (montmorillonite) | "Montmorillonite clay lattice with monomers adsorbed on the surface forming a chain, crystallographic plate, monochrome line art, transparent background" |
| `stage7-chirality.svg` | Homochirality (Frank/Soai) | "Two mirror-image molecules L and R facing each other, one dominant and bright, the other faint and receding, asymmetric autocatalysis chemistry plate, monochrome ink, transparent background" |
| `stage8-rna.svg` | RNA world | "Single self-replicating RNA strand mid-template-copy, two complementary strands annealing, with the four bases A/U/C/G as small glyphs, biochemistry monograph etching, monochrome, transparent background" |
| `stage9-code.svg` | Genetic code emergence | "Codon table sketched as a 4×4×4 cube unfolding, with one tRNA molecule rendered in detail beside it, biochemistry plate, monochrome ink, transparent background" |
| `stage10-coacervate.svg` | Coacervate droplets | "Three coacervate droplets in a liquid-liquid phase separation, varying sizes, with a faint Ostwald-ripening arrow between two of them, physical chemistry plate, monochrome etching, transparent background" |
| `stage11-luca.svg` | LUCA (Last Universal Common Ancestor) | "A single ancestral cell at the root of a sparse phylogenetic tree branching upward into three domains, evolutionary biology textbook plate, monochrome ink, transparent background" |

Plus a **fallback for non-pipeline rules:**

| Slug | Concept | Prompt |
|---|---|---|
| `rule-conway.svg` | Conway's Life | "A small Game-of-Life glider pattern (5 cells in classic glider shape), bold and crisp at low resolution, with a tiny annotation arrow showing direction of travel, recreational mathematics plate, monochrome, transparent background" |
| `rule-wolfram1d.svg` | Elementary cellular automaton | "A Sierpiński-triangle-like pattern generated by a 1D Wolfram automaton, ten rows of small filled and empty cells in a triangular composition, mathematical plate, monochrome, transparent background" |
| `rule-natural-selection.svg` | Generic specimen | "A simple Petri dish viewed from above with three cells inside, scientific plate, monochrome ink, transparent background" |

---

## 2 · Brand wordmark  ⭐ HIGH IMPACT

Replace the current text-rendered "cellauto" with a properly hand-set
wordmark.

- **Format:** SVG, viewBox `0 0 320 80`, currentColor (so we can recolor).
- **Style:** Cormorant Garamond Medium (500), set wide with subtle
  optical letter-spacing, lowercase, with a single tiny glyph after
  the "o" — a 7×7 px solid teal dot (the brand-mark) integrated as
  punctuation.
- **Tagline below (separate file `cellauto-tagline.svg`):** in IBM
  Plex Mono 10px, tracked 0.32em, uppercase — "A LIVE OBSERVATION
  PLATE · MMXXVI" — bone-white on transparent.

Deliver three weights: `cellauto-light.svg`, `cellauto-default.svg`,
`cellauto-bold.svg`.

---

## 3 · Action-button icon set  ⭐ HIGH IMPACT

Replace the Unicode `↓ ↑ ▶ ⏸ ◀ ▶ ✕ +` glyphs with a hand-tuned
hairline SVG icon set. Match Lucide proportions but with a slight
museum-instrument flourish.

- **Format:** SVG, 16×16 viewBox, stroke `currentColor`, stroke-width
  `1.25`, stroke-linecap `round`, stroke-linejoin `round`, no fill.
- **Naming:** `icon-<name>.svg`.

Required icons:
- `play` — right-pointing equilateral triangle, inset 2px
- `pause` — two vertical bars
- `step` — single right-pointing arrow with a bar (like skip-forward)
- `reset` — circular arrow (counter-clockwise)
- `download` — downward arrow into a tray (no fills)
- `upload` — upward arrow out of a tray
- `image` — frame with mountain glyph (the universal image icon)
- `film` — film strip with sprocket holes (for GIF export)
- `chevron-left`, `chevron-right` — for tutorial nav (more refined
  than ◀ ▶)
- `chevron-down` — for select dropdowns
- `plus` — for the tutorial expand button
- `close` — X mark for the dialog
- `github` — the GitHub octocat mark, hairline version

---

## 4 · Vitrine corner ornaments  ⭐ MEDIUM IMPACT

The canvas hero currently uses four plain L-shaped teal hairlines as
"vitrine corners". Replace with hand-drawn brass-instrument corner
brackets that suggest a 19th-century specimen case.

- **Format:** SVG, 32×32 viewBox each, 4 orientations (tl, tr, bl, br).
- **Style:** thin hairline (1px at 32px) tracing an ornate L with a
  small inward flourish, like the corner cap of a brass museum
  display frame. Color `currentColor`.
- **Deliver:** `vitrine-corner-tl.svg`, `-tr.svg`, `-bl.svg`, `-br.svg`,
  OR a single `vitrine-corners.svg` with all four in one viewBox.

---

## 5 · Atmosphere & texture layers  ⭐ MEDIUM IMPACT

Replace the current SVG-noise hack with proper textures.

- `texture-grain.png` — 320×320 seamless film grain tile, slate-warm
  cast (`#1a1814` to `#0a0d14`), 6–8% noise depth, monochrome. Used
  at body-level `background-blend-mode: overlay` at 0.04 opacity.
- `texture-vellum.png` — 640×640 seamless aged-vellum paper texture,
  bone-warm (`#e6e0d0` base), very faint horizontal fibres and a
  whisper of foxing. Used as a desaturated/inverted overlay at very
  low opacity for the wall-label region.
- `bg-vignette.png` — 1920×1080 radial vignette, transparent center,
  obsidian edges, soft falloff. Used as a fixed background layer.

---

## 6 · Open Graph + favicon set  ⭐ MEDIUM IMPACT

For social sharing and browser tab identity.

- `og-image.png` — 1200×630. Hero composition: large Gray-Scott
  "mitosis" specimen on obsidian, "cellauto" wordmark at top-left in
  Cormorant Garamond serif, italic tagline below ("a live observation
  of the coalescence of chemistry into pattern"), "PLATE · MMXXVI"
  tracked uppercase in mono at bottom-right. Reference: a single
  museum plate page bled to full bleed.
- `favicon.svg` — 32×32 vector. Just the brand-mark dot inside a
  thin square frame.
- `favicon.ico` — 16×16 + 32×32 fallback.
- `apple-touch-icon.png` — 180×180. Same composition as favicon.svg
  rasterised, on obsidian.
- `pwa-192.png` and `pwa-512.png` — PWA manifest icons, same look.

---

## 7 · Loading / empty states  ⭐ LOW IMPACT

- `spinner.svg` — animated SVG (CSS animation OK) showing a thin teal
  ring with one segment highlighted, rotating at 1.2s/cycle. 24×24.
- `empty-plate.svg` — a small empty Petri dish ink-etching, used in
  the "No live-adjustable parameters" empty state. 64×64.

---

## 8 · Decorative typographic ornaments  ⭐ LOW IMPACT

- `divider-flourish.svg` — a thin horizontal hairline with a tiny
  centered diamond ornament. Used between sections of the wall-label
  instead of plain `<hr>`. 240×8 viewBox.
- `dropcap-template.svg` — a stylized capital letter frame the JS can
  populate with the first letter of "About". Cormorant Garamond, 64px,
  bone with a faint teal inner stroke.

---

## Where assets should land

All assets go in `cellauto/web/static/img/` (create that directory). I
will:

1. Reference them from `index.html` (e.g. `<link rel="icon" href="/static/img/favicon.svg">`)
   and inline SVGs where appropriate (icons especially).
2. Wire per-stage etchings into `applyStageInfo()` in `app.js`, keyed
   by stage slug.
3. Reference textures from `style.css` via `background-image`.

## Delivery checklist for whipgen

- [ ] 12 stage etchings (`stage0-soup.svg` … `stage11-luca.svg`)
- [ ] 3 non-pipeline rule etchings (`rule-conway.svg`, `rule-wolfram1d.svg`, `rule-natural-selection.svg`)
- [ ] Brand wordmark (3 weights)
- [ ] 14 action-button icons
- [ ] Vitrine corner ornaments (4 files or 1 combined)
- [ ] 3 texture layers (grain / vellum / vignette)
- [ ] Open Graph image (1200×630)
- [ ] Favicon SVG + ICO + apple-touch + PWA 192 + 512
- [ ] Spinner SVG
- [ ] Empty-plate SVG
- [ ] Divider flourish SVG + dropcap template SVG

If anything is ambiguous, prefer to err toward **more restraint, more
breath, less ornament**. Catalytic Silence treats every line as
information — there should be nothing decorative in the literal sense
of the word.
