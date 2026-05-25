"""Engine tests — focus on save/load round-trip semantics.

The v2.0 sim had two failure modes covered here as regressions:
  - The RNG state was reset on load, so load-then-step diverged from a
    continuous run with the same seed.
  - Rule config (amoeba_lifespan, density, etc.) was discarded on load.
"""

from pathlib import Path

from cellauto.engine import Engine
from cellauto.rules import REGISTRY
from cellauto.rules.conway import ConwaysLifeRule
from cellauto.rules.natural_selection import NaturalSelectionRule


def _signature(grid) -> list:
    """A comparable summary of a NaturalSelection grid state."""
    return [(c.color, c.is_ameba, c.age) for row in grid.cells for c in row]


def test_save_load_resume_matches_continuous_run(tmp_path: Path):
    """Phase 2 §1.3: save at step N, load, step M more → must match a
    continuous run of (N+M) steps from the same seed."""
    SAVE_AT = 7
    EXTRA = 5

    e1 = Engine(width=8, height=8, rule=NaturalSelectionRule(), seed=42)
    for _ in range(SAVE_AT):
        e1.step()
    path = tmp_path / "snap.json"
    e1.save(path)
    e1_loaded = Engine.load(path, REGISTRY)
    for _ in range(EXTRA):
        e1_loaded.step()

    e2 = Engine(width=8, height=8, rule=NaturalSelectionRule(), seed=42)
    for _ in range(SAVE_AT + EXTRA):
        e2.step()

    assert _signature(e1_loaded.grid) == _signature(e2.grid)


def test_rule_config_round_trips(tmp_path: Path):
    """Phase 2 §2.2: rule parameters like amoeba_lifespan must be preserved
    across save/load, not silently reset to defaults."""
    rule = NaturalSelectionRule(amoeba_lifespan=7)
    engine = Engine(width=5, height=5, rule=rule, seed=1)
    engine.step()
    path = tmp_path / "snap.json"
    engine.save(path)
    loaded = Engine.load(path, REGISTRY)
    assert loaded.rule.amoeba_lifespan == 7


def test_conway_config_round_trips(tmp_path: Path):
    rule = ConwaysLifeRule(initial_density=0.7, wrap=False)
    engine = Engine(width=5, height=5, rule=rule, seed=1)
    engine.step()
    path = tmp_path / "snap.json"
    engine.save(path)
    loaded = Engine.load(path, REGISTRY)
    assert loaded.rule.initial_density == 0.7
    assert loaded.rule.wrap is False


def test_step_count_round_trips(tmp_path: Path):
    engine = Engine(width=5, height=5, rule=NaturalSelectionRule(), seed=1)
    for _ in range(10):
        engine.step()
    path = tmp_path / "snap.json"
    engine.save(path)
    loaded = Engine.load(path, REGISTRY)
    assert loaded.step_count == 10


def test_load_rejects_unknown_rule(tmp_path: Path):
    path = tmp_path / "bogus.json"
    path.write_text(
        '{"version":3,"rule":"does-not-exist","rule_config":{},'
        '"seed":1,"width":2,"height":2,"step_count":0,'
        '"rng_state":null,"state":{}}'
    )
    import pytest

    with pytest.raises(ValueError, match="unknown rule"):
        Engine.load(path, REGISTRY)


def test_snapshot_emits_format_v3(tmp_path: Path):
    """Confirm the writer is on the new format (P0-1)."""
    from cellauto.engine import SNAPSHOT_FORMAT_VERSION

    engine = Engine(width=4, height=4, rule=NaturalSelectionRule(), seed=1)
    d = engine.to_dict()
    assert d["version"] == SNAPSHOT_FORMAT_VERSION == 3
    # rng_state is a 3-element JSON-safe list, not a base64 pickle string.
    assert isinstance(d["rng_state"], list)
    assert len(d["rng_state"]) == 3
    version, internal, gauss_next = d["rng_state"]
    assert isinstance(version, int)
    assert isinstance(internal, list)
    assert all(isinstance(x, int) for x in internal)
    assert gauss_next is None or isinstance(gauss_next, (int, float))


def test_load_refuses_legacy_pickle_rng_state(tmp_path: Path, caplog):
    """A v2 snapshot with a base64-pickle rng_state must NOT be unpickled.
    The loader should warn and reseed from the stored seed instead.
    Demonstrating the security fix (P0-1)."""
    import base64
    import json
    import logging
    import pickle

    # Build a "v2" snapshot the old code would have happily pickle-loaded.
    rule = NaturalSelectionRule()
    engine = Engine(width=4, height=4, rule=rule, seed=99)
    engine.step()
    snap = engine.to_dict()
    # Overwrite with v2-style pickled rng_state (this is the attack surface).
    legacy_rng = base64.b64encode(pickle.dumps(rule.rng.getstate())).decode("ascii")
    snap["version"] = 2
    snap["rng_state"] = legacy_rng

    path = tmp_path / "v2.json"
    path.write_text(json.dumps(snap))

    with caplog.at_level(logging.WARNING):
        loaded = Engine.load(path, REGISTRY)
    # State/config/step count still load — only the rng stream offset is lost.
    assert loaded.rule.amoeba_lifespan == 25
    assert loaded.step_count == 1
    assert any("legacy v2 rng_state" in r.getMessage() for r in caplog.records)


def test_load_rejects_malformed_rng_state(tmp_path: Path):
    """A v3 snapshot with a malicious rng_state shape must be refused
    cleanly (no AttributeError leak, no setstate crash with surprise)."""
    import json

    import pytest

    snap = {
        "version": 3,
        "rule": "conway",
        "rule_config": {},
        "seed": 1,
        "width": 4,
        "height": 4,
        "step_count": 0,
        "rng_state": ["not", "a", "valid", "shape"],  # too long
        "state": {"width": 4, "height": 4, "cells": [[False] * 4 for _ in range(4)]},
    }
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(snap))
    with pytest.raises(ValueError, match="rng_state"):
        Engine.load(path, REGISTRY)
