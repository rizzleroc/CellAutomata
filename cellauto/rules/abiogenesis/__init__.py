"""Abiogenesis pipeline — five stages from primordial chemistry to protocell selection.

The four rules of the v1.0 README sketch the prebiotic-chemistry chapter of
the origin-of-life story. This package implements those rules as Stage 0
(primordial soup) and then carries the narrative forward through four more
scientifically-grounded stages:

    Stage 0  Primordial soup       Oparin (1924), Haldane (1929), Miller-Urey (1953)
    Stage 1  Reaction-diffusion    Turing (1952), Gray-Scott (1980s), Pearson (1993)
    Stage 2  Autocatalytic sets    Kauffman (1986), Hordijk & Steel (RAF algorithm)
    Stage 3  Vesicle formation     Deamer & Szostak (fatty-acid lipid vesicles)
    Stage 4  Protocell selection   Eigen-Schuster hypercycle (1977), Szostak Lab

Each stage is an independently runnable Rule with its own visualization. The
Pipeline rule composes them with auto-transition thresholds so a single run
can walk the whole story.

See ``docs/science.md`` for the math, the citations, and a discussion of
what each stage simplifies.
"""

from cellauto.rules.abiogenesis.pipeline import (
    AbiogenesisExtendedPipelineRule,
    AbiogenesisPipelineRule,
)
from cellauto.rules.abiogenesis.stage0_soup import AbiogenesisStage0Soup
from cellauto.rules.abiogenesis.stage1_grayscott import AbiogenesisStage1GrayScott
from cellauto.rules.abiogenesis.stage2_raf import AbiogenesisStage2RAF
from cellauto.rules.abiogenesis.stage3_vesicles import AbiogenesisStage3Vesicles
from cellauto.rules.abiogenesis.stage4_selection import AbiogenesisStage4Selection
from cellauto.rules.abiogenesis.stage_chirality import AbiogenesisStageHomochirality
from cellauto.rules.abiogenesis.stage_coacervate import AbiogenesisStageCoacervate
from cellauto.rules.abiogenesis.stage_code import AbiogenesisStageGeneticCode
from cellauto.rules.abiogenesis.stage_luca import AbiogenesisStageLUCA
from cellauto.rules.abiogenesis.stage_minerals import AbiogenesisStageMinerals
from cellauto.rules.abiogenesis.stage_rna import AbiogenesisStageRNAWorld
from cellauto.rules.abiogenesis.stage_vents import AbiogenesisStageVents

__all__ = [
    "AbiogenesisExtendedPipelineRule",
    "AbiogenesisPipelineRule",
    "AbiogenesisStage0Soup",
    "AbiogenesisStage1GrayScott",
    "AbiogenesisStage2RAF",
    "AbiogenesisStage3Vesicles",
    "AbiogenesisStage4Selection",
    "AbiogenesisStageRNAWorld",
    "AbiogenesisStageHomochirality",
    "AbiogenesisStageVents",
    "AbiogenesisStageCoacervate",
    "AbiogenesisStageMinerals",
    "AbiogenesisStageGeneticCode",
    "AbiogenesisStageLUCA",
]
