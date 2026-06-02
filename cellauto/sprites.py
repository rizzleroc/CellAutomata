"""Optional generated-body-sprite provider for the narrative channel (v4.1).

This is the bridge between externally-generated "AAA" protagonist art and
Channel B (``cellauto.channel.NarrativeChannel``). It loads a pre-rendered
protagonist cutout from an on-disk asset directory, chroma-keys its flat
background to transparency, and exposes a ``stage -> PIL RGBA`` callback that
plugs straight into ``NarrativeChannel.set_sprite_provider``.

Design contract — the grounded build never *depends* on these files:

  * If the asset directory is missing, empty, or every candidate fails to
    load, :func:`build_sprite_provider` returns ``None`` and the channel keeps
    its fully-procedural body (``cellauto.character`` draws the blob). So the
    shipped repo, with no generated art on disk, behaves exactly as before.
  * The body sprite is the SAME protagonist for every stage. Per-mood
    expression is drawn procedurally by ``character.render_character`` *on top*
    of the supplied body, so a single clean cutout lifts the whole
    day-in-the-life arc. Optional ``protagonist_<mood>.png`` variants are used
    when present, but are never required.
  * Every public function is total: it returns ``None`` rather than raising, so
    a malformed PNG can never crash the render loop.

The art pipeline that fills the directory generates each plate on a flat pure
chroma-magenta field (``#FF00FF``) — a colour that never occurs in the
grayscale / sepia / teal SEM subject — which :func:`chroma_key` lifts to alpha
with a feathered, de-spilled edge.

A PNG that already carries a genuine alpha channel (a true cutout, e.g. art
exported with real transparency rather than a flat key colour) is honoured
directly: :func:`load_body_sprite` detects meaningful per-pixel transparency
and uses it as-is, skipping the chroma key. So both keyable magenta plates and
real-alpha cutouts drop in without code changes.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from cellauto.narrative import DAY_IN_THE_LIFE

# Named key colours the art pipeline can paint behind the subject. Magenta
# stays the default for back-compat; green keys grayscale/sepia subjects far
# more cleanly (no magenta in a gray subject's blue+red, so spill suppression
# is gentler on soft edges).
MAGENTA_KEY: tuple[int, int, int] = (255, 0, 255)
GREEN_KEY: tuple[int, int, int] = (0, 255, 0)
CHROMA_KEY: tuple[int, int, int] = MAGENTA_KEY  # legacy alias / default

# Filenames tried for a stage, in priority order. ``{mood}`` is the stage's
# narrative mood (see cellauto.narrative.DAY_IN_THE_LIFE); the bare names are
# the single-sprite fallbacks shared by every stage.
_CANDIDATES: tuple[str, ...] = (
    "protagonist_{mood}.png",
    "protagonist.png",
    "protagonist_idle.png",
    "cell_protagonist_idle.png",
)

# (abs_path, mtime_ns, matte, key, tol_in, tol_out) -> RGBA image | None
_SPRITE_CACHE: dict[tuple[str, int, str, tuple[int, int, int] | None, int, int], Any] = {}


def default_asset_dir() -> Path:
    """Where narrative body sprites live. Overridable with the
    ``CELLAUTO_SPRITE_DIR`` environment variable (absolute path)."""
    env = os.environ.get("CELLAUTO_SPRITE_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent / "assets" / "narrative"


def stage_mood(stage: int) -> str:
    """Resolve a stage index to its narrative mood, clamped into range.

    The provider only receives a stage (not the pipeline length), so this
    treats ``stage`` as an extended-arc index — correct for the 12-stage
    pipeline and a harmless approximation for the canonical 5-stage one, where
    the body sprite is identical across moods anyway."""
    beats = DAY_IN_THE_LIFE
    if not beats:
        return "curious"
    idx = 0 if stage < 0 else len(beats) - 1 if stage >= len(beats) else stage
    return beats[idx].mood


def chroma_key(
    img: Any,
    *,
    key: tuple[int, int, int] = CHROMA_KEY,
    tol_in: int = 48,
    tol_out: int = 120,
    min_keyed_fraction: float = 0.12,
    despill: float = 0.85,
    fringe_kill: float = 0.85,
    fringe_alpha_ceil: float = 0.7,
    fringe_dominance: int = 24,
) -> Any | None:
    """Lift a flat ``key``-coloured background to transparency.

    Returns a NEW RGBA ``PIL.Image`` whose background pixels are fully
    transparent with a feathered, de-spilled edge, or ``None`` when the image
    doesn't actually sit on a ``key`` field (fewer than ``min_keyed_fraction``
    of pixels within the key band) — the caller then falls back to the
    procedural body rather than compositing an opaque rectangle.

    Alpha ramps from 0 at colour-distance ``tol_in`` (pure key) to 1 at
    ``tol_out`` (definitely subject). De-spill is *channel-aware*: only the
    spilling key channel(s) are pulled back toward the mean of the others, so
    soft cilia that legitimately carry some of the key hue are not chewed.

    Fringe-kill (the final pass) attacks the residual saturated-key rim that
    de-spill alone leaves on soft hair/cilia: for TRANSLUCENT edge pixels
    (``0 < alpha < fringe_alpha_ceil``) whose colour is STILL dominated by the
    key hue (key channels' mean exceeding the non-key channel mean by more than
    ``fringe_dominance``), alpha is pulled toward 0 in proportion to that excess
    dominance, scaled by ``fringe_kill``. Opaque subject pixels and pixels that
    have already lost the key hue are untouched, so magenta-tinted fringe fades
    out instead of remaining as a coloured rim. Conservative by construction;
    set ``fringe_kill`` to 0.0 to disable.
    """
    try:
        import numpy as np
        from PIL import Image

        rgb = np.asarray(img.convert("RGB"), dtype=np.float32)
        keyv = np.asarray(key, dtype=np.float32).reshape(1, 1, 3)
        dist = np.sqrt(np.sum((rgb - keyv) ** 2, axis=-1))  # (H, W) 0..441

        span = float(max(1, tol_out - tol_in))
        alpha = np.clip((dist - float(tol_in)) / span, 0.0, 1.0)

        keyed_fraction = float(np.mean(alpha < 0.5))
        if keyed_fraction < min_keyed_fraction:
            # Background isn't the key colour — don't manufacture an opaque box.
            return None

        # Channel-aware de-spill. The "spill" channels are those the key drives
        # high (e.g. R&B for magenta, G for green). For each translucent pixel
        # we cap the spill channel at the mean of the NON-spill channels, but
        # only by as much as the edge is translucent — interior pixels untouched.
        keymax = float(max(key)) or 1.0
        spill_w = np.asarray(key, dtype=np.float32) / keymax  # 0..1 per channel
        spill_mask = spill_w > 0.5
        if spill_mask.any() and not spill_mask.all():
            ref = rgb[..., ~spill_mask].mean(axis=-1, keepdims=True)  # neutral ref
            edge = ((1.0 - alpha) * float(np.clip(despill, 0.0, 1.0)))[..., None]
            for c in np.where(spill_mask)[0]:
                ch = rgb[..., c]
                capped = np.minimum(ch, ref[..., 0])
                rgb[..., c] = ch + (capped - ch) * edge[..., 0]
        else:
            # Degenerate key (all-channels or none) — fall back to luminance pull.
            lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
            mix = ((1.0 - alpha) * float(np.clip(despill, 0.0, 1.0)))[..., None]
            rgb = rgb * (1.0 - mix) + lum[..., None] * mix

        # Fringe-kill: erase the residual saturated-key rim on soft cilia. After
        # de-spill, a magenta-tinted fringe still reads with its key channels
        # (R&B) well above the non-key mean (G); de-spill can't fully neutralise
        # it without chewing genuine soft hair. Here we instead fade the ALPHA of
        # such pixels — but only in the translucent band and only where the key
        # hue still clearly dominates, so opaque subject pixels are never eaten.
        # TOTAL: any failure leaves ``alpha`` at its pre-fringe-kill value.
        try:
            fk = float(np.clip(fringe_kill, 0.0, 1.0))
            if fk > 0.0 and spill_mask.any() and not spill_mask.all():
                key_mean = rgb[..., spill_mask].mean(axis=-1)  # key-channel mean
                non_mean = rgb[..., ~spill_mask].mean(axis=-1)  # neutral mean
                dominance = key_mean - non_mean  # >0 when key hue persists
                thr = float(max(0, fringe_dominance))
                # Normalise excess dominance over [thr, thr+96] -> 0..1.
                excess = np.clip((dominance - thr) / 96.0, 0.0, 1.0)
                ceil = float(np.clip(fringe_alpha_ceil, 0.0, 1.0))
                # Only translucent edge pixels (0 < alpha < ceil) are eligible;
                # ramp the gate to 0 as alpha approaches the ceiling so we never
                # step on near-opaque subject.
                band = np.clip((ceil - alpha) / max(ceil, 1e-3), 0.0, 1.0)
                band = band * (alpha > 0.0)
                cut = fk * excess * band  # fraction of alpha to remove, 0..1
                alpha = alpha * (1.0 - cut)
        except Exception:
            pass

        out = np.empty((rgb.shape[0], rgb.shape[1], 4), dtype=np.uint8)
        out[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        out[..., 3] = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
        return Image.fromarray(out, "RGBA")
    except Exception:
        return None


def luminance_key(
    img: Any,
    *,
    black_floor: int = 16,
    black_ceil: int = 64,
    min_keyed_fraction: float = 0.12,
    unmix: float = 0.85,
) -> Any | None:
    """Matte a subject shot on a NEAR-BLACK background by its luminance.

    Returns a NEW RGBA ``PIL.Image`` where dark background pixels become
    transparent (feathered) and the subject stays opaque, or ``None`` when the
    frame isn't actually a black-background plate (fewer than
    ``min_keyed_fraction`` of pixels below ``black_ceil`` luminance) — so a
    bright/flat image falls through to the procedural body.

    Alpha ramps 0 -> 1 across luminance ``[black_floor, black_ceil]``. Edge
    pixels are "un-mixed": the residual black lift is divided back out so dim
    rim pixels read as the subject's true colour instead of a muddy grey halo.
    """
    try:
        import numpy as np
        from PIL import Image

        rgb = np.asarray(img.convert("RGB"), dtype=np.float32)
        lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]

        span = float(max(1, black_ceil - black_floor))
        alpha = np.clip((lum - float(black_floor)) / span, 0.0, 1.0)

        keyed_fraction = float(np.mean(alpha < 0.5))
        if keyed_fraction < min_keyed_fraction:
            # Not a dark-background plate — don't matte a bright image.
            return None

        # Un-premultiply against black: colour / alpha recovers the subject's
        # true colour at translucent rim pixels (which black-bg compositing has
        # darkened). Blend by ``unmix`` and only where alpha is in (0,1).
        a = alpha[..., None]
        safe = np.maximum(a, 1e-3)
        recovered = np.clip(rgb / safe, 0, 255)
        k = float(np.clip(unmix, 0.0, 1.0))
        edge = k * (1.0 - a) * (a > 0.0)  # weight: most at faint rim, 0 at core
        rgb = rgb * (1.0 - edge) + recovered * edge

        out = np.empty((rgb.shape[0], rgb.shape[1], 4), dtype=np.uint8)
        out[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        out[..., 3] = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
        return Image.fromarray(out, "RGBA")
    except Exception:
        return None


def has_real_alpha(img: Any, *, min_transparent_fraction: float = 0.04, alpha_thresh: int = 24) -> bool:
    """True when ``img`` already carries a genuine alpha cutout.

    Returns ``True`` when at least ``min_transparent_fraction`` of pixels are
    near-fully transparent (alpha ``<= alpha_thresh``), i.e. the PNG was
    exported with real transparency rather than a flat key colour. Such images
    are used as-is and must NOT be chroma-keyed (there is no key field to lift,
    and keying a transparent edge would corrupt it)."""
    try:
        import numpy as np

        a = np.asarray(img.convert("RGBA"))[..., 3]
        return float(np.mean(a <= alpha_thresh)) >= min_transparent_fraction
    except Exception:
        return False


def _sniff_matte(img: Any) -> tuple[str, tuple[int, int, int] | None]:
    """Classify which matte ``img`` wants from its corners + alpha.

    Returns one of:
      ("alpha", None)            -> already a real cutout, use as-is
      ("chroma", GREEN_KEY)      -> saturated green corners
      ("chroma", MAGENTA_KEY)    -> saturated magenta corners
      ("luminance", None)        -> near-black, low-saturation corners
      ("none", None)             -> no confident background; procedural fallback

    Samples a patch in each corner (mean, robust to noise) rather than a single
    pixel. Never raises."""
    try:
        import numpy as np

        if has_real_alpha(img):
            return ("alpha", None)

        rgb = np.asarray(img.convert("RGB"), dtype=np.float32)
        h, w = rgb.shape[:2]
        ph = max(1, h // 12)
        pw = max(1, w // 12)
        corners = np.concatenate(
            [
                rgb[:ph, :pw].reshape(-1, 3),
                rgb[:ph, -pw:].reshape(-1, 3),
                rgb[-ph:, :pw].reshape(-1, 3),
                rgb[-ph:, -pw:].reshape(-1, 3),
            ],
            axis=0,
        )
        mean = corners.mean(axis=0)  # (3,) average corner colour
        r, g, b = float(mean[0]), float(mean[1]), float(mean[2])
        mx, mn = max(r, g, b), min(r, g, b)
        sat = mx - mn  # cheap saturation proxy 0..255
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b

        # Near-black & not strongly coloured -> luminance/black-bg plate.
        if lum < 48.0 and sat < 48.0:
            return ("luminance", None)

        # Strongly saturated corners -> chroma. Pick the key by dominant hue.
        if sat >= 80.0:
            if g > r and g > b:
                return ("chroma", GREEN_KEY)
            if r > g and b > g:  # red & blue high, green low
                return ("chroma", MAGENTA_KEY)
        return ("none", None)
    except Exception:
        return ("none", None)


# ---------------------------------------------------------------------------
# Turn a sniff/override into an actual matte. ``matte`` may be "auto"
# (default), "alpha", "chroma", "luminance", or "none"; ``key`` forces the
# chroma colour. Filename hints win over the pixel sniff.
# ---------------------------------------------------------------------------

_NAME_HINTS: tuple[tuple[str, str], ...] = (
    ("_green", "chroma:green"),
    ("_chromagreen", "chroma:green"),
    ("_magenta", "chroma:magenta"),
    ("_chroma", "chroma:magenta"),
    ("_black", "luminance"),
    ("_luma", "luminance"),
    ("_dark", "luminance"),
    ("_alpha", "alpha"),
    ("_cutout", "alpha"),
)


def matte_image(
    img: Any,
    *,
    matte: str = "auto",
    key: tuple[int, int, int] | None = None,
    name_hint: str | None = None,
    tol_in: int = 48,
    tol_out: int = 120,
) -> Any | None:
    """Apply the appropriate matte to ``img`` and return RGBA, or ``None``.

    Resolution order: explicit ``matte``/``key`` > filename hint > pixel sniff.
    Total — never raises."""
    try:
        mode = (matte or "auto").lower()

        # Filename hint can pin the mode when auto.
        if mode == "auto" and name_hint:
            low = name_hint.lower()
            for needle, tag in _NAME_HINTS:
                if needle in low:
                    if tag.startswith("chroma:"):
                        mode = "chroma"
                        if key is None:
                            key = GREEN_KEY if tag.endswith("green") else MAGENTA_KEY
                    else:
                        mode = tag
                    break

        if mode == "auto":
            sniffed, skey = _sniff_matte(img)
            mode = sniffed
            if key is None:
                key = skey

        if mode == "alpha":
            from PIL import Image  # noqa: F401  (ensure PIL present)

            return img.convert("RGBA")
        if mode == "chroma":
            return chroma_key(img, key=key or CHROMA_KEY, tol_in=tol_in, tol_out=tol_out)
        if mode == "luminance":
            return luminance_key(img)
        return None  # "none" / unknown -> procedural fallback
    except Exception:
        return None


def _square_trim(img: Any, *, alpha_floor: int = 16, pad_frac: float = 0.06) -> Any | None:
    """Crop ``img`` (RGBA) to its alpha bounding box, then centre it on a
    transparent square so a later square resize preserves aspect ratio.
    Returns ``None`` if the image is effectively empty."""
    try:
        import numpy as np
        from PIL import Image

        arr = np.asarray(img)
        a = arr[..., 3]
        ys, xs = np.where(a > alpha_floor)
        if ys.size == 0 or xs.size == 0:
            return None
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        crop = img.crop((x0, y0, x1, y1))
        w, h = crop.size
        side = max(w, h)
        pad = int(side * pad_frac)
        side += 2 * pad
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.alpha_composite(crop, ((side - w) // 2, (side - h) // 2))
        return canvas
    except Exception:
        return None


def load_body_sprite(
    path: str | Path,
    *,
    matte: str = "auto",
    key: tuple[int, int, int] | None = None,
    tol_in: int = 48,
    tol_out: int = 120,
) -> Any | None:
    """Load, matte and square-trim a protagonist body PNG.

    Returns an RGBA ``PIL.Image`` ready to hand to
    ``character.render_character(sprite=...)``, or ``None`` on any failure
    (missing file, unreadable PNG, wrong/absent background for the chosen
    matte, empty subject). The matte mode is resolved by :func:`matte_image`
    (explicit ``matte``/``key`` > filename hint > pixel sniff), so green,
    black-background and magenta plates as well as real-alpha cutouts all drop
    in. Results are cached by ``(path, mtime, matte, key, tol_in, tol_out)`` so
    different matte requests for the same file never collide."""
    try:
        p = Path(path)
        if not p.is_file():
            return None
        ckey = (str(p.resolve()), p.stat().st_mtime_ns, matte, key, tol_in, tol_out)
        if ckey in _SPRITE_CACHE:
            return _SPRITE_CACHE[ckey]

        from PIL import Image

        with Image.open(p) as fh:
            fh.load()
            raw = fh.convert("RGBA")

        # matte_image runs the real-alpha-first check itself, so real cutouts
        # still win and only flat-key / black-bg plates are matted.
        keyed = matte_image(
            raw,
            matte=matte,
            key=key,
            name_hint=p.name,
            tol_in=tol_in,
            tol_out=tol_out,
        )
        if keyed is None:
            _SPRITE_CACHE[ckey] = None
            return None
        sprite = _square_trim(keyed)
        _SPRITE_CACHE[ckey] = sprite
        return sprite
    except Exception:
        return None


def resolve_sprite_path(asset_dir: Path, stage: int) -> Path | None:
    """First existing candidate file for ``stage`` in ``asset_dir`` (mood
    variant first, then the shared single-sprite fallbacks)."""
    mood = stage_mood(stage)
    for template in _CANDIDATES:
        candidate = asset_dir / template.format(mood=mood)
        if candidate.is_file():
            return candidate
    return None


def has_any_sprite(asset_dir: Path | None = None) -> bool:
    """True when at least one stage resolves to a real file on disk."""
    adir = asset_dir if asset_dir is not None else default_asset_dir()
    if not adir.is_dir():
        return False
    return any(resolve_sprite_path(adir, s) is not None for s in range(len(DAY_IN_THE_LIFE) or 1))


def build_sprite_provider(asset_dir: Path | None = None) -> Any | None:
    """Return a ``stage -> RGBA|None`` callback for
    ``NarrativeChannel.set_sprite_provider``, or ``None`` when no usable art
    is on disk (so the caller installs nothing and the procedural body stands).

    The returned callback is cheap: it resolves the stage to a path and loads
    through the module sprite cache, returning ``None`` for any stage whose art
    is missing or unkeyable (the channel then draws that stage procedurally).
    """
    adir = asset_dir if asset_dir is not None else default_asset_dir()
    if not has_any_sprite(adir):
        return None

    def _provider(stage: int) -> Any | None:
        try:
            path = resolve_sprite_path(adir, int(stage))
            if path is None:
                return None
            return load_body_sprite(path)
        except Exception:
            return None

    return _provider
