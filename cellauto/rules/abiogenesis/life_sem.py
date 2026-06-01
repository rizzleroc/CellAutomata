"""SEM "live feed" renderer for Stage XIII — 3D digital organisms.

This is the headline Phase 5.1 visual: a warm-sepia 400× scanning-electron-
microscope plate of the digital organisms. Unlike a flat sprite, every cell is
shaded as a real 3D body — a height field is built per organism (an organic,
per-cell amoeboid dome with internal organelle/gut relief and surface
micro-texture), surface normals are derived from it, and the body is lit with a
Blinn-Phong model: directional key + cool fill, a tight wet specular, a glassy
clearcoat lobe, ambient occlusion in the crevices, and the characteristic SEM
*edge-brightening* (a Fresnel rim that makes silhouettes glow). The substrate is
a lit granular terrain; the frame gets contact shadows, depth-of-field (far
cells soften), bloom, a filmic warm-sepia grade, vignette and grain. One
dividing cell is rendered as a teal figure-eight — the single saturated accent,
matching the reference plate.

The look was developed by fanning a 16-way parallel technique search and
harvesting the winning combination (composition, elongated body shape, organelle
relief, edge-brightening, subsurface translucency, ambient occlusion, filmic
grade, division accent). Placement is POSITION-BASED (each cell sits where it
lives on the grid) so the live feed animates continuously as the simulation
steps; a ``phase`` term wobbles membranes, beats cilia, and churns the gut so
the colony reads as alive.

Pure numpy + Pillow — no heavy 3D dependency. Every element maps to real
organism state (energy → size, genome → body harmonics + gut, instruction
pointer → the teal bead, division → the teal cell).
"""

from __future__ import annotations

import math
import random
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# Lighting rig (camera looks down +z). Warm key from upper-left, weak cool fill.
_LIGHT = np.array([-0.42, -0.58, 0.70], np.float32)
_LIGHT /= np.linalg.norm(_LIGHT)
_FILL = np.array([0.55, 0.35, 0.50], np.float32)
_FILL /= np.linalg.norm(_FILL)
_VIEW = np.array([0.0, 0.0, 1.0], np.float32)
_HALF = _LIGHT + _VIEW
_HALF /= np.linalg.norm(_HALF)


def _blur(a: np.ndarray, radius: float) -> np.ndarray:
    if radius <= 0:
        return a.astype(np.float32)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(radius)), np.float32)


