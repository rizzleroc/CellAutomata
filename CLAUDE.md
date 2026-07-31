# CLAUDE.md — project context for agents

Authoritative context for working in this repo. **Keep it current:** when the
structure, conventions, test/deploy flow, or the standing requirements below
change, update this file in the *same* PR. (See "Maintaining this file".)

## What this project is

CellAutomata is an origin-of-life **cellular-automata "lab"**. Two halves:

- **Python engine** — `cellauto/` (rules, SEM renderer, CLI/GUI). Packaged via
  `pyproject.toml`; entry point is the `cellauto` console script (or
  `python -m cellauto`) — `main.py` at the repo root is only a v1 deprecation
  stub. Tested with pytest under `tests/`.
- **Static web site** — `docs/`, deployed to **GitHub Pages**. The landing hub
  is `docs/index.html` (the "Catalytic Silence" ecosystem hub); it links into
  the clients below. Default live URL: `https://rizzleroc.github.io/CellAutomata/`.

The site tells two origin stories: **abiogenesis** (how life began — the lab
clients) and **ontogeny** (how *an individual* begins — sperm+egg → zygote →
multiples → stages of life).

## Web clients (under `docs/`)

| Dir | What it is | Status |
|---|---|---|
| `web7/` | **The canonical lab** ("Catalytic Silence") — 13 abiogenesis stages, each a photoreal Three.js apparatus + a live SEM micrograph | active |
| `web8/` | **The Guided Colony** = web7 + a living-amoeba guide creature (`guide.js`, `guide.css`, `blobgeom.js`) | active |
| `web9/` | **The Instrument** = web8 (guide/"slime" layer included) + a live measurement layer (`observables.js`): per-step observable sparkline (roughness σ²/⟨h⟩), CSV export, and a shareable run-URL (stage/view/palette in the hash). A **Pro paywall** (`paywall.js`/`paywall.css`) gates the Parameters rail (tweak knobs · step/reset transport · CSV/link export) behind a one-tap `$1`/`$9.99` unlock **or a redeemable access token**; watching the live specimen is free. The landing links to the on-site full-feed **Studio** (`../studio/`), **Slime Studio** (`../slime/`), and the **Murmuration** simulator (`../murmuration/`) | active |
| `web10/` | **"Mark X"** — a re-shell of web7 (own engine copies) with a refined identity: MK X build tag + magenta accent, a hero-art plate rail (`generated/web10/stageNN_*.png`), a 13-node timeline scrubber + run provenance, and a **token-gated Pro export** (`pro.js`) that renders the current stage's SEM micrograph in-page up to **4000²** | active |
| `ontogeny/` | **Part II — the origin of an individual.** Pure canvas + `sem.js`; engine `sim.js`, renderer `render.js`, controller `app.js` | active |
| `pondwater/` | **The Pond Water Analyzer** — a dark-field microscope of virtual pond water. Six procedurally-grown organisms (`organisms/*.js`) from bacterium → water flea, each with true-to-life internal organs; a continuous **infinite-zoom engine** (`main.js`) dives from the whole drop to organ level, fading in organ callout labels by scale. Three.js via importmap, `scene.js` for the wet-mount look | active |
| `slime/` | **Slime Studio** — interactive *Physarum* lab (`slime.js`): place nutrients, watch it grow paths, with a live SEM-micrograph feed beside the interactive view. Adjustable **Colony** (up to 60k plasmodia) and **Detail** (200²–360² grid, live `setGrid` realloc) controls for larger/higher-res colonies, plus a Pro paywall (shared `pro.js` token) gating a 4000² SEM plate export. Zero-dep canvas | active |
| `studio/` | **The Studio** — the full-feed generative desk: **13 engines** (flow, reaction–diffusion, Physarum incl. cosmic/kaleido/growth presets, boids murmuration, Lenia, cymatics, DLA, starling murmuration, fractal worlds), each a live tile with its own control desk, 🎲 randomize, and shareable-settings hash. Free to watch; **Pro** (shared `pro.js` token) unlocks every control desk + **real 4K video/still export** (in-browser `MediaRecorder`/`toBlob`). Single self-contained page; brought **on-site** from the former claude.ai artifact. Smoke-gated by `studio/tests/smoke.mjs` | active |
| `murmuration/` | **Murmuration** — a full starling-flocking simulator after Hoetzlein's *Flock2* (arXiv:2404.17804). **Orientation-based social flocking** (avoidance/alignment/cohesion as *turning* pressures through a limited visual field) drives a **single-body fixed-wing flight model** (`flock.js` — lift/drag/gravity/banking/stall; birds lose altitude in turns, speed up in dives). Framework-free engine (spatial-hash neighbours, seeded RNG) → InstancedMesh birds with a GPU wingbeat (`bird.js`); dusk-sky scope (`scene.js`); controller (`main.js`) with six regimes (`presets.js`), a stooping peregrine, order-parameter telemetry, three camera modes, and a shareable URL hash | active |
| `web`, `web2`, `web3`, `web6` | earlier clients, retained for comparison | legacy |

