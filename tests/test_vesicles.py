"""Tests for Stage 3 — vesicle formation.

Regression for the v3.0 smoke catch where the default CMC threshold was set
above the v-concentration range the underlying Gray-Scott PDE actually
produces, so vesicles never formed. The fix calibrated the default
threshold; this test pins it.
"""
from cellauto.engine import Engine
from cellauto.rules.abiogenesis.science import vesicle_indicator
from cellauto.rules.abiogenesis.stage3_vesicles import AbiogenesisStage3Vesicles


def test_default_threshold_actually_forms_vesicles():
    """At default parameters, vesicles should form within 100 steps. If this
    fails, the CMC threshold is miscalibrated against the GS v range."""
    rule = AbiogenesisStage3Vesicles()
    engine = Engine(width=40, height=40, rule=rule, seed=1)
    for _ in range(100):
        engine.step()
    assert int(engine.state.membrane_mask.sum()) > 0, \
        "no vesicles formed at default threshold — CMC vs v-range mismatch"


def test_vesicle_indicator_threshold():
    import numpy as np
    v = np.array([[0.1, 0.4, 0.6], [0.3, 0.5, 0.7]], dtype=np.float32)
    mask = vesicle_indicator(v, threshold=0.5)
    expected = np.array([[False, False, True], [False, True, True]])
    assert (mask == expected).all()


def test_vesicle_count_zero_initially():
    rule = AbiogenesisStage3Vesicles()
    engine = Engine(width=20, height=20, rule=rule, seed=1)
    pop = engine.population()
    assert pop["vesicles"] == 0
    assert pop["membrane_cells"] == 0


def test_connected_components_counts_separate_regions():
    import numpy as np
    mask = np.zeros((5, 5), dtype=bool)
    mask[0, 0] = True            # isolated 1-cell vesicle
    mask[2, 2] = True            # another isolated 1-cell vesicle
    mask[2, 3] = True            # joined to the second one — same vesicle
    mask[4, 4] = True            # third isolated vesicle
    n = AbiogenesisStage3Vesicles._count_connected(mask)
    assert n == 3
