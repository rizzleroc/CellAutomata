# web9 — SEM v9, Unreal Engine 5.8 powered

A scanning-microscope (SEM) viewer for a protocell that grows and divides, built
on the real Gray-Scott reaction-diffusion engine and an Unreal Engine 5.8 render
pipeline. Hero-first, with a live SEM lab, proof-of-life metrics, and a render
backend.

## Run

Static only (no live backend) — any static server:

    python3 -m http.server 8798     # then open http://localhost:8798

Full, with the live render backend (recommended):

    python3 server.py               # serves the site + /api on :8770
    # open http://localhost:8770

`server.py` needs `numpy` + `scikit-image` (+ `scipy`) — the same deps as
`../../tools/unreal/export_mesh.py`, which it runs.

## What's live

- Hero: the real 3D cleavage mesh sequence (`assets/cleavage.bin`) in WebGL,
  with division / size / rotate controls. `window.protocellHero.load(url)` can
  hot-swap a freshly simulated cell.
- SEM lab: the actual `grayscott.js` engine rendered through the Unreal-style
  membrane shader (`sem_unreal.js`) with synthesized inner workings — membrane,
  cytoskeleton, organelles, nucleus — at 0.005×–8× magnification.
- Render bridge: `POST /api/render { F, k, frames, seed, n }` →
  `server.py` runs `export_mesh.py` → bundles the OBJ sequence → the hero
  hot-loads your freshly-simulated cell. The full cinema render
  (`render.py`, Movie Render Queue) still runs on a UE 5.8 + GPU workstation.

## API

    GET  /api/health
    POST /api/render            { F, k, frames, frame_step, n, seed }  -> { job }
    GET  /api/job/<id>          -> { status, frames, bytes, bin_url, ... }
    GET  /api/job/<id>/cleavage.bin