Self-hosted fonts live in `web8/assets/fonts/`; ontogeny reuses them via
`../web8/assets/fonts/`. PRDs: `docs/PRD_ONTOGENY.md`,
`docs/PRD_SEM_VISUALIZATION.md`, `docs/PRD_LIFE_DIGITAL_ORGANISMS.md`,
`docs/PRD_COSMOS.md` (**Part III — the Constructors**: quantum lifeforms,
plasma, multiverse + the Element Studio sandbox; proposed, not yet built).

## Architecture notes

- **Zero-dependency ES modules.** No build step. Labs load **Three.js via a CDN
  importmap**; ontogeny is pure `<canvas>` + `sem.js` (classic script) + ES
  modules. Everything opens from `file://` or any static server.
- **Pro unlock — client-side token** (`pro.js`, copies in `web10/`, `slime/`, `studio/`, and the hub root `docs/pro.js`).
  The site is static (GitHub Pages), so "Pro" is a **client-side unlock keyed by a
  shareable token** (`CATSIL-XXXX-XXXX-CKSUM`, FNV-1a checksum) persisted in
  `localStorage['catsil.pro.token']`. Because localStorage is per-origin,
  redeeming a token in any client unlocks Pro in **all** of them and survives a
  reload. It exposes `window.CatSilPro` (`isUnlocked`/`showPaywall`/`redeem`/
  `grantDemo`/`clear`/`onChange`) and injects its own paywall modal (demo unlock +
  redeem-token field). It gates the **hi-res SEM plate export** (web10's `PRO ·
  4000²` pill renders the current stage in-page up to 4000²; slime's `Export 4K`
  button; **studio's** every control desk + real 4K video/still export; and the
  hub's `Go Pro` button, which unlocks site-wide from the front door). **Not a
  security boundary** — a client-side gate never is; it is the "free taste →
  unlock with a token" model (cf. `docs/PRICING.md`). The unmerged PR #76 (web9
  Clerk/Stripe server) is the server-side alternative, undeployable on Pages.
  web9 still ships its **own** `paywall.js` (token `CATALYST-SILENCE`); the other
  four share `pro.js` — propagate `pro.js` fixes to **all four copies**.
- **Front door & free/paid catalog.** `docs/index.html` is the front door: a
  hero clip (`media/hero_loop.mp4`), category-organized **tool cards each carrying
  a Free/Pro tier chip**, a plans surface with a working `Go Pro` unlock, the reel
  (`media/studio_reel.mp4`) and the plate gallery. The free/paid split is declared
  **once** in **`catalog.js`** (ES-module source of truth: `access:'free'|'freemium'`
  per tool) and mirrored to **`catalog.json`**; **`docs/PRICING.md`** is the human
  plans doc. `docs/tests/catalog.mjs` asserts the mirror never drifts and that the
  front door links + tier-labels **every** tool — add a client to `catalog.js` and
  the gate fails until the front door and PRICING agree.
- **SEM depth-shading pipeline** (`sem.js`, one copy per client): a Float32
  height field `[0,1]` → depth-shaded RGBA. `window.SEM.render(height, w, h,
  rgba, { palette, scale, relief, noise })`. Palettes `warm-sepia` / `cool-mono`;
  optional `noise` overrides substrate-grain opacity (default `0.045`; web8 copy).
  **`scale` (supersample) is capped 1–4** (`sem.js:144`). Self-contained.
- **Pond Water material/geometry grammar** (`docs/pondwater/organisms/lib.js`):
  the shared toolkit every organism inherits. `cuticle`/`organ`/`nucleus` are
  now `MeshPhysicalMaterial` (transmission + thickness + `attenuationColor`/
  `Distance` for real volumetric absorption, clearcoat, sheen, optional
  iridescence). `addRim(mat, {color,power,intensity})` injects a Fresnel edge
  glow via `onBeforeCompile` (replaces `#include <opaque_fragment>`, chains onto
  any existing hook; cuticle applies it by default — pass `rim:false` to skip).
  Micro-surface detail comes from `surfaceNormalMap({kind:'fbm'|'ridges'|
  'segments'|'granular'})` — a procedural **DataTexture** (no canvas, so it is
  identical under the headless `life.mjs` harness), cached/shared by key. Cilia
  (`ciliaRing`/`ciliaCoat`) use a shared pre-curved tapered `filamentGeo` and
  a hoisted pose object (no per-frame allocation); `helixFilament` is the
  rotating flagellum; `granuleField` is instanced cytoplasm granulation. Keep
  `userData._baseOpacity` intact — `main.js setOpacity` reads it for the dive
  fade. `nematode.js` morphs its tube buffers in place each frame (no per-frame
  geometry realloc). Tests: `smoke.mjs` guards the lib exports + anatomy
  contract; `life.mjs` builds each organism against real three and asserts it
  moves.
