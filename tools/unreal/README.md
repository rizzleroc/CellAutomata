# tools/unreal — UE 5.8 hero proof-of-concept: "THIS ISN'T A CELL"

A **handoff package** to render the origin-of-life viral concept in Unreal Engine 5.8 — real 3-D depth,
art-directed bioluminescent false-color, controllable density, deterministic loopable 1080×1920 output.
This is the v3 upgrade path: it merges Sora's glowing look with my pipeline's control, and it answers
every point from the multi-model visual critique (kill monochrome sameness, kill dead space, push the
Z-axis, distinct hero silhouette, a signature scan-sweep device).

> **Honesty / scope.** I cannot run Unreal in the build sandbox (headless Linux, no GPU/engine), so these
> scripts were authored against the **stable UE5 `unreal` Python API** but **not executed in-engine**.
> Treat them as a TD-ready first pass: ~90% there, with version-sensitive spots flagged in-code (material
> node enums under 5.8, and Movie Render **Queue** vs the newer Movie Render **Graph**). Scope is the single
> **hero shot** (the dividing cell) to lock the look + render settings before scaling to all 11 specimens.

## Prerequisites
- Unreal Engine **5.8** + a blank project (e.g. `Protocell.uproject`), GPU workstation.
- **Python Editor Script Plugin** + **Movie Render Queue** plugin enabled.
- The real-science heightmap (made in *this* repo, no UE needed):
  ```bash
  node tools/unreal/export_height.mjs grayscott 220 1024 protocell   # -> /tmp/protocell_height.png (16-bit)
  ```
  Copy that PNG to the UE box and point `UE_HEIGHT_PNG` at it.

## Files
| File | Role |
|---|---|
| `export_height.mjs` | **(runs here)** dumps a rule's real height field → 16-bit grayscale PNG for UE displacement |
| `import_heightfield.py` | imports that PNG as `T_sim_height` (linear/grayscale) |
| `build_scene.py` | builds `M_Protocell` (emissive Fresnel-rim translucent + heightmap WPO), the dividing-cell rig, dark volumetric lighting, scan-light, graded PostProcessVolume, CineCamera |
| `make_sequence.py` | `SEQ_Protocell`: creeping push-in + division (parent pinches → 2 daughters separate) + scan-sweep, 120f/24fps |
| `render.py` | Movie Render Queue → 1080×1920 24fps PNG sequence |
| `run_ue.sh` | headless orchestration (edit the 3 paths) + the ffmpeg mux line |

## Run
**Headless:** edit the paths in `run_ue.sh`, then `bash tools/unreal/run_ue.sh`.
**In-editor (recommended for the render step):** Tools ▸ Execute Python Script, in order:
`import_heightfield.py` → `build_scene.py` → `make_sequence.py` → `render.py`.
Then mux the frames:
```bash
ffmpeg -framerate 24 -i protocell.%04d.png -c:v libx264 -pix_fmt yuv420p -crf 17 -movflags +faststart protocell_hero.mp4
```
Finish in my pipeline (the part UE shouldn't do): drop `protocell_hero.mp4` through a `viral_cut`-style pass
to add the **"THIS ISN'T A CELL"** hook + microscope HUD + loop + pulse audio.

## How it answers the critique
- **Monochrome sameness →** per-channel false-color (cyan rim / magenta core) + a post color-split, animatable per specimen.
- **Dead space →** a satellite colony fills the frame; density is art-directed, not left to a sim's sparse tail.
- **Push the Z-axis →** real geometry + heightmap WPO + Lumen/volumetrics give true relief and depth-of-field.
- **Signature device →** the one-pass scan-light sweep (brand-able across the whole series).
- **Loopable / deterministic →** Sequencer + MRQ render the same frames every time, trimmable to a clean loop.

## Material spec (M_Protocell) — what `build_scene.py` wires
- **Translucent**, two-sided, Subsurface shading. **Emissive** = `(Fresnel(exp 3.2) * RimColor + CoreColor*0.15) * EmissiveBoost`.
  **Opacity** = `Fresnel * 0.9` (glassy: rim opaque, core clear). **WPO** = `VertexNormalWS * (HeightTex.R * DisplaceScale)`.
- Params (animatable via a Material Parameter Collection if you want them on the Sequencer): `EmissiveBoost, ScanPhase,
  DisplaceScale, RimColor, CoreColor, HeightTex`.

## Niagara upgrade (beyond the scriptable rig — optional v3.1)
Niagara isn't fully Python-authorable, so the hero division is done with animated meshes. For richer motion,
hand-build a Niagara system: a **fluid/coacervate** sim (Niagara Fluids 2D/3D) or a **mesh-renderer emitter**
of protocells with a "split" event, driven by the same `T_sim_height` as a spawn mask. Render the same way.
