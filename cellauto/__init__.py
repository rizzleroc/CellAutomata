"""cellauto — pluggable cellular-automata sandbox.

Public API:
    Grid                  — generic grid container parameterized by cell state.
    Engine                — drives a Grid forward with a chosen Rule.
    Rule                  — protocol for pluggable rule sets.
    NaturalSelectionRule  — the original (now actually working) 4-rule simulator.
    ConwaysLifeRule       — classic Conway's Game of Life on a binary grid.
    Wolfram1DRule         — elementary 1D automaton (configurable rule number 0–255).
"""

from cellauto.engine import Engine
from cellauto.grid import Grid
from cellauto.rules.base import Rule
from cellauto.rules.conway import ConwaysLifeRule
from cellauto.rules.natural_selection import NaturalSelectionRule
from cellauto.rules.wolfram1d import Wolfram1DRule

__version__ = "2.0.0"

__all__ = [
    "Engine",
    "Grid",
    "Rule",
    "ConwaysLifeRule",
    "NaturalSelectionRule",
    "Wolfram1DRule",
    "__version__",
]
