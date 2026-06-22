#!/usr/bin/env python3
# =============================================================================
# export_mesh.py  —  the 3D science bridge (TRUE cell division)
# -----------------------------------------------------------------------------
# Runs Gray-Scott reaction-diffusion in 3D and extracts the v-isosurface with
# marching cubes every frame, writing an OBJ sequence of a single protocell
# that genuinely GROWS, ELONGATES, PINCHES, and CLEAVES into two daughters —
# the same chemistry as docs/web3/rules/grayscott.js, lifted to a volume.
#
# This is the "true" path: the division is not animated or faked. It is the
# front instability of the real PDE in 3D. Unreal just renders the mesh
# sequence with the translucent membrane material.
#
# 3D regime: the 2D "mitosis" numbers flood a volume (more neighbours ->
# stronger diffusion). The replicating-spot regime in 3D for this 6-neighbour
# Laplacian / dt=1 scheme is F=0.030, k=0.067 (scanned + verified): a central
# seed stays one rounded cell to ~step 800, elongates by ~1000, pinches into
# two by ~1100, daughters separate, then cascade-divide.
#
# Runs anywhere with python + numpy + scikit-image (+ scipy for smoothing).
# No GPU. Deterministic (seeded). Verified in the authoring sandbox.
#
#   python export_mesh.py                                   # default hero cleave
#   STEPS=700 FRAMES=72 FRAME_STEP=10 N=72 OUTDIR=mesh python export_mesh.py
#
# Env:
#   N           grid size per axis (cube)                 (default 72)
#   F, k        Gray-Scott feed / kill                    (default 0.030 / 0.067)
#   STEPS       warm-up steps before the first frame      (default 700)
#   FRAMES      number of OBJ frames to export            (default 72)
#   FRAME_STEP  sim steps between exported frames         (default 10)
#   SEED        PRNG seed for the seed-ball perturbation  (default 7)
#   ISO         marching-cubes isolevel on v             (default 0.18)
#   SMOOTH      gaussian sigma on v before meshing        (default 0.8)
#   OUTDIR      output dir for the OBJ sequence           (default ./mesh)
#   SCALE       world size the domain maps to (UE units) (default 200.0)
#
# Frame window note: STEPS=700 + 72*10 spans steps 700..1420 — opens on a
# rounded cell, pinches mid-sequence, ends on two separated daughters. Lower
# STEPS to include more of the rounded pre-division; raise FRAME_STEP to reach
# the cascade (4, then 8 cells).
# =============================================================================

import os
import sys
import numpy as np
from skimage import measure

try:
    from scipy.ndimage import gaussian_filter
    _HAVE_SCIPY = True
except Exception:  # noqa: BLE001
    _HAVE_SCIPY = False


# ---- config ---------------------------------------------------------------
N = int(os.environ.get("N", "72"))
F = float(os.environ.get("F", "0.030"))
k = float(os.environ.get("k", "0.067"))
STEPS = int(os.environ.get("STEPS", "700"))
FRAMES = int(os.environ.get("FRAMES", "72"))
FRAME_STEP = int(os.environ.get("FRAME_STEP", "10"))
SEED = int(os.environ.get("SEED", "7"))
ISO = float(os.environ.get("ISO", "0.18"))
SMOOTH = float(os.environ.get("SMOOTH", "0.8"))
OUTDIR = os.environ.get("OUTDIR", "mesh")
SCALE = float(os.environ.get("SCALE", "200.0"))

Du, Dv, DT = 0.16, 0.08, 1.0


