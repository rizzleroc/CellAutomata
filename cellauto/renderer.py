"""Renderers — turn rule output into something a Tk canvas can show.

Two strategies:
  - DiscreteRenderer: per-cell rect/oval items on a tk.Canvas. Used by rules
    whose state is a coarse grid of distinct cells (Conway, Wolfram 1D, the
    Stage 0 soup rule).
  - FieldRenderer: numpy array → tk.PhotoImage via PPM blit, displayed as a
    single canvas image. Used by continuous-field rules (Gray-Scott and the
    rest of the abiogenesis pipeline) where per-pixel updates are common.

The shape-tracking in DiscreteRenderer fixes one of the Phase 2 P0 bugs: v2.0's
app.py called canvas.type(item) on every cell every frame to decide whether
to swap a rect for an oval, which produced a per-cell Tk roundtrip and made
the new renderer actually slower than v1's canvas.delete('all'). Here we track
the shape ourselves in _items so the only Tk calls are the ones that actually
need to fire.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class DiscreteRenderer:
    """Persistent rect/oval items for discrete-cell rules."""
    canvas: Any
    canvas_size: int
    width: int = 0
    height: int = 0
    # Tracks (item_id, shape) per cell, so we don't have to ask Tk what we drew.
    _items: list[list[tuple[int, str]]] = field(default_factory=list)

    def reset(self, width: int, height: int) -> None:
        self.canvas.delete("all")
        self.width = width
        self.height = height
        cw = self.canvas_size / width
        ch = self.canvas_size / height
        self._items = [
            [
                (self.canvas.create_rectangle(x * cw, y * ch, (x + 1) * cw, (y + 1) * ch,
                                              fill="#000000", outline=""), "rect")
                for x in range(width)
            ]
            for y in range(height)
        ]

    def render(self, render_cell: Callable[[int, int], tuple[str, str]]) -> None:
        cw = self.canvas_size / self.width
        ch = self.canvas_size / self.height
        for y in range(self.height):
            for x in range(self.width):
                color, shape = render_cell(x, y)
                item_id, current_shape = self._items[y][x]
                if shape != current_shape:
                    # Shape changed — must recreate the canvas item.
                    self.canvas.delete(item_id)
                    x1, y1 = x * cw, y * ch
                    x2, y2 = x1 + cw, y1 + ch
                    if shape == "oval":
                        new_id = self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline="")
                    else:
                        new_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                    self._items[y][x] = (new_id, shape)
                else:
                    self.canvas.itemconfigure(item_id, fill=color)


@dataclass
class FieldRenderer:
    """numpy → PhotoImage blit for continuous fields.

    The rule provides an (H, W, 3) uint8 RGB array per step. We pack it into a
    PPM byte string and load it as a tk.PhotoImage. PhotoImage redraws the
    whole image in one Tk call regardless of size — much faster than per-pixel
    canvas items above ~50×50.
    """
    canvas: Any
    canvas_size: int
    _image: Any = None
    _image_item: int = 0

    def reset(self, width: int, height: int) -> None:
        import tkinter as tk
        self.canvas.delete("all")
        # PhotoImage is sized to the source array; we scale up by drawing it
        # at the canvas's full size via a zoom + the canvas image coords.
        self._image = tk.PhotoImage(width=width, height=height)
        self._scale = max(1, self.canvas_size // max(width, height))
        zoomed = self._image.zoom(self._scale, self._scale)
        # Keep both — we update _image then re-zoom each frame.
        self._zoomed = zoomed
        self._image_item = self.canvas.create_image(
            self.canvas_size // 2, self.canvas_size // 2, image=zoomed,
        )
        # Tkinter PhotoImage objects need a held reference to survive GC.
        self.canvas.image = zoomed

    def render(self, rgb_array: np.ndarray) -> None:
        h, w = rgb_array.shape[:2]
        # Build a PPM-format byte string Tk can ingest.
        header = f"P6\n{w} {h}\n255\n".encode("ascii")
        body = rgb_array.astype(np.uint8).tobytes()
        self._image.configure(data=header + body, format="PPM")
        # Re-zoom and swap the canvas image to refresh.
        zoomed = self._image.zoom(self._scale, self._scale)
        self.canvas.itemconfigure(self._image_item, image=zoomed)
        self.canvas.image = zoomed
        self._zoomed = zoomed


def cmap_viridis(values: np.ndarray) -> np.ndarray:
    """Map a [0, 1] float array → (H, W, 3) uint8 RGB using a viridis-ish ramp.

    Tiny built-in colormap so we don't add matplotlib as a dependency. The 5
    control colors are a coarse sampling of the real viridis palette.
    """
    stops = np.array([
        [68, 1, 84],     # dark purple
        [59, 82, 139],   # blue
        [33, 144, 141],  # teal
        [94, 201, 98],   # green
        [253, 231, 37],  # yellow
    ], dtype=np.float32)
    v = np.clip(values, 0.0, 1.0)
    # Linear interpolation between stops.
    idx = v * (len(stops) - 1)
    lo = np.floor(idx).astype(np.int32)
    hi = np.minimum(lo + 1, len(stops) - 1)
    frac = (idx - lo)[..., None]
    rgb = stops[lo] * (1 - frac) + stops[hi] * frac
    return rgb.astype(np.uint8)
