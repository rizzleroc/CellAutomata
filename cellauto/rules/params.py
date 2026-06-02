"""Tunable-parameter metadata for the GUI's live controls.

Each rule exposes scientific knobs as dataclass fields that ``step`` reads
every frame, so changing them live (just ``setattr``) takes effect on the next
step with no re-initialisation. ``PARAM_SPECS`` maps a rule's ``name`` to the
sliders the GUI should show; the pipeline rule reuses the spec of whichever
inner stage is currently running.

Only live-applicable parameters live here. Structural parameters that require
rebuilding the state (grid size, species/reaction counts, Wolfram rule number)
are intentionally excluded for now — see docs/ROADMAP.md.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParamSpec:
    """One tunable knob: the attribute to set, a short label, the slider range
    and step, and whether the value is an integer. Set ``reinit=True`` for
    structural parameters that change the *shape* of the state (species
    counts, food fraction, …) so the GUI re-initialises the state on change."""

    attr: str
    label: str
    lo: float
    hi: float
    step: float
    integer: bool = False
    reinit: bool = False


PARAM_SPECS: dict[str, list[ParamSpec]] = {
    "abiogenesis-stage0-soup": [
        ParamSpec("amoeba_lifespan", "amoeba lifespan", 5, 60, 1, integer=True),
    ],
    "natural-selection": [
        ParamSpec("amoeba_lifespan", "amoeba lifespan", 5, 60, 1, integer=True),
    ],
    "abiogenesis-stage1-grayscott": [
        ParamSpec("F", "feed  F", 0.0, 0.09, 0.001),
        ParamSpec("k", "kill  k", 0.03, 0.075, 0.001),
        ParamSpec("Du", "diffuse  Du", 0.05, 0.30, 0.01),
        ParamSpec("Dv", "diffuse  Dv", 0.02, 0.20, 0.01),
    ],
    "abiogenesis-stage2-raf": [
        ParamSpec("food_supply", "food supply", 0.0, 0.20, 0.005),
        ParamSpec("diffusion_rate", "diffusion", 0.0, 0.20, 0.005),
        # Structural — rebuilds the random reaction network on change.
        ParamSpec("n_species", "species  N", 4, 16, 1, integer=True, reinit=True),
        ParamSpec("n_reactions", "reactions", 4, 40, 1, integer=True, reinit=True),
        ParamSpec("food_fraction", "food fraction", 0.1, 0.8, 0.05, reinit=True),
    ],
    "abiogenesis-stage3-vesicles": [
        ParamSpec("cmc_threshold", "CMC threshold", 0.05, 0.90, 0.01),
        ParamSpec("F", "feed  F", 0.0, 0.09, 0.001),
        ParamSpec("k", "kill  k", 0.03, 0.075, 0.001),
    ],
    "abiogenesis-stage4-selection": [
        # Default mutation_rate is 0.02; the Eigen error threshold is 1/n_species
        # (0.25 for n=4), so this slider can cross it and trigger error catastrophe.
        ParamSpec("mutation_rate", "mutation rate", 0.0, 0.40, 0.005),
        ParamSpec("division_radius", "division radius", 4, 20, 1, integer=True),
        ParamSpec("decay_age", "decay age", 20, 200, 5, integer=True),
    ],
    "abiogenesis-rna-world": [
        # The error-rate slider crosses the Eigen threshold ε_c = ln(σ)/L
        # (≈ 0.14 at the σ=10, L=16 defaults) — push it past to watch the
        # master quasispecies dissolve into the error catastrophe.
        ParamSpec("error_rate", "error rate  ε", 0.0, 0.40, 0.005),
        ParamSpec("superiority", "master adv.  σ", 2.0, 30.0, 1.0),
        ParamSpec("death_rate", "death rate", 0.02, 0.40, 0.01),
        ParamSpec("repro_prob", "replication", 0.1, 1.0, 0.05),
    ],
    "abiogenesis-homochirality": [
        # k_cross is the mutual-antagonism strength — the winner-take-all term
        # that drives symmetry breaking. Turn it down toward 0 and the racemic
        # state becomes stable (no homochirality).
        ParamSpec("k_auto", "autocatalysis  kₐ", 0.2, 2.0, 0.05),
        ParamSpec("k_cross", "antagonism  kₓ", 0.0, 4.0, 0.1),
        ParamSpec("feed", "substrate feed", 0.0, 0.4, 0.01),
        ParamSpec("diffusion", "diffusion", 0.0, 0.3, 0.01),
    ],
    "abiogenesis-hydrothermal-vent": [
        # The vent–ocean pH gap IS the free-energy source. Slide vent and ocean
        # toward the same value and the proton-motive force (and all synthesis)
        # vanishes — Lane & Martin's point that the gradient does the work.
        ParamSpec("vent_alkalinity", "vent pH (alk)", 0.0, 0.5, 0.01),
        ParamSpec("ocean_acidity", "ocean pH (acid)", 0.5, 1.0, 0.01),
        ParamSpec("k_synth", "synthesis rate", 0.0, 1.5, 0.05),
        ParamSpec("decay", "organic decay", 0.0, 0.2, 0.005),
    ],
    "abiogenesis-coacervate": [
        # kappa sets line tension / interface width (bigger → fewer, larger
        # droplets); mean_composition sets how much rich phase there is
        # (toward 0 → bicontinuous, more negative → sparse droplets).
        ParamSpec("kappa", "line tension  κ", 0.1, 1.0, 0.05),
        ParamSpec("mobility", "mobility  M", 0.2, 1.2, 0.05),
        ParamSpec("mean_composition", "mean comp.  φ̄", -0.7, 0.0, 0.02),
    ],
    "abiogenesis-mineral-catalysis": [
        # Raise the bulk rate to the clay rate and the surface catalysis
        # disappears — polymer forms everywhere, the Ferris result vanishes.
        ParamSpec("k_clay", "clay rate", 0.0, 0.5, 0.01),
        ParamSpec("k_bulk", "bulk-water rate", 0.0, 0.5, 0.01),
        ParamSpec("k_hydrolysis", "hydrolysis", 0.0, 0.1, 0.002),
        ParamSpec("feed", "monomer feed", 0.0, 0.3, 0.01),
    ],
    "abiogenesis-genetic-code": [
        # Lower strand mutation + lower code mutation → faster convergence to
        # a shared universal code (Vetsigian-Woese-Goldenfeld coevolution).
        ParamSpec("strand_mutation", "msg error", 0.0, 0.20, 0.005),
        ParamSpec("code_mutation", "code drift", 0.0, 0.05, 0.001),
        ParamSpec("death_rate", "death rate", 0.02, 0.30, 0.01),
        ParamSpec("repro_prob", "replication", 0.1, 1.0, 0.05),
    ],
    "abiogenesis-luca": [
        # gene_cost is the selection knob — higher cost trims the genome
        # toward the essential core, sharpening LUCA reconstruction.
        ParamSpec("gene_cost", "genome cost", 0.0, 0.4, 0.01),
        ParamSpec("mutation_rate", "mutation", 0.0, 0.05, 0.001),
        ParamSpec("death_rate", "death rate", 0.02, 0.30, 0.01),
        ParamSpec("core_prevalence", "core ≥", 0.5, 0.99, 0.01),
    ],
    "wolfram1d": [
        # Rule 30 = chaos, 90 = Sierpiński, 110 = Turing-complete (Cook 2004).
        ParamSpec("rule_number", "rule  #", 0, 255, 1, integer=True, reinit=True),
    ],
}


# Rules for which the GUI should also offer the Pearson regime preset picker.
PEARSON_PRESET_RULES: frozenset[str] = frozenset({"abiogenesis-stage1-grayscott"})
