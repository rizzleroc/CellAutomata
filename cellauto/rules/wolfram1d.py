"""Elementary 1D Wolfram automaton, drawn as a scrolling 2D grid.

The bottom row is the current 1D generation. Each step computes the next
generation from the chosen rule number (0-255) and scrolls history upward.
Rules 30, 90, 110 are the classics; 110 is Turing-complete.

Reference:
    Wolfram, S. (2002). A New Kind of Science. Wolfram Media.
    Cook, M. (2004). Universality in elementary cellular automata. Complex
        Systems, 15, 1-40.  [proof that Rule 110 is Turing-complete]
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.grid import Grid


@dataclass
class Wolfram1DRule:
    name: str = "wolfram1d"
    renderer_kind: str = "discrete"
    rule_number: int = 30
    alive_color: str = "#111111"
    dead_color: str = "#f5f5f5"
    rng: random.Random = field(default_factory=random.Random)

    def init_state(self, width: int, height: int) -> Grid[bool]:
        grid = Grid.filled(width, height, lambda x, y: False)
        # Seed bottom row with a single live cell at center.
        grid.cells[-1][width // 2] = True
        return grid

    def step(self, grid: Grid[bool]) -> Grid[bool]:
        current = list(grid.cells[-1])
        w = grid.width
        next_row = [False] * w
        for x in range(w):
            left = current[(x - 1) % w]
            center = current[x]
            right = current[(x + 1) % w]
            pattern = (1 if left else 0) << 2 | (1 if center else 0) << 1 | (1 if right else 0)
            next_row[x] = bool((self.rule_number >> pattern) & 1)
        grid.cells = grid.cells[1:] + [next_row]
        return grid

    def render_cell(self, grid: Grid[bool], x: int, y: int) -> tuple[str, str]:
        return (self.alive_color if grid.cells[y][x] else self.dead_color), "rect"

    def render_rgb(self, grid: Grid[bool]) -> np.ndarray:
        arr = np.full((grid.height, grid.width, 3), 245, dtype=np.uint8)
        for y in range(grid.height):
            for x in range(grid.width):
                if grid.cells[y][x]:
                    arr[y, x] = (17, 17, 17)
        return arr

    def population(self, grid: Grid[bool]) -> Mapping[str, int]:
        # Distinguish the live generation from scrolled history (Phase 2 §2.6).
        live_now = sum(1 for c in grid.cells[-1] if c)
        history = sum(1 for row in grid.cells[:-1] for c in row if c)
        return {
            "live_now": live_now,
            "history_on": history,
            "history_off": (grid.height - 1) * grid.width - history,
        }

    def serialize_state(self, grid: Grid[bool]) -> dict:
        return {
            "width": grid.width,
            "height": grid.height,
            "cells": [[bool(c) for c in row] for row in grid.cells],
        }

    def deserialize_state(self, data: dict) -> Grid[bool]:
        return Grid(
            width=data["width"],
            height=data["height"],
            cells=[[bool(c) for c in row] for row in data["cells"]],
        )

    def to_config(self) -> dict:
        return {
            "rule_number": self.rule_number,
            "alive_color": self.alive_color,
            "dead_color": self.dead_color,
        }
