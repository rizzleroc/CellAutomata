"""Rule protocol shared by every automaton ruleset.

A Rule owns its data shape (Grid for discrete-cell rules; Field for
continuous-concentration rules) and tells the Engine how to:
  - construct its initial state from (width, height)
  - advance it one step
  - render the current state (shape and color per cell, or an RGB array)
  - report a stats breakdown
  - serialize / deserialize for snapshots
  - report its own config so snapshots round-trip rule parameters

This is the only contract the Engine knows about.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Rule(Protocol):
    name: str
    renderer_kind: str  # "discrete" or "field"

    def init_state(self, width: int, height: int) -> Any: ...
    def step(self, state: Any) -> Any: ...
    def population(self, state: Any) -> Mapping[str, int]: ...

    # Discrete renderer path: render_cell returns (color_hex, shape) per (x, y).
    # Field renderer path: render_rgb returns an (H, W, 3) uint8 numpy array.
    def render_cell(self, state: Any, x: int, y: int) -> tuple[str, str]: ...

    def render_rgb(self, state: Any) -> Any: ...

    # Snapshot round-trip.
    def serialize_state(self, state: Any) -> Any: ...
    def deserialize_state(self, data: Any) -> Any: ...
    def to_config(self) -> dict: ...
