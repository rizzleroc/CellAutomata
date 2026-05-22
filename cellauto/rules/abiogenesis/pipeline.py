"""Pipeline — runs the abiogenesis stages in sequence with auto-transitions.

The simulation starts in Stage 0 (primordial soup). When a saturation
threshold is reached, it auto-promotes to Stage 1 (reaction-diffusion).
When Stage 1's pattern stabilizes, it promotes to Stage 2 (RAFs), and so on.
A user can also force a stage with ``--stage N`` from the CLI or via the
GUI's stage dropdown.

This is the "textbook" mode: one simulation that walks the entire
chemistry-to-life story end to end. Each transition advances the narrative
to the next scientifically-grounded chapter rather than just continuing the
same dynamics.

The thresholds are heuristic — chosen to give a reasonable demo, not to
match any specific origin-of-life timescale.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from cellauto.rules.abiogenesis.stage0_soup import AbiogenesisStage0Soup
from cellauto.rules.abiogenesis.stage1_grayscott import AbiogenesisStage1GrayScott
from cellauto.rules.abiogenesis.stage2_raf import AbiogenesisStage2RAF
from cellauto.rules.abiogenesis.stage3_vesicles import AbiogenesisStage3Vesicles
from cellauto.rules.abiogenesis.stage4_selection import AbiogenesisStage4Selection

STAGE_CLASSES = (
    AbiogenesisStage0Soup,
    AbiogenesisStage1GrayScott,
    AbiogenesisStage2RAF,
    AbiogenesisStage3Vesicles,
    AbiogenesisStage4Selection,
)


@dataclass(frozen=True)
class StageInfo:
    """Display metadata for one stage — what the user reads on screen so the
    science isn't trapped in docstrings. ``principle`` is the governing
    idea/equation, ``detail`` the one-paragraph explanation, ``citation`` the
    canonical sources, and ``legend`` decodes what the on-screen colours mean.
    """

    index: int
    title: str
    principle: str
    detail: str
    citation: str
    legend: str


STAGE_INFO: tuple[StageInfo, ...] = (
    StageInfo(
        index=0,
        title="PRIMORDIAL SOUP",
        principle="Dissolved monomers mix and condense in a reducing ocean.",
        detail=(
            "The Oparin–Haldane soup, validated by Miller & Urey's 1953 "
            "spark-discharge experiment. The starting mixture is sampled "
            "weighted by Miller's measured yields, so formic acid and glycine "
            "dominate — a real soup is not a uniform rainbow."
        ),
        citation="Oparin 1924 · Haldane 1929 · Miller 1953",
        legend="Each colour = one Miller–Urey product; ovals = nascent protocells.",
    ),
    StageInfo(
        index=1,
        title="REACTION–DIFFUSION",
        principle="∂u/∂t = Du∇²u − uv² + F(1−u);  ∂v/∂t = Dv∇²v + uv² − (F+k)v",
        detail=(
            "Gray–Scott autocatalysis on a continuous chemical field — the "
            "mechanism Turing proposed in 1952 for biological pattern "
            "formation. Self-replicating spots divide like protocells."
        ),
        citation="Turing 1952 · Gray–Scott 1985 · Pearson 1993",
        legend="viridis ramp = concentration of the autocatalyst v.",
    ),
    StageInfo(
        index=2,
        title="AUTOCATALYTIC SETS",
        principle="A closed, food-generated, reflexively-autocatalytic reaction set (RAF).",
        detail=(
            "Kauffman's 1986 insight: above a connectivity threshold a random "
            "reaction network spontaneously contains a self-sustaining "
            "catalytic loop. The RAF is found by the Hordijk–Steel closure; "
            "ignition is that loop amplifying itself."
        ),
        citation="Kauffman 1986 · Hordijk & Steel 2004",
        legend="viridis = total chemistry density; bright = autocatalytic hot-spot.",
    ),
    StageInfo(
        index=3,
        title="VESICLE FORMATION",
        principle="Amphiphiles self-assemble into bilayers above their CMC.",
        detail=(
            "Fatty acids (here decanoic acid, C10, CMC ≈ 85 mM) cluster into "
            "membranes once concentration crosses the critical micelle "
            "concentration — the first bounded compartments. Deamer & Szostak."
        ),
        citation="Deamer 2008 · Hanczyc & Szostak 2003",
        legend="amber = membrane (lipid above CMC); viridis = lipid concentration.",
    ),
    StageInfo(
        index=4,
        title="PROTOCELL SELECTION",
        principle="Bounded chemistry + heritable variation ⇒ Darwinian selection.",
        detail=(
            "Compartmentalized replicators grow, divide and mutate. Fitness is "
            "a hypercycle-flavoured proxy (Eigen–Schuster 1977); past the "
            "error threshold ≈ 1/L the master sequence melts (error "
            "catastrophe)."
        ),
        citation="Eigen 1971 · Eigen & Schuster 1977 · Szostak 2017",
        legend="disc colour = fitness (red→green); white ring = membrane.",
    ),
)


def stage_info(n: int) -> StageInfo:
    """Display metadata for stage ``n`` (clamped to the valid range)."""
    return STAGE_INFO[max(0, min(n, len(STAGE_INFO) - 1))]


@dataclass
class PipelineState:
    current_stage: int
    inner_state: Any
    inner_rule: Any
    width: int
    height: int


@dataclass
class AbiogenesisPipelineRule:
    name: str = "abiogenesis-pipeline"
    renderer_kind: str = "field"  # set to inner rule's kind in init
    starting_stage: int = 0
    stage_duration: int = 60  # steps before promoting to next stage
    auto_promote: bool = True
    rng: random.Random = field(default_factory=random.Random)
    _step_count: int = field(default=0, init=False)

    def _make_stage(self, n: int) -> Any:
        rule = STAGE_CLASSES[n]()
        # Hand the pipeline's RNG to the stage so reproducibility holds across
        # promotions.
        if hasattr(rule, "rng"):
            rule.rng = self.rng
        return rule

    def init_state(self, width: int, height: int) -> PipelineState:
        inner = self._make_stage(self.starting_stage)
        self.renderer_kind = inner.renderer_kind
        return PipelineState(
            current_stage=self.starting_stage,
            inner_rule=inner,
            inner_state=inner.init_state(width, height),
            width=width,
            height=height,
        )

    def step(self, state: PipelineState) -> PipelineState:
        state.inner_state = state.inner_rule.step(state.inner_state)
        self._step_count += 1
        if (
            self.auto_promote
            and self._step_count >= self.stage_duration
            and state.current_stage < len(STAGE_CLASSES) - 1
        ):
            self.promote(state)
        return state

    def promote(self, state: PipelineState) -> None:
        state.current_stage = min(state.current_stage + 1, len(STAGE_CLASSES) - 1)
        new_rule = self._make_stage(state.current_stage)
        state.inner_rule = new_rule
        state.inner_state = new_rule.init_state(state.width, state.height)
        self.renderer_kind = new_rule.renderer_kind
        self._step_count = 0

    def set_stage(self, state: PipelineState, n: int) -> None:
        """Jump directly to stage ``n`` (0..len(STAGE_CLASSES)-1). Unlike
        ``promote``, this can move backwards as well as forwards — it rebuilds
        the inner rule and state from scratch for the requested stage."""
        n = max(0, min(int(n), len(STAGE_CLASSES) - 1))
        if n == state.current_stage:
            return
        state.current_stage = n
        new_rule = self._make_stage(n)
        state.inner_rule = new_rule
        state.inner_state = new_rule.init_state(state.width, state.height)
        self.renderer_kind = new_rule.renderer_kind
        self._step_count = 0

    def render_cell(self, state: PipelineState, x: int, y: int) -> tuple[str, str]:
        return state.inner_rule.render_cell(state.inner_state, x, y)

    def render_rgb(self, state: PipelineState):
        return state.inner_rule.render_rgb(state.inner_state)

    def population(self, state: PipelineState) -> Mapping[str, int]:
        inner_pop = dict(state.inner_rule.population(state.inner_state))
        return {"stage": state.current_stage, **inner_pop}

    def serialize_state(self, state: PipelineState) -> dict:
        return {
            "current_stage": state.current_stage,
            "inner_state": state.inner_rule.serialize_state(state.inner_state),
            "width": state.width,
            "height": state.height,
            "step_in_stage": self._step_count,
        }

    def deserialize_state(self, data: dict) -> PipelineState:
        inner_rule = self._make_stage(data["current_stage"])
        self.renderer_kind = inner_rule.renderer_kind
        self._step_count = data.get("step_in_stage", 0)
        return PipelineState(
            current_stage=data["current_stage"],
            inner_rule=inner_rule,
            inner_state=inner_rule.deserialize_state(data["inner_state"]),
            width=data["width"],
            height=data["height"],
        )

    def to_config(self) -> dict:
        return {
            "starting_stage": self.starting_stage,
            "stage_duration": self.stage_duration,
            "auto_promote": self.auto_promote,
        }
