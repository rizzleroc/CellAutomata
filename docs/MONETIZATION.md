# cellauto — Monetization Strategy

*How the money works, why people pay, what to charge, and how to test whether
this is right before betting on it.*

Status: **proposal / v0** — the strategy and the immediately-shippable pieces
(GitHub Sponsors, pricing page, landing-page CTA, go-to-market copy) ship now.
The paid SaaS tier is a plan, not a live product. Nothing here claims revenue
that doesn't exist.

---

## 1. What we're selling, in one sentence

cellauto is a scientifically-grounded origin-of-life sandbox. The **free core**
(MIT, runs locally and in the browser) is the funnel; we charge for the things
that cost us money or save the user real time — **cloud compute, big runs,
high-resolution exports, save/share, and classroom/institution tooling.**

The product never paywalls *learning*. It paywalls *scale, convenience, and
production output.* That distinction is the whole strategy.

---

## 2. How comparable projects actually make money (research)

I looked at how the closest analogues monetize. There are three durable models
in this space, and one trap.

| Project | Model | Takeaway for us |
|---|---|---|
| **PhET Interactive Simulations** (Univ. of Colorado) | 100% free; funded by **grants + donations**. Founded by a Nobel laureate. The gold standard of science-ed sims. | Education buyers *expect* a free tier. A hard paywall on the learning experience is a non-starter for schools. Grants/sponsorship are a real revenue line, not a fallback. |
| **Golly** (Game of Life) | Free, open source (GPL). Volunteer-run. | The reference CA tools are free. We can't out-free them; we win on *science depth + polish + cloud*, not by charging for Conway. |
| **Automata Ecosystem** (Steam) | **Paid one-time** (~$10–15) GPU CA sandbox sold as a *game*. | There is real consumer willingness-to-pay when CA is framed as an *experience/toy*, sold on a store with a wishlist + trailer. A "Pro desktop app" SKU is viable. |
| **Wolfram** (Mathematica / System Modeler) | Expensive per-seat + site licenses to institutions. | Institutions pay four figures for tools their people already use. Site licensing is where the big checks are — but it's a slow B2B sale. |
| **Layer / generative-art platforms** | **Subscription**; royalties by view-time. | For the art-leaning audience, recurring subscription works and the *visuals* are the product. cellauto's museum plates are a genuine asset here. |

**The trap:** charging for the basic interactive sim. Every successful science
tool in the table gives the core away. The ones that make money charge for
*compute, production output, or institutional scale* on top of a free core.

Sources are listed at the bottom of this document.

---

## 3. Your idea — "free for 30 seconds, then pay" — graded honestly

Your instinct is **right about the mechanism and wrong about where to point it.**

**Why a hard 30-second wall on everything would backfire:**
- The education market (our biggest TAM) will not adopt a tool that locks out a
  student after 30 seconds. PhET-style "free to learn" is the table-stakes
  expectation. A 30s wall kills classroom adoption, kills word-of-mouth, kills
  the SEO/Show-HN funnel that brings free users we later convert.
- The free browser explorer is our **top-of-funnel growth engine.** Walling it
  is like charging admission to your own billboard.

**Why your instinct is still correct — and where it makes money:**
The 30-second "taste then pay" mechanic is *exactly* how render tools and
generative-art apps convert: **free preview, pay for the full-resolution / full-
length output.** People will pay at the moment they want to *keep* or *scale*
something they already love.

So we keep your idea and re-aim it at the **expensive, high-intent actions**:

> **The Preview Meter.** Any *cloud* action — a deep multi-stage run, a large-grid
> simulation, an HD/4K GIF or poster export — runs **free for the first ~30
> seconds / first preview**, watermarked, then prompts: *"Loving this? Unlock the
> full render."* Basic browser play and the local desktop app stay unlimited and
> free.

This converts on willingness-to-pay (you're about to export a poster for your
classroom / portfolio) instead of taxing curiosity. It's the same psychology you
described — applied where wallets actually open.

