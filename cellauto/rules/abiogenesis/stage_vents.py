"""Alkaline hydrothermal vents — a proton gradient does the work (Russell/Lane).

The metabolism-first school locates the origin of life not in a "soup" energised
by lightning, but at **alkaline hydrothermal vents** like the Lost City field.
Serpentinisation of the ocean crust produces warm, alkaline (pH ~9-11),
hydrogen-rich fluid. On the early Earth the ocean was mildly acidic (CO2-rich,
pH ~5-7). Where alkaline vent fluid meets acidic ocean across the thin
catalytic (FeS) walls of a vent chimney, there is a natural **proton gradient**
of ~3-4 pH units — a built-in proton-motive force, the same kind of gradient
that every living cell uses to make ATP today (chemiosmosis).

Lane & Martin (2012) argue this geochemical gradient, not a hand-set "feed
rate", is the free-energy source that drives the first carbon fixation and
organic synthesis. This stage models exactly that: a proton field with an
alkaline chimney and an acidic ocean held at fixed values (Dirichlet sources);
the steady gradient between them carries a proton-motive force; and organic
matter is synthesised in proportion to the *steepness* of the local gradient —
so synthesis ignites along the chimney wall, the interface, rather than
uniformly. Turn the gradient off (vent and ocean to the same pH) and synthesis
stops: no gradient, no free energy, no chemistry.

References:
    Russell, M. J., & Hall, A. J. (1997). The emergence of life from iron
        monosulphide bubbles… J. Geol. Soc., 154(3), 377-402.
    Martin, W., & Russell, M. J. (2007). On the origin of biochemistry at an
        alkaline hydrothermal vent. Phil. Trans. R. Soc. B, 362, 1887-1925.
    Lane, N., & Martin, W. F. (2012). The origin of membrane bioenergetics.
        Cell, 151(7), 1406-1416.
    Sojo, V., Herschy, B., Whicher, A., Camprubí, E., & Lane, N. (2016). The
        origin of life in alkaline hydrothermal vents. Astrobiology, 16(2),
        181-197.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.rules.abiogenesis.science import laplacian_5pt


@dataclass
class VentState:
    protons: np.ndarray  # proton proxy: 0 = alkaline (vent), 1 = acidic (ocean)
    organic: np.ndarray  # synthesised organic matter (H, W)


@dataclass
class AbiogenesisStageVents:
    name: str = "abiogenesis-hydrothermal-vent"
    renderer_kind: str = "field"
    vent_alkalinity: float = 0.05  # clamped proton level inside the chimney
    ocean_acidity: float = 0.95  # clamped proton level at the ocean edges
    diffusion_H: float = 0.6  # proton diffusion (sets how sharp the interface is)
    diffusion_O: float = 0.08
    k_synth: float = 0.8  # organic synthesis per unit proton-motive force
    decay: float = 0.04  # organic decay
    dt: float = 0.2
    substeps_per_frame: int = 4
    rng: random.Random = field(default_factory=random.Random)

    def _chimney_cols(self, width: int) -> tuple[int, int]:
        half = max(1, width // 12)
        c = width // 2
        return c - half, c + half

    def init_state(self, width: int, height: int) -> VentState:
        protons = np.full((height, width), self.ocean_acidity, dtype=np.float32)
        self._apply_sources(protons)
        organic = np.zeros((height, width), dtype=np.float32)
        return VentState(protons=protons, organic=organic)

    def _apply_sources(self, protons: np.ndarray) -> None:
        # Dirichlet boundary conditions: the chimney interior stays alkaline and
        # the ocean edges stay acidic, so a steady gradient is maintained.
        lo, hi = self._chimney_cols(protons.shape[1])
        protons[:, lo:hi] = self.vent_alkalinity
        protons[:, :1] = self.ocean_acidity
        protons[:, -1:] = self.ocean_acidity

    def step(self, state: VentState) -> VentState:
        H, org = state.protons, state.organic
        for _ in range(self.substeps_per_frame):
            H = H + self.dt * self.diffusion_H * laplacian_5pt(H)
            np.clip(H, 0.0, 1.0, out=H)
            self._apply_sources(H)
            # Proton-motive force ∝ steepness of the proton gradient.
            gy, gx = np.gradient(H)
            pmf = np.hypot(gx, gy).astype(np.float32)
            org = org + self.dt * (
                self.diffusion_O * laplacian_5pt(org) + self.k_synth * pmf * (1.0 - org) - self.decay * org
            )
            np.clip(org, 0.0, 1.0, out=org)
        state.protons, state.organic = H, org
        return state

    def _pmf(self, state: VentState) -> np.ndarray:
        gy, gx = np.gradient(state.protons)
        return np.hypot(gx, gy).astype(np.float32)

    def render_cell(self, state: VentState, x: int, y: int) -> tuple[str, str]:
        o = float(state.organic[y, x])
        if o > 0.3:
            g = int(np.clip(o * 255, 0, 255))
            return f"#00{g:02x}b4", "rect"
        h = float(state.protons[y, x])  # 0 alkaline .. 1 acidic
        r = int(40 + h * 170)
        b = int(160 - h * 120)
        return f"#{r:02x}5a{b:02x}", "rect"

    def render_rgb(self, state: VentState) -> np.ndarray:
        h = state.protons  # 0 alkaline (blue) .. 1 acidic (orange)
        r = (40 + h * 170).astype(np.float32)
        g = np.full_like(h, 90.0)
        b = (160 - h * 120).astype(np.float32)
        # Organic synthesis glows teal-green over the pH backdrop.
        o = state.organic
        r = r * (1 - o)
        g = g * (1 - o) + 235 * o
        b = b * (1 - o) + 180 * o
        return np.clip(np.stack([r, g, b], axis=-1), 0, 255).astype(np.uint8)

    def population(self, state: VentState) -> Mapping[str, int]:
        pmf = self._pmf(state)
        organic_cells = int((state.organic > 0.3).sum())
        interface = int((pmf > 0.05).sum())
        # ΔpH proxy across the chimney wall, ×100.
        delta = float(self.ocean_acidity - self.vent_alkalinity)
        return {
            "organic_cells": organic_cells,
            "interface_cells": interface,
            "mean_pmf_x1000": int(round(float(pmf.mean()) * 1000)),
            "gradient_x100": int(round(delta * 100)),
        }

    def serialize_state(self, state: VentState) -> dict:
        return {
            "protons": np.round(state.protons, 4).tolist(),
            "organic": np.round(state.organic, 4).tolist(),
        }

    def deserialize_state(self, data: dict) -> VentState:
        return VentState(
            protons=np.array(data["protons"], dtype=np.float32),
            organic=np.array(data["organic"], dtype=np.float32),
        )

    def to_config(self) -> dict:
        return {
            "vent_alkalinity": self.vent_alkalinity,
            "ocean_acidity": self.ocean_acidity,
            "diffusion_H": self.diffusion_H,
            "diffusion_O": self.diffusion_O,
            "k_synth": self.k_synth,
            "decay": self.decay,
            "dt": self.dt,
            "substeps_per_frame": self.substeps_per_frame,
        }
