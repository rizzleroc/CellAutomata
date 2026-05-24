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


def _closure(food: frozenset[int], reactions: set[Reaction]) -> set[int]:
    """Food-generated closure — Hordijk & Steel (2004) Algorithm 2.

    Start from the food set and repeatedly add a reaction's product *only*
    once both of its reactants are already producible, iterating to a
    fixpoint. The key invariant the older one-pass version got wrong: a
    product is reachable only when the reaction that makes it can actually
    run, so producibility must propagate layer by layer from the food set —
    you cannot assume every candidate's product is available up front.
    """
    producible = set(food)
    changed = True
    while changed:
        changed = False
        for r in reactions:
            if r.product not in producible and all(reactant in producible for reactant in r.reactants):
                producible.add(r.product)
                changed = True
    return producible


def find_raf(network: ReactionNetwork) -> frozenset[Reaction]:
    """Maximal RAF via the Hordijk-Steel closure.

    Hordijk & Steel (2004); formalized in Hordijk (2023), arXiv:2303.01809,
    Algorithms 1 & 2. A Reflexively Autocatalytic Food-generated (RAF) set R
    is the largest set of reactions such that, using only the food set plus
    the products of reactions in R, every reaction in R has (a) both reactants
    producible and (b) at least one catalyst that is itself producible.

    The "reflexively autocatalytic" requirement makes catalysis mandatory: an
    uncatalyzed reaction can never belong to a RAF (that is the "R"). We
    recompute the food-generated closure of the current candidate set, prune
    any reaction whose reactants or catalyst fall outside that closure, and
    repeat until the set stabilizes. Returns the empty set if no RAF exists.
    """
    candidates = set(network.reactions)
    while True:
        producible = _closure(network.food_set, candidates)
        next_candidates = {r for r in candidates if _viable(r, producible)}
        if next_candidates == candidates:
            break
        candidates = next_candidates
    return frozenset(candidates)


def _viable(r: Reaction, producible: set[int]) -> bool:
    """RAF-viable iff both reactants are producible AND the reaction has a
    catalyst that is itself producible. Catalysis is mandatory (the "R" in
    RAF) — an uncatalyzed reaction is excluded by definition, even if its
    reactants are available."""
    if any(reactant not in producible for reactant in r.reactants):
        return False
    if r.catalyst is None or r.catalyst not in producible:
        return False
    return True


def random_reaction_network(
    n_species: int, n_reactions: int, food_fraction: float, rng: random.Random
) -> ReactionNetwork:
    """Construct a random reaction network for sandbox experiments.

    A random subset of species are flagged as food. Random A+B->C reactions
    are generated, each catalyzed by a random species. Catalysis is assigned
    to every reaction because under the formal RAF definition an uncatalyzed
    reaction can never belong to a RAF (Hordijk & Steel 2004) — leaving half
    the reactions uncatalyzed, as an earlier version did, simply made them
    dead weight that could never join an autocatalytic set. Kauffman's 1986
    paper analyses exactly this construction and shows RAFs emerge
    spontaneously once the average catalysis level crosses a threshold of
    roughly one to two reactions catalyzed per species.
    """
    food_size = max(1, int(n_species * food_fraction))
    food_set = frozenset(rng.sample(range(n_species), food_size))
    reactions: list[Reaction] = []
    for _ in range(n_reactions):
        a, b = rng.sample(range(n_species), 2)
        c = rng.randrange(n_species)
        catalyst = rng.randrange(n_species)
        rate = round(rng.uniform(0.05, 0.5), 3)
        reactions.append(Reaction(reactants=(a, b), product=c, rate_constant=rate, catalyst=catalyst))
    return ReactionNetwork(n_species=n_species, reactions=tuple(reactions), food_set=food_set)


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
        np.roll(arr, 1, axis=0)
        + np.roll(arr, -1, axis=0)
        + np.roll(arr, 1, axis=1)
        + np.roll(arr, -1, axis=1)
        - 4 * arr
    )


def gray_scott_step(
    u: np.ndarray,
    v: np.ndarray,
    *,
    Du: float = 0.16,
    Dv: float = 0.08,
    F: float = 0.035,
    k: float = 0.065,
    dt: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
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
    "spots": (0.035, 0.065),
    "stripes": (0.04, 0.06),
    "mitosis": (0.0367, 0.0649),
    "waves": (0.014, 0.045),
    "labyrinth": (0.039, 0.058),
}


