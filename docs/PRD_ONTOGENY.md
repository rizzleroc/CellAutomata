# PRD — Ontogeny: From Gamete to Life

**One-line vision.** Extend the lab from *abiogenesis* (how life began on Earth)
to *ontogeny* (how an individual human life begins): a real, controllable
simulation of **sperm + egg → zygote → cleavage → blastocyst → implantation →
the developmental stages → birth → the stages of life**, with the actual
biological **conditions that produce singletons, identical/fraternal twins,
triplets, quintuplets, and the rarer outcomes** (conjoined, vanishing twin,
triploidy, chimerism, aneuploidy).

Status: **PROPOSED / documented capability.** This PRD specifies the feature so
it can be built; nothing here ships yet. It reuses the web7 lab architecture
(the Parameters panel, the **Regime** preset picker, `controlConsequence`
tooltips, the photoreal cell renderer) added in PR #50.

---

## 1. Why — the narrative bridge

The current lab tells one origin story: dead chemistry → the first cell → LUCA →
stromatolites (Stage 0 → XI → capstone, ~4.0–3.5 Ga). It stops at *life in
general*. This arc tells the **second origin story every person actually lived
through**: a single fertilised cell becoming *you*. It is the same theme one
scale up — self-organisation, division, differentiation, selection — and it ends
where the viewer is sitting. "The origin of our life," literally.

It is also where the project's existing engine already fits: cleavage **is** a
dividing-cell cellular automaton, and the photoreal `life` colony renderer
already draws dividing cells.

---

## 2. Scientific grounding (this must stay true to life)

### 2.1 The developmental timeline (real, citeable)

Times are **post-fertilisation** (add ~2 weeks for clinical "gestational age").
Embryonic morphology follows the **Carnegie stages (1–23, weeks 1–8)**.

| Phase | When | What actually happens | Sim treatment |
|---|---|---|---|
| **Gametes** | — | Oocyte arrested in meiosis II (zona pellucida + corona radiata); ~10⁸ sperm, only ~hundreds reach the ampulla; capacitation + acrosome reaction | **Mechanistic** (agents) |
| **Fertilisation** | Day 0, ampulla | Sperm penetration → cortical reaction (zona block to polyspermy) → meiosis II completes → pronuclei fuse (syngamy) → **zygote**, 1 cell, 46 chromosomes | **Mechanistic** |
| **Cleavage** | Days 1–3 | Mitosis without growth: 2→4→8 cells; compaction → **morula** (~16 cells) | **Mechanistic** (CA) |
| **Blastulation** | Days 4–5 | Blastocoel forms; differentiation into **inner cell mass** (embryo) vs **trophoblast** (placenta); hatches from zona ~Day 5–6 | **Mechanistic** |
| **Implantation** | Days 6–10 | Trophoblast invades endometrium; bilaminar disc; amnion, yolk sac, chorion | **Staged** |
| **Gastrulation** | Week 3 | Primitive streak → three germ layers (ecto/meso/endoderm); notochord — the body plan | **Staged** |
| **Organogenesis** | Weeks 3–8 | Neural tube, somites, **heart beats (~Day 22)**, limb buds, organ primordia; end of wk 8 = all major organs → **fetus** | **Staged** |
| **Fetal** | Wk 9 – birth | Growth + maturation; viability ~wk 24; surfactant | **Staged** |
| **Birth** | ~38 wk | Parturition | **Event** |
| **Stages of life** | postnatal | neonate → infant → child → adolescent → adult → senescence | **Timeline** |

### 2.2 Multiple births — the actual conditions

This is the heart of the request. Two root mechanisms, then combinations.

**Monozygotic (MZ, "identical")** — *one* egg + *one* sperm, then the early
embryo **splits**. The **day it splits sets the shared membranes** (chorionicity
/ amnionicity) — this is a genuinely simulatable hazard process:

| Split day | Type | Placentas / sacs | Share of MZ | Note |
|---|---|---|---|---|
| 1–3 (pre-morula) | **DCDA** | 2 / 2 | ~25–30% | indistinguishable from fraternal by membranes |
| 4–8 (blastocyst) | **MCDA** | 1 / 2 | ~70% | shared placenta → TTTS risk |
| 8–13 (post-amnion) | **MCMA** | 1 / 1 | ~1–5% | cord-entanglement risk |
| 13+ (post-streak) | **conjoined** | 1 / 1 | <1% | incomplete split |

