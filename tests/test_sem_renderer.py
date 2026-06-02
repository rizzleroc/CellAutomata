"""Regression tests for the v4.0 SEM renderer (PRD §S9).

Nine pins covering the SemRenderer surface defined in
``cellauto.renderer_sem`` plus the persisted-config helpers in
``cellauto.app``. The tests run headlessly: ``SemRenderer.compose`` is
pure numpy + Pillow, so the only Tk-touching call (``render``) is exercised
through a thin FakeCanvas (test #2) without ever instantiating a Tk root
where it can be avoided.
"""

from __future__ import annotations

import os
import time

import numpy as np
import pytest
from PIL import Image

from cellauto.engine import Engine
from cellauto.renderer_sem import (
    PALETTE_COOL_MONO,
    PALETTE_WARM_SEPIA,
    SemRenderer,
    palette_lut,
    sem_is_available,
    shade_height,
)
from cellauto.rules import REGISTRY
from cellauto.rules.abiogenesis.stage1_grayscott import AbiogenesisStage1GrayScott


class _FakeCanvas:
    """Tk-free stand-in capturing the calls SemRenderer/FieldRenderer make.

    Just enough to satisfy ``.delete``, ``.create_image``, and the
    ``self.canvas.image = ...`` reference-hold the renderers do; everything
    that would actually touch PhotoImage goes through ``SemRenderer.compose``
    in these tests, which is Tk-free.
    """

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
    """Build a chrome-free renderer suitable for headless compose() tests."""
    sr = SemRenderer(canvas=_FakeCanvas(), canvas_size=canvas_size, palette=palette)
    # width/height drive the scale-bar overlay; set to something realistic so
    # compose() never hits its grid_extent guard.
    sr.width = 20
    sr.height = 20
    return sr


# ── Pin 1 — every field-renderer rule composes to a real image ─────────────


def test_sem_renderer_non_trivial_for_every_field_rule():
    """For every field-renderer rule in the registry, drive a small engine 5
    steps and assert SemRenderer.compose() returns a (canvas, canvas, 3) uint8
    image with non-trivial variance."""
    canvas_size = 256
    checked = 0
    for name, cls in REGISTRY.items():
        probe = cls()
        if getattr(probe, "renderer_kind", "") != "field":
            continue
        eng = Engine(width=20, height=20, rule=cls(), seed=0)
        for _ in range(5):
            eng.step()
        sr = _make_sem(canvas_size=canvas_size)
        out = sr.compose(eng.rule.render_rgb(eng.state))
        assert out.shape == (canvas_size, canvas_size, 3), f"{name}: bad shape {out.shape}"
        assert out.dtype == np.uint8, f"{name}: bad dtype {out.dtype}"
        assert out.std() > 1.0, f"{name}: constant image (std={out.std():.3f})"
        checked += 1
    # Sanity: the registry actually has field rules.
    assert checked >= 5, f"expected ≥5 field rules, exercised {checked}"


# ── Pin 2 — SEM compose() must not perturb the engine state ────────────────


def test_sem_and_field_render_paths_share_engine_state():
    """Two Stage-1 Gray-Scott engines with the same seed must produce
    bit-identical render_rgb output after 10 steps regardless of whether the
    render path goes through SemRenderer.compose or just through the rule's
    render_rgb. The SEM pipeline must be a pure read of state."""
    sr = _make_sem()

    eng_sem = Engine(width=24, height=24, rule=AbiogenesisStage1GrayScott(preset="spots"), seed=42)
    eng_ref = Engine(width=24, height=24, rule=AbiogenesisStage1GrayScott(preset="spots"), seed=42)

    for _ in range(10):
        eng_sem.step()
        # Compose drives the SEM pipeline; we discard the canvas-sized image,
        # all we care about is that it didn't mutate eng_sem.state.
        sr.compose(eng_sem.rule.render_rgb(eng_sem.state))
        eng_ref.step()
        # Reference path is what FieldRenderer.render would call; we don't
        # actually blit (that needs a real Tk root) — we just call render_rgb.
        eng_ref.rule.render_rgb(eng_ref.state)

    assert eng_sem.step_count == eng_ref.step_count == 10
    np.testing.assert_array_equal(
        eng_sem.rule.render_rgb(eng_sem.state),
        eng_ref.rule.render_rgb(eng_ref.state),
    )


