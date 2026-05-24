"""Stage 4 — Protocell selection driven by the Eigen-Schuster hypercycle ODE.

Vesicles formed in Stage 3 are tracked as discrete protocells with internal
state. Each protocell carries a "genome" — a length-``n_species`` vector of
internal concentrations. The protocell evolves under two coupled pressures:

  1. Internal chemistry — the genome's concentration vector evolves by the
     Eigen-Schuster (1977) replicator ODE

         dx_i/dt = x_i ( k_i * x_{(i-1) mod n}  -  Φ )

     where Φ = Σ_j k_j * x_j * x_{(j-1) mod n} is the mean-field dilution
     flux that holds Σ x_i = 1 constant. This is THE hypercycle: each
     species i is catalysed by species (i-1 mod n), so closing the loop
     requires all n members to be present. Any missing member collapses the
     cycle (the limiting x_i → 0 takes the rest with it). The closed,
     "complete" hypercycle is evolutionarily stable in a way isolated
     replicators are not — this is the cooperative core of the model.

  2. External pressure — the protocell's size grows when the hypercycle is
     healthy (every member alive and contributing) and shrinks otherwise.
     Mutation adds Gaussian drift on division so daughters can diverge.
     Below a minimum size the cell dies.

The default ``dynamics="hypercycle"`` is the genuine replicator ODE; the
legacy ``dynamics="proxy"`` keeps the v3.4 scalar-coupling proxy as an
optional reference so the two can be A/B-compared (and the test suite can
pin both).

References:
    Eigen, M. (1971). Selforganization of matter and the evolution of
        biological macromolecules. Naturwissenschaften, 58(10), 465-523.
    Eigen, M., & Schuster, P. (1977-1979). The hypercycle. A principle of
        natural self-organization. Naturwissenschaften, 64(11), 541-565 and
        sequels.
    Szostak, J. W. (2017). The narrow road to the deep past: in search of the
        chemistry of the origin of life. Angew. Chem., 56(37), 11037-11043.
    Adamala, K., & Szostak, J. W. (2013). Nonenzymatic template-directed RNA
        synthesis inside model protocells. Science, 342(6162), 1098-1100.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.renderer import cmap_viridis
from cellauto.rules.abiogenesis.science import gray_scott_step


@dataclass
class Protocell:
    cx: float  # center x
    cy: float  # center y
    radius: float
    genome: np.ndarray  # vector of internal species concentrations, length S
    age: int = 0
    alive: bool = True

    def fitness(self) -> float:
        """Fitness proxy retained for the legacy ``dynamics='proxy'`` mode and
        for use by external observers (the inspector dialog, the network-view).

        The proxy is the cyclic coupling sum ``Σ g[i] * g[(i+1) % n]`` —
        scalar, maximised at the equal-concentration fixed point of the
        hypercycle, zero when any member is absent. Under the default
        ``dynamics='hypercycle'`` setting this is computed but not driving
        the population dynamics; the genuine replicator ODE in
        ``AbiogenesisStage4Selection._evolve_hypercycle`` runs underneath.
        """
        g = self.genome
        if float(g.sum()) <= 1e-6:
            return 0.0
        n = len(g)
        return float(sum(g[i] * g[(i + 1) % n] for i in range(n)))

    def hypercycle_health(self) -> float:
        """The genuine Eigen-Schuster measure of cycle integrity.

        For a closed hypercycle every species must be present, so the cycle
        is only as strong as its weakest member. We return ``min(genome) *
        n_species`` — bounded to [0, ~1] when the cycle is at the
        equal-concentration fixed point, and zero whenever ANY species is
        absent. This is what gates growth/division under the real ODE.
        """
        g = self.genome
        if g.size == 0:
            return 0.0
        return float(g.min() * g.size)


@dataclass
class SelectionState:
    chemistry: np.ndarray  # H x W x S float32 — underlying chemistry
    cells: list[Protocell]  # population of protocells


@dataclass
class AbiogenesisStage4Selection:
    name: str = "abiogenesis-stage4-selection"
    renderer_kind: str = "field"
    n_species: int = 4
    mutation_rate: float = 0.02
    division_radius: float = 10.0
    decay_age: int = 80
    F: float = 0.04
    k: float = 0.06
    Du: float = 0.16
    Dv: float = 0.08
    substeps_per_frame: int = 6
    # G2: pick the protocell dynamics. ``"hypercycle"`` (default) runs the
    # genuine Eigen-Schuster replicator ODE inside each cell every step;
    # ``"proxy"`` is the legacy scalar fitness from v3.4 retained for A/B
    # comparison and backward-compatibility of tests.
    dynamics: str = "hypercycle"
    hypercycle_dt: float = 0.15  # ODE step size (Euler) for the replicator ODE
    hypercycle_k: float = 1.0  # uniform catalytic rate; non-uniform breaks closure stability
    # Accessibility: swap the disc fitness colormap from red→green (CVD-hostile)
    # to a colourblind-safe blue→yellow ramp when toggled from View ▸ Colour-safe.
    colorblind_safe: bool = False
    rng: random.Random = field(default_factory=random.Random)

    def _evolve_hypercycle(self, x: np.ndarray) -> np.ndarray:
        """One Euler step of the Eigen-Schuster replicator ODE.

            dx_i/dt = x_i ( k_i * x_{(i-1) mod n}  -  Φ )

        with Φ chosen as the mean-field dilution that holds Σ x_i = 1 (the
        canonical constant-organisation hypercycle, see Eigen & Schuster
        1977 eqn 14). ``k_i`` is uniform here; non-uniform k_i is studied
        in the references and produces selective sub-cycles within the loop.
        """
        n = x.size
        if n == 0:
            return x
        # k_i * x_i * x_{(i-1) mod n} for every i.
        prev = np.roll(x, 1)
        growth = self.hypercycle_k * x * prev
        # Mean-field flux Φ = Σ growth (keeps Σ x_i conserved at equilibrium).
        phi = float(growth.sum()) / max(float(x.sum()), 1e-9)
        dx = growth - phi * x
        x_new = x + self.hypercycle_dt * dx
        np.clip(x_new, 0.0, None, out=x_new)
        # Renormalise to the original total mass to fight Euler drift.
        s = float(x_new.sum())
        if s > 1e-9:
            x_new = x_new * (float(x.sum()) / s)
        return x_new.astype(np.float32)

    @property
    def error_threshold(self) -> float:
        """Eigen's quasispecies error threshold ≈ 1/L, where L is the genome
        length (here ``n_species``). Above this per-digit mutation rate the
        master sequence can no longer be maintained against copying errors and
        the population melts into a random ensemble — the "error catastrophe."
        The default ``mutation_rate`` sits well below 1/n_species, so the
        population stays organized; raise it past the threshold to watch the
        catastrophe set in. Eigen (1971); Eigen & Schuster (1977)."""
        return 1.0 / self.n_species

    def init_state(
        self,
        width: int,
        height: int,
        *,
        seed_field: np.ndarray | None = None,
    ) -> SelectionState:
        from cellauto.rules.abiogenesis.science import normalise_signal

        signal = normalise_signal(seed_field)
        chem = np.zeros((height, width, self.n_species), dtype=np.float32)
        chem[:, :, 0] = 1.0  # background substrate
        if signal is not None:
            # G1: protocells are seeded at the brightest cells of the upstream
            # signal (vesicle centroids, RAF hot-spots) instead of random
            # positions. The number is fixed (3) but their locations follow
            # the field.
            flat = signal.flatten()
            top = np.argpartition(flat, -3)[-3:]
            cells: list[Protocell] = []
            for idx in top:
                py_i, px_i = divmod(int(idx), signal.shape[1])
                # Map onto the actual (width, height) — signal is already at
                # the target shape, so identity.
                genome = np.array(
                    [self.rng.uniform(0.05, 0.4) for _ in range(self.n_species)],
                    dtype=np.float32,
                )
                cells.append(Protocell(cx=float(px_i), cy=float(py_i), radius=4.0, genome=genome))
            # Boost the substrate where the upstream signal was active.
            chem[:, :, 1] = (signal * 0.4).astype(np.float32)
        else:
            for s in range(1, self.n_species):
                cx = self.rng.randrange(width // 4, width * 3 // 4)
                cy = self.rng.randrange(height // 4, height * 3 // 4)
                r = max(2, min(width, height) // 16)
                chem[cy - r : cy + r, cx - r : cx + r, s] = 0.4
            cells = []
            for _ in range(3):
                px = self.rng.uniform(width * 0.25, width * 0.75)
                py = self.rng.uniform(height * 0.25, height * 0.75)
                genome = np.array(
                    [self.rng.uniform(0.05, 0.4) for _ in range(self.n_species)],
                    dtype=np.float32,
                )
                cells.append(Protocell(cx=px, cy=py, radius=4.0, genome=genome))
        return SelectionState(chemistry=chem, cells=cells)

    def extract_signal(self, state: SelectionState) -> np.ndarray:
        """Downstream: a soft "where are the surviving protocells" mask —
        each living cell stamps a Gaussian into the field."""
        h, w = state.chemistry.shape[:2]
        out = np.zeros((h, w), dtype=np.float32)
        for cell in state.cells:
            if not cell.alive:
                continue
            cx, cy = int(round(cell.cx)), int(round(cell.cy))
            r = max(2, int(cell.radius))
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    y, x = cy + dy, cx + dx
                    if 0 <= y < h and 0 <= x < w:
                        d2 = dx * dx + dy * dy
                        out[y, x] = max(out[y, x], float(np.exp(-d2 / max(r * r, 1))))
        return out

    def step(self, state: SelectionState) -> SelectionState:
        # Step background chemistry (using species 0 and 1 as the GS pair).
        u, v = state.chemistry[:, :, 0], state.chemistry[:, :, 1]
        for _ in range(self.substeps_per_frame):
            u, v = gray_scott_step(u, v, Du=self.Du, Dv=self.Dv, F=self.F, k=self.k)
        state.chemistry[:, :, 0], state.chemistry[:, :, 1] = u, v

        # Update each protocell.
        new_cells: list[Protocell] = []
        use_hypercycle = self.dynamics == "hypercycle"
        for cell in state.cells:
            if not cell.alive:
                continue
            cell.age += 1
            if use_hypercycle:
                # G2: evolve the genome by the Eigen-Schuster replicator
                # ODE. The cycle's health (the limiting species concentration)
                # gates growth instead of the scalar proxy — this is the
                # genuine hypercycle dynamics, not just a fitness label.
                cell.genome = self._evolve_hypercycle(cell.genome)
                health = cell.hypercycle_health()
                # Apply a small Gaussian mutation as molecular noise.
                cell.genome = cell.genome + np.array(
                    [self.rng.gauss(0, self.mutation_rate) for _ in range(self.n_species)],
                    dtype=np.float32,
                )
                np.clip(cell.genome, 0.0, 1.0, out=cell.genome)
                # A healthy hypercycle (every species alive, near the
                # equal-concentration fixed point) grows; an incomplete one
                # shrinks. The threshold 0.4 = 0.4/n_species ≈ 0.1 per
                # species at the n=4 default.
                cell.radius += 0.2 if health > 0.4 else -0.1
            else:
                # Legacy proxy mode: scalar fitness gates growth, no ODE.
                fit = cell.fitness()
                cell.radius += 0.2 if fit > 0.05 else -0.1
                cell.genome = cell.genome + np.array(
                    [self.rng.gauss(0, self.mutation_rate) for _ in range(self.n_species)],
                    dtype=np.float32,
                )
                np.clip(cell.genome, 0.0, 1.0, out=cell.genome)
            cell.radius = max(0.0, cell.radius)
            # Death.
            if cell.age > self.decay_age or cell.radius < 1.0:
                cell.alive = False
                continue
            # Division when sufficiently large.
            if cell.radius >= self.division_radius:
                child = self._divide(cell)
                cell.radius = cell.radius / 2.0
                new_cells.append(child)
        state.cells = [c for c in state.cells if c.alive] + new_cells
        return state

    def _divide(self, parent: Protocell) -> Protocell:
        # Child inherits genome with mutation; placed adjacent to parent.
        child_genome = parent.genome + np.array(
            [self.rng.gauss(0, self.mutation_rate * 2) for _ in range(len(parent.genome))],
            dtype=np.float32,
        )
        np.clip(child_genome, 0.0, 1.0, out=child_genome)
        angle = self.rng.uniform(0, 2 * np.pi)
        offset = parent.radius * 0.6
        return Protocell(
            cx=parent.cx + float(np.cos(angle)) * offset,
            cy=parent.cy + float(np.sin(angle)) * offset,
            radius=parent.radius / 2.0,
            genome=child_genome,
        )

    def render_cell(self, state: SelectionState, x: int, y: int) -> tuple[str, str]:
        # Discrete view: are we inside any protocell?
        for cell in state.cells:
            if (x - cell.cx) ** 2 + (y - cell.cy) ** 2 <= cell.radius**2:
                return "#ffcc00", "oval"
        intensity = float(state.chemistry[y, x, 1])
        gray = int(np.clip(intensity * 255, 0, 255))
        return f"#{gray:02x}{gray:02x}{gray:02x}", "rect"

    def render_rgb(self, state: SelectionState) -> np.ndarray:
        v = state.chemistry[:, :, 1]
        img = cmap_viridis(v).copy()
        H, W = v.shape
        for cell in state.cells:
            if not cell.alive:
                continue
            # Paint a disc for each protocell.
            yy, xx = np.ogrid[:H, :W]
            disc = (xx - cell.cx) ** 2 + (yy - cell.cy) ** 2 <= cell.radius**2
            ring = ((xx - cell.cx) ** 2 + (yy - cell.cy) ** 2 <= cell.radius**2) & (
                (xx - cell.cx) ** 2 + (yy - cell.cy) ** 2 >= (cell.radius - 1) ** 2
            )
            # Fitness → hue. Default is red→green; colorblind_safe swaps to
            # blue→yellow (Wong's CVD-safe diverging pair), which separates
            # cleanly under deuteranopia and protanopia.
            fit = min(cell.fitness() / 0.25, 1.0)  # hypercycle max ≈ n*(0.5)^2/n = 0.25 for n=4
            if self.colorblind_safe:
                r = int(40 + 200 * fit)
                g = int(80 + 120 * fit)
                b = int(180 * (1 - fit) + 40 * fit)
            else:
                r = int(255 * (1 - fit))
                g = int(255 * fit)
                b = 0
            img[disc] = (r, g, b)
            img[ring] = (255, 255, 255)
        return img

    def population(self, state: SelectionState) -> Mapping[str, int]:
        alive = [c for c in state.cells if c.alive]
        avg_fit = float(np.mean([c.fitness() for c in alive])) if alive else 0.0
        return {
            "protocells": len(alive),
            "avg_radius": int(round(np.mean([c.radius for c in alive]) if alive else 0)),
            "avg_fitness_x1000": int(round(avg_fit * 1000)),
            "mutation_rate_x1000": int(round(self.mutation_rate * 1000)),
            "error_threshold_x1000": int(round(self.error_threshold * 1000)),
        }

    def serialize_state(self, state: SelectionState) -> dict:
        return {
            "chemistry": np.round(state.chemistry, 4).tolist(),
            "cells": [
                {
                    "cx": c.cx,
                    "cy": c.cy,
                    "radius": c.radius,
                    "genome": c.genome.tolist(),
                    "age": c.age,
                    "alive": c.alive,
                }
                for c in state.cells
            ],
        }

    def deserialize_state(self, data: dict) -> SelectionState:
        chem = np.array(data["chemistry"], dtype=np.float32)
        cells = [
            Protocell(
                cx=c["cx"],
                cy=c["cy"],
                radius=c["radius"],
                genome=np.array(c["genome"], dtype=np.float32),
                age=c["age"],
                alive=c["alive"],
            )
            for c in data["cells"]
        ]
        return SelectionState(chemistry=chem, cells=cells)

    def to_config(self) -> dict:
        return {
            "n_species": self.n_species,
            "mutation_rate": self.mutation_rate,
            "division_radius": self.division_radius,
            "decay_age": self.decay_age,
            "F": self.F,
            "k": self.k,
            "Du": self.Du,
            "Dv": self.Dv,
            "substeps_per_frame": self.substeps_per_frame,
        }
