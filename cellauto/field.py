"""Continuous chemical field — numpy-backed grid of species concentrations.

Used by reaction-diffusion (Stage 1) and downstream stages of the abiogenesis
pipeline. Each cell of the grid holds a vector of concentrations [c_0, c_1, ...]
for n species. Diffusion and reaction operate as numpy array ops, not Python
loops, so 200×200 grids stay interactive.

The discrete-cell rules (NaturalSelection / Conway / Wolfram / Stage 0) keep
using cellauto.grid.Grid; this module is for the continuous-state rules.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Field:
    """A H×W×S array of species concentrations.

    S is the number of chemical species tracked. concentrations[y, x, i] is
    the concentration of species i at cell (x, y).
    """
    width: int
    height: int
    species: int
    concentrations: np.ndarray  # shape (H, W, S), dtype float32

    @classmethod
    def zeros(cls, width: int, height: int, species: int) -> Field:
        return cls(width=width, height=height, species=species,
                   concentrations=np.zeros((height, width, species), dtype=np.float32))

    @classmethod
    def filled(cls, width: int, height: int, species: int, value: float) -> Field:
        arr = np.full((height, width, species), value, dtype=np.float32)
        return cls(width=width, height=height, species=species, concentrations=arr)

    def laplacian(self, species_index: int) -> np.ndarray:
        """5-point stencil Laplacian with toroidal wrap. Returns H×W array.

        Used by every reaction-diffusion implementation; computing it once
        and re-using makes the inner loops simple.
        """
        c = self.concentrations[:, :, species_index]
        return (
            np.roll(c, 1, axis=0) + np.roll(c, -1, axis=0)
            + np.roll(c, 1, axis=1) + np.roll(c, -1, axis=1)
            - 4 * c
        )

    def total(self, species_index: int) -> float:
        return float(self.concentrations[:, :, species_index].sum())

    def to_dict(self) -> dict:
        """Lossy-but-compact serialization: round to 4 decimals."""
        return {
            "width": self.width, "height": self.height, "species": self.species,
            "concentrations": np.round(self.concentrations, 4).tolist(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Field:
        arr = np.array(data["concentrations"], dtype=np.float32)
        return cls(width=data["width"], height=data["height"],
                   species=data["species"], concentrations=arr)
