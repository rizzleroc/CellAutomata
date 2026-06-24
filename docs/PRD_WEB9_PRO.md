# PRD — web9 "Pro Studio": publication-quality SEM export

**Status:** proposed (v1, MVP). **Owner:** rizzleroc. **Branch:** `claude/inspiring-pasteur-Fy2Jv`.

This is the product + technical definition for the project's first **paid tier**.
It is also the **operator setup guide** — the Clerk / Stripe / Railway steps a
human must do once for the paywall to go live.

---

## 1. One-line vision

The free site lets anyone *explore* the labs interactively at screen resolution.
**Pro Studio** (`/web9/`) lets a signed-in, subscribed user *produce the artifact*:
a publication-quality **SEM micrograph PNG up to 4000×4000** of any stage, rendered
server-side by the **existing, tested Python SEM renderer**, with the stage's full
real knob set and regime picker.

The compute (the hi-res render) is what's paywalled — so the gate is meaningful and
the feature reuses proven code instead of reimplementing the renderer in the browser.

## 2. Why this feature

- **Adds value, removes nothing.** web7 / web8 / ontogeny stay 100% free — that's the
  signup funnel. Pro is a *new* capability (hi-res export), not a lock on existing content.
- **Advances the roadmap.** Directly serves standing requirement **#64** (growth plate
  / render up to 4000²) and **#65** (expose each stage's full real knob set + a regime
  picker). The desktop app already exports hi-res PNGs (`cellauto/hires.py`); this brings
  that capability to the web, gated.
- **Reuses tested code.** `cellauto.renderer_sem.SemRenderer.compose_at(rgb, size)` is
  explicitly tkinter-free and already covered by `tests/test_sem_renderer.py`. The server
  drives the same engine + renderer the desktop uses.

## 3. Scope

### In scope (MVP)
- A new gated client at `docs/web9/` ("Pro Studio").
- A Railway **FastAPI app server** that (a) serves the existing free static site unchanged,
  (b) gates a hi-res render endpoint behind Clerk auth + an active Stripe subscription,
  (c) creates Stripe Checkout sessions and consumes Stripe webhooks.
- Server-side hi-res SEM render of the **field-renderer stages** (Gray-Scott, vesicles,
  RAF, RNA world, homochirality, vent, coacervate, minerals, genetic code, LUCA) at up to
  4000², warm-sepia or cool-mono, with the full per-rule knob set and (where applicable)
  the regime/preset picker.

### Out of scope (future)
- Discrete-renderer stages (Stage 0 soup, Conway, Wolfram, protocell-selection) — they
  render via `render_cell`, not `render_rgb`; a separate path. (Tracked, not built.)
- Timelapse / film export (heavy: ffmpeg + headless GL).
- Save / share / gallery persistence (needs a DB + object store).
- Async render jobs + progress (MVP renders synchronously within the request).

## 4. Architecture (consolidated on Railway)

One Railway service, one image. The static `python -m http.server` is replaced by a
FastAPI app that **also** serves `docs/` so the free site is byte-for-byte unchanged.

```
Browser (web9)                         Railway: FastAPI (server/app.py)
──────────────                         ────────────────────────────────
GET /web9/  ───────────────────────▶   StaticFiles(docs/)            (public)
GET /api/public-config  ───────────▶   clerk publishable key, flags  (public)
GET /api/rules  ───────────────────▶   rule + param + preset catalog (public)
Clerk sign-in (Clerk JS, CDN)
GET /api/me/entitlement  (Bearer)  ▶   verify Clerk JWT → check Stripe sub
POST /api/checkout       (Bearer)  ▶   Stripe Checkout Session → {url}
                          ◀────────    302 to Stripe-hosted checkout
POST /api/stripe/webhook ◀─────────    Stripe → verify sig → invalidate cache
POST /api/render (Bearer, entitled)▶   engine.step×N → SemRenderer.compose_at → PNG
                          ◀────────    image/png (up to 4000²)
```

- **Auth = Clerk.** The browser uses Clerk's JS (loaded from Clerk's CDN with the
  publishable key) for sign-in/up. The server verifies the session **JWT** against Clerk's
  **JWKS** (no secret needed for verification). No passwords touch our code.
