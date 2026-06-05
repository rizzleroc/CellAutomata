# CellAutomata — the 10-part explainer series

Thorough, science-grounded explainers. Each part: the **science**, the **art**, and
**how to drive the sandbox** — with a "TRY IT YOURSELF" card showing the real
`cellauto` command and the knobs you can tune. Voice-over + ambient bed, 1080².
Every claim, default, preset, and citation traces to the actual code.

Reproduce/extend any of these with `python3 tools/series.py --part N`
(scripts in `tools/series_scripts.py`).

| Part | File | Topic | Knobs taught |
|------|------|-------|--------------|
| 1 | `part01_overview.mp4` | What CellAutomata is | `--rule`, `--rule-config`, `--seed`, `--steps/--fps/--canvas` |
| 2 | `part02_grayscott.mp4` | Gray-Scott reaction-diffusion (Turing/Pearson) | `preset`, `F`, `k`, `Du`, `Dv`, `substeps_per_frame` |
| 3 | `part03_conway.mp4` | Conway's Game of Life (B3/S23) | `initial_density`, `wrap`, `--seed` |
| 4 | `part04_wolfram.mp4` | Wolfram 1D — rules 30/90/110 | `rule_number` (0–255) |
| 5 | `part05_pipeline.mp4` | The abiogenesis pipeline (soup→LUCA) | `--stage`, `stage_duration`, `auto_promote`, `--load` |
| 6 | `part06_early-chemistry.mp4` | Soup, vents & mineral catalysis | `vent_alkalinity/ocean_acidity`, `k_synth`, `clay_patches`, `amoeba_lifespan` |
| 7 | `part07_self-replication.mp4` | RAF autocatalytic sets & the RNA error catastrophe | `error_rate` vs `ln(σ)/L`, `superiority`, `seq_length` |
| 8 | `part08_compartments.mp4` | Vesicles, coacervates, hypercycles | `mutation_rate` vs `1/n`, `amphiphile`, `cmc_threshold`, `kappa_bend` |
| 9 | `part09_information-luca.mp4` | Homochirality, the genetic code, LUCA | `k_auto/k_cross`, `n_genes`, `per_gene_mutation` |
| 10 | `part10_sandbox-to-art.mp4` | Sandbox → art: search, kaleidoscope, relighting | `--seed`, `--canvas`, the `tools/` pipelines |

**Science grounding:** Miller (1953), Turing (1952), Pearson (1993), Kauffman (1986) /
Hordijk–Steel (2004), Helfrich (1973), Eigen–Schuster (1977–79), Lane–Martin (2012),
Ferris (1996), Frank (1953), Gilbert (1986), Vetsigian–Woese (2006), Cahn–Hilliard
(1958), Weiss et al. (2016), Wolfram (2002) / Cook (2004).
