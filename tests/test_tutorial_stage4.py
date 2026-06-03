"""Guard: the Stage-4 tutorial copy must track the shipped science.

v3.1 replaced the Stage-4 placeholder fitness with the genuine Eigen-Schuster
hypercycle (see cellauto/rules/abiogenesis/stage4_selection.py). The tutorial
must describe that and must not resurrect the old "Shannon entropy x total
concentration" placeholder string (PRD.md v3.2 residual nit).
"""

from __future__ import annotations

from cellauto.tutorial import tutorial_for


def test_stage4_tutorial_describes_hypercycle_not_placeholder():
    joined = " ".join(tutorial_for("abiogenesis-stage4-selection")).lower()
    assert "hypercycle" in joined
    assert "shannon" not in joined
