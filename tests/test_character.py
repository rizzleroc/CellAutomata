"""Tests for the anthropomorphized cell character renderer (v4.1).

Pins for ``cellauto.character.render_character``:
  1. Output is an (size, size) PIL RGBA image for a couple of sizes.
  2. Distinct moods produce visibly different pixels.
  3. anim_phase drives a blink — a frame near phase 0.5 differs from phase 0.0.
  4. Palette tinting changes the body hue (warm-sepia vs cool-mono).
  5. Never raises for size=8 or an unknown mood string; same args → same pixels.
  6. Sprite path: a solid sprite still gets a face drawn on top.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from cellauto.character import DEFAULT_MOOD, MOODS, render_character


def _frac_pixels_differ(a: Image.Image, b: Image.Image) -> float:
    """Fraction of pixels that differ at all between two same-size RGBA frames."""
    aa = np.asarray(a).astype(np.int16)
    bb = np.asarray(b).astype(np.int16)
    diff = np.abs(aa - bb).sum(axis=-1) > 0
    return float(diff.mean())


# ── Pin 1 — size + RGBA mode ────────────────────────────────────────────────


@pytest.mark.parametrize("size", [64, 128])
def test_output_size_and_mode(size):
    img = render_character(size, mood="calm")
    assert img.size == (size, size)
    assert img.mode == "RGBA"


def test_background_is_transparent():
    """The corners must stay fully transparent (the body is a centred blob)."""
    img = render_character(96, mood="calm")
    arr = np.asarray(img)
    # Top-left corner pixel alpha.
    assert arr[0, 0, 3] == 0
    assert arr[-1, -1, 3] == 0
    # ...but the centre is opaque (the body is there).
    assert arr[48, 48, 3] > 0


# ── Pin 2 — distinct moods differ visibly ───────────────────────────────────


def test_distinct_moods_produce_different_pixels():
    excited = render_character(128, mood="excited")
    weary = render_character(128, mood="weary")
    frac = _frac_pixels_differ(excited, weary)
    # The faces (eyes/mouth/brow) differ markedly; require a meaningful share.
    assert frac > 0.01, f"excited vs weary too similar (frac={frac:.4f})"


def test_every_mood_renders_distinct_from_calm():
    """Each mood other than calm should differ from the calm baseline."""
    base = render_character(96, mood="calm")
    for mood in MOODS:
        if mood == "calm":
            continue
        other = render_character(96, mood=mood)
        frac = _frac_pixels_differ(base, other)
        assert frac > 0.001, f"mood {mood!r} indistinguishable from calm (frac={frac:.4f})"


# ── Pin 3 — anim_phase drives a blink ───────────────────────────────────────


def test_anim_phase_drives_blink():
    open_frame = render_character(128, mood="curious", anim_phase=0.0)
    blink_frame = render_character(128, mood="curious", anim_phase=0.5)
    frac = _frac_pixels_differ(open_frame, blink_frame)
    assert frac > 0.001, f"blink frame indistinguishable from open (frac={frac:.4f})"


def test_anim_phase_bob_moves_body():
    """The breathing bob shifts the body vertically between phase 0.0 and 0.25."""
    a = render_character(128, mood="calm", anim_phase=0.0)
    b = render_character(128, mood="calm", anim_phase=0.25)
    assert _frac_pixels_differ(a, b) > 0.0005


# ── Pin 4 — palette tinting changes the body hue ────────────────────────────


def test_palette_tinting_changes_body_hue():
    warm = render_character(128, mood="calm", palette="warm-sepia")
    cool = render_character(128, mood="calm", palette="cool-mono")
    warm_arr = np.asarray(warm).astype(np.float32)
    cool_arr = np.asarray(cool).astype(np.float32)
    # Compare mean RGB over body (opaque) pixels only.
    body = np.asarray(warm)[..., 3] > 32
    warm_mean = warm_arr[..., :3][body].mean(axis=0)
    cool_mean = cool_arr[..., :3][body].mean(axis=0)
    assert np.abs(warm_mean - cool_mean).sum() > 10.0, (
        f"palettes too similar: warm={warm_mean}, cool={cool_mean}"
    )


# ── Pin 5 — robustness + determinism ────────────────────────────────────────


def test_tiny_size_does_not_raise():
    img = render_character(8, mood="excited", anim_phase=0.37)
    assert img.size == (8, 8)
    assert img.mode == "RGBA"


def test_unknown_mood_falls_back_to_default():
    unknown = render_character(96, mood="not-a-real-mood")
    default = render_character(96, mood=DEFAULT_MOOD)
    assert np.array_equal(np.asarray(unknown), np.asarray(default))


def test_same_args_give_identical_pixels():
    a = render_character(128, mood="triumphant", anim_phase=0.3, palette="cool-mono")
    b = render_character(128, mood="triumphant", anim_phase=0.3, palette="cool-mono")
    assert np.array_equal(np.asarray(a), np.asarray(b))


# ── Pin 6 — sprite path draws a face on top ─────────────────────────────────


def test_sprite_path_draws_face_on_top():
    sprite = Image.new("RGBA", (200, 200), (120, 90, 60, 255))
    out = render_character(128, mood="excited", sprite=sprite)
    assert out.size == (128, 128)
    assert out.mode == "RGBA"
    # A bare resized+tinted solid sprite (120,90,60) has no eye whites; the
    # rendered result must contain markedly brighter eye pixels. (The v4.2
    # _dim_specular step tones catch-lights down from pure white, so assert
    # "clearly brighter than the body" rather than an absolute near-white.)
    arr = np.asarray(out)[..., :3].astype(np.int16)
    bright = (arr > 130).all(axis=-1)
    assert bright.any(), "expected bright eye/sparkle pixels drawn over the sprite"
