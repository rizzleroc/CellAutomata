"""Tests for the v4.1 hi-res module (``cellauto.hires``).

Covers the supersample live path and the PNG/GIF export helpers. Everything is
pure numpy + Pillow, so the suite runs headlessly; file outputs go to
``tmp_path`` so nothing is left behind.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from cellauto.hires import (
    RenderScale,
    export_frame_png,
    export_hires_gif,
    export_hires_png,
    supersample,
)


def _flat(value: int = 128):
    """A compose_at factory returning a constant (n, n, 3) uint8 frame."""

    def compose_at(n: int) -> np.ndarray:
        return np.full((n, n, 3), value, np.uint8)

    return compose_at


# ── RenderScale ────────────────────────────────────────────────────────────


def test_render_scale_render_px():
    assert RenderScale(2).render_px(600) == 1200


def test_render_scale_rejects_zero_factor():
    with pytest.raises(ValueError):
        RenderScale(factor=0)


# ── supersample ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("factor", [1, 2, 3])
def test_supersample_shape_and_compose_call(factor):
    display = 64
    seen: list[int] = []

    def compose_at(n: int) -> np.ndarray:
        seen.append(n)
        return np.full((n, n, 3), 128, np.uint8)

    out = supersample(compose_at, display, factor)
    assert out.shape == (display, display, 3)
    assert out.dtype == np.uint8
    # compose_at must have been invoked at the supersampled edge length.
    assert seen == [display * factor]


def test_supersample_rejects_factor_zero():
    with pytest.raises(ValueError):
        supersample(_flat(), 64, 0)


def test_supersample_gradient_is_valid_downsample():
    display = 50
    factor = 3

    def gradient(n: int) -> np.ndarray:
        ramp = np.linspace(0, 255, n, dtype=np.uint8)
        frame = np.repeat(ramp[None, :, None], n, axis=0)
        return np.repeat(frame, 3, axis=2)

    out = supersample(gradient, display, factor)
    assert out.shape == (display, display, 3)
    assert out.dtype == np.uint8
    assert out.min() >= 0
    assert out.max() <= 255


def test_supersample_factor_one_passthrough():
    out = supersample(_flat(200), 32, 1)
    assert out.shape == (32, 32, 3)
    assert out.dtype == np.uint8
    assert int(out[0, 0, 0]) == 200


# ── export_frame_png ───────────────────────────────────────────────────────


def test_export_frame_png_roundtrip(tmp_path):
    rng = np.random.default_rng(2026)
    rgb = rng.integers(0, 256, size=(40, 24, 3), dtype=np.uint8)
    path = tmp_path / "frame.png"
    export_frame_png(rgb, str(path))
    assert path.exists()
    with Image.open(path) as img:
        assert img.size == (24, 40)  # PIL is (W, H)
        assert np.array_equal(np.array(img.convert("RGB")), rgb)


def test_export_frame_png_rejects_2d():
    with pytest.raises(ValueError):
        export_frame_png(np.zeros((10, 10), np.uint8), "unused.png")


def test_export_frame_png_creates_parent_dir(tmp_path):
    nested = tmp_path / "a" / "b" / "frame.png"
    export_frame_png(np.zeros((8, 8, 3), np.uint8), str(nested))
    assert nested.exists()


# ── export_hires_png ───────────────────────────────────────────────────────


def test_export_hires_png_composes_at_size(tmp_path):
    seen: list[int] = []

    def compose_at(n: int) -> np.ndarray:
        seen.append(n)
        return np.full((n, n, 3), 64, np.uint8)

    path = tmp_path / "hires.png"
    export_hires_png(compose_at, str(path), 128)
    assert seen == [128]
    with Image.open(path) as img:
        assert img.size == (128, 128)


# ── export_hires_gif ───────────────────────────────────────────────────────


def test_export_hires_gif_multiframe(tmp_path):
    frames = [np.full((16, 16, 3), v, np.uint8) for v in (0, 100, 200)]
    path = tmp_path / "anim.gif"
    export_hires_gif(frames, str(path), fps=10.0)
    assert path.exists()
    with Image.open(path) as img:
        assert img.n_frames >= 2


def test_export_hires_gif_rejects_empty():
    with pytest.raises(ValueError):
        export_hires_gif([], "unused.gif")


def test_export_hires_gif_rejects_mismatched_shapes():
    frames = [
        np.zeros((16, 16, 3), np.uint8),
        np.zeros((8, 8, 3), np.uint8),
    ]
    with pytest.raises(ValueError):
        export_hires_gif(frames, "unused.gif")
