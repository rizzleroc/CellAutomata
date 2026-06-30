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
| `web10/` | **Mark X** — web7 re-shelled: hero-art stage rail + a Pro · 4000² export pill (→ `web9/`), magenta accent, "MK X" build tag. Reuses web7's `rules/*` + `apparatus/*` + `scene.js`; carries web8's newer `sem.js`. Per-stage hero art in `docs/generated/web10/` (MCP-generated; backfilling). | active |
| `ontogeny/` | **Part II — the origin of an individual.** Pure canvas + `sem.js`; engine `sim.js`, renderer `render.js`, controller `app.js` | active |
| `web`, `web2`, `web3`, `web6` | earlier clients, retained for comparison | legacy |

Self-hosted fonts live in `web8/assets/fonts/`; ontogeny reuses them via
`../web8/assets/fonts/`. PRDs: `docs/PRD_ONTOGENY.md`,
`docs/PRD_SEM_VISUALIZATION.md`, `docs/PRD_LIFE_DIGITAL_ORGANISMS.md`.

## Architecture notes

- **Zero-dependency ES modules.** No build step. Labs load **Three.js via a CDN
  importmap**; ontogeny is pure `<canvas>` + `sem.js` (classic script) + ES
  modules. Everything opens from `file://` or any static server.
- **SEM depth-shading pipeline** (`sem.js`, one copy per client): a Float32
  height field `[0,1]` → depth-shaded RGBA. `window.SEM.render(height, w, h,
  rgba, { palette, scale, relief })`. Palettes `warm-sepia` / `cool-mono`.
  **`scale` (supersample) is capped 1–4** (`sem.js:144`). Self-contained.
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

# Web6 (legacy, still gated)
node docs/web6/tests/{smoke,colony,runtime}.mjs

# Ontogeny
node docs/ontogeny/tests/ontogeny.mjs # the science (split-day, presets, calibration)
node docs/ontogeny/tests/smoke.mjs    # module parse + page wiring + SEM harness

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
   per rule with a smoke test. web10's `DESIGN.md` §3 now documents each stage's
   wired knob set + these II/XI/XIII gaps as a committed reference (gated by
   `web10/tests/design.mjs`).
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
   4.1.1 / "v4.0 alpha" / "12-stage"; reality is 4.2.0 / 13 stages), client
   sprawl (web8 unlinked from the hub), a `railway.toml` healthcheck pointed at
   an orphaned client, and duplicated committed assets.
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
