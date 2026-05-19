"""Stage 1 — Reaction-diffusion (Gray-Scott).

A two-species reaction-diffusion system on a continuous concentration field.
At the right parameters it produces self-replicating spots that visually
resemble protocell division — Turing's "morphogenesis" mechanism applied to
a chemistry that mimics autocatalysis.

The math:
    ∂u/∂t = D_u ∇²u  -  u v² + F (1 - u)
    ∂v/∂t = D_v ∇²v  +  u v² - (F + k) v

u and v are two reactant concentrations. The non-linear term u v² is the
reaction; F is the feed rate of u; k+F is the kill rate of v; D_u and D_v
are diffusion coefficients. Pearson (1993) mapped out the (F, k) parameter
space and showed that small regions produce dramatically different patterns:
self-replicating spots, mitosis-like division, labyrinths, waves.

This is included in the abiogenesis pipeline because:
  1. Reaction-diffusion is one of the simplest systems that exhibits
     spontaneous pattern formation — exactly the "emergence" the original
     v1.0 README was reaching for.
  2. Gray-Scott spots can be interpreted as primitive autocatalytic
     reactions that have spatially localized themselves — a half-step
     toward Stage 2's autocatalytic sets.
  3. Visually it's the most arresting stage. It's what convinces a
     skeptic that simple rules can produce lifelike dynamics.

References:
    Turing, A. M. (1952). The chemical basis of morphogenesis. Philosophical
        Transactions of the Royal Society B, 237(641), 37-72.
    Gray, P., & Scott, S. K. (1985). Sustained oscillations and other exotic
        patterns of behavior in isothermal reactions. J. Phys. Chem., 89, 22.
    Pearson, J. E. (1993). Complex patterns in a simple system. Science,
        261(5118), 189-192.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.renderer import cmap_viridis
from cellauto.rules.abiogenesis.science import GRAY_SCOTT_PRESETS, gray_scott_step


@dataclass
class GrayScottState:
    u: np.ndarray  # H x W float32
    v: np.ndarray  # H x W float32


@dataclass
class AbiogenesisStage1GrayScott:
    name: str = "abiogenesis-stage1-grayscott"
    renderer_kind: str = "field"
    preset: str = "spots"
    F: float | None = None
    k: float | None = None
    Du: float = 0.16
    Dv: float = 0.08
    substeps_per_frame: int = 10  # the PDE is stable with small dt; run many sub-steps per visible frame
    rng: random.Random = field(default_factory=random.Random)

    def init_state(self, width: int, height: int) -> GrayScottState:
        # Standard Gray-Scott initial condition: u=1, v=0 everywhere except a
        # small perturbed central patch where v is seeded.
        u = np.ones((height, width), dtype=np.float32)
        v = np.zeros((height, width), dtype=np.float32)
        cx, cy = width // 2, height // 2
        r = max(2, min(width, height) // 16)
        u[cy - r:cy + r, cx - r:cx + r] = 0.5
        v[cy - r:cy + r, cx - r:cx + r] = 0.25
        # Small random noise so symmetric initial conditions break.
        noise = np.array([[self.rng.uniform(-0.02, 0.02) for _ in range(width)]
                          for _ in range(height)], dtype=np.float32)
        v += noise
        np.clip(v, 0.0, 1.0, out=v)
        return GrayScottState(u=u, v=v)

    def step(self, state: GrayScottState) -> GrayScottState:
        if self.F is not None and self.k is not None:
            F, k = self.F, self.k
        else:
            F, k = GRAY_SCOTT_PRESETS.get(self.preset, GRAY_SCOTT_PRESETS["spots"])
        u, v = state.u, state.v
        for _ in range(self.substeps_per_frame):
            u, v = gray_scott_step(u, v, Du=self.Du, Dv=self.Dv, F=F, k=k)
        state.u, state.v = u, v
        return state

    def render_cell(self, state: GrayScottState, x: int, y: int) -> tuple[str, str]:
        # Provided so discrete-renderer paths still function; not the canonical render.
        intensity = float(state.v[y, x])
        gray = int(np.clip(intensity * 255, 0, 255))
        return f"#{gray:02x}{gray:02x}{gray:02x}", "rect"

    def render_rgb(self, state: GrayScottState) -> np.ndarray:
        # Map v concentration through viridis — produces a published-paper-style image.
        return cmap_viridis(state.v)

    def population(self, state: GrayScottState) -> Mapping[str, int]:
        total = state.v.size
        active = int((state.v > 0.2).sum())
        spots = int((state.v > 0.5).sum())
        return {"active": active, "high_concentration": spots,
                "inactive": total - active}

    def serialize_state(self, state: GrayScottState) -> dict:
        return {"u": state.u.tolist(), "v": state.v.tolist()}

    def deserialize_state(self, data: dict) -> GrayScottState:
        return GrayScottState(
            u=np.array(data["u"], dtype=np.float32),
            v=np.array(data["v"], dtype=np.float32),
        )

    def to_config(self) -> dict:
        return {"preset": self.preset, "F": self.F, "k": self.k,
                "Du": self.Du, "Dv": self.Dv,
                "substeps_per_frame": self.substeps_per_frame}
