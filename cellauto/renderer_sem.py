"""SEM-grade depth-shaded renderer (v4.0).

Same ``render(rgb_array)`` interface as :class:`cellauto.renderer.FieldRenderer`,
so :mod:`cellauto.app` can swap between viridis and SEM with a single attribute
flip. The underlying simulation is unchanged — every pixel still traces back
to a rule's ``render_rgb(state)`` output. SEM mode reinterprets the luminance
of that output as a height field and shades it as a 2.5-D micrograph.

Pipeline (per PRD §6 Phase 1):

  height = blur(luminance(rgb_array))
  ∇H = sobel(height)
  N  = normalise((-∂H/∂x, -∂H/∂y, 1))
  I  = ambient + Lambertian(N · L) + specular((N · H_half)^k)
  I -= ao_alpha * relu(laplacian(H))
  I += noise_alpha * value_noise()
  rgb = LUT[clip(I, 0, 1) * 255]
  composite sprites (optional, Phase 2)
  upscale to canvas via PIL LANCZOS
  overlay vignette, crosshair, "LIVE SEM FEED" badge, scale bar

Performance budget per PRD §F5: 20 FPS @ 60×60 on CPU. Hot path is numpy;
the LANCZOS upscale runs in C via Pillow.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

# --- Palette LUTs (S2) -----------------------------------------------------

PALETTE_WARM_SEPIA = "warm-sepia"
PALETTE_COOL_MONO = "cool-mono"

# Hex stops match PRD §4 F4. Interpolated to a 256-entry uint8 ramp.
_WARM_SEPIA_STOPS = np.array(
    [
        [0x2A, 0x22, 0x1C],  # deep substrate
        [0x4A, 0x3B, 0x30],  # mid-dark
        [0x8A, 0x6B, 0x4A],  # midtone
        [0xB0, 0x8E, 0x64],  # warm body
        [0xD8, 0xC0, 0x95],  # near-highlight
        [0xE6, 0xDC, 0xC5],  # bone cream
    ],
    dtype=np.float32,
)

_COOL_MONO_STOPS = np.array(
    [
        [0x0A, 0x0E, 0x16],  # obsidian
        [0x1B, 0x22, 0x2E],  # near-black
        [0x2A, 0x31, 0x40],  # midnight
        [0x5C, 0x6A, 0x82],  # slate
        [0x8A, 0x96, 0xAA],  # bone-gray
        [0xE6, 0xE0, 0xD0],  # warm white
    ],
    dtype=np.float32,
)

# Accent teal (Catalytic Silence) — reticle, "LIVE SEM FEED" badge.
ACCENT_TEAL = (0x39, 0xD4, 0xC8)
HAIRLINE_TEAL = (0x1F, 0x4F, 0x4C)


def _build_lut(stops: np.ndarray, gamma: float = 2.2) -> np.ndarray:
    """Interpolate a (k, 3) float stop table into a (256, 3) uint8 LUT.

    v4.0.4 B6 — gamma-biased mapping. ``t ** gamma`` (gamma > 1) makes the
    LUT spend MORE entries in the dark stops and FEWER in the bright stops,
    so a depth-shaded scene with a mostly-dark substrate + occasional
    bright dome apex maps the substrate into the dark stops (0-1) and the
    apex into the bright stops (4-5). The old linear ramp drove the whole
    substrate into the midtone-brown stops and never reached bone-cream.
    """
    t = np.linspace(0.0, 1.0, 256, dtype=np.float32)
    idx_f = (len(stops) - 1) * (t**gamma)
    lo = np.floor(idx_f).astype(np.int32)
    hi = np.minimum(lo + 1, len(stops) - 1)
    frac = (idx_f - lo)[..., None]
    rgb = stops[lo] * (1 - frac) + stops[hi] * frac
    return np.clip(rgb, 0, 255).astype(np.uint8)


_LUT_WARM_SEPIA = _build_lut(_WARM_SEPIA_STOPS)
_LUT_COOL_MONO = _build_lut(_COOL_MONO_STOPS)


def palette_lut(name: str) -> np.ndarray:
    if name == PALETTE_COOL_MONO:
        return _LUT_COOL_MONO
    return _LUT_WARM_SEPIA


# --- Capability detection (S8) ---------------------------------------------


def sem_is_available() -> tuple[bool, str]:
    """Detect whether the SEM renderer can run. Returns (ok, reason).

    Checked at app startup; if False the app falls back to FieldRenderer and
    emits a one-time toast. Never raises.
    """
    try:
        import PIL  # noqa: F401
        from PIL import Image

        if not hasattr(Image, "Resampling"):
            return False, "Pillow too old (no Resampling enum)"
        if not hasattr(Image.Resampling, "LANCZOS"):
            return False, "Pillow has no LANCZOS resampling"
    except Exception as exc:
        return False, f"Pillow import failed: {exc}"
    try:
        import numpy  # noqa: F401
    except Exception as exc:
        return False, f"numpy import failed: {exc}"
    return True, "ok"


# --- Numpy shading pipeline (S1) -------------------------------------------


def _luminance(rgb: np.ndarray) -> np.ndarray:
    """Rec.709 luminance → float32 in [0, 1]."""
    r = rgb[..., 0].astype(np.float32)
    g = rgb[..., 1].astype(np.float32)
    b = rgb[..., 2].astype(np.float32)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def _gaussian_blur_3x3(field: np.ndarray) -> np.ndarray:
    """Cheap separable 3×3 Gaussian. Sufficient for σ ≈ 0.7 small-grid smoothing.

    Avoids the scipy dependency (which PRD §F6 lists as optional). The kernel
    is [1, 2, 1] / 4 applied row then column.
    """
    k = np.array([1.0, 2.0, 1.0], dtype=np.float32) / 4.0
    padded = np.pad(field, 1, mode="edge")
    horiz = k[0] * padded[1:-1, :-2] + k[1] * padded[1:-1, 1:-1] + k[2] * padded[1:-1, 2:]
    padded_h = np.pad(horiz, 1, mode="edge")
    return k[0] * padded_h[:-2, 1:-1] + k[1] * padded_h[1:-1, 1:-1] + k[2] * padded_h[2:, 1:-1]


def _sobel(field: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Sobel gradients ∂/∂x, ∂/∂y on a 2-D float field, edge-padded."""
    padded = np.pad(field, 1, mode="edge")
    gx = (
        -padded[:-2, :-2]
        - 2.0 * padded[1:-1, :-2]
        - padded[2:, :-2]
        + padded[:-2, 2:]
        + 2.0 * padded[1:-1, 2:]
        + padded[2:, 2:]
    )
    gy = (
        -padded[:-2, :-2]
        - 2.0 * padded[:-2, 1:-1]
        - padded[:-2, 2:]
        + padded[2:, :-2]
        + 2.0 * padded[2:, 1:-1]
        + padded[2:, 2:]
    )
    return gx, gy