- **Billing = Stripe.** Checkout is Stripe-hosted (redirect). Entitlement = "this Clerk
  user has an active/trialing subscription on the Pro price." We map Clerk user → Stripe
  customer via the customer's `metadata.clerk_user_id`, and **query Stripe live** at request
  time (cached in-memory ~60s; the webhook invalidates the cache on subscription changes).
  No database in the MVP.
- **Render = existing Python.** `server/render.py` builds a `cellauto` rule from the
  validated request, runs the engine headless, takes `rule.render_rgb(state)`, and calls
  `SemRenderer(canvas=None, canvas_size=size).compose_at(rgb, size)`. Never imports
  `cellauto.app` (which pulls tkinter), so it stays headless — also closing the spirit of
  **REV-01**.

### Safe rollout (important)
The server boots **with no Clerk/Stripe config** and serves the free site + `/healthz`
normally. The Pro endpoints return `503 {"error":"billing_not_configured"}` until the
operator sets the env vars. So this branch can deploy without breaking the live site, and
Pro switches on the moment the keys are present.

## 5. API contract

| Method | Path | Auth | Returns |
|---|---|---|---|
| GET | `/healthz` | – | `{"status":"ok"}` (Railway healthcheck) |
| GET | `/api/public-config` | – | `{clerkPublishableKey, billingEnabled, priceLabel}` |
| GET | `/api/rules` | – | `[{name,label,renderer,presets[],params[{attr,label,lo,hi,step,integer}]}]` |
| GET | `/api/me/entitlement` | Bearer | `{signedIn, entitled, reason}` |
| POST | `/api/checkout` | Bearer | `{url}` (Stripe Checkout) |
| POST | `/api/stripe/webhook` | Stripe sig | `{"received":true}` |
| POST | `/api/render` | Bearer + entitled | `image/png` |
| GET | `/*` | – | static `docs/` |

**`POST /api/render` body** (all validated + clamped server-side):
```json
{
  "rule":  "abiogenesis-stage1-grayscott",
  "preset": "spots",
  "params": { "F": 0.037, "k": 0.06, "Du": 0.16, "Dv": 0.08 },
  "seed":   12345,
  "grid":   200,
  "steps":  600,
  "size":   2048,
  "palette":"warm-sepia"
}
```
Only `params` keys present in the rule's `PARAM_SPECS` are accepted; each is range-checked
against its spec and integer-coerced where required. `grid`/`steps`/`size` are hard-capped
(see §7). Unknown rule, non-field renderer, or out-of-range input → `400`.

## 6. Operator setup (do this once)

### 6.1 Clerk (auth)
1. Create a Clerk application at <https://dashboard.clerk.com>.
2. Copy the **Publishable key** (`pk_live_…` / `pk_test_…`) → env `CLERK_PUBLISHABLE_KEY`.
3. Copy the **JWKS URL** (Clerk → API Keys → "Show JWKS URL", e.g.
   `https://<your-domain>/.well-known/jwks.json`) → env `CLERK_JWKS_URL`.
   *(Alternatively set `CLERK_ISSUER` and we derive `…/.well-known/jwks.json`.)*
4. Add your Railway domain to Clerk's allowed origins.

### 6.2 Stripe (billing)
1. Create a **Product** "CellAuto Pro" with a recurring **Price** → copy the price id
   (`price_…`) → env `STRIPE_PRICE_ID`.
2. Copy the **Secret key** (`sk_live_…` / `sk_test_…`) → env `STRIPE_SECRET_KEY`.
3. Add a **webhook endpoint** → `https://<your-domain>/api/stripe/webhook`, subscribe to
   `checkout.session.completed`, `customer.subscription.updated`,
   `customer.subscription.deleted`. Copy the **signing secret** (`whsec_…`) →
   env `STRIPE_WEBHOOK_SECRET`.

### 6.3 Railway (env vars)
Set on the service (Variables tab). Railway injects `PORT` automatically.

