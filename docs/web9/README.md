# cellauto · web9 — The Guided Colony

web9 is **web7** (the "Catalytic Silence" lab) with **living amoeba guides**
layered on top: the same cuddly amoeba from the desktop colony and the README
hero now appears in the room to **explain what's going on** and to **take
requests** — ask it to change the speed, stage, view, or parameters and it
drives web7's own controls.

The engine and the museum-vitrine shell are web7, **byte-identical**; web9 only
adds a guide layer (an overlay canvas + a few small ES modules). No build step —
vanilla ES modules + Three.js via importmap; opens from `file://` or any static
server.

```bash
python3 -m http.server -d docs   # then visit /web9/
```

## Status — V0 (scaffold)

- Forked from `docs/web7/` — engine, apparatus, live SEM, and the vitrine shell
  are unchanged.
- **Guide character** (`guide.js` + `blobgeom.js`): a procedural amoeba —
  membrane wobble, 3D sheen, wandering gaze, blink — rendered on a
  `pointer-events: none` overlay over the specimen, in Catalytic-Silence teal on
  obsidian. Respects `prefers-reduced-motion` (freezes to an idle pose).

## Roadmap — see [`../design/WEB9_PLAN.md`](../design/WEB9_PLAN.md)

- **V1 — narration:** stage/state-driven speech bubbles using the ported,
  citation-backed desktop copy, mirrored to web7's `#srStatus` aria-live; the
  guide points at what it describes.
- **V2 — ask & change:** an "ask the amoeba…" field + suggestion chips →
  whitelisted actions on web7's controls (run/view/explode/stage/params/speed);
  live freeform NL via the whipgen MCP **remote proxy**, with the offline
  intent-parser as the instant path **and** fallback.
- **V3 — polish:** helper amoebas throughout, milestone cheers, TTS, optional AI
  sprite skin.

`blobgeom.js` is a 1:1 port of `cellauto/blobgeom.py`, so the web guide and the
desktop colony are literally the same geometry.
