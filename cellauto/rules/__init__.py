from cellauto.rules.base import Rule
from cellauto.rules.conway import ConwaysLifeRule
from cellauto.rules.natural_selection import NaturalSelectionRule
from cellauto.rules.wolfram1d import Wolfram1DRule

REGISTRY: dict[str, type] = {
    "natural-selection": NaturalSelectionRule,
    "conway": ConwaysLifeRule,
    "wolfram1d": Wolfram1DRule,
}

__all__ = ["Rule", "REGISTRY", "ConwaysLifeRule", "NaturalSelectionRule", "Wolfram1DRule"]
