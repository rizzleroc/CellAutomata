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


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "ok"
    assert body["rules"] > 0


# --- Parameter sliders --------------------------------------------------------


def test_rule_params_metadata(client):
    res = client.get("/api/rules/abiogenesis-stage1-grayscott/params")
    assert res.status_code == 200
    body = res.get_json()
    attrs = {p["attr"] for p in body["params"]}
    assert attrs == {"F", "k", "Du", "Dv"}
    # Gray-Scott also exposes the Pearson presets.
    assert "spots" in body["presets"]


def test_session_params_live(client):
    sid = client.post(
        "/api/sessions",
        json={"rule": "abiogenesis-stage1-grayscott", "grid": 24, "seed": 1},
    ).get_json()["session_id"]

    # Initial values come back populated.
    res = client.get(f"/api/sessions/{sid}/params")
    body = res.get_json()
    vals = {p["attr"]: p["value"] for p in body["params"]}
    assert "F" in vals and "k" in vals

    # Live parameter change is applied and clamped within spec range.
    res = client.post(f"/api/sessions/{sid}/params", json={"F": 0.04, "k": 0.062})
    assert res.status_code == 200
    assert set(res.get_json()["applied"]) == {"F", "k"}

    res = client.get(f"/api/sessions/{sid}/params")
    vals = {p["attr"]: p["value"] for p in res.get_json()["params"]}
    assert abs(vals["F"] - 0.04) < 1e-6
    assert abs(vals["k"] - 0.062) < 1e-6


def test_reinit_param_rebuilds_state(client):
    """RAF's n_species is a structural param — changing it should reinit
    the state without raising and the engine should keep stepping."""
    sid = client.post(
        "/api/sessions",
        json={"rule": "abiogenesis-stage2-raf", "grid": 20, "seed": 5},
    ).get_json()["session_id"]
    client.post(f"/api/sessions/{sid}/step", json={"n": 3})
    res = client.post(f"/api/sessions/{sid}/params", json={"n_species": 8})
    assert res.status_code == 200
    body = res.get_json()
    assert body["reinit"] is True
    # The step counter must go back to 0 — without this the UI shows e.g.
    # step=3 next to a freshly-initialised canvas, which (especially on
    # Wolfram 1D's accumulated-history visualisation) reads as "broken".
    assert body["step_count"] == 0
    # And stepping still works after the reinit.
    assert client.post(f"/api/sessions/{sid}/step", json={"n": 1}).status_code == 200


def test_reinit_wolfram_resets_step_count(client):
    """Specifically lock in the Wolfram 1D case the playtest caught: the
    canvas is an accumulated history, so a reinit MUST zero step_count or
    the UI shows a stale number beside a blank canvas."""
    sid = client.post(
        "/api/sessions",
        json={"rule": "wolfram1d", "grid": 32, "seed": 1},
    ).get_json()["session_id"]
    client.post(f"/api/sessions/{sid}/step", json={"n": 5})
    assert client.get(f"/api/sessions/{sid}").get_json()["step_count"] == 5
    res = client.post(f"/api/sessions/{sid}/params", json={"rule_number": 110})
    assert res.status_code == 200
    assert res.get_json()["step_count"] == 0


def test_preset_applies_gray_scott(client):
    sid = client.post(
        "/api/sessions",
        json={"rule": "abiogenesis-stage1-grayscott", "grid": 24, "seed": 1},
    ).get_json()["session_id"]
    res = client.post(f"/api/sessions/{sid}/preset", json={"name": "mitosis"})
    assert res.status_code == 200
    # Mitosis preset is F=0.0367, k=0.0649 — check the live value matches.
    params = client.get(f"/api/sessions/{sid}/params").get_json()["params"]
    vals = {p["attr"]: p["value"] for p in params}
    assert abs(vals["F"] - 0.0367) < 1e-6
    assert abs(vals["k"] - 0.0649) < 1e-6


def test_unknown_preset_rejected(client):
    sid = client.post(
        "/api/sessions",
        json={"rule": "abiogenesis-stage1-grayscott", "grid": 16, "seed": 1},
    ).get_json()["session_id"]
    res = client.post(f"/api/sessions/{sid}/preset", json={"name": "not-a-preset"})
    assert res.status_code == 400


# --- Pipeline stage controls -------------------------------------------------


