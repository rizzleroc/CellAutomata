"""Offline bake of photoreal Stage XIII cell sprites with Mitsuba 3.

Path-traces translucent single-celled organisms as a FLIPBOOK so the live app
gets organic shapes AND mobile interiors at zero runtime render cost:

  * **Organic bodies** — each cell is a procedurally *displaced* mesh (a UV
    sphere whose radius is modulated by random spherical harmonics), so the
    silhouette is genuinely irregular/amoeboid, never a plain ellipsoid.
  * **Subsurface scattering** — a rough-dielectric shell over a dense,
    high-albedo scattering medium gives real translucency; a diffuse nucleus
    and organelles read as internal masses through the body.
  * **Mobile insides** — for each cell variant we bake F animation frames in
    which the nucleus + organelles ORBIT/drift; the live compositor cycles the
    frames so the interior visibly churns (the body silhouette is fixed per
    variant, so only the insides move — no flicker).

A separate emissive mask pass per frame gives a clean alpha cutout. The result
is a committed sprite sheet (``cellauto/assets/life/cells.png`` = variants ×
frames) + a teal division flipbook, composited live with plain Pillow. So the
RUNTIME has NO Mitsuba / GPU dependency; only this bake does.

Run:  python tools/bake_life_sprites.py [--variants 6 --frames 8 --size 300 --spp 192]
Requires:  pip install mitsuba   (bake-time only)
"""

from __future__ import annotations

import argparse
import math
import random
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ASSETS = Path(__file__).resolve().parent.parent / "cellauto" / "assets" / "life"


def _gblur(a: np.ndarray, radius: float) -> np.ndarray:
    if radius <= 0:
        return a.astype(np.float32)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(radius)), np.float32)


def organic_mesh(path: str, seed: int, stacks: int = 44, slices: int = 66) -> str:
    """Write a displaced-sphere PLY: an organic, irregular amoeboid body."""
    rng = random.Random(seed)
    harm = [
        (
            rng.randint(2, 5),
            rng.randint(0, 6),
            rng.uniform(0.05, 0.17),
            rng.uniform(0, 6.28),
            rng.uniform(0, 6.28),
        )
        for _ in range(6)
    ]
    th = np.linspace(1e-3, math.pi - 1e-3, stacks + 1)[:, None]
    ph = np.linspace(0, 2 * math.pi, slices, endpoint=False)[None, :]
    disp = np.ones((stacks + 1, slices), np.float64)
    for m, n, a, p1, p2 in harm:
        disp += a * np.sin(m * th + p1) * np.cos(n * ph + p2)
    ay = rng.uniform(1.2, 1.42)
    az = rng.uniform(0.82, 0.95)
    X = disp * np.sin(th) * np.cos(ph)
    Y = disp * np.cos(th) * ay
    Z = disp * np.sin(th) * np.sin(ph) * az
    P = np.stack([X, Y, Z], -1)
    du = np.gradient(P, axis=0)
    dv = np.gradient(P, axis=1)
    N = np.cross(du, dv)
    N /= np.linalg.norm(N, axis=-1, keepdims=True) + 1e-9
    if float(np.sum(N * P)) < 0:
        N = -N
    V = P.reshape(-1, 3)
    Nf = N.reshape(-1, 3)
    faces = []
    for i in range(stacks):
        for j in range(slices):
            a = i * slices + j
            b = i * slices + (j + 1) % slices
            c = (i + 1) * slices + j
            d = (i + 1) * slices + (j + 1) % slices
            faces.append((a, b, d))
            faces.append((a, d, c))
    # Binary PLY (Mitsuba parses this far faster than ASCII).
    import struct

    vdata = np.concatenate([V, Nf], axis=1).astype("<f4")
    fbuf = bytearray()
    for t in faces:
        fbuf += struct.pack("<Biii", 3, int(t[0]), int(t[1]), int(t[2]))
    header = (
        "ply\nformat binary_little_endian 1.0\n"
        f"element vertex {len(V)}\n"
        "property float x\nproperty float y\nproperty float z\n"
        "property float nx\nproperty float ny\nproperty float nz\n"
        f"element face {len(faces)}\n"
        "property list uchar int vertex_indices\nend_header\n"
    )
    with open(path, "wb") as f:
        f.write(header.encode("ascii"))
        f.write(vdata.tobytes())
        f.write(bytes(fbuf))
    return path


def _lights(mi):
    T = mi.ScalarTransform4f
    return {
        "key": {
            "type": "directional",
            "direction": [3.2, -4.0, -2.5],
            "irradiance": {"type": "rgb", "value": [7.5, 6.4, 4.6]},
        },
        "fill": {
            "type": "directional",
            "direction": [-3.5, 2.0, -2.0],
            "irradiance": {"type": "rgb", "value": [1.6, 1.9, 2.5]},
        },
        "rim": {
            "type": "directional",
            "direction": [0.0, -1.5, 3.5],
            "irradiance": {"type": "rgb", "value": [2.6, 2.6, 2.8]},
        },
    }, T


