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
    # G5 — pathway-coupled (epistatic) gene fitness.
    #
    # The v3.4 version used a hand-shaped 16-vector ``gene_values`` declaring
    # gene 0 worth +2.5 etc. — additive, per-gene, no interactions. This
    # replaces that with an *epistatic* model: fitness comes from a small set
    # of hand-specified pathways, where a pathway confers its joint benefit
    # only if ALL its member genes are present (an all-or-nothing AND-gate;
    # a partial pathway scores zero, not a fraction). The "essential" gene set
    # is simply the union of genes named in those pathways. HONEST NOTE: this
    # is a hand-authored vertex list, NOT a discovered topological invariant —
    # ``essential_count`` is ``len()`` of the union the author typed, and it is
    # benefit-independent. What is genuinely emergent is the *recovered* LUCA
    # core: which of those essential genes selection actually drives to ≥70%
    # prevalence (``_luca_core``), which is the real Weiss-et-al-style result.
    #
    # The 5 toy pathways below cover 10 of the 16 genes; the remaining 6
    # are accessory (small individual bonus, no pathway requirement).
    # Pathway names match the LUCA_GENE_NAMES tuple positions and are
    # informed by Weiss et al. 2016's reconstruction of LUCA as an
    # anaerobic thermophilic chemolithoautotroph subsisting on CO₂ + H₂.
    pathways: tuple[tuple[tuple[int, ...], float], ...] = (
        ((0, 1, 2), 1.4),  # translation core: rpoB · rpsC · rplB (ribosome)
        ((3, 4, 5), 1.5),  # Wood-Ljungdahl: fdhA · codhC · mrpA
        ((6, 7), 1.0),  # chemiosmotic ATP: atpA + Mrp-antiporter pair
        ((8, 9), 0.9),  # H₂ chemistry: hypE + nifH (anaerobic metabolism)
        ((10, 11), 0.8),  # DNA maintenance: dnaK chaperone + replication
    )
    pathway_break_penalty: float = 0.15  # cost per pathway present-but-incomplete
    accessory_bonus: float = 0.08  # small fitness for accessory (non-pathway) genes
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
    def pathway_genes(self) -> frozenset[int]:
        """The union of gene indices named in the hand-specified pathways —
        the genes the model treats as essential. (A declared vertex list, not
        a discovered invariant; the recovered LUCA core is a subset of this.)"""
        return frozenset(g for path, _ in self.pathways for g in path)

    @property
    def essential_count(self) -> int:
        """How many genes are members of at least one pathway. The recovered
        LUCA core size converges toward this under selection."""
        return len(self.pathway_genes)

    @property
    def fitness_normaliser(self) -> float:
        """Approximate maximum reachable fitness — every pathway complete
        plus every accessory gene, minus their maintenance cost."""
        pathway_benefit = sum(b for _, b in self.pathways)
        n_path_genes = len(self.pathway_genes)
        n_accessory = self.n_genes - n_path_genes
        accessory_total = self.accessory_bonus * n_accessory
        cost_total = self.gene_cost * self.n_genes
        return max(pathway_benefit + accessory_total - cost_total, 1.0)

    # ---- Rule protocol ----------------------------------------------------

    def init_state(
        self,
        width: int,
        height: int,
        *,
        seed_field: np.ndarray | None = None,
    ) -> LUCAState:
        from cellauto.rules.abiogenesis.science import normalise_signal

        signal = normalise_signal(seed_field)
        gen = np.random.default_rng(self.rng.randrange(2**31))
        if signal is None:
            occupied = gen.random((height, width)) < self.seed_fraction
        else:
            # G1: founder lineages emerge at the brightest cells of the
            # upstream signal (protocell-selection survivors, e.g.). Random
            # genomes everywhere they take root.
            probs = np.clip(self.seed_fraction * (0.3 + 1.4 * signal), 0.0, 1.0)
            occupied = gen.random((height, width)) < probs
        genome = gen.random((height, width, self.n_genes)) < 0.5
        return LUCAState(occupied=occupied, genome=genome)

    def extract_signal(self, state: LUCAState) -> np.ndarray:
        """Downstream: occupied × per-cell fitness — bright cells are
        well-adapted lineages."""
        fit = self._fitness_field(state)
        return (state.occupied.astype(np.float32) * fit).astype(np.float32)

    def _fitness_field(self, state: LUCAState) -> np.ndarray:
        """G5 — pathway-network fitness, not hand-shaped per-gene values.

        For each cell:
          * For every pathway, if ALL member genes are present, add the
            pathway's joint benefit. If only SOME members are present
            (partial machinery — wasted), subtract a small penalty.
          * For each accessory gene present (not in any pathway), add a
            small individual bonus.
          * Subtract per-gene maintenance cost (genome-size penalty).
        Normalise into [0, 1].

        The "essential" gene set this rewards is purely a topological
        property of the pathway graph — a network invariant rather than a
        list of pre-declared values.
        """
        H, W, N = state.genome.shape
        genome_f = state.genome.astype(np.float32)
        fit = np.zeros((H, W), dtype=np.float32)
        accessory = set(range(N)) - set(self.pathway_genes)
        # Pathway contributions.
        for path, benefit in self.pathways:
            members = np.array(path, dtype=np.int64)
            present_count = genome_f[..., members].sum(axis=-1)
            full = (present_count == len(members)).astype(np.float32)
            partial = ((present_count > 0) & (present_count < len(members))).astype(np.float32)
            fit = fit + full * benefit - partial * self.pathway_break_penalty
        # Accessory genes — small individual bonus.
        for g in accessory:
            fit = fit + genome_f[..., g] * self.accessory_bonus
        # Maintenance cost.
        size = genome_f.sum(axis=-1)
        fit = fit - self.gene_cost * size
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
            "pathways": tuple((tuple(int(g) for g in path), float(b)) for path, b in self.pathways),
            "pathway_break_penalty": self.pathway_break_penalty,
            "accessory_bonus": self.accessory_bonus,
            "gene_cost": self.gene_cost,
            "death_rate": self.death_rate,
            "repro_prob": self.repro_prob,
            "mutation_rate": self.mutation_rate,
            "seed_fraction": self.seed_fraction,
            "core_prevalence": self.core_prevalence,
        }
