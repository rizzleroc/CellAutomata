# web8 — The Guided Colony

**Status:** PLAN (pre-implementation) · **Builds on:** **web7** (`docs/web7/`)
**Design north-star:** Emil Kowalski motion craft + web7's **Catalytic Silence**
language (obsidian ground, rationed teal/magenta, Italiana/Crimson/IBM-Plex).

> **web7 reconciled.** web7 is real — it shipped in **PR #46** ("AAA Catalytic
> Silence lab") and is **merged to `main`** at `docs/web7/` (an earlier local
> mirror made it look absent). web7 reuses web6's engine *byte-identical* under
> the museum-vitrine shell. **web8 = a full-lab upgrade forked from web7**, adding
> the living amoeba guides. The engine stays frozen; we add a layer.

---

## 1. Vision

web8 is **web7's instrument, narrated and driven by living amoeba guides** — the
same characters as the desktop colony and the README hero, rendered in web7's
own teal-on-obsidian restraint. Three pillars (your words):

1. **Amoeba heroes throughout** — a persistent host guide + ephemeral helpers
   that surface beside a control or a region to annotate it.
2. **They explain what's going on** — contextual, citation-grounded narration
   tied to the current stage, the live micrograph state, and your actions.
3. **You can ask them to change it up — and they can** — an "ask the amoeba…"
   input + suggestion chips; requests drive web7's *own* controls; the guide
   acknowledges in character, performs the change, and narrates the result.

---

## 2. Architecture — fork web7, add a guide layer (static, no-build)

Reuse web7 wholesale; the only new thing is the guide layer.

- **Frozen engine + shell, carried over:** web7's apparatus (`apparatus/*`,
  Three.js), the live experiment (`experiment/` — web3 physics + `window.SEM` +
  `VIRIDIS_LUT`, classic-scripts-before-module), the vitrine markup
  (`.vitrine[data-view]` → `register` / `index` / `specimen` / `key` /
  `instrument`), `main.js` controller (`STAGES`, `STAGE_MAP`, `loadStage`,
  `selectExperiment`, `expTick`, view radiogroup, `announce()→#srStatus`,
  `expSpeedOverride`, `paramList`, Step/Reset), and the a11y/resilience work.
- **New guide layer (the web8 delta):**
  - a 2-D **overlay canvas** pinned over `.specimen` for the amoeba character(s);
  - a DOM **speech/ask UI** (bubble + "ask the amoeba…" field + chips);
  - four small ES modules: `guide.js`, `blobgeom.js`, `narration.js`,
    `intents.js`, plus `mcp_client.js` (the MCP-proxy bridge).

```
docs/web8/                      (forked from docs/web7/)
├── index.html  styles.css  main.js  scene.js   ← web7, + guide mount points
├── apparatus/  experiment/  assets/            ← web7 engine, unchanged
├── guide.js        amoeba character: render, moods, speech bubble, anchoring
├── blobgeom.js     JS port of cellauto/blobgeom.py (membrane + gaze)
├── narration.js    stage/state → grounded copy (ported tutorial/narrative/science)
├── intents.js      "change it up" → whitelisted actions on web7's controls
├── mcp_client.js   optional freeform NL via the whipgen MCP REMOTE PROXY
└── tests/  smoke.mjs · narration.mjs · intents.mjs   (+ web7's design/anim/runtime)
```

---

## 3. The amoeba guide (`guide.js` + `blobgeom.js`)

- **Procedural, on-brand:** port `cellauto/blobgeom.py` → `blobgeom.js` and draw
  the guide exactly like the desktop colony (membrane wobble, 3D sheen, wandering
  gaze, blink) — but in **Catalytic-Silence dress**: a single teal specimen on
  the obsidian ground, magenta only as an event. Crisp at any size, zero asset/MCP
  dependency. The AI hero (`docs/amoeba_hero_ai.png`) is the host's resting portrait.
- **Moods (parameter sets over one geometry):** idle, talking, **pointing** (leans
  toward an apparatus part or a micrograph region), thinking (awaiting the MCP),
  cheer (milestones: first vesicle, RNA master strand, LUCA), concerned (empty/offline).
- **Throughout:** one host guide (corner of `.specimen`, draggable) + helper
  amoebas that pop beside the run button / view toggle / a micrograph feature.
- **Respects web7:** `prefers-reduced-motion` freezes the guide to idle (matches
  web7 gating); never overlaps the scale-bar/badge of the SEM plate.

---

## 4. "They explain what's going on" (`narration.js`)

- **Inputs:** active stage (`loadStage`), live metrics from `expTick` (step,
  population, which mechanic is firing), and user actions.
