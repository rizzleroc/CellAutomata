"""Hi-res support (v4.1) — supersampled live render + high-resolution export.

The v4.0 SEM renderer upscaled the sim grid straight to the 600 px canvas. This
module decouples *render resolution* from *display resolution* so cellauto can:

  * supersample the live canvas (render the SEM + story channel at factor×600,
    then LANCZOS-downsample to 600) for crisper, anti-aliased on-screen output;
  * export a single composed frame as a high-resolution PNG (up to 4K) that is
    pixel-faithful to what the user sees, just larger and sharper;
  * export a high-resolution GIF/PNG sequence of the composed channel.

It is renderer-agnostic: callers pass a ``compose_at(size)`` callable that
returns an ``(size, size, 3)`` uint8 frame (``SemRenderer`` provides one). This
keeps hi-res orthogonal to both the SEM channel and the narrative channel.

Interface contract (locked):

    RenderScale(factor=1)                        — supersample config
      .render_px(base) -> int
    SCALE_PRESETS                                — dict label -> RenderScale
    supersample(compose_at, display_size, factor) -> np.ndarray  (display_size²,3)
    export_frame_png(rgb, path)                  — write a PNG (PIL)
    export_hires_png(compose_at, path, size)     — compose at `size`, write PNG
    export_hires_gif(frames, path, fps=...)      — write an animated GIF
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

# A frame factory: given an edge length in px, return an (edge, edge, 3) uint8
# RGB frame composed at that resolution.
ComposeAt = Callable[[int], np.ndarray]


@dataclass(frozen=True)
class RenderScale:
    """Supersampling configuration. ``factor`` is the integer multiple of the
    display size at which the scene is internally rendered before being
    downsampled for display."""

    factor: int = 1

    def __post_init__(self) -> None:
        if self.factor < 1:
            raise ValueError(f"RenderScale.factor must be >= 1, got {self.factor}")

    def render_px(self, base: int) -> int:
        return int(base) * int(self.factor)


# User-pickable supersample presets (View menu). Implementers may extend.
SCALE_PRESETS: dict[str, RenderScale] = {
    "1× (fast)": RenderScale(1),
    "2× (crisp)": RenderScale(2),
    "3× (max)": RenderScale(3),
}

# Hi-res export edge presets (File ▸ Export hi-res PNG…).
EXPORT_SIZES: dict[str, int] = {
    "1080²": 1080,
    "1440²": 1440,
    "2160² (4K)": 2160,
}


def supersample(compose_at: ComposeAt, display_size: int, factor: int) -> np.ndarray:
    """Render at ``display_size * factor`` via ``compose_at`` then LANCZOS-
    downsample to ``display_size``. ``factor == 1`` is a straight passthrough.

    Returns an ``(display_size, display_size, 3)`` uint8 array.

    AGENT(task #5): implement with PIL LANCZOS. Validate factor>=1; passthrough
    when factor==1. Keep dtype uint8 and shape exact.
    """
    if factor < 1:
        raise ValueError(f"supersample factor must be >= 1, got {factor}")

    if factor == 1:
        out = np.asarray(compose_at(display_size))
        return out.astype(np.uint8, copy=False).reshape(display_size, display_size, 3)

    from PIL import Image

    frame = np.asarray(compose_at(display_size * factor)).astype(np.uint8, copy=False)
    img = Image.fromarray(frame, mode="RGB")
    down = img.resize((display_size, display_size), Image.Resampling.LANCZOS)
    return np.asarray(down, dtype=np.uint8).reshape(display_size, display_size, 3)


def export_frame_png(rgb: np.ndarray, path: str) -> None:
    """Write an ``(H, W, 3)`` uint8 RGB array to ``path`` as a PNG via PIL.

    AGENT(task #5): implement. Validate ndim/shape; create parent dirs.
    """
    import pathlib

    arr = np.asarray(rgb)
    if arr.ndim != 3 or arr.shape[-1] != 3:
        raise ValueError(f"export_frame_png expects an (H, W, 3) array, got shape {arr.shape}")

    from PIL import Image

    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr.astype(np.uint8, copy=False), mode="RGB").save(path, format="PNG")


def export_hires_png(compose_at: ComposeAt, path: str, size: int) -> None:
    """Compose a single frame at ``size``×``size`` and write it as a PNG.

    AGENT(task #5): implement using compose_at(size) + export_frame_png.
    """
    frame = np.asarray(compose_at(size)).astype(np.uint8, copy=False)
    export_frame_png(frame, path)


def export_hires_gif(frames: list[np.ndarray], path: str, *, fps: float = 12.0) -> None:
    """Write a list of ``(H, W, 3)`` uint8 frames as an animated GIF via PIL.

    AGENT(task #5): implement. duration = 1000/fps ms, loop=0. Validate frames
    non-empty and same shape.
    """
    import pathlib

    if not frames:
        raise ValueError("export_hires_gif requires at least one frame")

    arrays = [np.asarray(f).astype(np.uint8, copy=False) for f in frames]
    first_shape = arrays[0].shape
    if any(a.shape != first_shape for a in arrays):
        raise ValueError("export_hires_gif requires all frames to share the same shape")

    from PIL import Image

    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    images = [Image.fromarray(a, mode="RGB") for a in arrays]
    duration = 1000.0 / fps
    images[0].save(
        path,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
    )
