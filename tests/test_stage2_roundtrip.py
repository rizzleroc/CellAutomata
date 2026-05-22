"""Stage 2 (RAF) snapshot round-trip: the reaction network must survive
serialize -> deserialize so a resumed run evolves under the *same* chemistry
that produced the saved concentration field."""

from __future__ import annotations

import random

from cellauto.rules.abiogenesis.stage2_raf import AbiogenesisStage2RAF


def test_network_survives_roundtrip():
    rule = AbiogenesisStage2RAF(rng=random.Random(7))
    state = rule.init_state(20, 20)
    blob = rule.serialize_state(state)
    restored = rule.deserialize_state(blob)

    # Same network identity: species count, food set, and every reaction.
    assert restored.network.n_species == state.network.n_species
    assert restored.network.food_set == state.network.food_set
    assert set(restored.network.reactions) == set(state.network.reactions)
    # RAF is derived deterministically from the network, so it round-trips too.
    assert restored.raf == state.raf


def test_concentrations_survive_roundtrip():
    rule = AbiogenesisStage2RAF(rng=random.Random(3))
    state = rule.init_state(16, 16)
    for _ in range(5):
        state = rule.step(state)
    restored = rule.deserialize_state(rule.serialize_state(state))
    # Field preserved to serialization rounding (4 dp).
    assert restored.concentrations.shape == state.concentrations.shape
    assert abs(float(restored.concentrations.sum()) - float(state.concentrations.sum())) < 1.0


def test_legacy_snapshot_without_network_still_loads():
    """Pre-network-roundtrip saves had only concentrations; they must still
    deserialize (falling back to a fresh random network)."""
    rule = AbiogenesisStage2RAF(rng=random.Random(1))
    state = rule.init_state(12, 12)
    legacy = {"concentrations": state.concentrations.round(4).tolist()}
    restored = rule.deserialize_state(legacy)
    assert restored.concentrations.shape == state.concentrations.shape
    assert restored.network is not None