- **Pond Water optics post-chain** (`docs/pondwater/scene.js`): what sells the
  live-microscopy look is the *optics*. The composer is `RenderPass → BokehPass
  (depth-of-field, focus retargeted to the specimen every frame) → UnrealBloom
  (refractive dark-field edge haloes) → OutputPass → OpticsShader (radial
  chromatic aberration + cool white-balance + vignette + animated sensor
  grain)`. `composer.render` is wrapped inside `createScope` to update the DoF
  focus (`camera.distanceTo(controls.target)`) and grain seed, so `main.js`
  stays untouched. Keep `ACESFilmicToneMapping` / `RoomEnvironment` /
  `UnrealBloomPass` / `FogExp2` present — `tests/smoke.mjs` asserts them.
- **Lab control panel** is built in `docs/web7/main.js:321-433` (web8 shares the
  rules) from each rule's **own `params` schema** plus its **regime picker**
  (`rule.presets` array, or an `enum` param), with two globals (speed, palette).
  The same panel drives the **LAB / SPLIT / LIVE·SEM (micrograph)** views in
  lockstep. CA engines live in `docs/web7/experiment/rules/*.js`; the bespoke 3D
  instruments in `docs/web7/apparatus/*.js`.
- **Ontogeny growth plate** (the SEM specimen canvas) is rendered in
  `docs/ontogeny/render.js` — currently `BASE=168, SCALE=2` → a 336px offscreen
  buffer drawn to fit. Height-field primitives are grid-relative
  (resolution-independent). See standing requirement #64.

## Build · test · deploy

Deploy is automatic: `.github/workflows/pages.yml` builds + deploys `docs/` to
Pages **on push to `main` only** (`build`/`deploy` are guarded by
`if: github.event_name != 'pull_request'`). The **`test` job runs on PRs too**,
so a broken client can't reach main. Python CI is `.github/workflows/ci.yml`.

