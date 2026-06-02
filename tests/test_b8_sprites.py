"""B8 regression tests — Stage 0 sprite emission + LUT-ramp sprite tint.

Pins the v4.0.4 "B8" work:

  (a) The SEM sprite compositor (``load_sprite`` / ``composite_sprites``) now
      tints each sprite through the palette LUT ramp (black=lut[110],
      white=lut[250]) so opaque pixels floor at a mid stop instead of pure
      black, pulls the source alpha back to 0.9, and draws a blurred,
      down-right-offset contact shadow under each pasted sprite.

  (b) Stage 0 (primordial soup) re-emits sprites via the new
      ``AbiogenesisStage0Soup.render_sprites`` — protocells from ``is_ameba``
      cells, granules from ``is_new``/settled cells, capped at 120 and
      deterministic.

Tests are plain functions in the existing ``tests/test_sem_*`` style: numpy
assertions, an autouse fixture clearing ``_SPRITE_CACHE``, and a Tk-free
``_FakeCanvas`` / ``_make_sem`` helper pattern copied from test_sem_renderer.
"""

from __future__ import annotations

import numpy as np
import pytest

from cellauto.engine import Engine
from cellauto.grid import Grid
from cellauto.renderer_sem import (
    _SPRITE_CACHE,
    PALETTE_COOL_MONO,
    PALETTE_WARM_SEPIA,
    SemRenderer,
    composite_sprites,
    load_sprite,
)
from cellauto.rules.abiogenesis.stage0_soup import AbiogenesisStage0Soup
from cellauto.rules.abiogenesis.stage3_vesicles import AbiogenesisStage3Vesicles

_STAGE0_ASSETS = {"stage0/granule.png", "stage0/protocell.png"}


class _FakeCanvas:
    """Tk-free stand-in (same surface as test_sem_renderer's _FakeCanvas)."""

    def __init__(self) -> None:
        self.image = None
        self.calls: list[tuple[str, tuple, dict]] = []

    def delete(self, *args, **kwargs):
        self.calls.append(("delete", args, kwargs))

    def create_image(self, *args, **kwargs) -> int:
        self.calls.append(("create_image", args, kwargs))
        return 1

    def itemconfigure(self, *args, **kwargs):
        self.calls.append(("itemconfigure", args, kwargs))


def _make_sem(canvas_size: int = 256, palette: str = PALETTE_WARM_SEPIA) -> SemRenderer:
    """Chrome-bearing renderer suitable for headless compose() tests."""
    sr = SemRenderer(canvas=_FakeCanvas(), canvas_size=canvas_size, palette=palette)
    sr.width = 20
    sr.height = 20
    return sr


@pytest.fixture(autouse=True)
def _clear_sprite_cache():
    _SPRITE_CACHE.clear()
    yield
    _SPRITE_CACHE.clear()


def _soup_state(steps: int = 8, w: int = 40, h: int = 30, seed: int = 1):
    """Drive a Stage-0 soup engine and return (rule, state)."""
    rule = AbiogenesisStage0Soup()
    eng = Engine(width=w, height=h, rule=rule, seed=seed)
    for _ in range(steps):
        eng.step()
    return eng.rule, eng.state


# ── 1 — render_sprites emits well-formed tuples ────────────────────────────


def test_stage0_render_sprites_returns_valid_tuples():
    rule, state = _soup_state(steps=8, w=40, h=30, seed=1)
    sprites = rule.render_sprites(state)

    assert isinstance(sprites, list)
    # The soup is fully populated, so SOME sprites must be emitted.
    assert len(sprites) > 0, "fully-populated soup emitted no sprites"
    assert len(sprites) <= 120, f"sprite cap exceeded: {len(sprites)}"

    for item in sprites:
        assert isinstance(item, tuple) and len(item) == 4
        sx, sy, name, scale = item
        assert isinstance(sx, int)
        assert isinstance(sy, int)
        assert isinstance(name, str)
        assert isinstance(scale, float)
        assert name in _STAGE0_ASSETS, f"unexpected asset {name!r}"
        assert 0 <= sx < state.width, f"x={sx} out of [0,{state.width})"
        assert 0 <= sy < state.height, f"y={sy} out of [0,{state.height})"
        assert scale > 0.0


# ── 2 — render_sprites is deterministic for a fixed state ──────────────────


def test_stage0_render_sprites_deterministic():
    rule, state = _soup_state(steps=8, w=40, h=30, seed=1)
    a = rule.render_sprites(state)
    b = rule.render_sprites(state)
    assert a == b


# ── 3 — empty / zero-size grid → [] ────────────────────────────────────────


