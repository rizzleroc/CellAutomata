"""Tests for the abiogenesis pipeline composite rule."""
from cellauto.engine import Engine
from cellauto.rules.abiogenesis.pipeline import (
    STAGE_CLASSES,
    AbiogenesisPipelineRule,
)


def test_pipeline_starts_at_stage_0_by_default():
    rule = AbiogenesisPipelineRule()
    engine = Engine(width=15, height=15, rule=rule, seed=1)
    assert engine.state.current_stage == 0
    assert engine.state.inner_rule.__class__ is STAGE_CLASSES[0]


def test_pipeline_auto_promotes_after_duration():
    """After stage_duration steps, the pipeline must promote to the next stage."""
    rule = AbiogenesisPipelineRule(stage_duration=3)
    engine = Engine(width=15, height=15, rule=rule, seed=1)
    for _ in range(3):
        engine.step()
    assert engine.state.current_stage == 1


def test_pipeline_starting_stage_respected():
    rule = AbiogenesisPipelineRule(starting_stage=2)
    engine = Engine(width=15, height=15, rule=rule, seed=1)
    assert engine.state.current_stage == 2
    assert engine.state.inner_rule.__class__ is STAGE_CLASSES[2]


def test_pipeline_caps_at_final_stage():
    """After enough promotions, the pipeline should stay on the last stage
    rather than crashing or wrapping."""
    rule = AbiogenesisPipelineRule(stage_duration=2)
    engine = Engine(width=10, height=10, rule=rule, seed=1)
    for _ in range(20):
        engine.step()
    assert engine.state.current_stage == len(STAGE_CLASSES) - 1


def test_pipeline_population_includes_stage():
    rule = AbiogenesisPipelineRule()
    engine = Engine(width=10, height=10, rule=rule, seed=1)
    pop = engine.population()
    assert "stage" in pop
