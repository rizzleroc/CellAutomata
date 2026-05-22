"""Alkaline hydrothermal vent: the proton gradient is the free-energy source.

The scientific claim under test (Lane & Martin 2012): organic synthesis is
driven by the proton-motive force across the chimney wall. So a real vent–ocean
pH gradient must produce organic matter at the interface, while flattening the
gradient (vent pH == ocean pH) must produce none.
"""

from __future__ import annotations

import random

from cellauto.rules.abiogenesis.stage_vents import AbiogenesisStageVents


def _run(rule: AbiogenesisStageVents, steps: int = 50) -> int:
    state = rule.init_state(40, 40)
    for _ in range(steps):
        state = rule.step(state)
    return rule.population(state)["organic_cells"]


def test_gradient_drives_synthesis():
    organic = _run(AbiogenesisStageVents(rng=random.Random(1)))
    assert organic > 100


def test_flat_gradient_yields_no_synthesis():
    flat = AbiogenesisStageVents(vent_alkalinity=0.5, ocean_acidity=0.5, rng=random.Random(1))
    assert _run(flat) == 0


def test_serialization_round_trip():
    import numpy as np

    rule = AbiogenesisStageVents(rng=random.Random(3))
    state = rule.init_state(16, 16)
    for _ in range(5):
        state = rule.step(state)
    restored = rule.deserialize_state(rule.serialize_state(state))
    assert np.allclose(restored.protons, state.protons, atol=1e-3)
    assert np.allclose(restored.organic, state.organic, atol=1e-3)


def test_registered():
    from cellauto.rules import REGISTRY

    assert "abiogenesis-hydrothermal-vent" in REGISTRY
