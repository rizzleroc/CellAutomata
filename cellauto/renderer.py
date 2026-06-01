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
FACE_MIN_CELL_PX = 16

EYE_WHITE = "#fdf6e3"  # warm white (matches the header mascot)
PUPIL = "#0a0e16"  # obsidian

# Face item indices within _CellItems.face_ids (fixed order so animate() can
# move individual features without querying the canvas).
_F_EYE_L, _F_EYE_R, _F_PUP_L, _F_PUP_R, _F_MOUTH = range(5)


@dataclass
class _CellItems:
    """All canvas items owned by a single (x, y) cell."""

    body_id: int
    shape: str  # "rect" | "oval"
    highlight_id: int | None = None
    face_ids: list[int] = field(default_factory=list)
    expression: str = ""  # "smile" | "surprise" | ""
    phase: float = 0.0  # per-cell animation phase so the colony isn't in sync
    blink_off: int = 0  # per-cell blink offset (frames)


@dataclass
class DiscreteRenderer:
    """Persistent rect/oval items for discrete-cell rules.

    Oval cells are the rule's "amoebas": they get a soft 3D highlight, a little
    face, and — when ``animate()`` is driven by a continuous tick — they
    breathe, bob and blink so the colony reads as a cuddly cartoon rather than
    a field of coloured dots. Each cell carries a deterministic phase/blink
    offset (hashed from x,y) so they move with their own personality instead of
    pulsing in lockstep.
    """

    canvas: Any
    canvas_size: int
    width: int = 0
    height: int = 0
    _items: list[list[_CellItems]] = field(default_factory=list)
    _cw: float = 0.0
    _ch: float = 0.0
    _faces_enabled: bool = False
    _frame: int = 0

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
                        x * self._cw,
                        y * self._ch,
                        (x + 1) * self._cw,
                        (y + 1) * self._ch,
                        fill="#000000",
                        outline="",
                    ),
                    shape="rect",
                    phase=self._hash01(x, y) * 6.2832,
                    blink_off=int(self._hash01(x + 7, y + 13) * 130),
                )
                for x in range(width)
            ]
            for y in range(height)
        ]

    @staticmethod
    def _hash01(x: int, y: int) -> float:
        """Deterministic [0,1) value from a cell coordinate."""
        h = (x * 73856093 ^ y * 19349663) & 0xFFFFFF
        return h / 0x1000000

    @property
    def animated(self) -> bool:
        """True when the colony has faces worth animating at this cell size."""
        return self._faces_enabled

    def render(self, render_cell: Callable[[int, int], tuple[str, str]]) -> None:
        for y in range(self.height):
            for x in range(self.width):
                color, shape = render_cell(x, y)
                item = self._items[y][x]
                if shape != item.shape:
                    self._rebuild_body(x, y, item, shape, color)
                else:
                    self.canvas.itemconfigure(item.body_id, fill=color)
                    if item.highlight_id is not None:
                        self.canvas.itemconfigure(item.highlight_id, fill=_lighten(color))

                # Faces + highlight only on amoebas, only when cells are large
                # enough for the features to actually read.
                if self._faces_enabled and shape == "oval":
                    if not item.face_ids:
                        item.expression = self._expression_for(x, y)
                        self._draw_face(x, y, item, color)
                elif item.face_ids:
                    for fid in item.face_ids:
                        self.canvas.delete(fid)
                    item.face_ids.clear()
                    item.expression = ""

    def _rebuild_body(self, x: int, y: int, item: _CellItems, shape: str, color: str) -> None:
        cw, ch = self._cw, self._ch
        self.canvas.delete(item.body_id)
        if item.highlight_id is not None:
            self.canvas.delete(item.highlight_id)
            item.highlight_id = None
        for fid in item.face_ids:
            self.canvas.delete(fid)
        item.face_ids.clear()
        item.expression = ""
        if shape == "oval":
            cx, cy, rx, ry = self._body_geom(x, y)
            item.body_id = self.canvas.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, fill=color, outline="")
            # Soft inner highlight — gives the amoeba a cuddly 3D sheen.
            hx, hy, hrx, hry = self._highlight_geom(cx, cy, rx, ry)
            item.highlight_id = self.canvas.create_oval(
                hx - hrx, hy - hry, hx + hrx, hy + hry, fill=_lighten(color), outline=""
            )
        else:
            item.body_id = self.canvas.create_rectangle(
                x * cw, y * ch, (x + 1) * cw, (y + 1) * ch, fill=color, outline=""
            )
        item.shape = shape

    # ── Geometry helpers (shared by draw + animate) ──────────────────────────

    def _body_geom(self, x: int, y: int) -> tuple[float, float, float, float]:
        cw, ch = self._cw, self._ch
        cx = x * cw + cw / 2
        cy = y * ch + ch / 2
        # Slightly inset so neighbouring amoebas read as individuals.
        return cx, cy, cw * 0.46, ch * 0.46

    @staticmethod
    def _highlight_geom(cx: float, cy: float, rx: float, ry: float) -> tuple[float, float, float, float]:
        return cx - rx * 0.30, cy - ry * 0.38, rx * 0.42, ry * 0.34

    def _face_geom(self, x: int, y: int) -> tuple[float, float, float, float, float, float]:
        cw, ch = self._cw, self._ch
        cx = x * cw + cw / 2
        cy = y * ch + ch / 2
        eye_dx = cw * 0.20
        eye_dy = -ch * 0.12
        ew = max(1.6, cw * 0.14)
        pr = max(0.9, ew * 0.55)
        return cx, cy, eye_dx, eye_dy, ew, pr

    @staticmethod
    def _expression_for(x: int, y: int) -> str:
        """Deterministic per-cell expression so each amoeba keeps its
        personality across frames."""
        h = (x * 73856093 ^ y * 19349663) & 0xFFFF
        return "surprise" if h % 100 >= 86 else "smile"

    def _draw_face(self, x: int, y: int, item: _CellItems, body_color: str) -> None:
        cx, cy, eye_dx, eye_dy, ew, pr = self._face_geom(x, y)
        cw, ch = self._cw, self._ch
        canvas = self.canvas
        outline = PUPIL if _is_light_color(body_color) else ""

        ids = [0, 0, 0, 0, 0]
        for slot, sx in ((_F_EYE_L, -1), (_F_EYE_R, 1)):
            ex = cx + sx * eye_dx
            ey = cy + eye_dy
            ids[slot] = canvas.create_oval(
                ex - ew, ey - ew, ex + ew, ey + ew, fill=EYE_WHITE, outline=outline, width=1
            )
        for slot, sx in ((_F_PUP_L, -1), (_F_PUP_R, 1)):
            ex = cx + sx * eye_dx
            ey = cy + eye_dy
            ids[slot] = canvas.create_oval(ex - pr, ey - pr, ex + pr, ey + pr, fill=PUPIL, outline="")

        if item.expression == "surprise":
            mr = max(1.0, cw * 0.10)
            ids[_F_MOUTH] = canvas.create_oval(
                cx - mr, cy + ch * 0.18 - mr, cx + mr, cy + ch * 0.18 + mr, fill=PUPIL, outline=""
            )
        else:
            mw = cw * 0.30
            ids[_F_MOUTH] = canvas.create_arc(
                cx - mw / 2,
                cy + ch * 0.05,
                cx + mw / 2,
                cy + ch * 0.05 + ch * 0.22,
                start=200,
                extent=140,
                style="arc",
                outline=PUPIL,
                width=max(1, int(cw / 14)),
            )
        item.face_ids = ids

    # ── Continuous animation ─────────────────────────────────────────────────

    def animate(self, frame: int) -> None:
        """Breathe / bob / blink every oval cell. Cheap: just coords() moves on
        items that already exist. Safe to call when faces are disabled (no-op)."""
        if not self._faces_enabled:
            return
        self._frame = frame
        import math

        canvas = self.canvas
        for y in range(self.height):
            row = self._items[y]
            for x in range(self.width):
                item = row[x]
                if item.shape != "oval":
                    continue
                ph = item.phase
                bob = math.sin(frame * 0.11 + ph) * (self._ch * 0.045)
                breath = math.sin(frame * 0.08 + ph * 1.3) * 0.07
                cx, cy, rx, ry = self._body_geom(x, y)
                cyb = cy + bob
                bx = rx * (1.0 + breath)
                by = ry * (1.0 - breath * 0.6)
                canvas.coords(item.body_id, cx - bx, cyb - by, cx + bx, cyb + by)
                if item.highlight_id is not None:
                    hx, hy, hrx, hry = self._highlight_geom(cx, cyb, bx, by)
                    canvas.coords(item.highlight_id, hx - hrx, hy - hry, hx + hrx, hy + hry)
                if item.face_ids:
                    blinking = ((frame + item.blink_off) % 132) < 6
                    self._animate_face(x, y, item, cyb, blinking)

    def _animate_face(self, x: int, y: int, item: _CellItems, cyb: float, blinking: bool) -> None:
        cx, cy, eye_dx, eye_dy, ew, pr = self._face_geom(x, y)
        cw, ch = self._cw, self._ch
        canvas = self.canvas
        ey = cyb + eye_dy
        ids = item.face_ids
        for slot, pslot, sx in ((_F_EYE_L, _F_PUP_L, -1), (_F_EYE_R, _F_PUP_R, 1)):
            ex = cx + sx * eye_dx
            if blinking:
                canvas.coords(ids[slot], ex - ew, ey - 0.8, ex + ew, ey + 0.8)
                canvas.coords(ids[pslot], ex, ey, ex, ey)
                canvas.itemconfigure(ids[pslot], fill="")
            else:
                canvas.coords(ids[slot], ex - ew, ey - ew, ex + ew, ey + ew)
                canvas.coords(ids[pslot], ex - pr, ey - pr, ex + pr, ey + pr)
                canvas.itemconfigure(ids[pslot], fill=PUPIL)
        if item.expression == "surprise":
            mr = max(1.0, cw * 0.10)
            my = cyb + ch * 0.18
            canvas.coords(ids[_F_MOUTH], cx - mr, my - mr, cx + mr, my + mr)
        else:
            mw = cw * 0.30
            my = cyb + ch * 0.05
            canvas.coords(ids[_F_MOUTH], cx - mw / 2, my, cx + mw / 2, my + ch * 0.22)


