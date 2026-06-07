# web8 — The Guided Colony

**Status:** PLAN (pre-implementation) · **Builds on:** [web6](../web6/README.md)
**Design north-star:** Emil Kowalski — motion craft, restraint; the amoeba as a
warm, expert *guide*, not a clippy.

> **web7?** There is no web7 — the lineage is `web → web2 → web3 → web6`
> (web4 was gitignored, web5 never shipped as a dir). web8 is the next client.

---

## 1. Vision

web8 is web6's origin-of-life lab **narrated and driven by living amoeba
guides** — the same characters from the desktop colony and the README hero.
Three pillars, in the user's words:

1. **Amoeba heroes throughout** — the cuddly amoeba appears across the UI (a
   host guide + small colony helpers that pop up to annotate things).
2. **They explain what's going on** — contextual, citation-grounded narration
   tied to the current stage, the live simulation state, and the user's actions.
3. **You can ask them to change it up — and they can** — a conversational input
   ("ask the amoeba…") + suggestion chips; requests map to real, safe changes to
   the sim/visuals, the guide acknowledges, performs them, and narrates the result.

The result: a newcomer can *watch the chemistry-to-life story unfold while a
friendly expert explains it and takes requests* — no manual required.

---

## 2. Architecture (static, no-build, GitHub-Pages — like every web client)

Reuse, don't rebuild:

- **Simulation core = web6's experiment engine, unchanged.** The byte-identical
  web3 physics (`window.CA.RULES`), the SEM depth-shading pipeline
  (`window.SEM`), the `VIRIDIS_LUT`, and the per-stage rule files already loaded
  as classic scripts before the ES module. web8's `main.js` drives them exactly
  as web6 does (fixed-timestep `step()` → `renderHeight()` → `SEM.render()` →
  `putImageData`). Optionally keep web6's Three.js apparatus pane behind a toggle.
- **New: a guide overlay layer** (vanilla ES modules + a 2-D `<canvas>` for the
  characters + a DOM speech/ask UI) composited over the experiment. No backend
  required for the core experience.

