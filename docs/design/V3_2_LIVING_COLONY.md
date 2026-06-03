# v3.2 — Living Colony & Visual Identity

**Status:** in progress · **Ships as version:** `4.2.0`
**Roadmap source:** [`PRD.md` §4 "v3.2 — Living colony & visual identity"](../../PRD.md)
**Design north-star:** Emil Kowalski — motion *craft*, restraint, legibility before ornament.
**Design system:** [Catalytic Silence](catalytic-silence.md)

> **Version note.** The roadmap calls this milestone "v3.2", but the shipped
> package version moved to the 4.x line while the web/SEM work landed (current:
> `4.1.1`). The *desktop living-colony polish* this milestone describes was
> deferred, not done. It therefore ships as the next minor, **`4.2.0`** — the
> name "v3.2 — Living colony" is kept for continuity with the roadmap.

---

## 1. Goal

Make the amoeba colony **read as living characters, not coloured dots** — the
signature "cuddly cartoon amoeba" identity — and make the desktop app's visual
identity (Catalytic Silence) airtight. Then prove it's safe and ship it.

The north-star is craft, not spectacle: organic motion that is *felt* rather
than announced, eyes that track, membranes that breathe, faces that stay
legible at small sizes. Nothing decorative; everything calibrated.

---

## 2. Current state (what already exists — do NOT rebuild)

A pre-flight audit found the renderer is **already well past** the PRD's prose.
Already shipped and working:

| Capability | Where | State |
|---|---|---|
| Per-cell phase + blink offset (no lock-step) | `renderer.py` `_CellItems.phase/blink_off` | ✅ |
| Continuous breathe / bob / blink animation | `renderer.py` `DiscreteRenderer.animate()` | ✅ |
| Soft 3D highlight sheen on amoebas | `renderer.py` `_highlight_geom` + `_lighten` | ✅ |
| Independent ~20 fps tick, **alive while paused** | `app.py` `_animate()` (self-reschedules, no `running` guard) | ✅ |
| Per-cell deterministic expression (smile/surprise) | `renderer.py` `_expression_for` | ✅ |
| Organic blob membrane math (PIL only) | `character.py` `_blob_points` | ✅ (not in the Tk colony) |
| Full Catalytic-Silence ttk theme, bundled fonts, themed Toplevels/menus | `app.py` `_register_bundled_fonts`, style block | ✅ broad |

**The catch that makes all of it invisible:** the whole animation + face path is
gated on `renderer.animated` → `_faces_enabled = _cw >= FACE_MIN_CELL_PX (16)`.
With `CANVAS_SIZE = 600` and `DEFAULT_GRID = 60`, `_cw = 600/60 = 10 px < 16`,
so **faces and the entire breathe/blink loop are OFF by default**. They only
appear at `grid = 30` (20 px). The colony you see out of the box is static
dots.

---

## 3. The genuine gaps (workstreams)

Each workstream has acceptance criteria and is independently committed so every
edit is trackable.

### WS-1 — Living colony alive & faced by default *(linchpin)*
The amoeba colony (the `natural-selection` / `abiogenesis-stage0-soup` rule)
must breathe and show faces at the **default grid**, while staying legible.

- **Decision:** do **not** change the flagship default rule
  (`abiogenesis-pipeline`) or the global `DEFAULT_GRID` — the pipeline is an
  SEM field view and coarsening it hurts the science. Instead make faces render
  (legibly) at smaller cells.
- Lower `FACE_MIN_CELL_PX` 16 → **10** so the default 60-grid (10 px) qualifies;
  100-grid (6 px) / 150-grid (4 px) stay faceless (correctly — sub-pixel).
- Add a **level-of-detail face**: at small cell sizes draw a simplified but
  still-cute face (clear eyes + smile, the tiny "surprise" mouth dropped below a
  size floor) so 10 px reads as a character, not mush.
- Reconcile the stale `renderer.py` docstring ("≥ 18 px") with the shipped value.
- **Acceptance:** at grid 60 the colony shows faces and breathes; faces remain
  legible (verified via headless PIL preview); grids ≥100 stay faceless.

### WS-2 — Organic blob bodies + membrane motion
Replace the perfect-ellipse amoeba body (`create_oval`) with a **smoothed blob
polygon** and give it subtle, continuous membrane motion.

- New pure-logic module `cellauto/blobgeom.py` (no Tk/PIL import) producing
  deterministic, animated blob outlines — **unit-testable headlessly**.
- `DiscreteRenderer` draws the body as `create_polygon(smooth=True)`; `animate()`
  re-flows the outline each frame (slow membrane wobble), keeping the highlight.
