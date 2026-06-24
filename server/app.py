"""FastAPI application — serves the free static site and gates Pro rendering.

Route order matters: the API routes are declared first, then ``docs/`` is
mounted at ``/`` last so it catches everything else (the free site, web9, etc.).
The server boots fine with no Clerk/Stripe config — Pro endpoints simply report
``billing_not_configured`` until the operator sets the env vars (PRD §4).
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from server import auth, billing, catalog, config, render

log = logging.getLogger("cellauto.server")

DOCS_DIR = Path(os.getenv("DOCS_DIR", str(Path(__file__).resolve().parent.parent / "docs")))

_DEV_USER = {"sub": "dev-user", "email": "dev@local", "_dev": True}


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    s = config.settings
    log.info(
        "cellauto server up — auth_configured=%s billing_configured=%s dev_unlocked=%s docs=%s",
        s.auth_configured(),
        s.billing_configured(),
        s.dev_unlocked,
        DOCS_DIR,
    )
    yield


app = FastAPI(title="CellAuto Pro", docs_url=None, redoc_url=None, lifespan=_lifespan)


# ── helpers ──────────────────────────────────────────────────────────────────


def _claims_or_none(request: Request) -> dict | None:
    authz = request.headers.get("authorization")
    if not authz:
        return None
    try:
        return auth.verify_token(auth.extract_bearer(authz))
    except auth.AuthError:
        return None


def _require_user(request: Request) -> dict:
    authz = request.headers.get("authorization")
    if authz:
        try:
            return auth.verify_token(auth.extract_bearer(authz))
        except auth.AuthError as exc:
            if config.settings.dev_unlocked:
                return dict(_DEV_USER)
            raise HTTPException(status_code=exc.status, detail=str(exc)) from exc
    if config.settings.dev_unlocked:
        return dict(_DEV_USER)
    raise HTTPException(status_code=401, detail="authentication required")


def _require_entitled(user: dict) -> None:
    s = config.settings
    if s.dev_unlocked:
        return
    if not s.billing_configured():
        raise HTTPException(status_code=503, detail="billing_not_configured")
    try:
        if not billing.is_entitled(user["sub"]):
            raise HTTPException(status_code=402, detail="subscription_required")
    except billing.BillingError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc


def _base_url(request: Request) -> str:
    if config.settings.app_base_url:
        return config.settings.app_base_url
    host = request.headers.get("host", "")
    return f"{request.url.scheme}://{host}"


# ── public endpoints ─────────────────────────────────────────────────────────


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/api/public-config")
def public_config() -> dict:
    s = config.settings
    return {
        "clerkPublishableKey": s.clerk_publishable_key,
        "authConfigured": s.auth_configured(),
        "billingConfigured": s.billing_configured(),
        "billingEnabled": s.billing_configured() or s.dev_unlocked,
        "devUnlocked": s.dev_unlocked,
        "priceLabel": s.pro_price_label,
        "limits": {
            "maxSize": s.max_render_size,
            "maxGrid": s.max_render_grid,
            "maxSteps": s.max_render_steps,
        },
    }


@app.get("/api/rules")
def rules() -> list[dict]:
    return catalog.catalog_payload()


@app.get("/api/me/entitlement")
def me_entitlement(request: Request) -> dict:
    s = config.settings
    if s.dev_unlocked:
        return {"signedIn": True, "entitled": True, "reason": "dev_unlocked"}
    user = _claims_or_none(request)
    if user is None:
        return {"signedIn": False, "entitled": False, "reason": "not_signed_in"}
    if not s.billing_configured():
        return {"signedIn": True, "entitled": False, "reason": "billing_not_configured"}
    try:
        entitled = billing.is_entitled(user["sub"])
    except billing.BillingError as exc:
        return {"signedIn": True, "entitled": False, "reason": str(exc)}
    return {"signedIn": True, "entitled": entitled, "reason": "ok" if entitled else "no_subscription"}


# ── billing endpoints ────────────────────────────────────────────────────────


@app.post("/api/checkout")
def checkout(request: Request) -> dict:
    if not config.settings.billing_configured():
        raise HTTPException(status_code=503, detail="billing_not_configured")
    user = _require_user(request)
    try:
        url = billing.create_checkout_session(user["sub"], user.get("email"), _base_url(request))
    except billing.BillingError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc
    return {"url": url}


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request) -> dict:
    if not config.settings.billing_configured():
        raise HTTPException(status_code=503, detail="billing_not_configured")
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        return await run_in_threadpool(billing.handle_webhook, payload, sig)
    except billing.BillingError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc


# ── the paywalled compute ────────────────────────────────────────────────────


@app.post("/api/render")
async def api_render(request: Request) -> Response:
    user = await run_in_threadpool(_require_user, request)
    await run_in_threadpool(_require_entitled, user)
    try:
        body: Any = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid JSON body") from exc
    try:
        png = await run_in_threadpool(render.render_png, body)
    except render.RenderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-store"})


# ── static site (mounted last so it catches everything else) ─────────────────

if DOCS_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(DOCS_DIR), html=True), name="site")
else:  # pragma: no cover - only in a misconfigured container
    log.warning("docs dir %s not found; static site not mounted", DOCS_DIR)
