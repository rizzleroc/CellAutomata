"""Mineral-surface catalysis — the first polymers form on clay, not in water.

A central problem for the "soup" picture is that **condensation polymerisation**
(joining monomers into chains, releasing water) is thermodynamically uphill in
bulk water — dilute monomers don't spontaneously become long polymers in the
open ocean. Mineral surfaces solve this. James Ferris showed that **montmorillonite
clay** catalyses the polymerisation of activated RNA nucleotides into chains of
30-50 units; the clay concentrates monomers on its charged surface and templates
the bond formation. A. G. Cairns-Smith went further, proposing clay crystals as
the first "genetic" material (clay-life genetic takeover). The same clay also
accelerates fatty-acid vesicle assembly (Hanczyc, Fujikawa & Szostak 2003).

This stage models that surface catalysis directly: a static **clay mask** sits
on the grid; free monomers diffuse and are fed; polymer forms from monomers at a
rate that is high *on* the clay and near-zero *off* it (bulk condensation is
unfavourable); polymer slowly hydrolyses everywhere. The result is that long
polymer accumulates on the clay patches while the bulk stays monomeric — the
chemistry is localised to the mineral surface. Set the on-clay and off-clay
rates equal (no catalysis) and the localisation disappears.

References:
    Ferris, J. P., Hill, A. R., Liu, R., & Orgel, L. E. (1996). Synthesis of
        long prebiotic oligomers on mineral surfaces. Nature, 381, 59-61.
    Cairns-Smith, A. G. (1982). Genetic Takeover and the Mineral Origins of
        Life. Cambridge University Press.
    Hanczyc, M. M., Fujikawa, S. M., & Szostak, J. W. (2003). Experimental
        models of primitive cellular compartments. Science, 302, 618-622.
    Hazen, R. M., & Sverjensky, D. A. (2010). Mineral surfaces, geochemical
        complexities, and the origins of life. CSH Perspect. Biol., 2, a002162.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.rules.abiogenesis.science import laplacian_5pt

# Real chemistry: Ferris (1996) showed that **Na-montmorillonite clay** catalyses
# the polymerisation of **5′-phosphorimidazolide of adenosine (ImpA)** — an
# activated nucleotide monomer — into RNA oligomers of length 30–50.
MONOMER_LABEL = "ImpA (5'-phosphorimidazolide of adenosine)"
POLYMER_LABEL = "RNA oligomer (30-50mer per Ferris 1996)"
MINERAL_LABEL = "Na-montmorillonite"


@dataclass
class MineralState:
    monomer: np.ndarray  # free monomer concentration (H, W)
    polymer: np.ndarray  # accumulated polymer (H, W)
    clay: np.ndarray  # static catalytic-surface mask (H, W) bool


@dataclass
class AbiogenesisStageMinerals:
    name: str = "abiogenesis-mineral-catalysis"
    renderer_kind: str = "field"
    k_clay: float = 0.25  # polymerisation rate on the clay surface
    k_bulk: float = 0.002  # polymerisation rate in bulk water (near zero)
    k_hydrolysis: float = 0.01  # polymer breakdown everywhere
    feed: float = 0.08  # monomer replenishment toward 1.0
    diffusion_M: float = 0.18
    diffusion_P: float = 0.04  # polymers diffuse slowly (large, surface-bound)
    clay_patches: int = 9
    dt: float = 0.5
    rng: random.Random = field(default_factory=random.Random)

    def init_state(self, width: int, height: int) -> MineralState:
        clay = np.zeros((height, width), dtype=bool)
        radius = max(2, min(width, height) // 9)
        yy, xx = np.ogrid[:height, :width]
        for _ in range(self.clay_patches):
            cx = self.rng.randrange(width)
            cy = self.rng.randrange(height)
            r = radius + self.rng.randrange(-1, 2)
            clay |= (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
        monomer = np.ones((height, width), dtype=np.float32)
        polymer = np.zeros((height, width), dtype=np.float32)
        return MineralState(monomer=monomer, polymer=polymer, clay=clay)

    def step(self, state: MineralState) -> MineralState:
        M, P, clay = state.monomer, state.polymer, state.clay
        kfield = np.where(clay, self.k_clay, self.k_bulk).astype(np.float32)
        poly_rate = kfield * M  # monomers condense into polymer at the local rate
        M = M + self.dt * (self.diffusion_M * laplacian_5pt(M) + self.feed * (1.0 - M) - poly_rate)
        P = P + self.dt * (self.diffusion_P * laplacian_5pt(P) + poly_rate - self.k_hydrolysis * P)
        np.clip(M, 0.0, 1.0, out=M)
        np.clip(P, 0.0, None, out=P)
        state.monomer, state.polymer = M, P
        return state

    def render_cell(self, state: MineralState, x: int, y: int) -> tuple[str, str]:
        p = float(np.clip(state.polymer[y, x], 0.0, 1.0))
        if p > 0.15:
            g = int(np.clip(p * 235, 0, 255))
            return f"#00{g:02x}96", "rect"
        return ("#322819", "rect") if state.clay[y, x] else ("#080a10", "rect")

    def render_rgb(self, state: MineralState) -> np.ndarray:
        h, w = state.clay.shape
        img = np.zeros((h, w, 3), dtype=np.float32)
        # Clay surface as a faint tan tint; bulk water near-black.
        img[state.clay] = (50, 40, 25)
        img[~state.clay] = (8, 10, 16)
        # Polymer glows teal-green where it has accumulated.
        p = np.clip(state.polymer, 0.0, 1.0)[..., None]
        glow = np.array([0, 235, 150], dtype=np.float32)
        img = img * (1 - p) + glow * p
        return np.clip(img, 0, 255).astype(np.uint8)

    def population(self, state: MineralState) -> Mapping[str, int]:
        P, clay = state.polymer, state.clay
        on = P[clay]
        off = P[~clay]
        on_mean = float(on.mean()) if on.size else 0.0
        off_mean = float(off.mean()) if off.size else 0.0
        return {
            "polymer_cells": int((P > 0.15).sum()),
            "clay_pct": int(round(100 * float(clay.mean()))),
            "polymer_on_clay_x100": int(round(on_mean * 100)),
            "polymer_in_bulk_x100": int(round(off_mean * 100)),
        }

    def serialize_state(self, state: MineralState) -> dict:
        return {
            "monomer": np.round(state.monomer, 4).tolist(),
            "polymer": np.round(state.polymer, 4).tolist(),
            "clay": state.clay.astype(int).tolist(),
        }

    def deserialize_state(self, data: dict) -> MineralState:
        return MineralState(
            monomer=np.array(data["monomer"], dtype=np.float32),
            polymer=np.array(data["polymer"], dtype=np.float32),
            clay=np.array(data["clay"], dtype=bool),
        )

    def to_config(self) -> dict:
        return {
            "k_clay": self.k_clay,
            "k_bulk": self.k_bulk,
            "k_hydrolysis": self.k_hydrolysis,
            "feed": self.feed,
            "diffusion_M": self.diffusion_M,
            "diffusion_P": self.diffusion_P,
            "clay_patches": self.clay_patches,
        }
