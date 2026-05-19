"""Stage 4 — Protocell selection (hypercycle dynamics).

Vesicles formed in Stage 3 are tracked as discrete protocells with internal
state. Each protocell carries a "genome" — a vector of internal species
concentrations sampled from the lipid field at the moment of formation. The
protocell evolves under two pressures:

  1. Growth pressure. Each step a protocell's "fitness" is computed from the
     diversity and concentration of its internal chemistry. Higher fitness
     → it grows; sustained high fitness → it divides into two protocells,
     each inheriting the parent's genome with stochastic mutation.

  2. Selection pressure. Each step a protocell's "decay" is computed from
     its size and age. Below a fitness threshold it shrinks; below a minimum
     size it dissolves back into chemical components.

This is the moment in the abiogenesis story where Darwinian dynamics
appear. Eigen and Schuster's hypercycle is the canonical theoretical
framework: a self-sustaining loop of replicators where each member catalyses
the formation of the next. The hypercycle is "evolutionarily stable" in a
way isolated replicators are not.

This implementation is a TOY. Real protocell evolution involves membrane
mechanics, internal RAF dynamics, and stochastic mutation rates that
collectively determine the error threshold. See the references for the
real math; this stage demonstrates the *concept* on top of Stage 3's
vesicles, not the rigorous biophysics.

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
    cx: float          # center x
    cy: float          # center y
    radius: float
    genome: np.ndarray  # vector of internal species concentrations, length S
    age: int = 0
    alive: bool = True

    def fitness(self) -> float:
        """Toy fitness: diversity (entropy) × total concentration.

        A protocell with one species at high concentration has low fitness
        (degenerate); a protocell with even mix has high fitness. This is
        a placeholder for proper RAF-based fitness — see PHASE2_BRUTAL §29.
        """
        g = self.genome
        total = float(g.sum())
        if total <= 1e-6:
            return 0.0
        p = g / total
        # Shannon entropy in nats; small log offset prevents log(0).
        entropy = float(-np.sum(p * np.log(p + 1e-12)))
        return entropy * total


@dataclass
class SelectionState:
    chemistry: np.ndarray             # H x W x S float32 — underlying chemistry
    cells: list[Protocell]            # population of protocells


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
    rng: random.Random = field(default_factory=random.Random)

    def init_state(self, width: int, height: int) -> SelectionState:
        chem = np.zeros((height, width, self.n_species), dtype=np.float32)
        # Seed each species with a Gray-Scott-style perturbation.
        chem[:, :, 0] = 1.0  # background substrate
        for s in range(1, self.n_species):
            cx = self.rng.randrange(width // 4, width * 3 // 4)
            cy = self.rng.randrange(height // 4, height * 3 // 4)
            r = max(2, min(width, height) // 16)
            chem[cy - r:cy + r, cx - r:cx + r, s] = 0.4

        # Initial protocell population: 3 cells with random genomes.
        cells = []
        for _ in range(3):
            cx = self.rng.uniform(width * 0.25, width * 0.75)
            cy = self.rng.uniform(height * 0.25, height * 0.75)
            genome = np.array([self.rng.uniform(0.05, 0.4) for _ in range(self.n_species)],
                              dtype=np.float32)
            cells.append(Protocell(cx=cx, cy=cy, radius=4.0, genome=genome))
        return SelectionState(chemistry=chem, cells=cells)

    def step(self, state: SelectionState) -> SelectionState:
        # Step background chemistry (using species 0 and 1 as the GS pair).
        u, v = state.chemistry[:, :, 0], state.chemistry[:, :, 1]
        for _ in range(self.substeps_per_frame):
            u, v = gray_scott_step(u, v, Du=self.Du, Dv=self.Dv, F=self.F, k=self.k)
        state.chemistry[:, :, 0], state.chemistry[:, :, 1] = u, v

        # Update each protocell.
        new_cells: list[Protocell] = []
        for cell in state.cells:
            if not cell.alive:
                continue
            cell.age += 1
            fit = cell.fitness()
            # Grow if fitness is high, shrink otherwise.
            cell.radius += 0.2 if fit > 1.0 else -0.1
            cell.radius = max(0.0, cell.radius)
            # Genome drift (mutation).
            cell.genome = cell.genome + np.array(
                [self.rng.gauss(0, self.mutation_rate) for _ in range(self.n_species)],
                dtype=np.float32,
            )
            np.clip(cell.genome, 0.0, 1.0, out=cell.genome)
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
            if (x - cell.cx) ** 2 + (y - cell.cy) ** 2 <= cell.radius ** 2:
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
            disc = (xx - cell.cx) ** 2 + (yy - cell.cy) ** 2 <= cell.radius ** 2
            ring = (
                ((xx - cell.cx) ** 2 + (yy - cell.cy) ** 2 <= cell.radius ** 2)
                & ((xx - cell.cx) ** 2 + (yy - cell.cy) ** 2 >= (cell.radius - 1) ** 2)
            )
            # Fitness → hue (low = red, high = green).
            fit = min(cell.fitness() / 5.0, 1.0)
            r = int(255 * (1 - fit))
            g = int(255 * fit)
            img[disc] = (r, g, 0)
            img[ring] = (255, 255, 255)
        return img

    def population(self, state: SelectionState) -> Mapping[str, int]:
        alive = [c for c in state.cells if c.alive]
        avg_fit = float(np.mean([c.fitness() for c in alive])) if alive else 0.0
        return {
            "protocells": len(alive),
            "avg_radius": int(round(np.mean([c.radius for c in alive]) if alive else 0)),
            "avg_fitness_x100": int(round(avg_fit * 100)),
        }

    def serialize_state(self, state: SelectionState) -> dict:
        return {
            "chemistry": np.round(state.chemistry, 4).tolist(),
            "cells": [
                {"cx": c.cx, "cy": c.cy, "radius": c.radius,
                 "genome": c.genome.tolist(), "age": c.age, "alive": c.alive}
                for c in state.cells
            ],
        }

    def deserialize_state(self, data: dict) -> SelectionState:
        chem = np.array(data["chemistry"], dtype=np.float32)
        cells = [Protocell(cx=c["cx"], cy=c["cy"], radius=c["radius"],
                           genome=np.array(c["genome"], dtype=np.float32),
                           age=c["age"], alive=c["alive"]) for c in data["cells"]]
        return SelectionState(chemistry=chem, cells=cells)

    def to_config(self) -> dict:
        return {"n_species": self.n_species, "mutation_rate": self.mutation_rate,
                "division_radius": self.division_radius, "decay_age": self.decay_age,
                "F": self.F, "k": self.k, "Du": self.Du, "Dv": self.Dv,
                "substeps_per_frame": self.substeps_per_frame}