| Var | Required | Purpose |
|---|---|---|
| `CLERK_PUBLISHABLE_KEY` | yes | frontend Clerk init |
| `CLERK_JWKS_URL` *(or `CLERK_ISSUER`)* | yes | verify session JWTs |
| `STRIPE_SECRET_KEY` | yes | checkout + entitlement lookup |
| `STRIPE_PRICE_ID` | yes | the Pro subscription price |
| `STRIPE_WEBHOOK_SECRET` | yes | verify webhook signatures |
| `APP_BASE_URL` | recommended | checkout success/cancel redirects (else derived from request) |
| `PRO_PRICE_LABEL` | optional | human label shown on the paywall (e.g. "$9/mo") |
| `MAX_RENDER_SIZE` | optional | hard cap, default `4000` |
| `MAX_RENDER_GRID` | optional | hard cap, default `384` |
| `MAX_RENDER_STEPS` | optional | hard cap, default `1500` |
| `CELLAUTO_DEV_UNLOCKED` | **never in prod** | local-only: treat caller as entitled without Clerk/Stripe |

### 6.4 Test-mode trial run (before the full security stack)
You can exercise the gate without real money or a finished production setup. Keys
go in Railway's **Variables** tab (or a local gitignored `.env`) — never in the
repo. A `.env.example` at the repo root lists every variable with placeholders.

- **Fastest — render only, no keys.** Set `CELLAUTO_DEV_UNLOCKED=1` and nothing
  else. `/api/render` unlocks and the studio opens — good for trialing the render
  itself, but it skips sign-in/checkout and grants Pro to **every** visitor, so
  don't leave it on a public deploy.
- **Recommended — the whole flow in test mode.** Use a Clerk **development**
  instance and Stripe **test mode**; the keys read as `pk_test_…` / `sk_test_…` /
  `whsec_…` and the code path is identical to live. Subscribe with Stripe's test
  card `4242 4242 4242 4242` (any future expiry, any CVC) and leave
  `CELLAUTO_DEV_UNLOCKED` unset. Flip the same vars to their `*_live_*` values
  when you go to production — no code change.

## 7. Security & resource bounds (tracks #42 / SEC-008)

`/api/render` is untrusted input and does real CPU/memory work, so:
- **Hard caps**, env-overridable but bounded: `size ≤ MAX_RENDER_SIZE (4000)`,
  `grid ≤ MAX_RENDER_GRID (384)`, `steps ≤ MAX_RENDER_STEPS (1500)`.
- **Strict validation**: rule must be a known field rule; every `params` key must exist in
  that rule's `PARAM_SPECS` and fall within `[lo,hi]`; ints coerced; everything else 400.
- **Auth before work**: entitlement is checked before any engine step runs.
- **Memory note**: a 4000² render peaks at a few hundred MB (RGBA overlay layers). Keep the
  Railway instance ≥ 1 GB, or lower `MAX_RENDER_SIZE`. Default UI export is 2048².
- Webhook signature is verified with `STRIPE_WEBHOOK_SECRET`; unverified posts are rejected.

## 8. Testing

- **Python** (`tests/test_server_render.py`, headless — no tkinter):
  catalog builds for field rules; render returns a valid PNG of the requested size; caps
  reject oversize `size`/`grid`/`steps`; unknown rule + out-of-range param rejected;
  `/api/render` returns 401 without a token and 200 PNG with auth+billing mocked.
- **JS** (`docs/web9/tests/smoke.mjs`, zero-dep): `studio.js` parses; `index.html` wires the
  module + the studio mount points + Catalytic-Silence tokens + reused web8 fonts.

## 9. Build plan / status

1. [ ] FastAPI server (`server/`): config, auth (Clerk JWKS), billing (Stripe), render, catalog, app.
2. [ ] Deploy: `[project.optional-dependencies] server`, Dockerfile → uvicorn, railway.toml healthcheck → `/healthz`.
3. [ ] web9 client: `index.html`, `studio.js`, `studio.css`.
4. [ ] Tests: Python server + web9 JS smoke.
5. [ ] Wire a tasteful Pro link into `docs/index.html`; update CLAUDE.md.

## 10. Open questions for the operator
- **Price point** — set in Stripe; surfaced via `PRO_PRICE_LABEL`. (Code is price-agnostic.)
- **Free trial?** — add a trial to the Stripe price; entitlement already counts `trialing`.
- **Per-user render quota / rate limit** — not in MVP; add when traffic warrants.
