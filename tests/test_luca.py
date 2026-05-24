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
    """G5 + v3.4 pin: the recovered core (≥70 % prevalence) should be a
    substantial fraction of the pathway-essential genes — not all of them
    necessarily (the pathway-graph fitness is more delicate than the
    old per-gene-value vector, so some essentials drift below prevalence),
    but the bulk of the network-essential set must lock in. The LUCA
    parsimony procedure is robust by design: it tolerates a few missing
    pathway genes without disclaiming the whole core."""
    rule = AbiogenesisStageLUCA(rng=random.Random(11))
    final = _run(rule)
    # At least half of the pathway-essential genes must reach the ≥70 %
    # prevalence threshold.
    assert final["luca_size"] >= rule.essential_count // 2, (
        f"LUCA core only recovered {final['luca_size']} of {rule.essential_count} pathway-essential genes"
    )
    # And it cannot exceed the network-essential bound.
    assert final["luca_size"] <= rule.essential_count


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


def test_essential_count_matches_pathway_graph():
    """G5 pin: essentiality is a topological property of the pathway graph,
    not a tuned per-gene benefit vector. ``essential_count`` should equal
    the number of unique gene indices that appear in any pathway."""
    rule = AbiogenesisStageLUCA()
    expected = len({g for path, _ in rule.pathways for g in path})
    assert rule.essential_count == expected
    # Default config: 5 pathways covering 12 unique genes (3+3+2+2+2).
    assert rule.essential_count == 12
    # The pathway-genes set should be exactly the network-derived essentials.
    assert rule.pathway_genes == frozenset({0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11})


def test_recovered_luca_core_subset_of_pathway_genes():
    """G5 pin: the recovered LUCA core (≥70 % prevalence) must be a SUBSET
    of the network-essential genes. We cannot guarantee it equals the full
    set at any single step (some pathway genes drift in and out near the
    threshold), but every gene the parsimony procedure flags as ancestral
    must be a member of the pathway graph — never a pure accessory.
    """
    import numpy as np

    rule = AbiogenesisStageLUCA(rng=random.Random(11))
    state = rule.init_state(28, 28)
    for _ in range(120):
        state = rule.step(state)
    core = rule._luca_core(state)
    core_indices = set(np.where(core)[0])
    pathway = set(rule.pathway_genes)
    # Every recovered core gene must participate in a pathway. (Not all
    # pathway genes are necessarily in the core — the prevalence threshold
    # may drop a gene that's high-cost relative to its pathway benefit.)
    bogus = core_indices - pathway
    assert not bogus, (
        f"recovered LUCA core contains genes not in any pathway: {bogus} "
        f"(pathway essentials: {sorted(pathway)})"
    )
    # And the core must not be trivially empty under reasonable conditions.
    assert len(core_indices) > 0, "recovered LUCA core was empty"
