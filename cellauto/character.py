"""Anthropomorphized cell character (v4.1) — the protagonist of the story channel.

The grounded SEM render shows the chemistry; *this* draws the cell as a
character with a face and a mood, so the "day in the life" channel has a
protagonist a viewer can follow. It is the grown-up sibling of
``cellauto.mascot.AmoebaMascot`` (the little Tk-canvas header avatar), but
rendered to a **PIL RGBA image** so the narrative channel
(``cellauto.channel``) can composite it over the micrograph at any resolution.

Design constraints:
  * Pure procedural PIL by default (no network, deterministic) so it works
    offline and in tests; an optional pre-rendered ``sprite`` body (a
    whipgen-generated protagonist) can be supplied and the procedural face /
    expression is drawn on top of it.
  * Palette-aware: tint to the active SEM palette ("warm-sepia" | "cool-mono")
    via ``cellauto.renderer_sem.palette_lut`` so the character belongs in the
    same world as the micrograph.
  * Animatable from a single scalar ``anim_phase`` in [0, 1): breathing bob,
    periodic blink, and a per-mood expression. No internal clock — the channel
    owns the timeline and passes the phase in.

Interface contract (locked):

    MOODS                       — tuple of supported mood keys
    render_character(size, mood, anim_phase, *, palette, sprite) -> PIL RGBA
"""

from __future__ import annotations

import math
from typing import Any

# Supported moods. Each maps to an eye/mouth expression in render_character.
# Keep in sync with cellauto.narrative DayBeat.mood values.
MOODS: tuple[str, ...] = (
    "curious",
    "calm",
    "excited",
    "struggling",
    "triumphant",
    "weary",
    "reborn",
)

DEFAULT_MOOD = "calm"

# Colour feel borrowed from cellauto.mascot. Hardcoded (not imported) so this
# module stays headless — mascot.py imports tkinter, which we must not drag in.
BODY_TEAL = "#39d4c8"
BODY_TEAL_HI = "#5ee7dc"
BODY_MAGENTA = "#d439a4"
EYE_WHITE = "#fdf6e3"
PUPIL = "#0a0e16"
HIGHLIGHT = "#ffffff"

# Supersample factor — render at SS× then LANCZOS-downsample for soft edges.
_SUPERSAMPLE = 3

# Number of blob outline vertices (an irregular, not-perfectly-round membrane).
_BLOB_POINTS = 24


class _TransparentStub:
    """Minimal duck-typed transparent RGBA stand-in for the PIL-missing path.

    Every other module in this repo assumes Pillow is installed (it is a hard
    dependency of ``renderer_sem``), so this is only reached if the import of
    PIL fails inside :func:`render_character`. It exposes just enough surface
    (``.size``, ``.mode``) that callers treating it as "a transparent image"
    don't crash, and a ``tobytes`` returning all-zero (fully transparent) RGBA.
    """

    def __init__(self, size: int) -> None:
        self.size = (size, size)
        self.mode = "RGBA"
        self._size = size

    def tobytes(self) -> bytes:
        return b"\x00\x00\x00\x00" * (self._size * self._size)


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    """Parse ``#rrggbb`` into an (r, g, b) int triple."""
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))


def _luma(rgb: tuple[int, int, int]) -> float:
    """Rec.709 luminance of an (r, g, b) triple in [0, 255]."""
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def _tint_color(rgb: tuple[int, int, int], palette: str, strength: float = 0.55) -> tuple[int, int, int]:
    """Blend a colour toward the SEM palette's tone at its own luminance.

    Maps ``rgb``'s luminance through ``palette_lut(palette)`` to get the
    palette tone the micrograph would use at that brightness, then blends the
    original colour ``strength`` of the way toward it. ``warm-sepia`` and
    ``cool-mono`` therefore pull the same body hue to visibly different tones.
    """
    from cellauto.renderer_sem import palette_lut

    lut = palette_lut(palette)
    idx = int(max(0.0, min(255.0, _luma(rgb))))
    tone = lut[idx]
    out = tuple(int(round(rgb[i] * (1.0 - strength) + float(tone[i]) * strength)) for i in range(3))
    return (out[0], out[1], out[2])