def test_stage0_render_sprites_empty_grid():
    rule = AbiogenesisStage0Soup()
    empty = Grid(width=0, height=0, cells=[])
    assert rule.render_sprites(empty) == []


# ── 4 — Stage-0 sprites visibly composite into the SEM frame ───────────────


def test_compose_with_stage0_sprites_differs_from_without():
    rule, state = _soup_state(steps=8, w=40, h=30, seed=1)
    rgb = rule.render_rgb(state)
    sprites = rule.render_sprites(state)
    assert sprites, "need a non-empty sprite list to prove compositing"

    sr = _make_sem(canvas_size=256)
    sr.width, sr.height = state.width, state.height

    plain = sr.compose(rgb)
    composed = sr.compose(rgb, sprites=sprites)

    assert plain.shape == composed.shape
    diff = np.abs(plain.astype(np.int64) - composed.astype(np.int64)).sum()
    assert diff > 0, "stage-0 sprites did not change any pixels"


# ── 5 — sprite compose is byte-deterministic ───────────────────────────────


def test_compose_with_stage0_sprites_deterministic():
    rule, state = _soup_state(steps=8, w=40, h=30, seed=1)
    rgb = rule.render_rgb(state)
    sprites = rule.render_sprites(state)

    sr = _make_sem(canvas_size=256)
    sr.width, sr.height = state.width, state.height

    out_a = sr.compose(rgb, sprites=sprites)
    out_b = sr.compose(rgb, sprites=sprites)
    assert np.array_equal(out_a, out_b)


# ── 6 — sprite tint floors at a mid stop, differs per palette ──────────────


def test_load_sprite_tint_in_palette_range():
    warm = load_sprite("stage0/granule.png", PALETTE_WARM_SEPIA)
    cool = load_sprite("stage0/granule.png", PALETTE_COOL_MONO)
    assert warm is not None and cool is not None
    assert warm.mode == "RGBA"

    warm_arr = np.asarray(warm)
    cool_arr = np.asarray(cool)

    # New ramp floors the shadow at lut[110], so no opaque pixel is pure black.
    opaque = warm_arr[..., 3] > 200
    assert opaque.any(), "granule sprite has no opaque pixels to check"
    opaque_rgb = warm_arr[..., :3][opaque]
    black = (opaque_rgb == 0).all(axis=-1)
    assert not black.any(), "found a fully-black opaque pixel (ramp floor missing)"
    # The opaque body's minimum luminance is genuinely above zero.
    lum = 0.2126 * opaque_rgb[..., 0] + 0.7152 * opaque_rgb[..., 1] + 0.0722 * opaque_rgb[..., 2]
    assert lum.min() > 0.0

    # Alpha pulled back to ~0.9 — no opaque pixel is fully 255.
    assert warm_arr[..., 3].max() <= 230, f"alpha not pulled back: max={warm_arr[..., 3].max()}"

    # Warm vs cool LUT tints must differ (same alpha, different RGB).
    assert np.array_equal(warm_arr[..., 3], cool_arr[..., 3])
    assert not np.array_equal(warm_arr[..., :3], cool_arr[..., :3])


# ── 7 — Stage 3 still emits + composites (no-regression guard) ─────────────


def _developed_vesicles():
    rule = AbiogenesisStage3Vesicles()
    eng = Engine(width=40, height=40, rule=rule, seed=7)
    for _ in range(400):
        eng.step()
    return eng.rule, eng.state


def test_stage3_still_composites():
    # Asset loads and tints without crashing.
    vesicle = load_sprite("stage3/vesicle.png", PALETTE_WARM_SEPIA)
    assert vesicle is not None
    assert vesicle.mode == "RGBA"

    rule, state = _developed_vesicles()
    sprites = rule.render_sprites(state)
    assert isinstance(sprites, list)
    for _sx, _sy, name, scale in sprites:
        assert name == "stage3/vesicle.png"
        assert scale > 0.0

    rgb = rule.render_rgb(state)
    sr = _make_sem(canvas_size=240)
    sr.width, sr.height = state.lipid.shape[1], state.lipid.shape[0]
    out = sr.compose(rgb, sprites=sprites)
    assert out.shape == (240, 240, 3)
    assert out.dtype == np.uint8

    # composite_sprites itself runs on a sample RGBA frame without error.
    from PIL import Image

    sample = Image.new("RGB", (120, 120), (40, 34, 28))
    composited = composite_sprites(
        sample,
        [(10, 10, "stage3/vesicle.png", 0.6)],
        palette=PALETTE_WARM_SEPIA,
        grid_w=40,
        grid_h=40,
    )
    assert composited.size == (120, 120)
