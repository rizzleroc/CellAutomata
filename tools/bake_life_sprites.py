"""Offline bake of photoreal Stage XIII cell sprites with Mitsuba 3.

Path-traces translucent single-celled organisms (rough-dielectric shell over a
dense, high-albedo scattering medium → genuine subsurface scattering, with a
diffuse nucleus + organelles) under a warm three-point directional rig plus a
dim ambient environment. A separate emissive mask pass gives a clean alpha
cutout. The result is a committed sprite atlas (``cellauto/assets/life/``) that
the live app composites with plain Pillow — so the *runtime* has NO Mitsuba /
GPU dependency; only this bake does.

This is the "2.5D billboard" pipeline: expensive offline render quality,
cheap live compositing (see ``cellauto/rules/abiogenesis/life_sprites.py``).

Run:  python tools/bake_life_sprites.py [--cells 12] [--size 384] [--spp 224]
Requires:  pip install mitsuba   (bake-time only)
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ASSETS = Path(__file__).resolve().parent.parent / "cellauto" / "assets" / "life"


def _gblur(a: np.ndarray, radius: float) -> np.ndarray:
    if radius <= 0:
        return a.astype(np.float32)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(radius)), np.float32)


def _lights(mi, T):
    return {
        "key": {"type": "directional", "direction": [3.2, -4.0, -2.5],
                "irradiance": {"type": "rgb", "value": [7.5, 6.4, 4.6]}},
        "fill": {"type": "directional", "direction": [-3.5, 2.0, -2.0],
                 "irradiance": {"type": "rgb", "value": [1.6, 1.9, 2.5]}},
        "rim": {"type": "directional", "direction": [0.0, -1.5, 3.5],
                "irradiance": {"type": "rgb", "value": [2.6, 2.6, 2.8]}},
    }


def bake_cell(mi, variant: int, size: int, spp: int, teal: bool = False) -> Image.Image:
    T = mi.ScalarTransform4f
    rng = random.Random(variant * 99 + (777 if teal else 1))
    ax, ay, az = rng.uniform(0.92, 1.06), rng.uniform(1.18, 1.42), rng.uniform(0.82, 0.96)
    dens = rng.uniform(10.0, 15.0)
    if teal:
        tint = [0.35, 0.80, 0.78]
    else:
        tint = [rng.uniform(0.93, 0.97), rng.uniform(0.82, 0.88), rng.uniform(0.62, 0.70)]
    organelles = {}
    for k in range(rng.randint(2, 4)):
        organelles[f"org{k}"] = {
            "type": "sphere", "radius": rng.uniform(0.12, 0.26),
            "to_world": T.translate([rng.uniform(-0.4, 0.4), rng.uniform(-0.5, 0.5), rng.uniform(-0.1, 0.3)]),
            "bsdf": {"type": "diffuse", "reflectance": {"type": "rgb", "value": [0.42, 0.33, 0.22]}},
        }
    sensor = {"type": "perspective", "fov": 26,
              "to_world": T.look_at(origin=[0, 0, 7], target=[0, 0, 0], up=[0, 1, 0]),
              "film": {"type": "hdrfilm", "width": size, "height": size, "rfilter": {"type": "gaussian"}},
              "sampler": {"type": "independent", "sample_count": spp}}
    beauty = mi.load_dict({
        "type": "scene",
        "integrator": {"type": "path", "max_depth": 14},
        "sensor": sensor,
        "env": {"type": "constant", "radiance": {"type": "rgb", "value": [0.55, 0.48, 0.36]}},
        "cell": {"type": "sphere", "radius": 1.0, "to_world": T.scale([ax, ay, az]),
                 "bsdf": {"type": "roughdielectric", "int_ior": 1.35, "ext_ior": 1.0, "alpha": 0.07},
                 "interior": {"type": "homogeneous", "albedo": {"type": "rgb", "value": tint}, "sigma_t": dens}},
        "nucleus": {"type": "sphere", "radius": rng.uniform(0.30, 0.40),
                    "to_world": T.translate([rng.uniform(-0.3, -0.1), rng.uniform(0.1, 0.3), 0.12]),
                    "bsdf": {"type": "diffuse", "reflectance": {"type": "rgb", "value": [0.5, 0.4, 0.27]}}},
        **organelles, **_lights(mi, T),
    })
    col = np.array(mi.render(beauty, spp=spp))[..., :3]
    mask_scene = mi.load_dict({
        "type": "scene",
        "integrator": {"type": "path", "max_depth": 2},
        "sensor": {**sensor, "sampler": {"type": "independent", "sample_count": 32}},
        "cell": {"type": "sphere", "radius": 1.0, "to_world": T.scale([ax, ay, az]),
                 "emitter": {"type": "area", "radiance": {"type": "rgb", "value": [1, 1, 1]}}},
    })
    m = np.array(mi.render(mask_scene, spp=32))[..., :3].mean(axis=2)
    alpha = np.clip(m * 1.4, 0, 1)
    rgb = _gblur((np.clip(col, 0, 1) ** (1 / 2.2)) * 255.0, 0.6)
    out = np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", type=int, default=12)
    ap.add_argument("--size", type=int, default=384)
    ap.add_argument("--spp", type=int, default=224)
    ap.add_argument("--tile", type=int, default=256)
    args = ap.parse_args()

    import mitsuba as mi

    mi.set_variant("scalar_rgb")
    ASSETS.mkdir(parents=True, exist_ok=True)

    cols = 4
    rows = (args.cells + cols - 1) // cols
    tile = args.tile
    sheet = Image.new("RGBA", (cols * tile, rows * tile), (0, 0, 0, 0))
    for v in range(args.cells):
        spr = bake_cell(mi, v, args.size, args.spp).resize((tile, tile), Image.LANCZOS)
        sheet.alpha_composite(spr, ((v % cols) * tile, (v // cols) * tile))
        print(f"baked cell {v + 1}/{args.cells}")
    sheet.save(ASSETS / "cells.png")
    div = bake_cell(mi, 0, args.size, args.spp, teal=True).resize((tile, tile), Image.LANCZOS)
    div.save(ASSETS / "cell_div.png")
    # tiny manifest so the loader knows the grid
    (ASSETS / "atlas.json").write_text(
        f'{{"cols": {cols}, "rows": {rows}, "tile": {tile}, "count": {args.cells}}}\n'
    )
    print(f"wrote {ASSETS / 'cells.png'} ({cols}x{rows} @ {tile}px) + cell_div.png")


if __name__ == "__main__":
    main()
