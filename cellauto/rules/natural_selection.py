"""NaturalSelectionRule — primordial-soup mixing (alias of AbiogenesisStage0).

The original v1.0 sim called itself a "natural selection simulator." It isn't.
What the four rules actually sketch is the prebiotic-chemistry chapter of the
origin-of-life story:

    Rule 1 — neighbor color propagation       → primordial-soup mixing /
                                                 diffusion of chemical species
                                                 (Oparin 1924, Haldane 1929)
    Rule 2 — same-color cells combine         → condensation reactions between
                                                 like monomers (Miller-Urey 1953)
    Rule 3 — only NEW cells can combine       → activated-intermediate kinetics
                                                 (fresh products are reactive,
                                                 settled products are inert)
    Rule 4 — combination → "amoeba"            → first protocell, first
                                                 compartmentalization

This module implements those four rules honestly. Rule 3 now actually gates
combinations: a cell is only "new" for the single step in which its color
genuinely shifted. v2.0 left Rule 3 as a no-op; this fix is the substance of
Phase 2 P0-1.

This is also the canonical Stage-0 implementation of the abiogenesis pipeline
in cellauto.rules.abiogenesis. The class is re-exported there as
AbiogenesisStage0Soup; the historical name NaturalSelectionRule is retained
for backward compatibility with v2.0 snapshots and CLI invocations.

References:
    Oparin, A. I. (1924). The Origin of Life.
    Haldane, J. B. S. (1929). The Origin of Life. Rationalist Annual.
    Miller, S. L. (1953). A production of amino acids under possible primitive
        Earth conditions. Science, 117(3046), 528-529.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.grid import Grid

# 16 "molecular species." With this many species, the probability that two
# random cells share a species is 1/16 — combinations fire on a human
# timescale (the v1 code used 24-bit random colors and combinations occurred
# at P ≈ 1/16,777,216).
PALETTE: tuple[str, ...] = (
    "#e6194b", "#3cb44b", "#ffe119", "#4363d8",
    "#f58231", "#911eb4", "#46f0f0", "#f032e6",
    "#bcf60c", "#fabebe", "#008080", "#e6beff",
    "#9a6324", "#fffac8", "#800000", "#aaffc3",
)
AMOEBA_LIFESPAN = 25  # steps before a protocell membrane breaks


@dataclass
class Cell:
    color: str
    is_new: bool = True
    is_ameba: bool = False
    age: int = 0

    def to_json(self) -> dict:
        return {"color": self.color, "is_new": self.is_new,
                "is_ameba": self.is_ameba, "age": self.age}

    @classmethod
    def from_json(cls, data: dict) -> Cell:
        return cls(color=data["color"], is_new=data["is_new"],
                   is_ameba=data["is_ameba"], age=data.get("age", 0))


@dataclass
class NaturalSelectionRule:
    """Stage 0 of the abiogenesis pipeline: primordial-soup mixing.

    Each step: every non-amoeba cell adopts the species of a random Moore
    neighbor (Rule 1). Then any adjacent pair of cells that BOTH just changed
    species AND share a species combine into an amoeba (Rules 2-4). Amoebas
    are inert for `amoeba_lifespan` steps, then die.

    The Rule 3 gate works because `is_new` is reset to False at the start of
    every step and is only flipped True for cells whose species genuinely
    changed *this* step. The v2.0 bug was setting `is_new = True` whenever
    a neighbor was sampled, regardless of whether the sample differed.
    """
    name: str = "natural-selection"
    renderer_kind: str = "discrete"
    palette: tuple[str, ...] = PALETTE
    amoeba_lifespan: int = AMOEBA_LIFESPAN
    rng: random.Random = field(default_factory=random.Random)

    # ---- Rule protocol -----------------------------------------------------

    def init_state(self, width: int, height: int) -> Grid[Cell]:
        return Grid.filled(width, height,
                           lambda x, y: Cell(color=self.rng.choice(self.palette)))

    def step(self, grid: Grid[Cell]) -> Grid[Cell]:
        w, h = grid.width, grid.height
        old_colors = [[grid.cells[y][x].color for x in range(w)] for y in range(h)]

        # Phase 1 — Rule 1 (mixing) + Rule 4 lifecycle:
        # Reset is_new on every cell first. Only cells whose species genuinely
        # SHIFTS this step get is_new = True. Aged amoebas die.
        for y in range(h):
            for x in range(w):
                cell = grid.cells[y][x]
                cell.is_new = False  # << Phase 2 P0 fix: reset every step
                if cell.is_ameba:
                    cell.age += 1
                    if cell.age >= self.amoeba_lifespan:
                        grid.cells[y][x] = Cell(color=self.rng.choice(self.palette))
                        # New cell starts is_new=True since its "color" appeared this step.
                        grid.cells[y][x].is_new = True
                    continue

                neighbors = []
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            neighbors.append(old_colors[ny][nx])
                if not neighbors:
                    continue
                new_color = self.rng.choice(neighbors)
                if new_color != cell.color:
                    cell.color = new_color
                    cell.is_new = True  # genuine shift this step

        # Phase 2 — Rules 2 & 3 & 4: combine same-species new pairs into amoebas.
        for y in range(h):
            for x in range(w):
                current = grid.cells[y][x]
                if current.is_ameba or not current.is_new:
                    continue
                for dx, dy in ((1, 0), (0, 1), (1, 1), (-1, 1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < w and 0 <= ny < h):
                        continue
                    other = grid.cells[ny][nx]
                    if other.is_ameba or not other.is_new:
                        continue
                    if other.color == current.color:
                        new_color = self._distinct_palette_color(current.color)
                        for c in (current, other):
                            c.color = new_color
                            c.is_new = False
                            c.is_ameba = True
                            c.age = 0
                        break
        return grid

    def _distinct_palette_color(self, exclude: str) -> str:
        choices = [c for c in self.palette if c != exclude]
        if not choices:
            return self.palette[0]  # palette-of-1 fallback (Phase 2 §2.11)
        return self.rng.choice(choices)

    def render_cell(self, grid: Grid[Cell], x: int, y: int) -> tuple[str, str]:
        cell = grid.cells[y][x]
        return cell.color, ("oval" if cell.is_ameba else "rect")

    def render_rgb(self, grid: Grid[Cell]) -> np.ndarray:
        # Allow continuous-renderer code paths to view this rule too.
        arr = np.zeros((grid.height, grid.width, 3), dtype=np.uint8)
        for y in range(grid.height):
            for x in range(grid.width):
                hex_color = grid.cells[y][x].color.lstrip("#")
                arr[y, x] = (int(hex_color[0:2], 16),
                             int(hex_color[2:4], 16),
                             int(hex_color[4:6], 16))
        return arr

    def population(self, grid: Grid[Cell]) -> Mapping[str, int]:
        amoebas = sum(1 for row in grid.cells for c in row if c.is_ameba)
        new_cells = sum(1 for row in grid.cells for c in row
                        if not c.is_ameba and c.is_new)
        total = grid.width * grid.height
        return {"amoebas": amoebas, "new": new_cells,
                "settled": total - amoebas - new_cells}

    def serialize_state(self, grid: Grid[Cell]) -> dict:
        return {
            "width": grid.width, "height": grid.height,
            "cells": [[c.to_json() for c in row] for row in grid.cells],
        }

    def deserialize_state(self, data: dict) -> Grid[Cell]:
        w, h = data["width"], data["height"]
        cells = [[Cell.from_json(c) for c in row] for row in data["cells"]]
        return Grid(width=w, height=h, cells=cells)

    def to_config(self) -> dict:
        # palette and rng are not part of the rule's reproducible identity.
        return {"amoeba_lifespan": self.amoeba_lifespan}
