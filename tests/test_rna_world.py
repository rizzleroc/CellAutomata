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