New files (mirrors web6's shape):

```
docs/web8/
├── index.html          stage host + experiment canvas + guide overlay + ask bar
├── styles.css          Catalytic-Silence chrome + speech bubbles + guide layer
├── main.js             controller: stage/sim driver (reuses web6 engine) + wiring
├── guide.js            the amoeba character system (render, moods, speech, anchor)
├── blobgeom.js         JS port of cellauto/blobgeom.py (membrane + gaze)  ← shared geometry
├── narration.js        stage/state → explanatory copy (ported tutorial/narrative/science)
├── intents.js          parse "change it up" requests → whitelisted sim/visual actions
├── experiment/         (symlink/copy of web6's engine: viridis.js, sem.js, rules/*)
└── tests/
    ├── smoke.mjs       structural gate (zero-dep) — markup/IDs, module resolution
    ├── narration.mjs   every stage has guide copy; citations resolve
    └── intents.mjs     intent-parser unit tests (request → expected action)
```

---

## 3. The amoeba guide character (`guide.js` + `blobgeom.js`)

- **Rendering — procedural canvas (recommended).** Port `cellauto/blobgeom.py`
  to `blobgeom.js` (it's pure math) and draw the guide the same way the desktop
  colony does: wobbling membrane blob, 3D sheen, **wandering gaze**, blink, mouth.
  Pros: crisp at any size, matches desktop + hero exactly, **zero asset/MCP
  dependency**, tiny. The AI hero (`docs/amoeba_hero_ai.png`) is the resting
  "portrait" for the host; the colony helpers are procedural.
- **Optional deluxe skin:** AI sprite sheets per mood via the whipgen
  `whipgen_animate_sheet` / `whipgen_pack_sheet` tools (idle/talk/point/think/
  cheer). Loaded only if present; procedural is the always-on fallback.
- **Moods/behaviors:** `idle` (breathe/blink/gaze), `talking` (mouth + bob while
  narrating), `pointing` (arm/lean toward a UI region or a spot on the SEM
  canvas), `thinking` (when parsing a request), `cheer` (milestones — first
  vesicle, RNA master strand, LUCA), `concerned` (edge/empty state). Each is a
  deterministic parameter set over the same geometry (north-star: motion, not new art).
- **"Throughout":** one persistent **host** guide (corner, draggable), plus
  ephemeral **helper** amoebas that surface beside a control or a region to
  annotate it ("← drag this to traverse the parameter landscape"), then dissolve.

---

## 4. "They explain what's going on" (`narration.js`)

- **Inputs:** active stage/rule, live metrics from the engine (step, population,
  which mechanic is firing), and user actions (stage change, run/pause, param edits).
- **Copy source:** port the *already-written, citation-backed* desktop copy —
  `cellauto/tutorial.py` (per-rule walkthroughs), `cellauto/narrative.py` (the 12
  dawn→rebirth beats), and `docs/science.md` (citations) — into a JS data module.
  This keeps web8 scientifically honest and avoids re-writing the science.
- **Delivery:** speech bubbles anchored to the guide (typewriter reveal, like the
  desktop ribbon), a collapsible transcript, optional **TTS** via the Web Speech
  API (off by default; respects reduced-motion / mute).
- **Event-driven beats:** stage load → the "what & why" + a citation; during a
  run → live commentary keyed to thresholds ("see those spots splitting? that's
  Gray-Scott — self-replicating like protocells"); the guide **points** at the
  region it's describing.

---

## 5. "Ask them to change it up — and they can" (`intents.js`)

- **Input UI:** an "ask the amoeba…" text field + a row of guide-offered
  **suggestion chips** ("show me RNA world", "make it warmer", "slow down").
- **Deterministic intent map (offline core — works on GitHub Pages, no backend):**
  a small rules-based parser maps phrases → a **whitelisted action**:

  | You say… | Action |
  |---|---|
  | faster / slower / "speed it up" | fps ↑/↓ |
  | "show RNA world" / "go to vesicles" / next/prev | stage switch |
  | warmer / cooler / "more colorful" | palette: warm-sepia / cool-mono / viridis |
  | bigger / smaller cells | grid size |
  | pause / run / reset / reseed | sim control |
  | "what is this?" / "explain" / "why?" | narrate current stage/mechanic |
  | sprites on/off, labels on/off | render toggles |

  The guide **acknowledges in character** ("You got it — warming the plate ☀️"),
  performs the action, then **narrates the effect**. Unknown requests → the guide
  offers the closest chips ("I can change speed, stage, palette, or size — which?").
- **Optional natural-language layer (config-gated):** if an LLM endpoint/key is
  configured, freeform questions route to it and it returns a **structured action
  + explanation** validated against the same whitelist. Off by default so the
  client stays static and offline-safe.
- **Safety:** the guide can ONLY emit actions from the whitelist (enumerated
  params) — never arbitrary code — so "they can change it up" is powerful but
  sandboxed.

---

## 6. Reuse map

| Need | Reuse from |
|---|---|
| Simulation + SEM render | `docs/web6/experiment/*` (web3 physics + SEM pipeline) |
| Guide geometry/motion | `cellauto/blobgeom.py` → `blobgeom.js` |
| Narration copy (grounded) | `cellauto/tutorial.py`, `cellauto/narrative.py`, `docs/science.md` |
| Host portrait / hero | `docs/amoeba_hero_ai.png`, `docs/amoeba_hero.png` |
| Mobile drawers, view toggle, chrome | `docs/web6` patterns + Catalytic Silence |
| Optional AI mood sprites | whipgen `animate_sheet` / `pack_sheet` |

---

## 7. Phases

- **V0 — scaffold:** `docs/web8/` shell reusing the web6 engine; procedural guide
  rendering on canvas (idle: breathe/blink/gaze). Structural smoke test.
- **V1 — narration:** port the copy; stage/state-driven speech bubbles + pointing;
  transcript; `narration.mjs` coverage test.
- **V2 — ask-to-change:** deterministic intent parser + suggestion chips; guide
  acknowledges + performs + narrates; `intents.mjs` unit tests.
- **V3 — polish:** colony helpers "throughout", milestone cheers, TTS, optional
  LLM NL layer, optional AI sprite skin; mobile + a11y pass.

---

## 8. Cross-cutting

- **Tech:** vanilla ES modules + 2-D canvas (+ web6's Three.js lab optional), no
  build step, served from `docs/` (Pages).
- **A11y:** narration mirrored to an `aria-live` region; reduced-motion freezes
  the guide to idle; all "ask" actions reachable via the chips (keyboard).
- **Perf:** one rAF loop drives sim + guide; guide is a handful of canvas ops.
- **Tests gate CI** alongside web2/3/6 in `pages.yml` (zero-dep `smoke.mjs` +
  the narration/intents unit gates).

---

## 9. Decisions needed (forks)

1. **Base:** build on web6's full Three.js lab (apparatus + SEM + guide), or a
   lighter standalone SEM-canvas client (faster, simpler) with guide? *(Rec:
   lighter standalone for V0–V2; add the apparatus pane in V3.)*
2. **Guide art:** procedural (blobgeom-JS) only, AI sprite sheets only, or
   procedural-with-optional-AI-skin? *(Rec: procedural primary + optional AI skin.)*
3. **"Ask" intelligence:** offline deterministic intent-parser only, or also the
   optional LLM NL layer (needs an endpoint/key)? *(Rec: ship deterministic;
   make LLM a config-gated enhancement.)*
4. **Voice (TTS):** include Web Speech narration, or text bubbles only? *(Rec:
   text first, TTS as an opt-in toggle.)*
5. **Scope:** is web8 a new **guided mode** beside web6, or the new flagship? *(Rec:
   new client beside web6; promote later if it lands well.)*
