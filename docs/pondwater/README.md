# Pond Water Analyzer

A dark-field microscope for a drop of virtual pond water. Draw a sample, watch
the microorganisms drift, then **click any organism to dive into it** — the
camera flies in and keeps zooming, revealing internal organs one scale-tier at
a time until you reach organ level. Everything is grown procedurally in
Three.js; no meshes are loaded, so every creature is inspectable at any
magnification.

Live: `https://rizzleroc.github.io/CellAutomata/pondwater/`

## The two registers

- **The drop** — a field of life at log-compressed relative size so a 2 µm
  bacterium and a 1.5 mm water flea are both findable at once. Drag to orbit,
  scroll to zoom the whole sample, click an organism to focus it.
- **The dive** — a focused specimen. Keep scrolling to magnify; as the field of
  view narrows, each organ's callout label fades in as you reach its scale, with
  a leader line to the structure in the body. **◈ Surface** zooms back out.

Magnification is honest to real size: framed, a *Daphnia* reads a few hundred ×
and a bacterium many thousands ×, derived from the true field-of-view width in
microns (`mag = 1,000,000 / field-µm`).

## The roster (floor to ceiling of the microscopic food web)

| Organism | Taxon | ~size | Anatomy modelled |
|---|---|---|---|
| Bacillus | *Bacillus* sp. | 2.4 µm | cell wall, nucleoid (DNA), ribosomes, rotary flagellum |
| Paramecium | *P. caudatum* | 130 µm | pellicle, cilia coat, oral groove/gullet, macro/micronucleus, contractile & food vacuoles |
| Rotifer | *Philodina* sp. | 320 µm | corona (ciliated wheels), mastax & trophi, stomach, intestine, ovary/eggs, foot & toes |
| Tardigrade | *Hypsibius* sp. | 420 µm | 4 segments, 8 clawed legs, stylets & sucking pharynx, midgut, ovary |
| Nematode | *Rhabditis* sp. | 620 µm | undulating body, pharynx & pumping bulb, nerve ring, intestine, gonad |
| Daphnia | *D. pulex* | 1.5 mm | transparent carapace, beating heart, compound eye, gut, brood pouch, rowing antennae |

## Architecture

Zero-build ES modules; Three.js loaded via a CDN importmap (no bundler).

- `scene.js` — `createScope()`: the dark-field wet-mount (ACES tone-mapping,
  `RoomEnvironment` IBL, `UnrealBloomPass`, exponential fog, drifting marine-snow
  particulate layers).
- `organisms/lib.js` — the shared anatomy grammar: translucent `cuticle()` and
  wet `organ()` materials, `tubeBody()` splines, `ciliaRing()`/`ciliaCoat()`
  beating fields, and the `registerOrgan()` registry the zoom engine reads.
- `organisms/*.js` — one procedural builder per organism. Each exports `meta`
  and a `build()` returning a `THREE.Group` whose `userData` carries the
  `anim` contract and the `organs` list (with per-organ `revealFrac`).
- `organisms/index.js` — the `ROSTER`, ordered by real size.
- `main.js` — orchestration: sample spawning + drift, click-to-focus picking,
  the fly-to/dive camera, the magnification model, and the organ-callout plate.

## Tests

```bash
node docs/pondwater/tests/smoke.mjs                       # zero-dep structural gate
npm i three@0.162.0 --no-save && \
  node docs/pondwater/tests/life.mjs                      # each organism builds, has organs, visibly moves
```

`life.mjs` asserts the *biology*, not just that it parses: every organism must
assemble from ≥3 named parts, register ≥3 organs spanning reveal tiers (a
gross-body organ near 0, a fine organ near 1), and **visibly move** over 90
running frames while going still when paused.