Run the JS gates locally (zero-dep, Node 20) — these mirror CI exactly:

```bash
# Web7 (canonical lab)
node docs/web7/tests/smoke.mjs
node docs/web7/tests/design.mjs
node docs/web7/tests/runtime.mjs      # needs: npm i three@0.162.0 --no-save
node docs/web7/tests/anim.mjs
node docs/web7/tests/controls.mjs     # presets wired to real params

# Web8 (guided lab) — same five gates
node docs/web8/tests/{smoke,design,runtime,anim,controls}.mjs

# Web10 (Mark X) — same five gates; design also locks the token-gated Pro export
node docs/web10/tests/{smoke,design,runtime,anim,controls}.mjs

# Web6 (legacy, still gated)
node docs/web6/tests/{smoke,colony,runtime}.mjs

# Ontogeny
node docs/ontogeny/tests/ontogeny.mjs # the science (split-day, presets, calibration)
node docs/ontogeny/tests/smoke.mjs    # module parse + page wiring + SEM harness

# Pond Water Analyzer
node docs/pondwater/tests/smoke.mjs   # importmap + module parse + roster/anatomy contract + HUD wiring
node docs/pondwater/tests/life.mjs    # needs three: each organism builds, has organs, visibly moves

# The Studio (on-site, 13 engines) + the front-door free/paid catalog
node docs/studio/tests/smoke.mjs      # 13 engines + shared Pro-token wiring + app parses
node docs/tests/catalog.mjs           # catalog.js↔.json mirror + front door links/tiers every tool

# Murmuration (Flock2 simulator)
node docs/murmuration/tests/smoke.mjs # importmap + module parse + param-schema/regime + HUD wiring
node docs/murmuration/tests/flock.mjs # the SCIENCE: order emerges, bounded/finite, banking, peregrine scatters
node docs/murmuration/tests/life.mjs  # needs three: InstancedMesh + wingbeat rig, orient() rigidity, birds move

# Python engine
pytest -q
```

## Conventions & gotchas

- **Branch + PR flow.** Develop on a feature branch; open a PR; **never push to
  `main` directly** — merging to main is what deploys. Push with
  `git push -u origin <branch>`. After pushing, open a (draft) PR if none exists.
- **CDN / ES-module caching.** A `?cb=` cache-buster on the *page* URL does **not**
  bust ES-module imports (`./sim.js`). To verify *deployed* code in a live eval,
  re-import with a fresh query: `await import('./sim.js?b=' + Date.now())`.
- **Each client owns its copy** of `sem.js` (and other shared helpers). A fix in
  one is not a fix in all — propagate deliberately.
- **web7 and web8 are *supposed* to share the experiment rules**
  (`experiment/rules/*.js`), but parity is maintained **by hand-copy and is not
  enforced** — no test diffs the two clients, and the per-client `sem.js` has
  **already drifted** (web7 runs an older copy than web8/ontogeny, with
  different shading constants). Propagate changes to both deliberately; a
  parity gate is an open gap.

## Ontogeny engine — calibration (test-locked science)

`docs/ontogeny/sim.js` is seeded/stochastic (mulberry32). The numbers below are
asserted by `tests/ontogeny.mjs` — don't regress them:

- **Split day → membranes:** days 1–3 → DCDA, 4–8 → MCDA, 8–13 → MCMA, 13+ →
  conjoined. Neutral monozygotic frequencies ≈ **27% DCDA / 68% MCDA / 4% MCMA /
  <1% conjoined**; spontaneous MZ rate ≈ **1/250** (age-flat).
- **Maternal age** raises dizygotic twinning and aneuploidy (both climb with age);
  monozygotic stays ~constant. At age 30, fraternal > identical (as in reality).
