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
    assert int(engine.state.membrane_mask.sum()) > 0, (
        "no vesicles formed at default threshold — CMC vs v-range mismatch"
    )


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
    mask[0, 0] = True  # isolated 1-cell vesicle
    mask[2, 2] = True  # another isolated 1-cell vesicle
    mask[2, 3] = True  # joined to the second one — same vesicle
    mask[4, 4] = True  # third isolated vesicle
    n = AbiogenesisStage3Vesicles._count_connected(mask)
    assert n == 3


def test_helfrich_bending_suppresses_total_curvature_energy():
    """G3 pin: turning on the Helfrich bending term (κ_b > 0) must reduce
    the total bending energy E_b ∝ Σ(∇²v)² of the lipid field — that's
    literally what the variational term is designed to minimise. We compare
    same-seed runs and assert the κ_b > 0 case has measurably lower total
    curvature energy WITHOUT erasing the CMC-threshold vesicle pattern.
    """

    from cellauto.rules.abiogenesis.science import laplacian_5pt

    sharp = AbiogenesisStage3Vesicles(kappa_bend=0.0)
    smooth = AbiogenesisStage3Vesicles(kappa_bend=0.025)
    eng_sharp = Engine(width=40, height=40, rule=sharp, seed=3)
    eng_smooth = Engine(width=40, height=40, rule=smooth, seed=3)
    for _ in range(120):
        eng_sharp.step()
        eng_smooth.step()
    # Total bending energy proxy (the actual quantity Helfrich minimises).
    e_sharp = float((laplacian_5pt(eng_sharp.state.lipid) ** 2).sum())
    e_smooth = float((laplacian_5pt(eng_smooth.state.lipid) ** 2).sum())
    assert e_smooth < e_sharp * 0.97, (
        f"Helfrich bending did not reduce total bending energy: sharp={e_sharp:.4f}, smooth={e_smooth:.4f}"
    )
    smooth_membrane = int(eng_smooth.state.membrane_mask.sum())
    assert smooth_membrane > 0, "Helfrich bending erased all vesicles — κ_b too aggressive"


def test_cmc_gate_zero_above_peak_positive_below():
    """G6 pin: the CMC threshold is the central scientific claim of the stage.
    With the threshold set far above any value the lipid field ever reaches,
    NO vesicles should form (no membrane, no protocell — the chemistry is
    just below the critical micelle concentration). With it set well below,
    vesicles must form. This pins that the threshold is genuinely gating
    self-assembly, not a cosmetic display knob.
    """
    high = AbiogenesisStage3Vesicles(cmc_threshold=10.0)  # unreachable
    eng_high = Engine(width=40, height=40, rule=high, seed=1)
    for _ in range(100):
        eng_high.step()
    assert int(eng_high.state.membrane_mask.sum()) == 0, (
        "membrane formed above an unreachable CMC — the threshold isn't gating self-assembly"
    )
    low = AbiogenesisStage3Vesicles(cmc_threshold=0.05)
    eng_low = Engine(width=40, height=40, rule=low, seed=1)
    for _ in range(100):
        eng_low.step()
    assert int(eng_low.state.membrane_mask.sum()) > 0, (
        "no membrane below the CMC — but lipid is clearly accumulating"
    )
