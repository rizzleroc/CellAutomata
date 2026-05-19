"""Elementary 1D Wolfram automaton, drawn as a scrolling 2D grid.

The grid's width is the 1D world. Each step shifts every row down by one and
computes a new top row from the row that just moved off. Rule number 0-255
picks one of the 256 elementary rules; rule 30 and rule 110 are the classics.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

from cellauto.grid import Grid


@dataclass
class Wolfram1DRule:
    name: str = "wolfram1d"
    rule_number: int = 30
    alive_color: str = "#111111"
    dead_color: str = "#f5f5f5"
    rng: random.Random = field(default_factory=random.Random)

    def state_factory(self, x: int, y: int) -> bool:
        # Seed the bottom-most row with a single live cell in the middle;
        # everything else dead. The top row holds the most-recent generation.
        return False

    def initial_seed(self, grid: Grid[bool]) -> None:
        """Helper called by Engine after grid construction for Wolfram only."""
        mid = grid.width // 2
        grid.cells[-1][mid] = True

    def step(self, grid: Grid[bool]) -> Grid[bool]:
        # The "current generation" lives on the last row; new generations
        # scroll upward so the top row is the oldest visible history.
        current = list(grid.cells[-1])
        w = grid.width
        next_row = [False] * w
        for x in range(w):
            left = current[(x - 1) % w]
            center = current[x]
            right = current[(x + 1) % w]
            pattern = (1 if left else 0) << 2 | (1 if center else 0) << 1 | (1 if right else 0)
            next_row[x] = bool((self.rule_number >> pattern) & 1)
        # Scroll up and put the new generation at the bottom.
        grid.cells = grid.cells[1:] + [next_row]
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