def _laplacian(field: np.ndarray) -> np.ndarray:
    """5-point Laplacian, edge-padded — used for ambient-occlusion in creases."""
    padded = np.pad(field, 1, mode="edge")
    return (
        padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:] - 4.0 * padded[1:-1, 1:-1]
    )


_VALUE_NOISE_CACHE: dict[tuple[int, int], np.ndarray] = {}
_VORONOI_NOISE_CACHE: dict[tuple[int, int, int], np.ndarray] = {}


def _voronoi_noise(h: int, w: int, density: int = 220) -> np.ndarray:
    """Cellular (F2 - F1) noise — produces angular faceted crystals.

    v4.0.4 B3 — substitute for the smooth value-noise substrate when the
    user wants "crystalline salt" texture instead of "velvet powder". For
    each output pixel, scatter ``density`` random seed points across the
    grid, compute F1 (nearest seed distance) and F2 (second-nearest), and
    use ``F2 - F1`` which produces sharp ridges along Voronoi-cell borders
    — visually identical to crystalline grain boundaries under SEM.
    Output in [-0.5, 0.5], deterministic by shape + density.

    Implementation note: a naive per-pixel nearest-two scan is O(W·H·D).
    For 720×720 with D=220 that's ~114 M ops — slow but cached, so this
    fires once per (h, w, density) tuple and stays free afterwards.
    """
    key = (h, w, density)
    cached = _VORONOI_NOISE_CACHE.get(key)
    if cached is not None:
        return cached
    rng = np.random.default_rng(20260527)
    seeds_y = rng.uniform(0, h, size=density).astype(np.float32)
    seeds_x = rng.uniform(0, w, size=density).astype(np.float32)
    ys = np.arange(h, dtype=np.float32).reshape(-1, 1, 1)
    xs = np.arange(w, dtype=np.float32).reshape(1, -1, 1)
    sy = seeds_y.reshape(1, 1, -1)
    sx = seeds_x.reshape(1, 1, -1)
    # Squared distance is cheaper and order-preserving for F1/F2.
    d2 = (ys - sy) ** 2 + (xs - sx) ** 2
    # Partition once for the two smallest values.
    part = np.partition(d2, 2, axis=-1)[..., :2]
    part.sort(axis=-1)
    f1 = np.sqrt(part[..., 0])
    f2 = np.sqrt(part[..., 1])
    out = (f2 - f1).astype(np.float32)
    out -= out.mean()
    std = out.std()
    if std > 1e-6:
        out /= std * 4.0  # ~[-0.5, 0.5] typical range
    _VORONOI_NOISE_CACHE[key] = out
    return out


def _contact_shadow(
    h: np.ndarray, *, foot_threshold: float = 0.45, base_threshold: float = 0.18
) -> np.ndarray:
    """v4.0.4 B5 — paint a soft darkening at the foot of each raised dome.

    For each pixel where ``base_threshold < h < foot_threshold`` (the "foot
    ring" between substrate and lit dome), the field's local height tells
    us how close that pixel is to a sphere's base; we darken those pixels
    proportionally. This is what visually anchors raised features to the
    substrate — without it, domes appear to float.

    Returns a [0, 1] shadow_field that ``shade_height`` subtracts BEFORE
    the AO pass.
    """
    band = (h > base_threshold) & (h < foot_threshold)
    if not band.any():
        return np.zeros_like(h)
    # Soft ramp inside the foot band: full shadow at h=foot_threshold/2,
    # fading to zero at the band edges.
    mid = 0.5 * (foot_threshold + base_threshold)
    half_width = 0.5 * (foot_threshold - base_threshold) + 1e-6
    ramp = 1.0 - np.abs(h - mid) / half_width
    ramp = np.clip(ramp, 0.0, 1.0)
    return np.where(band, ramp, 0.0).astype(np.float32)


