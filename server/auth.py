"""Clerk authentication — verify session JWTs against Clerk's JWKS.

We never see a password. The browser signs in with Clerk's JS and sends the
short-lived session JWT as ``Authorization: Bearer <token>``; here we verify its
RS256 signature against Clerk's published JWKS (no secret key required) and
return the claims. ``sub`` is the Clerk user id we key billing on.
"""

from __future__ import annotations

import hmac
import threading
from typing import Any

from server import config


class AuthError(Exception):
    def __init__(self, message: str, status: int = 401) -> None:
        super().__init__(message)
        self.status = status


def access_code_ok(presented: str | None) -> bool:
    """Constant-time check of the interim shared access code (see config).

    Returns False when no code is configured or none is presented, so the gate
    fails closed. This is a deliberately simple stopgap before the full
    Clerk/Stripe flow — the code is the bearer credential while it's enabled.
    """
    expected = config.settings.access_code
    if not expected or not presented:
        return False
    return hmac.compare_digest(str(presented), str(expected))


_lock = threading.Lock()
_jwks_client: Any = None
_jwks_url: str = ""


def _client() -> Any:
    global _jwks_client, _jwks_url
    url = config.settings.clerk_jwks_url
    if not url:
        raise AuthError("auth_not_configured", status=503)
    with _lock:
        if _jwks_client is None or _jwks_url != url:
            from jwt import PyJWKClient

            _jwks_client = PyJWKClient(url)
            _jwks_url = url
        return _jwks_client


def extract_bearer(authorization: str | None) -> str:
    if not authorization:
        raise AuthError("missing Authorization header")
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthError("Authorization must be 'Bearer <token>'")
    token = parts[1].strip()
    if not token:
        raise AuthError("empty bearer token")
    return token


def verify_token(token: str) -> dict[str, Any]:
    """Verify a Clerk session JWT and return its claims, or raise AuthError."""
    import jwt

    client = _client()
    try:
        signing_key = client.get_signing_key_from_jwt(token)
        kwargs: dict[str, Any] = {}
        if config.settings.clerk_issuer:
            kwargs["issuer"] = config.settings.clerk_issuer
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
            leeway=30,
            **kwargs,
        )
    except AuthError:
        raise
    except Exception as exc:  # jwt.* errors, JWKS fetch errors, etc.
        raise AuthError(f"invalid token: {exc}") from exc
    if not claims.get("sub"):
        raise AuthError("token missing subject")
    return claims
