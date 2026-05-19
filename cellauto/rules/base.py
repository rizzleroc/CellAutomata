"""Rule protocol shared by every automaton ruleset."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from cellauto.grid import Grid


@runtime_checkable
class Rule(Protocol):
    """A pluggable rule set.

    `name` is shown in the UI / CLI. `state_factory` produces the initial cell
    state for a given (x, y) — used by Grid.filled at engine start. `step`
    advances the grid one tick in-place or returns a new one (engine uses
    whatever it gets back). `render_cell` produces a (hex_color, shape) tuple
    the renderer can draw; shape is "rect" or "oval".
    """

    name: str

    def state_factory(self, x: int, y: int) -> Any: ...

    def step(self, grid: Grid[Any]) -> Grid[Any]: ...

    def render_cell(self, cell: Any) -> tuple[str, str]: ...

    def population(self, grid: Grid[Any]) -> Mapping[str, int]:
        """Return counts keyed by state-label, for the stats overlay."""
        ...

    def serialize_cell(self, cell: Any) -> Any:
        """Return a JSON-safe representation of a single cell."""
        ...

    def deserialize_cell(self, data: Any) -> Any:
        """Inverse of serialize_cell."""
        ...
