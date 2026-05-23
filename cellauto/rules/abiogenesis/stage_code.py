"""Origin of the genetic code — coevolution of message and code.

The deepest unsolved problem at the chemistry-to-biology boundary is the origin
of the **genetic code** itself: how did the (near-)universal mapping from
nucleotide codons to amino acids ever come to exist, and why is it shared by
every organism on Earth? Three classic answers:

* **Stereochemical** (Woese): codons and their amino acids are physically
  matched — the code reflects molecular complementarity.
* **Coevolution** (Wong; Vetsigian, Woese & Goldenfeld 2006): the code and
  the messages it interprets coevolve, and *innovation sharing* (horizontal
  gene transfer between proto-organisms with similar codes) drives the
  population to converge on a single universal code.
* **Frozen accident** (Crick 1968): whatever code happened first locked in,
  because changing it later is catastrophic.

This stage models the **coevolution** account. Each cell on the grid carries
two things at once:

* an RNA-like ``strand`` of codons (the message), and
* its own ``code`` — a private mapping from codon symbol to amino-acid symbol.

Every cell decodes its own strand through its own code, producing a peptide;
fitness is how well that peptide matches a fixed **target catalyst** (the
acetyl-CoA / Wood-Ljungdahl pathway, say — the chemistry the cell needs).
Empty cells are colonised by fitness-weighted occupied neighbours, copying
both the strand (with per-base mutation) and the code (with rare swaps).
Crucially, a cell can only "use" a *donor* cell's strand effectively if the
donor's code is compatible — so any code that happens to make a more useful
peptide spreads, and the population converges on a shared code purely through
selection. That convergence is the emergence of the universal genetic code.

What this captures: the coevolutionary dynamics of message and code, and the
population-level convergence onto a shared code through selection.
What it cuts: actual stereochemistry, actual translation, actual ribosomes,
and the specific historical contingencies that shaped the canonical code.

References:
    Crick, F. H. C. (1968). The origin of the genetic code. J. Mol. Biol.,
        38(3), 367-379.
    Woese, C. R. (1965). On the evolution of the genetic code. PNAS, 54,
        1546-1552.
    Wong, J. T.-F. (1975). A co-evolution theory of the genetic code. PNAS,
        72(5), 1909-1912.
    Vetsigian, K., Woese, C., & Goldenfeld, N. (2006). Collective evolution
        and the genetic code. PNAS, 103(28), 10696-10701.
    Koonin, E. V. (2017). Frozen accident pushing 50: stereochemistry,
        expansion, and chance in the evolution of the genetic code. Life,
        7(2), 22.
"""

from __future__ import annotations

import math
import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.renderer import cmap_viridis

# Real bases and amino acids. The 4 codon symbols map to the four RNA bases;
# the 4 amino-acid slots map to **GADV** — Ikehara's (2002) proposed proto-code
# of the four amino acids most readily made under prebiotic conditions (all
# four appear in Miller's 1953 spark-discharge yields). The default target
# peptide encodes a GADV protein motif.
CODON_BASES: tuple[str, str, str, str] = ("A", "U", "G", "C")
AMINO_ACIDS: tuple[str, str, str, str] = ("Gly", "Ala", "Asp", "Val")


@dataclass
class GeneticCodeState:
    occupied: np.ndarray  # (H, W) bool
    strand: np.ndarray  # (H, W, L) int8 — codon sequence; entries in [0, n_codons)
    code: np.ndarray  # (H, W, n_codons) int8 — codon→amino-acid table per cell


