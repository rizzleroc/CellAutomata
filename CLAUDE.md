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
| `lab/` | **The Lab** ("Mark X") — THE flagship, the consolidation of the former web7 (base) / web8 (+guide) / web9 (+instrument) / web10 (shell) lineage: 13 abiogenesis stages, each a photoreal Three.js apparatus + live SEM micrograph, in the Mark X shell (MK X build tag, hero-art plate rail from `generated/web10/stageNN_*.png`, 13-node timeline scrubber + provenance), with the **amoeba guide** (`guide.js`/`narration.js`/`intents.js` — narrates every stage, free) and the **instrument layer** (`observables.js`: per-step σ²/⟨h⟩ sparkline, CSV, shareable run hash). **Pro (CatSilPro)** gates the Parameters rail, observable CSV/run-link export, and the in-page SEM plate export up to **4000²**. Seven gates: `lab/tests/{smoke,design,runtime,anim,controls,intents,pro}.mjs` | active |
| `web7/` `web8/` `web9/` `web10/` | hash-preserving redirect stubs → `lab/` (each dir is a single index.html) | retired |
| `ontogeny/` | **Part II — the origin of an individual.** Pure canvas + `sem.js`; engine `sim.js`, renderer `render.js`, controller `app.js` | active |
| `pondwater/` | **The Pond Water Analyzer** — a dark-field microscope of virtual pond water. Six procedurally-grown organisms (`organisms/*.js`) from bacterium → water flea, each with true-to-life internal organs; a continuous **infinite-zoom engine** (`main.js`) dives from the whole drop to organ level, fading in organ callout labels by scale. Three.js via importmap, `scene.js` for the wet-mount look | active |
| `slime/` | **Slime Studio** — interactive *Physarum* lab (`slime.js`): place nutrients, watch it grow paths, with a live SEM-micrograph feed beside the interactive view. Adjustable **Colony** (up to 60k plasmodia) and **Detail** (200²–360² grid, live `setGrid` realloc) controls for larger/higher-res colonies, plus a Pro paywall (shared `pro.js` token) gating a 4000² SEM plate export. Zero-dep canvas | active |
| `studio/` | **The Studio** ("MK I") — the full-feed generative desk in the Catalytic Silence shell: **13 engines** (flow, reaction–diffusion, Physarum incl. cosmic/kaleido/growth presets, boids murmuration, Lenia, cymatics, DLA, starling murmuration, fractal worlds), each a live HiDPI tile with its own control desk, 🎲 randomize, and a **versioned share hash** (`#v=2` keyed by stable per-control `key`s; legacy label links still restore). Kernels live in `engines.js` (`window.StudioEngines`, classic script — vm-testable); the page is `index.html` + `engines.js` + `pro.js`. Free to watch; **Pro** (shared `pro.js` token) unlocks every control desk + **true-detail 4K video/still export** — per-engine `fidelity`/`warmPlan`/`still()` hooks compute finer fields at export size (fractal stills iterate every output pixel; a REC HUD + fidelity note keep the promise honest). Three gates: `studio/tests/{smoke,design,controls}.mjs` | active |
| `murmuration/` | **Murmuration** — a full starling-flocking simulator after Hoetzlein's *Flock2* (arXiv:2404.17804). **Orientation-based social flocking** (avoidance/alignment/cohesion as *turning* pressures through a limited visual field) drives a **single-body fixed-wing flight model** (`flock.js` — lift/drag/gravity/banking/stall; birds lose altitude in turns, speed up in dives). Framework-free engine (spatial-hash neighbours, seeded RNG) → InstancedMesh birds with a GPU wingbeat (`bird.js`); dusk-sky scope (`scene.js`); controller (`main.js`) with six regimes (`presets.js`), a stooping peregrine, order-parameter telemetry, three camera modes, and a shareable URL hash | active |
| `web`, `web2`, `web3`, `web6` | v1-era clients, retained on disk for comparison — unlinked from the catalog/front door and **no longer CI-gated** | legacy |

Self-hosted fonts live in **`docs/assets/fonts/`** (the neutral shared home);
every client references them via `../assets/fonts/`. PRDs: `docs/PRD_ONTOGENY.md`,
`docs/PRD_SEM_VISUALIZATION.md`, `docs/PRD_LIFE_DIGITAL_ORGANISMS.md`.

## Architecture notes

- **Zero-dependency ES modules.** No build step. Labs load **Three.js via a CDN
  importmap**; ontogeny is pure `<canvas>` + `sem.js` (classic script) + ES
  modules. Everything opens from `file://` or any static server.
