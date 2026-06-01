"""G1 + G10 pin: pipeline state hand-off across stage transitions.

The honest gap the v3.4 brutal audit flagged is that ``AbiogenesisPipelineRule.
promote()`` used to call ``new_rule.init_state(W, H)`` from scratch, so the
chemistry of Stage N was thrown away when promoting to Stage N+1. That made
the 12-stage "pipeline" a sequence of *isolated* simulations on a timer,
which is honesty-grade theatre, not a coupled chemistry-to-life arc.

After G1, every stage:
  - exposes ``extract_signal(state) -> np.ndarray`` returning a 2D float
    summary of its main output
  - accepts ``seed_field=np.ndarray | None`` in ``init_state()`` and biases
    its starting state by that field if provided

The pipeline's ``promote()`` and forward ``set_stage()`` extract the upstream
signal before discarding the previous state, then pass it into the new
stage's ``init_state``.

This file is the regression pin: stepping a pipeline through one promotion
must produce a downstream initial state whose field correlates with the
upstream final state. If a future change accidentally drops the hand-off,
the spatial correlation will fall to ~0 and these tests will fail.
"""

from __future__ import annotations

import random

import numpy as np

from cellauto.engine import Engine
from cellauto.rules.abiogenesis.pipeline import (
    AbiogenesisExtendedPipelineRule,
    AbiogenesisPipelineRule,
)
from cellauto.rules.abiogenesis.stage1_grayscott import AbiogenesisStage1GrayScott
from cellauto.rules.abiogenesis.stage2_raf import AbiogenesisStage2RAF