def _normals(h: np.ndarray, strength: float = 2.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    gy, gx = np.gradient(h.astype(np.float32))
    nx, ny, nz = -gx * strength, -gy * strength, np.ones_like(h, np.float32)
    inv = 1.0 / np.sqrt(nx * nx + ny * ny + nz * nz)
    return nx * inv, ny * inv, nz * inv


def _fbm(width: int, height: int, rng: np.random.RandomState, octaves: int = 6) -> np.ndarray:
    acc = np.zeros((height, width), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        cell = max(2, int(110 / (2**o)))
        gh, gw = height // cell + 2, width // cell + 2
        g = (rng.random_sample((gh, gw)) * 255).astype(np.uint8)
        up = np.asarray(Image.fromarray(g).resize((width, height), Image.BICUBIC), np.float32) / 255
        acc += up * amp
        tot += amp
        amp *= 0.5
    return acc / tot


def _aces(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0, None)
    return np.clip((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0, 1)


def _substrate(width: int, height: int, rng: np.random.RandomState) -> np.ndarray:
    base = _fbm(width, height, rng)
    fine = _blur(rng.random_sample((height, width)) * 255, 0.7) / 255
    pebbles = np.zeros((height, width), np.float32)
    for _ in range(360):
        r = 2.5 + rng.random_sample() ** 2.4 * 8
        cx, cy = rng.randint(0, width), rng.randint(0, height)
        y0, y1 = max(0, int(cy - r)), min(height, int(cy + r))
        x0, x1 = max(0, int(cx - r)), min(width, int(cx + r))
        if y0 >= y1 or x0 >= x1:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = ((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)
        pebbles[y0:y1, x0:x1] = np.maximum(pebbles[y0:y1, x0:x1], np.sqrt(np.clip(1 - d, 0, 1)) * 0.5)
    hsub = 0.52 * base + 0.22 * fine + 0.42 * pebbles
    nx, ny, nz = _normals(hsub, strength=3.6)
    ndl = np.clip(nx * _LIGHT[0] + ny * _LIGHT[1] + nz * _LIGHT[2], 0, 1)
    ndh = np.clip(nx * _HALF[0] + ny * _HALF[1] + nz * _HALF[2], 0, 1)
    spec = ndh**22
    lo = _blur(hsub * 255, min(width, height) * 0.04) / 255
    ao = np.clip(1.0 + 2.6 * (hsub - lo), 0.45, 1.08)
    shade = (0.22 + 0.86 * ndl) * ao
    img = np.empty((height, width, 3), np.float32)
    img[..., 0] = 116 * shade + 52 * spec
    img[..., 1] = 90 * shade + 42 * spec
    img[..., 2] = 62 * shade + 28 * spec
    return img


def _body_fields(
    size: int, ox: float, oy: float, rx: float, ry: float, org: Any, phase: float, rng: np.random.RandomState
):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    orng = random.Random((org.oid * 2654435761) & 0xFFFFFFFF)
    harm = [
        (
            k,
            orng.uniform(0.05, 0.18) / (1 + (k - 2) * 0.35),
            orng.uniform(0, 6.28),
            orng.uniform(0.4, 1.1) * (1 if orng.random() < 0.5 else -1),
        )
        for k in (2, 3, 5, 7)
    ]
    taper = orng.uniform(0.22, 0.40) * (1 if orng.random() < 0.5 else -1)
    ang = (org.facing / 8.0) * 6.2832 + phase * 0.012
    ca, sa = math.cos(-ang), math.sin(-ang)
    dx, dy = xx - ox, yy - oy
    bx, by = dx * ca - dy * sa, dx * sa + dy * ca
    th = np.arctan2(by, bx)
    rad = np.sqrt((bx / rx) ** 2 + (by / ry) ** 2)
    rr = np.ones_like(th)
    if org.genome:
        rr += 0.10 * (org.genome[0] % 5) / 5 * np.sin(2 * th + phase * 0.05)
    rr += taper * np.cos(th) * (0.55 + 0.45 * np.sin(th) ** 2)
    for k, a, ph, spd in harm:
        rr += a * np.sin(k * th + ph + phase * 0.13 * spd)
    mask = np.clip((rr - rad) / 0.08, 0, 1)
    norm = np.clip(rad / np.maximum(rr, 1e-3), 0, 1)
    dome = np.sqrt(np.clip(1 - norm**2, 0, 1))
    h = dome * mask

    def bump(cxn: float, cyn: float, rn: float, amp: float) -> np.ndarray:
        dd = ((bx - cxn) / rn) ** 2 + ((by - cyn) / rn) ** 2
        return amp * np.exp(-dd) * mask

    nucleus = bump(-rx * 0.30, -ry * 0.26, rx * 0.30, 0.22)
    h = h + nucleus
    gut = np.zeros_like(h)
    grng = random.Random((org.oid * 40503) & 0xFFFFFFFF)
    for _ in range(16):
        b = bump(
            grng.uniform(-rx * 0.30, rx * 0.55),
            grng.uniform(-ry * 0.10, ry * 0.55),
            rx * grng.uniform(0.12, 0.24),
            grng.uniform(0.07, 0.15),
        )
        h = h + b
        gut = gut + b
    micro = _blur(rng.random_sample((size, size)) * 255, 0.6) / 255
    micro2 = _blur(rng.random_sample((size, size)) * 255, 1.8) / 255
    h = h + ((micro - 0.5) * 0.10 + (micro2 - 0.5) * 0.06) * mask
    return mask, h, nucleus, gut, norm


def _organism_tile(r: float, org: Any, phase: float, rng: np.random.RandomState):
    pad = int(r * 2.6) + 6
    size = pad * 2
    ox = oy = float(pad)
    rx, ry = r, r * 0.62
    mask, h, nucleus, gut, norm = _body_fields(size, ox, oy, rx, ry, org, phase, rng)
    if mask.max() <= 0:
        return None, 0, 0
    hp = _blur(np.clip(h, 0, 2) * 110, r * 0.05) / 110
    nx, ny, nz = _normals(hp, strength=2.2)
    ndl = np.clip(nx * _LIGHT[0] + ny * _LIGHT[1] + nz * _LIGHT[2], 0, 1)
    ndf = np.clip(nx * _FILL[0] + ny * _FILL[1] + nz * _FILL[2], 0, 1)
    ndh = np.clip(nx * _HALF[0] + ny * _HALF[1] + nz * _HALF[2], 0, 1)
    ndv = np.clip(nz, 0, 1)
    lo = _blur(np.clip(hp, 0, 2) * 110, r * 0.5) / 110
    ao = np.clip(1.0 + 2.4 * (hp - lo), 0.4, 1.08)
    spec = ndh**70
    clear = ndh**140
    fres = (1 - ndv) ** 1.4
    mgy, mgx = np.gradient(mask)
    edge = np.clip(np.sqrt(mgx * mgx + mgy * mgy) * 2.2, 0, 1)
    shim = 1.0 + 0.05 * math.sin(phase * 0.3 + org.oid)
    gutn = np.clip(gut * 2.4, 0, 1)
    alb = np.empty((size, size, 3), np.float32)
    alb[:] = np.array([132, 112, 78], np.float32) * shim
    alb *= (1 - 0.58 * gutn)[..., None]
    alb += np.clip(nucleus * 2, 0, 1)[..., None] * np.array([26, 22, 12])
    shade = (0.15 + 0.86 * ndl + 0.12 * ndf) * ao
    rgb = alb * shade[..., None]
    thin = np.clip(1 - norm, 0, 1) * mask
    sss = _blur(thin * 255, r * 0.10) / 255 * (1 - gutn)
    rgb += (sss * 120)[..., None] * np.array([1.0, 0.62, 0.30])
    rgb += (spec * 235)[..., None] * np.array([1.0, 0.97, 0.86])
    rgb += (clear * 255)[..., None] * np.array([1.0, 0.99, 0.95])
    rgb += (fres * 190)[..., None] * np.array([1.0, 0.92, 0.74])
    rgb += (edge * 150)[..., None] * np.array([1.0, 0.95, 0.82])
    if org.genome:
        n_show = min(16, len(org.genome))
        ip0 = org.ip % len(org.genome)
        yy, xx = np.mgrid[0:size, 0:size]
        for i in range(n_show):
            t = 0.12 + 0.76 * i / max(1, n_show - 1)
            ba = math.pi * t
            px = ox + math.cos(ba) * rx * 0.82
            py = oy + math.sin(ba) * ry * 0.82
            dot = max(2, int(r * 0.08))
            dd = (xx - px) ** 2 + (yy - py) ** 2
            bm = np.clip(1 - dd / (dot * dot), 0, 1)
            if i == 0:
                col = np.array([90, 240, 215], np.float32)
            else:
                bc = 245 if org.genome[(ip0 + i) % len(org.genome)] / 19 > 0.5 else 210
                col = np.array([bc, bc - 16, bc - 70], np.float32)
            rgb += (bm**0.6)[..., None] * col * 0.9
    rgb = np.clip(rgb, 0, 255)
    tile = np.dstack([rgb, mask * 255]).astype(np.uint8)
    return tile, pad, size


def _division_tile(r: float, org: Any, phase: float, rng: np.random.RandomState):
    pad = int(r * 3.2) + 8
    size = pad * 2
    ox = oy = float(pad)
    rx, ry = r * 0.8, r * 0.66
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    sep = rx * 0.92
    h = np.zeros((size, size), np.float32)
    mask = np.zeros((size, size), np.float32)
    for cxn in (-sep, sep):
        rad = np.sqrt(((xx - ox - cxn) / rx) ** 2 + ((yy - oy) / ry) ** 2)
        m = np.clip((1.0 - rad) / 0.08, 0, 1)
        dome = np.sqrt(np.clip(1 - np.clip(rad, 0, 1) ** 2, 0, 1))
        h = np.maximum(h, dome * m)
        mask = np.maximum(mask, m)
    neck = np.clip(1 - ((xx - ox) / (rx * 0.5)) ** 2 - ((yy - oy) / (ry * 0.35)) ** 2, 0, 1)
    h = np.maximum(h, neck * 0.7)
    mask = np.maximum(mask, np.clip(neck * 3, 0, 1))
    hp = _blur(h * 110, r * 0.05) / 110
    nx, ny, nz = _normals(hp, 2.2)
    ndl = np.clip(nx * _LIGHT[0] + ny * _LIGHT[1] + nz * _LIGHT[2], 0, 1)
    ndh = np.clip(nx * _HALF[0] + ny * _HALF[1] + nz * _HALF[2], 0, 1)
    fres = (1 - np.clip(nz, 0, 1)) ** 1.4
    ao = np.clip(nz, 0.45, 1.0)
    rgb = np.zeros((size, size, 3), np.float32)
    rgb += np.array([42, 120, 116], np.float32) * (0.22 + 0.95 * ndl)[..., None] * ao[..., None]
    rgb += (fres * 150)[..., None] * np.array([0.45, 1.0, 0.95])
    rgb += ((ndh**80) * 200)[..., None] * np.array([0.85, 1.0, 1.0])
    bridge = np.clip(1 - ((xx - ox) / (rx * 0.16)) ** 2 - ((yy - oy) / (ry * 0.45)) ** 2, 0, 1)
    rgb += _blur(bridge * 255, r * 0.10)[..., None] / 255 * np.array([90, 235, 215]) * 1.1
    rgb = np.clip(rgb, 0, 255)
    halo = _blur(mask * 255, r * 0.30) / 255
    alpha = np.clip(mask + halo * 0.35, 0, 1)
    rgb += (np.clip(halo - mask, 0, 1) * 40)[..., None] * np.array([0.3, 1.0, 0.9])
    tile = np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)
    return tile, pad, size


def _overlay(img: Image.Image, scale_um: int = 50) -> Image.Image:
    width, height = img.size
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([6, 6, width - 7, height - 7], outline=(150, 132, 96, 150), width=2)
    cx, cy = width // 2, height // 2
    d.line([cx - 26, cy, cx + 26, cy], fill=(210, 195, 160, 120), width=1)
    d.line([cx, cy - 26, cx, cy + 26], fill=(210, 195, 160, 120), width=1)
    bw, bh = 250, 26
    d.rectangle(
        [width - bw - 16, 16, width - 16, 16 + bh], fill=(20, 15, 10, 150), outline=(150, 132, 96, 170)
    )
    d.text((width - bw - 6, 22), "LIVE SEM FEED  ·  STAGE XIII  ·  400×", fill=(225, 210, 170, 255))
    sb = 150
    sx, sy = cx - sb // 2, height - 34
    for seg in ([sx, sy, sx + sb, sy], [sx, sy - 5, sx, sy + 5], [sx + sb, sy - 5, sx + sb, sy + 5]):
        d.line(seg, fill=(228, 212, 172, 230), width=2)
    d.text((cx - 22, sy - 20), f"{scale_um} um", fill=(225, 210, 170, 255))
    return img


def photographic_finish(rgb: np.ndarray, seed: int = 0) -> np.ndarray:
    """Apply a real-DIC-micrograph photographic finish to an RGB uint8 plate
    (harvested from a 16-way look-dev search). In order: DIC directional shear
    relief, micrograph colour science (desat + filmic curve + sepia split-tone),
    diffraction-limited softening, veiling-glare bloom, lateral chromatic
    aberration, cos^4 lens vignette, and fine photon-statistics grain. Returns
    RGB uint8 the same size. This is what turns a clean render into something
    that reads as a captured photograph rather than CG."""
    rng = np.random.default_rng(seed & 0x7FFFFFFF)
    work = rgb.astype(np.float32) / 255.0
    h, w = work.shape[:2]

    def lum(a: np.ndarray) -> np.ndarray:
        return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114

    # 1. DIC directional shear relief (45deg luminance derivative, soft-light ~40%)
    ls = _blur(lum(work) * 255, 0.9) / 255
    gx = np.zeros_like(ls)
    gy = np.zeros_like(ls)
    gx[:, 1:-1] = (ls[:, 2:] - ls[:, :-2]) * 0.5
    gy[1:-1, :] = (ls[2:, :] - ls[:-2, :]) * 0.5
    relief = np.clip((gx + gy) * 0.7071 * 6.0, -1.0, 1.0)
    rl = (0.5 + 0.5 * relief)[..., None]
    sl = np.where(
        rl <= 0.5,
        work - (1 - 2 * rl) * work * (1 - work),
        work + (2 * rl - 1) * (np.sqrt(np.clip(work, 0, 1)) - work),
    )
    work = np.clip(work * 0.6 + sl * 0.4, 0, 1)

    # 2. Micrograph colour science: desaturate, filmic low-contrast, sepia split-tone
    work = work * 0.86 + lum(work)[..., None] * 0.14
    x = np.clip(work, 0, 1)
    work = 0.03 + (x * 0.55 + (x * x * (3 - 2 * x)) * 0.45) * 0.93
    lt = lum(work)
    hi = np.clip((lt - 0.45) / 0.55, 0, 1)[..., None]
    sh = np.clip(1 - lt * 1.5, 0, 1)[..., None]
    warm = np.array([1.0, 0.965, 0.87], np.float32)
    cool = np.array([0.965, 0.985, 1.01], np.float32)
    work = work * (1 - 0.10 * hi) + (work * warm) * (0.10 * hi)
    work = np.clip(work * (1 - 0.05 * sh) + (work * cool) * (0.05 * sh), 0, 1)

    # 3. Crisp capture: a hair of optical micro-softening, then an unsharp mask
    #    so detail stays sharp (a real well-focused micrograph is crisp).
    soft = _blur(work * 255, 1.1) / 255
    work = np.clip(work + 0.55 * (work - soft), 0.0, 1.0)

    # 4. Veiling-glare bloom on highlights
    himask = np.clip((lum(work) - 0.62) / 0.38, 0, 1)[..., None] * work
    bloom = _blur(himask * 255, 9) / 255 + 0.5 * (_blur(himask * 255, 22) / 255)
    work = np.clip((np.clip(work + 0.18 * bloom, 0, 1)) * 0.985 + 0.015, 0, 1)

    # 5. Lateral chromatic aberration (R out, B in, growing with radius)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    r2 = ((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2

    def remap(ch: np.ndarray, scale: float) -> np.ndarray:
        sx = np.clip(cx + (xx - cx) * (1 + scale * r2), 0, w - 1)
        sy = np.clip(cy + (yy - cy) * (1 + scale * r2), 0, h - 1)
        x0 = np.floor(sx).astype(int)
        y0 = np.floor(sy).astype(int)
        x1 = np.clip(x0 + 1, 0, w - 1)
        y1 = np.clip(y0 + 1, 0, h - 1)
        fx, fy = sx - x0, sy - y0
        return (ch[y0, x0] * (1 - fx) + ch[y0, x1] * fx) * (1 - fy) + (
            ch[y1, x0] * (1 - fx) + ch[y1, x1] * fx
        ) * fy

    work = np.clip(
        np.stack([remap(work[..., 0], 0.0016), work[..., 1], remap(work[..., 2], -0.0016)], -1), 0, 1
    )

    # 6. cos^4 lens vignette
    maxr = math.hypot(cx, cy)
    theta = (np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / maxr) * 0.62
    vig = np.cos(theta) ** 4
    vig = 0.80 + 0.20 * (vig - vig.min()) / (1 - vig.min() + 1e-9)
    work = np.clip(work * vig[..., None], 0, 1)

    # 7. Fine photon-statistics film grain (last)
    sig = np.clip(work, 1e-4, 1.0)
    grain = rng.normal(0, 1, work.shape) * np.sqrt(sig / 950.0) + rng.normal(0, 1, work.shape) * 0.0035
    grain = 0.7 * grain + 0.3 * grain.mean(-1, keepdims=True)
    return (np.clip(work + grain, 0, 1) * 255 + 0.5).astype(np.uint8)


def render(
    state: Any,
    rule: Any,
    width: int = 600,
    height: int = 600,
    max_org: int = 24,
    seed: int = 0,
    phase: float = 0.0,
) -> np.ndarray:
    """Render the Stage XIII population as a 3D SEM plate. Returns an
    ``(height, width, 3)`` uint8 array."""
    rng = np.random.RandomState(seed & 0x7FFFFFFF)
    img = _substrate(width, height, rng)
    canvas = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    base_r = min(width, height) * 0.095
    gh, gw = state.substrate.shape
    orgs = sorted(state.organisms.values(), key=lambda o: -o.energy)[:max_org]
    div_oid = max(orgs, key=lambda o: (o.n_divisions, o.energy)).oid if orgs else None
    margin = 0.09
    placed = []
    for o in orgs:
        depth = o.y / max(1, gh - 1)
        cx = (margin + (1 - 2 * margin) * (o.x / max(1, gw - 1))) * width
        cy = (margin + (1 - 2 * margin) * depth) * height
        ef = min(o.energy / max(rule.e_div, 1e-6), 1.6)
        r = base_r * (0.62 + 0.55 * depth) * (0.82 + 0.4 * ef)
        placed.append((depth, o, cx, cy, r))
    placed.sort(key=lambda t: t[0])  # far -> near
    hero = None
    for depth, o, cx, cy, r in placed:
        if o.oid == div_oid:
            hero = (o, cx, cy, r)  # composite AFTER the sepia grade so it stays teal
            continue
        tile, pad, size = _organism_tile(r, o, phase, rng)
        if tile is None:
            continue
        timg = Image.fromarray(tile, "RGBA")
        sh = Image.fromarray(tile[..., 3]).filter(ImageFilter.GaussianBlur(r * 0.28))
        shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        shadow.putalpha(sh.point(lambda v: int(v * 0.5)))
        canvas.alpha_composite(shadow, (int(cx - pad + r * 0.12), int(cy - pad + r * 0.16)))
        blur = (1.0 - depth) ** 1.4 * r * 0.34
        if blur > 0.4:
            timg = timg.filter(ImageFilter.GaussianBlur(blur))
        canvas.alpha_composite(timg, (int(cx - pad), int(cy - pad)))
    out = np.asarray(canvas.convert("RGB"), np.float32)
    bright = np.clip(out - 205, 0, 255)
    out = out + 0.30 * _blur(bright, 6)
    ln = _aces(out / 255.0 * 0.92) ** 1.06
    ln[..., 0] *= 1.07
    ln[..., 1] *= 0.99
    ln[..., 2] *= 0.80
    out = np.clip(ln, 0, 1) * 255
    if hero is not None:
        o, cx, cy, r = hero
        tile, pad, size = _division_tile(r, o, phase, rng)
        graded = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
        sh = Image.fromarray(tile[..., 3]).filter(ImageFilter.GaussianBlur(r * 0.3))
        shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        shadow.putalpha(sh.point(lambda v: int(v * 0.55)))
        graded.alpha_composite(shadow, (int(cx - pad + r * 0.12), int(cy - pad + r * 0.16)))
        graded.alpha_composite(Image.fromarray(tile, "RGBA"), (int(cx - pad), int(cy - pad)))
        out = np.asarray(graded.convert("RGB"), np.float32)
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    vig = 1 - 0.46 * (((xx / width - 0.5) ** 2 + (yy / height - 0.5) ** 2) * 2.0)
    out *= np.clip(vig, 0.45, 1)[..., None]
    out += rng.normal(0, 3.0, (height, width, 1)).astype(np.float32)
    result = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
    result = _overlay(result)
    return np.asarray(result, dtype=np.uint8)
