from cellauto.engine import Engine
from cellauto.rules.conway import ConwaysLifeRule


def _empty_engine(size: int = 5) -> Engine:
    rule = ConwaysLifeRule(initial_density=0.0, wrap=False)
    return Engine(width=size, height=size, rule=rule, seed=0)


def test_blinker_oscillates_with_period_2():
    engine = _empty_engine(size=5)
    engine.grid.cells[2][1] = True
    engine.grid.cells[2][2] = True
    engine.grid.cells[2][3] = True
    engine.step()
    assert engine.grid.cells[1][2] is True
    assert engine.grid.cells[2][2] is True
    assert engine.grid.cells[3][2] is True
    assert engine.grid.cells[2][1] is False
    assert engine.grid.cells[2][3] is False
    engine.step()
    assert engine.grid.cells[2][1] is True
    assert engine.grid.cells[2][2] is True
    assert engine.grid.cells[2][3] is True


def test_still_life_block_is_stable():
    engine = _empty_engine(size=5)
    for y, x in ((1, 1), (1, 2), (2, 1), (2, 2)):
        engine.grid.cells[y][x] = True
    snapshot = [row[:] for row in engine.grid.cells]
    engine.step()
    assert engine.grid.cells == snapshot


def test_glider_translates_diagonally():
    """A glider is the 5-cell period-4 traveling pattern. After 4 steps it
    appears one cell SE of where it started (under unbounded space)."""
    engine = Engine(width=12, height=12, rule=ConwaysLifeRule(initial_density=0.0, wrap=False), seed=0)
    # Classic glider, pointing SE.
    coords = [(2, 3), (3, 4), (4, 2), (4, 3), (4, 4)]
    for y, x in coords:
        engine.grid.cells[y][x] = True
    for _ in range(4):
        engine.step()
    # After 4 steps, the same 5-cell shape should appear shifted +1, +1.
    expected = {(y + 1, x + 1) for y, x in coords}
    actual = {(y, x) for y in range(12) for x in range(12) if engine.grid.cells[y][x]}
    assert actual == expected


def test_wrap_affects_corner_neighbors():
    rule = ConwaysLifeRule(initial_density=0.0, wrap=True)
    engine = Engine(width=5, height=5, rule=rule, seed=0)
    # Three live cells at row 0 — they wrap around to give the (0,0) cell 3 neighbors via toroidal wrap.
    engine.grid.cells[0][0] = True
    engine.grid.cells[0][4] = True
    engine.grid.cells[4][0] = True
    # (0,0) sees (4,4), (4,0), (4,1), (0,4), (0,1), (1,4), (1,0), (1,1) by wrap.
    # Two of those are live ((4,0) and (0,4)). (0,0) itself is alive with 2 live neighbors → survives under B3/S23.
    engine.step()
    assert engine.grid.cells[0][0] is True
