"""Smoke tests for the Flask web wrapper.

Skipped silently when Flask isn't installed (it lives in the optional
``[web]`` extras), so the regular ``pytest`` run on a fresh env doesn't
hard-fail just because someone hasn't ``pip install -e .[web]``.
"""

from __future__ import annotations

import pytest

flask = pytest.importorskip("flask")


@pytest.fixture
def client():
    from cellauto.web.server import build_app

    app = build_app()
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c


def test_list_rules_includes_canonical(client):
    res = client.get("/api/rules")
    assert res.status_code == 200
    names = [r["name"] for r in res.get_json()["rules"]]
    for expected in ("conway", "wolfram1d", "abiogenesis-pipeline"):
        assert expected in names


def test_session_lifecycle_conway(client):
    res = client.post(
        "/api/sessions",
        json={"rule": "conway", "grid": 16, "seed": 7},
    )
    assert res.status_code == 200
    body = res.get_json()
    sid = body["session_id"]
    assert body["rule"] == "conway"
    assert body["grid"] == 16
    assert body["step_count"] == 0

    res = client.post(f"/api/sessions/{sid}/step", json={"n": 3})
    assert res.status_code == 200
    assert res.get_json()["step_count"] == 3

    res = client.get(f"/api/sessions/{sid}/frame.png")
    assert res.status_code == 200
    assert res.mimetype == "image/png"
    assert res.data[:8] == b"\x89PNG\r\n\x1a\n"

    res = client.delete(f"/api/sessions/{sid}")
    assert res.status_code == 204
    assert client.get(f"/api/sessions/{sid}").status_code == 404


def test_field_rule_renders_png(client):
    """Gray-Scott returns a continuous-field rgb array — different code path
    from the discrete Conway grid, worth exercising."""
    res = client.post(
        "/api/sessions",
        json={"rule": "abiogenesis-stage1-grayscott", "grid": 24, "seed": 1},
    )
    assert res.status_code == 200
    sid = res.get_json()["session_id"]

    assert client.post(f"/api/sessions/{sid}/step", json={"n": 2}).status_code == 200
    res = client.get(f"/api/sessions/{sid}/frame.png")
    assert res.status_code == 200
    assert res.mimetype == "image/png"


def test_reset_replaces_engine(client):
    sid = client.post("/api/sessions", json={"rule": "conway", "grid": 12, "seed": 1}).get_json()[
        "session_id"
    ]
    client.post(f"/api/sessions/{sid}/step", json={"n": 5})
    res = client.post(
        f"/api/sessions/{sid}/reset",
        json={"rule": "wolfram1d", "grid": 20, "seed": 2},
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["rule"] == "wolfram1d"
    assert body["grid"] == 20
    assert body["step_count"] == 0


def test_bad_rule_rejected(client):
    res = client.post("/api/sessions", json={"rule": "not-a-real-rule", "grid": 16})
    assert res.status_code == 400
    assert "unknown rule" in res.get_json()["error"]


def test_oversized_grid_rejected(client):
    res = client.post("/api/sessions", json={"rule": "conway", "grid": 9999})
    assert res.status_code == 400


def test_step_clamped(client):
    sid = client.post("/api/sessions", json={"rule": "conway", "grid": 12, "seed": 1}).get_json()[
        "session_id"
    ]
    res = client.post(f"/api/sessions/{sid}/step", json={"n": 10_000})
    assert res.status_code == 400


def test_index_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"<canvas" in res.data
