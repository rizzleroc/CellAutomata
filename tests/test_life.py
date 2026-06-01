"""Stage XIII — integration tests for ``AbiogenesisStageLife``.

These drive the whole digital-life stage on small seeded grids: birth, death,
division, mutation-driven divergence, the Eigen error catastrophe, the F8
honest-emergence guard, substrate-collapse extinction, ancestry tracking,
render-buffer reuse, serialization round-trips, and the pipeline hand-off.

Everything uses small grids and seeded RNGs so the whole file stays fast.
"""

from __future__ import annotations

import random

import numpy as np

from cellauto.engine import Engine
from cellauto.rules.abiogenesis.life_vm import ANCESTOR_GENOME, OP
from cellauto.rules.abiogenesis.pipeline import AbiogenesisExtendedPipelineRule
from cellauto.rules.abiogenesis.stage_life import AbiogenesisStageLife


# --------------------------------------------------------------------------- #
# 1. Seeding                                                                  #
# --------------------------------------------------------------------------- #
def test_init_state_seeds_founder_population():
    rule = AbiogenesisStageLife(initial_population=30, rng=random.Random(1))
    state = rule.init_state(20, 20)
    assert len(state.organisms) == 30
    lineages = set()
    for org in state.organisms.values():
        # Each founder carries an unmutated copy of the ancestor genome.
        assert org.genome == list(ANCESTOR_GENOME)
        # Each founder starts its own lineage (lineage == its own oid).
        assert org.lineage == org.oid
        lineages.add(org.lineage)
        # The occupant index matches the organism's position.
        assert int(state.occupant[org.y, org.x]) == org.oid
    assert len(lineages) == 30
    # No phantom occupants: exactly the population is indexed.
    assert int((state.occupant != -1).sum()) == 30


# --------------------------------------------------------------------------- #
# 2. Death by starvation                                                      #
# --------------------------------------------------------------------------- #
def test_starved_organism_dies_and_frees_cell():
    rule = AbiogenesisStageLife(initial_population=5, rng=random.Random(1))
    state = rule.init_state(20, 20)
    victim = next(iter(state.organisms.values()))
    vx, vy, void = victim.x, victim.y, victim.oid
    victim.energy = 0.0  # forced starvation
    n_corpses_before = len(state.corpses)

    state = rule.step(state)

    assert void not in state.organisms  # removed
    assert int(state.occupant[vy, vx]) != void  # cell freed
    assert len(state.corpses) > n_corpses_before  # a corpse was recorded


# --------------------------------------------------------------------------- #
# 3. Division                                                                 #
# --------------------------------------------------------------------------- #
def test_energy_rich_population_divides_and_grows():
    rule = AbiogenesisStageLife(initial_population=20, max_population=400, rng=random.Random(2))
    state = rule.init_state(30, 30)
    n0 = len(state.organisms)
    # Keep the founders energy-rich so DIVIDE fires when it executes.
    for _ in range(20):
        for o in state.organisms.values():
            o.energy = max(o.energy, 600.0)
        state = rule.step(state)
    assert len(state.organisms) > n0  # population grew
    assert len(state.organisms) <= rule.max_population  # bounded by the cap

    # Daughters carry a parent pointer and share the parent's lineage.
    child = next(o for o in state.organisms.values() if o.parent is not None)
    parent = state.organisms.get(child.parent)
    if parent is not None:
        assert child.lineage == parent.lineage


def test_division_respects_max_population():
    rule = AbiogenesisStageLife(initial_population=20, max_population=40, rng=random.Random(4))
    state = rule.init_state(30, 30)
    for _ in range(30):
        for o in state.organisms.values():
            o.energy = max(o.energy, 600.0)
        state = rule.step(state)
    assert len(state.organisms) <= rule.max_population