def _blob_points(
    cx: float,
    cy: float,
    radius: float,
    *,
    n: int = _BLOB_POINTS,
    wobble: float = 0.12,
    seed: int = 0xCE11,
) -> list[tuple[float, float]]:
    """Return ``n`` points around an irregular blob (not a perfect circle).

    The per-angle radius is perturbed by a fixed low-frequency wobble seeded by
    ``seed`` so the membrane reads organic but is fully deterministic.
    """
    pts: list[tuple[float, float]] = []
    for k in range(n):
        ang = 2.0 * math.pi * k / n
        # Deterministic low-frequency wobble: a couple of sinusoids whose
        # frequency/phase come from the seed. No RNG → identical every call.
        w = math.sin(ang * 3.0 + (seed & 0xFF) * 0.013) + 0.5 * math.sin(
            ang * 5.0 + ((seed >> 8) & 0xFF) * 0.021
        )
        r = radius * (1.0 + wobble * w / 1.5)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def _draw_body(
    draw: Any,
    cx: float,
    cy: float,
    radius: float,
    body_rgb: tuple[int, int, int],
    hi_rgb: tuple[int, int, int],
    *,
    alpha: int = 235,
) -> None:
    """Draw the procedural membrane blob, nucleus, organelles and rim light."""
    # Translucent membrane blob (irregular outline).
    blob = _blob_points(cx, cy, radius)
    draw.polygon(blob, fill=(*body_rgb, alpha))

    # Rim / specular highlight — an offset lighter blob toward the upper-left.
    hi = _blob_points(
        cx - radius * 0.22,
        cy - radius * 0.28,
        radius * 0.62,
        wobble=0.10,
        seed=0x5EED,
    )
    draw.polygon(hi, fill=(*hi_rgb, 90))

    # Inner nucleus — a darker translucent disc, slightly off-centre.
    nx, ny = cx + radius * 0.10, cy + radius * 0.12
    nr = radius * 0.34
    nucleus = tuple(int(c * 0.55) for c in body_rgb)
    draw.ellipse(
        (nx - nr, ny - nr, nx + nr, ny + nr),
        fill=(nucleus[0], nucleus[1], nucleus[2], 150),
    )

    # A few organelle speckles at fixed (deterministic) positions.
    speck_rgb = _hex_to_rgb(BODY_MAGENTA)
    for fx, fy, fr in (
        (-0.30, 0.22, 0.09),
        (0.28, -0.18, 0.07),
        (0.05, 0.36, 0.06),
        (-0.18, -0.30, 0.05),
    ):
        sx, sy = cx + radius * fx, cy + radius * fy
        sr = radius * fr
        draw.ellipse(
            (sx - sr, sy - sr, sx + sr, sy + sr),
            fill=(speck_rgb[0], speck_rgb[1], speck_rgb[2], 170),
        )


def _eye_geometry(cx: float, cy: float, size: int) -> tuple[float, float, float, float]:
    """Return ``(left_x, right_x, eye_y, eye_white_r)`` for the two eyes."""
    dx = size * 0.16
    dy = -size * 0.06
    ew = max(2.0, size * 0.11)
    return (cx - dx, cx + dx, cy + dy, ew)


def _draw_eye_white(draw: Any, ex: float, ey: float, ew: float, openness: float) -> tuple[float, float]:
    """Draw one eye white squashed vertically by ``openness`` in [0, 1].

    Returns the pupil's centre so the caller can place a pupil/sparkle. At
    ``openness`` near 0 the eye is a thin slit (used for blinks / weariness).
    """
    eye_white = _hex_to_rgb(EYE_WHITE)
    half_h = max(0.6, ew * openness)
    draw.ellipse(
        (ex - ew, ey - half_h, ex + ew, ey + half_h),
        fill=(*eye_white, 255),
    )
    return (ex, ey)


def _draw_pupil(draw: Any, ex: float, ey: float, pr: float, *, sparkle: bool = False) -> None:
    """Draw a pupil at ``(ex, ey)``; optionally add a white catch-light."""
    pupil = _hex_to_rgb(PUPIL)
    draw.ellipse((ex - pr, ey - pr, ex + pr, ey + pr), fill=(*pupil, 255))
    if sparkle:
        sr = max(1.0, pr * 0.42)
        sx, sy = ex - pr * 0.35, ey - pr * 0.40
        draw.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=(255, 255, 255, 235))


