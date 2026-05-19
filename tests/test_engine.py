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
    path.write_text('{"version":2,"rule":"does-not-exist","rule_config":{},'
                    '"seed":1,"width":2,"height":2,"step_count":0,'
                    '"rng_state":null,"state":{}}')
    import pytest
    with pytest.raises(ValueError, match="unknown rule"):
        Engine.load(path, REGISTRY)
