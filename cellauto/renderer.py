"""Renderers — turn rule output into something a Tk canvas can show.

Two strategies:
  - DiscreteRenderer: per-cell rect/oval items on a tk.Canvas. Used by rules
    whose state is a coarse grid of distinct cells (Conway, Wolfram 1D, the
    Stage 0 soup rule). When cells are large enough (>= 18 px) and oval-shaped
    (the natural-selection rule's amoebas) the renderer paints little faces
    on top so the colony reads as a cuddly cartoon, not just coloured discs.
  - FieldRenderer: numpy array → tk.PhotoImage via PPM blit, displayed as a
    single canvas image. Used by continuous-field rules (Gray-Scott and the
    rest of the abiogenesis pipeline) where per-pixel updates are common.

Shape and face tracking happen in our own ``_items`` list so we never have to
ask Tk what we drew — that per-cell ``canvas.type()`` roundtrip was the
v2.0 perf regression noted in PHASE2_BRUTAL §1.2.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np

# Cell width (px) below which we skip face overlays — they'd be sub-pixel mush.
FACE_MIN_CELL_PX = 18


@dataclass
class _CellItems:
    """All canvas items owned by a single (x, y) cell."""
    body_id: int
    shape: str  # "rect" | "oval"
    face_ids: list[int] = field(default_factory=list)
    expression: str = ""  # "smile" | "wink" | "surprise" | ""


@dataclass
class DiscreteRenderer:
    """Persistent rect/oval items for discrete-cell rules."""
    canvas: Any
    canvas_size: int
    width: int = 0
    height: int = 0
    _items: list[list[_CellItems]] = field(default_factory=list)
    _cw: float = 0.0
    _ch: float = 0.0
    _faces_enabled: bool = False

    def reset(self, width: int, height: int) -> None:
        self.canvas.delete("all")
        self.width = width
        self.height = height
        self._cw = self.canvas_size / width
        self._ch = self.canvas_size / height
        self._faces_enabled = self._cw >= FACE_MIN_CELL_PX
        self._items = [
            [
                _CellItems(
                    body_id=self.canvas.create_rectangle(
                        x * self._cw, y * self._ch,
                        (x + 1) * self._cw, (y + 1) * self._ch,
                        fill="#000000", outline=""),
                    shape="rect",
                )
                for x in range(width)
            ]
            for y in range(height)
        ]

    def render(self, render_cell: Callable[[int, int], tuple[str, str]]) -> None:
        cw, ch = self._cw, self._ch
        for y in range(self.height):
            for x in range(self.width):
                color, shape = render_cell(x, y)
                item = self._items[y][x]
                if shape != item.shape:
                    # Body shape changed — recreate the body, clear any face.
                    self.canvas.delete(item.body_id)
                    for fid in item.face_ids:
                        self.canvas.delete(fid)
                    item.face_ids.clear()
                    item.expression = ""
                    x1, y1 = x * cw, y * ch
                    x2, y2 = x1 + cw, y1 + ch
                    if shape == "oval":
                        item.body_id = self.canvas.create_oval(
                            x1, y1, x2, y2, fill=color, outline="")
                    else:
                        item.body_id = self.canvas.create_rectangle(
                            x1, y1, x2, y2, fill=color, outline="")
                    item.shape = shape
                else:
                    self.canvas.itemconfigure(item.body_id, fill=color)

                # Faces only on amoebas, only when the cells are large enough
                # for the features to actually read.
                if self._faces_enabled and shape == "oval":
                    if not item.face_ids:
                        item.expression = self._expression_for(x, y)
                        self._draw_face(x, y, item, color)
                elif item.face_ids:
                    for fid in item.face_ids:
                        self.canvas.delete(fid)
                    item.face_ids.clear()
                    item.expression = ""

    # ── Face drawing ────────────────────────────────────────────────────────

    @staticmethod
    def _expression_for(x: int, y: int) -> str:
        """Deterministic per-cell expression based on (x, y).  Same cell
        keeps the same face across frames so the colony has stable
        personalities."""
        h = (x * 73856093 ^ y * 19349663) & 0xFFFF
        roll = h % 100
        if roll < 78:
            return "smile"
        if roll < 90:
            return "wink"
        return "surprise"

    def _draw_face(self, x: int, y: int, item: _CellItems, body_color: str) -> None:
        cw, ch = self._cw, self._ch
        cx = x * cw + cw / 2
        cy = y * ch + ch / 2

        # Geometry tuned to look balanced from ~18px to ~40px cells.
        eye_dx = cw * 0.20
        eye_dy = -ch * 0.10
        eye_white_r = max(1.5, cw * 0.13)
        pupil_r = max(0.8, eye_white_r * 0.55)
        eye_color = "#ffffff"
        pupil_color = "#0a0e16"

        items: list[int] = []
        canvas = self.canvas

        # Pick a slight darker outline so eyes register against pale cells.
        outline = "#0a0e16" if _is_light_color(body_color) else ""

        if item.expression == "wink":
            # Left eye open, right eye closed (a thin curved line).
            items.append(canvas.create_oval(
                cx - eye_dx - eye_white_r, cy + eye_dy - eye_white_r,
                cx - eye_dx + eye_white_r, cy + eye_dy + eye_white_r,
                fill=eye_color, outline=outline, width=1))
            items.append(canvas.create_oval(
                cx - eye_dx - pupil_r, cy + eye_dy - pupil_r,
                cx - eye_dx + pupil_r, cy + eye_dy + pupil_r,
                fill=pupil_color, outline=""))
            items.append(canvas.create_arc(
                cx + eye_dx - eye_white_r, cy + eye_dy - eye_white_r,
                cx + eye_dx + eye_white_r, cy + eye_dy + eye_white_r,
                start=10, extent=160, style="arc", outline=pupil_color, width=1))
        else:
            # Two normal eyes.
            for sx in (-1, 1):
                items.append(canvas.create_oval(
                    cx + sx * eye_dx - eye_white_r, cy + eye_dy - eye_white_r,
                    cx + sx * eye_dx + eye_white_r, cy + eye_dy + eye_white_r,
                    fill=eye_color, outline=outline, width=1))
                items.append(canvas.create_oval(
                    cx + sx * eye_dx - pupil_r, cy + eye_dy - pupil_r,
                    cx + sx * eye_dx + pupil_r, cy + eye_dy + pupil_r,
                    fill=pupil_color, outline=""))

        # Mouth.
        mouth_w = cw * 0.28
        mouth_h = ch * 0.20
        if item.expression == "surprise":
            mouth_r = max(1.0, cw * 0.10)
            items.append(canvas.create_oval(
                cx - mouth_r, cy + ch * 0.18 - mouth_r,
                cx + mouth_r, cy + ch * 0.18 + mouth_r,
                fill=pupil_color, outline=""))
        else:
            items.append(canvas.create_arc(
                cx - mouth_w / 2, cy + ch * 0.06,
                cx + mouth_w / 2, cy + ch * 0.06 + mouth_h,
                start=200, extent=140, style="arc",
                outline=pupil_color, width=max(1, int(cw / 14))))

        item.face_ids = items


def _is_light_color(hex_color: str) -> bool:
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
    except (ValueError, IndexError):
        return False
    # rec601 luma
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    return luma > 170


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
