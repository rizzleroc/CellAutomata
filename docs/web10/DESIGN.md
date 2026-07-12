# Web 10 · "Catalytic Silence — Mark X" — design & change callouts

This is the visual spec for **web10**: the Mark X UI with every change called out,
and the per-level hero art (one image per abiogenesis stage) annotated with its
composition. It's the companion to the live client (`docs/web10/`) and the plan.

**Status:** `[DONE]` shipped · `[BUILD]` to implement · `[OPT]` stretch · `✅` art generated (Gemini/Imagen).

---

## 1 · The Mark X UI — every change called out

![Mark X lab UI](../generated/web10/web10_shell_lab.png)

```
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │ ●  cellauto  ─ an origin-of-life instrument   ⟨MK X⟩①        PL.VII · LAB · cat.   │  HEADER
 ├────────────────────┬───────────────────────────────────────────┬───────────────────┤
 │  STAGE RAIL ③      │   ┌────────────────┐  ┌───────────────────┐│  PARAMETERS ⑥     │
 │ ┌────────────────┐ │   │                │  │   ◜ ● LIVE·SEM ◞  ││  REGIME:  spots ▾ │
 │ │ I   ░░hero░░   │ │   │  3D APPARATUS  │  │   ╭───────────╮   ││  F  ──●─────── .037│
 │ │ II  ░░hero░░ ◀ │ │   │  (per stage)   │  │   │ ▓ micro-  │   ││  k  ─────●──── .060│
 │ │ ...            │ │   │                │  │   │ ▓ graph   │   ││  Du ───●────── .16 │
 │ │ XIII ░░hero░░  │ │   │                │  │   ╰───────────╯   ││  ░ chart ▁▂▃▅▆    │
 │ └────────────────┘ │   └────────────────┘  │   ⟨PRO · 4000²⟩④  ││  [Step] [Reset]   │
 │ ③ card = its stage │      ◖ LAB · SPLIT · LIVE·SEM ◗           ││                   │
 ├────────────────────┴───────────────────────────────────────────┴───────────────────┤
 │  ◀  ●─○─○─○─○─○─◉─○─○─○─○─○─○  ▶  TIMELINE ⑤      seed 1 · 7c3a… · 2026-06 ⑥        │  FOOT (NEW)
 └──────────────────────────────────────────────────────────────────────────────────┘
   ② magenta accent on ⟨MK X⟩ · ⟨PRO⟩ · active node ◉        ⑦ amoeba guide ◍ (lower-left)
```

| # | Change | Where | Status |
|---|--------|-------|--------|
| ① | **"MK X" build tag** | header brand | `[DONE]` |
| ② | **Magenta accent** (`#d77bff`) on tag / pill / active states | shell-wide | `[DONE]` |
| ③ | **Hero-art stage rail** — each card backed by its `generated/web10/stageNN_*.png` (graceful fallback to the solid card when absent) | left rail | `[DONE]` |
| ④ | **Pro · 4000² export pill** → web9 Pro Studio | over the SEM plate | `[DONE]` |
| ⑤ | **13-node timeline scrubber** — ◀/▶ + a node per stage, `◉` = current, click → `loadStageById` | new footer | `[BUILD]` |
| ⑥ | **Provenance strip** — `seed · commit · timestamp` | footer, beside ⑤ | `[BUILD]` |
| ⑦ | **Amoeba guide** (port web8 `guide.js`/`blobgeom.js`) | lower-left | `[OPT]` |
| ⑧ | **Deeper Pro export** — pill POSTs the current stage/params to web9 `/api/render` inline | plate pill | `[OPT]` |

