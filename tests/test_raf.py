"""Tests for the Kauffman RAF (Reflexively Autocatalytic Food-generated) set
detection algorithm — the Hordijk & Steel (2004) closure (Algorithms 1 & 2,
as formalized in Hordijk 2023, arXiv:2303.01809).

These pin the two scientific corrections made to ``find_raf``:

* The closure must propagate producibility layer-by-layer from the food set;
  it cannot assume every candidate reaction's product is available up front.
  The earlier one-pass version reported false-positive RAFs for
  mutually-dependent reactions with no grounding in the food set.
* Catalysis is mandatory — the "R" (reflexively autocatalytic) requirement.
  An uncatalyzed reaction is excluded even when both reactants are producible.
"""

from __future__ import annotations

import random

from cellauto.rules.abiogenesis.science import (
    Reaction,
    ReactionNetwork,
    _closure,
    find_raf,
    random_reaction_network,
)


def test_empty_network_has_empty_raf():
    network = ReactionNetwork(n_species=3, reactions=(), food_set=frozenset({0}))
    assert find_raf(network) == frozenset()


def test_self_catalyzing_pair_forms_raf():
    """Classic minimal RAF: two reactions whose products catalyse each other,
    with reactants all in the food set.

    Food {0, 1}; r1: 0+1 -> 2 (cat 3); r2: 0+1 -> 3 (cat 2). Both reactants
    are food and each reaction's catalyst is produced by the other, so the
    pair is reflexively autocatalytic and food-generated.
    """
    r1 = Reaction(reactants=(0, 1), product=2, catalyst=3)
    r2 = Reaction(reactants=(0, 1), product=3, catalyst=2)
    network = ReactionNetwork(n_species=4, reactions=(r1, r2), food_set=frozenset({0, 1}))
    assert find_raf(network) == frozenset({r1, r2})


def test_grounded_chain_is_detected():
    """A producibility chain grounded in food. r1: 0+1 -> 2 (cat 0);
    r2: 2+0 -> 3 (cat 2). 2 comes from r1, then catalyzes r2."""
    r1 = Reaction(reactants=(0, 1), product=2, catalyst=0)
    r2 = Reaction(reactants=(2, 0), product=3, catalyst=2)
    network = ReactionNetwork(n_species=4, reactions=(r1, r2), food_set=frozenset({0, 1}))
    assert find_raf(network) == frozenset({r1, r2})


def test_reaction_with_unreachable_reactant_is_excluded():
    """A reaction whose reactant is neither food nor produced by another
    surviving reaction is pruned; the food-grounded one survives."""
    r1 = Reaction(reactants=(0, 1), product=2, catalyst=0)
    # r2 requires species 5, which nobody produces.
    r2 = Reaction(reactants=(5, 0), product=3, catalyst=0)
    network = ReactionNetwork(n_species=6, reactions=(r1, r2), food_set=frozenset({0, 1}))
    raf = find_raf(network)
    assert r1 in raf
    assert r2 not in raf


def test_ungrounded_mutual_dependency_is_not_a_raf():
    """The false positive the old one-pass closure accepted.

    rA: 10+11 -> 12 (cat 0); rB: 12+13 -> 11 (cat 0). food = {0, 10, 13}.
    Each reaction needs the *other's* product (11 / 12) as a reactant, and
    neither product is otherwise producible — so neither reaction can ever
    fire. There is no food-generated RAF. The old algorithm declared both
    products producible up front and wrongly returned {rA, rB}.
    """
    rA = Reaction(reactants=(10, 11), product=12, catalyst=0)
    rB = Reaction(reactants=(12, 13), product=11, catalyst=0)
    network = ReactionNetwork(n_species=14, reactions=(rA, rB), food_set=frozenset({0, 10, 13}))
    assert find_raf(network) == frozenset()


def test_uncatalyzed_reaction_excluded():
    """Catalysis is mandatory. r1: 0+1 -> 2 with no catalyst. Even though its
    reactants are food, an uncatalyzed reaction cannot belong to a RAF."""
    r1 = Reaction(reactants=(0, 1), product=2, catalyst=None)
    network = ReactionNetwork(n_species=3, reactions=(r1,), food_set=frozenset({0, 1}))
    assert find_raf(network) == frozenset()


