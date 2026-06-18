"""Canonical stage count — single source of truth, locked to code (REV-14).

Counts in this repo have drifted badly: prose has said the extended pipeline is
"10 stages", "12 stages", and "13 stages" in different files, all at once. The
*only* authoritative number is ``len(EXTENDED_STAGE_CLASSES)`` — the tuple the
extended pipeline actually runs. This gate pins that number, pins the parallel
metadata tuple to it, and pins the README's current-state claims to it, so a
stage can't be added (or a doc edited) without the count staying consistent
everywhere. Historical changelog/version entries are intentionally *not* checked
— "v3.4 extended the pipeline to 12 stages" was true when written.
"""

from __future__ import annotations

import re
from pathlib import Path

from cellauto.rules import REGISTRY
from cellauto.rules.abiogenesis.pipeline import (
    EXTENDED_STAGE_CLASSES,
    EXTENDED_STAGE_INFO,
)
from cellauto.rules.abiogenesis.stage_life import AbiogenesisStageLife

# The canonical count: 12 origin-of-life chemistry stages + the digital-life
# capstone (Stage XIII). Bump this deliberately when you add a stage — that is
# the signal to update the docs the README check below also guards.
CANONICAL_STAGE_COUNT = 13

_ROOT = Path(__file__).resolve().parents[1]


def test_extended_pipeline_is_the_canonical_count():
    assert len(EXTENDED_STAGE_CLASSES) == CANONICAL_STAGE_COUNT


def test_stage_info_runs_in_lockstep_with_classes():
    # The parallel metadata tuple must never fall out of sync with the classes.
    assert len(EXTENDED_STAGE_INFO) == len(EXTENDED_STAGE_CLASSES)


def test_digital_life_is_the_capstone():
    # Stage XIII (digital life) is the last stage — the chemistry-to-life arc
    # ends here. If this moves, the "capstone" framing in the docs is wrong.
    assert EXTENDED_STAGE_CLASSES[-1] is AbiogenesisStageLife


def test_registered_extended_rule_uses_the_canonical_tuple():
    # The selectable rule must run exactly the canonical stages, not a private
    # copy that could drift from EXTENDED_STAGE_CLASSES.
    rule = REGISTRY["abiogenesis-pipeline-extended"]()
    assert tuple(rule.stage_classes) == tuple(EXTENDED_STAGE_CLASSES)


def test_readme_current_state_matches_the_code_count():
    """The README's *current-state* stage count is locked to the code.

    We check the front-matter headline and the rule-registry table row — the two
    places that describe the product *as it is now* — and forbid the specific
    stale "12-stage extended pipeline" phrasing that caused the drift. Dated
    version-history bullets are left alone on purpose.
    """
    n = len(EXTENDED_STAGE_CLASSES)
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")

    # Headline: every "<n>-stage extended pipeline" claim must equal the code.
    counts = re.findall(r"(\d+)-stage extended pipeline", readme)
    assert counts, "README no longer states the extended-pipeline stage count"
    assert all(int(c) == n for c in counts), f"README extended-pipeline count(s) {counts} != code count {n}"

    # The exact stale phrase that REV-14 flagged must not come back.
    assert "12-stage extended pipeline" not in readme

    # Rule-registry table row describes the current product; lock it too.
    row = next(
        line for line in readme.splitlines() if "abiogenesis-pipeline-extended" in line and "|" in line
    )
    assert f"{n}-stage" in row, f"registry-table row out of sync with code count {n}: {row!r}"