def _spatial_correlation(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r between two same-shape float arrays, flattened. Returns 0.0
    when either input is constant (no variance)."""
    af = a.astype(np.float32).flatten()
    bf = b.astype(np.float32).flatten()
    if af.std() < 1e-9 or bf.std() < 1e-9:
        return 0.0
    return float(np.corrcoef(af, bf)[0, 1])


def test_promote_extracts_and_passes_upstream_signal():
    """The five-stage canonical pipeline, two consecutive stages: after
    promotion, the new stage's initial seed must reflect the old stage's
    final field. We use Stage I (Gray-Scott) → Stage II (RAF) and check
    that the RAF's initial chemistry density positively correlates with
    Stage I's final v-field. Correlation > 0 means information flowed."""
    rule = AbiogenesisPipelineRule(
        starting_stage=1,  # start AT Gray-Scott so we control the upstream
        stage_duration=500,
        auto_promote=False,
        rng=random.Random(7),
    )
    engine = Engine(width=40, height=40, rule=rule, seed=7)
    # Let Gray-Scott form spots.
    for _ in range(200):
        engine.step()
    pre_promote_v = engine.state.inner_state.v.copy()
    # Promote to RAF.
    rule.promote(engine.state)
    post_promote_density = engine.state.inner_rule.extract_signal(engine.state.inner_state)
    r = _spatial_correlation(pre_promote_v, post_promote_density)
    assert r > 0.3, (
        f"upstream → downstream signal did not flow across promote(): r = {r:.3f}. "
        f"G1 hand-off is broken — the new stage is initialising from scratch."
    )


def test_seeded_init_outperforms_unseeded_init():
    """Negative-control style: on the same upstream Gray-Scott v field,
    initialising Stage II with the upstream signal must correlate much
    more strongly with it than initialising Stage II from scratch. This
    isolates the effect of G1's seed_field plumbing from any incidental
    similarity between unrelated Gray-Scott-then-RAF runs.
    """
    # Build a fully-developed Gray-Scott v field once.
    gs = AbiogenesisStage1GrayScott(rng=random.Random(7))
    engine = Engine(width=40, height=40, rule=gs, seed=7)
    for _ in range(200):
        engine.step()
    upstream_v = engine.state.v.copy()

    # Two initialisations of Stage II RAF: one seeded by the upstream, one not.
    seeded = AbiogenesisStage2RAF(rng=random.Random(99))
    unseeded = AbiogenesisStage2RAF(rng=random.Random(99))
    seeded_state = seeded.init_state(40, 40, seed_field=upstream_v)
    unseeded_state = unseeded.init_state(40, 40)

    r_seeded = _spatial_correlation(upstream_v, seeded.extract_signal(seeded_state))
    r_unseeded = _spatial_correlation(upstream_v, unseeded.extract_signal(unseeded_state))
    assert r_seeded > 0.5, f"seeded init didn't track upstream: r_seeded = {r_seeded:.3f}"
    # Seeded must beat unseeded — even if Gray-Scott's natural central
    # symmetry happens to weakly correlate with the unseeded init, the
    # explicit seed must show a measurable improvement.
    assert r_seeded > r_unseeded, (
        f"seed_field has no positive effect: r_seeded={r_seeded:.3f}, r_unseeded={r_unseeded:.3f}"
    )


def test_set_stage_forward_jumps_carry_signal():
    """``set_stage`` with a forward jump simulates a multi-step promotion
    and must still carry the upstream signal. Backward jumps reset (and
    are tested below)."""
    rule = AbiogenesisPipelineRule(
        starting_stage=1, stage_duration=500, auto_promote=False, rng=random.Random(11)
    )
    engine = Engine(width=40, height=40, rule=rule, seed=11)
    for _ in range(180):
        engine.step()
    pre_v = engine.state.inner_state.v.copy()
    rule.set_stage(engine.state, 2)
    post_density = engine.state.inner_rule.extract_signal(engine.state.inner_state)
    r = _spatial_correlation(pre_v, post_density)
    assert r > 0.3, f"forward set_stage() jump did not carry the upstream signal: r = {r:.3f}"


def test_set_stage_backward_resets_state():
    """A backward jump (e.g. JUMP combobox set to an earlier stage) is a
    reset — the user is rewinding, not promoting. There's no upstream to
    carry a signal from, so it's fine for the new state to be independent.
    """
    rule = AbiogenesisPipelineRule(
        starting_stage=2, stage_duration=500, auto_promote=False, rng=random.Random(11)
    )
    engine = Engine(width=40, height=40, rule=rule, seed=11)
    for _ in range(40):
        engine.step()
    # Now jump backwards to Stage 1.
    rule.set_stage(engine.state, 1)
    # Stage 1's state should be a fresh GrayScottState — no constraint on
    # correlation, but we DO require that the system actually changed
    # stage class (no AttributeError on the next step).
    assert isinstance(engine.state.inner_rule, AbiogenesisStage1GrayScott)
    engine.step()  # must not raise.


def test_extended_pipeline_handoff_through_full_arc():
    """Walk EVERY transition of the extended pipeline (not just the first two)
    and verify each one carries the upstream signal forward.

    The earlier version did `for _ in range(2)`, so it only ever sampled
    Soup→Vent and Vent→Gray-Scott and passed if *one* of those correlated —
    11 of 13 transitions were never exercised. This walks all of them and
    asserts every transition whose upstream signal is non-trivial at the
    promote() instant shows real coupling (Pearson r above a modest floor),
    so a broken handoff on any single pair now fails the suite.
    """
    rule = AbiogenesisExtendedPipelineRule(stage_duration=400, auto_promote=False, rng=random.Random(13))
    engine = Engine(width=32, height=32, rule=rule, seed=13)
    n_stages = len(rule.stage_classes)
    results: list[tuple[str, str, float, float]] = []  # (from, to, upstream_std, r)
    for _ in range(n_stages - 1):
        for _ in range(40):
            engine.step()
        from_rule = engine.state.inner_rule
        from_title = rule.stage_info_for(engine.state.current_stage).title
        prev = (
            from_rule.extract_signal(engine.state.inner_state)
            if hasattr(from_rule, "extract_signal")
            else None
        )
        rule.promote(engine.state)
        to_title = rule.stage_info_for(engine.state.current_stage).title
        post = (
            engine.state.inner_rule.extract_signal(engine.state.inner_state)
            if hasattr(engine.state.inner_rule, "extract_signal")
            else None
        )
        if prev is None or post is None or prev.shape != post.shape:
            continue
        results.append((from_title, to_title, float(prev.std()), _spatial_correlation(prev, post)))

    # Every transition whose upstream signal actually carries information at the
    # promote() instant (non-flat field) must propagate it into the next stage.
    informative = [(f, t, s, r) for (f, t, s, r) in results if s > 1e-4]
    assert informative, f"no informative transitions sampled across the arc: {results}"
    weak = [(f, t, r) for (f, t, s, r) in informative if r <= 0.15]
    assert not weak, f"these transitions dropped the upstream signal (r<=0.15): {weak}"


def test_raf_with_seed_field_starts_in_high_density_state():
    """Direct unit-test of ``AbiogenesisStage2RAF.init_state(seed_field=...)``
    without going through the pipeline. A non-trivial signal must produce a
    starting concentration field whose spatial pattern tracks the signal."""
    rule = AbiogenesisStage2RAF(rng=random.Random(5))
    signal = np.zeros((30, 30), dtype=np.float32)
    signal[5:10, 5:10] = 1.0
    signal[20:25, 20:25] = 1.0
    state = rule.init_state(30, 30, seed_field=signal)
    density = state.concentrations.sum(axis=2)
    r = _spatial_correlation(signal, density)
    assert r > 0.5, f"RAF init didn't track seed_field: r = {r:.3f}"


def test_grayscott_with_seed_field_starts_in_seeded_pattern():
    rule = AbiogenesisStage1GrayScott(rng=random.Random(5))
    signal = np.zeros((30, 30), dtype=np.float32)
    signal[10:20, 10:20] = 1.0
    state = rule.init_state(30, 30, seed_field=signal)
    r = _spatial_correlation(signal, state.v)
    # v also picks up small uniform noise, so the threshold is moderate.
    assert r > 0.4, f"Gray-Scott init didn't track seed_field: r = {r:.3f}"
