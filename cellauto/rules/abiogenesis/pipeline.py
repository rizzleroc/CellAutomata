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
from cellauto.rules.abiogenesis.stage_chirality import AbiogenesisStageHomochirality
from cellauto.rules.abiogenesis.stage_coacervate import AbiogenesisStageCoacervate
from cellauto.rules.abiogenesis.stage_code import AbiogenesisStageGeneticCode
from cellauto.rules.abiogenesis.stage_life import AbiogenesisStageLife
from cellauto.rules.abiogenesis.stage_luca import AbiogenesisStageLUCA
from cellauto.rules.abiogenesis.stage_minerals import AbiogenesisStageMinerals
from cellauto.rules.abiogenesis.stage_rna import AbiogenesisStageRNAWorld
from cellauto.rules.abiogenesis.stage_vents import AbiogenesisStageVents

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
    # The classes the pipeline walks through, in narrative order, with parallel
    # display metadata. Subclasses (e.g. the extended pipeline) override these
    # by supplying different tuples.
    stage_classes: tuple = STAGE_CLASSES
    stage_infos: tuple[StageInfo, ...] = STAGE_INFO
    rng: random.Random = field(default_factory=random.Random)
    _step_count: int = field(default=0, init=False)

    def _make_stage(self, n: int) -> Any:
        rule = self.stage_classes[n]()
        # Hand the pipeline's RNG to the stage so reproducibility holds across
        # promotions.
        if hasattr(rule, "rng"):
            rule.rng = self.rng
        return rule

    @staticmethod
    def _extract_signal(rule: Any, state: Any) -> Any:
        """Pull the previous stage's transferable signal so we can seed the
        next stage with it. Returns ``None`` when the previous stage hasn't
        opted in. The G1 fix: state genuinely flows forward across promotion.
        """
        if hasattr(rule, "extract_signal"):
            try:
                return rule.extract_signal(state)
            except Exception:  # pragma: no cover — defensive
                return None
        return None

    def _init_new_stage_state(self, new_rule: Any, width: int, height: int, signal: Any) -> Any:
        """Initialise the new stage's state, passing the upstream signal if
        the new stage accepts it. Falls back to bare ``init_state`` when the
        new stage's ``init_state`` doesn't accept a ``seed_field`` kwarg —
        keeps backward compat with stages that haven't opted in yet."""
        if signal is None:
            return new_rule.init_state(width, height)
        try:
            return new_rule.init_state(width, height, seed_field=signal)
        except TypeError:
            return new_rule.init_state(width, height)

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
            and state.current_stage < len(self.stage_classes) - 1
        ):
            self.promote(state)
        return state

    def promote(self, state: PipelineState) -> None:
        # G1: extract the upstream signal BEFORE we lose the reference.
        prev_signal = self._extract_signal(state.inner_rule, state.inner_state)
        state.current_stage = min(state.current_stage + 1, len(self.stage_classes) - 1)
        new_rule = self._make_stage(state.current_stage)
        state.inner_rule = new_rule
        state.inner_state = self._init_new_stage_state(new_rule, state.width, state.height, prev_signal)
        self.renderer_kind = new_rule.renderer_kind
        self._step_count = 0

    def set_stage(self, state: PipelineState, n: int) -> None:
        """Jump directly to stage ``n``. Unlike ``promote``, this can move
        backwards as well as forwards — it rebuilds the inner rule and state
        from scratch for the requested stage. Backward jumps don't carry a
        signal forward (there is no upstream to inherit from)."""
        n = max(0, min(int(n), len(self.stage_classes) - 1))
        if n == state.current_stage:
            return
        # Forward jumps still carry the signal — the jump simulates a
        # multi-step promotion. Backward jumps reset.
        prev_signal = (
            self._extract_signal(state.inner_rule, state.inner_state) if n > state.current_stage else None
        )
        state.current_stage = n
        new_rule = self._make_stage(n)
        state.inner_rule = new_rule
        state.inner_state = self._init_new_stage_state(new_rule, state.width, state.height, prev_signal)
        self.renderer_kind = new_rule.renderer_kind
        self._step_count = 0

    def stage_info_for(self, n: int) -> StageInfo:
        """Display metadata for stage ``n`` according to this pipeline's own
        ``stage_infos`` tuple (clamped to the valid range)."""
        infos = self.stage_infos
        return infos[max(0, min(int(n), len(infos) - 1))]

    def render_cell(self, state: PipelineState, x: int, y: int) -> tuple[str, str]:
        return state.inner_rule.render_cell(state.inner_state, x, y)

    def render_rgb(self, state: PipelineState):
        return state.inner_rule.render_rgb(state.inner_state)

    def population(self, state: PipelineState) -> Mapping[str, int]:
        inner_pop = dict(state.inner_rule.population(state.inner_state))
        return {"stage": state.current_stage, **inner_pop}

    def serialize_state(self, state: PipelineState) -> dict:
        # Persist the inner rule's tuned config too — otherwise a snapshot taken
        # with non-default stage parameters reloads with defaults (the inner
        # rule was being rebuilt via the bare default constructor). ``to_config``
        # is optional on a rule, so guard for it.
        inner_cfg = state.inner_rule.to_config() if hasattr(state.inner_rule, "to_config") else {}
        return {
            "current_stage": state.current_stage,
            "inner_state": state.inner_rule.serialize_state(state.inner_state),
            "inner_config": inner_cfg,
            "width": state.width,
            "height": state.height,
            "step_in_stage": self._step_count,
        }

    def deserialize_state(self, data: dict) -> PipelineState:
        inner_rule = self._make_stage(data["current_stage"])
        # Reapply the persisted inner-stage config so a tuned stage reloads with
        # its tuned parameters, not the dataclass defaults.
        for key, val in (data.get("inner_config") or {}).items():
            if hasattr(inner_rule, key):
                try:
                    setattr(inner_rule, key, val)
                except (AttributeError, TypeError):
                    pass
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


