"""RNA world — spatial quasispecies with a visible Eigen error catastrophe.

Walter Gilbert's 1986 "RNA world" hypothesis holds that RNA, acting as both
genotype (template) and catalyst (ribozyme), preceded the DNA/protein world.
The central quantitative constraint on any such self-replicator is Manfred
Eigen's quasispecies theory (1971): a master sequence of length L can only be
maintained against copying errors if the per-base error rate stays below the
**error threshold**. For a single-peak fitness landscape (the master replicates
with superiority σ, everything else with rate 1) that threshold is

    ε_c = ln(σ) / L

Below ε_c the population is a "quasispecies" — a cloud centred on the master.
Above it the master is lost and the population melts into random sequences:
the **error catastrophe**. This stage makes that transition something you can
watch: drag the error-rate slider past ε_c and the bright master colonies
dissolve into dark noise.

This is a spatial Eigen model: each grid cell holds an RNA strand (a sequence
over a 4-letter alphabet) or is empty. Empty cells are colonised by an
occupied neighbour chosen in proportion to its fitness (selection), and the
copy is made base-by-base with per-base error ε (mutation). Occupied cells die
at a fixed rate. The master sequence is the all-zero strand; cells are coloured
by Hamming distance to it.

References:
    Gilbert, W. (1986). The RNA World. Nature, 319, 618.
    Eigen, M. (1971). Selforganization of matter and the evolution of
        biological macromolecules. Naturwissenschaften, 58(10), 465-523.
    Eigen, M., & Schuster, P. (1977). The hypercycle. Naturwissenschaften,
        64(11), 541-565.
    Spiegelman, S. (1971). An approach to the experimental analysis of
        precellular evolution. Q. Rev. Biophys., 4(2-3), 213-253.
    Joyce, G. F. (2002). The antiquity of RNA-based evolution. Nature,
        418(6894), 214-221.
"""

from __future__ import annotations

import math
import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.renderer import cmap_viridis

# Real RNA bases — the 4-letter alphabet maps directly onto the canonical
# nucleotide identities used by every modern organism. The all-zero "master"
# sequence is poly-A; mutant strands appear as mixes of the four bases.
RNA_BASES: tuple[str, str, str, str] = ("A", "U", "G", "C")


@dataclass
class RNAWorldState:
    seqs: np.ndarray  # (H, W, L) int8 — the strand in each cell (valid where occupied)
    occupied: np.ndarray  # (H, W) bool


