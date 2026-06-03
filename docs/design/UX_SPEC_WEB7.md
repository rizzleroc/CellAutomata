# UX Specification — cellauto · web7

**Catalytic Silence redesign of the CellAutomata web client**
PM → UX → DEV handoff. Authoritative for the `docs/web7/` build.

| | |
|---|---|
| Status | Built, shipped behind the existing engine. Documenting for handoff. |
| Owner (design) | Product Design |
| Engine | Reused **byte-identical** from web6 (`docs/web6/`, the "web4 / the lab" client). web7 is a presentation layer only. |
| Source of truth | `docs/web7/{index.html, styles.css, main.js, scene.js}`, `docs/web7/apparatus/*`, `docs/web7/experiment/*` |
| Design language | `docs/design/catalytic-silence.md` |
| Goal mockup | `docs/design/goal_sem_ui.jpg` |
| Regression guard | `docs/ROADMAP.md` §1 (Feature Inventory) |
| Guarding tests | `docs/web7/tests/{smoke.mjs, design.mjs, runtime.mjs}` |

This document does not invent values. Every token, duration, breakpoint, and
ARIA hook below is transcribed from the shipped source. Where a behaviour is
latent (guarded by a test but not exercised by any shipped stage) it is marked
as such.

---

## 1. Problem & goal

### 1.1 PM requirements that web7 serves

The product (`PRD.md`, `docs/ROADMAP.md`) is an **origin-of-life instrument**:
twelve abiogenesis stages plus a stromatolite capstone, each a real, steppable
simulation whose every rendered pixel traces back to an engine value
(`render_rgb(state)`). The v4.0 line earned scientific *representation* — every
frame should read like a **live SEM micrograph**, not a viridis heat-map
(`ROADMAP.md` §6). The web client (`ROADMAP.md` §3, "Web port") is the
zero-install surface for that instrument.

The ROADMAP Feature Inventory (§1) is the regression contract. web7 must not
drop: the 13-stage catalogue, the live SEM micrograph beside each apparatus,
the Run/Stop transport, the named-parts inventory, the view composition, and
the bundled Italiana / Crimson Pro / IBM Plex Mono type pack.

### 1.2 The gap web7 closes

The engine (photoreal Three.js apparatus + live web3 SEM physics) was already
proven in web6. **web6's problem was its skin.** web6 dressed the instrument in
a *vintage-lab brass/amber* identity: a warm brass accent (`#caa86a`), a green
hardcoded `MILLER–UREY 1953` chalkboard that only suited Stage 0, and type that
was not the laboratory's own grammar. That is the opposite register from
**Catalytic Silence**, which asks for a deep obsidian void, luminous teal as an
*event*, bone-white museum-caption text, and the discipline of the scientific
plate (`catalytic-silence.md`).

**web7 keeps the engine and rebuilds the room.** It is a museum vitrine over a
frozen engine: same `STAGE_MAP`, same fixed-timestep SEM loop, same single
`apparatusRunning` source-of-truth that keeps apparatus and micrograph in
lockstep. New: the Catalytic Silence shell, Roman-numeral plate numbering, the
SEM scientific-plate framing of the micrograph, a playback "breath", and a full
AAA accessibility pass. The brass identity is deleted from the stylesheet and
**`design.mjs` fails CI if `#caa86a` reappears**.

> Residual to flag for DEV: the *latent* placeholder card
> (`apparatus/placeholder.js`, `makeLabel`) still draws a `#caa86a` border and
> Georgia type into a canvas texture. It is never reached today — no shipped
> stage sets `placeholder: true` — and it lives in JS, not `styles.css`, so the
> brass-ban test does not see it. If the placeholder path is ever re-enabled,
> restyle that card to the tokens in §3.

---

## 2. Design principles

Catalytic Silence (`catalytic-silence.md`), distilled into actionable tenets.
Each maps to concrete decisions in the build.

1. **Colour is information; abundance is poverty.** The ground is obsidian. Teal
   and magenta appear only where they *mean* something — teal carries structure
   and the live "breath"; magenta marks the catalyst landing (the running
   state). Never decorative fills. *(See the running state, §6; the run button's
   teal→magenta flip, §5.)*

2. **Hairlines, not fences.** Structure is drawn with 1px rules at low alpha
   (`--hair`, `--teal-line`), corner ticks, and registration marks — a *whisper*
   of structure. No boxes-within-boxes, no heavy borders.

3. **One dominant specimen, given the dignity of breath.** Composition follows
   the vitrine and the scientific journal: a single subject (apparatus +
   micrograph) framed by deep negative space, a catalogue index left, a key
   right. Every margin is sufficient; nothing crowds.

4. **The laboratory's own grammar.** Type is functional notation, not voice. A
   didone (Italiana) for the single titular gesture; a reading-serif italic
   (Crimson Pro) for wall labels and footnotes; a geometric monospace (IBM Plex
   Mono) at near-microscopic sizes for the apparatus — plate numbers, mode,
   scale-bar metadata. *The text labels, then withdraws.*

