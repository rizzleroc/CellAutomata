"""Channel B — the "Day in the Life" narrative compositor (v4.1).

Pins for ``cellauto.channel.NarrativeChannel``:
  1. Identity when disabled — compose() returns the base frame unchanged.
  2. Enabled changes pixels — compose() differs from the base but keeps shape +
     dtype (uint8) and never mutates the input.
  3. Resolution-independence — shape/dtype preserved at 600, a small non-600
     size, and a larger hi-res size.
  4. reduced_motion freezes _phase under tick(); without it, tick() advances.
  5. Never raises across every mood/stage when enabled.
"""

from __future__ import annotations

import numpy as np

from cellauto.channel import NarrativeChannel
from cellauto.character import MOODS


def _frame(h: int, w: int | None = None, seed: int = 0) -> np.ndarray:
    """A deterministic synthetic SEM-ish base frame (no Tk / real renderer)."""
    w = h if w is None else w
    return np.random.default_rng(seed).integers(0, 256, (h, w, 3), dtype=np.uint8)


# ── Pin 1 — identity when disabled ──────────────────────────────────────────


def test_identity_when_disabled():
    chan = NarrativeChannel(size=600)
    assert chan.enabled is False  # default
    frame = _frame(600)
    out = chan.compose(frame)
    assert np.array_equal(out, frame)


def test_disabled_returns_same_object():
    """When disabled compose is the literal identity (scaffold guard)."""
    chan = NarrativeChannel(size=600)
    frame = _frame(600)
    assert chan.compose(frame) is frame


# ── Pin 2 — enabled changes pixels, preserves shape/dtype, no mutation ───────


def test_enabled_changes_pixels_same_shape_dtype():
    chan = NarrativeChannel(size=600)
    chan.set_enabled(True)
    chan.set_stage(0, 12)
    frame = _frame(600)
    base = frame.copy()
    out = chan.compose(frame)
    assert out.shape == frame.shape
    assert out.dtype == np.uint8
    assert not np.array_equal(out, frame), "enabled overlay should change pixels"
    # Input must not be mutated.
    assert np.array_equal(frame, base)


# ── Pin 3 — resolution independence ─────────────────────────────────────────


def test_shape_dtype_preserved_at_multiple_sizes():
    for size in (600, 320, 900):
        chan = NarrativeChannel(size=size)
        chan.set_enabled(True)
        chan.set_stage(4, 12)
        frame = _frame(size, seed=size)
        out = chan.compose(frame)
        assert out.shape == (size, size, 3)
        assert out.dtype == np.uint8
        assert not np.array_equal(out, frame)


def test_non_square_frame_preserved():
    chan = NarrativeChannel(size=600)
    chan.set_enabled(True)
    chan.set_stage(2, 12)
    frame = _frame(480, 640)
    out = chan.compose(frame)
    assert out.shape == (480, 640, 3)
    assert out.dtype == np.uint8


# ── Pin 4 — reduced_motion freezes the clock ────────────────────────────────


def test_reduced_motion_freezes_phase_under_tick():
    chan = NarrativeChannel(size=600)
    chan.set_reduced_motion(True)
    start = chan._phase
    for _ in range(10):
        chan.tick()
    assert chan._phase == start, "reduced motion must freeze the phase"


def test_tick_advances_phase_when_not_reduced():
    chan = NarrativeChannel(size=600)
    chan.set_reduced_motion(False)
    start = chan._phase
    chan.tick()
    assert chan._phase != start, "tick should advance the phase"
    # ~4 s cycle at dt=0.05 → 0.0125 per tick.
    assert abs(chan._phase - (start + 0.05 / 4.0)) < 1e-9


def test_tick_wraps_modulo_one():
    chan = NarrativeChannel(size=600)
    chan._phase = 0.99
    chan.tick(dt=0.1)  # +0.025 → 1.015 % 1.0 == 0.015
    assert 0.0 <= chan._phase < 1.0


# ── Pin 5 — never raises across moods/stages ────────────────────────────────


def test_never_raises_across_all_stages_when_enabled():
    frame = _frame(240, seed=7)
    for stage in range(12):
        chan = NarrativeChannel(size=240)
        chan.set_enabled(True)
        chan.set_stage(stage, 12)
        # Advance the clock to exercise the typewriter / blink phases.
        for _ in range(stage):
            chan.tick()
        out = chan.compose(frame)
        assert out.shape == frame.shape
        assert out.dtype == np.uint8


def test_every_mood_renders_without_error():
    """Drive each mood through a hand-built single-beat script-free path by
    pointing stages at beats; all DayBeat moods come from MOODS."""
    frame = _frame(200, seed=3)
    # Sanity: the channel's beats cover the known mood vocabulary.
    moods_seen = set()
    for stage in range(12):
        chan = NarrativeChannel(size=200)
        chan.set_enabled(True)
        chan.set_stage(stage, 12)
        beat = chan._script.beat_for(stage, pipeline_len=12)
        moods_seen.add(beat.mood)
        out = chan.compose(frame)
        assert out.dtype == np.uint8
    assert moods_seen <= set(MOODS)


def test_deterministic_same_inputs():
    frame = _frame(256, seed=11)
    a = NarrativeChannel(size=256)
    a.set_enabled(True)
    a.set_stage(6, 12)
    b = NarrativeChannel(size=256)
    b.set_enabled(True)
    b.set_stage(6, 12)
    assert np.array_equal(a.compose(frame), b.compose(frame))


def test_palette_switch_renders():
    frame = _frame(300, seed=5)
    chan = NarrativeChannel(size=300)
    chan.set_enabled(True)
    chan.set_stage(9, 12)
    chan.set_palette("cool-mono")
    out = chan.compose(frame)
    assert out.shape == frame.shape
    assert out.dtype == np.uint8
