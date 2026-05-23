"""Rule registry.

The abiogenesis stages are the canonical scientifically-grounded rules.
``natural-selection`` is retained as a deprecated alias for Stage 0 so v2.0
CLI invocations and snapshots keep working.
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
from cellauto.rules.base import Rule
from cellauto.rules.conway import ConwaysLifeRule
from cellauto.rules.natural_selection import NaturalSelectionRule
from cellauto.rules.wolfram1d import Wolfram1DRule

REGISTRY: dict[str, type] = {
    # Abiogenesis pipeline (canonical 5 stages, and the full-arc 10-stage version).
    "abiogenesis-pipeline": AbiogenesisPipelineRule,
    "abiogenesis-pipeline-extended": AbiogenesisExtendedPipelineRule,
    "abiogenesis-stage0-soup": AbiogenesisStage0Soup,
    "abiogenesis-stage1-grayscott": AbiogenesisStage1GrayScott,
    "abiogenesis-stage2-raf": AbiogenesisStage2RAF,
    "abiogenesis-stage3-vesicles": AbiogenesisStage3Vesicles,
    "abiogenesis-stage4-selection": AbiogenesisStage4Selection,
    # Additional origin-of-life processes (selectable directly).
    "abiogenesis-rna-world": AbiogenesisStageRNAWorld,
    "abiogenesis-homochirality": AbiogenesisStageHomochirality,
    "abiogenesis-hydrothermal-vent": AbiogenesisStageVents,
    "abiogenesis-coacervate": AbiogenesisStageCoacervate,
    "abiogenesis-mineral-catalysis": AbiogenesisStageMinerals,
    "abiogenesis-genetic-code": AbiogenesisStageGeneticCode,
    "abiogenesis-luca": AbiogenesisStageLUCA,
    # Reference automata.
    "conway": ConwaysLifeRule,
    "wolfram1d": Wolfram1DRule,
    # Legacy alias — same mechanics as Stage 0, kept for v2.0 backward compat.
    "natural-selection": NaturalSelectionRule,
}

__all__ = ["Rule", "REGISTRY"]
