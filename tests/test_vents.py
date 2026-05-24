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


def test_thermodynamic_readouts_hit_lane_martin_range():
    """The default vent vs ocean pH gap should produce a proton-motive force
    in the ~200-300 mV range and ~−25 kJ/mol per proton — the Lane-Martin
    "this can drive abiotic carbon fixation" window."""
    rule = AbiogenesisStageVents()
    # Default ΔpH should be 4.5 (alkaline 10.0, acidic 5.5).
    assert abs(rule.delta_pH() - 4.5) < 1e-9
    # Nernst: 59.16 mV × 4.5 ≈ 266 mV.
    assert 200 <= rule.pmf_mV() <= 300
    # Faraday: −96.485 × 0.266 ≈ −25.7 kJ/mol.
    assert -30 <= rule.delta_G_kJ_per_mol() <= -15


def test_flat_gradient_zeros_thermodynamics():
    rule = AbiogenesisStageVents(pH_alkaline=7.0, pH_acidic=7.0)
    assert rule.delta_pH() == 0.0
    assert rule.pmf_mV() == 0.0
    assert rule.delta_G_kJ_per_mol() == 0.0


def test_thermodynamics_in_population():
    rule = AbiogenesisStageVents(rng=random.Random(1))
    state = rule.init_state(16, 16)
    pop = rule.population(state)
    assert pop["delta_pH_x10"] == 45  # 4.5 × 10
    assert 200 <= pop["pmf_mV"] <= 300
    assert -300 <= pop["delta_G_x10_kJmol"] <= -150  # −25.7 × 10 ≈ −257


def test_wood_ljungdahl_yield_is_positive_with_full_feedstocks():
    rule = AbiogenesisStageVents(rng=random.Random(1))
    state = rule.init_state(40, 40)
    for _ in range(80):
        state = rule.step(state)
    pop = rule.population(state)
    assert pop["acetate_yield_x100"] > 0
    assert pop["wl_delta_G_kJmol"] == -95
    assert rule.pathway == "wood_ljungdahl"


def test_no_h2_means_no_synthesis():
    """The reaction needs H2 — cutting the chimney's H2 supply must kill the
    yield even with the proton gradient intact."""
    rule = AbiogenesisStageVents(h2_feed_level=0.0, rng=random.Random(1))
    state = rule.init_state(40, 40)
    for _ in range(50):
        state = rule.step(state)
    assert rule.population(state)["acetate_yield_x100"] == 0


def test_no_co2_means_no_synthesis():
    """Same for CO2 — both feedstocks are required for the stoichiometric
    Wood-Ljungdahl reaction to fire."""
    rule = AbiogenesisStageVents(co2_feed_level=0.0, rng=random.Random(1))
    state = rule.init_state(40, 40)
    for _ in range(50):
        state = rule.step(state)
    assert rule.population(state)["acetate_yield_x100"] == 0


def test_stoichiometric_cap_respects_two_to_one_ratio():
    """G8 pin: the Wood-Ljungdahl net reaction is 2 CO₂ + 4 H₂ → acetate
    (normalised in-sim to 1 CO₂ + 2 H₂). So no matter how much H₂ we flood
    in, the acetate yield must remain bounded by the CO₂ feed — the reaction
    can't run faster than its limiting reagent. We check this by clamping
    CO₂ low and H₂ high: yield should be small (because CO₂ is the limiter),
    NOT proportional to the H₂ excess.
    """
    co2_limited = AbiogenesisStageVents(
        h2_feed_level=1.0,
        co2_feed_level=0.05,  # CO2 is the limiting reagent
        co2_feed_rate=0.01,
        rng=random.Random(1),
    )
    full = AbiogenesisStageVents(rng=random.Random(1))
    state_lim = co2_limited.init_state(40, 40)
    state_full = full.init_state(40, 40)
    for _ in range(80):
        state_lim = co2_limited.step(state_lim)
        state_full = full.step(state_full)
    yield_limited = co2_limited.population(state_lim)["acetate_yield_x100"]
    yield_full = full.population(state_full)["acetate_yield_x100"]
    # The CO2-starved run must produce strictly less acetate than the
    # both-feedstocks-flush run, AND less than half of it (because the
    # CO2 supply is ~13× lower) — i.e. the stoichiometric cap binds.
    assert yield_limited < yield_full, (
        f"CO2-limited yield {yield_limited} should be < full-feed yield {yield_full}"
    )
    assert yield_limited <= yield_full // 2, (
        f"stoichiometric cap not binding: CO2-limited {yield_limited} vs full {yield_full}"
    )