def test_pipeline_stage_info(client):
    sid = client.post(
        "/api/sessions",
        json={"rule": "abiogenesis-pipeline", "grid": 24, "seed": 1},
    ).get_json()["session_id"]
    body = client.get(f"/api/sessions/{sid}").get_json()
    info = body["stage_info"]
    assert info["index"] == 0
    assert info["current_stage"] == 0
    assert info["total_stages"] >= 5
    assert "title" in info and "citation" in info


def test_promote_and_jump_stage(client):
    sid = client.post(
        "/api/sessions",
        json={"rule": "abiogenesis-pipeline", "grid": 20, "seed": 1},
    ).get_json()["session_id"]
    res = client.post(f"/api/sessions/{sid}/promote")
    assert res.status_code == 200
    assert res.get_json()["stage_info"]["current_stage"] == 1

    res = client.post(f"/api/sessions/{sid}/stage", json={"stage": 3})
    assert res.status_code == 200
    assert res.get_json()["stage_info"]["current_stage"] == 3


def test_auto_promote_toggle(client):
    sid = client.post(
        "/api/sessions",
        json={"rule": "abiogenesis-pipeline", "grid": 20, "seed": 1},
    ).get_json()["session_id"]
    res = client.post(f"/api/sessions/{sid}/auto_promote", json={"enabled": False, "duration": 30})
    assert res.status_code == 200
    info = res.get_json()["stage_info"]
    assert info["auto_promote"] is False
    assert info["stage_duration"] == 30


def test_promote_on_non_pipeline_rejected(client):
    sid = client.post("/api/sessions", json={"rule": "conway", "grid": 16, "seed": 1}).get_json()[
        "session_id"
    ]
    res = client.post(f"/api/sessions/{sid}/promote")
    assert res.status_code == 400


# --- Snapshot save / load ----------------------------------------------------


def test_snapshot_download_and_load(client):
    sid = client.post("/api/sessions", json={"rule": "conway", "grid": 16, "seed": 99}).get_json()[
        "session_id"
    ]
    client.post(f"/api/sessions/{sid}/step", json={"n": 4})

    res = client.get(f"/api/sessions/{sid}/snapshot.json")
    assert res.status_code == 200
    assert res.mimetype == "application/json"
    assert "attachment" in res.headers["Content-Disposition"]
    snapshot = res.get_json()
    assert snapshot["step_count"] == 4

    # Reset to a fresh state, then load — step count should jump back to 4.
    client.post(f"/api/sessions/{sid}/reset", json={"rule": "conway", "grid": 16, "seed": 99})
    assert client.get(f"/api/sessions/{sid}").get_json()["step_count"] == 0

    res = client.post(f"/api/sessions/{sid}/load", json=snapshot)
    assert res.status_code == 200
    assert res.get_json()["step_count"] == 4


def test_bad_snapshot_rejected(client):
    sid = client.post("/api/sessions", json={"rule": "conway", "grid": 12, "seed": 1}).get_json()[
        "session_id"
    ]
    res = client.post(f"/api/sessions/{sid}/load", json={"junk": True})
    assert res.status_code == 400


# --- PNG download + GIF export ------------------------------------------------


def test_frame_download_attachment(client):
    sid = client.post("/api/sessions", json={"rule": "conway", "grid": 16, "seed": 1}).get_json()[
        "session_id"
    ]
    res = client.get(f"/api/sessions/{sid}/frame.png?download=1")
    assert res.status_code == 200
    assert "attachment" in res.headers["Content-Disposition"]


def test_gif_export(client):
    sid = client.post(
        "/api/sessions",
        json={"rule": "abiogenesis-stage1-grayscott", "grid": 20, "seed": 1},
    ).get_json()["session_id"]
    res = client.post(
        f"/api/sessions/{sid}/gif",
        json={"steps": 6, "fps": 8, "canvas": 120},
    )
    assert res.status_code == 200
    assert res.mimetype == "image/gif"
    assert res.data[:6] in (b"GIF87a", b"GIF89a")


def test_gif_steps_clamped(client):
    sid = client.post("/api/sessions", json={"rule": "conway", "grid": 16, "seed": 1}).get_json()[
        "session_id"
    ]
    res = client.post(f"/api/sessions/{sid}/gif", json={"steps": 10_000, "fps": 8, "canvas": 200})
    assert res.status_code == 400
