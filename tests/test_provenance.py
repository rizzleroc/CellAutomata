"""Provenance manifest — every snapshot / headless run is traceable (Phase A)."""

from __future__ import annotations

import datetime

from cellauto import __version__
from cellauto.engine import Engine
from cellauto.provenance import run_manifest
from cellauto.rules import REGISTRY
from cellauto.rules.wolfram1d import Wolfram1DRule


def test_run_manifest_shape_and_version():
    m = run_manifest()
    assert m["cellauto_version"] == __version__
    assert isinstance(m["python"], str) and m["python"]
    assert isinstance(m["platform"], str) and m["platform"]
    # generated_at is a parseable ISO-8601 timestamp
    datetime.datetime.fromisoformat(m["generated_at"])
    # git_sha is a short hash or None — never raises outside a checkout
    assert m["git_sha"] is None or isinstance(m["git_sha"], str)


def test_snapshot_embeds_manifest_and_still_round_trips(tmp_path):
    eng = Engine(width=9, height=5, rule=Wolfram1DRule(rule_number=30), seed=3)
    eng.step()
    snap = eng.to_dict()
    assert snap["manifest"]["cellauto_version"] == __version__
    # the extra provenance key must not break load (load ignores unknown keys)
    path = tmp_path / "snap.json"
    eng.save(path)
    loaded = Engine.load(path, REGISTRY)
    assert loaded.step_count == eng.step_count
    assert loaded.grid.cells[-1] == eng.grid.cells[-1]
