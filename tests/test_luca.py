"""LUCA distillation — the inferred core genome converges on the essentials.

The scientific claim under test: starting from random gene-presence bitsets,
selection on a benefit-vs-cost gene economy should drive the population
toward keeping the essential genes; the gene set common to ≥70% of surviving
lineages (`luca_size`) climbs from 0 toward the essential-gene count. This
mirrors what Weiss et al. (2016) do for real prokaryotes: the *intersection*
(threshold-relaxed) over lineages is the inferred LUCA.
"""

from __future__ import annotations

import random

from cellauto.rules.abiogenesis.stage_luca import AbiogenesisStageLUCA


def _run(rule: AbiogenesisStageLUCA, steps: int = 120):
    state = rule.init_state(28, 28)
    for _ in range(steps):
        state = rule.step(state)
    return rule.population(state)


def test_luca_converges_to_essential_core():
    rule = AbiogenesisStageLUCA(rng=random.Random(11))
    final = _run(rule)
    # The intersection across lineages should recover the essential-gene count.
    assert final["luca_size"] >= rule.essential_count - 1
    assert final["luca_size"] <= rule.essential_count + 1


def test_mean_fitness_rises():
    rule = AbiogenesisStageLUCA(rng=random.Random(11))
    state = rule.init_state(28, 28)
    initial = rule.population(state)["mean_fitness_x100"]
    for _ in range(120):
        state = rule.step(state)
    final = rule.population(state)["mean_fitness_x100"]
    assert final >= initial + 20


def test_zero_cost_lets_genomes_bloat():
    """With no maintenance cost, selection has no reason to trim deleterious
    or neutral genes, so the genome should be larger than under cost pressure."""
    costed = AbiogenesisStageLUCA(gene_cost=0.20, rng=random.Random(13))
    free = AbiogenesisStageLUCA(gene_cost=0.00, rng=random.Random(13))
    costed_run = _run(costed, steps=100)
    free_run = _run(free, steps=100)
    assert free_run["mean_genome_size_x10"] >= costed_run["mean_genome_size_x10"]


def test_serialization_round_trip():
    rule = AbiogenesisStageLUCA(rng=random.Random(3))
    state = rule.init_state(12, 12)
    for _ in range(5):
        state = rule.step(state)
    restored = rule.deserialize_state(rule.serialize_state(state))
    assert (restored.occupied == state.occupied).all()
    assert (restored.genome == state.genome).all()


def test_registered():
    from cellauto.rules import REGISTRY

    assert "abiogenesis-luca" in REGISTRY


def test_essential_count_matches_gene_values():
    rule = AbiogenesisStageLUCA()
    assert rule.essential_count == sum(1 for v in rule.gene_values if v > 1.0)
    assert rule.essential_count == 6  # default config
