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

Every cell decodes its own strand through its own code, producing a peptide.
Fitness is, by default, the Miyazawa-Jernigan-style folding score of that
peptide (``fitness_mode="mj_landscape"``) — sequence-composition-dependent,
not a fixed answer key; the legacy ``"target_match"`` mode (peptide vs a fixed
target) is retained for comparison. Empty cells are colonised by
fitness-weighted occupied neighbours, copying both the strand (with per-base
mutation) and the code (with rare swaps), so any code that happens to make a
better-folding peptide spreads and the population converges on a shared code
through selection. That convergence is the emergence of the universal code.

HONEST SCOPE NOTE: this models the *selection-driven convergence* half of the
coevolution account via **vertical descent** (fitness-weighted colonisation +
mutation). It does **not** implement Vetsigian-Woese-Goldenfeld's signature
mechanism — *innovation sharing* / horizontal gene transfer gated on code
compatibility between donor and recipient. ``step()`` has no HGT term; the
convergence here is ordinary selection on a private code, not the
code-compatibility-mediated horizontal sharing the 2006 paper is about. Treat
the VWG citation as "in the lineage of the coevolution hypothesis", not "an
implementation of the 2006 model."

What this captures: coevolution of message and code, and population-level
convergence onto a shared code through (vertical) selection.
What it cuts: innovation-sharing/HGT (the VWG mechanism proper),
stereochemistry, actual translation/ribosomes, and the historical
contingencies of the canonical code.

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

