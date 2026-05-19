"""Conway's Game of Life — the canonical cellular automaton.

Cells are bool (alive/dead). B3/S23 rules: a dead cell with exactly 3 live
neighbors comes to life; a live cell with 2 or 3 live neighbors survives;
everything else dies.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

from cellauto.grid import Grid


@dataclass
class ConwaysLifeRule:
    name: str = "conway"
    initial_density: float = 0.35
    alive_color: str = "#222222"
    dead_color: str = "#f5f5f5"
    wrap: bool = True
    rng: random.Random = field(default_factory=random.Random)

    def state_factory(self, x: int, y: int) -> bool:
        return self.rng.random() < self.initial_density

    def step(self, grid: Grid[bool]) -> Grid[bool]:
        w, h = grid.width, grid.height
        next_cells = [[False] * w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                live = sum(1 for v in grid.neighbors_moore(x, y, wrap=self.wrap) if v)
                if grid.cells[y][x]:
                    next_cells[y][x] = live in (2, 3)
                else:
                    next_cells[y][x] = live == 3
        grid.cells = next_cells
        return grid

    def render_cell(self, cell: bool) -> tuple[str, str]:
        return (self.alive_color, "rect") if cell else (self.dead_color, "rect")

    def population(self, grid: Grid[bool]) -> Mapping[str, int]:
        alive = sum(1 for row in grid.cells for c in row if c)
        return {"alive": alive, "dead": grid.width * grid.height - alive}

    def serialize_cell(self, cell: bool) -> bool:
        return bool(cell)

    def deserialize_cell(self, data: bool) -> bool:
        return bool(data)