**Dizygotic (DZ, "fraternal")** — **polyovulation**: ≥2 eggs released, each
fertilised by a different sperm. Always DCDA; genetically ordinary siblings.
Raised by elevated FSH, maternal age, genetics, and **ART**.

**Higher-order** (triplets … quintuplets) = combinations:
- Triplets: trizygotic (3 eggs) · dizygotic (one egg splits + one egg) · monozygotic (one egg splits twice).
- Quadruplets/quintuplets: any partition of *N* babies into *zygotes that split*.
- **Spontaneous frequency** follows **Hellin's rule** (twins ≈ 1/89, triplets ≈ 1/89², …); spontaneous quintuplets are ~1 in 5×10⁷. **ART** (ovulation induction, multi-embryo transfer) dominates real higher-order multiples.

**Other conditions to expose** (all real, all "different conditions that create
us"): polyspermy → **triploidy** (zona-block failure; usually non-viable),
**chimerism** (two zygotes fuse — the inverse of MZ split), **aneuploidy** from
meiotic nondisjunction (e.g. **trisomy 21**), **vanishing twin** (one reabsorbed
early), and rarer **sesquizygotic / mirror-image** twins.

---

## 3. What is *actually simulated* (honest scope)

Per the project's REAL / PARTIAL ethic (`ROADMAP.md`), we are explicit about
which parts are mechanistic vs representational. **No overclaiming.**

- **Mechanistic (a genuine stochastic agent/CA simulation):** gamete race +
  fertilisation + the zona polyspermy block + cleavage divisions + the
  **splitting hazard whose timing yields the chorionicity outcome**. This is the
  scientifically load-bearing core — and it is exactly the part that "creates
  twins/triplets/…". It is real, not scripted: run it many times and the
  outcome distribution (singleton vs DCDA/MCDA/MCMA, higher-order frequencies)
  emerges from the parameters.
- **Staged representation (a guided developmental clock, honestly labelled):**
  implantation → gastrulation → organogenesis → fetal → birth. A full
  mechanistic morphogenesis sim is research-grade and out of scope for a
  browser; we advance a developmental clock keyed to **real Carnegie-stage
  milestones** and render the corresponding morphology. Labelled "developmental
  timeline," not "morphogenesis simulation."
- **Timeline (data, not simulation):** the postnatal stages of life — real age
  bands, shown as the closing arc.

---

## 4. Controls (wired to the web7 Parameters panel)

A new rule module (e.g. `docs/web7/experiment/rules/ontogeny.js`) exposing the
standard `params` / `controlConsequence` / `presets` contract `buildParamPanel`
already renders. The knobs *are* "the different conditions":

| Param | Range | Drives |
|---|---|---|
| `oocytes` | 1–6 | eggs ovulated this cycle (the DZ / higher-order root) |
| `spermDensity` | low–high | how many sperm race; affects fertilisation odds |
| `spermMotility` | 0–1 | race speed / reach |
| `fertility` | 0–1 | per-oocyte fertilisation probability |
| `zonaBlock` | 0–1 | polyspermy block efficiency (low → **triploidy**) |
| `splitHazard` | 0–0.05 | per-day probability a zygote splits (**MZ** propensity) |
| `splitDayBias` | 1–14 | *when* splits tend to occur → DCDA/MCDA/MCMA/conjoined |
| `nondisjunction` | 0–0.05 | meiotic error rate → **aneuploidy / trisomy** |
| `art` | enum: natural · ovulation-induction · IVF-transfer-2 · IVF-transfer-3 | shifts oocyte/embryo counts |
| `clock` | 1–60 | developmental timeline speed |

### Regime presets (the requested "conditions", one click each)

`singleton (typical)` · `identical twins — DCDA` · `identical twins — MCDA` ·
`identical twins — MCMA` · `conjoined (late split)` · `fraternal twins (2 eggs)` ·
`triplets — trizygotic` · `triplets — 2+1` · `quadruplets (ART)` ·
`quintuplets (ART)` · `polyspermy → triploidy` · `vanishing twin` ·
`trisomy 21 (nondisjunction)` · `chimerism (zygote fusion)`.

Each preset sets the params so the labelled outcome emerges (deterministic
outcomes are forced; stochastic ones bias the model so the outcome is typical).

---

## 5. Visualisation & UI

A **"Part II — Ontogeny"** plate arc continuing the catalogue (Roman numerals or
a fresh set), each a plate beside its live view:

1. **Gametes** — oocyte + sperm field (microscope apparatus).
2. **Fertilisation** — the race + zona block; readout: ploidy, # zygotes.
3. **Cleavage → Blastocyst** — dividing-cell CA via the existing photoreal cell
   renderer; ICM vs trophoblast colouring.
4. **Implantation & Gastrulation** — staged; germ-layer view.
5. **Organogenesis** — staged Carnegie morphology; "heart beats Day 22" beat.
6. **Fetal growth → Birth** — staged growth + viability marker.
7. **The stages of life** — the postnatal timeline.

**Multiples readout** (the payoff): a live panel showing each conceptus, its
zygosity, and the **membrane diagram** (e.g. "2 babies · monozygotic · MCDA ·
1 placenta / 2 sacs"). New 3D apparatus (microscope, IVF incubator, ultrasound)
to be modelled — flagged as to-build, with the placeholder pedestal as fallback.

---

## 6. Feasibility & honesty summary

| Capability | Verdict |
|---|---|
| Fertilisation + polyspermy block | **REAL** (stochastic agents) |
| Cleavage / morula / blastocyst (ICM vs trophoblast) | **REAL** (cell CA) |
| MZ split-timing → chorionicity; DZ polyovulation; higher-order combinatorics | **REAL** — the core deliverable |
| Triploidy / aneuploidy / chimerism / vanishing twin | **REAL** (as stochastic flags) |
| Gastrulation → organogenesis → fetal | **REPRESENTATIONAL** (Carnegie-keyed timeline) |
| Postnatal stages of life | **DATA TIMELINE** |
| New 3D apparatus models | **TO BUILD** |

---

## 7. Ethical & educational framing

This is a **developmental-biology education** feature: clinical, respectful,
scientifically sourced (Carnegie stages, standard embryology). It is not medical
advice and not a fertility predictor. Sensitive outcomes (non-viable
conditions, conjoined twins, aneuploidy) are presented as the documented
biology of human development, factually and without sensationalism.

---

## 8. Acceptance criteria

1. Over many runs at default natural settings, multiple-birth frequencies track
   Hellin's-rule order of magnitude (twins ≪ singletons; triplets ≪ twins).
2. Setting `splitDayBias` reproduces the **correct chorionicity** per the §2.2
   table (1–3 → DCDA, 4–8 → MCDA, 8–13 → MCMA, 13+ → conjoined).
3. `oocytes ≥ 2` with no split → **dizygotic**, always **DCDA**.
4. Each Regime preset yields its labelled outcome (deterministic) or its typical
   outcome ≥80% of runs (stochastic).
5. Low `zonaBlock` produces triploidy; the conceptus is flagged non-viable.
6. A zero-dep `tests/ontogeny.mjs` gate (mirroring `controls.mjs`) asserts 1–5.

---

## 9. Phased plan

- **P1 — the core the request is really about:** `ontogeny.js` mechanistic
  fertilisation + cleavage + the splitting hazard + the Regime presets +
  the multiples/membrane readout + `tests/ontogeny.mjs`. Ships the "simulate
  twins/triplets/quintuplets and the conditions" capability end-to-end.
- **P2 — the staged arc:** implantation → birth developmental timeline, the
  Part II plates, the stages-of-life closing timeline.
- **P3 — apparatus & polish:** 3D microscope / incubator / ultrasound models,
  SEM/photoreal tuning, curatorial copy.

---

*Sources: standard human embryology (Carnegie stages; Larsen's / Moore's
texts), twin chorionicity-by-split-day, Hellin's rule for multiple-birth
frequency, ART multiple-gestation literature. To be cited inline at
implementation in `docs/science.md`.*
