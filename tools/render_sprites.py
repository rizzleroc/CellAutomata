"""Procedurally render the v4.0 sprite library to cellauto/assets/sprites/.

Deterministic — re-running overwrites the same byte-for-byte sprites. Each
sprite is an alpha PNG at 96–128 px (composited on the depth-shaded SEM
background; per-stage rules supply position lists via render_sprites()).

Usage:
    python tools/render_sprites.py
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

REPO_ROOT = Path(__file__).resolve().parent.parent
SPRITES_ROOT = REPO_ROOT / "cellauto" / "assets" / "sprites"


def _radial_sphere(size: int, light_dir: tuple[float, float] = (-0.35, -0.45)) -> Image.Image:
    """Bone-cream sphere with directional shading (radial gradient + highlight).

    Output: RGBA, sphere centred, transparent outside the disc.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    cx = cy = (size - 1) / 2.0
    r = (size - 4) / 2.0
    lx, ly = light_dir
    llen = math.sqrt(lx * lx + ly * ly + 1.0)
    lx, ly, lz = lx / llen, ly / llen, 1.0 / llen
    for y in range(size):
        for x in range(size):
            dx = (x - cx) / r
            dy = (y - cy) / r
            d2 = dx * dx + dy * dy
            if d2 > 1.0:
                continue
            nz = math.sqrt(max(0.0, 1.0 - d2))
            # Hemispheric normal points outward; dot with light gives shading.
            lamb = max(0.0, dx * lx + dy * ly + nz * lz)
            spec = lamb**24 * 0.55
            v = 0.22 + 0.72 * lamb + spec
            v = max(0.0, min(1.0, v))
            shade = int(255 * v)
            # Soft edge (anti-alias the disc boundary).
            edge = max(0.0, 1.0 - (math.sqrt(d2) - 0.92) / 0.08) if d2 > 0.846 else 1.0
            alpha = int(255 * max(0.0, min(1.0, edge)))
            px[x, y] = (shade, shade, shade, alpha)
    return img


def _granule(size: int = 48) -> Image.Image:
    """Small unlit speckle — depth-shading is provided by the background."""
    img = _radial_sphere(size, light_dir=(-0.3, -0.4))
    # Drop the brightness so it reads as a darker speck, not a hero spot.
    px = img.load()
    for y in range(size):
        for x in range(size):
            r, g, b, a = px[x, y]
            v = int(r * 0.6)
            px[x, y] = (v, v, v, a)
    return img


def _protocell(size: int = 96) -> Image.Image:
    """Larger spherical protocell with a brighter highlight + faint inner ring."""
    img = _radial_sphere(size, light_dir=(-0.4, -0.5))
    # Subtle inner concentric ring to suggest a membrane.
    draw = ImageDraw.Draw(img)
    rr = (size - 4) // 2
    inner = int(rr * 0.78)
    cx = cy = size // 2
    for k in range(2):
        a = 70 - k * 30
        draw.ellipse(
            (cx - inner - k, cy - inner - k, cx + inner + k, cy + inner + k),
            outline=(255, 255, 255, a),
            width=1,
        )
    return img


def _spot(size: int = 80) -> Image.Image:
    """Gray-Scott self-replicating spot — bone-white sphere with sharp highlight."""
    img = _radial_sphere(size, light_dir=(-0.5, -0.6))
    # Brighten the centre highlight further so it pops on the SEM substrate.
    px = img.load()
    cx = cy = (size - 1) / 2.0
    r = (size - 4) / 2.0
    for y in range(size):
        for x in range(size):
            dx = (x - cx) / r + 0.32
            dy = (y - cy) / r + 0.38
            d2 = dx * dx + dy * dy
            if d2 < 0.18:
                rr, gg, bb, aa = px[x, y]
                boost = int(255 * (0.18 - d2) / 0.18 * 0.5)
                px[x, y] = (
                    min(255, rr + boost),
                    min(255, gg + boost),
                    min(255, bb + boost),
                    aa,
                )
    return img


def _vesicle(size: int = 112) -> Image.Image:
    """Translucent membrane sphere with a phospholipid bilayer ring.

    Interior is mostly transparent so the SEM background shows through, with
    a bright bilayer ring at the edge (Helfrich-style membrane).
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size // 2
    rr = (size - 4) // 2
    # Outer disc with low alpha — gives a hazy interior reading.
    draw.ellipse(
        (cx - rr, cy - rr, cx + rr, cy + rr),
        fill=(220, 215, 200, 38),
    )
    # Bilayer rings — two close concentric outlines, brighter than the interior.
    for k, (a, w) in enumerate(((220, 2), (150, 1))):
        off = k * 3
        draw.ellipse(
            (cx - rr + off, cy - rr + off, cx + rr - off, cy + rr - off),
            outline=(245, 240, 225, a),
            width=w,
        )
    # Specular highlight on the upper-left, blurred for a soft sheen.
    sheen = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(sheen)
    h_r = int(rr * 0.32)
    h_cx = cx - int(rr * 0.35)
    h_cy = cy - int(rr * 0.40)
    sdraw.ellipse(
        (h_cx - h_r, h_cy - h_r, h_cx + h_r, h_cy + h_r),
        fill=(255, 250, 235, 160),
    )
    sheen = sheen.filter(ImageFilter.GaussianBlur(radius=2.5))
    img = Image.alpha_composite(img, sheen)
    return img


def main() -> None:
    plan = {
        "stage0/granule.png": _granule(),
        "stage0/protocell.png": _protocell(),
        "stage1/spot.png": _spot(),
        "stage3/vesicle.png": _vesicle(),
    }
    for rel, img in plan.items():
        out = SPRITES_ROOT / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(out, format="PNG", optimize=True)
        print(f"wrote {out.relative_to(REPO_ROOT)}  ({img.size}, mode {img.mode})")


if __name__ == "__main__":
    main()