def _lighten(hex_color: str, amount: float = 0.42) -> str:
    """Blend a colour toward white — used for the amoeba highlight sheen."""
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
    except (ValueError, IndexError):
        return hex_color
    r = int(r + (255 - r) * amount)
    g = int(g + (255 - g) * amount)
    b = int(b + (255 - b) * amount)
    return f"#{r:02x}{g:02x}{b:02x}"


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
            self.canvas_size // 2,
            self.canvas_size // 2,
            image=zoomed,
        )
        # Tkinter PhotoImage objects need a held reference to survive GC.
        self.canvas.image = zoomed

    def render(self, rgb_array: np.ndarray) -> None:
        import tkinter as tk

        h, w = rgb_array.shape[:2]
        # ``configure(data=...)`` writes into the existing PhotoImage without
        # resizing it, so a frame whose size differs from the one reset() built
        # would be clipped. Rebuild the backing image when the size changes —
        # this lets a rule render at (near) canvas resolution (e.g. the Stage
        # XIII SEM feed at 600×600) while grid-sized fields keep their old size.
        if self._image.width() != w or self._image.height() != h:
            self._image = tk.PhotoImage(width=w, height=h)
        # Build a PPM-format byte string Tk can ingest.
        header = f"P6\n{w} {h}\n255\n".encode("ascii")
        body = rgb_array.astype(np.uint8).tobytes()
        self._image.configure(data=header + body, format="PPM")
        # Recompute the integer zoom from the ACTUAL frame size so the SEM feed
        # displays ~1:1 while grid-sized fields still scale up to fill the canvas.
        self._scale = max(1, self.canvas_size // max(w, h))
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
    stops = np.array(
        [
            [68, 1, 84],  # dark purple
            [59, 82, 139],  # blue
            [33, 144, 141],  # teal
            [94, 201, 98],  # green
            [253, 231, 37],  # yellow
        ],
        dtype=np.float32,
    )
    v = np.clip(values, 0.0, 1.0)
    # Linear interpolation between stops.
    idx = v * (len(stops) - 1)
    lo = np.floor(idx).astype(np.int32)
    hi = np.minimum(lo + 1, len(stops) - 1)
    frac = (idx - lo)[..., None]
    rgb = stops[lo] * (1 - frac) + stops[hi] * frac
    return rgb.astype(np.uint8)
