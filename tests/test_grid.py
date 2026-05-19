from cellauto.grid import Grid


def test_filled_uses_factory():
    grid = Grid.filled(3, 2, lambda x, y: (x, y))
    assert grid.width == 3 and grid.height == 2
    assert grid.get(0, 0) == (0, 0)
    assert grid.get(2, 1) == (2, 1)


def test_in_bounds():
    grid = Grid.filled(4, 4, lambda x, y: 0)
    assert grid.in_bounds(0, 0)
    assert grid.in_bounds(3, 3)
    assert not grid.in_bounds(-1, 0)
    assert not grid.in_bounds(4, 0)


def test_neighbors_moore_corner_no_wrap():
    grid = Grid.filled(3, 3, lambda x, y: f"{x},{y}")
    neighbors = list(grid.neighbors_moore(0, 0, wrap=False))
    # A corner cell has 3 neighbors.
    assert len(neighbors) == 3
    assert "1,0" in neighbors and "0,1" in neighbors and "1,1" in neighbors


def test_neighbors_moore_wrap():
    grid = Grid.filled(3, 3, lambda x, y: f"{x},{y}")
    neighbors = list(grid.neighbors_moore(0, 0, wrap=True))
    # With wrap, every cell has exactly 8 neighbors.
    assert len(neighbors) == 8
