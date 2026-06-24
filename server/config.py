"""Environment-driven settings for the Pro app server.

Everything is optional: with no Clerk/Stripe variables set, the server still
boots and serves the free static site + ``/healthz``. The Pro endpoints report
``billing_not_configured`` until the operator provides the keys (see
``docs/PRD_WEB9_PRO.md`` §6). This is what makes the rollout safe — deploying
this image never breaks the existing live site.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(value: str | None) -> bool:
    return str(value or "").strip().lower() in ("1", "true", "yes", "on")


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    # Clerk (auth)
    clerk_publishable_key: str
    clerk_jwks_url: str
    clerk_issuer: str
    # Stripe (billing)
    stripe_secret_key: str
    stripe_price_id: str
    stripe_webhook_secret: str
    # App
    app_base_url: str
    pro_price_label: str
    # Resource bounds (tracks #42 / SEC-008)
    max_render_size: int
    max_render_grid: int
    max_render_steps: int
    max_render_work: int
    # Local-only escape hatch — NEVER set in production.
    dev_unlocked: bool

    def auth_configured(self) -> bool:
        return bool(self.clerk_jwks_url)

    def billing_configured(self) -> bool:
        return bool(self.stripe_secret_key and self.stripe_price_id and self.stripe_webhook_secret)


def load_settings() -> Settings:
    jwks = os.getenv("CLERK_JWKS_URL", "").strip()
    issuer = os.getenv("CLERK_ISSUER", "").strip()
    if not jwks and issuer:
        jwks = issuer.rstrip("/") + "/.well-known/jwks.json"
    return Settings(
        clerk_publishable_key=os.getenv("CLERK_PUBLISHABLE_KEY", "").strip(),
        clerk_jwks_url=jwks,
        clerk_issuer=issuer,
        stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", "").strip(),
        stripe_price_id=os.getenv("STRIPE_PRICE_ID", "").strip(),
        stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", "").strip(),
        app_base_url=os.getenv("APP_BASE_URL", "").strip().rstrip("/"),
        pro_price_label=os.getenv("PRO_PRICE_LABEL", "").strip(),
        max_render_size=_int("MAX_RENDER_SIZE", 4000),
        max_render_grid=_int("MAX_RENDER_GRID", 384),
        max_render_steps=_int("MAX_RENDER_STEPS", 1500),
        # ~grid²·steps ceiling so a single request can't pin a worker for minutes.
        max_render_work=_int("MAX_RENDER_WORK", 120_000_000),
        dev_unlocked=_bool(os.getenv("CELLAUTO_DEV_UNLOCKED")),
    )


# Loaded once at import. Tests may reassign ``config.settings`` after tweaking
# the environment; the dependency functions read it dynamically.
settings: Settings = load_settings()
