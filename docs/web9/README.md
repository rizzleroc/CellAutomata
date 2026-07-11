# cellauto · web9 — The Instrument

web9 is **web8** (the guided lab) forked forward into a measuring instrument. It
keeps everything web8 has — the "Catalytic Silence" lab and the **living amoeba
"slime" guides** that explain each stage and take requests (ask them to change
the speed, stage, view, or parameters and they drive the controls) — and adds a
**live measurement layer** (`observables.js`): every step samples the running
specimen's height field into a real time-series (mean level ⟨h⟩, roughness σ²,
peak, plus the rule's population line), drawn as a live sparkline, exportable as
**CSV**, with a **shareable run link** that restores the stage, view, and palette.

The engine and the museum-vitrine shell are web7/web8, **byte-identical**; web9
only adds the instrument module + its panel. No build step — vanilla ES modules +
Three.js via importmap; opens from `file://` or any static server.

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

## Roadmap — see [`../design/WEB8_PLAN.md`](../design/WEB8_PLAN.md)

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