- **Pro unlock — client-side token** (`pro.js`, copies in `lab/`, `slime/`, `studio/`, and the hub root `docs/pro.js`).
  The site is static (GitHub Pages), so "Pro" is a **client-side unlock keyed by a
  shareable token** (`CATSIL-XXXX-XXXX-CKSUM`, FNV-1a checksum) persisted in
  `localStorage['catsil.pro.token']`. Because localStorage is per-origin,
  redeeming a token in any client unlocks Pro in **all** of them and survives a
  reload. It exposes `window.CatSilPro` (`isUnlocked`/`showPaywall`/`redeem`/
  `grantDemo`/`clear`/`onChange`) and injects its own paywall modal (demo unlock +
  redeem-token field); `showPaywall({title, reason, onUnlock})` takes an optional
  text-escaped `title` so each client speaks its own product language in the
  heading (the Studio passes "Unlock every desk"; the Lab passes "Unlock the
  Instrument"; the default stays the SEM-plate heading). It gates **the lab's**
  Parameters rail + observable CSV/run-link export + `PRO · 4000²` plate pill;
  slime's `Export 4K` button; **studio's** every control desk + true-detail 4K
  video/still export; and the hub's `Go Pro` button, which unlocks site-wide
  from the front door. **Not a security boundary** — a client-side gate never
  is; it is the "free taste → unlock with a token" model (cf.
  `docs/PRICING.md`). The unmerged PR #76 (a web9-era Clerk/Stripe server) is
  the server-side alternative, undeployable on Pages. This is the **only** Pro
  system — web9's bespoke `paywall.js` retired with its client. Propagate
  `pro.js` fixes to **all four copies** (`docs/`, `lab/`, `slime/`, `studio/`
  — the parity gate and the Studio smoke gate fail CI on drift).
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
  optional `noise` overrides substrate-grain opacity (default `0.045`).
  **`scale` (supersample) is capped 1–4** (`sem.js:144`). Self-contained. The
  two live copies (`lab/experiment/sem.js`, `ontogeny/sem.js`) are pinned
  byte-identical by `docs/tests/parity.mjs`.
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
- **Lab control panel** is built in `docs/lab/main.js` (`buildParamPanel`) from
  each rule's **own `params` schema** plus its **regime picker**
  (`rule.presets` array, or an `enum` param), with two globals (speed, palette).
  The same panel drives the **LAB / SPLIT / LIVE·SEM (micrograph)** views in
  lockstep; it sits behind the CatSilPro `.param-lock` overlay for free users.
  CA engines live in `docs/lab/experiment/rules/*.js`; the bespoke 3D
  instruments in `docs/lab/apparatus/*.js`.
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
# The Lab (flagship — engine + guide + instrument, Mark X shell)
node docs/lab/tests/smoke.mjs         # importmap/modules/STAGE_MAP + merged layers parse & wire
node docs/lab/tests/design.mjs        # Catalytic Silence + Mark X contract + shared fonts + a11y
node docs/lab/tests/runtime.mjs       # needs: npm i three@0.162.0 --no-save
node docs/lab/tests/anim.mjs          # proves each experiment visibly runs
node docs/lab/tests/controls.mjs      # presets wired to real params
node docs/lab/tests/intents.mjs       # ask-the-amoeba request -> action mapping
node docs/lab/tests/pro.mjs           # CatSilPro gates rail/CSV/plate; token checksum verifies

# Shared-file parity (sem.js lab↔ontogeny · pro.js ×4)
node docs/tests/parity.mjs

# Ontogeny
node docs/ontogeny/tests/ontogeny.mjs # the science (split-day, presets, calibration)
node docs/ontogeny/tests/smoke.mjs    # module parse + page wiring + SEM harness

# Pond Water Analyzer
node docs/pondwater/tests/smoke.mjs   # importmap + module parse + roster/anatomy contract + HUD wiring
node docs/pondwater/tests/life.mjs    # needs three: each organism builds, has organs, visibly moves

# The Studio (on-site, 13 engines) + the front-door free/paid catalog
node docs/studio/tests/smoke.mjs      # engines.js registry + Pro wiring + 4-way pro.js byte-identity
node docs/studio/tests/design.mjs     # Catalytic Silence design contract (fonts/tokens/shell/a11y)
node docs/studio/tests/controls.mjs   # vm-driven kernels: controls sound, science moves, export fidelity real
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
  one is not a fix in all — propagate deliberately. The copies that are meant to
  be identical are now **machine-enforced**: `docs/tests/parity.mjs` fails CI on
  any byte drift of `sem.js` (`lab/` ↔ `ontogeny/`) or `pro.js` (hub root, `lab/`,
  `slime/`, `studio/`). The old web7↔web8 hand-copy convention retired with those
  clients — the lab lineage is one flagship now.

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
   gate; `pages.yml` skips the JS gate on root-only changes (`paths:["docs/**"]`).
   *Done:* the sem.js drift + missing parity gate are resolved — the lab lineage
   consolidated into `lab/` and `docs/tests/parity.mjs` now fails CI on byte
   drift of the shared copies.
5. **Docs/repo drift — issue #69.** *Largely done:* the four lab variants
   consolidated into `lab/` (~39 MB of duplication removed, web7/web9's
   duplicate font copies included), README/PRD version claims corrected to
   4.2.0 / 13 stages, and the `railway.toml` healthcheck repointed off the
   orphaned client. Remaining: the duplicated committed assets under
   `docs/generated/` (stale versioned renders) are still uncurated.
6. **Security audit tracker — issues #44 / #35–#43.** SEC-001 (pickle RCE in
   `engine.py` snapshot load) is fixed; the input-validation Highs (snapshot
   dims/arrays #36/#37, path traversal #38, image-decode #39, dep pinning #41,
   resource bounds #42, CI scan #43) remain open — keep them on the radar.

## Maintaining this file

Treat CLAUDE.md as living. Update it in the same PR whenever you: add/retire a
client, change the test or deploy flow, alter the SEM contract or the control-
panel wiring, change ontogeny calibration, or add/resolve a standing
requirement. When a standing-requirement issue closes, move it from "open
direction" to a one-line "done" note (or remove it) so this list reflects reality.
