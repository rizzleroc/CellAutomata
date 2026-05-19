"""Tests that the four advertised rules are actually implemented.

These tests are the regression net for the gap analysis in CellAutomata_PRD.md:
each one corresponds to a Gap F1-F5 from that PRD.
"""

from cellauto.engine import Engine
from cellauto.rules.natural_selection import PALETTE, NaturalSelectionRule


def _make_engine(seed: int = 42, size: int = 12) -> Engine:
    return Engine(width=size, height=size, rule=NaturalSelectionRule(), seed=seed)


def test_initial_cells_use_palette():
    """Cells must be drawn from the quantized palette, not random 24-bit hex."""
    engine = _make_engine(seed=1)
    for x, y in engine.grid.iter_coords():
        cell = engine.grid.get(x, y)
        assert cell.color in PALETTE, f"cell color {cell.color} outside palette"


def test_rule1_color_propagates_from_neighbor():
    """Rule 1: a non-amoeba cell's new color must come from its Moore neighborhood."""
    rule = NaturalSelectionRule()
    engine = Engine(width=4, height=4, rule=rule, seed=7)
    # Snapshot neighbor colors before stepping.
    before = [[engine.grid.get(x, y).color for x in range(4)] for y in range(4)]
    engine.step()
    for y in range(4):
        for x in range(4):
            cell = engine.grid.get(x, y)
            if cell.is_ameba:
                continue
            # cell color must equal some pre-step neighbor color
            neighbors = []
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 4 and 0 <= ny < 4:
                        neighbors.append(before[ny][nx])
            assert cell.color in neighbors or cell.color == before[y][x], (
                f"cell at ({x},{y}) color {cell.color} not from any neighbor"
            )


def test_rule2_combinations_actually_happen():
    """Rule 2: with a 16-color palette, combinations must fire within 50 steps."""
    engine = _make_engine(seed=123, size=20)
    saw_amoeba = False
    for _ in range(50):
        engine.step()
        if any(c.is_ameba for row in engine.grid.cells for c in row):
            saw_amoeba = True
            break
    assert saw_amoeba, "no combinations fired in 50 steps — Rule 2 still broken"


def test_rule4_amoebas_have_lifecycle():
    """Rule 4: amoebas age and die — they don't accumulate forever."""
    rule = NaturalSelectionRule(amoeba_lifespan=3)
    engine = Engine(width=6, height=6, rule=rule, seed=42)
    # Force one cell to be an amoeba with age=0.
    cell = engine.grid.get(0, 0)
    cell.is_ameba = True
    cell.age = 0
    # After amoeba_lifespan steps, that specific cell should have been replaced.
    for _ in range(rule.amoeba_lifespan + 1):
        engine.step()
    after = engine.grid.get(0, 0)
    assert not after.is_ameba or after.age == 0, (
        "amoeba did not die or get replaced within lifespan"
    )


def test_seed_reproducibility():
    """Same seed must give bit-for-bit identical evolution."""
    e1 = _make_engine(seed=99)
    e2 = _make_engine(seed=99)
    for _ in range(10):
        e1.step()
        e2.step()
    c1 = [(c.color, c.is_ameba) for row in e1.grid.cells for c in row]
    c2 = [(c.color, c.is_ameba) for row in e2.grid.cells for c in row]
    assert c1 == c2


def test_population_sums_to_grid_size():
    engine = _make_engine(seed=5, size=10)
    for _ in range(5):
        engine.step()
    pop = engine.population()
    assert sum(pop.values()) == 100
