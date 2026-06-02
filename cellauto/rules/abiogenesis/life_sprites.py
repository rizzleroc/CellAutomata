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
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from cellauto.rules.abiogenesis import life_sem as _ls

_ASSETS = Path(__file__).resolve().parents[2] / "assets" / "life"


@lru_cache(maxsize=1)
def load_atlas() -> tuple[list[list[Image.Image]], list[Image.Image]]:
    """Load and slice the committed FLIPBOOK atlas (cached). Returns
    ``cells[variant][frame]`` and the teal division flipbook ``div[frame]``.
    Raises ``FileNotFoundError`` if the bake hasn't been run."""
    sheet_path = _ASSETS / "cells.png"
    meta_path = _ASSETS / "atlas.json"
    div_path = _ASSETS / "cell_div.png"
    if not (sheet_path.exists() and meta_path.exists() and div_path.exists()):
        raise FileNotFoundError(f"Stage XIII sprite atlas not found in {_ASSETS}")
    meta = json.loads(meta_path.read_text())
    if not all(k in meta for k in ("variants", "frames", "tile")):
        raise FileNotFoundError(f"Stage XIII atlas manifest {meta_path} is stale/incompatible")
    variants, frames, tile = meta["variants"], meta["frames"], meta["tile"]
    sheet = Image.open(sheet_path).convert("RGBA")
    cells = []
    for v in range(variants):
        row = []
        for f in range(frames):
            x, y = f * tile, v * tile
            row.append(sheet.crop((x, y, x + tile, y + tile)))
        cells.append(row)
    div_sheet = Image.open(div_path).convert("RGBA")
    div = [div_sheet.crop((f * tile, 0, f * tile + tile, tile)) for f in range(frames)]
    return cells, div


def _bubbly_substrate(width: int, height: int, rng: np.random.RandomState) -> Image.Image:
    """Lit granular floor + scattered vesicle bubbles (bright-rimmed circles) —
    the bubbly DIC substrate from the reference plate."""
    img = _ls._substrate(width, height, rng)
    base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")
    dr = ImageDraw.Draw(base, "RGBA")
    for _ in range(int(width * height / 950)):
        r = 2 + rng.random_sample() ** 2 * 9
        x, y = rng.randint(0, width), rng.randint(0, height)
        dr.ellipse([x - r, y - r, x + r, y + r], outline=(225, 208, 170, 70), width=1)
        dr.ellipse([x - r * 0.5, y - r * 0.5, x + r * 0.5, y + r * 0.5], fill=(150, 130, 96, 40))
    return base.convert("RGBA")


def _contour(alpha: np.ndarray, n: int = 56) -> list[tuple[int, int, float, float]]:
    """Radial-sample a sprite's silhouette from its centre → membrane points."""
    h, w = alpha.shape
    cx, cy = w / 2, h / 2
    maxr = math.hypot(w, h)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        rr = maxr
        while rr > 2:
            x, y = int(cx + ca * rr), int(cy + sa * rr)
            if 0 <= x < w and 0 <= y < h and alpha[y, x] > 110:
                pts.append((x, y, ca, sa))
                break
            rr -= 2
    return pts


