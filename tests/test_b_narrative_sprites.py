"""v4.1 tests — generated protagonist body sprites for Channel B.

Pins ``cellauto.sprites``: the optional bridge that loads externally-generated
"day in the life" protagonist art, chroma-keys its flat magenta background to
transparency, and exposes a ``stage -> RGBA`` provider for
``NarrativeChannel.set_sprite_provider``.

The contract under test:

  * No art on disk → ``build_sprite_provider`` returns ``None`` (the channel
    stays fully procedural; the shipped repo is unaffected).
  * A magenta-field plate is keyed to RGBA with transparent corners, an opaque
    subject, and a square (aspect-preserving) trim.
  * An image with no key background returns ``None`` rather than an opaque box,
    so a bad generation degrades to the procedural body.
  * Mood-variant filenames take priority over the shared default.
  * A real sprite actually reaches the rendered character (the composite
    differs from the procedural body).

Tests are Tk-free: they synthesise PNGs into ``tmp_path`` and assert with
numpy, in the plain-function style of the existing ``tests/test_b8_sprites``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

from cellauto import sprites as S
from cellauto.channel import NarrativeChannel
from cellauto.narrative import DAY_IN_THE_LIFE


@pytest.fixture(autouse=True)
def _clear_sprite_cache():
    S._SPRITE_CACHE.clear()
    yield
    S._SPRITE_CACHE.clear()


def _magenta_sprite(path: Path, *, size: int = 96, subject: tuple[int, int, int] = (80, 90, 110)) -> Path:
    """A subject disc on a flat #FF00FF chroma field — the art pipeline's shape."""
    img = Image.new("RGB", (size, size), (255, 0, 255))
    draw = ImageDraw.Draw(img)
    r = size * 0.32
    cx = cy = size / 2.0
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=subject)
    img.save(path)
    return path