*(The embedded mockup above is the Gemini/Imagen concept render; the live client
matches its structure. The ① ④ shell changes ship in PR #78; ⑤ ⑥ are the next build.)*

---

## 2 · The per-level hero — composition template (Ⓐ–Ⓔ)

Every level's hero shares one composition; only the apparatus, micrograph, and tag
change. Each §3 block lists what fills Ⓐ–Ⓔ for that stage.

```
 ┌───────────────────────────────────────────────────────────┐
 │ Ⓔ obsidian field · teal+magenta · vitrine rim-light        │
 │            ╭─────────────╮          ╭─────────────╮         │
 │            │  Ⓐ 3D       │          │ Ⓑ ◜ SEM ◞   │         │
 │            │  APPARATUS  │          │  (circular  │         │
 │            │  on plinth  │          │  micrograph)│         │
 │            ╰─────────────╯          ╰─────────────╯         │
 │   CATALYTIC SILENCE · <APPARATUS> Ⓓ                        │
 │   System · Reagent · Process  (science caption)            │
 │                                       ⟨ Ⓒ [ROMAN] · NAME ⟩ │
 └───────────────────────────────────────────────────────────┘
```

- **Ⓐ Apparatus** — the stage's instrument on a dark plinth.
- **Ⓑ Circular SEM micrograph inset** — the stage's depth-shaded micrograph motif.
- **Ⓒ Stage tag** — `[ROMAN] · NAME`, corner.
- **Ⓓ Caption** — didone title + one-line science gloss.
- **Ⓔ Styling** — `#07090d` ground, teal `#3fe0d0`, sparing magenta `#d77bff`; sharp/flat, no blur.

---

## 3 · The 13 levels — image + callouts

> **Globals on every stage:** **Speed** (1–60 s⁻¹) + **Palette** (warm-sepia / cool-mono). Each block's **Controls** lists that stage's regime presets + sliders (`range·default`).

### I · Miller–Urey  ✅
![stage00_miller_urey](../generated/web10/stage00_miller_urey.png)
- **Ⓐ** spark-discharge glassware: boiling flask, upper spark chamber w/ electrodes, condenser arch, darkening collection flask · **Ⓑ** organic microspheres coalescing · **Ⓒ** `I · MILLER–UREY` · **Ⓔ** photoreal warm.
- **Controls** — regimes — Miller 1953 · weakly-reducing · volcanic spark-storm. sliders — gas density 120–900·420, spark rate 0.2–4.0·1.2, reducing atm 0.2–1.0·0.85, boil 0.1–1.0·0.6.

### II · Reaction–diffusion  ✅
![II · Reaction–diffusion](../generated/web10/stage01_reaction_diffusion.png)
- **Ⓐ** shallow Petri dish under a brass ring light, concentric Belousov–Zhabotinsky waves · **Ⓑ** labyrinthine reaction-diffusion / Turing maze · **Ⓒ** `II · REACTION–DIFFUSION` · **Ⓔ** warm-sepia.
- **Controls** — regimes — spots·stripes·mitosis·waves·labyrinth. controls — Pearson preset (dropdown), feed F 0–0.09·0.035, kill k 0.03–0.075·0.065. ⚠ #65: Du/Dv/substeps hardcoded.

### III · Autocatalytic sets  ✅
![stage02_raf](../generated/web10/stage02_raf.png)
- **Ⓐ** round-bottom flask on a stir plate; ring of glowing catalyst nodes + cyan edges (reflexive closure) · **Ⓑ** networked catalytic nodes · **Ⓒ** `III · AUTOCATALYTIC SETS` · **Ⓔ** warm-sepia.
- **Controls** — regimes — ignited·starved collapse·subcritical. sliders — catalysis 0–6·3, food 0–1·0.85, decay 0–0.3·0.05, reactions/frame 1–6·2.

### IV · Vesicles  ✅
![stage03_vesicles](../generated/web10/stage03_vesicles.png)
- **Ⓐ** vintage brass microscope; eyepiece disc of drifting teal bilayer vesicles · **Ⓑ** dividing vesicles · **Ⓒ** `IV · VESICLES` · **Ⓔ** warm-sepia.
- **Controls** — regimes — floppy·balanced·stiff spheres. sliders — diffusion 0.05–0.5·0.18, γ 0.5–4·1.6, κ-bend 0.01–0.3·0.1, noise 0–0.02·0.004.

### V · Hydrothermal vent  ✅
![stage04_vent](../generated/web10/stage04_vent.png)
- **Ⓐ** sealed glass reactor column, glowing FeS mineral chimney, pH probe, bakelite mV/ΔG readout · **Ⓑ** porous mineral-chimney pores · **Ⓒ** `V · HYDROTHERMAL VENT` · **Ⓔ** warm-sepia.
- **Controls** — regimes — living vent·no-gradient (control)·vigorous. sliders — diffusion 0.05–0.4·0.2, updraft 0–0.5·0.18, decay 0–0.02·0.004, ΔpH 0–1·0.5, feedstock 0–0.2·0.06.

### VI · Mineral catalysis  ✅
![stage05_minerals](../generated/web10/stage05_minerals.png)
- **Ⓐ** beaker with a layered ochre montmorillonite clay bed, amber RNA-like chains growing up · **Ⓑ** clay platelets + polymer chains · **Ⓒ** `VI · MINERAL CATALYSIS` · **Ⓔ** warm-sepia.
- **Controls** — regimes — surface catalysis·no-catalysis (control)·washed-out. sliders — k_clay 0–0.6·0.25, k_bulk 0–0.3·0.002, feed 0–0.3·0.08, hydrolysis 0–0.05·0.01, clay patches 1–24·9, steps/frame 1–6·2.

### VII · Homochirality  ✅
![stage06_chirality](../generated/web10/stage06_chirality.png)
- **Ⓐ** tinting reaction flask + brass polarimeter, needle swung off-zero · **Ⓑ** chiral spiral microtextures · **Ⓒ** `VII · HOMOCHIRALITY` · **Ⓔ** warm-sepia + magenta cast.
- **Controls** — regimes — near-racemic·symmetry-breaking·homochiral sweep. sliders — α 0.01–0.3·0.12, β 0–1.5·0.5, diffusion 0–0.3·0.1, noise 0–0.05·0.005.

### VIII · RNA world  ✅
![stage07_rna](../generated/web10/stage07_rna.png)
- **Ⓐ** PCR thermocycler, 8-tube strip, glowing thermal-program display, gel-doc teal bands · **Ⓑ** migrating RNA strands / bands · **Ⓒ** `VIII · RNA WORLD` · **Ⓔ** warm-sepia + teal.
- **Controls** — regimes — quasispecies locked·at error threshold·error catastrophe. sliders — μ 0–0.5·0.01, σ 1–8·4, length 4–64·32, rounds/frame 1–6·2.

### IX · Genetic code  ✅
![stage08_code](../generated/web10/stage08_code.png)
- **Ⓐ** 4×4 codon-table card locking into a teal→warm→magenta spectrum, ribosome on mRNA · **Ⓑ** ordered codon grid · **Ⓒ** `IX · GENETIC CODE` · **Ⓔ** teal–warm–magenta ramp.
- **Controls** — regimes — frozen accident·vertical-only (no HGT)·universal (HGT). sliders — β-selection 0–12·4, HGT 0–1·0.4, reassign 0–0.5·0.08, aa classes 2–12·8, sweeps/frame 1–8·3.

### X · Coacervates  ✅
![stage09_coacervate](../generated/web10/stage09_coacervate.png)
- **Ⓐ** brass microscope; eyepiece disc of teal coacervate droplets ripening · **Ⓑ** coalescing droplets · **Ⓒ** `X · COACERVATES` · **Ⓔ** warm-sepia.
- **Controls** — regimes — many small·balanced·few large. sliders — mobility 0.05–0.6·0.3, κ-interface 0.1–2·1.0, iters/frame 1–8·3.

### XI · Protocell selection  ✅
![stage10_selection](../generated/web10/stage10_selection.png)
- **Ⓐ** acrylic microfluidic chip, serpentine channel, 5×8 well grid (magenta→teal fitness) · **Ⓑ** droplet-well fitness array · **Ⓒ** `XI · PROTOCELL SELECTION` · **Ⓔ** magenta→teal.
- **Controls** — regimes — fast turnover·balanced·long-lived. sliders — amoeba lifespan 10–200·60. ⚠ #65: only one knob.

### XII · LUCA  ✅
![stage11_luca](../generated/web10/stage11_luca.png)
- **Ⓐ** vintage-futurist console, gene-family screen locking to a core, rotating tree-of-life hologram converging to a root · **Ⓑ** converging phylogenetic tree · **Ⓒ** `XII · LUCA` · **Ⓔ** teal emissive.
- **Controls** — regimes — sharp LUCA·balanced descent·tree of life·no ancestor. sliders — μ-divergence 0–0.05·0.004, selection 0–1·0.5, transfer 0–1·0.4, core threshold 0.5–0.99·0.85, gens/frame 1–6·2.

### XIII · Stromatolite  ✅
![stage12_stromatolite](../generated/web10/stage12_stromatolite.png)
- **Ⓐ** sawn rock hand-specimen on felt, ochre/cream/grey laminations, scale bar, faint teal water caustics · **Ⓑ** layered microbial laminae · **Ⓒ** `XIII · STROMATOLITE` · **Ⓔ** ochre/cream/grey.
- **Controls** — runs the digital-life (`life`) experiment. regimes — none ⚠ #65. sliders — founder pop 20–600·200, ε-mutation 0–0.2·0.02, substrate regen 0–0.2·0.05, pop cap 200–2000·1400, energy 20–120·60. No Palette (hi-res).

---

## 4 · Change log

| Change | Status | Notes |
|---|---|---|
| ① MK X build tag · ② magenta accent · ③ hero-art rail · ④ Pro 4000² pill | `[DONE]` | shipped in PR #78 |
| ⑤ timeline scrubber · ⑥ provenance strip | `[BUILD]` | next build |
| ⑦ amoeba guide · ⑧ inline Pro `/api/render` · #65 control parity | `[OPT]` | stretch |
| 13 per-level hero PNGs | **`13/13` ✅** | generated via Gemini/Imagen, committed under docs/generated/web10/ |

> Note: the Gemini extractor recovered; the set was generated one-at-a-time (the concurrent batch overloads the tab past its 120s cap — ~7/11 of a batch survive, the rest are re-run singly). Re-run any single stage with the same prompt to refine it.
