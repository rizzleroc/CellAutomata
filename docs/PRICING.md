# Plans & pricing — cellauto

_The free / paid map for the whole site. The machine-readable version is
[`catalog.js`](./catalog.js) (mirrored to [`catalog.json`](./catalog.json)); this
document is the human one. When a tool's tier changes, change it in **one**
place — `catalog.js` — and update this file in the same PR._

## The model in one line

**Watching is free. Creating is Pro.** Every live specimen — every lab, every
studio, every organism — runs for free in your browser. What Pro unlocks is
*making things with it*: the control desks and parameter rails, the
publication-scale exports, the data, and the larger colonies.

## Free — $0

Nothing to unlock. Open it and go.

- Every live simulation on the site, running in your browser.
- **The Lab** (`lab/`) — watch all thirteen origin-of-life stages, each beside
  its live SEM micrograph, with the amoeba guide narrating every plate.
- **Ontogeny** (`ontogeny/`) and the **Pond Water Analyzer** (`pondwater/`),
  end to end.
- The full **plate gallery** and the **studio reel**.

For the Pro tools below, watching the live feed is part of Free — the gate is
only on control + export.

## Pro — $1 a lab · $9.99 everything

One unlock, redeemable on any device with a token. Pro grants:

- **Every control desk and parameter rail** unlocked.
- **Hi-res SEM plate export — up to 4000×4000.**
- **True-detail 4K video + still export** from the Studio — computed at export
  resolution (finer grids, larger colonies, uncapped fractal stills), not upscaled.
- **Observable plots, CSV data and shareable run links.**
- **Larger colonies and higher-detail grids.**
- One unlock covers **every Pro tool on the device**.

### What each Pro tool unlocks

| Tool | Path | Free (watch) | Pro (create) |
|---|---|---|---|
| **The Lab** | `lab/` | All 13 stages, guided + measured, live | Parameters rail (tune · step · reset) · observables CSV + shareable run links · SEM plate export up to 4000×4000 |
| **The Studio** | `studio/` | All 13 engines running live | Every control desk · true-detail 4K video + still export |
| **Slime Studio** | `slime/` | The live Physarum feed | 4K SEM plate export · colonies up to 60k · higher-detail grid |

## How the unlock works

The site is a **static GitHub Pages deploy** — there is no server to hold an
entitlement — so Pro is a deliberately **client-side unlock keyed by a shareable
token**. This is a "free taste → unlock with a token" model, **not a security
boundary** (a client-side gate never is).

- **Token format:** `CATSIL-XXXX-XXXX-CKSUM` — a short body plus an FNV-1a
  checksum that makes it verifiable offline (the checksum is not a secret).
- **Storage:** persisted in `localStorage['catsil.pro.token']`. Because
  localStorage is per-origin, redeeming a token in **any** client (The Lab,
  Studio, Slime…) unlocks Pro in **all** of them, and it survives a reload.
- **Redeem:** open any Pro tool, hit **Unlock Pro**, and either run the demo
  checkout (nothing is charged — it mints a token for you) or paste a token into
  the redeem field.
- **One paywall, site-wide.** The former Instrument (`web9/`) shipped its own
  allow-list paywall; that client is retired into `lab/`, which speaks the
  shared token like everything else. There is exactly one Pro system now.

### Implementation

- `pro.js` — the shared unlock. Exposes `window.CatSilPro`
  (`isUnlocked` / `getToken` / `verify` / `redeem` / `grantDemo` / `clear` /
  `showPaywall` / `onChange`) and injects its own paywall modal;
  `showPaywall({title, reason, onUnlock})` lets each client speak its own
  product language in the heading (the Studio says "Unlock every desk"; the
  Lab says "Unlock the Instrument"). Copies live in `lab/`, `slime/` and
  `studio/` beside the hub root's — **propagate fixes to all four** (the
  parity gate and the Studio smoke gate fail CI if the copies drift).

### Getting a demo token

Any Pro tool's **Unlock Pro → demo checkout** mints and stores one for you and
prints it so you can reuse it on another device. Programmatically,
`CatSilPro.grantDemo()` returns a fresh valid token.

---

_A server-side entitlement (Clerk/Stripe) was prototyped for the Instrument in
PR #76 but is undeployable on Pages; the token model above is what ships._
