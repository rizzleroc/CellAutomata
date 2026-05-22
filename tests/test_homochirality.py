"""Homochirality (Frank 1953): spontaneous mirror-symmetry breaking.

The scientific claim under test: with autocatalysis + mutual antagonism the
racemic state is unstable and local chiral domains form, whereas with the
antagonism turned off the field stays racemic. We assert that the fraction of
cells with a strong handedness (|ee| > 0.5) grows from ~0 under the default
dynamics, and stays low when k_cross = 0.
"""

from __future__ import annotations

import random

import numpy as np

from cellauto.rules.abiogenesis.stage_chirality import AbiogenesisStageHomochirality


def _broken_fraction(rule: AbiogenesisStageHomochirality, state) -> float:
    total = state.left + state.right
    active = total > 0.2
    n = int(active.sum())
    if not n:
        return 0.0
    ee = (state.left - state.right) / (total + 1e-6)
    return int((active & (np.abs(ee) > 0.5)).sum()) / n


def test_symmetry_breaks_into_chiral_domains():
    rule = AbiogenesisStageHomochirality(rng=random.Random(1))
    state = rule.init_state(32, 32)
    assert _broken_fraction(rule, state) < 0.05  # starts racemic
    for _ in range(60):
        state = rule.step(state)
    assert _broken_fraction(rule, state) > 0.6  # most cells picked a hand


def test_no_breaking_without_antagonism():
    # k_cross = 0 removes the winner-take-all term; the racemic state is stable.
    rule = AbiogenesisStageHomochirality(k_cross=0.0, rng=random.Random(2))
    state = rule.init_state(32, 32)
    for _ in range(60):
        state = rule.step(state)
    assert _broken_fraction(rule, state) < 0.2


def test_serialization_round_trip():
    rule = AbiogenesisStageHomochirality(rng=random.Random(3))
    state = rule.init_state(12, 12)
    for _ in range(5):
        state = rule.step(state)
    restored = rule.deserialize_state(rule.serialize_state(state))
    assert np.allclose(restored.left, state.left, atol=1e-3)
    assert np.allclose(restored.right, state.right, atol=1e-3)


def test_registered():
    from cellauto.rules import REGISTRY

    assert "abiogenesis-homochirality" in REGISTRY