def _draw_brow(draw: Any, lx: float, rx: float, ey: float, ew: float, tilt: float) -> None:
    """Draw two angled brows above the eyes. ``tilt`` > 0 → angry/struggling."""
    pupil = _hex_to_rgb(PUPIL)
    w = max(1, int(ew * 0.5))
    by = ey - ew * 1.6
    span = ew * 0.9
    drop = ew * 0.7 * tilt
    # Left brow: inner end (toward centre) drops when tilt>0 (downturned/angry).
    draw.line((lx - span, by - drop, lx + span, by + drop), fill=(*pupil, 230), width=w)
    draw.line((rx - span, by + drop, rx + span, by - drop), fill=(*pupil, 230), width=w)


def _draw_mouth_arc(draw: Any, cx: float, my: float, mw: float, mh: float, *, smile: bool) -> None:
    """Draw an upturned (smile) or downturned (frown) mouth arc."""
    pupil = _hex_to_rgb(PUPIL)
    w = max(1, int(mh * 0.35))
    if smile:
        draw.arc((cx - mw, my - mh, cx + mw, my + mh), start=20, end=160, fill=(*pupil, 235), width=w)
    else:
        draw.arc((cx - mw, my, cx + mw, my + 2 * mh), start=200, end=340, fill=(*pupil, 235), width=w)


def _draw_mouth_o(draw: Any, cx: float, my: float, r: float) -> None:
    """Draw a small open 'o' mouth (surprise / curiosity)."""
    pupil = _hex_to_rgb(PUPIL)
    draw.ellipse((cx - r, my - r, cx + r, my + r), fill=(*pupil, 230))


# ── Per-mood face helpers ───────────────────────────────────────────────────
# Each draws eyes + mouth (+ brow) for one mood, at the given centre. ``blink``
# in [0, 1] multiplies eye openness so the animation blink works for every mood.


def _eyes_curious(draw: Any, cx: float, cy: float, size: int, blink: float) -> None:
    """Curious: wide round eyes with a catch-light and a small 'o' mouth."""
    lx, rx, ey, ew = _eye_geometry(cx, cy, size)
    pr = ew * 0.55
    for ex in (lx, rx):
        _draw_eye_white(draw, ex, ey, ew, blink)
        if blink > 0.4:
            _draw_pupil(draw, ex, ey - ew * 0.1, pr, sparkle=True)
    _draw_mouth_o(draw, cx, cy + size * 0.16, size * 0.05)


def _eyes_calm(draw: Any, cx: float, cy: float, size: int, blink: float) -> None:
    """Calm: soft medium eyes, gentle level brows, a faint relaxed smile."""
    lx, rx, ey, ew = _eye_geometry(cx, cy, size)
    pr = ew * 0.5
    for ex in (lx, rx):
        _draw_eye_white(draw, ex, ey, ew * 0.85, blink)
        if blink > 0.4:
            _draw_pupil(draw, ex, ey, pr)
    _draw_mouth_arc(draw, cx, cy + size * 0.16, size * 0.14, size * 0.05, smile=True)


def _eyes_excited(draw: Any, cx: float, cy: float, size: int, blink: float) -> None:
    """Excited: very wide eyes with bright sparkles + a big open smile."""
    lx, rx, ey, ew = _eye_geometry(cx, cy, size)
    pr = ew * 0.6
    for ex in (lx, rx):
        _draw_eye_white(draw, ex, ey, ew * 1.1, blink)
        if blink > 0.4:
            _draw_pupil(draw, ex, ey - ew * 0.12, pr, sparkle=True)
    _draw_mouth_arc(draw, cx, cy + size * 0.14, size * 0.18, size * 0.09, smile=True)


def _eyes_struggling(draw: Any, cx: float, cy: float, size: int, blink: float) -> None:
    """Struggling: downturned angled brows, tense narrow eyes, a frown."""
    lx, rx, ey, ew = _eye_geometry(cx, cy, size)
    pr = ew * 0.45
    for ex in (lx, rx):
        _draw_eye_white(draw, ex, ey, ew * 0.7, blink)
        if blink > 0.4:
            _draw_pupil(draw, ex, ey + ew * 0.05, pr)
    _draw_brow(draw, lx, rx, ey, ew, tilt=1.0)
    _draw_mouth_arc(draw, cx, cy + size * 0.18, size * 0.13, size * 0.05, smile=False)


