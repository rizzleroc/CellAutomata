"""Shared scientific primitives for the abiogenesis pipeline.

Reaction networks, RAF (Reflexively Autocatalytic Food-generated) set
detection, and reaction-diffusion kernels live here so each stage can reuse
them without re-implementing the science.

The RAF algorithm is the Hordijk & Steel (2004) closure procedure — the
canonical way to detect Kauffman-style autocatalytic sets in a reaction
network.

References:
    Kauffman, S. A. (1986). Autocatalytic sets of proteins. J. Theor. Biol.,
        119, 1-24.
    Hordijk, W., & Steel, M. (2004). Detecting autocatalytic, self-sustaining
        sets in chemical reaction systems. J. Theor. Biol., 227, 451-461.
    Eigen, M., & Schuster, P. (1977). The hypercycle: a principle of natural
        self-organization. Naturwissenschaften, 64(11), 541-565.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np

# ---------------------------------------------------------------------------
# Reaction networks
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Reaction:
    """A reaction A + B -> C with optional catalyst K.

    `rate_constant` is the per-step probability that the reaction fires when
    all reactants (and the catalyst, if present) are colocated. We're working
    at toy-model scales, so we don't bother with Arrhenius temperature
    dependence — the rate is a single number per reaction.
    """
    reactants: tuple[int, int]
    product: int
    rate_constant: float = 0.1
    catalyst: int | None = None


@dataclass
class ReactionNetwork:
    """A set of species + a set of reactions over them.

    `food_set` is the subset of species considered freely available (the
    "food set" in Kauffman / Hordijk-Steel terminology). RAF detection finds
    subsets of reactions whose products can all be built from food + each
    other, with every reaction catalyzed by some species in the same set.
    """
    n_species: int
    reactions: tuple[Reaction, ...]
    food_set: frozenset[int]

    def producers_of(self, species: int) -> tuple[Reaction, ...]:
        return tuple(r for r in self.reactions if r.product == species)


def find_raf(network: ReactionNetwork) -> frozenset[Reaction]:
    """Hordijk-Steel closure: largest subset R of reactions where every
    reaction's reactants and catalyst are either in the food set or produced
    by some other reaction in R.

    Iteratively prune reactions whose requirements aren't met until the set
    stabilizes. The result is the maximal RAF — empty if none exists.
    """
    candidates = set(network.reactions)
    while True:
        # The "closure" reachable from food + current candidates' products.
        producible = set(network.food_set)
        producible.update(r.product for r in candidates)
        next_candidates = {r for r in candidates if _viable(r, producible)}
        if next_candidates == candidates:
            break
        candidates = next_candidates
    return frozenset(candidates)


def _viable(r: Reaction, producible: set[int]) -> bool:
    """A reaction is viable iff all reactants AND any catalyst are producible."""
    for reactant in r.reactants:
        if reactant not in producible:
            return False
    if r.catalyst is not None and r.catalyst not in producible:
        return False
    return True


def random_reaction_network(n_species: int, n_reactions: int, food_fraction: float,
                            rng: random.Random) -> ReactionNetwork:
    """Construct a random reaction network for sandbox experiments.

    A random subset of species are flagged as food. Random A+B->C reactions
    are generated; ~half are catalyzed by a random other species. Kauffman's
    1986 paper analyses exactly this construction and shows RAFs emerge
    spontaneously above a threshold connectivity.
    """
    food_size = max(1, int(n_species * food_fraction))
    food_set = frozenset(rng.sample(range(n_species), food_size))
    reactions: list[Reaction] = []
    for _ in range(n_reactions):
        a, b = rng.sample(range(n_species), 2)
        c = rng.randrange(n_species)
        catalyst = rng.randrange(n_species) if rng.random() < 0.5 else None
        rate = round(rng.uniform(0.05, 0.5), 3)
        reactions.append(Reaction(reactants=(a, b), product=c,
                                  rate_constant=rate, catalyst=catalyst))
    return ReactionNetwork(n_species=n_species, reactions=tuple(reactions),
                           food_set=food_set)


# ---------------------------------------------------------------------------
# Reaction-diffusion kernels
# ---------------------------------------------------------------------------


def laplacian_5pt(arr: np.ndarray) -> np.ndarray:
    """5-point stencil Laplacian with toroidal wrap.

    For a function f on a grid, the discrete Laplacian approximates ∇²f.
    Toroidal wrap is the standard textbook simplification — it avoids
    boundary-condition headaches.
    """
    return (
        np.roll(arr, 1, axis=0) + np.roll(arr, -1, axis=0)
        + np.roll(arr, 1, axis=1) + np.roll(arr, -1, axis=1)
        - 4 * arr
    )


def gray_scott_step(u: np.ndarray, v: np.ndarray, *,
                    Du: float = 0.16, Dv: float = 0.08,
                    F: float = 0.035, k: float = 0.065,
                    dt: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """One forward-Euler step of the Gray-Scott reaction-diffusion system.

    The Gray-Scott model:
        ∂u/∂t = D_u ∇²u  -  u v² + F (1 - u)
        ∂v/∂t = D_v ∇²v  +  u v² - (F + k) v

    Parameters (F, k) in the ranges (0.01-0.1, 0.04-0.075) produce a rich
    parameter landscape — Pearson (1993) catalogued the regimes (mitosis,
    spots, waves, fingers, U-skate world).

    For a guided tour, F=0.035, k=0.065 gives clean self-replicating spots
    that look astonishingly like dividing protocells. F=0.04, k=0.06 gives
    long meandering stripes.
    """
    uvv = u * v * v
    u_new = u + dt * (Du * laplacian_5pt(u) - uvv + F * (1.0 - u))
    v_new = v + dt * (Dv * laplacian_5pt(v) + uvv - (F + k) * v)
    np.clip(u_new, 0.0, 1.0, out=u_new)
    np.clip(v_new, 0.0, 1.0, out=v_new)
    return u_new, v_new


# Pearson's parameter regions, useful as presets.
GRAY_SCOTT_PRESETS: dict[str, tuple[float, float]] = {
    "spots":    (0.035, 0.065),
    "stripes":  (0.04, 0.06),
    "mitosis":  (0.0367, 0.0649),
    "waves":    (0.014, 0.045),
    "labyrinth":(0.039, 0.058),
}


# ---------------------------------------------------------------------------
# Lipid self-assembly (toy)
# ---------------------------------------------------------------------------


def vesicle_indicator(amphiphile_concentration: np.ndarray,
                      threshold: float = 0.6) -> np.ndarray:
    """Threshold-based protocell marker.

    Real lipid bilayers self-assemble above a critical micelle concentration
    (CMC). Below CMC the lipids stay dispersed; above CMC they cluster into
    bilayers and eventually close into vesicles. This toy implementation
    just checks where the amphiphile concentration exceeds a threshold —
    sufficient for a visual demo, way short of the real fluid mechanics.

    For a real implementation see Lipowsky & Sackmann's *Structure and
    Dynamics of Membranes* (1995) or Szostak's recent protocell work.
    """
    return amphiphile_concentration >= threshold
