"""Stage 2 — Autocatalytic sets (Kauffman RAFs).

Builds on Stage 1's continuous chemistry by adding a discrete reaction
network. Each cell of the grid holds concentrations of `n_species` chemical
species. A shared random reaction network of A+B→C reactions (some
catalyzed) governs how species transform into each other.

At init time we run the Hordijk-Steel closure algorithm on the network and
display the resulting RAF (Reflexively Autocatalytic Food-generated set).
RAFs are the formal mathematical object that captures Kauffman's intuition
that life starts when chemistry crosses a closure threshold — once enough
reactions catalyze each other in a closed loop, you get spontaneous
self-amplification.

Visually: when a local region of the grid happens to have all the food-set
species AND the RAF reactions can fire, that region ignites with rising
concentrations. The video looks like fires spreading across the grid —
literally autocatalytic amplification.

References:
    Kauffman, S. A. (1986). Autocatalytic sets of proteins. J. Theor. Biol.,
        119, 1-24.
    Kauffman, S. A. (1993). The Origins of Order. Oxford University Press.
    Hordijk, W., & Steel, M. (2004). Detecting autocatalytic, self-sustaining
        sets in chemical reaction systems. J. Theor. Biol., 227, 451-461.
    Hordijk, W., Steel, M., & Kauffman, S. A. (2012). The structure of
        autocatalytic sets: evolvability, enablement, and emergence. Acta
        Biotheoretica, 60(4), 379-392.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.renderer import cmap_viridis
from cellauto.rules.abiogenesis.science import (
    Reaction,
    ReactionNetwork,
    find_raf,
    laplacian_5pt,
    random_reaction_network,
)


@dataclass
class RAFState:
    concentrations: np.ndarray   # shape (H, W, S), float32
    network: ReactionNetwork
    raf: frozenset[Reaction]     # the precomputed RAF


@dataclass
class AbiogenesisStage2RAF:
    name: str = "abiogenesis-stage2-raf"
    renderer_kind: str = "field"
    n_species: int = 8
    n_reactions: int = 16
    food_fraction: float = 0.4
    food_supply: float = 0.05    # food concentration injected per cell per step
    diffusion_rate: float = 0.05
    rng: random.Random = field(default_factory=random.Random)

    def init_state(self, width: int, height: int) -> RAFState:
        # Build a random reaction network and locate its RAF. If the network
        # has no RAF, regenerate up to 5 times — RAFs are common above
        # connectivity ~2 (Kauffman 1986).
        for _ in range(5):
            network = random_reaction_network(
                n_species=self.n_species,
                n_reactions=self.n_reactions,
                food_fraction=self.food_fraction,
                rng=self.rng,
            )
            raf = find_raf(network)
            if raf:
                break
        else:
            network = random_reaction_network(
                n_species=self.n_species, n_reactions=self.n_reactions,
                food_fraction=self.food_fraction, rng=self.rng,
            )
            raf = frozenset()

        c = np.zeros((height, width, self.n_species), dtype=np.float32)
        # Seed food species at low concentration everywhere — the "primordial
        # ocean has a uniform background concentration of small molecules"
        # idealization.
        for s in network.food_set:
            c[:, :, s] = 0.1
        # Localised perturbation in the center to break symmetry.
        cx, cy = width // 2, height // 2
        r = max(3, min(width, height) // 12)
        c[cy - r:cy + r, cx - r:cx + r, :] += 0.3 / self.n_species
        return RAFState(concentrations=c, network=network, raf=raf)

    def step(self, state: RAFState) -> RAFState:
        c = state.concentrations
        H, W, S = c.shape
        new_c = c.copy()

        # Diffusion (Laplacian for each species).
        for s in range(S):
            new_c[:, :, s] += self.diffusion_rate * laplacian_5pt(c[:, :, s])

        # Food injection.
        for s in state.network.food_set:
            new_c[:, :, s] += self.food_supply
            new_c[:, :, s] *= 0.995  # mild outflow to keep totals bounded

        # Reactions. We run only the RAF reactions — those are the ones that
        # form a closed self-sustaining loop. Non-RAF reactions are present
        # in the network but can't fire indefinitely without external input.
        for r in (state.raf if state.raf else state.network.reactions):
            a, b = r.reactants
            ca = new_c[:, :, a]
            cb = new_c[:, :, b]
            # Mass-action rate: r = k * [A] * [B], modulated by catalyst if any.
            rate = r.rate_constant * ca * cb
            if r.catalyst is not None:
                rate = rate * (1.0 + 5.0 * new_c[:, :, r.catalyst])
            # Apply: consume A and B, produce C.
            dt = 0.1
            delta = np.minimum(rate * dt, np.minimum(ca, cb))
            new_c[:, :, a] -= delta
            new_c[:, :, b] -= delta
            new_c[:, :, r.product] += delta

        np.clip(new_c, 0.0, None, out=new_c)
        state.concentrations = new_c
        return state

    def render_cell(self, state: RAFState, x: int, y: int) -> tuple[str, str]:
        intensity = float(state.concentrations[y, x].sum()) / self.n_species
        gray = int(np.clip(intensity * 255, 0, 255))
        return f"#{gray:02x}{gray:02x}{gray:02x}", "rect"

    def render_rgb(self, state: RAFState) -> np.ndarray:
        # Sum across species → "total chemistry density." Viridis ramp shows
        # autocatalytic hot spots in yellow against a dark background.
        density = state.concentrations.sum(axis=2)
        m = max(float(density.max()), 1e-6)
        return cmap_viridis(density / m)

    def population(self, state: RAFState) -> Mapping[str, int]:
        active = int((state.concentrations.sum(axis=2) > 0.5).sum())
        ignited = int((state.concentrations.sum(axis=2) > 2.0).sum())
        return {
            "active_cells": active,
            "ignited_cells": ignited,
            "raf_size": len(state.raf),
            "network_size": len(state.network.reactions),
        }

    def serialize_state(self, state: RAFState) -> dict:
        # Reaction network identity is in to_config; here we just snapshot the field.
        return {"concentrations": np.round(state.concentrations, 4).tolist()}

    def deserialize_state(self, data: dict) -> RAFState:
        # We can't fully restore the random network without saving it; rebuild
        # one from current config so concentrations make sense, mark raf empty.
        # (Full network round-trip is item P1-4 in PHASE2_BRUTAL.)
        c = np.array(data["concentrations"], dtype=np.float32)
        network = random_reaction_network(
            n_species=self.n_species, n_reactions=self.n_reactions,
            food_fraction=self.food_fraction, rng=self.rng,
        )
        return RAFState(concentrations=c, network=network, raf=find_raf(network))

    def to_config(self) -> dict:
        return {"n_species": self.n_species, "n_reactions": self.n_reactions,
                "food_fraction": self.food_fraction, "food_supply": self.food_supply,
                "diffusion_rate": self.diffusion_rate}
