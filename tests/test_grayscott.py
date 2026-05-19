"""Tests for the Gray-Scott reaction-diffusion stage."""
import numpy as np

from cellauto.engine import Engine
from cellauto.rules.abiogenesis.science import gray_scott_step, laplacian_5pt
from cellauto.rules.abiogenesis.stage1_grayscott import AbiogenesisStage1GrayScott


def test_laplacian_zero_on_uniform_field():
    """∇² of a constant field is zero."""
    arr = np.ones((10, 10), dtype=np.float32) * 3.5
    np.testing.assert_array_almost_equal(laplacian_5pt(arr), np.zeros_like(arr))


def test_laplacian_known_value_on_peak():
    """A single peak surrounded by zeros gives Laplacian = -4 at the peak."""
    arr = np.zeros((5, 5), dtype=np.float32)
    arr[2, 2] = 1.0
    lap = laplacian_5pt(arr)
    assert lap[2, 2] == -4.0
    # The 4 neighbors should each get +1.
    assert lap[1, 2] == 1.0
    assert lap[3, 2] == 1.0
    assert lap[2, 1] == 1.0
    assert lap[2, 3] == 1.0


def test_gray_scott_step_conserves_clip_range():
    u = np.full((8, 8), 0.9, dtype=np.float32)
    v = np.full((8, 8), 0.2, dtype=np.float32)
    for _ in range(20):
        u, v = gray_scott_step(u, v, F=0.04, k=0.06)
    assert u.min() >= 0.0 and u.max() <= 1.0
    assert v.min() >= 0.0 and v.max() <= 1.0


def test_gray_scott_rule_produces_pattern():
    """Stage 1 should develop non-zero v concentration outside the seed area."""
    rule = AbiogenesisStage1GrayScott(preset="spots")
    engine = Engine(width=40, height=40, rule=rule, seed=1)
    for _ in range(50):
        engine.step()
    v = engine.state.v
    # After 50 steps × 10 substeps = 500 simulated steps, the seed has spread
    # well beyond the initial 5x5 patch in the center.
    assert (v > 0.1).sum() > 25
