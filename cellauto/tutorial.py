"""Per-rule tutorial copy. Each rule has its own walkthrough.

Phase 2 §2.4 — v2.0 shipped a single hardcoded tutorial that talked about
amoebas no matter which rule was selected. Now `tutorial_for(rule_name)`
returns the relevant copy for the active rule.
"""

from __future__ import annotations

_TUTORIALS: dict[str, tuple[str, ...]] = {
    "abiogenesis-pipeline": (
        "Welcome. This sim walks the chemistry-to-life story end to end.",
        "Stage 0 — Primordial soup. Discrete molecules in random Brownian motion. Same-species cells in proximity can combine.",
        "Stage 1 — Reaction-diffusion. Continuous chemistry on a numpy field. Gray-Scott (1985) produces self-replicating spots; Pearson (1993) mapped the parameter regimes.",
        "Stage 2 — Autocatalytic sets (Kauffman 1986). A random reaction network is generated; the RAF algorithm (Hordijk-Steel 2004) detects closed catalytic cycles. Bright regions are autocatalytic ignition.",
        "Stage 3 — Lipid vesicles. Where amphiphile concentration exceeds the critical micelle threshold, membranes self-assemble. The amber halos are protocell membranes.",
        "Stage 4 — Protocell selection. Each protocell carries a genome; size-based growth and division create heritable variation. Eigen-Schuster hypercycle dynamics emerge.",
        "Click 'Promote stage' to step manually; the pipeline auto-promotes every 60 steps. See docs/science.md for citations.",
    ),
    "abiogenesis-pipeline-extended": (
        "Extended pipeline — every shipped origin-of-life process toured in narrative order.",
        "0 Soup → 1 Alkaline vent → 2 Reaction-diffusion → 3 Mineral catalysis → 4 RAFs → 5 Homochirality → 6 RNA world → 7 Genetic code → 8 Coacervates → 9 Vesicles → 10 Protocell selection → 11 LUCA.",
        "The vent supplies the proton-motive force (Lane-Martin chemiosmosis). Mineral surfaces localise polymerisation (Ferris). Chirality breaks before the first replicators (Frank). RNA world meets the error threshold (Eigen). Genetic code coevolves under selection (Vetsigian-Woese-Goldenfeld). Coacervates and vesicles offer parallel compartmentalisation routes. LUCA is distilled from a population of cells under selection.",
        "Each stage runs to its own steady-ish state and then promotes — there is no chemical carry-over between stages, so think of this as a curated slideshow of 12 honest models, not one continuous simulation. (See docs/PUNCHLIST.md P1-5.)",
        "Auto-promotes every 90 steps by default — use AUTO-PROMOTE / DUR to slow it, JUMP to skip ahead, or SCRUB to rewind.",
        "Use the canonical 5-stage abiogenesis-pipeline for the museum-plate tour; use this rule when you want to see every process.",
    ),
    "abiogenesis-stage0-soup": (
        "Stage 0 — Primordial soup. The 16-species palette stands in for distinct chemical species in an Oparin-Haldane prebiotic ocean.",
        "Rule 1: each non-amoeba cell adopts the species of a random neighbor every step. This models the Brownian mixing of dissolved molecules.",
        "Rule 2: when two adjacent cells SHARE a species and BOTH just changed this step, they condense into a protocell (amoeba). Same-monomer condensation is real prebiotic chemistry.",
        "Rule 3 — activated intermediates. A cell only stays 'new' for the single step in which its species shifted. Settled cells are inert.",
        "Rule 4 — amoebas are first-generation protocells. They are inert for 25 steps, then dissolve, releasing fresh chemistry.",
        "Try the abiogenesis-pipeline rule to see this stage feed into reaction-diffusion, autocatalytic sets, and vesicles.",
    ),
    "abiogenesis-stage1-grayscott": (
        "Gray-Scott reaction-diffusion. Two species u and v on a continuous concentration field.",
        "PDE: ∂u/∂t = D_u∇²u - uv² + F(1-u); ∂v/∂t = D_v∇²v + uv² - (F+k)v.",
        "Pearson (1993) charted the (F, k) parameter space. The default preset is 'spots' — F=0.035, k=0.065 — which produces self-replicating spots that visually resemble protocell division.",
        "Look for 'mitosis' (cells split), 'waves' (traveling fronts), 'labyrinth' (maze-like stripes).",
        "Turing (1952) showed that two interacting species + diffusion can produce stable spatial patterns. This is the same mechanism that gives zebras stripes.",
    ),
    "abiogenesis-stage2-raf": (
        "Kauffman autocatylic sets. A random reaction network of n_species molecules.",
        "Hordijk-Steel (2004) closure algorithm finds the maximal RAF — Reflexively Autocatalytic Food-generated set.",
        "The RAF is the formal mathematical object that makes Kauffman's 1986 intuition rigorous: above a connectivity threshold, closed catalytic cycles emerge spontaneously.",
        "Bright (yellow) regions are cells where RAF reactions are firing — autocatalytic ignition. Dark regions are catalytically inert.",
        "Real prebiotic chemistry research (Joyce, Sutherland) is trying to construct minimal RAFs in the lab right now.",
    ),
    "abiogenesis-stage3-vesicles": (
        "Lipid concentration regime (Gray-Scott proxy). Reaction-diffusion grows a 'lipid' field locally.",
        "Above a dimensionless threshold (cmc_threshold), the field is marked as 'membrane' and connected components are counted as vesicles. The threshold is NOT the CMC in mM — the named amphiphile (decanoic, oleic, …) sets the cmc_mM readout but does not change the dynamics.",
        "Amber rings are membrane pixels — enclosed regions of high field value. Real lipid self-assembly requires curvature elasticity, surface tension, and amphiphile-specific kinetics, none of which are modelled here. See Helfrich (1973), Deamer for the real physics; see docs/PUNCHLIST.md P1-1 for the honest scope of THIS implementation.",
        "Once compartments exist (here as field regions), evolution can act on the compartments — see Stage 4.",
    ),
    "abiogenesis-stage4-selection": (
        "Protocell selection. Vesicles tracked as discrete agents with internal 'genomes'.",
        "Fitness = Shannon entropy × total internal concentration. Cells with diverse internal chemistry grow; degenerate cells shrink.",
        "Sufficient size triggers division; the daughter inherits the parent's genome with mutation. Heritable variation + differential survival = Darwinian evolution.",
        "Eigen-Schuster (1977) showed that mutually-catalyzing replicator loops (hypercycles) are evolutionarily stable in a way isolated replicators are not.",
        "This stage is a toy model of the moment biology splits off from chemistry.",
    ),
    "abiogenesis-rna-world": (
        "RNA world (Gilbert 1986). RNA as both genotype and catalyst — a spatial population of self-replicating strands.",
        "Each cell holds an RNA strand (4-letter alphabet) or is empty. Empty cells are colonized by a fitness-weighted occupied neighbor, copied base-by-base with per-base error ε.",
        "Single-peak landscape: the 'master' strand replicates σ× faster than mutants. Bright (yellow) = master; darker = more mutations away from it.",
        "Eigen (1971) error threshold: the master survives only while ε < ε_c = ln(σ)/L. At the σ=10, L=16 defaults that's ≈ 0.14.",
        "Drag the error-rate slider past the threshold and watch the bright master colonies dissolve into dark noise — the error catastrophe.",
    ),
    "abiogenesis-homochirality": (
        "Homochirality (Frank 1953). Life uses only L-amino acids and D-sugars — but a prebiotic soup is racemic (equal L and R). What broke the mirror symmetry?",
        "Two enantiomers L and R diffuse on the field. Each AUTOCATALYSES its own production from substrate A; opposite hands ANTAGONISE (L + R → inert).",
        "Teal = L-dominant, magenta = R-dominant, dark = racemic/empty. Watch local domains spontaneously pick a hand from tiny initial fluctuations.",
        "This is unstable to the racemic state: the tiniest excess is amplified to dominance. The Soai reaction (1995) demonstrates this asymmetric autocatalysis in the lab.",
        "Turn the antagonism slider kₓ toward 0 and the racemic state becomes stable again — no symmetry breaking, no homochirality.",
    ),
    "abiogenesis-hydrothermal-vent": (
        "Alkaline hydrothermal vents (Russell, Martin & Lane). The metabolism-first alternative to the lightning-powered soup.",
        "Serpentinization makes warm, alkaline, H2-rich vent fluid; the early ocean was mildly acidic (CO2). Across the thin mineral chimney wall sits a natural proton gradient of ~3-4 pH units.",
        "Blue = alkaline vent interior, orange = acidic ocean. The steep gradient at the chimney WALL carries a proton-motive force — the same kind of gradient every living cell uses to make ATP.",
        "Teal-green glow = organic matter synthesised by that gradient. Synthesis ignites along the interface, not uniformly: the gradient, not a hand-set feed rate, is the free-energy source (Lane & Martin 2012).",
        "Slide the vent and ocean pH toward each other until the gradient is flat — synthesis stops. No gradient, no free energy, no chemistry.",
    ),
    "abiogenesis-genetic-code": (
        "Origin of the genetic code (Crick 1968; Woese 1965; Wong 1975). The deepest unsolved problem at the chemistry-to-biology boundary — and the conceptual bridge from this simulator's protocells to actual life.",
        "Each cell holds an RNA-like strand AND its own private codon→amino-acid code. Fitness is how well the peptide (strand decoded via the cell's own code) matches a needed catalyst.",
        "Crucially, both the strand AND the code mutate when copied (vertical inheritance). AND adjacent cells with similar codes exchange codon assignments at rate hgt_rate (horizontal gene transfer — the Vetsigian-Woese-Goldenfeld 2006 mechanism). HGT is what makes code universality emerge collectively rather than via single-lineage fixation; drag hgt_rate to 0 to see the vertical-only baseline.",
        "Watch the `code_consensus` stat rise: this is the population converging on a SHARED code, which is what happened on Earth ~4 billion years ago.",
        "This is the last hand-off before biology proper: with a shared code, the population now has a translation system. Everything downstream is evolution within bounded chemical individuals.",
    ),
    "abiogenesis-luca": (
        "LUCA distillation — the inferred Last Universal Common Ancestor (Koonin 2003; Weiss et al. 2016).",
        "Each cell carries a gene-presence bitset; some genes are essential (high benefit), some accessory (mild), some deleterious (costly). Per-gene maintenance cost penalises bloat.",
        "Selection + mutation drives the population. The `luca_size` stat tracks the inferred ancestral core: genes present in ≥70% of surviving lineages — exactly how Weiss et al. (2016) reconstructed LUCA from comparative genomics across all sequenced prokaryotes.",
        "Watch luca_size climb from 0 (random initial genomes) to the essential-gene count. That intersection IS the simulated LUCA — every living thing in the population descends from a lineage that retained those genes.",
        "Raise the genome-size cost slider to sharpen LUCA further; lower it and the lineages bloat with neutral accessory genes.",
    ),
    "abiogenesis-coacervate": (
        "Coacervates (Oparin 1924). The ORIGINAL protocell idea: dense, membraneless droplets that form when macromolecules phase-separate from solution.",
        "Modelled by the Cahn-Hilliard equation — conserved liquid-liquid phase separation. From a near-uniform mix, a polymer-rich phase (gold droplets) separates from a dilute phase (dark).",
        "This is the same physics as modern biomolecular condensates (membraneless organelles) — droplets concentrate RNA and catalysts without needing a lipid membrane.",
        "Watch the droplets COARSEN: small ones dissolve and feed larger ones (Ostwald ripening) and neighbours fuse, so the droplet count falls over time.",
        "Coacervates (membraneless) and lipid vesicles (Stage 3, membrane-bound) are two competing answers to the same question: how did chemistry first get a boundary?",
    ),
    "abiogenesis-mineral-catalysis": (
        "Mineral-surface catalysis (Ferris; Cairns-Smith). Condensation polymerization is uphill in bulk water — dilute monomers don't spontaneously form long chains in the open ocean.",
        "Montmorillonite clay solves this: it concentrates monomers on its charged surface and catalyses bond formation. Ferris (1996) grew RNA chains of 30-50 units this way.",
        "Tan patches = clay surface, dark = bulk water. Teal-green glow = polymer. Watch polymer accumulate ON the clay and barely anywhere else — the chemistry is localized to the mineral surface.",
        "Cairns-Smith (1982) went further: clay crystals as the first 'genetic' material, later handed off to organics (genetic takeover).",
        "Raise the bulk-water rate up to the clay rate and the localization vanishes — polymer forms everywhere. The surface is what makes it work.",
    ),
    "conway": (
        "Conway's Game of Life (Gardner 1970). B3/S23: dead cells with 3 live neighbors come alive; live cells with 2 or 3 neighbors survive.",
        "Look for: blinkers (3-cell oscillators), blocks (still life), gliders (5-cell traveling patterns).",
        "Conway's Life is Turing-complete — it can simulate any computation given enough space.",
    ),
    "wolfram1d": (
        "Elementary 1D automaton (Wolfram 2002). Each row is computed from the row below using a fixed rule (0-255).",
        "Rule 30 produces aperiodic chaos and is used in Mathematica's random number generator.",
        "Rule 110 is Turing-complete (Cook 2004). Rule 90 produces the Sierpiński triangle.",
    ),
    "natural-selection": (
        "Note: this is the v1.0 name for the Stage 0 primordial-soup rule. See abiogenesis-stage0-soup for the canonical version + citations.",
        "Same mechanics: discrete-species mixing → condensation when adjacent cells share a freshly-changed species → protocell formation.",
        "Rule 1: random neighbor color propagation. Rule 2: same-species condensation. Rule 3: activated intermediates. Rule 4: protocell membrane.",
    ),
}


def tutorial_for(rule_name: str) -> tuple[str, ...]:
    return _TUTORIALS.get(
        rule_name, (f"No tutorial copy for '{rule_name}' yet. Pick a rule from the dropdown.",)
    )


# Back-compat: v2.0 exposed this constant directly.
TUTORIAL_STEPS = _TUTORIALS["natural-selection"]
