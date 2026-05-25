"""Stage 3 — Lipid concentration regime (Gray-Scott proxy).

Chemistry compartmentalises. Once enough amphiphilic (lipid-like) molecules
accumulate in a region, they spontaneously self-assemble into a bilayer
membrane that encloses an interior. The first stable membrane around a patch
of self-sustaining chemistry is a protocell — the threshold the original
v1.0 README called "evolving into an amoeba."

⚠ HONEST STATUS — see docs/PUNCHLIST.md P1-1:

The stage runs a **Gray-Scott reaction-diffusion on (u, v)** with v
relabelled "lipid concentration", thresholds at ``cmc_threshold``
(a dimensionless field value, NOT the CMC in mM), and counts
connected components above the threshold as "vesicles". This is a
useful visualisation of concentration regimes but it is **not lipid
self-assembly** in any physical sense — there is no surface tension,
no curvature elasticity (Helfrich 1973), no fluid mechanics, and no
amphiphile-specific kinetics. The ``AMPHIPHILE_CMC_MM`` table
(decanoic ≈ 85 mM, oleic ≈ 0.1 mM) ships real measured CMCs but they
appear only as the ``cmc_mM`` display readout — switching the
``amphiphile`` knob between fatty acids does not change any dynamics.

To make this an actual lipid model would require: (a) coupling the
field threshold to ``AMPHIPHILE_CMC_MM[amphiphile]`` non-trivially,
(b) adding a curvature/line-tension term so closed shells are
energetically preferred over arbitrary blobs, (c) acknowledging
real measured fatty-acid kinetics. None of those are present.

References (for the concepts the stage gestures at, not what the
code implements):
    Pearson, J. E. (1993). Complex patterns in a simple system. Science,
        261(5118), 189-192.
    Helfrich, W. (1973). Elastic properties of lipid bilayers: theory and
        possible experiments. Z. Naturforsch. C, 28(11-12), 693-703.
    Deamer, D. W. (2008). Origins of life: How leaky were primitive cells?
        Nature, 454(7200), 37-38.
    Szostak, J. W., Bartel, D. P., & Luisi, P. L. (2001). Synthesizing life.
        Nature, 409(6818), 387-390.
    Hanczyc, M. M., & Szostak, J. W. (2004). Replicating vesicles as models
        of primitive cell growth and division. Curr. Opin. Chem. Biol., 8(6),
        660-664.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.renderer import cmap_viridis
from cellauto.rules.abiogenesis.science import (
    AMPHIPHILE_CMC_MM,
    gray_scott_step,
    vesicle_indicator,
)


@dataclass
class VesicleState:
    lipid: np.ndarray  # amphiphile concentration, H x W float32
    substrate: np.ndarray  # substrate concentration that feeds lipid synthesis
    membrane_mask: np.ndarray  # H x W bool — True where a membrane exists


@dataclass
class AbiogenesisStage3Vesicles:
    name: str = "abiogenesis-stage3-vesicles"
    renderer_kind: str = "field"
    # Which fatty acid the membrane is made of (see AMPHIPHILE_CMC_MM for the
    # measured CMCs). C8-C10 is the prebiotic sweet spot (Deamer, Murchison).
    amphiphile: str = "decanoic acid (C10)"
    cmc_threshold: float = 0.3  # normalized field value where 1.0 == this amphiphile's CMC
    F: float = 0.04
    k: float = 0.06
    Du: float = 0.16
    Dv: float = 0.08
    substeps_per_frame: int = 8
    rng: random.Random = field(default_factory=random.Random)

    def init_state(self, width: int, height: int) -> VesicleState:
        u = np.ones((height, width), dtype=np.float32)
        v = np.zeros((height, width), dtype=np.float32)
        # Multiple seeded centers — each will potentially grow into a vesicle.
        for _ in range(4):
            cx = self.rng.randrange(width // 4, width * 3 // 4)
            cy = self.rng.randrange(height // 4, height * 3 // 4)
            r = max(2, min(width, height) // 20)
            u[cy - r : cy + r, cx - r : cx + r] = 0.5
            v[cy - r : cy + r, cx - r : cx + r] = 0.25
        v += np.array(
            [[self.rng.uniform(-0.01, 0.01) for _ in range(width)] for _ in range(height)], dtype=np.float32
        )
        np.clip(v, 0.0, 1.0, out=v)
        return VesicleState(substrate=u, lipid=v, membrane_mask=np.zeros_like(v, dtype=bool))

    def step(self, state: VesicleState) -> VesicleState:
        # Step the underlying Gray-Scott chemistry to grow lipid concentration.
        u, v = state.substrate, state.lipid
        for _ in range(self.substeps_per_frame):
            u, v = gray_scott_step(u, v, Du=self.Du, Dv=self.Dv, F=self.F, k=self.k)
        state.substrate, state.lipid = u, v

        # Detect membrane regions where lipid concentration > CMC.
        state.membrane_mask = vesicle_indicator(v, threshold=self.cmc_threshold)
        return state

    def render_cell(self, state: VesicleState, x: int, y: int) -> tuple[str, str]:
        if state.membrane_mask[y, x]:
            return "#ffcc00", "oval"
        intensity = float(state.lipid[y, x])
        gray = int(np.clip(intensity * 255, 0, 255))
        return f"#{gray:02x}{gray:02x}{gray:02x}", "rect"

    def render_rgb(self, state: VesicleState) -> np.ndarray:
        # Lipid concentration as viridis underlay, membranes overlaid in yellow.
        base = cmap_viridis(state.lipid)
        mask = state.membrane_mask
        base[mask] = (255, 204, 0)  # amber, like a real lipid stain
        return base

    def population(self, state: VesicleState) -> Mapping[str, int]:
        membrane_cells = int(state.membrane_mask.sum())
        n_vesicles = self._count_connected(state.membrane_mask)
        active_lipid = int((state.lipid > 0.2).sum())
        cmc_mM = int(round(AMPHIPHILE_CMC_MM.get(self.amphiphile, 0.0)))
        return {
            "membrane_cells": membrane_cells,
            "vesicles": n_vesicles,
            "active_lipid": active_lipid,
            "cmc_mM": cmc_mM,
        }

    @staticmethod
    def _count_connected(mask: np.ndarray) -> int:
        """Count 4-connected True regions in `mask` via flood fill."""
        h, w = mask.shape
        seen = np.zeros_like(mask, dtype=bool)
        count = 0
        for y in range(h):
            for x in range(w):
                if mask[y, x] and not seen[y, x]:
                    count += 1
                    stack = [(x, y)]
                    while stack:
                        cx, cy = stack.pop()
                        if not (0 <= cx < w and 0 <= cy < h):
                            continue
                        if seen[cy, cx] or not mask[cy, cx]:
                            continue
                        seen[cy, cx] = True
                        stack.extend(((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)))
        return count

    def serialize_state(self, state: VesicleState) -> dict:
        return {
            "substrate": np.round(state.substrate, 4).tolist(),
            "lipid": np.round(state.lipid, 4).tolist(),
            "membrane_mask": state.membrane_mask.astype(int).tolist(),
        }

    def deserialize_state(self, data: dict) -> VesicleState:
        return VesicleState(
            substrate=np.array(data["substrate"], dtype=np.float32),
            lipid=np.array(data["lipid"], dtype=np.float32),
            membrane_mask=np.array(data["membrane_mask"], dtype=bool),
        )

    def to_config(self) -> dict:
        return {
            "amphiphile": self.amphiphile,
            "cmc_threshold": self.cmc_threshold,
            "F": self.F,
            "k": self.k,
            "Du": self.Du,
            "Dv": self.Dv,
            "substeps_per_frame": self.substeps_per_frame,
        }
