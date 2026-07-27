# Run the Unreal 5.8 protocell render — on YOUR machine

This session runs in a headless cloud VM with **no GPU and no Unreal**, so it can't
render this here. Everything below runs on **your** box, where UE 5.8 is installed.
The science-driven displacement map is already committed
(`assets/protocell_hero_height.png`, a dense dividing-cell colony), so there's
nothing to generate — just point the script at your engine + project and go.

## Prereqs (one-time)
- **Unreal Engine 5.8** installed.
- A blank project, e.g. `~/Protocell/Protocell.uproject` (any empty C++/Blueprint project).
- In that project: **Edit ▸ Plugins**, enable **Python Editor Script Plugin** and
  **Movie Render Queue** (restart the editor after enabling).

## Get the kit
```bash
git clone https://github.com/rizzleroc/CellAutomata   # or: git pull
cd CellAutomata
```

## Fastest path — one command (headless)
Edit the two paths, then run:
```bash
UE=/path/to/UE_5.8/Engine/Binaries/Linux/UnrealEditor-Cmd \
PROJ=$HOME/Protocell/Protocell.uproject \
bash tools/unreal/run_ue.sh
```
(Windows: set `UE=".../Win64/UnrealEditor-Cmd.exe"`.) It runs the four steps in
order — import heightmap → build scene+material → build the division sequence →
render — then prints the ffmpeg mux line.

## Or step-by-step in the editor (most reliable for the render)
Open the project, then **Tools ▸ Execute Python Script**, in this order:
1. `tools/unreal/import_heightfield.py`   ← first `set UE_HEIGHT_PNG` to the abs path of
   `tools/unreal/assets/protocell_hero_height.png`, or edit line 7.
2. `tools/unreal/build_scene.py`
3. `tools/unreal/make_sequence.py`
4. `tools/unreal/render.py`

Then mux the frame sequence to MP4:
```bash
ffmpeg -framerate 24 -i protocell.%04d.png -c:v libx264 -pix_fmt yuv420p -crf 17 \
  -movflags +faststart protocell_hero.mp4
```
Output frames land in `<project>/Saved/MovieRenders/protocell/` (1080×1920, 24fps).

## Two version-sensitive spots (flagged in-code) — fix if 5.8 complains
- **Material node enums** (`build_scene.py`): under 5.8 a couple of
  `unreal.MaterialExpression*` / `MaterialProperty` names occasionally moved. If a
  `create_material_expression` line errors, check the name in **Window ▸ Python API
  reference** and swap it — the try/except blocks already guard the optional ones.
- **Movie Render Queue vs Graph** (`render.py`): if your build defaults to the newer
  **Movie Render Graph**, use the headless MRQ command commented at the bottom of
  `run_ue.sh`, or render the queue from the open editor.

## Re-export the heightmap (optional — to change the specimen)
Runs here or anywhere with Node; no UE needed:
```bash
# dense dividing-cell colony (what's committed):
FF=0.0367 KK=0.0649 node tools/unreal/export_height.mjs grayscott 1100 2048 protocell_hero
# other specimens: swap the rule id (soup, raf, vesicles, rna, luca, life, …)
node tools/unreal/export_height.mjs vesicles 900 2048 protocell_hero
```
→ writes `/tmp/protocell_hero_height.png`; copy it over `assets/protocell_hero_height.png`.

## Finish (the part UE shouldn't do)
Drop `protocell_hero.mp4` through a viral-cut pass for the **"THIS ISN'T A CELL"**
hook + microscope HUD + clean loop + pulse audio (see `tools/morphogenesis/viral_cut.py`).