def _eyes_triumphant(draw: Any, cx: float, cy: float, size: int, blink: float) -> None:
    """Triumphant: happy upturned arc eyes (^_^) and a broad open smile."""
    lx, rx, ey, ew = _eye_geometry(cx, cy, size)
    pupil = _hex_to_rgb(PUPIL)
    w = max(1, int(ew * 0.5))
    if blink > 0.4:
        # Upturned smiling-eye arcs instead of round whites.
        for ex in (lx, rx):
            draw.arc(
                (ex - ew, ey - ew * 0.4, ex + ew, ey + ew),
                start=200,
                end=340,
                fill=(*pupil, 235),
                width=w,
            )
    else:
        for ex in (lx, rx):
            _draw_eye_white(draw, ex, ey, ew, blink)
    _draw_mouth_arc(draw, cx, cy + size * 0.14, size * 0.19, size * 0.10, smile=True)


def _eyes_weary(draw: Any, cx: float, cy: float, size: int, blink: float) -> None:
    """Weary: heavy half-lidded eyes and a tired, slightly downturned mouth."""
    lx, rx, ey, ew = _eye_geometry(cx, cy, size)
    pr = ew * 0.5
    # Half-lidded: openness capped low even when "fully open".
    lid = min(blink, 0.45)
    for ex in (lx, rx):
        _draw_eye_white(draw, ex, ey, ew, lid)
        if blink > 0.4:
            _draw_pupil(draw, ex, ey + ew * 0.1, pr)
    _draw_mouth_arc(draw, cx, cy + size * 0.2, size * 0.12, size * 0.04, smile=False)


def _eyes_reborn(draw: Any, cx: float, cy: float, size: int, blink: float) -> None:
    """Reborn: fresh, bright, slightly smaller-set eyes + a soft hopeful smile.

    The smaller fresh *body* is handled in :func:`render_character` (reborn
    shrinks the membrane); this draws a wide-eyed wondering face on top.
    """
    lx, rx, ey, ew = _eye_geometry(cx, cy, size)
    pr = ew * 0.55
    for ex in (lx, rx):
        _draw_eye_white(draw, ex, ey, ew, blink)
        if blink > 0.4:
            _draw_pupil(draw, ex, ey - ew * 0.08, pr, sparkle=True)
    _draw_mouth_arc(draw, cx, cy + size * 0.16, size * 0.13, size * 0.06, smile=True)


_MOOD_FACES = {
    "curious": _eyes_curious,
    "calm": _eyes_calm,
    "excited": _eyes_excited,
    "struggling": _eyes_struggling,
    "triumphant": _eyes_triumphant,
    "weary": _eyes_weary,
    "reborn": _eyes_reborn,
}


def _blink_openness(anim_phase: float) -> float:
    """Map ``anim_phase`` in [0, 1) to eye openness in [0, 1].

    Eyes are fully open at phase 0.0 and nearly closed around phase ≈ 0.5
    (one blink per cycle). The blink is a short dip: openness stays ~1 for
    most of the cycle and plunges only in a narrow window centred on 0.5.
    """
    p = anim_phase - math.floor(anim_phase)  # wrap into [0, 1)
    # Distance from the blink centre (0.5), normalised so the closed window
    # is ~12% of the cycle wide.
    d = abs(p - 0.5)
    if d > 0.12:
        return 1.0
    # Smooth dip: 0 at centre, 1 at the window edge.
    t = d / 0.12
    return float(0.05 + 0.95 * (1.0 - math.cos(t * math.pi)) / 2.0)


# Deterministic seed for eye-integration grain. Position/seed only (never time)
# so "same phase → same frame" still holds. (0x53EE, NOT the invalid 0x5EM.)
_EYE_GRAIN_SEED = 0x53EE