5. **Calibrated, not animated.** Motion is the hush before a reaction completes:
   slow, eased, singular. The playback pulse is a 2200ms "breath"; the caption
   "rises" once on stage change. No theatrical gestures, and all of it yields to
   `prefers-reduced-motion`.

6. **The artefact studies the ephemeral.** Frame the live simulation as a
   *scientific plate held a moment too long* — matte, registration ticks, scale
   bar, `LIVE · SEM` badge, italic caption, 1:1 letterbox. The instrument is
   reverent about its subject.

7. **Quiet is accessible.** Restraint and accessibility are the same
   discipline. Sufficient contrast, a single visible focus ring, a polite live
   region that announces meaning and never per-frame noise, full keyboard reach.

---

## 3. Design tokens

All values transcribed from `styles.css` `:root` (lines 20–61). These are the
single source; do not redefine in component CSS.

### 3.1 Colour

| Token | Hex / value | Role | Where used |
|---|---|---|---|
| `--obsidian` | `#07090d` | Receiving darkness — the ground | `html`/`body` bg; vitrine base; Three.js `scene.background`; range-thumb fill |
| `--obsidian-2` | `#0a0e15` | Slightly lifted ground | reserved / panel washes |
| `--obsidian-3` | `#0d131c` | Raised surface | skip-link background |
| `--obsidian-4` | `#111822` | Hover wash (rgba forms preferred) | reserved |
| `--ink` | `#ece7da` | Bone-white — primary museum-caption text | brand word, caption title, body text |
| `--ink-soft` | `#cbc5b6` | Secondary ink | stage names, blurbs, plate caption, key rows |
| `--muted` | `#9a9280` | Footnote voice (≥5:1 on obsidian) | subtitle, kickers, meta line, scale bar |
| `--muted-dim` | `#6f6a5c` | Quietest label / inert dot | numerals (inactive), cat. mark, idle dots |
| `--teal` | `#3fe0d0` | The chemistry, used as an **event** | active numeral, focus ring, run icon, readout, breath dot |
| `--teal-bright` | `#74f4e7` | Teal highlight | reserved highlight |
| `--magenta` | `#d77bff` | The counterpoint — rarer still | running-state dots, run button when active (catalyst landed) |
| `--teal-line` | `rgba(63,224,208,.18)` | Hairline structure | corner ticks, registration marks, scale bar, button borders |
| `--teal-line-soft` | `rgba(63,224,208,.09)` | Faintest teal rule | reserved |
| `--teal-glow` | `rgba(63,224,208,.38)` | Glow / bloom accent | active-numeral text-shadow, thumb glow, plate breath |
| `--magenta-line` | `rgba(215,123,255,.22)` | Magenta hairline | run button border when active |
| `--hair` | `rgba(236,231,218,.08)` | Neutral hairline | register/index/key borders, view-toggle frame, plate border |
| `--hair-soft` | `rgba(236,231,218,.045)` | Faintest neutral rule | index/key footer tops |
| `--plate-bg` | `#0a0e16` | Behind the micrograph | plate background, canvas background |

Three.js scene colours (in `scene.js`, deliberately matched to the shell):
background `#07090d`; bench `#14110d`; wall `#0a0d12`; backdrop gradient
`#080a0f → #05070a` with a `rgba(63,224,208,0.22)` teal hairline and
`rgba(154,146,128,0.55)` mono caption. Tungsten key light `#ffd29a`, cool rim
`#b9c4e0`, warm lamp `#ffb866` — these define the glass as a luminous specimen
against the dark and are intentional, not skin.

### 3.2 Type scale

Three families, self-hosted in `assets/fonts/`, declared `@font-face` with
`font-display: swap` (`styles.css` 9–18). Stacks include period fallbacks.

| Variable | Family | Fallback chain | Role |
|---|---|---|---|
| `--font-display` | **Italiana** 400 | Didot, Bodoni MT, Playfair Display, Georgia, serif | The single titular gesture |
| `--font-read` | **Crimson Pro** 400 (regular + italic) | Crimson Text, Georgia, Times New Roman, serif | Wall labels, blurbs, body, footnotes |
| `--font-mono` | **IBM Plex Mono** 400 + 600 | ui-monospace, SFMono-Regular, Menlo, Consolas, monospace | Apparatus: plate no., mode, kickers, scale bar, key rows |

Sizes are set by ear (not a strict ratio). Observed scale, by role:

| Size | Family | Element |
|---|---|---|
| 30px | display | caption title (`.caption-title`) |
| 26px | display | brand word (`.brand-word`), letter-spacing `.14em` |
| 19px | display | empty-state line (`.plate-empty .empty-line`) |
| 16px | read | body base (`body`), line-height 1.5 |
| 15px | read | stage name (`.stage-name`) |
| 14.5px | read | caption blurb (`.caption-blurb`) |
| 14px | read italic | brand subtitle (`.brand-sub`) |
| 13px | read italic | plate caption (`.plate-caption`) |
| 12.5px | read italic | index/key footers, empty-state sub |
| 12px | mono | stage numeral; skip-link |
| 11px | mono | readout; key rows |
| 10.5px | mono | meta line; caption label; view toggle |
| 10px | mono | kickers; plate badge; scale bar; explode label |
| 9.5px | mono | stage subtitle (`.stage-sub`), uppercase |

