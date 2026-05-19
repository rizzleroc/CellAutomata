from cellauto.engine import Engine
from cellauto.rules.wolfram1d import Wolfram1DRule


def test_rule_30_produces_known_pattern():
    """Rule 30 starting from a single center cell produces a deterministic pattern."""
    rule = Wolfram1DRule(rule_number=30)
    engine = Engine(width=7, height=4, rule=rule, seed=0)
    # Bottom row should be: 0 0 0 1 0 0 0 after initial_seed.
    assert engine.grid.cells[-1] == [False, False, False, True, False, False, False]
    engine.step()
    # Rule 30 expansion (single seed): generation 1 is 0 0 1 1 1 0 0
    assert engine.grid.cells[-1] == [False, False, True, True, True, False, False]


def test_rule_0_dies_immediately():
    rule = Wolfram1DRule(rule_number=0)
    engine = Engine(width=5, height=3, rule=rule, seed=0)
    engine.step()
    assert all(not c for c in engine.grid.cells[-1])