- **Copy:** port the *already-written, citation-backed* desktop copy —
  `cellauto/tutorial.py`, `cellauto/narrative.py`, `docs/science.md` — to a JS
  data module. Keeps web8 scientifically honest; no re-writing the science.
- **Delivery:** speech bubble styled as a **museum wall label** (Crimson Pro
  italic), typewriter reveal; **mirror every line to web7's `#srStatus`
  `aria-live`** so narration is accessible by construction; optional TTS (off by
  default). Event beats: stage load → what & why + citation; mid-run → live
  commentary keyed to thresholds, with the guide **pointing** at what it describes.

---

## 5. "Ask them to change it up — and they can" (`intents.js` + `mcp_client.js`)

- **Input:** an "ask the amoeba…" field + guide-offered **suggestion chips**.
- **Actions = web7's own controls (whitelisted):** the guide can only emit these,
  so it's powerful but sandboxed:

  | You say… | Drives |
  |---|---|
  | faster / slower | `expSpeedOverride` |
  | show RNA world / next / prev | `loadStage` / `stageSelect` |
  | lab / split / micrograph only | the view radiogroup |
  | run / pause / step / reset | `runBtn` / Step / Reset |
  | explode / reassemble | the `explode` slider |
  | <param> up/down (per stage) | `paramList` inputs |
  | what is this? / why? | narrate current stage/mechanic |

  Flow: parse → act on the real control → guide acknowledges in character →
  narrates the effect (and mirrors to `#srStatus`).
- **Live freeform NL via the MCP remote proxy:** since the whipgen MCP is exposed
  through a **remote proxy**, `mcp_client.js` POSTs the user's question (+ a compact
  state digest) to that proxy's LLM-chat endpoint and gets back **a structured
  action + explanation**, validated against the same whitelist before it runs.
  Needs: the **proxy URL**, an **auth token**, and **CORS** for the Pages origin.
  The offline intent-parser is the instant path **and** the fallback when the
  proxy is unreachable (it's been intermittent), so the client always works.

---

## 6. Reuse map

| Need | Reuse |
|---|---|
| Apparatus + live SEM + vitrine shell + a11y | `docs/web7/*` (forked) |
| Guide geometry/motion | `cellauto/blobgeom.py` → `blobgeom.js` |
| Grounded narration copy | `cellauto/tutorial.py`, `narrative.py`, `docs/science.md` |
| Host portrait | `docs/amoeba_hero_ai.png` (+ procedural fallback) |
| Live LLM | whipgen MCP via its **remote proxy** (`mcp_client.js`) |
| Optional AI mood sprites | whipgen `animate_sheet` / `pack_sheet` (build-time) |

---

## 7. Phases

- **V0 — fork + guide:** copy `docs/web7` → `docs/web8`; mount the overlay canvas;
  procedural host guide idling (breathe/blink/gaze). web7 tests still green +
  a structural smoke test.
- **V1 — narration:** port copy; `loadStage`/`expTick`-driven bubbles + pointing;
  mirror to `#srStatus`; `narration.mjs` coverage.
- **V2 — ask-to-change:** intent parser + chips driving web7's controls; guide
  acts + narrates; `intents.mjs` tests. (MCP-proxy NL behind a config flag.)
- **V3 — polish:** helper amoebas throughout, milestone cheers, TTS, AI sprite
  skin, micrograph-region pointing; mobile (index hides ≤860px) + a11y pass.

---

## 8. Cross-cutting

- **Tech:** vanilla ES modules + Three.js (web7) + a 2-D overlay canvas; no build;
  served from `docs/` (Pages). Add web8 smoke/design tests to `pages.yml`.
- **A11y:** narration → `#srStatus`; reduced-motion freezes the guide; every ask
  reachable via chips (keyboard); the guide never traps focus or hides controls.
- **Perf:** one rAF already drives web7; the guide adds a handful of canvas ops.

---

## 9. Decisions needed

1. **Fork vs in-place:** web8 as a new `docs/web8` forked from web7 *(rec: yes —
   reversible, A/B against web7)*, or fold the guides **into web7** itself?
2. **Branch:** web8 needs web7, which is on `main` (ahead of this PR-47 branch).
   Build web8 on a **branch off latest `main`** (clean, needs your go-ahead since
   I'm pinned to `claude/inspiring-pasteur-Fy2Jv`), or **merge `main` into this
   branch** and build here?
3. **MCP proxy wiring:** the live-NL path needs the **proxy URL + auth token +
   CORS** for the Pages origin — can you provide these (or confirm offline-only
   for now, MCP used at dev-time to pre-curate copy/art)?