Monospace labels are uppercased with wide tracking (`.12em`–`.30em`) — apparatus
notation, not prose.

### 3.3 Spacing scale

A modular step set (`styles.css` 47–48), used for all padding/gaps:

| Token | px |
|---|---|
| `--s1` | 4 |
| `--s2` | 8 |
| `--s3` | 12 |
| `--s4` | 16 |
| `--s5` | 24 |
| `--s6` | 32 |
| `--s7` | 48 |
| `--s8` | 64 |

Layout columns/rows: `--col-index: 272px`, `--col-key: 248px`, `--reg-h: 66px`
(register height). These are overridden at breakpoints (§4.2).

### 3.4 Motion durations & easings

| Token | Value | Role |
|---|---|---|
| `--ease` | `cubic-bezier(.22,.61,.36,1)` | Default ease (most transitions) |
| `--ease-out` | `cubic-bezier(.16,1,.3,1)` | Decelerate (caption rise, active-plate rule) |
| `--fast` | `170ms` | Hover/affordance feedback (buttons, rows, toggle) |
| `--med` | `400ms` | State changes (run button, brand mark, emissive) |
| `--slow` | `720ms` | Caption rise; plate border/shadow transitions |
| `--breath` | `2200ms` | The playback pulse cycle (running state) |

See §6 for how these compose into the breath and caption-rise.

---

## 4. Layout & composition — the vitrine

### 4.1 Structure (desktop)

The root is `.vitrine` (full-viewport, `100dvh`, `overflow: hidden`), carrying
`data-view` as the single source of truth for composition. It is a vertical
flex: a fixed **register** on top, then a **body** grid filling the rest.

```
┌──────────────────────────────────────────────────────────────────────┐
│  REGISTER   cellauto · subtitle              PL.x · MODE · cat.        │  66px
├──────────┬───────────────────────────────────────────┬───────────────┤
│  INDEX    │              SPECIMEN                      │   KEY         │
│  (plates) │   ┌──────────────┬──────────────┐         │  (named       │
│  272px    │   │  apparatus   │   micrograph │         │   parts)      │
│           │   │  (pane-lab)  │  (pane-exp,  │         │   248px       │
│  scrolls  │   │  vtick×4     │   .plate)    │         │   scrolls     │
│           │   └──────────────┴──────────────┘         │               │
│           │   caption (wall label, top-left, overlay) │               │
│           │   instrument bar (run · explode · readout · view) bottom  │
└──────────┴───────────────────────────────────────────┴───────────────┘
```

- **Register** (`<header class="register">`): brand cluster left (breathing
  status dot · `cellauto` didone wordmark · teal rule · italic subtitle);
  monospace meta cluster right (`PL.<numeral>` · mode label · `cat. — Catalytic
  Silence`). Bottom hairline. Decorative meta is `aria-hidden`.
- **Body** (`.body`): CSS grid, `grid-template-columns: var(--col-index)
  minmax(0,1fr) var(--col-key)`.
  - **Index** (`<nav class="index">`): catalogue of plates; header
    (kicker + count), scrollable list (`#stageNav`, injected by `main.js`),
    italic footer.
  - **Specimen** (`<main class="specimen" tabindex="-1">`): absolutely-positioned
    `.panes` (apparatus + divider + micrograph), with the **caption** overlaid
    top-left and the **instrument bar** pinned bottom over a bottom-up gradient
    scrim.
  - **Key** (`<aside class="key">`): named-parts list; header (kicker + count),
    scrollable list (`#partsList`), italic footer.
- **Film**: a fixed `.grain` (≈4.5% SVG fractal-noise, `mix-blend: overlay`) and
  a `.vignette` (radial darkening to 45% at edges) sit above content,
  `pointer-events: none`, `aria-hidden`.