- **Triploidy** arises from both dispermy (zona-block failure) and digyny.
- Presets force deterministic outcomes via `params._force`.

## Standing requirements (maintain these)

These are committed product directions. Keep them visible and don't quietly drop
them; track work against the linked issues.

1. **Growth plate up to 4000×4000 — issue #64.** The ontogeny SEM specimen must
   be renderable at up to 4000². Plan: decouple grid resolution from display
   (`renderPlate(grid, scale)`); two-tier (interactive live res + on-demand
   high-res render/PNG export); **memory-safe tiled SEM** for 4000² (~64 MB RGBA
   + scratch); lift/parameterize the `scale` cap; keep granularity/relief
   grid-relative so it magnifies cleanly; **hard-bound** the max (cf. SEC-008 /
   #42). Cover a large-grid render in `ontogeny/tests/smoke.mjs`.
2. **Micrograph control parity — issue #65.** Every stage's micrograph should
   expose its model's full real knob set **and** a regime picker. Known gaps:
   **grayscott** (add `Du`, `Dv`, `substeps` — currently hardcoded in
   `grayscott.js:16-21`); **natural-selection** (only `amoebaLifespan`);
   **life** (the only stage with no regime picker). Guard a minimum control set
   per rule with a smoke test.
3. **Test gates must verify the science — issue #67.** Several smoke gates pass
   on blank/garbage output (ontogeny lights 100% of pixels from the `0.10`
   substrate fill alone; the lab gate only checks opaque + >1 colour), and the
   ontogeny "stochastic across seeds" test is dead (every preset sets `_force`).
   Assert *structure* (specimen relief > substrate) and that the sim evolves.
4. **CI & shared-code integrity — issue #68.** Headless `pytest` is red (a SEM
   test pulls in `app.py` → `import tkinter`) but masked by the 80% coverage
   gate; `pages.yml` skips the JS gate on root-only changes (`paths:["docs/**"]`);
   there is **no** web7↔web8 parity gate and `sem.js` has already drifted.
5. **Docs/repo drift — issue #69.** Stale version claims (PRD.md/README say
   4.1.1 / "v4.0 alpha" / "12-stage"; reality is 4.2.0 / 13 stages), a
   `railway.toml` healthcheck pointed at an orphaned client, and duplicated
   committed assets. *Client sprawl is largely addressed:* the reorganized
   front door (`docs/index.html`, driven by `catalog.js`) now links **every**
   active client — web8 included — organized Free vs Pro, and `catalog.mjs`
   fails if a client is dropped from it.
6. **Security audit tracker — issues #44 / #35–#43.** SEC-001 (pickle RCE in
   `engine.py` snapshot load) is fixed; the input-validation Highs (snapshot
   dims/arrays #36/#37, path traversal #38, image-decode #39, dep pinning #41,
   resource bounds #42, CI scan #43) remain open — keep them on the radar.
7. **Part III — the Constructors (proposed).** `docs/PRD_COSMOS.md` specifies the
   next-phase client (fork of web9): **plasma**, **quantum lifeforms**, and
   **multiverse** constructor plates plus the **Element Studio** sandbox (combine
   any elements to create/transform). Adds a **SPECULATIVE** honesty tier beside
   REAL/REPRESENTATIONAL; every plate declares its tier. New plates reuse the rule
   (`renderHeight`) / apparatus (`build`+`meta`) / preset contracts, so the panel,
   SEM micrograph, and observables come free; the element-palette editor is the
   one new UI surface. Prompt/PRD only — no code shipped yet.

## Maintaining this file

Treat CLAUDE.md as living. Update it in the same PR whenever you: add/retire a
client, change the test or deploy flow, alter the SEM contract or the control-
panel wiring, change ontogeny calibration, or add/resolve a standing
requirement. When a standing-requirement issue closes, move it from "open
direction" to a one-line "done" note (or remove it) so this list reflects reality.
