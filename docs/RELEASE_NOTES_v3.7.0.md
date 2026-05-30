# cellauto v3.7.0 — Free Edition MVP

**The release that turns cellauto from a project into a product.** It defines the
free tier, makes the browser explorer a real shareable product (not just a demo),
and ships the whole monetization + go-to-market scaffolding around it.

No breaking changes. The science engine, the desktop app, and all 141 tests are
unchanged. This release is additive: a productized free tier + the business layer.

## ✨ Highlights

**The Free Edition MVP** — the browser explorer is now a complete free product:
- **Share link** — your exact F/k/preset state encodes into the URL; one click
  copies a permalink. Open a shared link and the state is restored. This is the
  free tier's growth engine.
- **Save PNG** — free single still-frame export (3× upscaled). Animated GIF, 4K,
  and the poster generator are the Pro upgrade.
- Clean GitHub Pages root URL (a redirect → the explorer) for one shareable link.

**The business layer (docs + landing):**
- `docs/FREE_MVP.md` — what the free version is and where the paid line sits.
- `docs/MONETIZATION.md` — open-core freemium strategy, competitor research,
  funnel math, and an honest grade of the "free 30s → pay" idea (re-aimed as a
  Preview Meter on cloud/export, not a wall on learning).
- `docs/PRICING.md` — Free / Plus / Pro / Classroom / Institution tiers.
- `docs/GO_TO_MARKET.md` — channel-ranked launch plan + ready-to-post copy.
- `docs/VALIDATION_KIT.md` + `docs/POND_BOUNTY.md` — price-test the plan with real
  users before building a backend.
- `.github/FUNDING.yml` — GitHub Sponsors, live with zero infra.
- Landing page: pricing/support section + Sponsor CTA; README support section.

## 📦 What's free, forever

The browser explorer and the open-source desktop app (all 12 stages + Conway +
Wolfram, run locally) stay fully functional, no account required. We only ever
meter *cloud* compute and *production* export.

## 🔜 Next (not in this release)

Accounts, billing, cloud "deep runs", the Preview Meter, and GIF/4K/poster
export are scoped but deferred — to be built against validated demand, not ahead
of it. See `docs/VALIDATION_KIT.md`.

## Install

```bash
pip install -e .      # desktop app + CLI, all rules, offline
```

Or just open the live explorer — no install. **Full changelog:** see
[CHANGELOG.md](../CHANGELOG.md).