def _value_noise(h: int, w: int, octaves: int = 4) -> np.ndarray:
    """Multi-octave value noise in [-0.5, 0.5], BILINEAR-interpolated. Cached
    by output shape.

    v4.0.3 audit fix: the previous implementation used nearest-neighbour
    integer indexing, producing visible blocky checkerboard artifacts at the
    coarsest octave. This version interpolates bilinearly so each octave's
    contribution is a smooth random field, and the sum reads as SEM grain
    rather than digital noise. Deterministic across calls (fixed seed).
    """
    key = (h, w)
    cached = _VALUE_NOISE_CACHE.get(key)
    if cached is not None:
        return cached
    rng = np.random.default_rng(20260525)
    out = np.zeros((h, w), dtype=np.float32)
    amp = 1.0
    norm = 0.0
    for o in range(octaves):
        # Octave's coarse-grid resolution doubles each step. Smallest is
        # ~h/8 cells across for octave 0 (broad clouds) up to ~h/(8/8)=h
        # cells across for octave 3 (per-pixel grain).
        small_h = max(2, h // (8 // max(2**o, 1) if (2**o) <= 8 else 1))
        small_w = max(2, w // (8 // max(2**o, 1) if (2**o) <= 8 else 1))
        small = rng.standard_normal((small_h, small_w)).astype(np.float32)
        # Bilinear interpolation: per output pixel, find the four nearest
        # source cells and blend by fractional position.
        ys = np.arange(h, dtype=np.float32) * (small_h - 1) / max(1, h - 1)
        xs = np.arange(w, dtype=np.float32) * (small_w - 1) / max(1, w - 1)
        y0 = np.clip(np.floor(ys), 0, small_h - 1).astype(np.int32)
        x0 = np.clip(np.floor(xs), 0, small_w - 1).astype(np.int32)
        y1 = np.clip(y0 + 1, 0, small_h - 1)
        x1 = np.clip(x0 + 1, 0, small_w - 1)
        ty = (ys - y0).reshape(-1, 1)
        tx = (xs - x0).reshape(1, -1)
        # Gather four corners and bilinear-blend.
        v00 = small[y0[:, None], x0[None, :]]
        v01 = small[y0[:, None], x1[None, :]]
        v10 = small[y1[:, None], x0[None, :]]
        v11 = small[y1[:, None], x1[None, :]]
        v0 = v00 * (1 - tx) + v01 * tx
        v1 = v10 * (1 - tx) + v11 * tx
        layer = v0 * (1 - ty) + v1 * ty
        out += amp * layer
        norm += amp
        amp *= 0.5
    out /= max(norm, 1e-6)
    out -= out.mean()
    std = out.std()
    if std > 1e-6:
        out /= std * 4.0  # ~[-0.5, 0.5] typical range
    _VALUE_NOISE_CACHE[key] = out
    return out


def shade_height(
    height: np.ndarray,
    *,
    light_dir: tuple[float, float, float] = (-0.25, -0.18, 0.95),
    ambient: float = 0.08,
    height_bias: float = 0.65,
    height_bias_exponent: float = 1.2,
    lambert_weight: float = 0.32,
    specular_strength: float = 0.15,
    specular_hardness: int = 24,
    ao_strength: float = 0.45,
    noise_strength: float = 0.05,
    gradient_scale: float = 4.0,
    substrate_kind: str = "crystalline",
    contact_shadow_strength: float = 0.30,
    height_remap: bool = True,
) -> np.ndarray:
    """Run the depth-shading pipeline on a 2-D float height field in [0, 1].

    Returns a float32 intensity field in [0, 1] (pre-LUT).

    **v4.0.2 audit fix (V1).** The v4.0.1 mix had ``ambient + lambert``
    summed un-weighted, so a flat background and a peak's flat top both
    saturated to 1.0 — the only visible feature was the lower-right shadow
    slope, which the visual cortex misread as the inside of a CRATER lit
    from upper-left. Fixed by:

    1. Light direction now points from upper-left (was lower-right) so the
       crater-vs-dome ambiguity resolves the right way.
    2. ``ambient`` reduced + Lambertian *weighted* (not added raw) so a
       flat background renders mid-grey, not saturated bright. This gives
       the dome's bright cap a value to be brighter THAN.
    3. New ``height_bias`` term: peaks contribute brightness directly,
       independent of slope. A 2-D Gaussian's centre has normal=(0,0,1)
       (same as flat ground), so Lambertian alone leaves the cap and the
       background identical. The height term gives the cap its lift.
    4. ``ao_strength`` halved — over-strong AO was darkening the inter-
       spot "valleys" so much that peaks read recessed by contrast.
    """
    if height.ndim != 2:
        raise ValueError(f"height field must be 2-D, got shape {height.shape}")

    raw = height.astype(np.float32)
    if height_remap:
        # v4.0.4 B4 — non-linear remap: crush the substrate range, stretch
        # the dome range. Without this, domes barely lift above the background
        # under the gamma-biased LUT (B6); with it, peaks stand proud.
        raw = np.where(raw > 0.15, 0.15 + (raw - 0.15) * 2.5, raw * 0.3).astype(np.float32)
    h = _gaussian_blur_3x3(raw)
    gx, gy = _sobel(h)
    gx *= gradient_scale
    gy *= gradient_scale

    # Normal map: N = normalise((-∂H/∂x, -∂H/∂y, 1)). Vectorised dot products
    # against the light direction give per-pixel Lambertian intensity.
    nz = np.ones_like(h)
    nx = -gx
    ny = -gy
    norm = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6

    lx, ly, lz = light_dir
    llen = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / llen, ly / llen, lz / llen

    lambert = np.clip((nx * lx + ny * ly + nz * lz) / norm, 0.0, 1.0)

    # Specular: halfway vector between light and a fixed eye = +z.
    hx = lx
    hy = ly
    hz = lz + 1.0
    hlen = math.sqrt(hx * hx + hy * hy + hz * hz)
    hx, hy, hz = hx / hlen, hy / hlen, hz / hlen
    cos_nh = np.clip((nx * hx + ny * hy + nz * hz) / norm, 0.0, 1.0)
    specular = specular_strength * (cos_nh**specular_hardness)

    # Three-term composition (v4.0.3 audit-driven walk-back): ambient
    # floor + NONLINEAR height-from-relief + weighted Lambertian.
    #
    # Why nonlinear height_bias: a linear bias makes the ENTIRE dome bright
    # (apex AND its slope contribute), which competes with the off-axis
    # Lambertian highlight and produces a "wet droplet on apex" effect.
    # Raising the exponent (>=1.6) concentrates the contribution at the
    # TOP of each dome, so the apex lifts above its slopes without
    # double-highlighting the lit-side flank.
    #
    # The light is also brought closer to overhead (lz=0.95) so the
    # Lambertian on the apex (normal=(0,0,1)) is high — clean dome reading
    # without ambiguity.
    # v4.0.4 R7 — keep Lambertian full-strength so dome flanks read as a
    # bodied sphere; gate ONLY specular so the substrate doesn't show
    # specular hotspots. Lambertian on flat ground with lz=0.95 only adds
    # ~0.30 baseline anyway, which after gamma=2.2 maps to dark stop 0 —
    # gating it was solving a non-problem at the cost of amputating dome
    # flanks. The earlier R1/R6 gating overshoot; this is the audit verdict.
    height_gate = 0.25 + 0.75 * np.clip(h * 2.5, 0.0, 1.0)
    intensity = (
        ambient + height_bias * (h**height_bias_exponent) + lambert_weight * lambert + specular * height_gate
    )

    # v4.0.4 B5 — contact shadow at each dome's foot, BEFORE AO. This is
    # what anchors raised features to the substrate.
    if contact_shadow_strength > 0.0:
        intensity -= contact_shadow_strength * _contact_shadow(h)

    # Ambient occlusion — concave regions (Laplacian > 0) get darker.
    lap = _laplacian(h)
    intensity -= ao_strength * np.clip(lap, 0.0, None)

    # Instrument micro-texture. v4.0.4 R2 — for "crystalline" substrate, MIX
    # high-density Voronoi (fine grain boundaries) with value-noise (smooth
    # bed). Pure Voronoi at density=220 read as a coarse tile mosaic; mixing
    # at density=1400 produces fine salt-crystal grain on a smooth substrate.
    if noise_strength > 0.0:
        if substrate_kind == "crystalline":
            tex = 0.5 * _voronoi_noise(h.shape[0], h.shape[1], density=1400) + 0.5 * _value_noise(
                h.shape[0], h.shape[1]
            )
        else:
            tex = _value_noise(h.shape[0], h.shape[1])
        intensity = intensity + noise_strength * tex

    return np.clip(intensity, 0.0, 1.0)


def apply_lut(intensity: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """Map a [0, 1] intensity field → (H, W, 3) uint8 RGB via LUT."""
    idx = np.clip(intensity * 255.0, 0, 255).astype(np.uint8)
    return lut[idx]


# Pink tint used by `_sprinkle_pink_variety` for the rare colored granules
# (B7) — dusty rose, breaks the pure-monochrome read without dominating.
_PINK_TINT = np.array([0xC8, 0x9A, 0x9A], dtype=np.float32)


def _sprinkle_pink_variety(rgb: np.ndarray, intensity: np.ndarray, fraction: float) -> np.ndarray:
    """v4.0.4 B7 — tint ~`fraction` of high-intensity pixels toward dusty pink.

    Goal: introduce the "Miller-Urey product class" colour variety the user
    reference image shows, without splattering pink everywhere. We pick
    pixels in the top 25% of intensity, then deterministic-RNG-sample
    `fraction` of those, blend their LUT colour halfway toward `_PINK_TINT`.
    Result: a few rosy granules / sphere-tops scattered through an
    otherwise monochrome warm-sepia frame.
    """
    if fraction <= 0.0:
        return rgb
    out = rgb.astype(np.float32)
    h, w = intensity.shape
    # v4.0.4 R3 — tighten the quantile so pink only lands on genuinely bright
    # pixels (dome highlights), not on every above-median substrate pixel.
    high_threshold = float(np.quantile(intensity, 0.92))
    mask = intensity > high_threshold
    if not mask.any():
        return rgb
    # Deterministic per-shape sampling — the same sim state always picks the
    # same pink pixels.
    rng = np.random.default_rng((h * 1_000_003 + w) & 0xFFFFFFFF)
    coin = rng.random(intensity.shape)
    pick = mask & (coin < fraction)
    if not pick.any():
        return rgb
    blend = 0.55
    out[pick] = out[pick] * (1.0 - blend) + _PINK_TINT * blend
    return np.clip(out, 0, 255).astype(np.uint8)


# --- Instrument framing overlay (S4) ---------------------------------------


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))


def overlay_instrument_chrome(
    img: Any,
    *,
    stage_label: str,
    palette: str,
    badge_alpha: float = 1.0,
    show_reticle: bool = True,
    show_badge: bool = True,
    show_scale: bool = True,
    show_vignette: bool = True,
    grid_extent: int = 60,
) -> Any:
    """Composite the LIVE SEM FEED instrument framing onto a PIL image.

    Per PRD §F2:
      • 1-px hairline teal crosshair reticle with quadrant midpoint ticks
      • "LIVE SEM FEED · Stage N — name" microcaps badge upper-right
      • "1 μm" scale-bar microcopy below canvas (length tracks grid_extent)
      • ~10% corner vignette suggesting curved aperture

    badge_alpha is the live opacity (S4 wires this to the 2.2-s playback pulse).
    """
    from PIL import Image, ImageDraw

    if img.mode != "RGBA":
        img = img.convert("RGBA")
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    accent = ACCENT_TEAL + (220,)
    hairline = HAIRLINE_TEAL + (200,)
    bone = (0xE6, 0xDC, 0xC5, 235) if palette == PALETTE_WARM_SEPIA else (0xE6, 0xE0, 0xD0, 235)

    if show_vignette:
        # Cheap radial vignette — 4 corner gradients via alpha-on-black squares.
        v_size = int(min(w, h) * 0.55)
        vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        vdraw = ImageDraw.Draw(vignette)
        cx, cy = w // 2, h // 2
        for r in range(0, v_size, 4):
            a = int(80 * (r / v_size) ** 2)
            box = (cx - (w // 2 + r), cy - (h // 2 + r), cx + (w // 2 + r), cy + (h // 2 + r))
            vdraw.rectangle(box, outline=(0, 0, 0, a), width=2)
        # Centre cutout — re-blank a central disc so the vignette is corners-only.
        cut = Image.new("L", (w, h), 0)
        cutd = ImageDraw.Draw(cut)
        cutd.ellipse(
            (cx - int(w * 0.45), cy - int(h * 0.45), cx + int(w * 0.45), cy + int(h * 0.45)),
            fill=255,
        )
        vignette.putalpha(Image.eval(cut, lambda v: 255 - v))
        overlay = Image.alpha_composite(overlay, vignette)
        draw = ImageDraw.Draw(overlay)

    if show_reticle:
        cx, cy = w // 2, h // 2
        arm = int(min(w, h) * 0.08)
        gap = int(min(w, h) * 0.012)
        draw.line((cx - arm, cy, cx - gap, cy), fill=hairline, width=1)
        draw.line((cx + gap, cy, cx + arm, cy), fill=hairline, width=1)
        draw.line((cx, cy - arm, cx, cy - gap), fill=hairline, width=1)
        draw.line((cx, cy + gap, cx, cy + arm), fill=hairline, width=1)
        # Quadrant midpoint tick marks.
        tick = int(min(w, h) * 0.015)
        for fx in (0.25, 0.75):
            for fy in (0.25, 0.75):
                tx, ty = int(w * fx), int(h * fy)
                draw.line((tx - tick, ty, tx + tick, ty), fill=hairline, width=1)
                draw.line((tx, ty - tick, tx, ty + tick), fill=hairline, width=1)

    # v4.0.3 — bump from w//56 to w//44 so the μ glyph in "1 μm" rasterises
    # cleanly at 720px canvases. At the old size 12 the μ was rendering as
    # tofu on some IBM Plex Mono builds.
    font = _load_mono_font(size=max(13, w // 44))
    if show_badge and font is not None:
        # v4.0.5 E0 — honesty pass. The earlier "LIVE SEM FEED" badge
        # implied an instrument feed; the rendering is a depth-shaded
        # interpretation of a simulation, not a measurement. science.md
        # already explicitly disclaims this — the badge now matches.
        text = f"SEM RENDER · {stage_label}"
        # Tracked, all-caps microcaps; text rendered onto its own RGBA layer
        # so we can pulse opacity per-frame without redrawing everything.
        badge = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        bdraw = ImageDraw.Draw(badge)
        bbox = bdraw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = w - tw - int(w * 0.024)
        y = int(h * 0.022)
        # Soft dark plate so the text reads on bright SEM frames.
        plate_pad_x = int(w * 0.012)
        plate_pad_y = int(h * 0.006)
        bdraw.rectangle(
            (x - plate_pad_x, y - plate_pad_y, x + tw + plate_pad_x, y + bbox[3] - bbox[1] + plate_pad_y),
            fill=(0, 0, 0, 90),
        )
        bdraw.text((x, y), text, font=font, fill=accent)
        # Small accent square left of the text (reads as "recording" dot).
        dot = int(font.size * 0.55)
        bdraw.rectangle(
            (x - plate_pad_x - dot - 6, y + 2, x - plate_pad_x - 6, y + 2 + dot),
            fill=accent,
        )
        if badge_alpha < 1.0:
            alpha = badge.split()[-1].point(lambda v: int(v * badge_alpha))
            badge.putalpha(alpha)
        overlay = Image.alpha_composite(overlay, badge)
        draw = ImageDraw.Draw(overlay)

    if show_scale and font is not None:
        # Length: scaled so a 60-grid sim shows ~1/6 of canvas as "1 μm",
        # bigger grids show a longer bar. Capped to a sensible range.
        bar_px = int(w * min(0.30, max(0.10, 18.0 / max(grid_extent, 12))))
        bar_y = int(h * 0.965)
        bar_x0 = int(w * 0.04)
        bar_x1 = bar_x0 + bar_px
        draw.line((bar_x0, bar_y, bar_x1, bar_y), fill=bone, width=2)
        draw.line((bar_x0, bar_y - 4, bar_x0, bar_y + 4), fill=bone, width=2)
        draw.line((bar_x1, bar_y - 4, bar_x1, bar_y + 4), fill=bone, width=2)
        label = _scale_bar_label(font)
        draw.text((bar_x1 + 8, bar_y - font.size + 2), label, font=font, fill=bone)

        # v4.0.5 E0 — honesty disclaimer at the very bottom, dim and small,
        # tied to the scale bar so it reads as a footnote, not a feature.
        # The earlier "LIVE SEM FEED" badge implied instrument-feed truth;
        # this single footnote keeps the badge stylistically present while
        # being honest about what the user is actually looking at.
        disclaimer = "Render of simulated chemistry — not a microscope image."
        dim_bone = (bone[0], bone[1], bone[2], 150)
        small_font = _load_mono_font(size=max(10, w // 70))
        if small_font is not None:
            dis_bbox = draw.textbbox((0, 0), disclaimer, font=small_font)
            dis_w = dis_bbox[2] - dis_bbox[0]
            draw.text(
                ((w - dis_w) // 2, bar_y + 8),
                disclaimer,
                font=small_font,
                fill=dim_bone,
            )

    return Image.alpha_composite(img, overlay).convert("RGB")


# --- Sprite library (S6 — Phase 2) ----------------------------------------

_SPRITE_CACHE: dict[tuple[str, str], Any] = {}
_SPRITE_DIR_OVERRIDE: str | None = None


def set_sprite_dir(path: str | None) -> None:
    """Override the sprite asset root (used by tests). ``None`` restores default."""
    global _SPRITE_DIR_OVERRIDE
    _SPRITE_DIR_OVERRIDE = path
    _SPRITE_CACHE.clear()


def _sprite_root() -> Any:
    from pathlib import Path

    if _SPRITE_DIR_OVERRIDE is not None:
        return Path(_SPRITE_DIR_OVERRIDE)
    return Path(__file__).resolve().parent / "assets" / "sprites"


def load_sprite(name: str, palette: str) -> Any:
    """Load and palette-tint a sprite. Returns a PIL RGBA Image or None.

    ``name`` is the asset-relative path (e.g. "stage1/spot.png").
    Tinting multiplies the sprite's RGB by the LUT's mid-tone colour so warm
    and cool palettes share one sprite source asset.
    """
    key = (name, palette)
    if key in _SPRITE_CACHE:
        return _SPRITE_CACHE[key]
    from PIL import Image, ImageOps

    path = _sprite_root() / name
    if not path.is_file():
        _SPRITE_CACHE[key] = None
        return None
    src = Image.open(str(path)).convert("RGBA")
    lut = palette_lut(palette)
    lo = tuple(int(x) for x in lut[110])  # sprite shadow → mid stop, not black
    hi = tuple(int(x) for x in lut[250])  # sprite highlight → near bone-cream
    grey = ImageOps.grayscale(src)
    tinted = ImageOps.colorize(grey, black=lo, white=hi).convert("RGBA")
    # keep the source alpha, but pull opaque fills back ~10% so solid sprites read
    # as specimen film (like the translucent Stage-3 vesicle) instead of hard discs
    alpha = src.split()[-1].point(lambda v: int(v * 0.9))
    tinted.putalpha(alpha)
    _SPRITE_CACHE[key] = tinted
    return tinted


def composite_sprites(
    img: Any,
    sprites: list,
    *,
    palette: str,
    grid_w: int,
    grid_h: int,
) -> Any:
    """Alpha-composite sprite instances over the depth-shaded background.

    ``sprites`` is a list of (sim_x, sim_y, name, scale) tuples — sim_x/sim_y
    in sim-grid coordinates, scale is a multiplier on the sprite's native
    size. Out-of-image sprites are clipped silently.
    """
    from PIL import Image, ImageFilter

    if img.mode != "RGBA":
        img = img.convert("RGBA")
    cw, ch = img.size
    for sim_x, sim_y, name, scale in sprites:
        sprite = load_sprite(name, palette)
        if sprite is None:
            continue
        target_w = max(2, int(sprite.width * float(scale)))
        target_h = max(2, int(sprite.height * float(scale)))
        s = sprite.resize((target_w, target_h), Image.Resampling.LANCZOS)
        # Sim-grid → canvas-pixel mapping (centre-anchored)
        px = int((sim_x + 0.5) * cw / max(grid_w, 1)) - target_w // 2
        py = int((sim_y + 0.5) * ch / max(grid_h, 1)) - target_h // 2
        # Soft offset contact shadow so the sprite sits ON the substrate
        # instead of floating. Light is upper-left → shadow falls down-right.
        sa = s.split()[-1].point(lambda v: int(v * 0.5))  # half-strength alpha
        shadow_sprite = Image.new("RGBA", s.size, (0, 0, 0, 0))
        shadow_sprite.putalpha(sa)
        blur_r = max(2, int(target_h * 0.12))
        shadow_sprite = shadow_sprite.filter(ImageFilter.GaussianBlur(blur_r))
        dx = int(target_w * 0.06)
        dy = int(target_h * 0.10)
        shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        shadow_layer.alpha_composite(shadow_sprite, (px + dx, py + dy))
        img = Image.alpha_composite(img, shadow_layer)  # shadow under the sprite
        img.alpha_composite(s, (px, py))  # then the sprite
    return img


def _scale_bar_label(font: Any) -> str:
    """v4.0.3 — return "1 μm" if the font has U+03BC, else fall back to
    "1 um". Detected by drawing the glyph onto a small probe image and
    checking that at least one pixel of ink lands. Cached per-font.
    """
    if font is None:
        return "1 um"
    cached = getattr(font, "_cellauto_scale_label", None)
    if cached is not None:
        return cached
    try:
        from PIL import Image as _Image
        from PIL import ImageDraw as _ImageDraw

        probe = _Image.new("L", (24, 24), 0)
        _ImageDraw.Draw(probe).text((2, 2), "μ", font=font, fill=255)
        # If the font has no glyph for μ, Pillow draws nothing OR a tofu
        # box. A box draws lots of pixels around the perimeter; a real μ
        # draws strokes in the interior. Heuristic: ink count differs.
        ink = sum(probe.getdata())
        # Compare to ink count for a glyph we KNOW is present (the digit 1).
        probe2 = _Image.new("L", (24, 24), 0)
        _ImageDraw.Draw(probe2).text((2, 2), "1", font=font, fill=255)
        ink_1 = sum(probe2.getdata())
        # If μ-ink is < 25% of "1"-ink (extremely sparse / blank) OR very
        # close to a tofu rectangle's ink, fall back.
        label = "1 μm" if (ink > 0 and 0.4 * ink_1 < ink < 4.0 * ink_1) else "1 um"
    except Exception:
        label = "1 um"
    try:
        font._cellauto_scale_label = label  # type: ignore[attr-defined]
    except Exception:
        pass
    return label


_FONT_CACHE: dict[int, Any] = {}
_SERIF_CACHE: dict[tuple[int, bool], Any] = {}


def _load_mono_font(size: int) -> Any:
    """Best-effort monospace font load. Returns None if Pillow has no font path
    that resolves on this OS (text overlay is then skipped silently).
    """
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]
    from PIL import ImageFont

    # Try IBM Plex Mono shipped with cellauto first, then OS fallbacks.
    candidates = [
        _shipped_mono_path(),
        "consola.ttf",
        "Consolas.ttf",
        "DejaVuSansMono.ttf",
        "Menlo.ttc",
    ]
    for c in candidates:
        if not c:
            continue
        try:
            font = ImageFont.truetype(c, size=size)
            _FONT_CACHE[size] = font
            return font
        except Exception:
            continue
    try:
        default_font: Any = ImageFont.load_default()
        _FONT_CACHE[size] = default_font
        return default_font
    except Exception:
        return None


def _load_serif_font(size: int, italic: bool = False) -> Any:
    """Best-effort serif font load (CrimsonPro shipped with cellauto, then OS
    fallbacks). Mirrors :func:`_load_mono_font` and reuses the same
    ``assets/fonts`` directory.

    Never returns None: if no serif resolves on this OS it falls back to the
    mono font for ``size`` so the title/narration hierarchy still rests on the
    size ratio. Cached by ``(size, italic)``. Never raises.
    """
    key = (size, italic)
    if key in _SERIF_CACHE:
        return _SERIF_CACHE[key]
    from pathlib import Path

    from PIL import ImageFont

    base = Path(__file__).resolve().parent / "assets" / "fonts"
    name = "CrimsonPro-Italic.ttf" if italic else "CrimsonPro-Regular.ttf"
    candidates = [str(base / name), "Georgia.ttf", "DejaVuSerif.ttf"]
    for c in candidates:
        try:
            font = ImageFont.truetype(c, size=size)
            _SERIF_CACHE[key] = font
            return font
        except Exception:
            continue
    # Graceful fallback: the mono font keeps the size-driven hierarchy intact.
    font = _load_mono_font(size)
    _SERIF_CACHE[key] = font
    return font


def _shipped_mono_path() -> str | None:
    import os
    from pathlib import Path

    here = Path(__file__).resolve().parent / "assets" / "fonts"
    if not here.is_dir():
        return None
    for fname in os.listdir(here):
        if "Mono" in fname and fname.lower().endswith(".ttf"):
            return str(here / fname)
    return None


# --- Renderer class (S1 + S3 hook surface) ---------------------------------


@dataclass
class SemRenderer:
    """Drop-in replacement for :class:`FieldRenderer` with SEM-grade shading.

    Public surface:
      reset(width, height) — called by app.py on rule change
      render(rgb_array)    — called per step with the rule's render_rgb output
      set_palette(name)    — swap LUT (warm-sepia | cool-mono)
      set_stage_label(s)   — update the badge text on stage promotion
      set_reduced_motion(b)— disable the badge pulse (PRD §F2)
      set_running(b)       — toggle badge pulse on/off with playback state
    """

    canvas: Any
    canvas_size: int
    palette: str = PALETTE_WARM_SEPIA
    stage_label: str = "Stage 0 — soup"
    reduced_motion: bool = False
    running: bool = False
    show_chrome: bool = True

    # v4.1 hi-res: when > canvas_size, the live frame is composed at this edge
    # length and LANCZOS-downsampled to canvas_size for crisp, anti-aliased
    # display. 0 (or <= canvas_size) keeps the v4.0 1:1 behaviour.
    render_size: int = 0

    # v4.1 narrative channel: an optional post-compositor invoked on the
    # finished (chrome'd) frame inside compose(). Channel B
    # (cellauto.channel.NarrativeChannel.compose) installs itself here; when
    # None the SEM frame is returned untouched. Runs at the compose resolution
    # so the story overlay is hi-res too.
    post_compositor: Any = None

    # populated by reset()
    width: int = 0
    height: int = 0
    _image: Any = None
    _image_item: int = 0
    _t0: float = field(default_factory=time.monotonic)
    _last_rgb: np.ndarray | None = None
    # v4.1 — last pre-overlay (Channel-A only) composed frame, cached so the
    # narrative channel can re-animate over a static SEM frame without re-running
    # the (expensive) shade pipeline. See reanimate_overlay().
    _channel_a: np.ndarray | None = None

    # Knobs S5 / V1 tune for the Stage-1 hero pass. Exposed as attributes so
    # the hero pass + tests can poke them without touching shade_height
    # directly. The defaults below match `shade_height`'s v4.0.2 audit fix:
    # light from upper-left, weighted Lambertian + height-bias so peak
    # centres are brighter than the flat background (resolving the
    # crater-vs-dome ambiguity in favour of dome).
    light_dir: tuple[float, float, float] = (-0.25, -0.18, 0.95)
    ambient: float = 0.08
    # v4.0.4 audit: nonlinear height_bias (h**1.6) concentrates the
    # apex-brightening at the TOP of each dome; height_bias bumped 0.50→0.65
    # and ambient 0.12→0.08 so the substrate genuinely darkens (B4).
    height_bias: float = 0.65
    # v4.0.4 R8 — exponent 1.6 → 1.2 spreads the height_bias contribution
    # across the upper third of each dome instead of pinning it to the apex
    # pixel; eliminates the "stuck-on LED bead" reading the round-5 audit
    # called out as the final blocker.
    height_bias_exponent: float = 1.2
    lambert_weight: float = 0.32
    specular_strength: float = 0.15
    # v4.0.4 R5 — widen specular spot so the dome cap stays bright across
    # the whole apex instead of a hairline slash; was 24, now 12.
    specular_hardness: int = 12
    ao_strength: float = 0.45
    noise_strength: float = 0.05
    gradient_scale: float = 4.0
    # v4.0.4 B3 — substrate texture: "crystalline" = mixed Voronoi+value
    # (salt-crystal grain on smooth bed), "smooth" = value-noise (organic).
    # B5 — contact-shadow knob.
    substrate_kind: str = "crystalline"
    contact_shadow_strength: float = 0.30
    height_remap: bool = True
    # v4.0.4 R3 — sparse pink-tint variety. fraction lowered 0.03 → 0.008
    # so only ~6-10 pink granules show (was ~22, read as artifact).
    pink_variety: float = 0.008

    def reset(self, width: int, height: int) -> None:
        import tkinter as tk

        self.canvas.delete("all")
        self.width = width
        self.height = height
        self._image = tk.PhotoImage(width=self.canvas_size, height=self.canvas_size)
        self._image_item = self.canvas.create_image(
            self.canvas_size // 2,
            self.canvas_size // 2,
            image=self._image,
        )
        # Pillow PhotoImage anchors die without a held reference.
        self.canvas.image = self._image
        self._t0 = time.monotonic()

    def render(self, rgb_array: np.ndarray, sprites: list | None = None) -> None:
        target = (
            self.render_size if self.render_size and self.render_size > self.canvas_size else self.canvas_size
        )
        out = self.compose(rgb_array, sprites=sprites, out_size=target)
        if target != self.canvas_size:
            from PIL import Image

            out = np.asarray(
                Image.fromarray(out, "RGB").resize(
                    (self.canvas_size, self.canvas_size), Image.Resampling.LANCZOS
                ),
                dtype=np.uint8,
            )
        self._blit(out)

    def compose_at(self, rgb_array: np.ndarray, size: int, *, sprites: list | None = None) -> np.ndarray:
        """Compose a single frame at an arbitrary ``size``×``size`` edge length.

        Used by the hi-res export path (cellauto.hires) to produce a frame that
        matches the on-screen composition but at PNG/GIF resolution. The
        narrative-channel post-compositor (if installed) runs at ``size`` too,
        so the story overlay exports crisp.
        """
        return self.compose(rgb_array, sprites=sprites, out_size=size)

    def reanimate_overlay(self) -> None:
        """Re-apply the narrative post-compositor to the cached Channel-A frame
        and blit, WITHOUT re-running the SEM shade pipeline.

        This is the cheap per-tick path that lets Channel B (the protagonist +
        narration ribbon) keep breathing/typing while the simulation is paused
        — and between sim steps while it runs. No-op when there's no cached
        frame or no post-compositor installed (so it's safe to call blindly
        from the animation loop).
        """
        if self._channel_a is None or self.post_compositor is None:
            return
        out = self.post_compositor(self._channel_a)
        out = np.asarray(out, dtype=np.uint8)
        if out.shape[0] != self.canvas_size or out.shape[1] != self.canvas_size:
            from PIL import Image

            out = np.asarray(
                Image.fromarray(out, "RGB").resize(
                    (self.canvas_size, self.canvas_size), Image.Resampling.LANCZOS
                ),
                dtype=np.uint8,
            )
        self._blit(out)

    # ── Composition (separated so tests + PNG export can call it headlessly) ──

    def compose(
        self, rgb_array: np.ndarray, *, sprites: list | None = None, out_size: int | None = None
    ) -> np.ndarray:
        """Run the full SEM pipeline and return an (out, out, 3) uint8 RGB array
        where ``out`` is ``out_size`` (defaults to ``canvas_size``).
        Side-effect-free except for the noise cache.

        ``sprites`` is an optional list of (sim_x, sim_y, name, scale) tuples
        per PRD §F3; if supplied, sprites are alpha-composited over the
        depth-shaded background BEFORE the chrome overlay (so the chrome
        framing still reads through them).

        ``out_size`` lets the hi-res path (cellauto.hires) compose at an
        arbitrary edge length. The narrative-channel ``post_compositor`` (if
        installed) is applied to the finished frame at the compose resolution.
        """
        if rgb_array.ndim != 3 or rgb_array.shape[-1] != 3:
            raise ValueError(f"SemRenderer expects (H, W, 3) RGB, got {rgb_array.shape}")
        target = int(out_size) if out_size else self.canvas_size
        self._last_rgb = rgb_array

        h_field = _luminance(rgb_array)
        intensity = shade_height(
            h_field,
            light_dir=self.light_dir,
            ambient=self.ambient,
            height_bias=self.height_bias,
            height_bias_exponent=self.height_bias_exponent,
            lambert_weight=self.lambert_weight,
            specular_strength=self.specular_strength,
            specular_hardness=self.specular_hardness,
            ao_strength=self.ao_strength,
            noise_strength=self.noise_strength,
            gradient_scale=self.gradient_scale,
            substrate_kind=self.substrate_kind,
            contact_shadow_strength=self.contact_shadow_strength,
            height_remap=self.height_remap,
        )
        rgb_lut = apply_lut(intensity, palette_lut(self.palette))
        if self.pink_variety > 0.0:
            rgb_lut = _sprinkle_pink_variety(rgb_lut, intensity, self.pink_variety)

        from PIL import Image

        small = Image.fromarray(rgb_lut, mode="RGB")
        upscaled = small.resize((target, target), Image.Resampling.LANCZOS)
        if sprites:
            upscaled = composite_sprites(
                upscaled,
                sprites,
                palette=self.palette,
                grid_w=self.width,
                grid_h=self.height,
            )
        if self.show_chrome:
            upscaled = overlay_instrument_chrome(
                upscaled,
                stage_label=self.stage_label,
                palette=self.palette,
                badge_alpha=self._badge_alpha(),
                grid_extent=max(self.width, self.height),
            )
        out = np.asarray(upscaled, dtype=np.uint8)
        self._channel_a = out  # cache the pre-overlay frame for reanimate_overlay()
        if self.post_compositor is not None:
            out = self.post_compositor(out)
        return out

    def _blit(self, rgb_canvas: np.ndarray) -> None:
        """Push an (canvas_size, canvas_size, 3) uint8 array into the PhotoImage."""
        h, w = rgb_canvas.shape[:2]
        header = f"P6\n{w} {h}\n255\n".encode("ascii")
        body = rgb_canvas.astype(np.uint8, copy=False).tobytes()
        self._image.configure(data=header + body, format="PPM")

    def _badge_alpha(self) -> float:
        """2.2-s sinusoidal pulse while playing, full opacity while paused.
        Reduced-motion mode pins the badge at 0.85 opacity (no pulse).
        """
        if self.reduced_motion:
            return 0.85
        if not self.running:
            return 0.95
        phase = ((time.monotonic() - self._t0) % 2.2) / 2.2
        return 0.55 + 0.45 * (0.5 + 0.5 * math.sin(phase * 2.0 * math.pi))

    # ── App-facing setters ──────────────────────────────────────────────────

    def set_palette(self, name: str) -> None:
        if name not in (PALETTE_WARM_SEPIA, PALETTE_COOL_MONO):
            raise ValueError(f"unknown palette {name!r}")
        self.palette = name
        if self._last_rgb is not None:
            self.render(self._last_rgb)

    def set_stage_label(self, label: str) -> None:
        self.stage_label = label

    def set_reduced_motion(self, on: bool) -> None:
        self.reduced_motion = on

    def set_running(self, running: bool) -> None:
        self.running = running

    def set_show_chrome(self, on: bool) -> None:
        self.show_chrome = on
