"""Headless PIL render of the amoeba mascot — the colony's friendly avatar.

This is a still-image twin of the live Tk colony amoeba (``cellauto.renderer``)
and the header widget (``cellauto.mascot``): it draws the *same* organic
membrane blob and wandering-eye face using the shared ``cellauto.blobgeom``
geometry, but with Pillow instead of a Tk canvas — so it needs no display and
can be rendered in CI, in a script, or on a server.

Used to bake the project's amoeba hero/identity art (``tools/render_mascot_hero``)
without depending on any external image service, and to give the colony a
visual regression surface that doesn't need a GUI.
"""

from __future__ import annotations

from typing import Any

from cellauto.blobgeom import blob_points, gaze_offset

# Brand palette — mirrors cellauto/mascot.py (kept literal here so this module
# stays free of any Tk import).
BODY_TEAL = (57, 212, 200)  # #39d4c8
BODY_TEAL_HI = (94, 231, 220)  # #5ee7dc
EYE_WHITE = (253, 246, 227)  # #fdf6e3
PUPIL = (10, 14, 22)  # #0a0e16


def render_amoeba(
    size: int = 512,
    *,
    happy: bool = True,
    frame: int = 0,
    seed: int = 0xCE11,
    supersample: int = 3,
    background: tuple[int, int, int, int] | None = None,
) -> Any:
    """Return a ``size``x``size`` RGBA ``PIL.Image`` of one amoeba.

    ``frame`` advances the membrane ripple + eye gaze (so a sequence animates);
    ``seed`` gives the cell its own membrane signature; ``supersample`` renders
    large then downsamples for crisp anti-aliased edges (the hero-art touch).
    Transparent background unless ``background`` is given.
    """
    from PIL import Image, ImageDraw

    ss = max(1, supersample)
    s = size * ss
    img = Image.new("RGBA", (s, s), background or (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")

    cx = cy = s / 2.0
    r = s * 0.36
    rx, ry = r, r * 0.96
    # Dense sampling (n high) so the straight-edged PIL polygon reads as the same
    # smooth membrane the Tk renderer draws with smooth=True.
    body = blob_points(cx, cy, rx, ry, n=72, seed=seed, phase=frame * 0.06)
    draw.polygon(body, fill=(*BODY_TEAL, 255))

    # Small upper-left sheen = cuddly 3D highlight (mirrors the Tk renderer's
    # offset _lighten() blob, not a big translucent wash).
    hi = blob_points(
        cx - rx * 0.30, cy - ry * 0.40, rx * 0.44, ry * 0.34,
        n=72, seed=seed ^ 0x5EED, phase=frame * 0.05, wobble=0.10,
    )
    draw.polygon(hi, fill=(*BODY_TEAL_HI, 210))

    ew = r * 0.20
    pr = ew * 0.5
    eye_dx = r * 0.42
    eye_dy = -r * 0.12
    gx, gy = gaze_offset(frame, seed, ew - pr - 1.0)
    for sx in (-1, 1):
        ex = cx + sx * eye_dx
        ey = cy + eye_dy
        draw.ellipse([ex - ew, ey - ew, ex + ew, ey + ew], fill=(*EYE_WHITE, 255))
        px, py = ex + gx, ey + gy
        draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(*PUPIL, 255))

    mw = r * 0.34
    my = cy + r * 0.26
    line_w = max(2, int(s * 0.012))
    if happy:
        # Bottom arc of the ellipse = an upturned smile.
        draw.arc([cx - mw / 2, my - mw * 0.35, cx + mw / 2, my + mw * 0.75],
                 start=20, end=160, fill=(*PUPIL, 255), width=line_w)
    else:
        mr = r * 0.06
        draw.ellipse([cx - mr, my - mr, cx + mr, my + mr], fill=(*PUPIL, 255))

    if ss != 1:
        img = img.resize((size, size), Image.LANCZOS)
    return img
