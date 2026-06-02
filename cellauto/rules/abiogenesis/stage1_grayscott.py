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

    def init_state(
        self,
        width: int,
        height: int,
        *,
        seed_field: np.ndarray | None = None,
    ) -> GrayScottState:
        # Standard Gray-Scott initial condition: u=1, v=0 everywhere except a
        # small perturbed central patch where v is seeded. The G1 pipeline
        # hand-off: if an upstream stage supplied a ``seed_field`` (organic
        # concentration from the vent, polymer from minerals, etc.) we use it
        # to seed v directly — the locations where upstream chemistry was
        # active become the locations where Gray-Scott patterns ignite.
        from cellauto.rules.abiogenesis.science import normalise_signal, seed_from_signal

        signal = normalise_signal(seed_field)
        u = np.ones((height, width), dtype=np.float32)
        if signal is not None:
            v = seed_from_signal(signal, shape=(height, width), lo=0.0, hi=0.45)
            # Pull u down where v is high so the system is locally near the
            # interesting (mass-conserved) regime, not the trivial (u=1, v=0).
            u = np.clip(1.0 - 0.5 * (v / 0.45 if v is not None else 0.0), 0.5, 1.0).astype(np.float32)  # type: ignore[assignment]
            if v is None:
                v = np.zeros((height, width), dtype=np.float32)
        else:
            # v4.0.4 B1 — sparse Poisson-disk scatter of 6-10 seed patches so
            # the hero frame shows scattered isolated spheres rather than a
            # hex-packed lattice at carrying capacity. The single-central-patch
            # legacy behaviour saturated the domain by ~step 600 and made the
            # Gray-Scott Stage 1 SEM look tiled. Deterministic via self.rng.
            v = np.zeros((height, width), dtype=np.float32)
            margin = max(4, min(width, height) // 12)
            # For tiny grids (where 2*margin would exceed the dimensions),
            # fall through to the degenerate single-patch fallback so we
            # never hit an empty-range randint.
            placed: list[tuple[int, int]] = []
            if width > 2 * margin + 1 and height > 2 * margin + 1:
                min_spacing = max(8, min(width, height) // 6)
                target = self.rng.randint(6, 10)
                attempts = 0
                while len(placed) < target and attempts < 400:
                    attempts += 1
                    cx = self.rng.randint(margin, width - margin - 1)
                    cy = self.rng.randint(margin, height - margin - 1)
                    if all((cx - px) ** 2 + (cy - py) ** 2 >= min_spacing**2 for px, py in placed):
                        placed.append((cx, cy))
                for cx, cy in placed:
                    r = self.rng.randint(2, max(3, min(width, height) // 14))
                    seed_v = self.rng.uniform(0.20, 0.45)
                    u[cy - r : cy + r, cx - r : cx + r] = 0.5
                    v[cy - r : cy + r, cx - r : cx + r] = seed_v
            if not placed:
                # Degenerate fallback (tiny grid): retain the legacy single-patch
                # behaviour so we never ship with v = 0 everywhere.
                cx, cy = width // 2, height // 2
                r = max(2, min(width, height) // 16)
                u[cy - r : cy + r, cx - r : cx + r] = 0.5
                v[cy - r : cy + r, cx - r : cx + r] = 0.25
        # Small random noise so symmetric initial conditions break (and so a
        # uniform seed field still has the variability the PDE needs to grow
        # interesting structure).
        noise = np.array(
            [[self.rng.uniform(-0.02, 0.02) for _ in range(width)] for _ in range(height)], dtype=np.float32
        )
        v += noise
        np.clip(v, 0.0, 1.0, out=v)
        return GrayScottState(u=u, v=v)

    def extract_signal(self, state: GrayScottState) -> np.ndarray:
        """Downstream stages get the inhibitor concentration field. Bright
        regions are where reaction-diffusion produced self-replicating spots."""
        return state.v.copy()

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

    def render_sprites(self, state: GrayScottState) -> list:
        """v4.0.2 — disabled. The v4.0.1 audit (whipgen-claude critique, see
        ROADMAP §6a) found that the sprite layer FOUGHT the depth-shaded
        substrate: spots became "ball bearings in egg cups" because the
        substrate was rendering peaks as craters AND the sprites superimposed
        discrete spheres on top. v4.0.2 flips the substrate light direction
        so peaks read as raised domes, and drops the sprite layer for
        Stage 1 — the continuous Gray-Scott concentration field IS the
        topography. Method kept (returns []) so the app's optional dispatch
        stays a no-op; the previous logic is preserved below as `_v401_sprites`
        for the historical record.
        """
        return []

    def _v401_sprites(self, state: GrayScottState) -> list:
        """Historical: the v4.0.1 sprite-emitter that the v4.0.2 audit
        retired. Kept for reference and for any future re-experimentation."""
        v = state.v
        if v.size == 0:
            return []
        h, w = v.shape
        threshold = 0.30
        # Cheap 3×3 local-maximum filter via numpy roll — no scipy dep.
        peaks = (v >= threshold) & (
            v
            == np.maximum.reduce(
                [
                    v,
                    np.roll(v, 1, 0),
                    np.roll(v, -1, 0),
                    np.roll(v, 1, 1),
                    np.roll(v, -1, 1),
                    np.roll(np.roll(v, 1, 0), 1, 1),
                    np.roll(np.roll(v, 1, 0), -1, 1),
                    np.roll(np.roll(v, -1, 0), 1, 1),
                    np.roll(np.roll(v, -1, 0), -1, 1),
                ]
            )
        )
        ys, xs = np.nonzero(peaks)
        # Scale per-spot by the v-field magnitude so younger spots are smaller.
        # Map to the canvas via the sprite library's 80px native size.
        canonical = 80.0  # spot.png native dimension in px
        # Target spot footprint: ~5 sim cells wide on the canvas so spots read
        # as raised protocell-sized blobs above the depth-shaded substrate.
        scale_base = 5.0 * (720.0 / max(w, h)) / canonical
        return [
            (int(x), int(y), "stage1/spot.png", float(scale_base * (0.8 + 0.4 * float(v[y, x]))))
            for y, x in zip(ys, xs, strict=False)
        ]

    def population(self, state: GrayScottState) -> Mapping[str, int]:
        total = state.v.size
        active = int((state.v > 0.2).sum())
        spots = int((state.v > 0.5).sum())
        return {"active": active, "high_concentration": spots, "inactive": total - active}

    def serialize_state(self, state: GrayScottState) -> dict:
        return {"u": state.u.tolist(), "v": state.v.tolist()}

    def deserialize_state(self, data: dict) -> GrayScottState:
        return GrayScottState(
            u=np.array(data["u"], dtype=np.float32),
            v=np.array(data["v"], dtype=np.float32),
        )

    def to_config(self) -> dict:
        return {
            "preset": self.preset,
            "F": self.F,
            "k": self.k,
            "Du": self.Du,
            "Dv": self.Dv,
            "substeps_per_frame": self.substeps_per_frame,
        }