def test_catalyst_must_be_producible():
    """r1: 0+1 -> 2 catalyzed by species 5, which nothing produces. Excluded
    despite producible reactants."""
    r1 = Reaction(reactants=(0, 1), product=2, catalyst=5)
    network = ReactionNetwork(n_species=6, reactions=(r1,), food_set=frozenset({0, 1}))
    assert find_raf(network) == frozenset()


def test_raf_is_closed_under_producibility():
    """The returned set is self-consistent: every reaction's reactants and
    catalyst lie in the closure of food plus the RAF's products."""
    r1 = Reaction(reactants=(0, 1), product=2, catalyst=0)
    r2 = Reaction(reactants=(2, 1), product=3, catalyst=2)
    r3 = Reaction(reactants=(3, 9), product=4, catalyst=0)  # 9 ungrounded
    network = ReactionNetwork(n_species=10, reactions=(r1, r2, r3), food_set=frozenset({0, 1}))
    raf = find_raf(network)
    producible = _closure(network.food_set, set(raf))
    for r in raf:
        assert all(reactant in producible for reactant in r.reactants)
        assert r.catalyst is not None and r.catalyst in producible
    assert r3 not in raf


def test_closure_propagates_in_layers():
    """Closure reaches species only obtainable through a chain. food = {0};
    r1: 0+0 -> 1 (cat 0); r2: 1+0 -> 2 (cat 0) yields {0, 1, 2}."""
    r1 = Reaction(reactants=(0, 0), product=1, catalyst=0)
    r2 = Reaction(reactants=(1, 0), product=2, catalyst=0)
    assert _closure(frozenset({0}), {r1, r2}) == {0, 1, 2}


def test_random_network_finds_raf_above_connectivity_threshold():
    """Kauffman 1986: above ~2 reactions per species, RAFs form spontaneously
    in most random networks. With every reaction now catalyzed, n_species=6
    and n_reactions=20 should almost always yield a non-empty RAF."""
    rng = random.Random(42)
    saw_raf = sum(
        bool(find_raf(random_reaction_network(n_species=6, n_reactions=20, food_fraction=0.5, rng=rng)))
        for _ in range(10)
    )
    assert saw_raf >= 7, f"only {saw_raf}/10 random high-connectivity nets had RAF"


def test_rendered_dynamics_are_catalysis_gated():
    """Stage 2's *displayed* dynamics must honour the RAF's defining property:
    a catalysed reaction effectively does not run where its catalyst is absent.
    The audit found the old rate was plain k·[A]·[B] regardless of catalyst, so
    the on-screen 'autocatalytic ignition' wasn't actually autocatalytic.

    Same single catalysed reaction A+B->C (catalyst K), same starting [A],[B]:
    a field with abundant K must accumulate FAR more C than a field with K=0.
    """
    import numpy as np

    from cellauto.rules.abiogenesis.science import Reaction, ReactionNetwork
    from cellauto.rules.abiogenesis.stage2_raf import AbiogenesisStage2RAF, RAFState

    # Species: 0=A, 1=B, 2=C (product), 3=K (catalyst). Food = {0,1} so A,B
    # are replenished; the only reaction is A+B->C catalysed by K.
    rxn = Reaction(reactants=(0, 1), product=2, rate_constant=0.5, catalyst=3)
    net = ReactionNetwork(n_species=4, reactions=(rxn,), food_set=frozenset({0, 1}))

    def run_with_catalyst(k_level: float) -> float:
        rule = AbiogenesisStage2RAF(n_species=4, rng=random.Random(0))
        c = np.zeros((8, 8, 4), dtype=np.float32)
        c[:, :, 0] = 0.5  # A
        c[:, :, 1] = 0.5  # B
        c[:, :, 3] = k_level  # catalyst K
        state = RAFState(concentrations=c, network=net, raf=frozenset({rxn}))
        for _ in range(30):
            state = rule.step(state)
        return float(state.concentrations[:, :, 2].sum())  # total C produced

    c_with = run_with_catalyst(1.0)
    c_without = run_with_catalyst(0.0)
    assert c_with > 0.0
    # With no catalyst, only the faint bootstrap fires → at least ~10x less C.
    assert c_without < c_with * 0.1, (
        f"reaction ran nearly as fast without its catalyst: with={c_with:.4f}, without={c_without:.4f}"
    )