@dataclass
class AbiogenesisStageGeneticCode:
    name: str = "abiogenesis-genetic-code"
    renderer_kind: str = "field"
    strand_length: int = 6  # codons per strand (and length of the target peptide)
    n_codons: int = 4  # codon alphabet size
    n_amino: int = 4  # amino-acid alphabet size
    target_peptide: tuple[int, ...] = (0, 1, 2, 3, 0, 1)
    death_rate: float = 0.10
    repro_prob: float = 0.6
    strand_mutation: float = 0.04  # per-codon mutation when copying the strand
    code_mutation: float = 0.01  # per-position swap when copying the code
    seed_fraction: float = 0.35
    rng: random.Random = field(default_factory=random.Random)

    @property
    def error_threshold(self) -> float:
        """Eigen analog: per-symbol error rate above which the master message
        cannot be maintained against copy errors, ≈ ln(σ)/L. For the default
        single-peak landscape we approximate σ ≈ n_amino so the threshold is
        a convenient handle (~0.23 at the defaults)."""
        return math.log(max(2.0, float(self.n_amino))) / self.strand_length

    # ---- Rule protocol ----------------------------------------------------

    def init_state(self, width: int, height: int) -> GeneticCodeState:
        gen = np.random.default_rng(self.rng.randrange(2**31))
        occupied = gen.random((height, width)) < self.seed_fraction
        strand = gen.integers(0, self.n_codons, size=(height, width, self.strand_length), dtype=np.int8)
        # Each cell starts with a private *random* codon table. No universal
        # code exists yet — its emergence is what the simulation should show.
        code = gen.integers(0, self.n_amino, size=(height, width, self.n_codons), dtype=np.int8)
        return GeneticCodeState(occupied=occupied, strand=strand, code=code)

    def _peptides(self, state: GeneticCodeState) -> np.ndarray:
        """For each cell, decode its own strand with its own code. Returns
        an (H, W, L) array of amino-acid indices."""
        # `np.take_along_axis` over the codon axis: at each (y, x), the L
        # codons in strand index into the n_codons-entry table in code.
        return np.take_along_axis(state.code, state.strand.astype(np.int64), axis=2)

    def _fitness_field(self, state: GeneticCodeState) -> np.ndarray:
        target = np.array(self.target_peptide[: self.strand_length], dtype=np.int8)
        if target.size < self.strand_length:
            # Pad shorter targets with zeros so the dimensions line up.
            pad = np.zeros(self.strand_length - target.size, dtype=np.int8)
            target = np.concatenate([target, pad])
        peptide = self._peptides(state)
        matches = (peptide == target).sum(axis=2)
        return matches.astype(np.float32) / self.strand_length

    def _mutated_strand(self, strand: np.ndarray) -> np.ndarray:
        out = strand.copy()
        for i in range(self.strand_length):
            if self.rng.random() < self.strand_mutation:
                delta = self.rng.randrange(1, self.n_codons)
                out[i] = (out[i] + delta) % self.n_codons
        return out

    def _mutated_code(self, code: np.ndarray) -> np.ndarray:
        out = code.copy()
        for i in range(self.n_codons):
            if self.rng.random() < self.code_mutation:
                # Reassign one codon to a different amino acid (a code swap).
                delta = self.rng.randrange(1, self.n_amino)
                out[i] = (out[i] + delta) % self.n_amino
        return out

    def step(self, state: GeneticCodeState) -> GeneticCodeState:
        H, W, _ = state.strand.shape
        occ = state.occupied
        fit = self._fitness_field(state)
        new_occ = occ.copy()
        new_strand = state.strand.copy()
        new_code = state.code.copy()

        # Death — fitness-weighted survival: low-fitness cells die preferentially.
        for y in range(H):
            for x in range(W):
                if occ[y, x] and self.rng.random() < self.death_rate * (1.0 - 0.7 * fit[y, x]):
                    new_occ[y, x] = False

        # Replication: each empty cell is potentially colonised by a
        # fitness-weighted occupied Moore neighbour.
        for y in range(H):
            for x in range(W):
                if occ[y, x] or new_occ[y, x]:
                    continue
                if self.rng.random() >= self.repro_prob:
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
                            weights.append(0.05 + float(fit[ny, nx]))
                if not parents:
                    continue
                py, px = self.rng.choices(parents, weights=weights, k=1)[0]
                new_strand[y, x] = self._mutated_strand(state.strand[py, px])
                new_code[y, x] = self._mutated_code(state.code[py, px])
                new_occ[y, x] = True

        state.occupied = new_occ
        state.strand = new_strand
        state.code = new_code
        return state

    def _code_consensus(self, state: GeneticCodeState) -> float:
        """Fraction of the *population* that shares the modal codon→amino-acid
        assignment at each position, averaged over codons. 1.0 = universal
        code; 1/n_amino = totally random."""
        occ = state.occupied
        if not occ.any():
            return 0.0
        total = 0.0
        for c in range(self.n_codons):
            assignments = state.code[..., c][occ]
            counts = np.bincount(assignments, minlength=self.n_amino)
            total += float(counts.max()) / float(assignments.size)
        return total / self.n_codons

    # ---- Rendering --------------------------------------------------------

    def render_cell(self, state: GeneticCodeState, x: int, y: int) -> tuple[str, str]:
        if not state.occupied[y, x]:
            return "#000000", "rect"
        peptide = np.take_along_axis(
            state.code[y, x : x + 1, np.newaxis], state.strand[y, x : x + 1, np.newaxis], axis=2
        )
        target = np.array(self.target_peptide[: self.strand_length], dtype=np.int8)
        if target.size < self.strand_length:
            target = np.concatenate([target, np.zeros(self.strand_length - target.size, dtype=np.int8)])
        f = float((peptide.squeeze() == target).sum()) / self.strand_length
        gray = int(np.clip(f * 255, 0, 255))
        return f"#{gray:02x}{gray:02x}{gray:02x}", "rect"

    def render_rgb(self, state: GeneticCodeState) -> np.ndarray:
        fit = self._fitness_field(state)
        img = cmap_viridis(fit).copy()
        img[~state.occupied] = (0, 0, 0)
        return img

    def population(self, state: GeneticCodeState) -> Mapping[str, int]:
        fit = self._fitness_field(state)
        occ = state.occupied
        total = int(occ.sum())
        if not total:
            return {
                "cells": 0,
                "mean_fitness_x100": 0,
                "best_fitness_x100": 0,
                "master_pct": 0,
                "code_consensus_x100": 0,
            }
        masked = fit[occ]
        return {
            "cells": total,
            "mean_fitness_x100": int(round(float(masked.mean()) * 100)),
            "best_fitness_x100": int(round(float(masked.max()) * 100)),
            "master_pct": int(round(100 * float((masked >= 0.99).mean()))),
            "code_consensus_x100": int(round(100 * self._code_consensus(state))),
        }

    def serialize_state(self, state: GeneticCodeState) -> dict:
        return {
            "occupied": state.occupied.astype(int).tolist(),
            "strand": state.strand.tolist(),
            "code": state.code.tolist(),
        }

    def deserialize_state(self, data: dict) -> GeneticCodeState:
        return GeneticCodeState(
            occupied=np.array(data["occupied"], dtype=bool),
            strand=np.array(data["strand"], dtype=np.int8),
            code=np.array(data["code"], dtype=np.int8),
        )

    def to_config(self) -> dict:
        return {
            "strand_length": self.strand_length,
            "n_codons": self.n_codons,
            "n_amino": self.n_amino,
            "target_peptide": tuple(int(x) for x in self.target_peptide),
            "death_rate": self.death_rate,
            "repro_prob": self.repro_prob,
            "strand_mutation": self.strand_mutation,
            "code_mutation": self.code_mutation,
            "seed_fraction": self.seed_fraction,
        }
