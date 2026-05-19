"""Generic 2D grid container.

The grid stores opaque cell-state objects — what those mean is up to the active
Rule. This keeps Conway (bool), Wolfram 1D (int), and NaturalSelection (Cell)
on the same data structure.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class Grid(Generic[T]):
    width: int
    height: int
    cells: list[list[T]]

    @classmethod
    def filled(cls, width: int, height: int, factory: Callable[[int, int], T]) -> Grid[T]:
        cells = [[factory(x, y) for x in range(width)] for y in range(height)]
        return cls(width=width, height=height, cells=cells)

    def get(self, x: int, y: int) -> T:
        return self.cells[y][x]

    def set(self, x: int, y: int, value: T) -> None:
        self.cells[y][x] = value

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def neighbors_moore(self, x: int, y: int, *, wrap: bool = False) -> Iterator[T]:
        """8-neighborhood (Moore). Skips out-of-bounds unless wrap is True."""
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if wrap:
                    nx %= self.width
                    ny %= self.height
                elif not self.in_bounds(nx, ny):
                    continue
                yield self.cells[ny][nx]

    def iter_coords(self) -> Iterator[tuple[int, int]]:
        for y in range(self.height):
            for x in range(self.width):
                yield x, y

    def map(self, fn: Callable[[T], T]) -> Grid[T]:
        new = [[fn(self.cells[y][x]) for x in range(self.width)] for y in range(self.height)]
        return Grid(width=self.width, height=self.height, cells=new)
