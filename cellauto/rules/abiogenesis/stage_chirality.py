"""Homochirality — spontaneous mirror-symmetry breaking (Frank 1953).

Life is homochiral: it uses only L-amino acids and D-sugars, never their mirror
images. A racemic prebiotic soup contains both enantiomers in equal amounts, so
something must have broken the mirror symmetry and amplified one handedness to
exclusivity. F. C. Frank's 1953 model showed how: an **autocatalytic** reaction
in which each enantiomer catalyses its own formation, combined with **mutual
antagonism** in which opposite enantiomers annihilate each other, is unstable
to the racemic state — the tiniest fluctuation is amplified until one hand wins.

Frank's kinetic scheme (here on a 2D reaction-diffusion field, substrate A):

    A + L  →  2L      (L autocatalyses,   rate k_a)
    A + R  →  2R      (R autocatalyses,   rate k_a)
    L + R  →  inert   (mutual antagonism, rate k_x)

Starting from a near-racemic field with small random fluctuations, local patches
break to opposite handedness, forming **chiral domains** (teal = L-dominant,
magenta = R-dominant) that then compete. The Soai reaction (1995) is the
experimental realisation of asymmetric autocatalysis with amplification of
enantiomeric excess.

References:
    Frank, F. C. (1953). On spontaneous asymmetric synthesis. Biochim. Biophys.
        Acta, 11, 459-463.
    Soai, K., Shibata, T., Morioka, H., & Choji, K. (1995). Asymmetric
        autocatalysis and amplification of enantiomeric excess. Nature, 378, 767.
    Blackmond, D. G. (2004). Asymmetric autocatalysis and its implications for
        the origin of homochirality. PNAS, 101(16), 5732-5736.
    Kondepudi, D. K., & Nelson, G. W. (1985). Weak neutral currents and the
        origin of biomolecular chirality. Nature, 314, 438-441.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.rules.abiogenesis.science import laplacian_5pt


@dataclass
class ChiralityState:
    left: np.ndarray  # L-enantiomer concentration (H, W)
    right: np.ndarray  # R-enantiomer concentration (H, W)
    substrate: np.ndarray  # achiral feedstock A (H, W)


@dataclass
class AbiogenesisStageHomochirality:
    name: str = "abiogenesis-homochirality"
    renderer_kind: str = "field"
    k_auto: float = 1.0  # autocatalysis rate (A + X -> 2X)
    k_cross: float = 2.0  # mutual antagonism rate (L + R -> inert)
    feed: float = 0.10  # substrate replenishment toward A0
    A0: float = 1.0  # baseline substrate level
    diffusion: float = 0.10  # enantiomer diffusion
    diffusion_A: float = 0.20  # substrate diffusion
    dt: float = 0.2
    substeps_per_frame: int = 4
    noise: float = 0.02  # initial racemic fluctuation amplitude
    rng: random.Random = field(default_factory=random.Random)

    def init_state(self, width: int, height: int) -> ChiralityState:
        npr = np.random.RandomState(self.rng.randrange(2**31))
        base = 0.1
        left = base + self.noise * npr.rand(height, width).astype(np.float32)
        right = base + self.noise * npr.rand(height, width).astype(np.float32)
        substrate = np.full((height, width), self.A0, dtype=np.float32)
        return ChiralityState(left=left, right=right, substrate=substrate)

    def step(self, state: ChiralityState) -> ChiralityState:
        L, R, A = state.left, state.right, state.substrate
        for _ in range(self.substeps_per_frame):
            auto_l = self.k_auto * A * L
            auto_r = self.k_auto * A * R
            cross = self.k_cross * L * R
            lap_l = laplacian_5pt(L)
            lap_r = laplacian_5pt(R)
            lap_a = laplacian_5pt(A)
            L = L + self.dt * (self.diffusion * lap_l + auto_l - cross)
            R = R + self.dt * (self.diffusion * lap_r + auto_r - cross)
            A = A + self.dt * (self.diffusion_A * lap_a - (auto_l + auto_r) + self.feed * (self.A0 - A))
            np.clip(L, 0.0, 4.0, out=L)
            np.clip(R, 0.0, 4.0, out=R)
            np.clip(A, 0.0, self.A0, out=A)
        state.left, state.right, state.substrate = L, R, A
        return state

    def _excess(self, state: ChiralityState) -> np.ndarray:
        total = state.left + state.right
        return (state.left - state.right) / (total + 1e-6)

    def render_cell(self, state: ChiralityState, x: int, y: int) -> tuple[str, str]:
        ee = float((state.left[y, x] - state.right[y, x]) / (state.left[y, x] + state.right[y, x] + 1e-6))
        t = (ee + 1.0) / 2.0
        r = int((1 - t) * 212 + t * 57)
        g = int((1 - t) * 57 + t * 212)
        b = int((1 - t) * 164 + t * 200)
        return f"#{r:02x}{g:02x}{b:02x}", "rect"

    def render_rgb(self, state: ChiralityState) -> np.ndarray:
        ee = self._excess(state)  # -1 (R) .. +1 (L)
        t = (ee + 1.0) / 2.0
        total = state.left + state.right
        bright = np.clip(total / (float(total.max()) + 1e-6), 0.0, 1.0)
        # Diverging map: magenta (R) ↔ dark ↔ teal (L), scaled by total concentration.
        r = ((1 - t) * 212 + t * 57) * bright
        g = ((1 - t) * 57 + t * 212) * bright
        b = ((1 - t) * 164 + t * 200) * bright
        return np.stack([r, g, b], axis=-1).astype(np.uint8)

    def population(self, state: ChiralityState) -> Mapping[str, int]:
        L, R = state.left, state.right
        total = L + R
        active = total > 0.2
        ee = self._excess(state)
        ee_global = float((L.sum() - R.sum()) / (total.sum() + 1e-6))
        l_dom = int((active & (ee > 0.5)).sum())
        r_dom = int((active & (ee < -0.5)).sum())
        return {
            "active": int(active.sum()),
            "ee_x100": int(round(ee_global * 100)),
            "L_dominant": l_dom,
            "R_dominant": r_dom,
        }

    def serialize_state(self, state: ChiralityState) -> dict:
        return {
            "left": np.round(state.left, 4).tolist(),
            "right": np.round(state.right, 4).tolist(),
            "substrate": np.round(state.substrate, 4).tolist(),
        }

    def deserialize_state(self, data: dict) -> ChiralityState:
        return ChiralityState(
            left=np.array(data["left"], dtype=np.float32),
            right=np.array(data["right"], dtype=np.float32),
            substrate=np.array(data["substrate"], dtype=np.float32),
        )

    def to_config(self) -> dict:
        return {
            "k_auto": self.k_auto,
            "k_cross": self.k_cross,
            "feed": self.feed,
            "A0": self.A0,
            "diffusion": self.diffusion,
            "diffusion_A": self.diffusion_A,
            "dt": self.dt,
            "substeps_per_frame": self.substeps_per_frame,
            "noise": self.noise,
        }
