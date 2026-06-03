"""Headless test for the PIL amoeba render (no Tk/display needed)."""

from __future__ import annotations

from cellauto.mascot_image import render_amoeba


def test_render_amoeba_is_nonblank_rgba():
    img = render_amoeba(64, supersample=2)
    assert img.mode == "RGBA"
    assert img.size == (64, 64)
    px = img.load()
    opaque = sum(1 for y in range(64) for x in range(64) if px[x, y][3] > 200)
    # The body should cover a meaningful chunk of the frame.
    assert opaque > 300


def test_render_amoeba_frames_differ():
    # Advancing the frame must change the image (membrane + gaze move).
    a = render_amoeba(48, frame=0, supersample=2).tobytes()
    b = render_amoeba(48, frame=20, supersample=2).tobytes()
    assert a != b


def test_render_amoeba_neutral_mouth_variant():
    # Exercise the happy=False branch (neutral mouth) so it stays covered.
    img = render_amoeba(48, happy=False, supersample=2)
    assert img.size == (48, 48)
