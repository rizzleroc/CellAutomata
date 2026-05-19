"""Conway's Game of Life — the canonical cellular automaton.

B3/S23: a dead cell with exactly 3 live neighbors comes alive; a live cell
with 2 or 3 live neighbors survives. Included as a known-good reference rule
that anyone can sanity-check the engine against (gliders, blinkers, blocks).

Reference:
    Gardner, M. (1970). Mathematical Games: The fantastic combinations of
        John Conway's new solitaire game "life". Scientific American.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.grid import Grid


@dataclass
class ConwaysLifeRule:
    name: str = "conway"
    renderer_kind: str = "discrete"
    initial_density: float = 0.35
    alive_color: str = "#222222"
    dead_color: str = "#f5f5f5"
    wrap: bool = True
    rng: random.Random = field(default_factory=random.Random)

    def init_state(self, width: int, height: int) -> Grid[bool]:
        return Grid.filled(width, height,
                           lambda x, y: self.rng.random() < self.initial_density)

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

    def render_cell(self, grid: Grid[bool], x: int, y: int) -> tuple[str, str]:
        return (self.alive_color if grid.cells[y][x] else self.dead_color), "rect"

    def render_rgb(self, grid: Grid[bool]) -> np.ndarray:
        arr = np.full((grid.height, grid.width, 3), 245, dtype=np.uint8)
        for y in range(grid.height):
            for x in range(grid.width):
                if grid.cells[y][x]:
                    arr[y, x] = (34, 34, 34)
        return arr

    def population(self, grid: Grid[bool]) -> Mapping[str, int]:
        alive = sum(1 for row in grid.cells for c in row if c)
        return {"alive": alive, "dead": grid.width * grid.height - alive}

    def serialize_state(self, grid: Grid[bool]) -> dict:
        return {"width": grid.width, "height": grid.height,
                "cells": [[bool(c) for c in row] for row in grid.cells]}

    def deserialize_state(self, data: dict) -> Grid[bool]:
        return Grid(width=data["width"], height=data["height"],
                    cells=[[bool(c) for c in row] for row in data["cells"]])

    def to_config(self) -> dict:
        return {"initial_density": self.initial_density, "wrap": self.wrap,
                "alive_color": self.alive_color, "dead_color": self.dead_color}
