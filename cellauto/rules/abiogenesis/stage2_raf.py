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
    concentrations: np.ndarray  # shape (H, W, S), float32
    network: ReactionNetwork
    raf: frozenset[Reaction]  # the precomputed RAF


@dataclass
class AbiogenesisStage2RAF:
    name: str = "abiogenesis-stage2-raf"
    renderer_kind: str = "field"
    n_species: int = 8
    n_reactions: int = 16
    food_fraction: float = 0.4
    catalysis_fraction: float = 1.0  # P(a reaction is catalyzed); 0 -> no RAF can form (REV-03 control)
    food_supply: float = 0.05  # food concentration injected per cell per step
    diffusion_rate: float = 0.05
    rng: random.Random = field(default_factory=random.Random)

    def init_state(
        self,
        width: int,
        height: int,
        *,
        seed_field: np.ndarray | None = None,
    ) -> RAFState:
        # Build a random reaction network and locate its RAF. If the network
        # has no RAF, regenerate up to 5 times — RAFs are common above
        # connectivity ~2 (Kauffman 1986).
        for _ in range(5):
            network = random_reaction_network(
                n_species=self.n_species,
                n_reactions=self.n_reactions,
                food_fraction=self.food_fraction,
                catalysis_fraction=self.catalysis_fraction,
                rng=self.rng,
            )
            raf = find_raf(network)
            if raf:
                break
        else:
            network = random_reaction_network(
                n_species=self.n_species,
                n_reactions=self.n_reactions,
                food_fraction=self.food_fraction,
                catalysis_fraction=self.catalysis_fraction,
                rng=self.rng,
            )
            raf = frozenset()

        from cellauto.rules.abiogenesis.science import normalise_signal

        signal = normalise_signal(seed_field)
        c = np.zeros((height, width, self.n_species), dtype=np.float32)
        # Seed food species at low concentration everywhere — the "primordial
        # ocean has a uniform background concentration of small molecules"
        # idealization.
        for s in network.food_set:
            c[:, :, s] = 0.1
        if signal is not None:
            # G1: bump every species's concentration in proportion to the
            # upstream signal at each cell. Bright upstream regions (where
            # Stage 1 had Gray-Scott spots, where the vent had organic
            # synthesis, etc.) become high-chemistry-density regions for
            # the RAF to ignite from.
            bias = signal.astype(np.float32)[..., None]  # (H, W, 1)
            c += bias * (0.35 / max(self.n_species, 1))
        else:
            # Localised perturbation in the center to break symmetry.
            cx, cy = width // 2, height // 2
            r = max(3, min(width, height) // 12)
            c[cy - r : cy + r, cx - r : cx + r, :] += 0.3 / self.n_species
        return RAFState(concentrations=c, network=network, raf=raf)

    def extract_signal(self, state: RAFState) -> np.ndarray:
        """Downstream stages get the spatial density of RAF chemistry —
        the location of self-sustaining autocatalytic activity."""
        return state.concentrations.sum(axis=2).astype(np.float32)

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

        # Reactions. We fire the RAF reactions and highlight them as the
        # self-sustaining core. Note the RAF is a *topological* property of the
        # network (it is closed and food-generated); dynamic realizability is a
        # related but distinct notion (a CAF — constructively autocatalytic
        # set), since a mutually-catalysing pair may need one reaction to fire
        # uncatalysed first. Our mass-action term keeps a baseline (the 1.0
        # below) so that bootstrap firing can occur.
        for r in state.raf if state.raf else state.network.reactions:
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
        # Kauffman's connectivity metric: the mean number of reactions each
        # species catalyzes. RAFs appear with high probability once this
        # crosses roughly 1-2 (Hordijk & Steel 2004; Mossel & Steel 2005).
        net = state.network
        n_catalyzed = sum(1 for r in net.reactions if r.catalyst is not None)
        catalysis_level = n_catalyzed / net.n_species if net.n_species else 0.0
        return {
            "active_cells": active,
            "ignited_cells": ignited,
            "raf_size": len(state.raf),
            "network_size": len(state.network.reactions),
            "catalysis_level_x100": int(round(catalysis_level * 100)),
        }

    def serialize_state(self, state: RAFState) -> dict:
        # Snapshot the field AND the exact reaction network. Without the
        # network a resumed run would evolve under a *different* random
        # chemistry than the one that produced the saved field, making the
        # restored state scientifically meaningless. The RAF is derived from
        # the network, so we recompute it on load rather than storing it.
        net = state.network
        return {
            "concentrations": np.round(state.concentrations, 4).tolist(),
            "network": {
                "n_species": net.n_species,
                "food_set": sorted(net.food_set),
                "reactions": [
                    {
                        "reactants": list(r.reactants),
                        "product": r.product,
                        "rate_constant": r.rate_constant,
                        "catalyst": r.catalyst,
                    }
                    for r in net.reactions
                ],
            },
        }

    def deserialize_state(self, data: dict) -> RAFState:
        c = np.array(data["concentrations"], dtype=np.float32)
        net_data = data.get("network")
        if net_data is None:
            # Legacy snapshot without a stored network: fall back to a fresh
            # random one so the file still loads (pre-network-roundtrip saves).
            network = random_reaction_network(
                n_species=self.n_species,
                n_reactions=self.n_reactions,
                food_fraction=self.food_fraction,
                catalysis_fraction=self.catalysis_fraction,
                rng=self.rng,
            )
        else:
            reactions = tuple(
                Reaction(
                    reactants=(r["reactants"][0], r["reactants"][1]),
                    product=r["product"],
                    rate_constant=r["rate_constant"],
                    catalyst=r["catalyst"],
                )
                for r in net_data["reactions"]
            )
            network = ReactionNetwork(
                n_species=net_data["n_species"],
                reactions=reactions,
                food_set=frozenset(net_data["food_set"]),
            )
        return RAFState(concentrations=c, network=network, raf=find_raf(network))

    def to_config(self) -> dict:
        return {
            "n_species": self.n_species,
            "n_reactions": self.n_reactions,
            "food_fraction": self.food_fraction,
            "catalysis_fraction": self.catalysis_fraction,
            "food_supply": self.food_supply,
            "diffusion_rate": self.diffusion_rate,
        }
