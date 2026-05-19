from cellauto.engine import Engine
from cellauto.rules.conway import ConwaysLifeRule


def _empty_engine(size: int = 5) -> Engine:
    rule = ConwaysLifeRule(initial_density=0.0, wrap=False)
    engine = Engine(width=size, height=size, rule=rule, seed=0)
    return engine


def test_blinker_oscillates_with_period_2():
    """The 3-in-a-row 'blinker' is the simplest period-2 oscillator."""
    engine = _empty_engine(size=5)
    # Horizontal blinker at row 2.
    engine.grid.cells[2][1] = True
    engine.grid.cells[2][2] = True
    engine.grid.cells[2][3] = True
    engine.step()
    # After one step, should be vertical at column 2.
    assert engine.grid.cells[1][2] is True
    assert engine.grid.cells[2][2] is True
    assert engine.grid.cells[3][2] is True
    assert engine.grid.cells[2][1] is False
    assert engine.grid.cells[2][3] is False
    engine.step()
    # Back to horizontal.
    assert engine.grid.cells[2][1] is True
    assert engine.grid.cells[2][2] is True
    assert engine.grid.cells[2][3] is True


def test_still_life_block_is_stable():
    engine = _empty_engine(size=5)
    # 2x2 block.
    engine.grid.cells[1][1] = True
    engine.grid.cells[1][2] = True
    engine.grid.cells[2][1] = True
    engine.grid.cells[2][2] = True
    snapshot = [row[:] for row in engine.grid.cells]
    engine.step()
    assert engine.grid.cells == snapshot
