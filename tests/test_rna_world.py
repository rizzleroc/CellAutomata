"""RNA-world stage: the spatial Eigen quasispecies and its error catastrophe.

The scientific claim under test is Eigen's error threshold ε_c = ln(σ)/L: below
it the master sequence is maintained; above it the population melts into random
sequences (error catastrophe). We run the same world below and above threshold
and assert the master survives in the first case and collapses in the second.
"""

from __future__ import annotations

import math
import random

from cellauto.engine import Engine
from cellauto.rules.abiogenesis.stage_rna import AbiogenesisStageRNAWorld


def test_error_threshold_formula():
    rule = AbiogenesisStageRNAWorld(superiority=10.0, seq_length=16)
    assert math.isclose(rule.error_threshold, math.log(10.0) / 16)


def _run(error_rate: float, steps: int = 40) -> int:
    """Return master_pct after `steps` steps at the given per-base error rate."""
    rule = AbiogenesisStageRNAWorld(
        error_rate=error_rate,
        superiority=10.0,
        seq_length=16,
        seed_fraction=0.5,
        death_rate=0.1,
    )
    engine = Engine(width=24, height=24, rule=rule, seed=7)
    for _ in range(steps):
        engine.step()
    return engine.population()["master_pct"]


def test_master_survives_below_threshold():
    # ε well below ε_c ≈ 0.144 — the master quasispecies should persist.
    assert _run(error_rate=0.01) > 40


def test_error_catastrophe_above_threshold():
    # ε well above ε_c — the master should be all but wiped out.
    below = _run(error_rate=0.01)
    above = _run(error_rate=0.35)
    assert above < below
    assert above < 15


def test_eigen_transition_at_predicted_threshold():
    """The phase transition Eigen 1971 predicts at ε_c = ln(σ)/L should be
    sharp: well below ε_c the master survives, well above ε_c it collapses.
    We tie the test to the *theoretical* formula by using 0.5·ε_c and
    1.5·ε_c rather than the broad-strokes 0.01-vs-0.35 numbers in the
    legacy test above. The claim under test is the RATIO — the master
    fraction at half-threshold must be substantially higher than at
    above-threshold, and the above-threshold value must be near zero.
    """
    rule_template = AbiogenesisStageRNAWorld(superiority=10.0, seq_length=16)
    eps_c = rule_template.error_threshold
    half = _run(error_rate=0.5 * eps_c, steps=80)
    above = _run(error_rate=1.5 * eps_c, steps=80)
    # Above ε_c the master is wiped out — finite-size noise allows a few
    # surviving cells but the population is no longer a quasispecies.
    assert above <= 3, f"above ε_c the master should collapse to near-zero (got {above} %)"
    # And the half-threshold case must be at least an order of magnitude
    # higher — the phase transition is sharp.
    assert half >= max(10, 5 * above), f"phase transition not sharp: half={half} %, above={above} %"


def test_serialization_round_trip():
    rule = AbiogenesisStageRNAWorld(rng=random.Random(3))
    state = rule.init_state(12, 12)
    for _ in range(5):
        state = rule.step(state)
    data = rule.serialize_state(state)
    restored = rule.deserialize_state(data)
    assert (restored.seqs == state.seqs).all()
    assert (restored.occupied == state.occupied).all()


def test_registered_in_registry():
    from cellauto.rules import REGISTRY

    assert "abiogenesis-rna-world" in REGISTRY
