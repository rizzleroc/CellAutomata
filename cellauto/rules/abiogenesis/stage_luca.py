"""LUCA distillation — the last universal common ancestor as a core genome.

Every organism alive today descends from a single inferred ancestor: the
**last universal common ancestor (LUCA)**. We cannot dig LUCA up; we infer
its genome by comparative genomics — taking the *intersection* of gene
families present across all surviving lineages. Weiss et al. (2016) used
exactly this approach on ~6.1 million sequenced prokaryotic protein-coding
genes to reconstruct LUCA as a hydrothermal-vent, hydrogen-using,
chemolithoautotroph; the core gene set they recovered (~355 protein
families) is what every living organism inherited.

This stage models that distillation. A spatial population of proto-organisms
each carries a gene-presence bitset over ``n_genes`` possible genes. Each
gene contributes a positive or negative fitness term; a small set of
**essential genes** confers most of the fitness, **accessory genes** are
mildly beneficial, **deleterious genes** are costly. Every gene also imposes
a maintenance cost (genome-size penalty), so selection pushes cells to keep
only the genes they truly need. Cells reproduce with per-gene mutation and
fitness-weighted colonisation of empty neighbours.

The headline observable is ``luca_size``: the number of genes present in
**every** active cell — i.e. the genome of the inferred LUCA. Starting from
random genomes it falls to roughly the essential-gene count and locks there,
because any lineage that loses an essential gene is selected out. That
intersection IS the simulated LUCA.

What this captures: comparative-genomics distillation of the core ancestral
genome, selection on gene presence/absence, and the trade-off between gene
benefit and genome-size cost.
What it cuts: actual protein sequence evolution, horizontal gene transfer
(which Vetsigian et al. argue is *how* the universal code converged — the
genetic-code stage handles that part), and real biochemistry.

References:
    Weiss, M. C., Sousa, F. L., Mrnjavac, N., et al. (2016). The physiology
        and habitat of the last universal common ancestor. *Nature
        Microbiology*, 1, 16116.
    Koonin, E. V. (2003). Comparative genomics, minimal gene-sets and the
        last universal common ancestor. *Nature Reviews Microbiology*, 1,
        127-136.
    Theobald, D. L. (2010). A formal test of the theory of universal common
        ancestry. *Nature*, 465, 219-222.
    Mirkin, B. G., Fenner, T. I., Galperin, M. Y., & Koonin, E. V. (2003).
        Algorithms for computing parsimonious evolutionary scenarios for
        genome evolution… *BMC Evol. Biol.*, 3, 2.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.renderer import cmap_viridis

# Real LUCA core families (Weiss et al. 2016 *Nat. Microbiol.* 1:16116;
# Koonin 2003 *Nat. Rev. Microbiol.* 1:127). The 16-bit genome maps onto well-
# attested gene-family identities, aligned with the gene-value table:
#   indices 0-5  = essential (high benefit): translation + core W-L metabolism
#   indices 6-11 = accessory (mild benefit): energy + stress / synthesis
#   indices 12-15 = deleterious/late (penalised): post-GOE or post-DNA innovations
LUCA_GENE_NAMES: tuple[str, ...] = (
    "rpoB",  # RNA polymerase β
    "rpsC",  # ribosomal protein S3
    "rplB",  # ribosomal protein L2
    "fdhA",  # formate dehydrogenase
    "codhC",  # CODH/ACS — Wood-Ljungdahl key enzyme
    "mrpA",  # Na⁺/H⁺ antiporter
    "atpA",  # ATP synthase α
    "hypE",  # hydrogenase maturation
    "nifH",  # nitrogenase iron-protein
    "gltB",  # glutamate synthase
    "dnaK",  # Hsp70 chaperone
    "trpB",  # tryptophan synthase β
    "oxyR",  # oxidative-stress regulator (pre-GOE: deleterious)
    "gyrB",  # DNA gyrase (pre-DNA-world: deleterious)
    "photolyase",  # CPD photolyase (UV-damage repair: late)
    "mutS",  # DNA mismatch repair (late)
)


@dataclass
class LUCAState:
    occupied: np.ndarray  # (H, W) bool
    genome: np.ndarray  # (H, W, n_genes) bool — gene presence/absence per cell


@dataclass
class AbiogenesisStageLUCA:
    name: str = "abiogenesis-luca"
    renderer_kind: str = "field"
    n_genes: int = 16
    # Gene fitness contributions: indices 0-5 essential (high benefit), 6-11
    # accessory (mild), 12-15 deleterious (cost). The essential-gene count
    # sets the LUCA target — `luca_size` should converge to this.
    gene_values: tuple[float, ...] = (
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        0.7,
        0.7,
        0.7,
        0.7,
        0.7,
        0.7,
        -0.6,
        -0.6,
        -0.6,
        -0.6,
    )
    gene_cost: float = 0.10  # per-gene maintenance cost (genome-size penalty)
    death_rate: float = 0.10
    repro_prob: float = 0.6
    mutation_rate: float = 0.008  # per-gene flip probability when copying
    seed_fraction: float = 0.40
    # Strict intersection across all lineages collapses to ∅ under non-zero
    # mutation (one mutant misses every gene at any moment), so LUCA
    # reconstruction in practice uses parsimony / high-prevalence thresholds
    # (Weiss et al. 2016). We threshold at 0.7 — genes present across the
    # majority of surviving lineages — which lets essential genes lock in
    # while accessory genes drift in and out.
    core_prevalence: float = 0.70
    rng: random.Random = field(default_factory=random.Random)

    @property
    def essential_count(self) -> int:
        return sum(1 for v in self.gene_values if v > 1.0)

    @property
    def fitness_normaliser(self) -> float:
        """Approximate maximum reachable fitness (essential genes only,
        accounting for their maintenance cost)."""
        essentials = [v for v in self.gene_values if v > 1.0]
        return max(sum(essentials) - self.gene_cost * len(essentials), 1.0)

    # ---- Rule protocol ----------------------------------------------------

    def init_state(self, width: int, height: int) -> LUCAState:
        gen = np.random.default_rng(self.rng.randrange(2**31))
        occupied = gen.random((height, width)) < self.seed_fraction
        genome = gen.random((height, width, self.n_genes)) < 0.5
        return LUCAState(occupied=occupied, genome=genome)

    def _fitness_field(self, state: LUCAState) -> np.ndarray:
        vals = np.array(self.gene_values, dtype=np.float32)
        score = (state.genome.astype(np.float32) * vals).sum(axis=2)
        size = state.genome.sum(axis=2).astype(np.float32)
        fit = score - self.gene_cost * size
        return np.clip(fit / self.fitness_normaliser, 0.0, 1.0)

    def _luca_core(self, state: LUCAState) -> np.ndarray:
        """Genes present in ≥ `core_prevalence` of active cells — the inferred
        LUCA core genome. Mirrors how real LUCA reconstruction (Weiss et al.
        2016) treats genes that appear across nearly all lineages as
        ancestral, rather than requiring strict universal presence (which is
        unstable under non-zero mutation)."""
        occ = state.occupied
        if not occ.any():
            return np.zeros(self.n_genes, dtype=bool)
        active = state.genome[occ]
        return active.mean(axis=0) >= self.core_prevalence

    def step(self, state: LUCAState) -> LUCAState:
        H, W, N = state.genome.shape
        occ = state.occupied
        fit = self._fitness_field(state)
        new_occ = occ.copy()
        new_genome = state.genome.copy()

        # Death: low-fitness cells preferentially die.
        for y in range(H):
            for x in range(W):
                if occ[y, x] and self.rng.random() < self.death_rate * (1.0 - 0.7 * fit[y, x]):
                    new_occ[y, x] = False

        # Replication: fitness-weighted colonisation of empty Moore neighbours.
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
                child = state.genome[py, px].copy()
                # Per-gene mutation (independent flips).
                for i in range(N):
                    if self.rng.random() < self.mutation_rate:
                        child[i] = not child[i]
                new_genome[y, x] = child
                new_occ[y, x] = True

        state.occupied = new_occ
        state.genome = new_genome
        return state

    # ---- Rendering --------------------------------------------------------

    def render_cell(self, state: LUCAState, x: int, y: int) -> tuple[str, str]:
        if not state.occupied[y, x]:
            return "#000000", "rect"
        fit = self._fitness_field(state)[y, x]
        gray = int(np.clip(fit * 255, 0, 255))
        return f"#{gray:02x}{gray:02x}{gray:02x}", "rect"

    def render_rgb(self, state: LUCAState) -> np.ndarray:
        fit = self._fitness_field(state)
        img = cmap_viridis(fit).copy()
        img[~state.occupied] = (0, 0, 0)
        return img

    def population(self, state: LUCAState) -> Mapping[str, int]:
        occ = state.occupied
        total = int(occ.sum())
        if not total:
            return {
                "cells": 0,
                "mean_fitness_x100": 0,
                "luca_size": 0,
                "essential_target": self.essential_count,
                "mean_genome_size": 0,
            }
        fit = self._fitness_field(state)
        mean_fit = float(fit[occ].mean())
        luca_size = int(self._luca_core(state).sum())
        mean_genome = float(state.genome[occ].sum(axis=-1).mean())
        return {
            "cells": total,
            "mean_fitness_x100": int(round(mean_fit * 100)),
            "luca_size": luca_size,
            "essential_target": self.essential_count,
            "mean_genome_size_x10": int(round(mean_genome * 10)),
        }

    def serialize_state(self, state: LUCAState) -> dict:
        return {
            "occupied": state.occupied.astype(int).tolist(),
            "genome": state.genome.astype(int).tolist(),
        }

    def deserialize_state(self, data: dict) -> LUCAState:
        return LUCAState(
            occupied=np.array(data["occupied"], dtype=bool),
            genome=np.array(data["genome"], dtype=bool),
        )

    def to_config(self) -> dict:
        return {
            "n_genes": self.n_genes,
            "gene_values": tuple(float(v) for v in self.gene_values),
            "gene_cost": self.gene_cost,
            "death_rate": self.death_rate,
            "repro_prob": self.repro_prob,
            "mutation_rate": self.mutation_rate,
            "seed_fraction": self.seed_fraction,
        }
