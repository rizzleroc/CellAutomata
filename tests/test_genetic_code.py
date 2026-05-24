"""Origin of the genetic code — coevolution of message and code.

The scientific claims under test: with selection on peptide-target match and
copy-fidelity on both the strand and the code, (1) the mean fitness of the
population rises substantially from random initial conditions, and (2) the
code itself shifts away from the totally-random baseline as selection
amplifies any code that happens to make a more useful peptide. We deliberately
do *not* assert full code universality — that takes many more steps than the
unit-test budget allows — only that selection is genuinely acting on the code.
"""

from __future__ import annotations

import random

import numpy as np

from cellauto.rules.abiogenesis.stage_code import AbiogenesisStageGeneticCode


def _run(rule: AbiogenesisStageGeneticCode, steps: int = 80):
    state = rule.init_state(28, 28)
    initial_fit = rule.population(state)["mean_fitness_x100"]
    initial_consensus = rule.population(state)["code_consensus_x100"]
    for _ in range(steps):
        state = rule.step(state)
    final = rule.population(state)
    return initial_fit, initial_consensus, final


def test_mean_fitness_rises_under_selection_target_match():
    """Under the legacy target-match landscape: random peptides start near
    the 1/n_amino = 25 % baseline; selection rises them by ≥10 points."""
    rule = AbiogenesisStageGeneticCode(fitness_mode="target_match", rng=random.Random(7))
    initial_fit, _, final = _run(rule)
    assert initial_fit <= 35
    assert final["mean_fitness_x100"] >= initial_fit + 10


def test_mean_fitness_rises_under_selection_mj():
    """Under the G4 MJ landscape: random peptides start at ~50 % (the mean
    of the normalised contact-energy table); selection must drive them
    higher. The MJ landscape has a smaller fitness span than target-match,
    so we require a modest rise of ≥5 points."""
    rule = AbiogenesisStageGeneticCode(fitness_mode="mj_landscape", rng=random.Random(7))
    initial_fit, _, final = _run(rule)
    assert final["mean_fitness_x100"] >= initial_fit + 5, (
        f"MJ landscape did not respond to selection: "
        f"initial={initial_fit}, final={final['mean_fitness_x100']}"
    )


def test_best_strand_emerges_above_random():
    rule = AbiogenesisStageGeneticCode(fitness_mode="target_match", rng=random.Random(7))
    _, _, final = _run(rule)
    assert final["best_fitness_x100"] >= 60


def test_code_mutation_knob_controls_consensus():
    """G9 pin (replaces the vacuous tautological test that asserted only
    `0 <= x <= 100` on a [0,100]-bounded metric).

    The honest claim: the code-mutation knob is the dial that decides
    whether the population's modal codon table can converge or whether it
    is reshuffled away every replication. So:

      - `code_mutation = 0.0` (no drift): consensus must rise comfortably
        above the random baseline (1 / n_amino = 25 %).
      - `code_mutation = 1.0` (max drift): consensus must stay near random
        because every replication picks fresh code assignments.
      - The no-drift run must beat the max-drift run by a meaningful
        margin — the knob has real authority.

    Concrete numbers are deliberately loose so the test pins the *claim*,
    not the model's specific stochastic equilibrium at this seed.
    """
    no_drift = AbiogenesisStageGeneticCode(code_mutation=0.0, rng=random.Random(7))
    max_drift = AbiogenesisStageGeneticCode(code_mutation=1.0, rng=random.Random(7))
    _, _, final_no_drift = _run(no_drift, steps=120)
    _, _, final_max_drift = _run(max_drift, steps=120)
    nd = final_no_drift["code_consensus_x100"]
    md = final_max_drift["code_consensus_x100"]
    assert nd > 35, f"no-drift consensus failed to rise above the 25 % random baseline — got {nd} %"
    assert md < 50, (
        "max-drift consensus rose despite code being randomised every "
        f"replication — got {md} % (the knob isn't binding)"
    )
    assert nd > md + 5, f"code-mutation knob has no real authority: no-drift={nd} %, max-drift={md} %"


def test_serialization_round_trip():
    rule = AbiogenesisStageGeneticCode(rng=random.Random(3))
    state = rule.init_state(12, 12)
    for _ in range(5):
        state = rule.step(state)
    restored = rule.deserialize_state(rule.serialize_state(state))
    assert (restored.occupied == state.occupied).all()
    assert (restored.strand == state.strand).all()
    assert (restored.code == state.code).all()


def test_registered():
    from cellauto.rules import REGISTRY

    assert "abiogenesis-genetic-code" in REGISTRY


def test_error_threshold_formula():
    import math

    rule = AbiogenesisStageGeneticCode(strand_length=6, n_amino=4)
    assert np.isclose(rule.error_threshold, math.log(4) / 6)


def test_mj_landscape_prefers_hydrophobic_packing():
    """G4 pin: under the Miyazawa-Jernigan-style landscape, a V-V-V-V peptide
    (most-favourable hydrophobic packing) must score higher than a D-D-D-D
    peptide (like-charge clash, the worst score in MJ_CONTACT_ENERGY).
    This is the qualitative MJ physicochemical pattern.
    """
    from cellauto.rules.abiogenesis.stage_code import (
        MJ_CONTACT_ENERGY,
        AbiogenesisStageGeneticCode,
        GeneticCodeState,
    )

    rule = AbiogenesisStageGeneticCode(fitness_mode="mj_landscape", strand_length=4)
    # Force a single cell to encode V-V-V-V and another to encode D-D-D-D
    # by setting the strand to the codon that points at that amino acid
    # and the code to be the identity table.
    L = rule.strand_length
    code_identity = np.tile(np.arange(rule.n_codons, dtype=np.int8)[None, None, :], (2, 1, 1))
    # Cell (0,0) has strand all-V (amino index 3); cell (1,0) has strand all-D
    # (amino index 2). With the identity code, strand value == amino index, so
    # we set strand[0,0] = [3,3,3,3] and strand[1,0] = [2,2,2,2].
    strand = np.zeros((2, 1, L), dtype=np.int8)
    strand[0, 0, :] = 3  # V
    strand[1, 0, :] = 2  # D
    occupied = np.ones((2, 1), dtype=bool)
    state = GeneticCodeState(occupied=occupied, strand=strand, code=code_identity)
    fit = rule._fitness_field(state)
    assert fit[0, 0] > fit[1, 0], (
        f"MJ landscape failed to prefer V-V over D-D: V-V={fit[0, 0]}, D-D={fit[1, 0]}"
    )
    # The V-V chain should be near-maximum fitness; D-D near-minimum.
    assert fit[0, 0] > 0.85, f"V-V-V-V peptide should score near max: {fit[0, 0]}"
    assert fit[1, 0] < 0.15, f"D-D-D-D peptide should score near min: {fit[1, 0]}"
    # Sanity-check that the table itself encodes the MJ pattern.
    assert MJ_CONTACT_ENERGY[3, 3] < MJ_CONTACT_ENERGY[2, 2], (
        "MJ_CONTACT_ENERGY: V-V should be more favourable than D-D"
    )


def test_mj_landscape_is_default():
    """G4 commitment: the MJ landscape is the default. The v3.4 audit
    flagged the target-match landscape as 'matching a hard-coded answer
    key'; MJ is the honest replacement."""
    rule = AbiogenesisStageGeneticCode()
    assert rule.fitness_mode == "mj_landscape"
