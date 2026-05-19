"""cellauto — scientifically-grounded abiogenesis sandbox + reference cellular automata.

Public API:
    Grid     — generic grid container.
    Field    — numpy-backed continuous chemical-concentration field.
    Engine   — drives a Grid/Field forward with a chosen Rule.
    Rule     — protocol for pluggable rule sets.

Rules:
    AbiogenesisPipelineRule        — composite running stages 0-4 in sequence.
    AbiogenesisStage0Soup          — primordial-soup mixing (Oparin/Haldane).
    AbiogenesisStage1GrayScott     — Gray-Scott reaction-diffusion (Turing/Pearson).
    AbiogenesisStage2RAF           — Kauffman RAF autocatalytic sets.
    AbiogenesisStage3Vesicles      — Lipid bilayer self-assembly.
    AbiogenesisStage4Selection     — Protocell selection / Eigen-Schuster hypercycle.
    ConwaysLifeRule                — Conway's Game of Life (reference).
    Wolfram1DRule                  — elementary 1D automaton (reference).
    NaturalSelectionRule           — legacy alias of AbiogenesisStage0Soup.

See docs/science.md for citations and the math behind each stage.
"""

from cellauto.engine import Engine
from cellauto.field import Field
from cellauto.grid import Grid
from cellauto.rules.abiogenesis import (
    AbiogenesisPipelineRule,
    AbiogenesisStage0Soup,
    AbiogenesisStage1GrayScott,
    AbiogenesisStage2RAF,
    AbiogenesisStage3Vesicles,
    AbiogenesisStage4Selection,
)
from cellauto.rules.base import Rule
from cellauto.rules.conway import ConwaysLifeRule
from cellauto.rules.natural_selection import NaturalSelectionRule
from cellauto.rules.wolfram1d import Wolfram1DRule

__version__ = "3.0.0"

__all__ = [
    "Engine", "Field", "Grid", "Rule",
    "AbiogenesisPipelineRule",
    "AbiogenesisStage0Soup",
    "AbiogenesisStage1GrayScott",
    "AbiogenesisStage2RAF",
    "AbiogenesisStage3Vesicles",
    "AbiogenesisStage4Selection",
    "ConwaysLifeRule",
    "NaturalSelectionRule",
    "Wolfram1DRule",
    "__version__",
]