- **Acceptance:** `blobgeom` unit tests pass (determinism, closed loop, bounded
  radius, motion non-degenerate); colony body is a wobbling blob, not an ellipse.

### WS-3 — Gaze (eyes that track)
Port the mascot's wandering-gaze idea into the colony faces — pupils drift to a
slowly-moving target, per-cell phase so the colony doesn't stare in unison.

- **Acceptance:** pupils visibly drift within the eye-white and never escape it;
  deterministic per cell; pure-logic gaze offset unit-tested.

### WS-4 — Visual identity: canonical icon, amoeba hero, favicons
- **Canonical app icon:** `docs/icon.png` (already wired in 3 places). Document
  `docs/icon_v2.png` as an archived alternate (note in this spec / CHANGELOG).
- **Amoeba hero (the "missing" asset):** add `AmoebaMascot.to_image(size)` — a
  **PIL** render of the mascot (no display, no external MCP) — and a tiny
  `tools/render_mascot_hero.py` that writes `docs/amoeba_hero.png`. Wire it into
  the README header and the About dialog.
- **Web favicons:** add `<link rel="icon">` to the `docs/web*/index.html`
  clients (canonical icon).
- **Acceptance:** hero renders headlessly and is committed; favicons present;
  `to_image` is smoke-tested.

### WS-5 — Catalytic-Silence chrome polish (surgical)
From the chrome audit — small, no structural rewrite:
1. Kill platform sans leak (`_fam_ui` → bundled mono).
2/3/7. Hoist hardcoded disabled grays (`#3a3934`, `#262421`) to named palette
   constants and reuse.
4. Name the magic mid-teal `#2c8d86` (`TEAL_MID`).
5. Bring toast colours into-system (derive from `HAIRLINE_HI` / `STOP_R`).
6. Single panel-fill constant (`#0e1218` vs `BG`).
- **Acceptance:** `python -m py_compile cellauto/app.py` clean; no behaviour
  change; palette is auditable from named constants.

### WS-6 — Residual test/doc nits
- **Wolfram Rule 110** regression test (Turing-complete; currently untested).
- **CLI subprocess** smoke tests (`python -m cellauto …`: `--help`,
  required-subcommand, headless `simulate` JSON contract, unknown-rule).
- **Stale Stage-4 tutorial copy:** `tutorial.py:58` still says "Fitness =
  Shannon entropy × total internal concentration" — the shipped Stage 4 runs the
  **Eigen–Schuster hypercycle** (`rules/abiogenesis/stage4_selection.py`). Fix
  the tutorial line + the matching `docs/science.md` paragraph; add a guard test.

### WS-7 — Release + sign-off
- Version `4.1.1` → `4.2.0`; `CHANGELOG.md` entry; mark PRD/ROADMAP v3.2 shipped.
- **Security review** (`/security-review`) of the full diff before release; fix
  any findings; document the result here.

---

## 4. Definition of Done

- [x] WS-1 faces + animation on at the default grid; legible; large grids unaffected
- [x] WS-2 organic blob bodies + membrane motion; `blobgeom` tests green
- [x] WS-3 gaze drifts, stays in-eye, deterministic
- [x] WS-4 amoeba hero rendered headlessly + wired (README + favicons); canonical icon documented — *About-dialog gallery wiring deferred (untestable Tk layout)*
- [x] WS-5 chrome leaks closed; `app.py` compiles; palette fully named
- [x] WS-6 Rule-110 test, CLI subprocess tests, Stage-4 copy fixed + guard test
- [x] WS-7 version 4.2.0 + CHANGELOG; PRD/ROADMAP updated
- [x] Full suite green (328 passed locally; CI adds the Tk-gated tests)
- [ ] Security review clean (or findings resolved + documented) — pending

---

## 5. Verification strategy (no display in this environment)

This sandbox has **no tkinter and no DISPLAY**, so the Tk GUI can't run here.

- **Pure-logic** (`blobgeom`, gaze, rules, tutorial, CLI) → real pytest in a venv.
- **Tk modules** (`app.py`, `renderer.py`, `mascot.py`) → `py_compile` +
  coverage-omitted by design; exercised by CI's display-backed matrix.
- **Visual proof without a display** → render the colony/mascot through a small
  **PIL mirror** of the new geometry to `v32-*.png` (gitignored) and inspect.

---

## 6. Process

Worktreams are partitioned by file so parallel agents never collide. Edits are
committed per workstream with descriptive messages; the final diff goes through
security review before the milestone is declared shippable.