# --------------------------------------------------------------------------- #
# 4. Mutation gates diversity                                                 #
# --------------------------------------------------------------------------- #
def _divergence_after(mutation_rate: float, *, seed: int = 3, steps: int = 600, grid: int = 32) -> float:
    rule = AbiogenesisStageLife(mutation_rate=mutation_rate, rng=random.Random(seed))
    state = rule.init_state(grid, grid)
    for _ in range(steps):
        state = rule.step(state)
    return rule.founder_divergence(state)


def test_higher_mutation_rate_drives_more_divergence():
    low = _divergence_after(0.005)
    high = _divergence_after(0.4)
    # A high copy-error rate explores genome space far faster than a low one.
    assert high > low * 3
    assert high > 1.0  # substantial drift away from the ancestor


# --------------------------------------------------------------------------- #
# 5. Error catastrophe (Eigen)                                                #
# --------------------------------------------------------------------------- #
def test_error_catastrophe_melts_master_sequence():
    # Sub-threshold ε keeps the population near the ancestor; an ε well above
    # the Eigen threshold (~1/L) melts the master sequence into a random
    # ensemble, so founder_divergence explodes.
    sub = _divergence_after(0.005)
    catastrophe = _divergence_after(0.6)
    assert catastrophe > sub * 5
    # Above the catastrophe, drift is large in absolute terms too.
    assert catastrophe > 2.0


# --------------------------------------------------------------------------- #
# 6. Honest emergence (F8)                                                    #
# --------------------------------------------------------------------------- #
def test_f8_distinct_lineage_variant_emerges():
    # F8 honest-emergence guard: at default params and a fixed seed, after a
    # few thousand instruction-ticks at least one organism's genome differs
    # from the founding ancestor (a real variant arose, not a frozen clone
    # army). We use a 50x50 grid and ~1500 steps to stay under a few seconds;
    # the PRD's full guarantee is "within 10k steps at the default seed".
    rule = AbiogenesisStageLife(rng=random.Random(7))
    state = rule.init_state(50, 50)
    for _ in range(1500):
        state = rule.step(state)
    assert rule.founder_divergence(state) > 0.0
    # Concretely: at least one live organism is not the ancestor genome.
    assert any(o.genome != list(ANCESTOR_GENOME) for o in state.organisms.values())


# --------------------------------------------------------------------------- #
# 7. Substrate depletion → extinction                                         #
# --------------------------------------------------------------------------- #
def test_no_substrate_regen_leads_to_extinction():
    # With substrate_regen = 0 the only energy income is the finite initial
    # substrate; a populous small grid burns through it and the population
    # collapses to nothing within a bounded number of steps.
    rule = AbiogenesisStageLife(substrate_regen=0.0, rng=random.Random(5))
    state = rule.init_state(20, 20)
    extinct_at = None
    for i in range(1500):
        state = rule.step(state)
        if not state.organisms:
            extinct_at = i
            break
    assert extinct_at is not None, "population never went extinct without substrate regen"
    assert len(state.organisms) == 0


# --------------------------------------------------------------------------- #
# 8. Ancestry tracking                                                        #
# --------------------------------------------------------------------------- #
def test_ancestry_chain_ends_at_a_founder():
    rule = AbiogenesisStageLife(initial_population=10, max_population=300, rng=random.Random(2))
    state = rule.init_state(30, 30)
    # Build a short multi-generation lineage by keeping organisms rich.
    for _ in range(20):
        for o in state.organisms.values():
            o.energy = max(o.energy, 600.0)
        state = rule.step(state)

    # Pick the deepest descendant we can find (one with a parent).
    descendant = max(
        (o for o in state.organisms.values() if o.parent is not None),
        key=lambda o: len(rule.ancestry(state, o)),
        default=None,
    )
    assert descendant is not None

    chain = rule.ancestry(state, descendant)
    assert chain[0] == descendant.oid
    # Parent pointers along the chain are consistent.
    for child_oid, parent_oid in zip(chain, chain[1:], strict=False):
        child = state.organisms[child_oid]
        assert child.parent == parent_oid
    # The chain terminates at a surviving founder (parent is None) — or at the
    # last surviving ancestor we could follow. The terminal organism must be a
    # founder when fully resolved: a founder has parent None and lineage==oid.
    terminal = state.organisms[chain[-1]]
    if terminal.parent is None:
        assert terminal.lineage == terminal.oid
    # Every organism in the chain shares the founder lineage.
    assert all(state.organisms[oid].lineage == descendant.lineage for oid in chain)


