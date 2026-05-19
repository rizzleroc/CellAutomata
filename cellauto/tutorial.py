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
        "Lipid self-assembly. Reaction-diffusion grows amphiphile concentration locally.",
        "Above the critical micelle concentration (CMC), lipids spontaneously assemble into bilayer membranes.",
        "Amber rings are vesicle membranes — enclosed regions of chemistry. These are the simplest possible protocells.",
        "Real lipid bilayer dynamics include curvature, fluidity, and pore formation; see Helfrich (1973), Deamer.",
        "Once chemistry is compartmentalized, evolution can act on the compartments — see Stage 4.",
    ),
    "abiogenesis-stage4-selection": (
        "Protocell selection. Vesicles tracked as discrete agents with internal 'genomes'.",
        "Fitness = Shannon entropy × total internal concentration. Cells with diverse internal chemistry grow; degenerate cells shrink.",
        "Sufficient size triggers division; the daughter inherits the parent's genome with mutation. Heritable variation + differential survival = Darwinian evolution.",
        "Eigen-Schuster (1977) showed that mutually-catalyzing replicator loops (hypercycles) are evolutionarily stable in a way isolated replicators are not.",
        "This stage is a toy model of the moment biology splits off from chemistry.",
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
    return _TUTORIALS.get(rule_name, (
        f"No tutorial copy for '{rule_name}' yet. Pick a rule from the dropdown.",
    ))


# Back-compat: v2.0 exposed this constant directly.
TUTORIAL_STEPS = _TUTORIALS["natural-selection"]
