# cellauto — Social Media Content Plan

> Operating doc for the recurring social-media loop. Each loop cycle reads this
> file, picks the next un-posted topic from the **Topic Backlog**, writes a
> multi-platform post under `posts/`, commits/pushes, and surfaces it in chat.

## The project in one line

**cellauto** — an open-source, scientifically-grounded cellular sandbox that
walks the **chemistry-to-life transition** (abiogenesis) across a 12-stage
pipeline, from primordial soup to LUCA. Every constant traces to a published
measurement. v3.6.0. MIT. Python + Tk + a static-HTML web demo.

Repo: https://github.com/rizzleroc/CellAutomata

## Positioning / the hook

The central, repeatable hook: **"A four-parameter PDE is enough to make a
'cell' divide."** The origin of life reframed not as a miracle but as emergent
behaviour you can run on your laptop — backed by real literature (Miller-Urey,
Turing/Gray-Scott, Kauffman, Eigen-Schuster, Lane-Martin, Weiss et al.).

Secondary angle: **radical honesty.** The project publicly audits its own
claims (see the v3.5 "honest-gap-closure" release) — rare and trust-building.

## Audiences & platform voice

| Platform | Audience | Voice | Length |
|---|---|---|---|
| **X / Twitter** | sci-curious devs, #scicomm, ALife crowd | punchy, visual-first, 1 hook + thread | ≤280 chars/tweet, 2–4 tweet thread |
| **LinkedIn** | engineering leaders, researchers, recruiters | professional, "science × software" showcase | 1–3 short paragraphs |
| **Reddit** | r/cellular_automata, r/abiogenesis, r/Python, r/alife | technical, community-first, citations, *no marketing voice* | title + body, link last |

## Visual assets (attach where relevant)

- `docs/hero.png` — Gray-Scott self-replicating "protocell" spots (the hero)
- `docs/pipeline.png` — five stages left→right
- `docs/genesis.png` — 12-stage magnum-opus museum poster
- `docs/prima-materia.png` — Plate XII museum composition
- `docs/web/` — live in-browser Stage 1 demo
- GIF export via `cellauto export --rule abiogenesis-stage1-grayscott --rule-config preset=mitosis ...`

## Hashtags / tags

- **X:** #ArtificialLife #ALife #abiogenesis #originoflife #cellularautomata #Python #scicomm #openscience #ReactionDiffusion
- **LinkedIn:** #ArtificialLife #ComputationalBiology #OpenSource #Python #ScientificComputing #OriginOfLife
- **Reddit:** no hashtags; pick the right subreddit and lead with substance.

## Rules of the loop (operating procedure)

1. Read this file and list existing files in `posts/`.
2. The **next topic** = backlog item at index `N` where `N` = count of existing
   `post-*.md` files (zero-based against the numbered list below).
3. Write `posts/post-NNN-<slug>.md` containing all three platform variants,
   the suggested asset, and the hashtag set. Keep facts accurate — only claim
   what the README/CHANGELOG support.
4. Commit (`social: post NNN — <topic>`), push to `claude/cool-shannon-Sa9Tu`.
5. Surface the post text in chat.
6. When the backlog is exhausted, generate a **fresh angle** (deeper dive on a
   stage, a "behind the science" thread, a milestone/changelog highlight, a
   community question, a reply-bait poll) and keep numbering upward.
7. Never repeat a topic already covered in `posts/`.

## Topic Backlog (numbered, zero-based)

0. **Launch / intro** — "A 4-parameter PDE makes cells divide." What cellauto is.
1. **Hero result** — Stage 1 Gray-Scott self-replicating spots (Pearson 1993 "spots", F=0.035 k=0.065).
2. **Stage 0 — primordial soup** — initial mix weighted by Miller-Urey (1953) measured yields.
3. **Hydrothermal vent** — Lane-Martin chemiosmosis; live PMF (mV) + ΔG via Nernst; Wood-Ljungdahl CO₂ fixation.
4. **Stage 2 — RAF autocatalytic sets** — Kauffman + the correct Hordijk-Steel layered closure.
5. **Homochirality** — Frank (1953) chiral symmetry breaking; teal/magenta domains; Soai reaction.
6. **RNA world** — spatial Eigen quasispecies; error catastrophe live at ε_c = ln(σ)/L.
7. **Genetic-code coevolution** — Vetsigian-Woese-Goldenfeld; codon→amino-acid table converges under selection.
8. **Coacervates** — Cahn-Hilliard liquid-liquid phase separation (Oparin); droplets coarsen.
9. **Mineral-surface catalysis** — Na-montmorillonite clay mask; Ferris-style polymerisation of ImpA.
10. **Stage 3 — vesicles** — lipid self-assembly above the measured CMC; Helfrich bending elasticity.
11. **Stage 4 — protocell selection** — real Eigen-Schuster hypercycle ODE inside each protocell.
12. **LUCA distillation** — Weiss et al. (2016) comparative-genomics parsimony, 70% prevalence threshold.
13. **The coupled pipeline** — v3.5 made every stage hand its output field forward: one continuous narrative, not 12 demos on a timer.
14. **Museum plates** — Prima Materia & Genesis; the "Catalytic Silence" design philosophy.
15. **Try it in your browser** — static-HTML Stage 1 demo, F/k sliders, Pearson preset chips, viridis colormap.
16. **Radical honesty** — the v3.5 "honest-gap-closure" release: a project that publicly audits its own claims.
17. **Reproducibility** — deterministic from seed, bit-for-bit across save/load (RNG state serialized).
18. **The science spine** — every constant traces to a published measurement; see docs/science.md.
19. **Reference automata** — Conway's Life + Wolfram rule 110 (Turing-complete) shipped for comparison.
20. **Accessibility & UX** — colourblind-safe Wong palette, reduced-motion toggle (WCAG), full keyboard nav.
21. **Contribute / open source** — MIT, 141 tests, CI green; how to get involved.
