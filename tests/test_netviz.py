"""Smoke test for the RAF reaction-network renderer (Stage 2 payoff)."""

from __future__ import annotations

import random

from cellauto.netviz import render_reaction_network
from cellauto.rules.abiogenesis.stage2_raf import AbiogenesisStage2RAF


def test_render_reaction_network_returns_rgb_image():
    rule = AbiogenesisStage2RAF(n_species=6, n_reactions=12, rng=random.Random(1))
    state = rule.init_state(16, 16)
    img = render_reaction_network(state.network, state.raf, size=480)
    assert img.size == (480, 480)
    assert img.mode == "RGB"


def test_render_handles_empty_raf():
    rule = AbiogenesisStage2RAF(n_species=5, n_reactions=4, rng=random.Random(2))
    state = rule.init_state(12, 12)
    # Even if no RAF exists, rendering must not crash.
    img = render_reaction_network(state.network, frozenset(), size=320)
    assert img.size == (320, 320)
