"""Live SPRITE compositor for Stage XIII — the runtime half of the 2.5D
billboard pipeline.

The expensive part (photoreal, path-traced translucent cells with subsurface
scattering) is baked OFFLINE by ``tools/bake_life_sprites.py`` into a committed
sprite atlas under ``cellauto/assets/life/``. This module loads that atlas and
composites the sprites cheaply with plain Pillow — rotated by each organism's
heading, scaled by its energy, depth-sorted with contact shadows and
depth-of-field, on the lit granular substrate, finished with a warm filmic
grade. The one dividing cell uses the teal sprite (the single colour accent).

So the look is genuinely photoreal while the **runtime has no Mitsuba / GPU
dependency** — it only blits PNGs. ``phase`` (the engine step) drives a gentle
rotation wobble and scale pulse so the colony reads as alive frame-to-frame,
on top of the organisms actually moving as the simulation steps.

If the baked atlas is missing (e.g. a source checkout that never ran the bake),
:func:`load_atlas` raises ``FileNotFoundError`` and the Stage XIII rule falls
back to the procedural :mod:`life_sem` renderer.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageFilter

from cellauto.rules.abiogenesis import life_sem as _ls

_ASSETS = Path(__file__).resolve().parents[2] / "assets" / "life"


@lru_cache(maxsize=1)
def load_atlas() -> tuple[list[Image.Image], Image.Image]:
    """Load and slice the committed sprite atlas (cached). Returns the list of
    cell sprites and the teal division sprite. Raises ``FileNotFoundError`` if
    the bake hasn't been run."""
    sheet_path = _ASSETS / "cells.png"
    meta_path = _ASSETS / "atlas.json"
    div_path = _ASSETS / "cell_div.png"
    if not (sheet_path.exists() and meta_path.exists() and div_path.exists()):
        raise FileNotFoundError(f"Stage XIII sprite atlas not found in {_ASSETS}")
    meta = json.loads(meta_path.read_text())
    cols, tile, count = meta["cols"], meta["tile"], meta["count"]
    sheet = Image.open(sheet_path).convert("RGBA")
    cells = []
    for i in range(count):
        x, y = (i % cols) * tile, (i // cols) * tile
        cells.append(sheet.crop((x, y, x + tile, y + tile)))
    return cells, Image.open(div_path).convert("RGBA")


def render(
    state: Any,
    rule: Any,
    width: int = 600,
    height: int = 600,
    max_org: int = 28,
    seed: int = 0,
    phase: float = 0.0,
) -> np.ndarray:
    """Composite the live population from the baked photoreal sprite atlas.
    Returns an ``(height, width, 3)`` uint8 array. Raises ``FileNotFoundError``
    (via :func:`load_atlas`) if the atlas is absent so the caller can fall back."""
    cells, div_sprite = load_atlas()
    rng = np.random.RandomState(seed & 0x7FFFFFFF)
    sub = _ls._substrate(width, height, rng)
    canvas = Image.fromarray(np.clip(sub, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    gh, gw = state.substrate.shape
    base_r = min(width, height) * 0.085
    orgs = sorted(state.organisms.values(), key=lambda o: -o.energy)[:max_org]
    div_oid = max(orgs, key=lambda o: (o.n_divisions, o.energy)).oid if orgs else None
    margin = 0.09
    placed = []
    for o in orgs:
        depth = o.y / max(1, gh - 1)
        cx = (margin + (1 - 2 * margin) * (o.x / max(1, gw - 1))) * width
        cy = (margin + (1 - 2 * margin) * depth) * height
        ef = min(o.energy / max(rule.e_div, 1e-6), 1.6)
        r = base_r * (0.7 + 0.5 * depth) * (0.85 + 0.35 * ef)
        placed.append((depth, o, cx, cy, r))
    placed.sort(key=lambda t: t[0])  # far -> near
    for depth, o, cx, cy, r in placed:
        if o.oid == div_oid:
            spr = div_sprite
            ang = 4.0 * math.sin(phase * 0.2 + o.oid)
        else:
            spr = cells[o.oid % len(cells)]
            ang = o.facing * 45 + 5.0 * math.sin(phase * 0.25 + o.oid)
        pulse = 1.0 + 0.03 * math.sin(phase * 0.3 + o.oid * 1.7)
        target = max(8, int(r * 3.0 * pulse))
        s = spr.resize((target, target), Image.LANCZOS)
        if abs(ang) > 0.1:
            s = s.rotate(ang, resample=Image.BICUBIC, expand=True)
        blur = (1.0 - depth) ** 1.5 * r * 0.30
        if blur > 0.4:
            s = s.filter(ImageFilter.GaussianBlur(blur))
        ox, oy = int(cx - s.width / 2), int(cy - s.height / 2)
        sh = s.split()[3].filter(ImageFilter.GaussianBlur(r * 0.25))
        shadow = Image.new("RGBA", s.size, (0, 0, 0, 0))
        shadow.putalpha(sh.point(lambda v: int(v * 0.40)))
        canvas.alpha_composite(shadow, (ox + int(r * 0.1), oy + int(r * 0.16)))
        canvas.alpha_composite(s, (ox, oy))
    out = np.asarray(canvas.convert("RGB"), np.float32)
    bright = np.clip(out - 205, 0, 255)
    out = out + 0.28 * _ls._blur(bright, 6)
    ln = _ls._aces(out / 255.0 * 0.95) ** 1.05
    ln[..., 0] *= 1.06
    ln[..., 2] *= 0.83
    out = np.clip(ln, 0, 1) * 255
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    vig = 1 - 0.42 * (((xx / width - 0.5) ** 2 + (yy / height - 0.5) ** 2) * 2.0)
    out *= np.clip(vig, 0.5, 1)[..., None]
    out += rng.normal(0, 2.6, (height, width, 1)).astype(np.float32)
    result = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
    return np.asarray(_ls._overlay(result), dtype=np.uint8)