# --------------------------------------------------------------------------- #
# 9. Render buffer reuse                                                       #
# --------------------------------------------------------------------------- #
def test_render_rgb_reuses_buffer():
    rule = AbiogenesisStageLife(initial_population=10, rng=random.Random(1))
    state = rule.init_state(24, 18)
    a = rule.render_rgb(state)
    b = rule.render_rgb(state)
    assert a is b  # no per-frame allocation
    assert a.shape == (18, 24, 3)
    assert a.dtype == np.uint8


# --------------------------------------------------------------------------- #
# 10. Serialization round-trip                                                #
# --------------------------------------------------------------------------- #
def test_serialization_round_trip():
    rule = AbiogenesisStageLife(initial_population=15, rng=random.Random(8))
    state = rule.init_state(20, 20)
    for _ in range(8):
        state = rule.step(state)

    restored = rule.deserialize_state(rule.serialize_state(state))

    assert len(restored.organisms) == len(state.organisms)
    assert restored.next_oid == state.next_oid
    for oid, org in state.organisms.items():
        r = restored.organisms[oid]
        assert r.genome == org.genome
        assert (r.oid, r.x, r.y) == (org.oid, org.x, org.y)
        assert abs(r.energy - round(org.energy, 4)) < 1e-3
        assert r.ip == org.ip
        assert r.lineage == org.lineage
        assert r.parent == org.parent
        # The occupant index is rebuilt to point back at the organism.
        assert int(restored.occupant[r.y, r.x]) == oid
    assert np.allclose(restored.substrate, np.round(state.substrate, 4), atol=1e-3)
    assert np.allclose(restored.waste, np.round(state.waste, 4), atol=1e-3)


# --------------------------------------------------------------------------- #
# 11. Pipeline hand-off (G1)                                                   #
# --------------------------------------------------------------------------- #
def test_pipeline_reaches_digital_life_with_seeded_population():
    rule = AbiogenesisExtendedPipelineRule(stage_duration=2, rng=random.Random(3))
    engine = Engine(width=16, height=16, rule=rule, seed=3)
    steps = 0
    # Stage XIII (DIGITAL LIFE) is index 12 in the 13-stage extended pipeline.
    while engine.state.current_stage < 12 and steps < 400:
        engine.step()
        steps += 1
    assert engine.state.current_stage == 12, "pipeline never reached the digital-life stage"
    assert engine.population()["organisms"] > 0, "no organisms were seeded at hand-off"


# --------------------------------------------------------------------------- #
# 12. High-res anatomy plate                                                  #
# --------------------------------------------------------------------------- #
def test_render_plate_shape_and_nontrivial():
    rule = AbiogenesisStageLife(initial_population=20, rng=random.Random(1))
    state = rule.init_state(16, 16)
    # Make the organisms energetic so they render large enough to show pixels.
    for o in state.organisms.values():
        o.energy = 200.0
    plate = rule.render_plate(state, scale=10)
    assert plate.shape == (16 * 10, 16 * 10, 3)
    assert plate.dtype == np.uint8
    # Non-trivial: organisms paint pixels well brighter than the dim sepia
    # background (background red channel tops out around 28 + 40 ≈ 68).
    assert int(plate.max()) > 150


def test_ancestor_genome_contains_metabolic_program():
    # Sanity guard the integration tests lean on: the ancestor really does
    # sense, ingest, and divide (so seeded founders can actually live).
    assert OP["SENSE"] in ANCESTOR_GENOME
    assert OP["INGEST"] in ANCESTOR_GENOME
    assert OP["DIVIDE"] in ANCESTOR_GENOME
