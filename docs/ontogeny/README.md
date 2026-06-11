# cellauto · ontogeny — the origin of a life

A real, controllable simulation of how an **individual** life begins: sperm + egg
→ zygote → cleavage → the embryo-splitting that makes identical multiples →
through the developmental stages → birth → the stages of life. It is the second
origin story (after the lab's abiogenesis arc): not how life began on Earth, but
how *you* began.

No build step, **zero dependencies**, no framework — three small ES modules and
a canvas. Opens from `file://` or any static server.

```
docs/ontogeny/
├── index.html      the vitrine + the three panels (conditions · specimen · diagnosis)
├── styles.css      Catalytic Silence (reuses web8's self-hosted fonts)
├── sim.js          the conception ENGINE — seedable, stochastic, browser+test shared
├── render.js       canvas drawing: gametes → cleavage → split → membranes → fetuses
├── app.js          controller: conditions, parameters, the developmental clock, diagnosis
└── tests/
    ├── ontogeny.mjs  engine contract (the science) — zero-dep
    └── smoke.mjs     page wiring + module parse — zero-dep
```

## What it actually simulates (honest scope — see [`../PRD_ONTOGENY.md`](../PRD_ONTOGENY.md))

**REAL (mechanistic, in `sim.js`):** ovulation → fertilisation with the zona
polyspermy block → the per-day **splitting hazard** whose *timing* sets the shared
membranes. This is the part that *creates* the multiples, and it is genuinely
stochastic and **calibrated to real data**: run it across many seeds and the
monozygotic chorionicity distribution emerges at the real frequencies
(~27% DCDA, ~68% MCDA, ~4% MCMA, <1% conjoined), with spontaneous MZ twins at
~1/270 (real ≈ 1/250). It is not scripted. Triploidy arises from both dispermy
(zona-block failure) and digyny (a retained polar body). Dating is
post-fertilisation days; "SEM" is the lab's depth-shade visual style, not a
literal electron micrograph of a living embryo.

- **Split day → membranes (the real twin rule):** days 1–3 → **DCDA**, 4–8 →
  **MCDA**, 8–13 → **MCMA**, 13+ → **conjoined**.
- **Dizygotic** from polyovulation (≥2 eggs); **higher-order** as combinations.
- **Conditions:** triploidy (polyspermy), trisomy (non-disjunction), chimerism
  (zygote fusion), and the vanishing twin.

**Staged (a guided clock):** implantation → gastrulation → organogenesis (the
heart beats ~day 22) → fetal → birth → the postnatal stages of life, keyed to the
real Carnegie-stage timeline. A full morphogenesis sim is research-grade and out
of scope for a browser; this is honestly a developmental *timeline*, not a
mechanistic morphogenesis.

## Controls

- **Conditions** — one click each: *Singleton · Identical DCDA / MCDA / MCMA ·
  Conjoined · Fraternal · Triplets (trizygotic / 2+1) · Quadruplets · Quintuplets
  · Triploidy · Trisomy 21 · Chimerism · Vanishing twin.* The deterministic ones
  are guaranteed; the open ones bias the dice.
- **Parameters** — eggs ovulated, fertility, zona block, split hazard, split day,
  non-disjunction, ART. Move any knob to go *custom* and re-roll the seed.
- **Transport** — Play the developmental clock, Step, Reset, and scrub the
  timeline from the gametes to the stages of life.

## Tests

```bash
node docs/ontogeny/tests/ontogeny.mjs   # the science (split-day table, presets, Hellin, triploidy)
node docs/ontogeny/tests/smoke.mjs      # module parse + page wiring (no browser)
```

Both run in CI (`.github/workflows/pages.yml`).