# G4 — Miyazawa-Jernigan-style residue-pair contact-energy table for the
# Ikehara GADV proto-code. The MJ statistical potential (Miyazawa & Jernigan
# 1985, 1996) derives pairwise residue contact energies from observed
# frequencies in folded protein structures: hydrophobic-hydrophobic contacts
# are energetically favourable (negative ΔG); like-charged polar contacts
# are unfavourable (positive ΔG). A peptide's folding score is then the sum
# over adjacent pair contact energies — more negative = better-folded =
# more functional. We project the full 20×20 MJ table down to the 4-letter
# GADV alphabet using residue physicochemistry:
#
#     G (Gly) — small, flexible, neutral; weak interactions everywhere
#     A (Ala) — hydrophobic, small; favours other hydrophobics
#     D (Asp) — charged, polar; D-D unfavourable (same charge)
#     V (Val) — hydrophobic, bulky; V-V strongly favourable
#
# Numbers are dimensionless analogues calibrated to the MJ scale; the
# qualitative pattern is the published one.
#
# References:
#     Miyazawa, S., & Jernigan, R. L. (1985). Estimation of effective
#         interresidue contact energies from protein crystal structures.
#         Macromolecules, 18(3), 534-552.
#     Miyazawa, S., & Jernigan, R. L. (1996). Residue-residue potentials
#         with a favorable contact pair term and an unfavorable high
#         packing density term. J. Mol. Biol., 256(3), 623-644.
#     Ikehara, K. (2002). Origins of gene, genetic code, protein and life.
#         J. Biosci., 27(2), 165-186.
MJ_CONTACT_ENERGY: np.ndarray = np.array(
    [
        # contact partner:   G      A      D      V
        [-0.50, -0.60, -0.40, -0.70],  # row = G (Gly)
        [-0.60, -1.00, -0.30, -1.20],  # row = A (Ala)
        [-0.40, -0.30, +0.50, -0.20],  # row = D (Asp) — D-D unfavourable
        [-0.70, -1.20, -0.20, -1.50],  # row = V (Val) — V-V most favourable
    ],
    dtype=np.float32,
)


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
    # ``target_peptide`` is used only when fitness_mode == "target_match"
    # (the legacy v3.4 mode). Under the default Miyazawa-Jernigan landscape
    # there is no fixed target — fitness depends on the peptide's
    # sequence composition (G4).
    target_peptide: tuple[int, ...] = (0, 1, 2, 3, 0, 1)
    # G4 — pick the fitness landscape. Default ``"mj_landscape"`` scores
    # peptides by sequence composition under a Miyazawa-Jernigan-style
    # residue-pair contact-energy table (MJ_CONTACT_ENERGY): fitness is
    # the negative summed contact energy of adjacent residue pairs,
    # normalised to [0, 1]. The legacy ``"target_match"`` mode scores
    # peptides by how many positions match a fixed target sequence — that
    # was the v3.4 audit's "matching a hard-coded answer key" critique.
    fitness_mode: str = "mj_landscape"
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

    def init_state(
        self,
        width: int,
        height: int,
        *,
        seed_field: np.ndarray | None = None,
    ) -> GeneticCodeState:
        from cellauto.rules.abiogenesis.science import normalise_signal

        signal = normalise_signal(seed_field)
        gen = np.random.default_rng(self.rng.randrange(2**31))
        if signal is None:
            occupied = gen.random((height, width)) < self.seed_fraction
        else:
            # G1: occupancy probability tracks the upstream signal — cells
            # where the previous stage (RNA quasispecies) was active are the
            # cells that carry the first translated peptides.
            probs = np.clip(self.seed_fraction * (0.3 + 1.4 * signal), 0.0, 1.0)
            occupied = gen.random((height, width)) < probs
        strand = gen.integers(0, self.n_codons, size=(height, width, self.strand_length), dtype=np.int8)
        # Each cell starts with a private *random* codon table. No universal
        # code exists yet — its emergence is what the simulation should show.
        code = gen.integers(0, self.n_amino, size=(height, width, self.n_codons), dtype=np.int8)
        return GeneticCodeState(occupied=occupied, strand=strand, code=code)

    def extract_signal(self, state: GeneticCodeState) -> np.ndarray:
        """Downstream: occupied × per-cell peptide fitness — bright cells
        are translating useful peptides under the current code."""
        fit = self._fitness_field(state)
        return (state.occupied.astype(np.float32) * fit).astype(np.float32)

    def _peptides(self, state: GeneticCodeState) -> np.ndarray:
        """For each cell, decode its own strand with its own code. Returns
        an (H, W, L) array of amino-acid indices."""
        # `np.take_along_axis` over the codon axis: at each (y, x), the L
        # codons in strand index into the n_codons-entry table in code.
        return np.take_along_axis(state.code, state.strand.astype(np.int64), axis=2)

    def _fitness_field(self, state: GeneticCodeState) -> np.ndarray:
        peptide = self._peptides(state)  # (H, W, L) amino-acid indices
        if self.fitness_mode == "mj_landscape":
            return self._mj_fitness_field(peptide)
        # Legacy target-match landscape (v3.4 behaviour).
        target = np.array(self.target_peptide[: self.strand_length], dtype=np.int8)
        if target.size < self.strand_length:
            pad = np.zeros(self.strand_length - target.size, dtype=np.int8)
            target = np.concatenate([target, pad])
        matches = (peptide == target).sum(axis=2)
        return matches.astype(np.float32) / self.strand_length

    def _mj_fitness_field(self, peptide: np.ndarray) -> np.ndarray:
        """G4 — Miyazawa-Jernigan-style sequence-composition fitness.

        At each (y, x) cell, compute the sum of adjacent residue-pair
        contact energies under the ``MJ_CONTACT_ENERGY`` table. Negate
        (lower energy = better fold), shift, and normalise into [0, 1].
        This rewards peptides with many hydrophobic neighbours (A-V, V-V)
        and penalises like-charged contacts (D-D) — the published MJ
        physicochemical pattern, projected to the GADV proto-code.
        """
        L = peptide.shape[2]
        if L < 2:
            return np.zeros(peptide.shape[:2], dtype=np.float32)
        # peptide[..., i] is the amino-acid index at position i for that cell.
        # Pair energies: MJ_CONTACT_ENERGY[peptide[i], peptide[i+1]] for each
        # adjacent pair. Sum across pairs gives per-cell folding energy.
        left = peptide[..., :-1].astype(np.int64)
        right = peptide[..., 1:].astype(np.int64)
        energies = MJ_CONTACT_ENERGY[left, right]  # (H, W, L-1)
        folding_energy = energies.sum(axis=2)  # (H, W) — more negative = better
        # Normalise to [0, 1]: best possible all-V-V is L-1 contacts × −1.5;
        # worst is L-1 contacts × +0.5 (all D-D, the only positive entry).
        worst = float(MJ_CONTACT_ENERGY.max()) * (L - 1)  # +0.5 × (L-1)
        best = float(MJ_CONTACT_ENERGY.min()) * (L - 1)  # −1.5 × (L-1)
        span = max(worst - best, 1e-6)
        fit = (worst - folding_energy) / span  # 1 at the most favourable, 0 at the least
        return np.clip(fit, 0.0, 1.0).astype(np.float32)

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
