"""Stage 0 — Primordial soup.

Discrete cells in random Brownian-style mixing. Same-species cells in
proximity can combine into protocells (Stage 4 / Rule 4 of the original
README). Activated intermediates carry an ``is_new`` flag for one step; only
freshly-changed cells react.

This is the original v1.0 four-rule sketch implemented honestly, including
the Rule 3 gating fix that v2.0 left as a no-op. The mechanics live in
``cellauto.rules.natural_selection``; here we wrap them with the
scientifically-honest name and a citation block.

References (full text in ``docs/science.md``):
    Oparin, A. I. (1924). The Origin of Life.
    Haldane, J. B. S. (1929). The Origin of Life. Rationalist Annual.
    Miller, S. L. (1953). A production of amino acids under possible primitive
        Earth conditions. Science, 117(3046), 528-529.
"""

from __future__ import annotations

from dataclasses import dataclass

from cellauto.rules.natural_selection import NaturalSelectionRule


@dataclass
class AbiogenesisStage0Soup(NaturalSelectionRule):
    name: str = "abiogenesis-stage0-soup"
