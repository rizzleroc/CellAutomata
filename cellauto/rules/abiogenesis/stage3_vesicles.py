"""Stage 3 — Vesicle formation (lipid self-assembly).

Chemistry compartmentalises. Once enough amphiphilic (lipid-like) molecules
accumulate in a region, they spontaneously self-assemble into a bilayer
membrane that encloses an interior. The first stable membrane around a patch
of self-sustaining chemistry is a protocell — the threshold the original
v1.0 README called "evolving into an amoeba."

This stage runs a Gray-Scott-like reaction-diffusion for a "lipid precursor"
species (L) and a substrate (S), then marks cells where L exceeds the
critical micelle concentration (CMC) threshold as belonging to a vesicle.
Connected high-L regions become discrete vesicles tracked by ID.

Toy in scope, real in concept: real lipid bilayer dynamics involve fluid
mechanics, curvature elasticity, and surface tension — see Helfrich (1973),
Lipowsky & Sackmann (1995). This implementation is a discrete approximation:
threshold + connected-component labelling. Sufficient for the educational
demo; not sufficient to publish a paper.

References:
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
    # G3 — Helfrich (1973) bending-elastic regularisation. The bending
    # energy of a fluid membrane is E_b = (κ_b/2) ∫ (2H)² dA where H is the
    # local mean curvature. In a phase-field representation the variational
    # derivative contributes a biharmonic term ∂φ/∂t += −κ_b · ∇²(∇²φ),
    # which suppresses high-curvature interfaces — i.e. real fluid
    # membranes resist sharp bends. Setting kappa_bend = 0 recovers the
    # pure-Gray-Scott behaviour the v3.4 vesicle stage shipped with.
    #
    # The biharmonic operator's CFL stability limits κ_b to small values
    # when applied per Gray-Scott substep, so we apply it ONCE per visible
    # frame (after all GS substeps), which gives a stronger per-frame
    # smoothing pass while staying numerically stable.
    #
    # The real bending modulus for prebiotic fatty-acid bilayers is
    # ~5–25 k_B T ≈ 2–10 × 10⁻²⁰ J (Boal 2012, *Mechanics of the Cell*).
    # We use a normalised dimensionless analogue here.
    kappa_bend: float = 0.025
    substeps_per_frame: int = 8
    rng: random.Random = field(default_factory=random.Random)

    def init_state(
        self,
        width: int,
        height: int,
        *,
        seed_field: np.ndarray | None = None,
    ) -> VesicleState:
        from cellauto.rules.abiogenesis.science import normalise_signal, seed_from_signal

        signal = normalise_signal(seed_field)
        u = np.ones((height, width), dtype=np.float32)
        if signal is not None:
            # G1: regions where upstream chemistry (RAF products, coacervate
            # droplets, autocatalytic hot-spots) was active become the
            # regions where amphiphiles accumulate first.
            v = seed_from_signal(signal, shape=(height, width), lo=0.0, hi=0.35)
            if v is None:
                v = np.zeros((height, width), dtype=np.float32)
            u = np.clip(1.0 - 0.6 * (v / 0.35), 0.4, 1.0).astype(np.float32)  # type: ignore[assignment]
        else:
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

    def extract_signal(self, state: VesicleState) -> np.ndarray:
        """Downstream: the amphiphile (lipid) concentration — bright cells
        are where bilayers and vesicles have formed."""
        return state.lipid.copy()

    def step(self, state: VesicleState) -> VesicleState:
        from cellauto.rules.abiogenesis.science import laplacian_5pt

        # Step the underlying Gray-Scott chemistry to grow lipid concentration.
        u, v = state.substrate, state.lipid
        for _ in range(self.substeps_per_frame):
            u, v = gray_scott_step(u, v, Du=self.Du, Dv=self.Dv, F=self.F, k=self.k)
        # G3: Helfrich bending-elasticity contribution applied ONCE per
        # visible frame (after all Gray-Scott substeps). The variational
        # derivative of the bending energy E_b ∝ (∇²φ)² is the biharmonic
        # operator ∇⁴φ = ∇²(∇²φ); applied with a small negative weight, it
        # rounds high-curvature interfaces — real fluid membranes resist
        # sharp bends.
        if self.kappa_bend > 0.0:
            biharmonic_v = laplacian_5pt(laplacian_5pt(v))
            v = v - self.kappa_bend * biharmonic_v
            np.clip(v, 0.0, 1.0, out=v)
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