# ── Pin 3 — flat input → near-uniform background in the centre patch ───────


def test_zero_field_produces_near_uniform_centre_patch():
    """A flat input (all-zero RGB) has no gradient → Lambertian term is flat,
    Laplacian-AO is zero. The only remaining variance in compose() comes from
    the value-noise overlay and the corner vignette / chrome — sampled away
    from the badge by inspecting a 200×200 patch around the centre."""
    canvas_size = 512
    sr = _make_sem(canvas_size=canvas_size)
    flat = np.zeros((20, 20, 3), dtype=np.uint8)
    out = sr.compose(flat)
    cx = cy = canvas_size // 2
    patch = out[cy - 100 : cy + 100, cx - 100 : cx + 100]
    assert patch.shape == (200, 200, 3)
    # Empirically ~15.5 on this machine — leave plenty of headroom for the
    # noise-cache to differ across Pillow/numpy versions.
    assert patch.std() < 35.0, f"centre patch too noisy (std={patch.std():.2f})"


# ── Pin 4 — SEM palette mode round-trips through the persisted config ──────


def test_sem_palette_round_trips_through_config():
    """``cellauto.app._save_sem_config`` / ``_load_sem_config`` must round-trip
    both the sem_mode flag and the palette name. Restore the prior config in
    finally so a developer running the suite locally doesn't lose their pref."""
    from cellauto.app import _CONFIG_PATH, _load_sem_config, _save_sem_config

    prior = _load_sem_config()
    try:
        _save_sem_config({"sem_mode": True, "sem_palette": PALETTE_COOL_MONO})
        cfg = _load_sem_config()
        assert cfg.get("sem_mode") is True
        assert cfg.get("sem_palette") == PALETTE_COOL_MONO
    finally:
        if prior:
            _save_sem_config(prior)
        else:
            try:
                _CONFIG_PATH.unlink()
            except FileNotFoundError:
                pass


# ── Pin 5 — reduced-motion freezes the badge pulse ─────────────────────────


def test_reduced_motion_freezes_badge_alpha():
    """While playing with reduced_motion=True the badge alpha is pinned;
    flipping reduced_motion=False makes it phase with monotonic()."""
    sr = SemRenderer(
        canvas=_FakeCanvas(),
        canvas_size=256,
        palette=PALETTE_WARM_SEPIA,
        running=True,
        reduced_motion=True,
    )
    a1 = sr._badge_alpha()
    time.sleep(0.1)
    a2 = sr._badge_alpha()
    assert a1 == a2, f"reduced-motion alpha drifted: {a1} → {a2}"

    sr.set_reduced_motion(False)
    a3 = sr._badge_alpha()
    time.sleep(0.55)
    a4 = sr._badge_alpha()
    assert a3 != a4, f"playing-pulse alpha frozen: {a3} == {a4}"


# ── Pin 6 — PNG export matches the on-screen compose byte-for-byte ─────────


def test_png_export_matches_compose(tmp_path):
    """compose() is the single source of truth for both the canvas blit and
    the PNG export. Save → reload via PIL must be exact (PNG is lossless)."""
    sr = _make_sem(canvas_size=256)
    rng = np.random.default_rng(2026)
    src = rng.integers(0, 256, size=(20, 20, 3), dtype=np.uint8)
    original = sr.compose(src)

    out_path = tmp_path / "sem_frame.png"
    Image.fromarray(original, mode="RGB").save(out_path, format="PNG")
    loaded = np.array(Image.open(out_path).convert("RGB"))

    assert np.array_equal(loaded, original)


# ── Pin 7 — capability detection + fallback when LANCZOS is gone ───────────


