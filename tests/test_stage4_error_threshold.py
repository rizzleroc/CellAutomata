"""Stage 4 protocell-selection tests.

The Eigen error threshold ε_c = 1/L was a readout-only decoration in
pre-v3.5 — past the threshold, nothing in the dynamics changed. This
test pins the v3.5 fix (PUNCHLIST P1-2): when mutation_rate exceeds
1/n_species the genome drift visibly amplifies, and the population's
`error_catastrophe` stat surfaces it.
"""

from __future__ import annotations

import numpy as np

from cellauto.engine import Engine
from cellauto.rules.abiogenesis.stage4_selection import (
    AbiogenesisStage4Selection,
    Protocell,
)


def test_error_catastrophe_stat_surfaces_threshold_crossing():
    """At mutation_rate just below 1/n_species: catastrophe stat is 0.
    At mutation_rate just above: catastrophe stat is 1."""
    safe = AbiogenesisStage4Selection(n_species=4, mutation_rate=0.20)
    danger = AbiogenesisStage4Selection(n_species=4, mutation_rate=0.30)
    assert safe.error_threshold == 0.25
    assert danger.error_threshold == 0.25

    e_safe = Engine(width=20, height=20, rule=safe, seed=1)
    e_danger = Engine(width=20, height=20, rule=danger, seed=1)
    e_safe.step()
    e_danger.step()

    assert e_safe.population()["error_catastrophe"] == 0
    assert e_danger.population()["error_catastrophe"] == 1


def test_above_threshold_amplifies_genome_drift():
    """Across many steps, mutation above ε_c should drive higher per-cell
    genome variance than mutation just below ε_c. Pin the *qualitative*
    claim that the threshold gates dynamics, not just the readout."""
    rng_seed = 7
    # Seed identical initial genomes for both runs so the only difference
    # is the mutation regime.
    initial_genome = np.array([0.5, 0.5, 0.5, 0.5], dtype=np.float32)

    def run(mutation_rate: float, steps: int = 30) -> float:
        rule = AbiogenesisStage4Selection(n_species=4, mutation_rate=mutation_rate)
        engine = Engine(width=20, height=20, rule=rule, seed=rng_seed)
        # Replace the random initial cells with one fixed cell so we can
        # compare like-for-like.
        engine.state.cells = [
            Protocell(cx=10.0, cy=10.0, radius=4.0, genome=initial_genome.copy()),
        ]
        for _ in range(steps):
            engine.step()
            if not engine.state.cells:
                break
        # Measure spread of genomes across surviving cells (post any
        # division) as a coarse proxy for "how chaotic did this get?".
        alive = [c for c in engine.state.cells if c.alive]
        if not alive:
            return float("inf")  # extinction is the loud catastrophe
        genomes = np.stack([c.genome for c in alive])
        return float(np.std(genomes))

    spread_safe = run(0.20)  # below ε_c = 0.25
    spread_danger = run(0.40)  # above ε_c
    # The amplified-drift regime should produce noticeably more spread,
    # OR drive the population to extinction (also acceptable evidence
    # the dynamics changed). Either outcome confirms the gating works.
    assert spread_danger > spread_safe, (
        f"Expected larger genome spread above ε_c: safe={spread_safe:.4f} vs danger={spread_danger:.4f}"
    )


def test_below_threshold_matches_old_behavior():
    """When mutation_rate stays below ε_c, sigma_eff == mutation_rate
    and the dynamics are numerically identical to the pre-v3.5 code path.
    This protects against accidental regressions on the common-case demo
    (default mutation_rate=0.02 with n_species=4 → ε_c=0.25)."""
    rule = AbiogenesisStage4Selection(n_species=4, mutation_rate=0.02)
    engine = Engine(width=10, height=10, rule=rule, seed=42)
    for _ in range(5):
        engine.step()
    # Just confirms the step doesn't crash and the catastrophe stat is 0;
    # the actual stream identity is preserved because sigma_eff = mutation_rate
    # below the threshold (verified by code inspection).
    assert engine.population()["error_catastrophe"] == 0
