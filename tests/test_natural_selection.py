"""Tests for the original four rules — implemented honestly in v3.0.

Each test corresponds to a gap from CellAutomata_PRD.md (the original) and/or
PHASE2_BRUTAL.md (the self-audit). F3 in particular was claimed-fixed in v2.0
but the regression test is new in v3.0.
"""
from cellauto.engine import Engine
from cellauto.rules.natural_selection import PALETTE, NaturalSelectionRule


def _make_engine(seed: int = 42, size: int = 12) -> Engine:
    return Engine(width=size, height=size, rule=NaturalSelectionRule(), seed=seed)


def test_initial_cells_use_palette():
    engine = _make_engine(seed=1)
    for x, y in engine.grid.iter_coords():
        assert engine.grid.get(x, y).color in PALETTE


def test_rule1_color_propagates_from_neighbor():
    rule = NaturalSelectionRule()
    engine = Engine(width=4, height=4, rule=rule, seed=7)
    before = [[engine.grid.get(x, y).color for x in range(4)] for y in range(4)]
    engine.step()
    for y in range(4):
        for x in range(4):
            cell = engine.grid.get(x, y)
            if cell.is_ameba:
                continue
            neighbors = []
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if (dx, dy) == (0, 0):
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 4 and 0 <= ny < 4:
                        neighbors.append(before[ny][nx])
            assert cell.color in neighbors or cell.color == before[y][x], \
                f"cell ({x},{y}) color {cell.color} not from neighbor"


def test_rule2_combinations_fire_within_50_steps():
    engine = _make_engine(seed=123, size=20)
    for _ in range(50):
        engine.step()
        if any(c.is_ameba for row in engine.grid.cells for c in row):
            return
    raise AssertionError("no combinations fired in 50 steps — Rule 2 broken")


def test_rule3_settled_cells_cannot_combine():
    """F3 has TEETH now. A non-amoeba cell that did NOT change color this step
    must have is_new=False; a settled cell adjacent to another settled cell of
    the SAME color must NOT combine."""
    rule = NaturalSelectionRule()
    engine = Engine(width=5, height=5, rule=rule, seed=1)

    # Force all cells to one color so neighbor propagation can't change anything.
    for cell in (c for row in engine.grid.cells for c in row):
        cell.color = PALETTE[0]
        cell.is_new = False
        cell.is_ameba = False

    engine.step()
    # After the step: nobody's color actually shifted (every neighbor was already
    # PALETTE[0]). With Rule 3 working, is_new should be False for everyone.
    # The settled-cells-can't-combine clause forbids combinations.
    amoebas = sum(1 for row in engine.grid.cells for c in row if c.is_ameba)
    assert amoebas == 0, f"settled same-color cells must not combine, got {amoebas} amoebas"
    all_settled = all(not c.is_new and not c.is_ameba
                      for row in engine.grid.cells for c in row)
    assert all_settled, "all-same-color step should leave every cell settled"


def test_rule3_settled_population_is_reachable():
    """Phase 2 §2.1: v2.0 made settled=0 mathematically guaranteed. v3.0 must
    reach settled>0 within a small number of steps from a random seed."""
    engine = _make_engine(seed=11, size=15)
    saw_settled = False
    for _ in range(30):
        engine.step()
        if engine.population()["settled"] > 0:
            saw_settled = True
            break
    assert saw_settled, "settled population should be reachable (v2.0 always-zero bug)"


def test_rule4_amoebas_die_after_lifespan():
    rule = NaturalSelectionRule(amoeba_lifespan=3)
    engine = Engine(width=6, height=6, rule=rule, seed=42)
    cell = engine.grid.get(0, 0)
    cell.is_ameba = True
    cell.age = 0
    for _ in range(rule.amoeba_lifespan + 1):
        engine.step()
    after = engine.grid.get(0, 0)
    # After lifespan+1 steps the original amoeba must have been replaced.
    # The replacement is either a fresh cell (not amoeba) OR a new amoeba that
    # happens to have formed at (0,0) and therefore has age=0.
    assert (not after.is_ameba) or (after.age == 0)


def test_seed_reproducibility():
    e1 = _make_engine(seed=99)
    e2 = _make_engine(seed=99)
    for _ in range(10):
        e1.step()
        e2.step()
    s1 = [(c.color, c.is_ameba) for row in e1.grid.cells for c in row]
    s2 = [(c.color, c.is_ameba) for row in e2.grid.cells for c in row]
    assert s1 == s2


def test_population_sums_to_grid_size():
    engine = _make_engine(seed=5, size=10)
    for _ in range(5):
        engine.step()
    assert sum(engine.population().values()) == 100


def test_palette_of_size_1_does_not_crash():
    """Phase 2 §2.11: _distinct_palette_color used to crash on a 1-element palette."""
    rule = NaturalSelectionRule(palette=("#ff0000",))
    engine = Engine(width=5, height=5, rule=rule, seed=1)
    for _ in range(10):
        engine.step()  # must not raise
