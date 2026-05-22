"""GIF export validity and grid edge cases.

Closes PHASE2_BRUTAL P2-18 (GIF export test) and P2-19 (edge cases).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from cellauto.engine import Engine
from cellauto.export import export_gif
from cellauto.rules import REGISTRY
from cellauto.rules.abiogenesis import (
    AbiogenesisStage1GrayScott,
)
from cellauto.rules.conway import ConwaysLifeRule
from cellauto.rules.natural_selection import NaturalSelectionRule

# ── GIF export validity (P2-18) ─────────────────────────────────────────────


def _build_distinct_discrete_frames(n: int, width: int, height: int) -> list[dict]:
    """Build N visibly-different discrete frames so Pillow won't dedupe them."""
    frames = []
    for i in range(n):
        shade = f"#{(20 + i * 40) % 255:02x}aa00"
        cells = [[(shade, "rect") for _ in range(width)] for _ in range(height)]
        frames.append(
            {"kind": "discrete", "width": width, "height": height, "cells": cells, "canvas_size": 120}
        )
    return frames


def _build_distinct_field_frames(n: int, width: int, height: int) -> list[dict]:
    rng = np.random.RandomState(0)
    frames = []
    for _ in range(n):
        rgb = rng.randint(0, 255, (height, width, 3)).astype(np.uint8).tolist()
        frames.append({"kind": "field", "rgb": rgb, "canvas_size": 120})
    return frames


def test_export_gif_discrete_writes_valid_file(tmp_path: Path) -> None:
    frames = _build_distinct_discrete_frames(5, 8, 8)
    out = tmp_path / "discrete.gif"
    written = export_gif(frames, out, fps=10)
    assert written == out and out.exists()

    img = Image.open(out)
    assert img.format == "GIF"
    assert img.size == (120, 120)
    assert img.n_frames == 5


def test_export_gif_field_writes_valid_file(tmp_path: Path) -> None:
    frames = _build_distinct_field_frames(4, 16, 16)
    out = tmp_path / "field.gif"
    export_gif(frames, out, fps=8)
    img = Image.open(out)
    assert img.format == "GIF"
    assert img.size == (120, 120)
    assert img.n_frames == 4


def test_export_gif_rejects_empty(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        export_gif([], tmp_path / "nope.gif", fps=8)


# ── Engine + rule edge cases (P2-19) ────────────────────────────────────────


@pytest.mark.parametrize("dim", [1, 2])
def test_engine_handles_tiny_grids(dim: int) -> None:
    """1×1 and 2×2 grids must still construct and step without crashing."""
    rule = NaturalSelectionRule()
    e = Engine(width=dim, height=dim, rule=rule, seed=1)
    for _ in range(3):
        e.step()
    assert e.step_count == 3


def test_conway_density_zero_stays_dead() -> None:
    rule = ConwaysLifeRule(initial_density=0.0)
    e = Engine(width=10, height=10, rule=rule, seed=42)
    for _ in range(5):
        e.step()
    # No live cells were seeded; Conway can't spontaneously generate them.
    pop = e.population()
    assert pop["alive"] == 0


def test_natural_selection_palette_of_one_does_not_crash() -> None:
    """v2.0's _distinct_palette_color raised IndexError on a palette of
    size 1.  v3.0 traded that crash for a silent palette[0] fallback —
    the simulation is degenerate (no colour changes ever) but it must at
    least construct, step, and report a population without raising."""
    rule = NaturalSelectionRule(palette=("#000000",))
    e = Engine(width=6, height=6, rule=rule, seed=11)
    for _ in range(5):
        e.step()
    pop = e.population()
    assert pop["amoebas"] >= 0


def test_grayscott_runs_without_seed_perturbation() -> None:
    """Stage 1 must not raise on small grids — the central perturbation
    patch (min(w, h) // 16) collapses to zero for tiny inputs."""
    rule = AbiogenesisStage1GrayScott()
    e = Engine(width=8, height=8, rule=rule, seed=2)
    for _ in range(5):
        e.step()
    assert np.isfinite(e.state.v).all()


def test_every_registered_rule_serializes_roundtrip(tmp_path: Path) -> None:
    """Each registered rule must produce a snapshot that loads back
    without crashing — this is the heaviest cross-cutting assertion the
    rule registry can support."""
    for name, cls in REGISTRY.items():
        rule = cls()
        e = Engine(width=12, height=12, rule=rule, seed=7)
        for _ in range(3):
            e.step()
        snap = tmp_path / f"{name}.json"
        e.save(snap)
        e2 = Engine.load(snap, REGISTRY)
        assert e2.rule.name == name
        assert e2.step_count == e.step_count