# ---- simulation -----------------------------------------------------------
def make_field():
    rng = np.random.default_rng(SEED)
    u = np.ones((N, N, N), np.float32)
    v = np.zeros((N, N, N), np.float32)
    c = N // 2
    r = max(4, N // 14)
    zz, yy, xx = np.ogrid[:N, :N, :N]
    ball = ((xx - c) ** 2 + (yy - c) ** 2 + (zz - c) ** 2) <= r * r
    u[ball] = 0.5
    v[ball] = 0.25
    v += (rng.random((N, N, N), dtype=np.float32) - 0.5) * 0.02
    np.clip(v, 0, 1, out=v)
    return u, v


def lap(a):
    return (np.roll(a, 1, 0) + np.roll(a, -1, 0)
            + np.roll(a, 1, 1) + np.roll(a, -1, 1)
            + np.roll(a, 1, 2) + np.roll(a, -1, 2) - 6 * a)


def step(u, v):
    uvv = u * v * v
    u += DT * (Du * lap(u) - uvv + F * (1.0 - u))
    v += DT * (Dv * lap(v) + uvv - (F + k) * v)
    np.clip(u, 0, 1, out=u)
    np.clip(v, 0, 1, out=v)


# ---- meshing + OBJ --------------------------------------------------------
def write_obj(path, verts, faces, normals):
    # center on the DOMAIN centre (not per-frame centroid) and use a FIXED
    # scale, so the daughters genuinely move apart frame-to-frame instead of
    # the whole cell appearing to breathe/rescale.
    half = N / 2.0
    s = SCALE / N
    with open(path, "w") as f:
        f.write("# protocell cleavage frame — 3D Gray-Scott isosurface\n")
        for p in verts:
            x = (p[0] - half) * s
            y = (p[1] - half) * s
            z = (p[2] - half) * s
            f.write("v %.5f %.5f %.5f\n" % (x, y, z))
        for nrm in normals:
            f.write("vn %.5f %.5f %.5f\n" % (nrm[0], nrm[1], nrm[2]))
        for tri in faces:
            a, b, c = tri[0] + 1, tri[1] + 1, tri[2] + 1
            f.write("f %d//%d %d//%d %d//%d\n" % (a, a, b, b, c, c))


def mesh_frame(v):
    field = gaussian_filter(v, SMOOTH) if (_HAVE_SCIPY and SMOOTH > 0) else v
    # pad so a blob touching the border still closes into a watertight surface
    field = np.pad(field, 1, mode="constant", constant_values=0.0)
    verts, faces, normals, _ = measure.marching_cubes(field, level=ISO)
    verts -= 1.0  # undo pad offset
    return verts, faces, normals


# ---- main -----------------------------------------------------------------
def main():
    print("[export_mesh] N=%d F=%.3f k=%.3f steps=%d frames=%d frameStep=%d "
          "iso=%.2f smooth=%.1f seed=%d -> %s/" %
          (N, F, k, STEPS, FRAMES, FRAME_STEP, ISO, SMOOTH, SEED, OUTDIR))
    if not _HAVE_SCIPY:
        print("[export_mesh] note: scipy not found — meshing un-smoothed v "
              "(install scipy for a smoother membrane).")
    os.makedirs(OUTDIR, exist_ok=True)

    u, v = make_field()
    for _ in range(STEPS):
        step(u, v)

    blob_log = []
    for fi in range(FRAMES):
        verts, faces, normals = mesh_frame(v)
        path = os.path.join(OUTDIR, "protocell.%04d.obj" % fi)
        write_obj(path, verts, faces, normals)
        nblobs = int(measure.label(v > ISO).max())
        blob_log.append(nblobs)
        if fi == 0 or fi == FRAMES - 1 or fi % 12 == 0:
            print("[export_mesh]  frame %04d  verts=%d faces=%d  cells=%d"
                  % (fi, len(verts), len(faces), nblobs))
        for _ in range(FRAME_STEP):
            step(u, v)

    # report the division arc
    first_two = next((i for i, b in enumerate(blob_log) if b >= 2), None)
    print("[export_mesh] DONE  %d OBJ frames in %s/" % (FRAMES, OUTDIR))
    print("[export_mesh] cell-count arc: %s" % blob_log)
    if first_two is not None:
        print("[export_mesh] first cleavage (1->2) at frame %04d" % first_two)
    else:
        print("[export_mesh] WARNING: no cleavage in window — lower STEPS or "
              "raise FRAMES/FRAME_STEP to reach the division.")


if __name__ == "__main__":
    main()
