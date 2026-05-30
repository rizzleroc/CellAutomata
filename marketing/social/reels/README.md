# cellauto — 30 vertical reels

A pack of 30 short (~10s) vertical (1080×1920) reels for TikTok (@ai.news760)
and other vertical-video feeds. Each reel is **hook card → real simulator
footage → branded end card** with a soft ambient bed, built entirely from the
project's own output (no stock media).

The `.mp4` files are **gitignored** (large, regenerable) — rebuild them locally:

```bash
pip install -e . && pip install imageio-ffmpeg
bash marketing/social/render_footage.sh            # real sim footage -> exports/
python3 marketing/social/build_reels.py            # all 30 -> marketing/social/reels/
# subset / parallel:
python3 marketing/social/build_reels.py --only 0,5,12
```

Several processes (or subagents) can each build a disjoint `--only` slice in
parallel — outputs and temp dirs never collide.

| # | slug | focus |
|---|------|-------|
| 00 | hero-division | Gray-Scott self-replicating spots |
| 01 | reaction-diffusion | reaction–diffusion 101 (Turing) |
| 02 | five-regimes | F/k presets: spots→mazes |
| 03 | primordial-soup | Stage 0, Miller-Urey 1953 |
| 04 | hydrothermal-vent | Lane-Martin chemiosmosis |
| 05 | autocatalytic-sets | Kauffman / Hordijk-Steel RAF |
| 06 | homochirality | Frank 1953 symmetry breaking |
| 07 | rna-world | Eigen quasispecies / error catastrophe |
| 08 | genetic-code | Woese code coevolution |
| 09 | coacervates | Cahn-Hilliard / Oparin |
| 10 | mineral-catalysis | montmorillonite / Ferris |
| 11 | vesicles | Helfrich / CMC |
| 12 | protocell-selection | Eigen-Schuster hypercycle |
| 13 | luca | Weiss et al. 2016 |
| 14 | pipeline-tour | 12 coupled stages |
| 15 | conway | Game of Life (reference) |
| 16 | wolfram-110 | rule 110, Turing-complete |
| 17 | science-spine | every constant is cited |
| 18 | reproducible | deterministic from seed |
| 19 | web-demo | in-browser Stage 1 |
| 20 | honest-gaps | v3.5 self-audit |
| 21 | twelve-tableaux | Twelve Tableaux plate |
| 22 | genesis-poster | Genesis magnum opus |
| 23 | prima-materia | Catalytic Silence design |
| 24 | hero-closeup | the hero frame |
| 25 | open-source | MIT · 141 tests · CI |
| 26 | accessibility | CVD-safe / reduced-motion |
| 27 | chemistry-to-life | the whole arc |
| 28 | error-catastrophe | ε_c = ln(σ)/L |
| 29 | final-cta | star it on GitHub |

Publishing is manual — download the MP4s and upload them yourself.