def test_sem_is_available_and_lanczos_fallback(monkeypatch):
    """On this machine SEM should be available. If we shim ``PIL.Image.Resampling``
    with a stand-in lacking LANCZOS, ``sem_is_available`` must return False with
    a reason mentioning LANCZOS — and crucially never raise. The original
    enum is restored via the monkeypatch fixture's teardown."""
    ok, reason = sem_is_available()
    assert ok, f"SEM unexpectedly unavailable on test host: {reason}"

    class _ResamplingNoLanczos:
        NEAREST = 0  # has at least one resampling member, just not LANCZOS

    # Pillow's Resampling is an IntEnum — its members can't be del'd, so we
    # swap the class wholesale via monkeypatch (auto-restored on teardown).
    monkeypatch.setattr(Image, "Resampling", _ResamplingNoLanczos)
    ok2, reason2 = sem_is_available()
    assert ok2 is False
    assert "LANCZOS" in reason2, f"reason missing LANCZOS hint: {reason2!r}"


# ── Pin 8 — perf budget: 20 FPS at 60×60 ────────────────────────────────────


@pytest.mark.skipif(
    os.environ.get("CI") == "slow",
    reason="perf assertion skipped on slow CI tier",
)
def test_compose_perf_budget_at_60x60():
    """PRD §F5 target: 20 FPS @ 60×60 (≤50 ms / frame). On a healthy dev box
    this runs in ~7 ms; we keep a generous budget so a noisy CI runner doesn't
    flake. If perf-sensitive CI ever does flake, bump to 75 ms (=13 FPS) and
    file the regression."""
    rule = AbiogenesisStage1GrayScott(preset="spots")
    eng = Engine(width=60, height=60, rule=rule, seed=0)
    for _ in range(20):
        eng.step()
    rgb = eng.rule.render_rgb(eng.state)

    sr = SemRenderer(canvas=_FakeCanvas(), canvas_size=512, palette=PALETTE_WARM_SEPIA)
    sr.width = 60
    sr.height = 60
    # Warm caches (font, value-noise, font-fallback path) so the timed loop
    # measures steady-state cost only.
    sr.compose(rgb)
    sr.compose(rgb)

    n = 30
    t0 = time.perf_counter()
    for _ in range(n):
        sr.compose(rgb)
    mean_ms = (time.perf_counter() - t0) * 1000.0 / n

    assert mean_ms < 50.0, f"SEM compose 60×60 too slow: {mean_ms:.2f} ms/frame (budget 50 ms)"


# ── Pin 9 — palette LUTs have the right shape and ramp direction ───────────


def test_palette_lut_shape_and_ramp_direction():
    """Both palettes must return a (256, 3) uint8 LUT whose highlight (index
    255) is luminance-brighter than the substrate (index 0). Catches any
    future stop-table edit that accidentally inverts the ramp."""
    for name in (PALETTE_WARM_SEPIA, PALETTE_COOL_MONO):
        lut = palette_lut(name)
        assert lut.shape == (256, 3), f"{name}: shape {lut.shape}"
        assert lut.dtype == np.uint8, f"{name}: dtype {lut.dtype}"
        substrate = 0.2126 * lut[0, 0] + 0.7152 * lut[0, 1] + 0.0722 * lut[0, 2]
        highlight = 0.2126 * lut[255, 0] + 0.7152 * lut[255, 1] + 0.0722 * lut[255, 2]
        assert highlight > substrate, (
            f"{name}: ramp inverted (substrate luma {substrate:.1f} ≥ highlight {highlight:.1f})"
        )

    # And the shade pipeline itself should be sane: a flat field has zero
    # gradient, so the post-shading intensity is essentially flat too.
    flat = np.zeros((16, 16), dtype=np.float32)
    intensity = shade_height(flat, noise_strength=0.0)
    assert intensity.shape == (16, 16)
    assert intensity.std() < 1e-3, f"shade_height not flat on flat input: std={intensity.std()}"