# ---------------------------------------------------------------------------
# Lipid self-assembly
# ---------------------------------------------------------------------------

# Measured critical aggregation concentrations (mM, ~pH 7-8) for
# prebiotically-plausible single-chain fatty-acid amphiphiles, drawn from the
# Szostak/Deamer protocell literature. Chain length sets the scale: short
# chains need very high concentrations to aggregate; long chains aggregate at
# trace levels. The prebiotic "sweet spot" is C8-C10 monocarboxylic acids —
# the very species Deamer extracted from the Murchison meteorite that form
# vesicles under plausible early-Earth conditions. The critical *vesicle*
# concentration (CVC) is typically a few-fold below the CMC.
#
#   Deamer, D. W. (2008). How leaky were primitive cells? Nature 454, 37-38.
#   Hanczyc, Fujikawa & Szostak (2003). Science 302, 618-622.
#   Apel, Deamer & Mautner (2002). Biochim. Biophys. Acta 1559, 1-9.
AMPHIPHILE_CMC_MM: dict[str, float] = {
    "octanoic acid (C8)": 250.0,
    "decanoic acid (C10)": 85.0,
    "dodecanoic acid (C12)": 12.0,
    "oleic acid (C18:1)": 0.1,
}


# ---------------------------------------------------------------------------
# Pipeline state hand-off — the G1 fix
# ---------------------------------------------------------------------------


def normalise_signal(signal: np.ndarray | None) -> np.ndarray | None:
    """Min-max normalise a 2D signal to [0, 1]; pass through None.

    Used by the pipeline-coupling glue. A stage's ``extract_signal`` may
    return raw concentrations / fitness values / occupancy counts on any
    scale; downstream stages should not have to know that scale. Normalising
    once here means every consumer sees the same dynamic range.
    """
    if signal is None:
        return None
    arr = np.asarray(signal, dtype=np.float32)
    lo, hi = float(arr.min()), float(arr.max())
    if hi - lo < 1e-9:
        return np.zeros_like(arr, dtype=np.float32)
    return (arr - lo) / (hi - lo)


def seed_from_signal(
    signal: np.ndarray | None,
    *,
    shape: tuple[int, int],
    lo: float = 0.0,
    hi: float = 1.0,
    fallback: np.ndarray | None = None,
) -> np.ndarray | None:
    """Build an initial-state field from an incoming normalised signal.

    Given a signal in roughly [0, 1] (after ``normalise_signal``), produce a
    target field of ``shape`` in [lo, hi] — bright signal pixels become
    ``hi``-valued, dim ones become ``lo``-valued. If ``signal`` is None we
    return ``fallback`` (which is itself allowed to be None — the caller is
    then expected to use its own default init).

    This is the *common case* of pipeline state hand-off: the previous
    stage's interesting locations become the next stage's high-energy seed.
    """
    if signal is None:
        return fallback
    arr = np.asarray(signal, dtype=np.float32)
    if arr.shape != shape:
        # Resize via PIL when shapes mismatch (rare — only triggered when a
        # snapshot is loaded into a different grid size).
        from PIL import Image

        img = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
        img = img.resize((shape[1], shape[0]), Image.Resampling.BILINEAR)
        arr = np.asarray(img, dtype=np.float32) / 255.0
    return (lo + (hi - lo) * np.clip(arr, 0.0, 1.0)).astype(np.float32)


def vesicle_indicator(amphiphile_concentration: np.ndarray, threshold: float = 0.6) -> np.ndarray:
    """Critical-micelle-concentration membrane marker.

    Real lipid bilayers self-assemble above a critical micelle concentration
    (CMC): below it the amphiphiles stay dispersed; above it they cluster into
    bilayers and eventually close into vesicles. ``AMPHIPHILE_CMC_MM`` lists
    measured CMCs for the prebiotically-relevant fatty acids. The simulation's
    field is in normalized units calibrated so 1.0 corresponds to the chosen
    amphiphile's CMC, and ``threshold`` is therefore that normalized value; we
    flag where concentration meets or exceeds it.

    This is a thermodynamic threshold model — it captures the existence of a
    sharp self-assembly transition but not the fluid mechanics of the bilayer
    (curvature elasticity, surface tension). For the full treatment see
    Lipowsky & Sackmann's *Structure and Dynamics of Membranes* (1995).
    """
    return amphiphile_concentration >= threshold