def _alpha_sprite(path: Path, *, size: int = 96, subject: tuple[int, int, int] = (80, 90, 110)) -> Path:
    """A subject disc on a genuinely transparent field — a true alpha cutout
    (the shape produced when art is exported with real transparency rather than
    a flat key colour)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r = size * 0.32
    cx = cy = size / 2.0
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*subject, 255))
    img.save(path)
    return path


# ── 1 — no art on disk → provider is None (procedural body stands) ──────────


def test_provider_is_none_when_dir_empty(tmp_path):
    assert S.has_any_sprite(tmp_path) is False
    assert S.build_sprite_provider(tmp_path) is None


def test_provider_is_none_when_dir_missing(tmp_path):
    assert S.build_sprite_provider(tmp_path / "does-not-exist") is None


# ── 2 — chroma_key lifts the magenta field, keeps the subject ──────────────


def test_chroma_key_transparent_bg_opaque_subject(tmp_path):
    p = _magenta_sprite(tmp_path / "x.png")
    keyed = S.chroma_key(Image.open(p).convert("RGBA"))
    assert keyed is not None and keyed.mode == "RGBA"
    a = np.asarray(keyed)[..., 3]
    assert a[0, 0] == 0 and a[-1, -1] == 0, "corners should be keyed transparent"
    h, w = a.shape
    assert a[h // 2, w // 2] > 200, "subject centre should stay opaque"


def test_chroma_key_returns_none_without_key_background():
    # A flat grey frame has no magenta field → don't manufacture an opaque box.
    assert S.chroma_key(Image.new("RGB", (64, 64), (90, 90, 90))) is None


def test_chroma_key_despills_edges_no_neon_fringe(tmp_path):
    p = _magenta_sprite(tmp_path / "x.png", size=128)
    keyed = S.chroma_key(Image.open(p).convert("RGBA"))
    assert keyed is not None
    arr = np.asarray(keyed).astype(np.int32)
    # Partially-transparent edge pixels must not stay saturated magenta
    # (R high, G low, B high). De-spill pulls them toward their luminance.
    a = arr[..., 3]
    edge = (a > 10) & (a < 245)
    if edge.any():
        r, g, b = arr[..., 0][edge], arr[..., 1][edge], arr[..., 2][edge]
        neon = (r > 180) & (g < 80) & (b > 180)
        assert not neon.any(), "magenta fringe survived de-spill"


# ── 3 — load_body_sprite keys + square-trims, and caches ───────────────────


def test_load_body_sprite_keys_and_squares(tmp_path):
    p = _magenta_sprite(tmp_path / "protagonist.png", size=80)
    spr = S.load_body_sprite(p)
    assert spr is not None and spr.mode == "RGBA"
    w, h = spr.size
    assert w == h, "sprite should be square-trimmed for aspect-safe resize"
    a = np.asarray(spr)[..., 3]
    assert a.max() > 200 and a.min() == 0
    # Second call is served from the cache (same object identity).
    assert S.load_body_sprite(p) is spr


def test_load_body_sprite_missing_file_returns_none(tmp_path):
    assert S.load_body_sprite(tmp_path / "nope.png") is None


# ── 3b — real-alpha cutouts are honoured directly (no chroma key) ──────────


def test_has_real_alpha_true_for_cutout_false_for_flat(tmp_path):
    cut = Image.open(_alpha_sprite(tmp_path / "cut.png")).convert("RGBA")
    flat = Image.open(_magenta_sprite(tmp_path / "flat.png")).convert("RGBA")
    assert S.has_real_alpha(cut) is True
    assert S.has_real_alpha(flat) is False


def test_load_body_sprite_uses_real_alpha_without_key(tmp_path):
    # A transparent cutout has NO magenta to key; it must still load (via its
    # own alpha) rather than fall through chroma_key to None.
    p = _alpha_sprite(tmp_path / "protagonist.png", size=80, subject=(120, 130, 150))
    spr = S.load_body_sprite(p)
    assert spr is not None and spr.mode == "RGBA"
    w, h = spr.size
    assert w == h, "real-alpha sprite should also be square-trimmed"
    a = np.asarray(spr)[..., 3]
    assert a.max() > 200 and a.min() == 0, "subject opaque, background transparent"
    # The subject body keeps its true colour (no de-spill / key tint applied).
    arr = np.asarray(spr)
    body = arr[..., 3] > 200
    assert body.any()
    mean_rgb = arr[..., :3][body].mean(axis=0)
    assert abs(float(mean_rgb[0]) - 120) < 25 and abs(float(mean_rgb[2]) - 150) < 25


def test_provider_resolves_real_alpha_plate(tmp_path):
    _alpha_sprite(tmp_path / "protagonist.png", subject=(200, 200, 210))
    prov = S.build_sprite_provider(tmp_path)
    assert prov is not None
    spr = prov(0)
    assert spr is not None and spr.mode == "RGBA"
    assert np.asarray(spr)[..., 3].min() == 0


# ── 4 — provider resolution: every stage + mood-variant priority ───────────


def test_provider_resolves_default_for_all_stages(tmp_path):
    _magenta_sprite(tmp_path / "protagonist.png")
    prov = S.build_sprite_provider(tmp_path)
    assert prov is not None
    for stage in range(len(DAY_IN_THE_LIFE)):
        spr = prov(stage)
        assert spr is not None and spr.mode == "RGBA"


def test_mood_variant_takes_priority(tmp_path):
    _magenta_sprite(tmp_path / "protagonist.png", subject=(60, 60, 60))
    mood = S.stage_mood(0)
    _magenta_sprite(tmp_path / f"protagonist_{mood}.png", subject=(210, 210, 210))
    resolved = S.resolve_sprite_path(tmp_path, 0)
    assert resolved is not None and resolved.name == f"protagonist_{mood}.png"


def test_stage_mood_clamps_out_of_range():
    assert S.stage_mood(-7) == DAY_IN_THE_LIFE[0].mood
    assert S.stage_mood(9999) == DAY_IN_THE_LIFE[-1].mood


# ── 5 — the sprite actually reaches the rendered character ─────────────────


def test_channel_uses_sprite_body(tmp_path):
    base = np.full((140, 140, 3), 40, dtype=np.uint8)

    procedural = NarrativeChannel(size=140, palette="warm-sepia", enabled=True, reduced_motion=True)
    out_proc = procedural.compose(base.copy())

    _magenta_sprite(tmp_path / "protagonist.png", size=96, subject=(230, 230, 230))
    with_sprite = NarrativeChannel(size=140, palette="warm-sepia", enabled=True, reduced_motion=True)
    with_sprite.set_sprite_provider(S.build_sprite_provider(tmp_path))
    out_spr = with_sprite.compose(base.copy())

    assert out_proc.shape == out_spr.shape
    assert not np.array_equal(out_proc, out_spr), "sprite body did not change the composite"
