"""Coacervates: Cahn-Hilliard liquid-liquid phase separation + coarsening.

Scientific claims under test: (1) from a near-uniform mixture the field
spontaneously separates into a coacervate-rich phase and a dilute phase
(spinodal decomposition), and (2) the droplets then coarsen — the droplet
count peaks and then declines (Ostwald ripening / fusion). The integrator must
also stay finite.
"""

from __future__ import annotations

import random

import numpy as np

from cellauto.rules.abiogenesis.stage_coacervate import AbiogenesisStageCoacervate


def _trajectory(rule: AbiogenesisStageCoacervate, frames: int = 9, per: int = 10):
    state = rule.init_state(48, 48)
    counts = []
    for _ in range(frames):
        for _ in range(per):
            state = rule.step(state)
        counts.append(rule.population(state)["droplets"])
    return state, counts


def test_phase_separation_and_finite():
    rule = AbiogenesisStageCoacervate(rng=random.Random(1))
    state, counts = _trajectory(rule)
    assert np.isfinite(state.phi).all()
    # A rich phase emerges (droplets form, rich fraction becomes non-trivial).
    assert max(counts) > 5
    assert rule.population(state)["rich_pct"] > 5


def test_coarsening_reduces_droplet_count():
    rule = AbiogenesisStageCoacervate(rng=random.Random(1))
    _, counts = _trajectory(rule, frames=10)
    peak = max(counts)
    peak_i = counts.index(peak)
    # After the peak, coarsening should reduce the count.
    assert counts[-1] < peak
    assert peak_i < len(counts) - 1


def test_serialization_round_trip():
    rule = AbiogenesisStageCoacervate(rng=random.Random(3))
    state = rule.init_state(12, 12)
    for _ in range(5):
        state = rule.step(state)
    restored = rule.deserialize_state(rule.serialize_state(state))
    assert np.allclose(restored.phi, state.phi, atol=1e-3)


def test_registered():
    from cellauto.rules import REGISTRY

    assert "abiogenesis-coacervate" in REGISTRY
