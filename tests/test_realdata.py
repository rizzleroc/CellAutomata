"""Tests for the toy->real-data parameter upgrades (B-series): Miller-Urey
soup composition, fatty-acid CMC values, Kauffman catalysis level, and the
Eigen quasispecies error threshold. These pin that the simulation's numbers
trace to published measurements rather than arbitrary constants."""

from __future__ import annotations

import random

from cellauto.rules.abiogenesis.science import AMPHIPHILE_CMC_MM
from cellauto.rules.abiogenesis.stage2_raf import AbiogenesisStage2RAF
from cellauto.rules.abiogenesis.stage3_vesicles import AbiogenesisStage3Vesicles
from cellauto.rules.abiogenesis.stage4_selection import AbiogenesisStage4Selection
from cellauto.rules.natural_selection import (
    MILLER_UREY_YIELDS,
    PALETTE,
    SPECIES_NAMES,
    NaturalSelectionRule,
)


def test_miller_urey_table_aligns_with_palette():
    assert len(SPECIES_NAMES) == len(PALETTE)
    assert len(MILLER_UREY_YIELDS) == len(PALETTE)
    # Formic acid is the most abundant Miller-Urey product.
    assert SPECIES_NAMES[0] == "formic acid"
    assert MILLER_UREY_YIELDS[0] == max(MILLER_UREY_YIELDS)


def test_soup_is_dominated_by_formic_acid():
    """Weighted by Miller's yields, formic acid (palette[0]) should be the
    single most common species in a fresh soup — not an even 1/16 split."""
    rule = NaturalSelectionRule(rng=random.Random(0))
    grid = rule.init_state(40, 40)
    counts = {c: 0 for c in PALETTE}
    for row in grid.cells:
        for cell in row:
            counts[cell.color] += 1
    most_common = max(counts, key=counts.__getitem__)
    assert most_common == PALETTE[0]  # formic acid
    # And it should be a sizable plurality (yield share ~49%).
    assert counts[PALETTE[0]] / (40 * 40) > 0.3


def test_custom_palette_falls_back_to_uniform_and_does_not_crash():
    rule = NaturalSelectionRule(palette=("#000000", "#ffffff"), rng=random.Random(1))
    grid = rule.init_state(10, 10)
    for row in grid.cells:
        for cell in row:
            assert cell.color in ("#000000", "#ffffff")


def test_stage3_reports_real_cmc():
    rule = AbiogenesisStage3Vesicles(rng=random.Random(2))
    assert rule.amphiphile in AMPHIPHILE_CMC_MM
    state = rule.init_state(16, 16)
    pop = rule.population(state)
    assert pop["cmc_mM"] == round(AMPHIPHILE_CMC_MM["decanoic acid (C10)"])  # 85
    assert rule.to_config()["amphiphile"] == "decanoic acid (C10)"


def test_stage4_error_threshold_is_inverse_genome_length():
    rule = AbiogenesisStage4Selection(n_species=4, rng=random.Random(3))
    assert rule.error_threshold == 1.0 / 4
    state = rule.init_state(20, 20)
    pop = rule.population(state)
    assert pop["error_threshold_x1000"] == 250  # 1/4
    assert pop["mutation_rate_x1000"] == 20  # default 0.02


def test_stage2_reports_catalysis_level():
    """Every reaction is catalyzed, so mean catalysis per species is
    n_reactions / n_species — Kauffman's connectivity metric."""
    rule = AbiogenesisStage2RAF(n_species=8, n_reactions=16, rng=random.Random(4))
    state = rule.init_state(16, 16)
    pop = rule.population(state)
    assert pop["catalysis_level_x100"] == round(100 * 16 / 8)  # 200 == 2.0/species
