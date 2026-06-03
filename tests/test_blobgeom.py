"""Headless tests for the living-colony blob geometry (no Tk/display needed)."""

from __future__ import annotations

import math

from cellauto.blobgeom import BLOB_N, blob_points, gaze_offset


def test_blob_points_count_and_determinism():
    a = blob_points(10.0, 10.0, 5.0, 5.0, seed=1234, phase=0.3)
    b = blob_points(10.0, 10.0, 5.0, 5.0, seed=1234, phase=0.3)
    assert len(a) == BLOB_N
    assert a == b  # pure function of its inputs
    # A different seed gives a different membrane signature.
    assert blob_points(10.0, 10.0, 5.0, 5.0, seed=1) != a


def test_blob_points_radius_is_bounded_by_wobble():
    cx = cy = 0.0
    r = 8.0
    wobble = 0.12
    pts = blob_points(cx, cy, r, r, seed=42, phase=1.1, wobble=wobble)
    # The wobble factor is 1 + wobble*w/1.5 with |w| <= 1.5, so the radius stays
    # within +/- wobble of the base radius. Allow a hair of float slack.
    lo, hi = r * (1.0 - wobble) - 1e-9, r * (1.0 + wobble) + 1e-9
    for x, y in pts:
        d = math.hypot(x - cx, y - cy)
        assert lo <= d <= hi


def test_blob_membrane_motion_is_non_degenerate():
    # Advancing phase must actually move the membrane (otherwise it's static).
    p0 = blob_points(0.0, 0.0, 6.0, 6.0, seed=7, phase=0.0)
    p1 = blob_points(0.0, 0.0, 6.0, 6.0, seed=7, phase=0.9)
    moved = max(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(p0, p1))
    assert moved > 1e-3


def test_gaze_offset_stays_inside_eye():
    max_off = 2.5
    for seed in (0, 17, 255, 4096, 65535):
        for frame in range(0, 400, 3):
            dx, dy = gaze_offset(frame, seed, max_off)
            assert math.hypot(dx, dy) <= max_off + 1e-9


def test_gaze_offset_deterministic_and_wanders():
    assert gaze_offset(123, 9, 3.0) == gaze_offset(123, 9, 3.0)
    samples = {gaze_offset(f, 9, 3.0) for f in range(0, 200, 5)}
    assert len(samples) > 5  # it actually moves over time


def test_gaze_offset_clamps_negative_max():
    # A degenerate (negative) eye budget must not produce an outward pupil.
    assert gaze_offset(50, 3, -1.0) == (0.0, 0.0)
