from cellauto.engine import Engine
from cellauto.rules.wolfram1d import Wolfram1DRule


def test_rule_30_known_first_generation():
    engine = Engine(width=7, height=4, rule=Wolfram1DRule(rule_number=30), seed=0)
    assert engine.grid.cells[-1] == [False, False, False, True, False, False, False]
    engine.step()
    assert engine.grid.cells[-1] == [False, False, True, True, True, False, False]


def test_rule_0_kills_immediately():
    engine = Engine(width=5, height=3, rule=Wolfram1DRule(rule_number=0), seed=0)
    engine.step()
    assert all(not c for c in engine.grid.cells[-1])


def test_rule_90_sierpinski_first_steps():
    """Rule 90 produces the Sierpiński triangle from a single seed."""
    engine = Engine(width=9, height=5, rule=Wolfram1DRule(rule_number=90), seed=0)
    engine.step()
    # Single cell becomes two cells.
    assert engine.grid.cells[-1] == [False, False, False, True, False, True, False, False, False]
    engine.step()
    # Two cells → "1 0 1 0 0 0 1 0 1" pattern (the famous Sierpiński fractal step).
    assert engine.grid.cells[-1] == [False, False, True, False, False, False, True, False, False]


def test_history_scrolls_upward():
    """After each step, what was the bottom row should now be the row above."""
    engine = Engine(width=5, height=4, rule=Wolfram1DRule(rule_number=30), seed=0)
    bottom_before = list(engine.grid.cells[-1])
    engine.step()
    assert engine.grid.cells[-2] == bottom_before


def test_population_distinguishes_live_now_from_history():
    rule = Wolfram1DRule(rule_number=30)
    engine = Engine(width=9, height=5, rule=rule, seed=0)
    for _ in range(3):
        engine.step()
    pop = engine.population()
    assert set(pop) == {"live_now", "history_on", "history_off"}
    # live_now must be exactly the count of True in the bottom row.
    assert pop["live_now"] == sum(1 for c in engine.grid.cells[-1] if c)


def test_rule_110_known_evolution_from_single_seed():
    """Rule 110 — the Turing-complete elementary CA (Cook 2004) — from a single
    centre seed. Deterministic: the engine seed only feeds rule.rng, which the
    Wolfram step never reads. Width 9 keeps the left-marching triangle clear of
    the toroidal wrap for the first four generations.

    Truth table (L,C,R): 111->0 110->1 101->1 100->0 011->1 010->1 001->1 000->0.
    """
    engine = Engine(width=9, height=5, rule=Wolfram1DRule(rule_number=110), seed=0)
    o, x = False, True
    assert engine.grid.cells[-1] == [o, o, o, o, x, o, o, o, o]
    engine.step()
    assert engine.grid.cells[-1] == [o, o, o, x, x, o, o, o, o]
    engine.step()
    assert engine.grid.cells[-1] == [o, o, x, x, x, o, o, o, o]
    engine.step()
    assert engine.grid.cells[-1] == [o, x, x, o, x, o, o, o, o]
    engine.step()
    assert engine.grid.cells[-1] == [x, x, x, x, x, o, o, o, o]
