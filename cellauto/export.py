"""GIF export — Pillow renderer for both discrete and field frames."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

log = logging.getLogger(__name__)


def _frame_to_image(frame: dict) -> Image.Image:
    canvas = int(frame.get("canvas_size", 600))
    kind = frame.get("kind", "discrete")
    if kind == "field":
        rgb = np.array(frame["rgb"], dtype=np.uint8)
        h, w = rgb.shape[:2]
        img = Image.fromarray(rgb, mode="RGB")
        # Upscale to canvas size with nearest-neighbor so pixels stay crisp.
        if (w, h) != (canvas, canvas):
            img = img.resize((canvas, canvas), Image.Resampling.NEAREST)
        return img
    # Discrete frame.
    w = frame["width"]
    h = frame["height"]
    img = Image.new("RGB", (canvas, canvas), "white")
    draw = ImageDraw.Draw(img)
    cw = canvas / w
    ch = canvas / h
    for y in range(h):
        for x in range(w):
            color, shape = frame["cells"][y][x]
            x1, y1 = x * cw, y * ch
            x2, y2 = x1 + cw, y1 + ch
            if shape == "oval":
                draw.ellipse((x1, y1, x2, y2), fill=color)
            else:
                draw.rectangle((x1, y1, x2, y2), fill=color)
    return img


def export_gif(frames: Iterable[dict], path: str | Path, fps: int = 8) -> Path:
    frames = list(frames)
    if not frames:
        raise ValueError("no frames to export")
    images = [_frame_to_image(f) for f in frames]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    duration_ms = int(1000 / max(fps, 1))
    images[0].save(
        path,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )
    log.info("exported %d-frame GIF to %s @ %d fps", len(images), path, fps)
    return path
