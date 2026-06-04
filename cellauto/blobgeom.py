"""Deterministic organic-blob geometry for the living colony.

Pure stdlib (``math`` only) — no Tk, no PIL, no numpy — so the colony's
*shape and motion* can be unit-tested headlessly even though the renderer that
draws it (``cellauto.renderer``) needs a real Tk canvas and a display.

Two primitives:

  - ``blob_points`` — an irregular, smoothly-wobbling closed outline (a
    membrane, not a perfect ellipse). The per-angle radius is perturbed by a
    couple of low-frequency sinusoids seeded by ``seed``; advancing ``phase``
    each frame makes the membrane *breathe* without any random state, so every
    cell is reproducible and every frame is a pure function of its inputs.
  - ``gaze_offset`` — a slowly-wandering pupil offset, bounded to stay inside
    the eye-white, deterministic per ``seed`` so each amoeba looks around with
    its own rhythm instead of the colony staring in unison.
"""

from __future__ import annotations

import math

# Outline vertex count. Enough for a smooth spline once Tk re-curves it with
# ``smooth=True``; few enough that re-flowing every amoeba per frame is cheap.
BLOB_N = 14


def blob_points(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    *,
    n: int = BLOB_N,
    seed: int = 0xCE11,
    phase: float = 0.0,
    wobble: float = 0.12,
) -> list[tuple[float, float]]:
    """Return ``n`` points around an irregular blob centred at ``(cx, cy)``.

    ``rx``/``ry`` are the base radii (an ellipse the blob hugs); ``wobble`` is
    the fractional membrane deformation; ``phase`` advances the deformation for
    continuous membrane motion. Deterministic: same args → identical points.
    """
    # Two seed-derived offsets give each cell a distinct membrane signature.
    s0 = (seed & 0xFF) * 0.013
    s1 = ((seed >> 8) & 0xFF) * 0.021
    pts: list[tuple[float, float]] = []
    for k in range(n):
        ang = 2.0 * math.pi * k / n
        # Low-frequency wobble: a 3rd + 5th harmonic so the outline reads
        # organic (lumpy) rather than a clean ellipse. phase drifts it slowly.
        w = math.sin(ang * 3.0 + s0 + phase) + 0.5 * math.sin(ang * 5.0 + s1 - phase * 0.7)
        f = 1.0 + wobble * w / 1.5
        pts.append((cx + rx * f * math.cos(ang), cy + ry * f * math.sin(ang)))
    return pts


def gaze_offset(frame: int, seed: int, max_off: float) -> tuple[float, float]:
    """A bounded, slowly-wandering pupil offset in pixels.

    The raw target traces lissajous-like curves of ``frame`` (so it drifts
    smoothly and never jumps); it's clamped to the unit disk and scaled by
    ``max_off`` so the pupil can never leave the eye-white. ``seed`` phases each
    cell differently. Deterministic.
    """
    mo = max(0.0, max_off)
    a = (seed & 0xFF) * 0.0245
    b = ((seed >> 8) & 0xFF) * 0.0193
    gx = 0.7 * math.sin(frame * 0.013 + a) + 0.3 * math.sin(frame * 0.030 + b)
    gy = 0.6 * math.cos(frame * 0.011 + b)
    mag = math.hypot(gx, gy)
    if mag > 1.0:
        gx, gy = gx / mag, gy / mag
    return gx * mo, gy * mo
