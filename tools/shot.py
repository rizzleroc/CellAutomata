"""Throwaway visual-capture harness for the cellauto GUI.

Builds the real App, switches to a rule + grid, advances N steps, then grabs
the canvas region to a PNG via PIL.ImageGrab. Used during the v3.2 visual
overhaul to compare colony renderings before/after.

Usage:
    python tools/shot.py <rule> <grid> <steps> <out.png>
"""
from __future__ import annotations

import os
import sys
import tkinter as tk

# Ensure the v3.1 SOURCE package wins over any stale installed cellauto in
# site-packages. Running `python tools/shot.py` puts tools/ on sys.path[0],
# NOT the project root, so without this `import cellauto` can resolve to an
# old installed build (e.g. v3.0, which has none of the dark theme).
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJECT_ROOT)

from PIL import ImageGrab

from cellauto.app import App


def capture(rule: str, grid: int, steps: int, out: str) -> None:
    root = tk.Tk()
    app = App(root, rule_name=rule, grid_size=grid, seed=1234)
    root.geometry("+40+40")
    root.deiconify()
    root.lift()
    root.attributes("-topmost", True)
    root.focus_force()
    root.update()
    root.update_idletasks()
    for _ in range(steps):
        app._step_once()
    # Let the continuous animation (if any) run a few ticks.
    for _ in range(12):
        root.update()
        root.after(33)
        root.update_idletasks()
    root.update()
    root.after(200)
    root.update()
    # Full window grab — the whole museum-plate UI, not just the canvas.
    wx = root.winfo_rootx()
    wy = root.winfo_rooty()
    ww = root.winfo_width()
    wh = root.winfo_height()
    full = ImageGrab.grab(bbox=(wx, wy, wx + ww, wy + wh))
    fout = out.rsplit(".", 1)[0] + "-window.png"
    full.save(fout)
    print(f"saved {fout}  window=({wx},{wy},{ww},{wh})  size={full.size}")
    # Canvas-only grab for the zoomed cell inspection below.
    c = app.canvas
    x0 = c.winfo_rootx()
    y0 = c.winfo_rooty()
    x1 = x0 + c.winfo_width()
    y1 = y0 + c.winfo_height()
    img = ImageGrab.grab(bbox=(x0, y0, x1, y1))
    img.save(out)
    # Zoomed crop of ~7 cells from the image centre (pure canvas, avoids any
    # chrome that leaks into the grab bbox) so faces/animation are legible.
    cell_px = c.winfo_width() / grid
    crop_cells = min(7, grid)
    side = int(cell_px * crop_cells)
    iw, ih = img.size
    cx0 = (iw - side) // 2
    cy0 = (ih - side) // 2
    zoom = img.crop((cx0, cy0, cx0 + side, cy0 + side)).resize((side * 5, side * 5))
    zout = out.rsplit(".", 1)[0] + "-zoom.png"
    zoom.save(zout)
    print(f"saved {out}  bbox={x0,y0,x1,y1}  size={img.size}")
    print(f"saved {zout}  ({crop_cells} cells, {side}px -> {side*5}px)")
    root.destroy()


if __name__ == "__main__":
    rule = sys.argv[1] if len(sys.argv) > 1 else "natural-selection"
    grid = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    out = sys.argv[4] if len(sys.argv) > 4 else "shot.png"
    capture(rule, grid, steps, out)