# ---------------------------------------------------------------------------
# Extended pipeline — every shipped origin-of-life process in narrative order
# ---------------------------------------------------------------------------

# StageInfo entries for the new processes inserted between the original five.
_STAGE_VENT_INFO = StageInfo(
    index=1,
    title="ALKALINE VENT",
    principle="Proton gradient across a chimney wall drives synthesis (chemiosmosis).",
    detail=(
        "Alkaline serpentinisation fluid meets the acidic ocean; the proton-"
        "motive force across the FeS wall does the work for early carbon "
        "fixation (Russell, Martin & Lane)."
    ),
    citation="Russell & Hall 1997 · Lane & Martin 2012 · Sojo 2016",
    legend="blue = alkaline vent; orange = acidic ocean; teal-green = synthesis at the wall.",
)
_STAGE_MINERAL_INFO = StageInfo(
    index=3,
    title="MINERAL CATALYSIS",
    principle="Condensation polymerisation localised to montmorillonite clay surfaces.",
    detail=(
        "Bulk water disfavours condensation; clay concentrates monomers on its "
        "charged surface and templates polymer growth (Ferris 1996; Cairns-Smith 1982)."
    ),
    citation="Ferris 1996 · Cairns-Smith 1982 · Hanczyc 2003",
    legend="tan = clay surface; teal-green = polymer accumulated on the clay.",
)
_STAGE_CHIRALITY_INFO = StageInfo(
    index=5,
    title="HOMOCHIRALITY",
    principle="Autocatalysis + mutual antagonism breaks mirror symmetry (Frank 1953).",
    detail=(
        "Each enantiomer catalyses its own production and annihilates the "
        "other; the racemic state is unstable to fluctuations, which are "
        "amplified until one hand dominates (Soai 1995; Blackmond 2004)."
    ),
    citation="Frank 1953 · Soai 1995 · Blackmond 2004",
    legend="teal = L-dominant; magenta = R-dominant; dark = racemic.",
)
_STAGE_RNA_INFO = StageInfo(
    index=6,
    title="RNA WORLD",
    principle="RNA as genotype and catalyst; replication with per-base error ε.",
    detail=(
        "Spatial Eigen quasispecies on a single-peak landscape. The master "
        "sequence is maintained only while ε < ln(σ)/L; past it, the population "
        "melts into the error catastrophe (Gilbert 1986; Eigen 1971)."
    ),
    citation="Gilbert 1986 · Eigen 1971 · Joyce 2002",
    legend="bright = master RNA strand; dark = far-from-master mutant; black = empty.",
)
_STAGE_CODE_INFO = StageInfo(
    index=7,
    title="GENETIC CODE",
    principle="Message and code coevolve; selection drives the population onto a shared code.",
    detail=(
        "Each cell decodes its own RNA strand with its own private "
        "codon→amino-acid table. Fitness depends on whether the produced "
        "peptide matches a needed catalyst, so any code that makes a more "
        "useful peptide spreads — the universal genetic code emerges from "
        "selection on the code itself (Vetsigian, Woese & Goldenfeld 2006)."
    ),
    citation="Crick 1968 · Woese 1965 · Wong 1975 · Vetsigian–Woese–Goldenfeld 2006",
    legend="viridis = fitness (peptide vs target); code_consensus stat shows convergence.",
)
_STAGE_LUCA_INFO = StageInfo(
    index=11,
    title="LUCA DISTILLATION",
    principle="Comparative genomics across surviving lineages reveals the ancestral core genome.",
    detail=(
        "A spatial population of evolving cells with gene-presence bitsets; "
        "selection on a benefit-vs-cost gene economy distills a shared core "
        "genome — the inferred LUCA. Mirrors Weiss et al. (2016)'s "
        "reconstruction of LUCA from genes shared across all sequenced "
        "prokaryotes."
    ),
    citation="Koonin 2003 · Theobald 2010 · Weiss et al. 2016",
    legend="viridis = fitness; luca_size stat = inferred ancestral core genome.",
)
_STAGE_LIFE_INFO = StageInfo(
    index=12,
    title="DIGITAL LIFE",
    principle="Virtual-CPU genomes that execute, ingest, excrete, divide, and mutate under selection.",
    detail=(
        "After LUCA, the lineages that lived. Each organism is a tape of "
        "opcodes run by a tiny virtual CPU (Tierra 1991; Avida 2004). Every "
        "instruction costs energy; INGEST converts substrate to energy; "
        "EXCRETE adds toxic waste; energy = 0 ⇒ death; energy ≥ E_div ⇒ "
        "division with per-instruction copy error ε. Distinct lineages "
        "diverge from the founding ancestor — open-ended evolution in a "
        "digital substrate (Channon 2003)."
    ),
    citation="Ray 1991 · Adami 1994 · Ofria & Wilke 2004 · Eigen 1971 · Channon 2003",
    legend="disc colour = organism energy; white ring = membrane; substrate = viridis field; dark = waste.",
)
_STAGE_COACERVATE_INFO = StageInfo(
    index=8,
    title="COACERVATES",
    principle="Liquid-liquid phase separation forms membraneless droplets (Cahn-Hilliard).",
    detail=(
        "Macromolecule-rich and dilute phases separate spontaneously and "
        "coarsen (Ostwald ripening). Modern biomolecular condensates run on "
        "the same physics (Oparin 1924; Banani 2017)."
    ),
    citation="Oparin 1924 · Cahn-Hilliard 1958 · Banani 2017",
    legend="gold = coacervate-rich droplet; dark = dilute phase.",
)