The specimen panes are governed entirely by `data-view` (§5, view toggle):
`split` shows both panes 50/50 with a 1px divider; `lab` expands the apparatus
to 100% (divider + micrograph hidden); `exp` expands the micrograph to 100%
(apparatus + divider + vtick hidden, and the caption is narrowed to 38% so it
doesn't fight the plate).

### 4.2 Responsive behaviour

Two breakpoints (`styles.css` 415–437). The principle: **the vitrine adapts; the
specimen stays the subject.** Furniture sheds from the outside in.

**≤ 1180px — drop the key.**
- `--col-key: 0`; `.key { display: none }`.
- Body becomes two columns: `var(--col-index) minmax(0,1fr)`.
- `--col-index` narrows 272 → 232px.
- Caption max-width relaxes to 60% (room reclaimed from the key).

**≤ 860px — drop the index; single scrolling column.**
- `--col-index: 0`; `.index { display: none }`; `--reg-h: 58px`.
- `body { overflow: auto }`, `.vitrine { height: auto; min-height: 100dvh }` —
  the page scrolls instead of being a fixed viewport.
- Body is one column. `.panes` becomes `position: relative` and stacks
  vertically (`flex-direction: column`); in split view each pane gets
  `flex: 1 1 360px; min-height: 360px` and the divider is hidden.
- Caption goes static (in-flow, no overlay animation), full width.
- Instrument bar becomes `position: sticky`, wraps (`flex-wrap`), opaque
  background, top hairline; the readout drops to its own full-width row
  (`order: 5`).
- Register tightens; subtitle and meta line hide.

At ≤860px the apparatus and micrograph are both reachable by scroll; the
3-up vitrine collapses to a vertical reading column without losing any control.

---

## 5. Component inventory

For each: **purpose**, **states**, **accessibility**. Markup in `index.html`,
behaviour in `main.js`, style in `styles.css`.

### 5.1 Register (`.register`)
- **Purpose:** museum header. Brand identity + live instrument status line.
- **States:** brand status dot is idle (`--muted-dim`) → running (teal + glow +
  breathe, via `.vitrine.is-running`). Meta line updates `PL.<numeral>` and
  mode (`LAB` / `SPLIT` / `LIVE · SEM`) live.
- **A11y:** `<h1>` is the page's single document title gesture. The entire
  `.register-meta` cluster and the status dot are `aria-hidden` (decorative —
  the real status is announced via the live region, §7).

### 5.2 Stage index plate (`.index` / `.stage-btn`)
- **Purpose:** the catalogue. One `<button class="stage-btn">` per stage,
  injected by `main.js` (13 entries): a Roman-numeral cell, the stage name, and
  the apparatus subtitle. Header shows `stageCount` (`0–XI · ✦`).
- **States:**
  - *default* — `--ink-soft` name, `--muted-dim` numeral.
  - *hover* — faint ink wash, numeral lifts to `--muted`.
  - *active* — teal wash, a teal hairline scales in on the left edge
    (`::before`, `scaleY 0→1`, `--med`/`ease-out`), numeral turns teal with
    glow, name brightens to `--ink`.
  - *pending* — `.pending` modifier: name muted, subtitle gains `· pending`.
    **Latent today** — no shipped stage sets `placeholder: true`, so this state
    is guarded but not currently rendered.
- **A11y:** native `<button>` (Enter/Space activate for free). Active button
  gets `aria-current="true"`; others have it removed. Full arrow-key navigation
  on the container (§7). Focus uses the global `:focus-visible` ring.

### 5.3 Specimen panes (`.panes` / `.pane-lab` / `.pane-exp`)
- **Purpose:** hold the two views of the subject — the 3D apparatus (`pane-lab`,
  the `#viewport` WebGL canvas with four corner `vtick`s) and the live
  micrograph (`pane-exp`, the `.plate`).
- **States:** widths driven by `data-view` (split 50/50 + divider · lab 100% ·
  exp 100%). Corner ticks hidden in exp view. On stage change the apparatus is
  rebuilt and the camera re-frames it (`frameTo`).
- **A11y:** each pane has an `aria-label` ("Apparatus" / "Live micrograph"); the
  `vtick`s and divider are `aria-hidden`. The specimen `<main>` is the skip-link
  target (`tabindex="-1"`).

### 5.4 SEM plate (`.plate` + `#expCanvas`)
- **Purpose:** the live micrograph framed as a scientific plate (full spec §9).
  A `<figure>` holding the 2D canvas, the matte with registration ticks, the
  `LIVE · SEM` badge, the `50 µm` scale bar, the italic caption, and the empty
  state.
- **States:**
  - *live* — canvas painted each tick via the SEM pipeline; 1:1 letterboxed;
    `image-rendering: pixelated` (grids) or `.smooth` (the photoreal LIFE feed).
  - *calibrating* — caption reads `calibrating…` while the classic experiment
    scripts wire up (polled ≤60×/≈3s; §8).
  - *running* — plate border + shadow gain a teal glow and breathe; the badge's
    `rec` dot turns magenta and breathes.
  - *empty/pending* — `#expEmpty` shown ("specimen pending") when no rule maps
    to the stage (§8).
- **A11y:** the plate's framing chrome (mat, scale bar) is `aria-hidden`; the
  caption is real text. Canvas is presentational (state is announced via the
  caption + live region). The badge is legible static text.

### 5.5 Caption — the wall label (`.caption`)
- **Purpose:** the museum wall label for the current specimen: a teal mono
  **label** (`Stage N — name`), a didone **title**, and a reading-serif
  **blurb**, sourced from the apparatus `meta` (`{label, title, blurb}`).
- **States:** *rises* on every stage change (opacity 0→1, translateY 6px→0,
  `--slow`/`ease-out`; re-triggered by `retriggerCaption`). In exp view it
  narrows to 38%; ≤1180px it relaxes to 60%; ≤860px it goes static (no
  animation).
- **A11y:** `pointer-events: none` (it overlays the canvas but never traps
  input). Plain semantic text (`<h2>` title). Under reduced motion it is shown
  immediately at full opacity (no rise).

### 5.6 Instrument bar (`.instrument`)
- **Purpose:** the apparatus made operable. A bottom-pinned bar over a gradient
  scrim holding: Run control, Explode slider, Readout, View toggle.
- **States:** the bar itself is `pointer-events: none` with `> * { pointer-events:
  auto }` so the scrim never blocks the canvas. Sticky + wrapping ≤860px.
- **A11y:** each child carries its own semantics (below). Logical DOM order:
  run → explode → readout → toggle.

### 5.7 Run control (`#runBtn`)
- **Purpose:** the single transport. Drives **both** the apparatus animation and
  the live SEM sim — `apparatusRunning` is the one source of truth, so they
  cannot desync (preserves the web6 engine contract; `ROADMAP.md` §1 "Run
  control").
- **States:** *idle* — teal-tinted, teal play triangle, label "Run experiment".
  *running* — flips to magenta tint + magenta square (the catalyst has landed),
  label "Stop experiment", and the whole vitrine gains `.is-running`. Auto-runs
  on every stage load. Hidden for a stage that is both a placeholder/capstone
  *and* has no live experiment (latent).
- **A11y:** `aria-pressed` reflects run/stop (toggle-button pattern). Label text
  swaps with state for AT and sighted users alike. The play/stop glyph is
  `aria-hidden` (state is in `aria-pressed` + label).

### 5.8 View toggle (`#viewToggle`)
- **Purpose:** composition control — Lab / Split / Micrograph. Sets
  `data-view` on `.vitrine` (the single source of truth that CSS reads to show/
  hide panes). Also updates the register mode label and resizes the renderer.
- **States:** the selected button gets a teal wash; switching to `lab` stops the
  experiment loop, switching away restarts it (if running) and paints one
  immediate frame so the plate is never blank.
- **A11y:** `role="radiogroup"` with `aria-label="Composition"`; each button is
  `role="radio"` with `aria-checked` kept in sync (exactly one true). Default
  selection is **Split** (`aria-checked="true"` in markup).

### 5.9 Explode slider (`#explode`)
- **Purpose:** exploded-view of the apparatus — pushes every mesh radially out
  from the model centre by `value × 1.5` (an exploded lab diagram).
- **States:** range 0–1, step 0.01, default 0. Reset to 0 on every stage load so
  a new specimen reads whole. The row (`#explodeRow`) is hidden for placeholder
  or capstone specimens.
- **A11y:** native `<input type="range">` with an explicit `<label for>` **and**
  `aria-label="Exploded view amount"`. Custom thumb keeps a visible teal ring +
  glow; keyboard arrow-stepping is native.

### 5.10 Readout (`#readout`)
- **Purpose:** a single live, per-stage telemetry line (teal mono), e.g.
  `organics collected · 42%`. The label is stage-specific
  (`READOUT_LABEL` map: organics collected / reaction extent / replication
  cycles / mean fitness / core distilled) and falls back to
  `experiment progress`. Value is the apparatus anim's `getProgress()`.
- **States:** blank for placeholder/capstone specimens; otherwise updates every
  render tick.
- **A11y:** `aria-hidden="true"` — this is **per-frame telemetry** and is
  deliberately kept out of the live region (which announces meaning, not noise;
  §7).

### 5.11 Specimen key (`.key` / `.part-row`)
- **Purpose:** the named apparatus parts as a monospace catalogue. Built per
  stage from every named mesh in the model (`main.js buildPartsPanel`). Count in
  the header.
- **States:**
  - *default* — ink-soft row with a teal-line bullet.
  - *hover / focus* — ink wash; bullet lights teal + glow; **and the
    corresponding 3D mesh's emissive is lifted** (`highlight()` → `#1f8f86`,
    restored on leave/blur) — the list illuminates the specimen.
  - *veiled* — clicking toggles `mesh.visible`; the row gets `.hidden`
    (strike-through, dimmed bullet).
  - *empty* — "No named parts on this specimen." when a model exposes none.
- **A11y:** each row is a `<button>` with `aria-pressed` reflecting the
  veil state (pressed = hidden). Hover and **focus** both illuminate (keyboard
  parity). Footer hint: "Hover to illuminate · select to veil a part."

---

## 6. Motion spec

Motion is the hush before a reaction completes. Three named motions, all on the
tokens in §3.4.

### 6.1 The running "breath" (`--breath`, 2200ms)
When the instrument runs, `main.js` toggles `.is-running` on `.vitrine`, which
triggers three synchronized 2200ms loops on `var(--ease)`:
- **brand status dot** — turns teal + glow, then `breathe`s (opacity 1 ↔ .42).
- **plate `rec` dot** — turns magenta + glow, then `breathe`s.
- **the plate frame** — `plate-breathe`: its outer glow oscillates between
  `0 0 30px -10px` and `0 0 60px -6px` of `--teal-glow` (the plate inhales).

All three share one period, so the room breathes as a single organism. This is
the only ambient motion; it is the literal "playback pulse cycle."

### 6.2 Caption rise (`--slow`, 720ms, `ease-out`)
`@keyframes caption-rise`: the wall label fades in and lifts from `translateY(6px)`
to rest. It plays once on load and is re-triggered on every stage change by
`retriggerCaption()` (clears `animation`, forces reflow, restores) — *unless*
reduced motion is set, in which case the re-trigger is skipped entirely.

### 6.3 Micro-motions
- Active-plate hairline: `scaleY(0→1)` over `--med` (`ease-out`).
- Hover affordances (buttons, rows, toggle): `--fast` (170ms) colour/background.
- Run/toggle state changes, emissive highlight: `--med` (400ms).
- Plate border/shadow transitions: `--slow` (720ms).
- Skip-link reveal: `top` over `--fast`.

### 6.4 Reduced motion
`@media (prefers-reduced-motion: reduce)` collapses **all** animation and
transition durations to `.001ms` and iteration counts to 1, and forces the
caption to its rested state (opacity 1, no transform). The breath, the
caption-rise, and every transition effectively freeze. The controller also
checks `reduceMotion.matches` and **does not** re-trigger the caption animation
on stage change. See §7.

---

## 7. Accessibility spec

web7 adds an AAA pass over the engine. All hooks below are in the shipped source
and guarded by `design.mjs` §5–6.

### 7.1 Keyboard map

| Key(s) | Context | Action |
|---|---|---|
| `Tab` / `Shift+Tab` | global | Move through the focus order (skip-link → index buttons → specimen → run → explode → view radios → key rows). |
| `Enter` / `Space` | any button | Activate (native button semantics — stage buttons, run, view radios, part rows). |
| `↑` / `↓` | stage index | Move focus to prev/next plate (`main.js` keydown on `#stageNav`; `preventDefault`). |
| `Home` / `End` | stage index | Jump focus to first / last plate. |
| `←` / `→` | explode slider | Native range step (0.01). |
| `Enter`/`Space` on skip-link | top of page | Jump to `#specimen`. |

The index implements correct **vertical-menu** semantics: arrows move focus
(they do not activate); the user commits with Enter/Space. This is the documented
intent in `main.js`.

### 7.2 ARIA

| Element | ARIA |
|---|---|
| View toggle container | `role="radiogroup"`, `aria-label="Composition"` |
| View toggle buttons | `role="radio"`, `aria-checked` (exactly one `true`, kept in sync in `setView`) |
| Run button | `aria-pressed` (`false` idle → `true` running) |
| Part rows | `aria-pressed` (`true` = part veiled/hidden) |
| Active stage button | `aria-current="true"` (removed from the rest in `loadStage`) |
| Status line, scale bar, ticks, grain, vignette, readout | `aria-hidden="true"` (decorative or per-frame) |
| Panes | `aria-label` ("Apparatus" / "Live micrograph") |
| Index / key | `aria-label` on the landmark |

### 7.3 The `srStatus` live region
`<div class="sr-only" aria-live="polite" id="srStatus">`. `announce(msg)` writes
to it. It speaks **meaning, not telemetry**: on stage load it announces
`"<label>. <title>."` (e.g. "Stage 0 — Miller–Urey. Spark-discharge apparatus ·
1953."). The per-frame readout is *intentionally excluded* (it is `aria-hidden`)
so the region is never a chatter source. `polite` = it waits for a pause.

### 7.4 Focus-visible
`:focus-visible { outline: 2px solid var(--teal); outline-offset: 3px;
border-radius: 3px; }` and `:focus:not(:focus-visible) { outline: none }` — a
single, high-contrast teal ring for keyboard users, suppressed for mouse users.
Applies uniformly (buttons, slider, rows, skip-link).

### 7.5 Skip-link & `.sr-only`
Skip-link (`Skip to specimen`) is fixed off-screen (`top: -100px`) and slides to
`var(--s4)` on focus, jumping to the `#specimen` main. `.sr-only` is the standard
1px-clip visually-hidden utility used by the live region.

### 7.6 Reduced motion (a11y view)
Honoured in **both** layers: CSS (§6.4 — durations to `.001ms`, caption forced
to rest) and the controller (`reduceMotion = matchMedia('(prefers-reduced-motion:
reduce)')`; `retriggerCaption` early-returns). A user with the OS preference set
gets a fully static instrument with no loss of function.

### 7.7 Forced-colors / high-contrast
`@media (forced-colors: active)`: structural marks (active-plate rule, vticks,
registration ticks) opt out of forced-color override so they stay visible, and
the major containers (plate, run, view toggle, register, index, key) take
`CanvasText` borders so the composition stays legible in high-contrast mode.

### 7.8 Contrast notes
Body ink `#ece7da` on obsidian `#07090d` is high-contrast. `--muted` `#9a9280`
is documented in-token as "≥5:1 on obsidian" — appropriate for the footnote /
mono-label register where it is used; do not promote it to body copy.

---

## 8. States — loading, empty, error/degradation

The live experiment is driven by classic `<script>`s (`sem.js` + rule files)
that must populate `window.SEM` / `window.CA.RULES` before use. `main.js`
handles the lifecycle states gracefully (no crashes, no blank canvas):

| State | Trigger | Presentation |
|---|---|---|
| **Calibrating** | A mapped rule exists but its globals (`CA.RULES[id]`, and `window.SEM` for SEM rules) aren't wired yet | Canvas hidden, empty state hidden, caption reads `calibrating…`. Polls every 50ms, up to 60 tries (~3s), then re-decides — it does **not** latch the empty state on a transient slow load. |
| **Empty / specimen pending** | No `STAGE_MAP` rule for the stage, **or** calibration exhausts its ~3s budget | `#expEmpty` shown: a teal `✦` mark, "specimen pending", and the sub "no live instrument mapped to this plate yet". Canvas hidden, caption cleared. |
| **Live** | Rule instantiated, `reset()`, first frame painted immediately (even paused) | Canvas visible; caption = plate name; SEM pipeline paints per tick. |
| **Degradation (render fallback)** | `window.SEM` or `renderHeight` unavailable for a rule | Falls back to the rule's own `render(rgba)` path so the plate still paints rather than failing. |
| **Renderer 0×0 guard** | In `exp` view the lab pane is `display:none` (0×0) | `scene.js setSize()` skips the resize (avoids `NaN` aspect / a 0×0 renderer); the next switch back to lab/split re-runs it with real dims. |
| **Loop safety cap** | Tab backgrounded → large `now - lastStep` | The fixed-timestep loop advances at most 4 steps per frame (`safety = 4`) so it can't spiral after a stall. |

There is no global "error toast" in web7 (the Tk client's L12 pattern); the web
client's degradation strategy is **silent graceful fallback** per the table
above. If a future change can surface a user-facing failure, route it through the
`srStatus` region and a non-blocking strip rather than an alert.

---

## 9. SEM scientific-plate framing

This is how the micrograph matches `goal_sem_ui.jpg`: a single luminous specimen
on a matte dark plate, surrounded by the quiet apparatus of a real instrument.
The goal image reads as a **scanning-electron micrograph held in a registration
mat** — a near-black field, a bright specimen catching directional light,
dotted/dashed registration margins, and microcaps metadata in the margins.
web7's `figure.plate` reconstructs that grammar with CSS chrome around the live
canvas:

| Goal-image trait | web7 realisation |
|---|---|
| **Matte dark field** | `.pane-exp` radial obsidian gradient → `.plate` `--plate-bg` (`#0a0e16`) with a deep inset shadow (`inset 0 0 80px rgba(0,0,0,.5)`) — the receiving dark. |
| **Specimen catching light** | The SEM depth-shading pipeline (`experiment/sem.js`) renders the engine height-field with Lambertian + specular shading in the `warm-sepia` palette — the same warm directional micrograph as the goal. |
| **Registration margins / ticks** | `.plate-mat` inset 10px with four corner `.reg` L-marks in `--teal-line`; plus four `vtick` corner marks around the apparatus pane. Hairlines, the instrument's own marks. |
| **Scale bar** | `.plate-scale` bottom-left: a 56px teal-hairline `bar` with end caps + `50 µm` mono microcopy. |
| **"LIVE SEM FEED" badge** | `.plate-badge` top-right: `LIVE · SEM` microcaps with a recording dot (`rec`), on a blurred translucent chip — turns magenta and breathes while running. |
| **Caption / metadata** | `.plate-caption` bottom-right: italic Crimson Pro naming the specimen, with a text-shadow so it floats over the micrograph. |
| **Letterboxing (never stretched)** | `.plate` is `aspect-ratio: 1 / 1`, capped at `min(100%, calc(100vh - 220px))`; the canvas is `object-fit: contain`. The simulation is **never anisotropically stretched** — it is letterboxed into the square plate, exactly as a real plate is matted. `image-rendering: pixelated` keeps the grid crisp (the LIFE feed opts into `.smooth`). |

The register's `modeLabel` reads `LIVE · SEM` in micrograph view, echoing the
badge. Together these make the centre pane read as an instrument feed, not a
web canvas — the design language's "scientific plate held a moment too long."

---

## 10. DEV handoff checklist

Each requirement → the web7 file(s) that implement it → the guarding test. Run:

```bash
node docs/web7/tests/smoke.mjs       # structural + live-SEM integration (zero-dep)
node docs/web7/tests/design.mjs      # Catalytic Silence design contract (zero-dep)
npm install three@0.162.0 --no-save  # for the runtime gate
node docs/web7/tests/runtime.mjs     # executes all 13 apparatus vs real three
```

| # | Requirement | Implemented in | Guarding test |
|---|---|---|---|
| R1 | 13 stages in the catalogue (Stage 0 + 11 pipeline + capstone), no regression | `main.js` `STAGES`; `apparatus/*.js` | `smoke.mjs` (registry length === 13; each apparatus `meta` + anim contract) · `runtime.mjs` (executes all 13) |
| R2 | Live SEM micrograph beside each apparatus; engine reused byte-identical | `index.html` classic scripts; `main.js` `STAGE_MAP`, SEM loop; `experiment/*` | `smoke.mjs` §7 (STAGE_MAP keys/values, classic-script order, `vm` harness drives all 13 rules through `SEM.render` to a painted, opaque, non-blank buffer) |
| R3 | SEM render uses web3's exact convention (`renderHeight` → `SEM.render` → `putImageData`) | `main.js` `renderExperimentFrame` | `smoke.mjs` §7d (`SEM.render`, `renderHeight`, `putImageData` all called) |
| R4 | `viridis.js` loads before its readers; rules bridge via globals | `index.html` script order | `smoke.mjs` §7b (viridis before `grayscott.js`/`life.js`; every rule file a classic script before module) |
| R5 | Single Run source-of-truth; apparatus + sim never desync | `main.js` `apparatusRunning`, `setRunning` | `runtime.mjs` (anim `setRunning/getProgress/update` over 60 ticks) + manual |
| R6 | Catalytic Silence palette present; **brass/amber identity gone** | `styles.css` `:root` | `design.mjs` §2 (`--teal #3fe0d0`, `--ink #ece7da`, obsidian, magenta present; `#caa86a` / `--accent` brass **absent**) |
| R7 | Self-hosted laboratory type pack (Italiana / Crimson Pro / IBM Plex Mono), no network dep | `styles.css` `@font-face`; `assets/fonts/*`; `index.html` preloads | `design.mjs` §1 (5 font files exist; 3 families `@font-face`-d; `font-display: swap`) |
| R8 | Museum-vitrine landmarks (register / index / specimen / key) + didone wordmark | `index.html`; `styles.css` | `design.mjs` §3 (`.vitrine`, `.register`, `.index`, `.specimen`, `.key`, `.brand-word` + Italiana) |
| R9 | SEM scientific-plate framing (badge, scale bar, pending state) | `index.html` `.plate*`; `styles.css` | `design.mjs` §4 (`.plate`, `LIVE · SEM` badge, `.plate-scale`, `#expEmpty`/"specimen pending") |
| R10 | Accessibility scaffolding (skip-link, live region, radiogroup, focus-visible, reduced-motion, `.sr-only`) | `index.html`; `styles.css` | `design.mjs` §5 |
| R11 | Controller wires the presentation layer (Roman numerals, `aria-current`, announcements, keyboard nav, reduced-motion) | `main.js` | `design.mjs` §6 (`is-running`, `aria-current`, `toRoman`, `srStatus`/`announce`, `ArrowDown`, `prefers-reduced-motion`) |
| R12 | Running "breath" wired in CSS **and** JS | `styles.css` `@keyframes breathe`/`plate-breathe`; `main.js` `.is-running` toggle | `design.mjs` §6 (`is-running` in both `main.js` and `styles.css`) |
| R13 | Responsive vitrine (key drops ≤1180px, index ≤860px) | `styles.css` media queries | `design.mjs` §7 (a `max-width` breakpoint exists) — manual check both breakpoints |
| R14 | No build step; valid importmap; all modules parse; relative imports resolve | `index.html` importmap; all `*.js` | `smoke.mjs` §1–3 (importmap JSON + `three`/addons mapped; `node --check` every module; relative imports exist) |
| R15 | Photoreal scene pillars (PBR/IBL + ACES + bloom), obsidian environment | `scene.js` | `smoke.mjs` §6 (`ACESFilmicToneMapping`, `RoomEnvironment`, `UnrealBloomPass`) · `runtime.mjs` (finite mesh positions, ≥3 named meshes) |
| R16 | Tasteful empty/calibrating/fallback states (no crash, no blank) | `main.js` `selectExperiment`, `showExpEmpty`, render fallback; `scene.js` 0×0 guard | `smoke.mjs` §7e (non-blank, opaque buffer) + manual for the pending state |

### CI note
`.github/workflows/pages.yml` currently invokes the **web6** smoke + runtime
gates and deploys `docs/` to Pages. web7 ships the equivalent
`smoke.mjs` / `design.mjs` / `runtime.mjs`; **add these three to the same gate**
when web7 becomes the published client (the design contract `design.mjs` is the
one that defends the redesign from regressing toward brass/amber).

### Known residuals for DEV (not blockers)
1. **Placeholder card brass.** `apparatus/placeholder.js` `makeLabel()` draws a
   `#caa86a` border + Georgia type into a canvas texture (latent — no shipped
   stage is a placeholder; not seen by `design.mjs`, which scans `styles.css`).
   Restyle to §3 tokens if the placeholder path is ever re-enabled.
2. **`pending` index state is latent.** The `.stage-btn.pending` styling and the
   run/explode hide-for-placeholder logic exist but are not exercised today (all
   13 apparatus are built). Keep them — they are the graceful path for a future
   un-baked stage.
3. **Apparatus material `brass()` in 3D.** Some apparatus modules (e.g.
   `miller_urey.js`) use a literal brass *material* (`#b8893f`) for physical
   metal parts (clamps, fittings). This is a real material on a real object, not
   UI chrome, and is part of the frozen engine — out of scope for the shell
   redesign. Leave as-is.
</content>
</invoke>
