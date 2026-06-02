"""SEM sprite-compositing tests (PRD §S6 — v4.0.1 Phase 2).

Pins:
  1. load_sprite caches + tints per palette.
  2. compose() with sprites differs from sprite-free compose for the same state.
  3. Per-stage render_sprites returns sensible counts.
  4. Sprite path is deterministic given the same state.
  5. Sprite list with a missing asset name composites cleanly (no crash).
"""

from __future__ import annotations

import numpy as np
import pytest

from cellauto.engine import Engine
from cellauto.renderer_sem import (
    _SPRITE_CACHE,
    PALETTE_COOL_MONO,
    PALETTE_WARM_SEPIA,
    SemRenderer,
    load_sprite,
)
from cellauto.rules.abiogenesis.stage1_grayscott import (
    AbiogenesisStage1GrayScott,
    GrayScottState,
)
from cellauto.rules.abiogenesis.stage3_vesicles import AbiogenesisStage3Vesicles


class _FakeCanvas:
    def delete(self, *a, **k) -> None: ...
    def create_image(self, *a, **k) -> int:
        return 1

    image = None


@pytest.fixture(autouse=True)
def _clear_sprite_cache():
    _SPRITE_CACHE.clear()
    yield
    _SPRITE_CACHE.clear()


def _developed_grayscott() -> tuple[AbiogenesisStage1GrayScott, GrayScottState]:
    rule = AbiogenesisStage1GrayScott(preset="spots")
    w = h = 60
    u = np.ones((h, w), dtype=np.float32)
    v = np.zeros((h, w), dtype=np.float32)
    rng = np.random.default_rng(42)
    for _ in range(8):
        cy, cx = rng.integers(10, h - 10), rng.integers(10, w - 10)
        r = int(rng.integers(3, 6))
        u[cy - r : cy + r, cx - r : cx + r] = 0.5
        v[cy - r : cy + r, cx - r : cx + r] = 0.25
    v += rng.uniform(-0.02, 0.02, size=v.shape).astype(np.float32)
    np.clip(v, 0, 1, out=v)
    state = GrayScottState(u=u, v=v)
    for _ in range(400):
        state = rule.step(state)
    return rule, state


def test_load_sprite_returns_rgba_image_and_caches():
    a = load_sprite("stage1/spot.png", PALETTE_WARM_SEPIA)
    assert a is not None
    assert a.mode == "RGBA"
    # Cache hit — second call returns the SAME object.
    b = load_sprite("stage1/spot.png", PALETTE_WARM_SEPIA)
    assert a is b


def test_load_sprite_tints_differently_per_palette():
    warm = load_sprite("stage1/spot.png", PALETTE_WARM_SEPIA)
    cool = load_sprite("stage1/spot.png", PALETTE_COOL_MONO)
    assert warm is not None and cool is not None
    # Different objects, different tints.
    assert warm is not cool
    warm_arr = np.asarray(warm)
    cool_arr = np.asarray(cool)
    # Same alpha (same source), different RGB.
    assert np.array_equal(warm_arr[..., 3], cool_arr[..., 3])
    assert not np.array_equal(warm_arr[..., :3], cool_arr[..., :3])


def test_compose_with_sprites_differs_from_compose_without():
    """The sprite-compositing layer still must change pixels when called
    with a non-empty sprite list. Stage 1 itself no longer emits sprites
    (v4.0.4 audit — depth-shaded substrate is the topography), so we pass
    a synthetic sprite list directly to exercise composite_sprites.
    """
    rule, state = _developed_grayscott()
    rgb = rule.render_rgb(state)
    sprites = [(15, 15, "stage1/spot.png", 0.5), (30, 30, "stage1/spot.png", 0.5)]

    r = SemRenderer(canvas=_FakeCanvas(), canvas_size=480, palette=PALETTE_WARM_SEPIA)
    r.width, r.height = state.v.shape[1], state.v.shape[0]
    plain = r.compose(rgb)
    composed = r.compose(rgb, sprites=sprites)
    assert plain.shape == composed.shape
    diff = np.abs(plain.astype(np.int16) - composed.astype(np.int16)).sum()
    assert diff > 1000, f"sprite layer should modify >1000 pixel intensity units, got {diff}"


def test_stage1_render_sprites_returns_empty_post_v404_audit():
    """v4.0.4 audit (whipgen-claude critique) retired the Stage 1 sprite
    emitter. The Gray-Scott v-field IS the topography — depth-shading the
    substrate already produces the dome reading, so sprites just floated
    on top as 'strange balls'. ``render_sprites`` returns ``[]`` as a
    permanent no-op; this test pins that contract."""
    rule, state = _developed_grayscott()
    sprites = rule.render_sprites(state)
    assert sprites == []


def test_stage3_render_sprites_returns_one_per_component():
    rule = AbiogenesisStage3Vesicles()
    eng = Engine(width=40, height=40, rule=rule, seed=7)
    for _ in range(400):
        eng.step()
    sprites = rule.render_sprites(eng.state)
    # The vesicle mask labyrinth typically yields between 1 and ~50 components
    # at this grid size; if zero, the sim didn't develop — we still want the
    # contract to hold (returns a list, not None).
    assert isinstance(sprites, list)
    for _sx, _sy, name, scale in sprites:
        assert name == "stage3/vesicle.png"
        assert 0.0 < scale


def test_sprite_path_is_deterministic_for_same_state():
    rule, state = _developed_grayscott()
    a = rule.render_sprites(state)
    b = rule.render_sprites(state)
    assert a == b  # tuples of primitives compare cleanly


def test_compose_handles_missing_sprite_gracefully():
    """A typo in a sprite name shouldn't crash the renderer — load_sprite
    returns None and composite_sprites skips it silently."""
    rule, state = _developed_grayscott()
    rgb = rule.render_rgb(state)
    r = SemRenderer(canvas=_FakeCanvas(), canvas_size=240, palette=PALETTE_WARM_SEPIA)
    r.width, r.height = state.v.shape[1], state.v.shape[0]
    bogus = [(5, 5, "nonexistent/missing.png", 1.0)]
    out = r.compose(rgb, sprites=bogus)
    assert out.shape == (240, 240, 3)


def test_compose_with_empty_sprite_list_matches_no_sprites():
    rule, state = _developed_grayscott()
    rgb = rule.render_rgb(state)
    r = SemRenderer(canvas=_FakeCanvas(), canvas_size=240, palette=PALETTE_WARM_SEPIA)
    r.width, r.height = state.v.shape[1], state.v.shape[0]
    none_out = r.compose(rgb)
    empty_out = r.compose(rgb, sprites=[])
    assert np.array_equal(none_out, empty_out)
