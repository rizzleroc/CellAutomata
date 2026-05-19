"""Tests for the Kauffman RAF (Reflexively Autocatalytic Food-generated) algorithm."""
import random

from cellauto.rules.abiogenesis.science import (
    Reaction,
    ReactionNetwork,
    find_raf,
    random_reaction_network,
)


def test_empty_network_has_empty_raf():
    network = ReactionNetwork(n_species=3, reactions=(), food_set=frozenset({0}))
    assert find_raf(network) == frozenset()


def test_self_catalyzing_pair_forms_raf():
    """Classic minimal RAF: two reactions whose products catalyse each other,
    with reactants all in the food set."""
    # Food: {0, 1}. Reactions:
    #   r1: 0 + 1 -> 2, catalyzed by 3
    #   r2: 0 + 1 -> 3, catalyzed by 2
    # Both reactants are food. Catalysts are produced by the OTHER reaction.
    # The pair forms a RAF.
    r1 = Reaction(reactants=(0, 1), product=2, catalyst=3)
    r2 = Reaction(reactants=(0, 1), product=3, catalyst=2)
    network = ReactionNetwork(n_species=4, reactions=(r1, r2),
                              food_set=frozenset({0, 1}))
    raf = find_raf(network)
    assert raf == frozenset({r1, r2})


def test_reaction_with_unreachable_reactant_is_excluded():
    """A reaction whose reactant is neither food nor produced by another
    surviving reaction must be pruned."""
    r1 = Reaction(reactants=(0, 1), product=2)
    # r2 requires species 5, which nobody produces.
    r2 = Reaction(reactants=(5, 0), product=3)
    network = ReactionNetwork(n_species=6, reactions=(r1, r2),
                              food_set=frozenset({0, 1}))
    raf = find_raf(network)
    assert r1 in raf
    assert r2 not in raf


def test_uncatalysed_reaction_kept_in_raf():
    """A reaction with no catalyst at all is fine — RAF requires *if* a
    catalyst is named, that catalyst must be reachable. Uncatalysed reactions
    are unconstrained on the catalyst axis."""
    r1 = Reaction(reactants=(0, 1), product=2, catalyst=None)
    network = ReactionNetwork(n_species=3, reactions=(r1,),
                              food_set=frozenset({0, 1}))
    assert find_raf(network) == frozenset({r1})


def test_random_network_finds_raf_above_connectivity_threshold():
    """Kauffman 1986: above ~2 reactions per species, RAFs form spontaneously
    in most random networks. With n_species=6 and n_reactions=20, we should
    almost always find a non-empty RAF."""
    rng = random.Random(42)
    saw_raf = 0
    for _ in range(10):
        network = random_reaction_network(n_species=6, n_reactions=20,
                                          food_fraction=0.5, rng=rng)
        if find_raf(network):
            saw_raf += 1
    assert saw_raf >= 7, f"only {saw_raf}/10 random high-connectivity nets had RAF"
