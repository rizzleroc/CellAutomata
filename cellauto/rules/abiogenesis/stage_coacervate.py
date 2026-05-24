"""Coacervates — membraneless compartments by liquid-liquid phase separation.

Before lipid vesicles, Alexander Oparin (1924) proposed that the first
protocells were **coacervates**: dense, membraneless droplets that form when a
solution of macromolecules spontaneously separates into a polymer-rich phase
and a dilute phase. This is the same physics behind modern **biomolecular
condensates** (membraneless organelles like nucleoli and stress granules),
which has revived coacervates as a serious origin-of-life compartment model
(Tang, Mann, and others): droplets can concentrate RNA and catalysts, exchange
material with their surroundings, and grow, fuse, and divide — all without a
membrane.

The dynamics are modelled with the **Cahn-Hilliard equation**, the canonical
continuum model of phase separation with a *conserved* order parameter φ (local
composition):

    μ   =  φ³ − φ − κ ∇²φ          (chemical potential; double-well + interface)
    ∂φ/∂t  =  M ∇²μ                 (conserved: total φ is preserved)

From a nearly-uniform, slightly off-critical mixture with small fluctuations,
φ spontaneously separates into a coacervate-rich phase (φ → +1, drawn as warm
gold droplets) and a dilute phase (φ → −1, dark). The droplets then **coarsen**
— smaller droplets dissolve and feed larger ones (Ostwald ripening) and
neighbours fuse — so the droplet count falls over time, exactly as observed for
real coacervates.

References:
    Oparin, A. I. (1924). The Origin of Life. (Coacervate hypothesis.)
    Cahn, J. W., & Hilliard, J. E. (1958). Free energy of a nonuniform system.
        J. Chem. Phys., 28(2), 258-267.
    Bungenberg de Jong, H. G. (1932). Coacervation. (Original coacervate work.)
    Oparin, A. I., et al. (1976). On the role of coacervate droplets in the
        origin of life. Orig. Life, 7, 23-30.
    Banani, S. F., et al. (2017). Biomolecular condensates: organizers of
        cellular biochemistry. Nat. Rev. Mol. Cell Biol., 18, 285-298.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.rules.abiogenesis.science import laplacian_5pt


@dataclass
class CoacervateState:
    phi: np.ndarray  # composition order parameter, ~[-1, 1] (H, W)


@dataclass
class AbiogenesisStageCoacervate:
    name: str = "abiogenesis-coacervate"
    renderer_kind: str = "field"
    kappa: float = 0.3  # gradient-energy coefficient → interface width / line tension
    mobility: float = 0.8  # M — how fast material moves down the potential gradient
    mean_composition: float = -0.4  # off-critical: < 0 favours isolated droplets
    noise: float = 0.3  # initial fluctuation amplitude
    droplet_threshold: float = 0.2  # φ above this counts as coacervate-rich
    dt: float = 0.06
    substeps_per_frame: int = 10
    rng: random.Random = field(default_factory=random.Random)

    def init_state(
        self,
        width: int,
        height: int,
        *,
        seed_field: np.ndarray | None = None,
    ) -> CoacervateState:
        from cellauto.rules.abiogenesis.science import normalise_signal

        signal = normalise_signal(seed_field)
        gen = np.random.default_rng(self.rng.randrange(2**31))
        phi = self.mean_composition + self.noise * (gen.random((height, width), dtype=np.float32) - 0.5)
        if signal is not None:
            # G1: bias φ upward where the upstream chemistry was active —
            # those become the nucleation seeds for the Cahn-Hilliard
            # coarsening so coacervate droplets emerge from real upstream
            # hot-spots instead of pure noise.
            phi = phi + (signal * 0.6).astype(np.float32)
        return CoacervateState(phi=phi.astype(np.float32))

    def extract_signal(self, state: CoacervateState) -> np.ndarray:
        """Downstream: the coacervate-rich field (normalised composition).
        Bright cells are inside droplets."""
        return np.clip((state.phi + 1.0) / 2.0, 0.0, 1.0).astype(np.float32)

    def step(self, state: CoacervateState) -> CoacervateState:
        phi = state.phi
        for _ in range(self.substeps_per_frame):
            # Chemical potential μ = f'(φ) − κ∇²φ, with double-well f'(φ)=φ³−φ.
            mu = phi**3 - phi - self.kappa * laplacian_5pt(phi)
            # Conserved (Cahn-Hilliard) dynamics: ∂φ/∂t = M ∇²μ.
            phi = phi + self.dt * self.mobility * laplacian_5pt(mu)
            np.clip(phi, -1.5, 1.5, out=phi)
        state.phi = phi
        return state

    def _rich_mask(self, state: CoacervateState) -> np.ndarray:
        return state.phi > self.droplet_threshold

    def render_cell(self, state: CoacervateState, x: int, y: int) -> tuple[str, str]:
        t = float(np.clip((state.phi[y, x] + 1.0) / 2.0, 0.0, 1.0))
        r = int(20 + t * 192)
        g = int(16 + t * 164)
        b = int(24 + t * 66)
        return f"#{r:02x}{g:02x}{b:02x}", "rect"

    def render_rgb(self, state: CoacervateState) -> np.ndarray:
        t = np.clip((state.phi + 1.0) / 2.0, 0.0, 1.0)  # 0 dilute (dark) .. 1 rich (gold)
        r = 20 + t * 192
        g = 16 + t * 164
        b = 24 + t * 66
        return np.clip(np.stack([r, g, b], axis=-1), 0, 255).astype(np.uint8)

    def population(self, state: CoacervateState) -> Mapping[str, int]:
        mask = self._rich_mask(state)
        return {
            "coacervate_cells": int(mask.sum()),
            "droplets": self._count_connected(mask),
            "rich_pct": int(round(100 * float(mask.mean()))),
        }

    @staticmethod
    def _count_connected(mask: np.ndarray) -> int:
        """Count 4-connected True regions via flood fill (droplet count)."""
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

    def serialize_state(self, state: CoacervateState) -> dict:
        return {"phi": np.round(state.phi, 4).tolist()}

    def deserialize_state(self, data: dict) -> CoacervateState:
        return CoacervateState(phi=np.array(data["phi"], dtype=np.float32))

    def to_config(self) -> dict:
        return {
            "kappa": self.kappa,
            "mobility": self.mobility,
            "mean_composition": self.mean_composition,
            "noise": self.noise,
            "droplet_threshold": self.droplet_threshold,
            "dt": self.dt,
            "substeps_per_frame": self.substeps_per_frame,
        }
