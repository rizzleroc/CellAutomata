# cellauto Free Edition — MVP definition

*What the free version is, where the line to paid sits, and the bar it has to
clear to count as "done."* This is the funnel from
[MONETIZATION.md](MONETIZATION.md); it ships as **v3.7.0**.

---

## 1. The job of the free tier

The free version exists to **acquire and activate users at zero friction**, and
to make the value obvious enough that a fraction convert to paid (Plus/Pro) or
sponsor. It is the top of the funnel — so it must be (a) instantly usable with no
install, (b) genuinely useful on its own, and (c) **shareable**, because
word-of-mouth is the cheapest growth we have.

It must *not* feel like crippleware. We never paywall learning — only scale,
convenience, and production output.

---

## 2. MVP scope — what's IN the free version

### A. Browser explorer (the funnel centrepiece) — `docs/web/`
- Live **Gray-Scott reaction-diffusion** Stage 1, running in-browser, no install.
- Five **Pearson presets** (spots · stripes · mitosis · waves · labyrinth) +
  live **F/k sliders**.
- Transport: **Play / Stop / Step / Reset**; Space to play/pause.
- **Share link** — the current F/k/preset state encodes into the URL; one click
  copies a permalink. *(New in v3.7.0 — this is the growth feature.)*
- **Save PNG** — a free single still-frame export (3× upscaled). *(New in v3.7.0.)*
- **Gallery** — the other 11 origin-of-life stages as static museum plates.
- **Pricing / Support** section + Sponsor CTA, so the upgrade path is visible.

### B. Open-source desktop app (the "power user" free option) — `pip install -e .`
- All 12 coupled abiogenesis stages + Conway + Wolfram, run locally, unlimited.
- Full GUI (parameters, scrubber, inspector, gallery), CLI, local GIF export.
- MIT licensed, forkable, runs offline.

### C. Always-free guarantees
- The browser explorer and the desktop app stay fully functional **forever**.
- No account required to use either.
- We only ever meter *cloud* compute and *production* export (see §3).

---

## 3. The boundary — what's OUT (reserved for paid)

This line is the entire business model. Free gets a real product; paid gets
scale + convenience + production output.

| Capability | Free | Paid (Plus/Pro) |
|---|---|---|
| Stage-1 browser play | ✅ unlimited | ✅ |
| Local desktop app, all 12 stages | ✅ unlimited | ✅ |
| Share current state via URL | ✅ | ✅ |
| **Save named runs to an account** | — | ✅ Plus |
| Export a single still PNG | ✅ | ✅ |
| **Animated GIF export** | — | ✅ Plus |
| **4K / poster export + plate generator** | — | ✅ Pro |
| **Cloud big-grid / long "deep runs"** | preview only¹ | ✅ Pro |
| Full 12-stage pipeline *in the browser* | — | ✅ |
| Headless/batch API, CSV data export | — | ✅ Pro |

¹ The **Preview Meter** ("free taste → pay"): cloud renders run free for ~30s,
then prompt to upgrade. Not in the MVP (needs a backend) — it's the first paid
build. The MVP only needs the *free* side to be excellent.

---

## 4. Definition of done (the MVP ships when all true)

- [x] Loads and runs in a modern browser with **no install, no account**.
- [x] All five presets + sliders work; sim is smooth.
- [x] **Share link** round-trips: open a shared URL → the exact F/k/preset is
      restored.
- [x] **Save PNG** downloads a still of the current frame.
- [x] Pricing/support visible; **Sponsor** button live (`.github/FUNDING.yml`).
- [x] Landing page deployable to GitHub Pages from `/docs` with a clean root URL.
- [x] Desktop app installs and runs all rules locally (unchanged, already true).
- [x] Versioned + changelogged + tagged as a release.

Out of scope for the MVP (deliberately deferred until demand is validated):
accounts, billing, cloud compute, the Preview Meter, GIF/4K/poster export, the
in-browser full 12-stage pipeline.

---

## 5. Success metrics (instrument before launch)

| Funnel stage | Metric | Target signal |
|---|---|---|
| Acquisition | unique visitors, ⭐, shares | channel fit |
| Activation | % who move a slider / change a preset | hook lands |
| Virality | **shared-link opens** / visitor | the new feature working |
| Intent | Sponsor clicks, early-access clicks | demand |

Validate the *paid* appetite with the Pond bounty + survey
([VALIDATION_KIT.md](VALIDATION_KIT.md)) **before** building the billing/compute
backend.

---

## 6. Why this is the right MVP

- **Zero-friction reach:** a browser page out-converts a `pip install` for the
  top of the funnel by orders of magnitude.
- **It's already real:** the science, the sim, and the visuals exist and are
  polished — the only true gaps for a *free product* (vs. a demo) were *share*
  and *save*, which v3.7.0 adds.
- **The upgrade path is honest:** every paid feature is "more/bigger/faster of a
  thing you already saw work," not a feature held hostage. That converts without
  resentment.
