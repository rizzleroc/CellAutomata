# Protocell — UE 5.8 dividing-cell hero render

Turns the repo's real Gray-Scott reaction–diffusion chemistry into a vertical
1080×1920 hero shot of a single protocell that grows, elongates, pinches, and
**cleaves into two** — matching the reference footage (translucent cyan
membrane, electric Fresnel rim, granular interior, circular microscope mask,
dark field, scan-sweep). The packaging (hook, HUD, loop, pulse audio) is
finished afterward in the `viral_cut` pass.

The division is not animated or model-hallucinated. It is the front
instability of the real PDE, run in 3D. Unreal renders the resulting mesh
sequence; it does not invent the motion.

## Two pipelines

| Pipeline | Bridge | Geometry | Use |
|---|---|---|---|
| **mesh** (default, "true") | `export_mesh.py` | one cell cleaving 1→2, real 3D isosurface sequence | the reference hero shot |
| heightfield (legacy) | `export_height.mjs` | top-down colony of many dividing spots on a displaced plane | colony-carpet alt |

Both share `build_scene.py` / `make_sequence.py` / `render.py` / `pcfg.py`.

## The true path (3D cleavage)

### Step 1 — generate the cleavage mesh sequence (here, no GPU)

```bash
# 72 OBJ frames of one cell cleaving into two. Verified in the sandbox.
STEPS=700 FRAMES=72 FRAME_STEP=10 N=72 OUTDIR=mesh python export_mesh.py
```

3D Gray-Scott in the replicating-spot regime `F=0.030, k=0.067` (scanned +
verified — the 2D "mitosis" numbers flood a volume). A central seed stays one
rounded cell, elongates by ~frame 30, pinches into a cleavage furrow, and
splits into two daughters around frame 38, which then drift apart. Marching
cubes (`skimage`) extracts the v-isosurface each frame; a fixed normalization
keeps the daughters genuinely separating instead of rescaling.

Knobs: `STEPS` (pre-division warm-up), `FRAME_STEP` (division speed), `N` (grid
/ membrane smoothness), `ISO`, `SMOOTH`, `SEED` (deterministic). Needs
`numpy` + `scikit-image` (+ `scipy` for the smooth membrane).

### Step 2 — copy `mesh/` to the workstation

Point the env var at it, or drop it next to the `.py` files:

```bash
export UE_MESH_SEQ_DIR=/path/to/mesh
```

### Step 3 — render

```bash
export UE_ENGINE=/opt/UnrealEngine/Engine/Binaries/Linux/UnrealEditor-Cmd
export UPROJECT=/path/to/YourProject.uproject
export UE_OUTPUT_DIR=/path/to/render_out
./run_ue.sh                         # PIPELINE=mesh is the default
```

`run_ue.sh` runs the stages in order; or run them in the editor Python console:

```python
exec(open("import_mesh_sequence.py").read())   # OBJ seq -> SM_ProtoCleave_*
exec(open("build_scene.py").read())            # membrane mat, mask, bg cells, lights, cam
exec(open("make_sequence.py").read())          # push-in + scan + per-frame reveal
exec(open("render.py").read())                 # vertical 1080x1920 / 24fps
```

### Render modes (`UE_RENDER_MODE`)

- `mrq` (default) — Movie Render Queue. The per-frame visibility tracks cleave
  the cell; camera + scan animate; full quality + motion blur.
- `flipbook` — Python reveals one `Cleave_` mesh per frame and screenshots.
  Robust fallback, needs no visibility tracks.

### Step 4 — mux + finish

```bash
ffmpeg -y -framerate 24 -i render_out/protocell.%04d.png \
  -c:v libx264 -pix_fmt yuv420p -crf 16 \
  -vf "scale=1080:1920:flags=lanczos" render_out/protocell_hero.mp4
```

Then feed `protocell_hero.mp4` to the `viral_cut` pass for the
"THIS ISN'T A CELL" hook, microscope HUD, loop point, and pulse audio.

## The look (build_scene.py → reference match)

- `M_Protocell` — translucent two-sided membrane: cyan Fresnel rim, deep-blue
  subsurface interior, granular/fibrous detail from world-space 3D Voronoi
  noise, depth-faded opacity so you see through the membrane. A magenta-rim
  instance handles the occasional pink cell.
- `M_MicroscopeMask` — post-process circular objective vignette (dark field
  outside the lens) + chromatic edge.
- Dark volumetric fog, a cool rim key + back rim, the vertical scan-sweep
  rect-light sheet, drifting background cells, and a close-up push-in camera.

## Flagged spots (glance on first run on 5.8)

The Python is authored against the documented `unreal` API but is **not
engine-tested here** (no GPU/engine in the authoring sandbox). Grep these tags:

- `FLAG-OBJ` (`import_mesh_sequence.py`) — OBJ import goes through Interchange
  in 5.8; the task importer works, swap to `InterchangeManager` if disabled.
- `FLAG-GC` — for one animated asset instead of N static meshes, export
  Alembic and import as a Geometry Cache; bind one track instead of per-frame.
- `FLAG-M / FLAG-T` (`build_scene.py`) — material expression classes,
  `connect_material_property` enums, translucency lighting mode; verify if
  Substrate is on.
- `FLAG-PP` — `M_MicroscopeMask` is a post-process material added to the PPV
  `weighted_blendables`; that pair is the version-sensitive part.
- `FLAG-S / FLAG-VIS` (`make_sequence.py`) — Sequencer channel access and the
  visibility-track polarity (flip `VIS_SHOWN` if cells show inverted).
- `FLAG-R / FLAG-X` (`render.py`) — classic Movie Render Queue vs the new 5.8
  Render Graph; most likely to need a touch.

## Verified in the authoring sandbox

- 3D cleavage dynamics: cell-count arc 1→2 at frame 38 (scanned the F/k space
  to find the replicating regime; rendered the OBJ sequence to confirm the
  rounded→dumbbell→pinch→two-daughters arc).
- 72 valid OBJ frames with vertex normals, centered + fixed-scaled.
- All Python compiles; `export_height.mjs` (legacy bridge) runs deterministically.

## Legacy heightfield path

Set `PIPELINE=heightfield` in `run_ue.sh` and generate with `export_height.mjs`
(see header). Produces the top-down colony of many small dividing spots on a
displaced plane — kept as an alternative, not the reference hero.
