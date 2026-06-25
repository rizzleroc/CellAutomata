"""Headless tests for the Pro app server (server/).

These exercise the render core and the FastAPI gate without a browser, a real
Clerk instance, or Stripe — and crucially without tkinter (the render path uses
``SemRenderer.compose_at``, not the Tk canvas). If the optional server deps
aren't installed the whole module skips; CI installs ``.[dev]`` so it runs.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("jwt")
pytest.importorskip("stripe")

from fastapi.testclient import TestClient  # noqa: E402

from server import catalog, config  # noqa: E402
from server import render as render_mod  # noqa: E402
from server.app import app  # noqa: E402

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

_AUTH_VARS = (
    "CLERK_JWKS_URL",
    "CLERK_ISSUER",
    "STRIPE_SECRET_KEY",
    "STRIPE_PRICE_ID",
    "STRIPE_WEBHOOK_SECRET",
)


@pytest.fixture
def locked(monkeypatch):
    for key in ("CELLAUTO_DEV_UNLOCKED", "CELLAUTO_ACCESS_CODE", *_AUTH_VARS):
        monkeypatch.delenv(key, raising=False)
    config.settings = config.load_settings()
    yield
    config.settings = config.load_settings()


@pytest.fixture
def dev_unlocked(monkeypatch):
    for key in ("CELLAUTO_ACCESS_CODE", *_AUTH_VARS):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("CELLAUTO_DEV_UNLOCKED", "1")
    config.settings = config.load_settings()
    yield
    config.settings = config.load_settings()


@pytest.fixture
def access_code(monkeypatch):
    """Interim shared-code mode: a code is set, no Clerk/Stripe, no dev-unlock."""
    for key in ("CELLAUTO_DEV_UNLOCKED", *_AUTH_VARS):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("CELLAUTO_ACCESS_CODE", "trial-s3cret")
    config.settings = config.load_settings()
    yield "trial-s3cret"
    config.settings = config.load_settings()


@pytest.fixture
def client():
    return TestClient(app)


# ── catalog (#65 — full knob set + regime picker for the field stages) ────────


def test_catalog_only_field_rules():
    payload = catalog.catalog_payload()
    assert payload, "catalog should not be empty"
    assert all(entry["renderer"] == "field" for entry in payload)
    names = {entry["name"] for entry in payload}
    assert "abiogenesis-stage1-grayscott" in names
    # discrete-renderer rules and the meta pipelines are excluded
    assert "conway" not in names
    assert "wolfram1d" not in names
    assert not any(n.startswith("abiogenesis-pipeline") for n in names)
    grayscott = next(e for e in payload if e["name"] == "abiogenesis-stage1-grayscott")
    assert grayscott["presets"], "grayscott must expose its regime picker"
    assert {p["attr"] for p in grayscott["params"]} >= {"F", "k", "Du", "Dv"}


# ── render core ──────────────────────────────────────────────────────────────


def test_render_returns_valid_png():
    png = render_mod.render_png(
        {
            "rule": "abiogenesis-stage1-grayscott",
            "preset": "spots",
            "seed": 1,
            "grid": 48,
            "steps": 20,
            "size": 192,
            "params": {"F": 0.037, "k": 0.06},
        }
    )
    assert png[:8] == PNG_MAGIC
    assert len(png) > 1000


def test_render_size_is_honoured():
    from io import BytesIO

    from PIL import Image

    png = render_mod.render_png(
        {"rule": "abiogenesis-coacervate", "seed": 2, "grid": 48, "steps": 15, "size": 160}
    )
    with Image.open(BytesIO(png)) as img:
        assert img.size == (160, 160)


@pytest.mark.parametrize(
    "body",
    [
        {"rule": "conway", "grid": 48, "steps": 5, "size": 128},  # discrete renderer
        {"rule": "nope", "grid": 48, "steps": 5, "size": 128},  # unknown rule
        {"rule": "abiogenesis-stage1-grayscott", "grid": 48, "steps": 5, "size": 99999},  # oversize
        {"rule": "abiogenesis-stage1-grayscott", "grid": 99999, "steps": 5, "size": 128},  # oversize grid
        {"rule": "abiogenesis-stage1-grayscott", "grid": 300, "steps": 99999, "size": 128},  # steps cap
        {"rule": "abiogenesis-stage1-grayscott", "grid": 48, "steps": 5, "size": 128, "params": {"F": 99}},
        {"rule": "abiogenesis-stage1-grayscott", "grid": 48, "steps": 5, "size": 128, "params": {"x": 1}},
        {"rule": "abiogenesis-stage1-grayscott", "grid": 48, "steps": 5, "size": 128, "preset": "bogus"},
        {"rule": "abiogenesis-stage1-grayscott", "grid": 48, "steps": 5, "size": 128, "palette": "rainbow"},
    ],
)
def test_render_rejects_bad_input(body):
    with pytest.raises(render_mod.RenderError):
        render_mod.render_png(body)


# ── HTTP surface (dev-unlocked: no Clerk/Stripe needed) ──────────────────────


def test_http_dev_flow(dev_unlocked, client):
    assert client.get("/healthz").json() == {"status": "ok"}

    cfg = client.get("/api/public-config").json()
    assert cfg["devUnlocked"] is True
    assert cfg["billingConfigured"] is False
    assert cfg["limits"]["maxSize"] >= 1024

    rules = client.get("/api/rules").json()
    assert any(r["name"] == "abiogenesis-stage1-grayscott" for r in rules)

    assert client.get("/api/me/entitlement").json()["entitled"] is True

    good = client.post(
        "/api/render",
        json={
            "rule": "abiogenesis-stage1-grayscott",
            "preset": "spots",
            "seed": 1,
            "grid": 48,
            "steps": 20,
            "size": 128,
        },
    )
    assert good.status_code == 200
    assert good.headers["content-type"] == "image/png"
    assert good.content[:8] == PNG_MAGIC

    bad = client.post("/api/render", json={"rule": "conway", "grid": 48, "steps": 5, "size": 128})
    assert bad.status_code == 400


def test_http_static_site_served(dev_unlocked, client):
    root = client.get("/")
    assert root.status_code == 200
    assert "<html" in root.text.lower()


# ── HTTP surface (locked: gate must refuse) ──────────────────────────────────


def test_http_locked_gate(locked, client):
    no_auth = client.post(
        "/api/render",
        json={"rule": "abiogenesis-stage1-grayscott", "grid": 48, "steps": 5, "size": 128},
    )
    assert no_auth.status_code == 401

    assert client.post("/api/checkout").status_code == 503
    assert client.post("/api/stripe/webhook", content=b"{}").status_code == 503
    assert client.get("/api/me/entitlement").json()["signedIn"] is False
    # No access code configured → the interim verify endpoint is absent (404).
    assert client.post("/api/access/verify", headers={"X-Access-Code": "x"}).status_code == 404


# ── HTTP surface (interim shared access code) ────────────────────────────────


def test_http_access_code_flow(access_code, client):
    code = access_code

    cfg = client.get("/api/public-config").json()
    assert cfg["accessCodeEnabled"] is True
    assert cfg["billingConfigured"] is False
    assert cfg["devUnlocked"] is False

    # verify endpoint: right code 200, wrong/missing 401
    assert client.post("/api/access/verify", headers={"X-Access-Code": code}).status_code == 200
    assert client.post("/api/access/verify", headers={"X-Access-Code": "nope"}).status_code == 401
    assert client.post("/api/access/verify").status_code == 401

    # entitlement reflects the code
    ent = client.get("/api/me/entitlement", headers={"X-Access-Code": code}).json()
    assert ent["entitled"] is True and ent["reason"] == "access_code"
    assert client.get("/api/me/entitlement").json()["entitled"] is False

    body = {
        "rule": "abiogenesis-stage1-grayscott",
        "preset": "spots",
        "seed": 1,
        "grid": 48,
        "steps": 20,
        "size": 128,
    }
    # render is gated by the code: none/wrong → 401, right → 200 PNG
    assert client.post("/api/render", json=body).status_code == 401
    assert client.post("/api/render", headers={"X-Access-Code": "wrong"}, json=body).status_code == 401
    good = client.post("/api/render", headers={"X-Access-Code": code}, json=body)
    assert good.status_code == 200
    assert good.headers["content-type"] == "image/png"
    assert good.content[:8] == PNG_MAGIC

    # a valid code still can't bypass input validation
    bad = client.post(
        "/api/render",
        headers={"X-Access-Code": code},
        json={"rule": "conway", "grid": 48, "steps": 5, "size": 128},
    )
    assert bad.status_code == 400