# Extended pipeline order: soup → vent → reaction-diffusion → clay → RAF →
# chirality → RNA → genetic code → coacervates → vesicles → protocell selection.
# This is the "show every process" version of the abiogenesis narrative; the
# original 5-stage pipeline is kept untouched (default REGISTRY entry).
EXTENDED_STAGE_CLASSES = (
    AbiogenesisStage0Soup,
    AbiogenesisStageVents,
    AbiogenesisStage1GrayScott,
    AbiogenesisStageMinerals,
    AbiogenesisStage2RAF,
    AbiogenesisStageHomochirality,
    AbiogenesisStageRNAWorld,
    AbiogenesisStageGeneticCode,
    AbiogenesisStageCoacervate,
    AbiogenesisStage3Vesicles,
    AbiogenesisStage4Selection,
    AbiogenesisStageLUCA,
    AbiogenesisStageLife,
)
EXTENDED_STAGE_INFO: tuple[StageInfo, ...] = (
    STAGE_INFO[0],
    _STAGE_VENT_INFO,
    STAGE_INFO[1],
    _STAGE_MINERAL_INFO,
    STAGE_INFO[2],
    _STAGE_CHIRALITY_INFO,
    _STAGE_RNA_INFO,
    _STAGE_CODE_INFO,
    _STAGE_COACERVATE_INFO,
    STAGE_INFO[3],
    STAGE_INFO[4],
    _STAGE_LUCA_INFO,
    _STAGE_LIFE_INFO,
)


@dataclass
class AbiogenesisExtendedPipelineRule(AbiogenesisPipelineRule):
    """Auto-promoting pipeline that walks every shipped origin-of-life process
    and on into digital life (13 stages, scientific order, soup → … → LUCA →
    LIFE). Drop-in replacement for the canonical `AbiogenesisPipelineRule` —
    same protocol, just a longer narrative."""

    name: str = "abiogenesis-pipeline-extended"
    stage_classes: tuple = EXTENDED_STAGE_CLASSES
    stage_infos: tuple[StageInfo, ...] = EXTENDED_STAGE_INFO
    # Each chapter card sits on-screen for ~4.5 s; pair that with a longer
    # stage_duration so transitions don't feel rushed at the default FPS.
    stage_duration: int = 90