We should **A/B test the exact threshold** (15s / 30s / 60s / "first export
free") rather than guess. See [VALIDATION_KIT.md](VALIDATION_KIT.md).

---

## 4. The model: open-core freemium + metered cloud + licensing

Because you chose a **broad audience** (hobbyist → educator → institution), the
pricing is tiered so each segment self-selects. One free funnel, four ways to
pay.

```
                         ┌──────────────────────────────┐
   FREE (the funnel) ───▶│  unlimited browser explorer   │──┐
   MIT core, local app   │  + open-source desktop build  │  │  word of mouth,
                         └──────────────────────────────┘  │  SEO, Show HN,
                                       │                     │  classrooms
                 Preview Meter (your   │                     ▼
                 "30s then pay") fires │           more free users
                 on cloud/export ──────┤                     │
                                       ▼                     │
        ┌─────────────┬───────────────┬──────────────┬──────┴────────┐
        │   PLUS      │     PRO        │  CLASSROOM    │  INSTITUTION  │
        │ hobbyist    │  creator/      │  educator     │  museum /     │
        │ $5/mo       │  educator      │  site license │  university   │
        │             │  $15/mo        │  $299+/yr     │  custom       │
        └─────────────┴───────────────┴──────────────┴───────────────┘
                                       ▲
                         SPONSOR / GRANTS (GitHub Sponsors, NSF/ed
                         foundations) — funds the pure-OSS core
```

Full price table and feature matrix: **[PRICING.md](PRICING.md)**.

### Why each segment pays

- **Plus ($5/mo, hobbyist/learner):** to *save and share* runs (permalink), run
  the full 12-stage coupled pipeline in the browser, and export HD GIFs without
  the preview watermark. Impulse price point; the generative-art crowd converts
  here.
- **Pro ($15/mo, creator / educator / researcher):** 4K + poster export, the
  museum-plate poster generator, large grids and long "deep runs" on our
  compute, headless/batch API, CSV data export, and a **commercial-use license**
  for exported art. People who *produce* (teachers making materials, artists
  selling prints, researchers generating figures) pay to scale.
- **Classroom ($299–999/yr per school, or ~$2–4/student/yr):** NGSS-aligned
  lesson bundle, a teacher dashboard, rostered student accounts with **zero
  individual sign-up friction**, and offline classroom builds. Schools pay for
  *curriculum + admin convenience*, not for the sim itself.
- **Institution / Museum (custom):** kiosk/on-prem license, the high-res museum
  plates and the "Genesis"/"Prima Materia" poster series, and co-branding.
  Four-figure checks, slow cycle, high margin.
- **Sponsor / Grants ($0+):** keeps the MIT core honest and funded; underwrites
  the free tier the whole funnel depends on. This is real money for science-ed
  OSS (PhET runs on it) — and it's **shippable today** via GitHub Sponsors.

---

## 5. The conversion funnel (the numbers behind the model)

Research benchmarks (2025–26): **freemium converts 2–5%** of free users to paid;
opt-in free trials convert ~9–18%, opt-out (card required) ~30–48%, but trials
draw fewer signups. For a broad-reach education tool, **freemium with the Preview
Meter as the upgrade trigger** is the right default — maximize the free top, take
2–5% to paid, sell the high-ticket tiers via outbound.

Illustrative — *not a forecast*, a model to fill in with real funnel data:

| Stage | Conservative | Base | Optimistic |
|---|---|---|---|
| Monthly free users (browser + desktop) | 2,000 | 10,000 | 50,000 |
| → Plus/Pro conversion @ 2–5% | 40 @ $5 | 300 @ ~$7 blended | 2,000 @ ~$8 |
| Consumer MRR | ~$200 | ~$2,100 | ~$16,000 |
| Edu/Institution deals / yr | 1 × $500 | 6 × $700 | 30 × $1,200 |
| Edu ARR | $500 | $4,200 | $36,000 |
| Sponsors/grants (annual) | $600 | $5,000 | $40,000+ |

The point isn't the totals — it's the **shape**: consumer subscriptions fund
the lights, education/institution licensing is the upside, and sponsorship
underwrites the free core that feeds all of it.

---

## 6. What ships now vs. what needs building

**Now (this PR — zero infrastructure):**
- `​.github/FUNDING.yml` → GitHub Sponsors live the moment Sponsors is enabled.
- **Pricing page** on the landing site + a "Support / Go Pro" CTA.
- **Go-to-market kit** with ready-to-post launch copy ([GO_TO_MARKET.md](GO_TO_MARKET.md)).
- **Validation kit** so you can price-test with real people ([VALIDATION_KIT.md](VALIDATION_KIT.md)).

**Next (needs a backend — scoped, not built):**
- Cloud render workers + the Preview Meter (the paid compute path).
- Accounts, save/share permalinks, Stripe billing.
- Teacher dashboard + rostering for the Classroom tier.

The honest sequencing: **prove demand with Sponsors + a waitlist + the
validation survey first**, then build the billing/compute backend only against
evidence. Don't build a SaaS for a willingness-to-pay you haven't measured.

---

## 7. Risks & how we de-risk

| Risk | Mitigation |
|---|---|
| It's MIT — anyone can fork the free core and self-host. | We don't sell the code; we sell **hosted compute, save/share, exports, curriculum, and the brand/plates.** Forks don't get those. (Same reason people pay for hosted Postgres.) |
| Niche topic = small TAM. | Broad tiering + the *visuals* widen it: generative-art buyers + classrooms + museums, not just origin-of-life nerds. |
| Education sales are slow. | Lead with self-serve consumer tiers for cash flow; treat edu/institution as high-ticket upside, not the engine. |
| The 30s wall annoys people. | It never touches free learning; only the expensive cloud/export action — and the threshold is A/B-tested, not assumed. |
| No backend yet. | Ship Sponsors + waitlist + validation *first*; build billing only on proven demand. |

---

## Sources

- [PhET Interactive Simulations](https://phet.colorado.edu/) — free, grant/donation funded.
- [Golly](https://golly.sourceforge.io/) — open-source CA reference tool.
- [Automata Ecosystem on Steam](https://store.steampowered.com/app/1966940/Automata_Ecosystem__Cellular_Automata_Simulation/) — paid CA sandbox.
- [Wolfram System Modeler](https://www.wolfram.com/system-modeler/) — institutional licensing.
- [Layer — generative-art display platform](https://www.wallpaper.com/tech/layer-generative-art-display) — subscription model.
- [SaaS freemium conversion benchmarks 2026 — First Page Sage](https://firstpagesage.com/seo-blog/saas-freemium-conversion-rates/)
- [SaaS free-trial conversion benchmarks — First Page Sage](https://firstpagesage.com/seo-blog/saas-free-trial-conversion-rate-benchmarks/)
- [How museums make money online — MuseumNext](https://www.museumnext.com/article/how-can-museums-make-money-online/)
