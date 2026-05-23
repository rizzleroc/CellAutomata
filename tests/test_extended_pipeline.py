"""Tests for the 10-stage extended abiogenesis pipeline.

The canonical 5-stage pipeline keeps its behaviour; this one walks every
shipped origin-of-life process in scientific order.
"""

from cellauto.engine import Engine
from cellauto.rules.abiogenesis.pipeline import (
    EXTENDED_STAGE_CLASSES,
    EXTENDED_STAGE_INFO,
    STAGE_CLASSES,
    AbiogenesisExtendedPipelineRule,
    AbiogenesisPipelineRule,
)


def test_canonical_pipeline_still_has_five_stages():
    rule = AbiogenesisPipelineRule()
    assert len(rule.stage_classes) == 5
    assert tuple(rule.stage_classes) == STAGE_CLASSES


def test_extended_pipeline_has_twelve_stages():
    rule = AbiogenesisExtendedPipelineRule()
    assert len(rule.stage_classes) == 12
    assert len(rule.stage_infos) == 12
    assert tuple(rule.stage_classes) == EXTENDED_STAGE_CLASSES
    assert tuple(rule.stage_infos) == EXTENDED_STAGE_INFO


def test_extended_pipeline_auto_promotes_all_stages():
    rule = AbiogenesisExtendedPipelineRule(stage_duration=2)
    engine = Engine(width=12, height=12, rule=rule, seed=1)
    final = len(EXTENDED_STAGE_CLASSES) - 1
    for _ in range(2 * (final + 2)):
        engine.step()
    assert engine.state.current_stage == final


def test_extended_pipeline_set_stage_jumps_to_any_index():
    rule = AbiogenesisExtendedPipelineRule()
    engine = Engine(width=12, height=12, rule=rule, seed=1)
    rule.set_stage(engine.state, 7)
    assert engine.state.current_stage == 7
    assert engine.state.inner_rule.__class__ is EXTENDED_STAGE_CLASSES[7]


def test_extended_pipeline_population_includes_stage():
    rule = AbiogenesisExtendedPipelineRule()
    engine = Engine(width=12, height=12, rule=rule, seed=1)
    assert "stage" in engine.population()


def test_stage_info_for_uses_rule_table():
    canonical = AbiogenesisPipelineRule()
    extended = AbiogenesisExtendedPipelineRule()
    # The extended pipeline's stage 5 is HOMOCHIRALITY; the canonical pipeline
    # clamps to its final entry (protocell selection) for the same index.
    assert extended.stage_info_for(5).title == "HOMOCHIRALITY"
    assert extended.stage_info_for(7).title == "GENETIC CODE"
    assert extended.stage_info_for(11).title == "LUCA DISTILLATION"
    assert canonical.stage_info_for(5).title == "PROTOCELL SELECTION"


def test_registered_in_registry():
    from cellauto.rules import REGISTRY

    assert "abiogenesis-pipeline" in REGISTRY
    assert "abiogenesis-pipeline-extended" in REGISTRY