def _organelles(mi, T, params, frame, frames):
    """Inner nucleus + organelles, ORBITING with the frame → mobile insides."""
    t = 2 * math.pi * frame / frames
    out = {}
    nuc = params["nuc"]
    nx = nuc[0] + 0.10 * math.cos(t + nuc[3])
    ny = nuc[1] + 0.10 * math.sin(t + nuc[3])
    out["nucleus"] = {
        "type": "sphere",
        "radius": nuc[2],
        "to_world": T.translate([nx, ny, 0.12]),
        "bsdf": {"type": "diffuse", "reflectance": {"type": "rgb", "value": [0.5, 0.4, 0.27]}},
    }
    for k, (bx, by, rad, sp, ph) in enumerate(params["orgs"]):
        ang = t * sp + ph
        ox = bx + rad * 0.5 * math.cos(ang)
        oy = by + rad * 0.5 * math.sin(ang)
        out[f"org{k}"] = {
            "type": "sphere",
            "radius": rad,
            "to_world": T.translate([ox, oy, 0.05 + 0.1 * math.sin(ang)]),
            "bsdf": {"type": "diffuse", "reflectance": {"type": "rgb", "value": [0.42, 0.33, 0.22]}},
        }
    return out


def _variant_params(variant, teal):
    rng = random.Random(variant * 131 + (777 if teal else 5))
    return {
        "tint": [0.35, 0.80, 0.78]
        if teal
        else [rng.uniform(0.93, 0.97), rng.uniform(0.83, 0.89), rng.uniform(0.64, 0.72)],
        "dens": rng.uniform(13.0, 17.0),
        "nuc": (
            rng.uniform(-0.3, -0.05),
            rng.uniform(0.05, 0.3),
            rng.uniform(0.30, 0.40),
            rng.uniform(0, 6.28),
        ),
        "orgs": [
            (
                rng.uniform(-0.35, 0.4),
                rng.uniform(-0.45, 0.5),
                rng.uniform(0.13, 0.24),
                rng.uniform(0.6, 1.6) * (1 if rng.random() < 0.5 else -1),
                rng.uniform(0, 6.28),
            )
            for _ in range(rng.randint(3, 5))
        ],
    }


def bake_frame(mi, mesh_ply, params, frame, frames, size, spp):
    lights, T = _lights(mi)
    sensor = {
        "type": "perspective",
        "fov": 28,
        "to_world": T.look_at(origin=[0, 0, 6.5], target=[0, 0, 0], up=[0, 1, 0]),
        "film": {"type": "hdrfilm", "width": size, "height": size, "rfilter": {"type": "gaussian"}},
        "sampler": {"type": "independent", "sample_count": spp},
    }
    beauty = mi.load_dict(
        {
            "type": "scene",
            "integrator": {"type": "path", "max_depth": 14},
            "sensor": sensor,
            "env": {"type": "constant", "radiance": {"type": "rgb", "value": [0.55, 0.48, 0.36]}},
            "cell": {
                "type": "ply",
                "filename": mesh_ply,
                "bsdf": {"type": "roughdielectric", "int_ior": 1.35, "ext_ior": 1.0, "alpha": 0.07},
                "interior": {
                    "type": "homogeneous",
                    "albedo": {"type": "rgb", "value": params["tint"]},
                    "sigma_t": params["dens"],
                },
            },
            **_organelles(mi, T, params, frame, frames),
            **lights,
        }
    )
    col = np.array(mi.render(beauty, spp=spp))[..., :3]
    mask_scene = mi.load_dict(
        {
            "type": "scene",
            "integrator": {"type": "path", "max_depth": 2},
            "sensor": {**sensor, "sampler": {"type": "independent", "sample_count": 32}},
            "cell": {
                "type": "ply",
                "filename": mesh_ply,
                "emitter": {"type": "area", "radiance": {"type": "rgb", "value": [1, 1, 1]}},
            },
        }
    )
    m = np.array(mi.render(mask_scene, spp=32))[..., :3].mean(axis=2)
    alpha = np.clip(m * 1.5, 0, 1)
    rgb = _gblur((np.clip(col, 0, 1) ** (1 / 2.2)) * 255.0, 0.7)
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8), "RGBA")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", type=int, default=6)
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--size", type=int, default=300)
    ap.add_argument("--spp", type=int, default=192)
    ap.add_argument("--tile", type=int, default=192)
    args = ap.parse_args()

    import mitsuba as mi

    mi.set_variant("scalar_rgb")
    ASSETS.mkdir(parents=True, exist_ok=True)
    V, F, T = args.variants, args.frames, args.tile

    sheet = Image.new("RGBA", (F * T, V * T), (0, 0, 0, 0))
    for v in range(V):
        mesh = organic_mesh(tempfile.mktemp(suffix=".ply"), seed=v * 13 + 1)
        params = _variant_params(v, teal=False)
        for f in range(F):
            spr = bake_frame(mi, mesh, params, f, F, args.size, args.spp).resize((T, T), Image.LANCZOS)
            sheet.alpha_composite(spr, (f * T, v * T))
            print(f"variant {v + 1}/{V} frame {f + 1}/{F}")
    sheet.save(ASSETS / "cells.png")

    div_mesh = organic_mesh(tempfile.mktemp(suffix=".ply"), seed=999)
    div_params = _variant_params(0, teal=True)
    div = Image.new("RGBA", (F * T, T), (0, 0, 0, 0))
    for f in range(F):
        spr = bake_frame(mi, div_mesh, div_params, f, F, args.size, args.spp).resize((T, T), Image.LANCZOS)
        div.alpha_composite(spr, (f * T, 0))
        print(f"division frame {f + 1}/{F}")
    div.save(ASSETS / "cell_div.png")

    (ASSETS / "atlas.json").write_text(f'{{"variants": {V}, "frames": {F}, "tile": {T}}}\n')
    print(f"wrote {ASSETS / 'cells.png'} ({V} variants × {F} frames @ {T}px) + cell_div.png")


if __name__ == "__main__":
    main()
