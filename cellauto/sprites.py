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

# Default flat background colour the art pipeline paints behind the subject.
CHROMA_KEY: tuple[int, int, int] = (255, 0, 255)

# Filenames tried for a stage, in priority order. ``{mood}`` is the stage's
# narrative mood (see cellauto.narrative.DAY_IN_THE_LIFE); the bare names are
# the single-sprite fallbacks shared by every stage.
_CANDIDATES: tuple[str, ...] = (
    "protagonist_{mood}.png",
    "protagonist.png",
    "protagonist_idle.png",
    "cell_protagonist_idle.png",
)

# (abs_path, mtime_ns, key, tol_in, tol_out) -> RGBA image | None
_SPRITE_CACHE: dict[tuple[str, int, tuple[int, int, int], int, int], Any] = {}


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
) -> Any | None:
    """Lift a flat ``key``-coloured background to transparency.

    Returns a NEW RGBA ``PIL.Image`` whose background pixels are fully
    transparent with a feathered, de-spilled edge, or ``None`` when the image
    doesn't actually sit on a ``key`` field (fewer than ``min_keyed_fraction``
    of pixels within the key band) — in that case the caller should fall back
    to the procedural body rather than composite an opaque rectangle.

    The alpha ramps from 0 at colour-distance ``tol_in`` (pure key) to 1 at
    ``tol_out`` (definitely subject); edge pixels are desaturated toward their
    own luminance to kill magenta fringing.
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

        # De-spill: desaturate translucent edge pixels toward their luminance.
        lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
        mix = ((1.0 - alpha) * 0.85)[..., None]
        rgb = rgb * (1.0 - mix) + lum[..., None] * mix

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
    key: tuple[int, int, int] = CHROMA_KEY,
    tol_in: int = 48,
    tol_out: int = 120,
) -> Any | None:
    """Load, chroma-key and square-trim a protagonist body PNG.

    Returns an RGBA ``PIL.Image`` ready to hand to
    ``character.render_character(sprite=...)``, or ``None`` on any failure
    (missing file, unreadable PNG, no key background, empty subject). Results
    are cached by ``(path, mtime, key, tol_in, tol_out)``."""
    try:
        p = Path(path)
        if not p.is_file():
            return None
        ckey = (str(p.resolve()), p.stat().st_mtime_ns, key, tol_in, tol_out)
        if ckey in _SPRITE_CACHE:
            return _SPRITE_CACHE[ckey]

        from PIL import Image

        with Image.open(p) as fh:
            fh.load()
            raw = fh.convert("RGBA")

        # A real-alpha cutout is used directly; only flat-key plates are keyed.
        if has_real_alpha(raw):
            keyed: Any | None = raw
        else:
            keyed = chroma_key(raw, key=key, tol_in=tol_in, tol_out=tol_out)
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
