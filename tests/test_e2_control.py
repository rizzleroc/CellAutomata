"""Tests for the E2 control (null-experiment) twin diagrams.

Pins ``render_control`` in ``cellauto.diagrams``: the CONTROL/null twin of
each stage's apparatus diagram. Dispatch mirrors ``render_apparatus`` —
rule-name is the primary key, ``stage_index`` (0-4) is the fallback. Also
guards the just-fixed size-robustness bug in ``render_rna_world`` (and, by
the differ-from-apparatus test, every apparatus renderer at 336x190).
"""

import pytest
from PIL import Image

from cellauto.diagrams import (
    _CONTROL_RENDERERS_BY_RULE_NAME,
    render_apparatus,
    render_control,
)

# Canonical list of the 12 abiogenesis rule names the control twins cover.
RULE_NAMES = [
    "abiogenesis-stage0-soup",
    "abiogenesis-stage1-grayscott",
    "abiogenesis-stage2-raf",
    "abiogenesis-stage3-vesicles",
    "abiogenesis-stage4-selection",
    "abiogenesis-hydrothermal-vent",
    "abiogenesis-mineral-catalysis",
    "abiogenesis-homochirality",
    "abiogenesis-rna-world",
    "abiogenesis-genetic-code",
    "abiogenesis-coacervate",
    "abiogenesis-luca",
]


def test_control_rule_name_list_matches_registry():
    """The hardcoded list must match the canonical dispatch dict keys exactly."""
    assert set(RULE_NAMES) == set(_CONTROL_RENDERERS_BY_RULE_NAME)
    assert len(RULE_NAMES) == 12


def test_render_control_all_rule_names_correct_size():
    """Each rule name renders a PIL Image at the requested + default sizes."""
    for rn in RULE_NAMES:
        small = render_control(0, 336, 190, rule_name=rn)
        assert isinstance(small, Image.Image), rn
        assert small.size == (336, 190), rn
        # Default size path.
        default = render_control(0, rule_name=rn)
        assert isinstance(default, Image.Image), rn
        assert default.size == (640, 320), rn


def test_render_control_index_fallback():
    """Indices 0-4 with no rule_name use the canonical control fallback."""
    for i in range(5):
        img = render_control(i, 336, 190)
        assert isinstance(img, Image.Image), i
        assert img.size == (336, 190), i
    # Out-of-range index with no rule_name → None.
    assert render_control(99, 336, 190) is None


def test_render_control_unknown_rule_name_returns_none_or_fallback():
    """No rule-name match and no index fallback → None."""
    assert render_control(99, 336, 190, rule_name="not-a-real-rule") is None


def test_render_control_differs_from_apparatus():
    """The control plate must look different from its experiment counterpart.

    Compared at the default 640x320 (every apparatus renderer is healthy
    there); the small-size apparatus health is pinned separately below.
    """
    for rn in RULE_NAMES:
        control = render_control(0, 640, 320, rule_name=rn)
        apparatus = render_apparatus(0, 640, 320, rule_name=rn)
        assert isinstance(control, Image.Image), rn
        assert isinstance(apparatus, Image.Image), rn
        assert control.size == apparatus.size == (640, 320), rn
        assert control.tobytes() != apparatus.tobytes(), rn


# Small canvas sizes the "How it works" dialog can request. All 12 apparatus
# renderers must survive each without raising and return the exact size — the
# coordinate-scaling fix (render_homochirality / render_genetic_code /
# render_coacervate, joining the already-fixed render_rna_world) makes this a
# strict pass for every renderer at every size.
_SMALL_SIZES = [(336, 190), (300, 160), (220, 140)]


@pytest.mark.parametrize("rule_name", RULE_NAMES)
@pytest.mark.parametrize("size", _SMALL_SIZES)
def test_render_apparatus_renders_at_small_size(rule_name, size):
    """Every apparatus renderer must survive the dialog's small-size requests.

    Pins the size-robustness contract for all 12 apparatus diagrams at the
    dialog's 336x190 and two tighter sizes. No renderer may raise or return a
    mis-sized image (previously render_homochirality, render_genetic_code and
    render_coacervate inverted a box rectangle at small widths).
    """
    w, h = size
    img = render_apparatus(0, w, h, rule_name=rule_name)
    assert isinstance(img, Image.Image), (rule_name, size)
    assert img.size == (w, h), (rule_name, size)


def test_render_control_deterministic():
    """All 12 control renderers must be byte-stable across calls (no randomness)."""
    for rn in RULE_NAMES:
        a = render_control(0, 336, 190, rule_name=rn)
        b = render_control(0, 336, 190, rule_name=rn)
        assert a.tobytes() == b.tobytes(), rn


def test_render_apparatus_rna_world_small_size_regression():
    """Explicit guard for the just-fixed render_rna_world small-size bug.

    The RNA-world apparatus must render at a sweep of sizes — including the
    dialog's 336x190 — each returning a correctly-sized Image without raising.
    """
    sizes = [(336, 190), (300, 160), (256, 256), (640, 320)]
    for w, h in sizes:
        img = render_apparatus(8, w, h, rule_name="abiogenesis-rna-world")
        assert isinstance(img, Image.Image), (w, h)
        assert img.size == (w, h), (w, h)