@dataclass
class AbiogenesisStageRNAWorld:
    name: str = "abiogenesis-rna-world"
    renderer_kind: str = "field"
    seq_length: int = 16  # L — strand length
    alphabet: int = 4  # A, U, G, C
    superiority: float = 10.0  # σ — master replication advantage (single-peak landscape)
    error_rate: float = 0.02  # ε — per-base copy error probability
    death_rate: float = 0.1
    repro_prob: float = 0.6  # base chance an empty cell with neighbours is colonised
    seed_fraction: float = 0.12
    rng: random.Random = field(default_factory=random.Random)

    @property
    def error_threshold(self) -> float:
        """Eigen single-peak per-base error threshold ε_c = ln(σ) / L."""
        return math.log(self.superiority) / self.seq_length

    # ---- Rule protocol -----------------------------------------------------

    def init_state(self, width: int, height: int) -> RNAWorldState:
        L = self.seq_length
        seqs = np.zeros((height, width, L), dtype=np.int8)  # master = all zeros
        occupied = np.zeros((height, width), dtype=bool)
        for y in range(height):
            for x in range(width):
                if self.rng.random() < self.seed_fraction:
                    occupied[y, x] = True  # seed wild-type (master) colonisers
        return RNAWorldState(seqs=seqs, occupied=occupied)

    def _fitness(self, seq: np.ndarray) -> float:
        # Single-peak landscape: the master (all-zero) strand replicates σ×
        # faster; every other sequence replicates at rate 1.
        return self.superiority if not seq.any() else 1.0

    def _mutated_copy(self, seq: np.ndarray) -> np.ndarray:
        child = seq.copy()
        eps = self.error_rate
        for i in range(self.seq_length):
            if self.rng.random() < eps:
                # Replace with one of the (A-1) other symbols.
                delta = self.rng.randrange(1, self.alphabet)
                child[i] = (child[i] + delta) % self.alphabet
        return child

    def step(self, state: RNAWorldState) -> RNAWorldState:
        H, W, _ = state.seqs.shape
        occ = state.occupied
        seqs = state.seqs
        new_occ = occ.copy()
        new_seqs = seqs.copy()

        # Death.
        for y in range(H):
            for x in range(W):
                if occ[y, x] and self.rng.random() < self.death_rate:
                    new_occ[y, x] = False

        # Replication: each empty cell may be colonised by a fitness-weighted
        # occupied neighbour (selection), copied with per-base error (mutation).
        for y in range(H):
            for x in range(W):
                if occ[y, x] or new_occ[y, x]:
                    continue
                parents: list[tuple[int, int]] = []
                weights: list[float] = []
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and occ[ny, nx]:
                            parents.append((ny, nx))
                            weights.append(self._fitness(seqs[ny, nx]))
                if not parents:
                    continue
                if self.rng.random() >= self.repro_prob:
                    continue
                py, px = self.rng.choices(parents, weights=weights, k=1)[0]
                new_seqs[y, x] = self._mutated_copy(seqs[py, px])
                new_occ[y, x] = True

        state.seqs = new_seqs
        state.occupied = new_occ
        return state

    def _distance_field(self, state: RNAWorldState) -> np.ndarray:
        # Hamming distance to the all-zero master sequence.
        return (state.seqs != 0).sum(axis=2).astype(np.float32)

    def render_cell(self, state: RNAWorldState, x: int, y: int) -> tuple[str, str]:
        if not state.occupied[y, x]:
            return "#000000", "rect"
        dist = int((state.seqs[y, x] != 0).sum())
        t = 1.0 - dist / self.seq_length
        gray = int(np.clip(t * 255, 0, 255))
        return f"#{gray:02x}{gray:02x}{gray:02x}", "rect"

    def render_rgb(self, state: RNAWorldState) -> np.ndarray:
        dist = self._distance_field(state)
        proximity = 1.0 - dist / self.seq_length  # 1 = master (bright), 0 = far mutant
        img = cmap_viridis(proximity).copy()
        img[~state.occupied] = (0, 0, 0)
        return img

    def population(self, state: RNAWorldState) -> Mapping[str, int]:
        occ = state.occupied
        total = int(occ.sum())
        dist = self._distance_field(state)
        master = int((occ & (dist == 0)).sum())
        mean_dist = float(dist[occ].mean()) if total else 0.0
        master_pct = int(round(100 * master / total)) if total else 0
        return {
            "strands": total,
            "master_pct": master_pct,
            "mean_distance_x10": int(round(mean_dist * 10)),
            "error_rate_x1000": int(round(self.error_rate * 1000)),
            "error_threshold_x1000": int(round(self.error_threshold * 1000)),
        }

    def serialize_state(self, state: RNAWorldState) -> dict:
        return {
            "seqs": state.seqs.tolist(),
            "occupied": state.occupied.astype(int).tolist(),
        }

    def deserialize_state(self, data: dict) -> RNAWorldState:
        return RNAWorldState(
            seqs=np.array(data["seqs"], dtype=np.int8),
            occupied=np.array(data["occupied"], dtype=bool),
        )

    def to_config(self) -> dict:
        return {
            "seq_length": self.seq_length,
            "alphabet": self.alphabet,
            "superiority": self.superiority,
            "error_rate": self.error_rate,
            "death_rate": self.death_rate,
            "repro_prob": self.repro_prob,
            "seed_fraction": self.seed_fraction,
        }
