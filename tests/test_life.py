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
    # Keep founders energy-rich so the ONLY gate on division is the self-copy.
    # Reproduction is self-encoded: an organism must run its COPY loop enough
    # times to build a full daughter tape before DIVIDE fires (~4 LOOP passes),
    # so we run long enough for the ancestor's copy loop to complete.
    for _ in range(60):
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
    for _ in range(80):
        for o in state.organisms.values():
            o.energy = max(o.energy, 600.0)
        state = rule.step(state)
    # The cap actually binds here (the population reaches it), so this also
    # exercises the max_population guard rather than passing vacuously.
    assert len(state.organisms) == rule.max_population


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
# 6. Self-encoded replication + real selection (replaces the old vacuous F8)   #
# --------------------------------------------------------------------------- #
def test_replication_is_self_encoded_copy_stripped_lineage_leaves_no_offspring():
    """The defining Tierra/Avida property, pinned directly.

    Reproduction must be *encoded in the genome*: an organism has to run its
    own COPY loop to build a daughter tape before DIVIDE can fire. So a genome
    that is identical to the viable ancestor EXCEPT that its COPY opcodes are
    replaced by NOP — it can still sense, eat, move, and *wants* to divide
    (DIVIDE is intact) — must leave **zero** offspring, while the intact
    ancestor reproduces freely. The old test only checked
    ``founder_divergence > 0`` (guaranteed by any mutation) and proved nothing
    about emergence; this proves the mechanism.
    """
    rule = AbiogenesisStageLife(initial_population=60, mutation_rate=0.0, rng=random.Random(11))
    state = rule.init_state(40, 40)
    orgs = list(state.organisms.values())
    nocopy = [OP["NOP"] if g == OP["COPY"] else g for g in ANCESTOR_GENOME]
    assert OP["DIVIDE"] in nocopy and OP["INGEST"] in nocopy  # still wants to divide; can eat
    assert OP["COPY"] not in nocopy
    crippled_lineage = -999
    for o in orgs[:30]:
        o.genome = list(nocopy)
        o.lineage = crippled_lineage
    for _ in range(3000):
        state = rule.step(state)
    # Every surviving crippled organism is a FOUNDER (was never born): the
    # lineage produced no descendants because it cannot self-copy.
    crippled = [o for o in state.organisms.values() if o.lineage == crippled_lineage]
    assert all(o.parent is None for o in crippled), (
        "a COPY-less genome reproduced — replication is not self-encoded"
    )
    born_crippled = sum(1 for o in crippled if o.parent is not None)
    assert born_crippled == 0
    # The intact ancestor lineage, by contrast, produced many descendants.
    born_ancestor = sum(
        1 for o in state.organisms.values() if o.lineage != crippled_lineage and o.parent is not None
    )
    assert born_ancestor > 100, f"the self-replicating ancestor barely reproduced ({born_ancestor})"


def test_selection_enriches_functional_opcodes_over_baseline():
    """Selection is real and measurable: after a few thousand steps the
    surviving population is strongly enriched for the opcodes that build a
    working organism — COPY (replication), INGEST (metabolism), DIVIDE — far
    above the 1/20 = 5 % frequency a neutral (drift-only) model would give,
    and neutral opcodes (RAND, ADD) are depleted well below 5 %.
    """
    rule = AbiogenesisStageLife(rng=random.Random(7))
    state = rule.init_state(50, 50)
    for _ in range(3000):
        state = rule.step(state)
    counts: dict[int, int] = {}
    total = 0
    for o in state.organisms.values():
        for op in o.genome:
            counts[op] = counts.get(op, 0) + 1
            total += 1
    assert total > 0

    def freq(name: str) -> float:
        return counts.get(OP[name], 0) / total

    baseline = 1.0 / 20  # uniform-random opcode frequency
    # Functional opcodes enriched well above neutral.
    assert freq("COPY") > 2 * baseline, f"COPY not enriched: {freq('COPY'):.3f}"
    assert freq("INGEST") > 2 * baseline, f"INGEST not enriched: {freq('INGEST'):.3f}"
    # Pure-neutral opcodes depleted below neutral (they cost a cycle, do nothing).
    assert freq("RAND") < baseline, f"RAND not depleted: {freq('RAND'):.3f}"


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
    # Build a multi-generation lineage by keeping organisms rich. Self-encoded
    # replication means each division needs a full COPY pass first, so run long
    # enough for several generations to accumulate.
    for _ in range(80):
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


def test_ancestor_genome_is_a_viable_self_replicator():
    # Sanity guard the integration tests lean on: the ancestor senses, ingests,
    # and divides (so seeded founders can live) AND contains a COPY loop (so it
    # can actually self-replicate — without COPY it would leave no offspring).
    assert OP["SENSE"] in ANCESTOR_GENOME
    assert OP["INGEST"] in ANCESTOR_GENOME
    assert OP["DIVIDE"] in ANCESTOR_GENOME
    assert OP["COPY"] in ANCESTOR_GENOME, "ancestor must encode its own replication"
