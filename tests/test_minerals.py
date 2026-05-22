"""Mineral-surface catalysis: polymers form on clay, not in bulk water.

Scientific claim under test (Ferris): condensation polymerisation is catalysed
by the clay surface, so polymer accumulates preferentially on the clay. With
catalysis on, on-clay polymer should far exceed bulk polymer; with the bulk and
clay rates equal (no surface advantage), the two should be comparable.
"""

from __future__ import annotations

import random

import numpy as np

from cellauto.rules.abiogenesis.stage_minerals import AbiogenesisStageMinerals


def _run(rule: AbiogenesisStageMinerals, steps: int = 40):
    state = rule.init_state(48, 48)
    for _ in range(steps):
        state = rule.step(state)
    return rule.population(state)


def test_polymer_localises_on_clay():
    pop = _run(AbiogenesisStageMinerals(rng=random.Random(1)))
    # On-clay polymer should be several times the bulk-water polymer.
    assert pop["polymer_on_clay_x100"] > 3 * max(pop["polymer_in_bulk_x100"], 1)


def test_no_catalysis_no_localisation():
    rule = AbiogenesisStageMinerals(k_clay=0.05, k_bulk=0.05, rng=random.Random(1))
    pop = _run(rule)
    on, off = pop["polymer_on_clay_x100"], pop["polymer_in_bulk_x100"]
    # Equal rates → comparable polymer on and off the clay.
    assert abs(on - off) <= max(5, on // 5)


def test_serialization_round_trip():
    rule = AbiogenesisStageMinerals(rng=random.Random(3))
    state = rule.init_state(16, 16)
    for _ in range(5):
        state = rule.step(state)
    restored = rule.deserialize_state(rule.serialize_state(state))
    assert np.allclose(restored.monomer, state.monomer, atol=1e-3)
    assert np.allclose(restored.polymer, state.polymer, atol=1e-3)
    assert (restored.clay == state.clay).all()


def test_registered():
    from cellauto.rules import REGISTRY

    assert "abiogenesis-mineral-catalysis" in REGISTRY
