"""Stripe billing — checkout, webhook, and live entitlement lookup.

Entitlement = "this Clerk user has an active or trialing subscription on the Pro
price." We map a Clerk user to a Stripe customer via the customer's
``metadata.clerk_user_id`` and query Stripe live (cached ~60s). The webhook
invalidates the cache on subscription changes so upgrades/cancellations reflect
quickly. No database — see PRD §4.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from server import config

_CACHE_TTL = 60.0
_cache: dict[str, tuple[bool, float]] = {}
_cache_lock = threading.Lock()


class BillingError(Exception):
    def __init__(self, message: str, status: int = 503) -> None:
        super().__init__(message)
        self.status = status


def _stripe() -> Any:
    if not config.settings.billing_configured():
        raise BillingError("billing_not_configured", status=503)
    import stripe

    stripe.api_key = config.settings.stripe_secret_key
    return stripe


def _find_customers(stripe: Any, clerk_user_id: str) -> list:
    """Customers tagged with this Clerk user id. Prefers the Search API; falls
    back to a bounded list scan if search is unavailable."""
    query = f"metadata['clerk_user_id']:'{clerk_user_id}'"
    try:
        res = stripe.Customer.search(query=query, limit=20)
        return list(res.data)
    except Exception:
        out = []
        for cust in stripe.Customer.list(limit=100).auto_paging_iter():
            if (cust.get("metadata") or {}).get("clerk_user_id") == clerk_user_id:
                out.append(cust)
            if len(out) >= 20:
                break
        return out


def _get_or_create_customer(stripe: Any, clerk_user_id: str, email: str | None) -> Any:
    found = _find_customers(stripe, clerk_user_id)
    if found:
        return found[0]
    return stripe.Customer.create(email=email or None, metadata={"clerk_user_id": clerk_user_id})


def create_checkout_session(clerk_user_id: str, email: str | None, base_url: str) -> str:
    stripe = _stripe()
    customer = _get_or_create_customer(stripe, clerk_user_id, email)
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer.id,
        line_items=[{"price": config.settings.stripe_price_id, "quantity": 1}],
        success_url=f"{base_url}/web9/?checkout=success",
        cancel_url=f"{base_url}/web9/?checkout=cancel",
        client_reference_id=clerk_user_id,
        allow_promotion_codes=True,
    )
    if not session.url:
        raise BillingError("stripe did not return a checkout url", status=502)
    return session.url


def _query_entitled(stripe: Any, clerk_user_id: str) -> bool:
    price_id = config.settings.stripe_price_id
    for customer in _find_customers(stripe, clerk_user_id):
        subs = stripe.Subscription.list(customer=customer.id, status="all", limit=100)
        for sub in subs.auto_paging_iter():
            if sub.get("status") not in ("active", "trialing"):
                continue
            for item in sub["items"]["data"]:
                if item["price"]["id"] == price_id:
                    return True
    return False


def is_entitled(clerk_user_id: str) -> bool:
    now = time.time()
    with _cache_lock:
        cached = _cache.get(clerk_user_id)
        if cached and cached[1] > now:
            return cached[0]
    result = _query_entitled(_stripe(), clerk_user_id)
    with _cache_lock:
        _cache[clerk_user_id] = (result, now + _CACHE_TTL)
    return result


def invalidate(clerk_user_id: str) -> None:
    with _cache_lock:
        _cache.pop(clerk_user_id, None)


def handle_webhook(payload: bytes, sig_header: str) -> dict:
    stripe = _stripe()
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, config.settings.stripe_webhook_secret)
    except Exception as exc:
        raise BillingError(f"invalid signature: {exc}", status=400) from exc

    obj = event["data"]["object"]
    clerk_user_id = obj.get("client_reference_id")
    if not clerk_user_id and obj.get("customer"):
        try:
            cust = stripe.Customer.retrieve(obj["customer"])
            clerk_user_id = (cust.get("metadata") or {}).get("clerk_user_id")
        except Exception:
            clerk_user_id = None
    if clerk_user_id:
        invalidate(clerk_user_id)
    return {"received": True, "type": event.get("type")}