def _apply_eye_grain(face_img: Any) -> Any:
    """Add deterministic equal-per-channel luminance jitter to the drawn face.

    Adds a small luminance jitter (amp ~14, the SAME delta on R, G and B so no
    chroma is introduced — chroma noise would look wrong on a monochrome-LUT
    world) ONLY where the face alpha exceeds 24, breaking up the "pasted vector
    eyes" read. The RNG is seeded by position/seed only (``0x53EE``), never by
    time, so the same animation phase yields the same frame. Returns a new RGBA
    image; the caller falls back to the un-grained face on any exception.
    """
    import numpy as np
    from PIL import Image

    arr = np.asarray(face_img, dtype=np.float32)
    alpha = arr[..., 3]
    mask = alpha > 24
    rng = np.random.default_rng(_EYE_GRAIN_SEED)
    # One jitter value per pixel, applied equally to R, G, B (luminance-only).
    jitter = rng.normal(0.0, 14.0, size=alpha.shape).astype(np.float32)
    jitter *= mask  # zero outside the face footprint
    arr[..., 0] = np.clip(arr[..., 0] + jitter, 0, 255)
    arr[..., 1] = np.clip(arr[..., 1] + jitter, 0, 255)
    arr[..., 2] = np.clip(arr[..., 2] + jitter, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def _dim_specular(face_img: Any) -> Any:
    """Knock down the face's blown-out highlights so they stop reading as stickers.

    Where the face is both very bright (luma > 225) and nearly opaque
    (alpha > 200) — i.e. the EYE_WHITE fill at alpha 255 and the catch-light
    dots at alpha 235 — pull the RGB toward 0.91× and drop the alpha toward
    ~110 so the membrane shows through the highlight. Returns a new RGBA image;
    the caller falls back to the un-dimmed face on any exception.
    """
    import numpy as np
    from PIL import Image

    arr = np.asarray(face_img, dtype=np.float32)
    rgb = arr[..., :3]
    alpha = arr[..., 3]
    luma = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    spec = (luma > 225) & (alpha > 200)
    arr[..., 0] = np.where(spec, rgb[..., 0] * 0.91, rgb[..., 0])
    arr[..., 1] = np.where(spec, rgb[..., 1] * 0.91, rgb[..., 1])
    arr[..., 2] = np.where(spec, rgb[..., 2] * 0.91, rgb[..., 2])
    arr[..., 3] = np.where(spec, 110.0, alpha)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def _clip_face_to_body(face_img: Any, body_img: Any, *, erode: int = 2) -> Any:
    """Multiply ``face_img``'s alpha by the body silhouette so no face pixel
    can sit outside the membrane.

    The body alpha is taken straight from ``body_img`` (the layer that already
    holds either the resized sprite or the procedural blob), binarised at a low
    threshold, optionally eroded a few pixels so the eyes tuck just inside the
    membrane rim, then used as a 0..1 multiplier on ``face_img``'s alpha. This
    is the single fix for the "eyes spilling onto the background" giveaway.
    Returns a new RGBA image; the caller falls back to the unclipped face on any
    exception (so a body with no usable alpha can never blank the face).
    """
    import numpy as np
    from PIL import Image

    body = np.asarray(body_img, dtype=np.float32)
    body_a = body[..., 3]
    # Solid where the body is at least faintly present. The procedural blob and
    # tinted sprites are both well above this floor inside the silhouette.
    solid = body_a > 12.0
    if not bool(solid.any()):
        # No body silhouette to clip against — leave the face untouched.
        return face_img

    mask = solid.astype(np.float32)
    if erode > 0:
        # Erode by `erode` px via repeated 4-neighbour minimum so eyes sit just
        # inside the rim. Pure-numpy (no scipy) to honour the PIL+numpy limit.
        for _ in range(int(erode)):
            shrunk = mask.copy()
            shrunk[1:, :] = np.minimum(shrunk[1:, :], mask[:-1, :])
            shrunk[:-1, :] = np.minimum(shrunk[:-1, :], mask[1:, :])
            shrunk[:, 1:] = np.minimum(shrunk[:, 1:], mask[:, :-1])
            shrunk[:, :-1] = np.minimum(shrunk[:, :-1], mask[:, 1:])
            mask = shrunk

    face = np.asarray(face_img, dtype=np.float32)
    face[..., 3] = face[..., 3] * mask
    return Image.fromarray(np.clip(face, 0, 255).astype(np.uint8), "RGBA")


def _symmetrize_specular(face_img: Any, cx: float, eye_dx: float) -> Any:
    """Make the two eyes' catch-lights identical and consistently lit.

    The per-mood helpers place a sparkle at the SAME in-eye offset on both eyes
    (one implied light direction), but ``_apply_eye_grain`` jitters each eye
    independently so one catch-light can end up hard-bright and the other
    dim/grey — the asymmetry the art-director flagged. This isolates the LEFT
    eye's near-pure-white catch-light, then copies a tight bounding box around it
    *wholesale* onto the right eye, translated (not reflected) by the inter-eye
    spacing ``2*eye_dx``. Copying the whole box — rather than only the bright
    pixels — guarantees the right catch-light is pixel-identical to the left (same
    size, brightness, shape) with no stray bright specks left behind, while the
    translation keeps both dots at the same in-eye offset so the implied light
    stays a single direction. Returns a new RGBA image; the caller falls back to
    the un-symmetrised face on any exception.
    """
    import numpy as np
    from PIL import Image

    arr = np.asarray(face_img, dtype=np.float32)
    h, w = arr.shape[0], arr.shape[1]
    mid = int(round(cx))
    shift = int(round(2.0 * eye_dx))  # left-eye → right-eye horizontal spacing
    if mid <= 0 or mid >= w or shift <= 0 or shift >= w:
        return face_img

    rgb = arr[..., :3]
    alpha = arr[..., 3]
    luma = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    # Threshold tight enough to isolate the near-pure-white catch-light dot
    # (drawn at 255,255,255) from the cream EYE_WHITE fill (luma ~246), so we
    # only move the sparkle, never the whole eye-white. The grain (amp ~14) can
    # nudge a pure-white dot down slightly, so >248 keeps the dot, drops the fill.
    spec = (luma > 248.0) & (alpha > 150.0)
    left_spec = spec & (np.arange(w)[None, :] < mid)
    if not bool(left_spec.any()):
        return face_img

    rows = np.where(left_spec.any(axis=1))[0]
    cols = np.where(left_spec.any(axis=0))[0]
    # Pad the catch-light bbox by 1px so its soft anti-aliased rim travels too.
    r0 = max(0, int(rows[0]) - 1)
    r1 = min(h, int(rows[-1]) + 2)
    c0 = max(0, int(cols[0]) - 1)
    c1 = min(mid, int(cols[-1]) + 2)
    # Destination box is the same rows, shifted right by `shift`; clip to width.
    dc0, dc1 = c0 + shift, c1 + shift
    if dc0 >= w:
        return face_img
    dc1 = min(w, dc1)
    span = dc1 - dc0
    if span <= 0:
        return face_img
    arr[r0:r1, dc0:dc1, :] = arr[r0:r1, c0 : c0 + span, :]

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def render_character(
    size: int,
    mood: str = DEFAULT_MOOD,
    anim_phase: float = 0.0,
    *,
    palette: str = "warm-sepia",
    sprite: Any | None = None,
) -> Any:
    """Render the anthropomorphized cell as an ``(size, size)`` PIL RGBA image.

    Args:
      size        output square edge in pixels (transparent background).
      mood        one of MOODS; unknown moods fall back to DEFAULT_MOOD.
      anim_phase  [0, 1) animation phase from the channel's clock. Drives a
                  gentle vertical breathing bob and a blink that fires once per
                  cycle. Deterministic: the same phase yields the same frame.
      palette     "warm-sepia" | "cool-mono" — tints the body to match the SEM
                  world via cellauto.renderer_sem.palette_lut.
      sprite      optional PIL RGBA image to use as the body (a generated
                  protagonist). When given, the procedural eyes / mouth /
                  highlight for ``mood`` are drawn on top; when None, the whole
                  character is drawn procedurally (blobby membrane body with a
                  nucleus, organelle speckles, rim light).

    Returns a PIL RGBA Image. Must never raise for valid sizes (>= 8); returns
    a fully-transparent image if PIL is unavailable.
    """
    try:
        from PIL import Image, ImageDraw, ImageFilter
    except ImportError:
        # Cannot build a real PIL image; hand back a duck-typed transparent one.
        return _TransparentStub(size)

    size = max(8, int(size))
    if mood not in _MOOD_FACES:
        mood = DEFAULT_MOOD

    # Animation: breathing bob (gentle vertical sinusoid) + blink openness.
    p = anim_phase - math.floor(anim_phase)
    bob = math.sin(p * 2.0 * math.pi) * (size * 0.025)
    openness = _blink_openness(p)

    # Supersample so anti-aliasing comes for free from the LANCZOS downscale.
    ss = _SUPERSAMPLE
    big = size * ss
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = big / 2.0
    cy = big / 2.0 + bob * ss

    # "reborn" gets a fresh, smaller body so it reads as a new-born cell.
    body_scale = 0.62 if mood == "reborn" else 1.0
    radius = big * 0.40 * body_scale

    body_rgb = _tint_color(_hex_to_rgb(BODY_TEAL), palette)
    hi_rgb = _tint_color(_hex_to_rgb(BODY_TEAL_HI), palette)

    if sprite is not None:
        # Use the supplied sprite as the body. Resize to fit the (bobbed) body
        # box, then tint it toward the palette so it matches the micrograph.
        try:
            spr = sprite if sprite.mode == "RGBA" else sprite.convert("RGBA")
            box = int(radius * 2.0)
            spr = spr.resize((box, box), Image.Resampling.LANCZOS)
            spr = _tint_sprite(spr, palette)
            img.alpha_composite(spr, (int(cx - box / 2), int(cy - box / 2)))
        except Exception:
            # If anything about the sprite is off, fall back to a drawn body so
            # we still honour "never raise".
            _draw_body(draw, cx, cy, radius, body_rgb, hi_rgb)
    else:
        _draw_body(draw, cx, cy, radius, body_rgb, hi_rgb)

    # Snapshot the body layer now (it holds ONLY the body — sprite or blob) so
    # the face can be clipped to its alpha silhouette before compositing. Guarded
    # so a copy failure never blocks the render.
    body_layer: Any | None = None
    try:
        body_layer = img.copy()
    except Exception:
        body_layer = None

    # Draw the per-mood face ON TOP (of either the sprite or the drawn body).
    face = _MOOD_FACES.get(mood, _MOOD_FACES[DEFAULT_MOOD])
    face_size = int(big * body_scale)  # faces are sized in big-pixels (reborn scales)
    # Route the face onto its OWN transparent RGBA layer so we can integrate the
    # eyes (grain + specular knock-down + body clip) before compositing. Each
    # step is independently guarded; ANY failure falls back to drawing the face
    # directly on ``img`` exactly as before — never raise into the render path.
    try:
        face_img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        face_draw = ImageDraw.Draw(face_img)
        face(face_draw, cx, cy, face_size, openness)
        try:
            face_img = _apply_eye_grain(face_img)
        except Exception:
            pass  # keep the un-grained face_img
        try:
            # Eye spacing mirrors _eye_geometry's dx = size * 0.16.
            face_img = _symmetrize_specular(face_img, cx, face_size * 0.16)
        except Exception:
            pass  # keep the (possibly grained) face_img
        try:
            face_img = _dim_specular(face_img)
        except Exception:
            pass  # keep the (possibly grained/symmetrised) face_img
        # CRITICAL: clip the face to the body silhouette so no eye/face pixel
        # can spill onto the background. Done LAST so grain/specular tweaks can't
        # re-introduce out-of-body pixels. Falls back to the unclipped face.
        if body_layer is not None:
            try:
                face_img = _clip_face_to_body(face_img, body_layer)
            except Exception:
                pass  # keep the un-clipped face_img (today's behaviour)
        img.alpha_composite(face_img, (0, 0))
    except Exception:
        # Layering failed wholesale: draw the face directly on img as today.
        face(draw, cx, cy, face_size, openness)

    # Soft edges: a tiny blur before downsampling smooths the polygon outline.
    img = img.filter(ImageFilter.GaussianBlur(ss * 0.4))
    out = img.resize((size, size), Image.Resampling.LANCZOS)
    return out


def _tint_sprite(spr: Any, palette: str) -> Any:
    """Tint a sprite's RGB toward the palette mid-tone, preserving its alpha.

    Uses numpy to blend each pixel toward the palette tone at its own
    luminance, so warm-sepia and cool-mono sprites read differently while
    keeping the sprite's shape and transparency.
    """
    import numpy as np

    from cellauto.renderer_sem import palette_lut

    arr = np.asarray(spr, dtype=np.float32)
    rgb = arr[..., :3]
    luma = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    lut = palette_lut(palette).astype(np.float32)
    idx = np.clip(luma, 0, 255).astype(np.int32)
    tone = lut[idx]
    strength = 0.5
    rgb_out = rgb * (1.0 - strength) + tone * strength
    arr[..., :3] = np.clip(rgb_out, 0, 255)

    from PIL import Image

    return Image.fromarray(arr.astype(np.uint8), "RGBA")