def _rim_cilia(
    canvas: Image.Image, sprite: Image.Image, ox: int, oy: int, r: float, beat: float = 0.0
) -> None:
    """Beaded membrane rim + an UNDULATING cilia fringe along the silhouette.

    Each cilium is a short curved stroke whose length and tangential curl
    oscillate; a phase offset around the perimeter makes the fringe ripple as a
    metachronal travelling wave (the way real ciliate beat), driven by ``beat``."""
    alpha = np.asarray(sprite.split()[3], np.uint8)
    pts = _contour(alpha, 64)
    n = max(1, len(pts))
    d = ImageDraw.Draw(canvas, "RGBA")
    dot = max(1, int(r * 0.07))
    wcil = max(1, dot // 2)
    for i, (x, y, ca, sa) in enumerate(pts):
        gx, gy = ox + x, oy + y
        # metachronal wave: ~3 wavelengths around the rim, advancing with beat
        ph = beat - (i / n) * 2 * math.pi * 3.0
        wave = math.sin(ph)
        hl = r * (0.15 + 0.11 * wave)  # length undulates
        tx, ty = -sa, ca  # membrane tangent
        curl = r * 0.07 * math.cos(ph)  # S-curve flagellar curl
        mx = gx + ca * hl * 0.55 + tx * curl
        my = gy + sa * hl * 0.55 + ty * curl
        tipx = gx + ca * hl + tx * curl * 0.5
        tipy = gy + sa * hl + ty * curl * 0.5
        d.line([gx, gy, mx, my, tipx, tipy], fill=(214, 196, 154, 125), width=wcil, joint="curve")
        bx, by = gx - ca * dot * 1.2, gy - sa * dot * 1.2
        d.ellipse([bx - dot, by - dot, bx + dot, by + dot], fill=(238, 222, 182, 225))


def _paste_cell(canvas, spr, cx, cy, r, depth, ang, furniture, jitter_key=None, beat=0.0):
    target = max(8, int(r * 3.0))
    if jitter_key is not None:
        # stable per-cell jitter (seeded by identity, NOT per frame) so cells
        # vary in shape/tone — breaking the clone-like uniformity — without
        # flickering across animation frames.
        jr = random.Random(jitter_key)
        aspect = 0.80 + 0.36 * jr.random()
        s = spr.resize((target, max(8, int(target * aspect))), Image.LANCZOS)
        rr, gg, bb, aa = s.split()
        body = Image.merge("RGB", (rr, gg, bb))
        body = ImageEnhance.Brightness(body).enhance(0.84 + 0.32 * jr.random())
        body = ImageEnhance.Contrast(body).enhance(0.88 + 0.34 * jr.random())
        s = Image.merge("RGBA", (*body.split(), aa))
    else:
        s = spr.resize((target, target), Image.LANCZOS)
    if abs(ang) > 0.1:
        s = s.rotate(ang, resample=Image.BICUBIC, expand=True)
    blur = max(0.0, 1.0 - depth) ** 1.8 * r * 0.16
    if blur > 0.5:
        s = s.filter(ImageFilter.GaussianBlur(blur))
    ox, oy = int(cx - s.width / 2), int(cy - s.height / 2)
    sh = s.split()[3].filter(ImageFilter.GaussianBlur(r * 0.25))
    shadow = Image.new("RGBA", s.size, (0, 0, 0, 0))
    shadow.putalpha(sh.point(lambda v: int(v * 0.40)))
    canvas.alpha_composite(shadow, (ox + int(r * 0.1), oy + int(r * 0.16)))
    canvas.alpha_composite(s, (ox, oy))
    if furniture and blur < 1.6:
        _rim_cilia(canvas, s, ox, oy, r, beat)


def _grade(canvas: Image.Image, rng: np.random.RandomState) -> np.ndarray:
    width, height = canvas.size
    out = np.asarray(canvas.convert("RGB"), np.float32)
    bright = np.clip(out - 205, 0, 255)
    out = out + 0.26 * _ls._blur(bright, 6)
    ln = _ls._aces(out / 255.0 * 0.92) ** 1.02
    ln[..., 0] *= 1.05
    ln[..., 2] *= 0.84
    out = np.clip(ln, 0, 1) * 255
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    vig = 1 - 0.32 * (((xx / width - 0.5) ** 2 + (yy / height - 0.5) ** 2) * 2.0)
    out *= np.clip(vig, 0.6, 1)[..., None]
    out += rng.normal(0, 2.3, (height, width, 1)).astype(np.float32)
    return np.clip(out, 0, 255).astype(np.uint8)


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
    cells, div = load_atlas()
    n_frames = len(div)
    rng = np.random.RandomState(seed & 0x7FFFFFFF)
    canvas = _bubbly_substrate(width, height, rng)
    gh, gw = state.substrate.shape
    base_r = min(width, height) * 0.05  # smaller cells → more of them, with breathing room
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
        # flipbook frame: advance with phase, offset per cell so the colony's
        # interiors churn out of sync (mobile insides).
        frame = int(phase * 0.5 + o.oid * 3) % n_frames
        if o.oid == div_oid:
            spr = div[frame]
            ang = 4.0 * math.sin(phase * 0.2 + o.oid)
        else:
            spr = cells[o.oid % len(cells)][frame]
            ang = o.facing * 45 + 5.0 * math.sin(phase * 0.25 + o.oid)
        _paste_cell(
            canvas, spr, cx, cy, r, depth, ang, furniture=True, jitter_key=o.oid, beat=phase * 0.7 + o.oid
        )
    finished = _ls.photographic_finish(_grade(canvas, rng), seed=seed)
    return np.asarray(_ls._overlay(Image.fromarray(finished, "RGB")), dtype=np.uint8)


def render_hero(width: int = 1100, height: int = 720, seed: int = 7) -> np.ndarray:  # pragma: no cover
    """A LOCKED, reference-matched hero plate: the baked photoreal cells laid
    out in loose rows (foreground larger) on the bubbly substrate, with beaded
    rims + cilia + one teal divider + the even sepia DIC grade. Deterministic
    for a given seed — used to mint ``docs/generated/stage13_life.png``. This is
    a fixed composition (not the live sim), so it can be tuned to mirror the
    reference plate directly."""
    cells, div = load_atlas()
    n_frames = len(div)
    rng = np.random.RandomState(seed & 0x7FFFFFFF)
    canvas = _bubbly_substrate(width, height, rng)
    rows = 7
    placed = []
    idx = 0
    for rrow in range(rows):
        depth = rrow / (rows - 1)
        n_in_row = 10 + 2 * rrow
        rsize = 0.55 + 0.75 * depth
        for c in range(n_in_row):
            depthj = min(1.0, max(0.0, depth + (rng.random_sample() - 0.5) * 0.09))
            cx = (0.03 + 0.94 * (c + 0.5 + (rng.random_sample() - 0.5) * 0.6) / n_in_row) * width
            cy = (0.10 + 0.82 * depth + (rng.random_sample() - 0.5) * 0.05) * height
            r = min(width, height) * 0.046 * rsize * (0.82 + 0.34 * rng.random_sample())
            placed.append((depthj, idx, cx, cy, r))
            idx += 1
    placed.sort(key=lambda t: t[0])
    div_slot = len(placed) * 6 // 10
    for k, (depth, i, cx, cy, r) in enumerate(placed):
        frame = (i * 3 + k) % n_frames
        if k == div_slot:
            spr, rr = div[frame], r * 1.25
        else:
            spr, rr = cells[i % len(cells)][frame], r
        _paste_cell(canvas, spr, cx, cy, rr, depth, (i * 53) % 360, furniture=True, jitter_key=1000 + i)
    finished = _ls.photographic_finish(_grade(canvas, rng), seed=seed)
    return np.asarray(_ls._overlay(Image.fromarray(finished, "RGB")), dtype=np.uint8)
