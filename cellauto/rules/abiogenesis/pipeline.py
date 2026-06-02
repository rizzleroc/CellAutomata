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
    # v4.0.6 E3 — surface the methods/controls/connective tissue that already
    # lives in docs/science.md. All five are optional (default empty string)
    # so the 12+ legacy stages keep working; the new fields render in the
    # "How it works" panel only when populated.
    apparatus: str = ""  # what physical setup we're modelling
    methods: str = ""  # how the engine step maps to that experiment
    control: str = ""  # what the null/control experiment looks like
    expect: str = ""  # the visual signature of success/failure
    caveats: str = ""  # honest limitations — what this ISN'T
    # v4.0.6 E4 — connected-narrative scaffolding. ``produces`` and
    # ``consumes`` link stages causally so the chapter card can read "last
    # stage gave you X; now we do Y; expect Z".
    produces: str = ""  # what this stage hands off to the next
    consumes: str = ""  # what this stage expects from the previous


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
        apparatus=(
            "Miller–Urey flask: a sealed loop of (a) boiling-water flask "
            "modelling a warm ocean, (b) a spark gap modelling atmospheric "
            "lightning across CH₄/NH₃/H₂/H₂O vapour, (c) a condenser trap "
            "collecting product. After 1 week Miller recovered the amino "
            "acids + organic acids in the proportions we sample here."
        ),
        methods=(
            "Each cell holds one species drawn from MILLER_UREY_SPECIES "
            "weighted by Miller's measured yields (formic acid ≈ 49 %, "
            "glycine ≈ 13 %, etc.). Per step, every cell either keeps its "
            "species or condenses with a same-species neighbour (combine "
            "rule) → larger ovals = nascent protocells. Engine step ≈ one "
            "stirring/mixing cycle of the simulated ocean."
        ),
        control=(
            "Null: replace the weighted sample with a uniform-random species "
            "(NO Miller priors). The output looks visually similar but the "
            "histogram of species frequencies goes flat — the real Miller "
            "soup is heavily biased toward a handful of species, and that "
            "bias is what gates the chemistry-to-life ladder."
        ),
        expect=(
            "Watch for: small monochrome patches forming where same-species "
            "cells meet. Larger ovals (protocell flag) appear after several "
            "combine events. ≥ 10 % of cells should be ovals by step 80."
        ),
        caveats=(
            "This is condensation in cell-grid form — not a real free-energy "
            "calculation. No mass conservation across species; the combine "
            "rule is a toy stand-in for actual prebiotic condensation "
            "kinetics. Use it to teach 'biased mixing → patches,' not "
            "'real organic-chemistry yields.'"
        ),
        consumes="",
        produces="Patches of condensed amino-acid product → seed v-field for Stage 1.",
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
        apparatus=(
            "A continuous-flow chemical reactor: two reactants (u feed and "
            "v autocatalyst) diffuse through a thin gel layer while u is "
            "continuously fed in at rate F and v + product are killed at "
            "rate F + k. Real-world analogues include the CIMA reaction "
            "(Castets et al. 1990) which produces Turing patterns in vitro."
        ),
        methods=(
            "Forward-Euler integration of the Gray-Scott PDE on a 2-D grid "
            "with a 5-point Laplacian. substeps_per_frame=10 sub-PDE steps "
            "per visible engine step so the CFL condition holds at dt=1. "
            "Du:Dv ratio = 2:1 chosen to satisfy Turing's diffusion-driven "
            "instability criterion. Initial v seeded as Poisson-disk "
            "scatter of 6–10 patches (v4.0.4 sparsification — earlier "
            "single-patch seed tiled the domain by step 600)."
        ),
        control=(
            "Null: F = 0 (no feed). The autocatalyst v decays exponentially "
            "to zero within ~50 steps and no spots ever form. This pins the "
            "claim that the pattern is sustained by far-from-equilibrium "
            "feed, not by initial conditions."
        ),
        expect=(
            "Watch for: scattered isolated spots appearing where the seed "
            "patches were, then each spot splitting into two (mitosis-like "
            "division) over ~50–100 steps. The 'spots' preset (F=0.035, "
            "k=0.065) is the canonical regime; switch to 'mitosis' or "
            "'labyrinth' for different topology."
        ),
        caveats=(
            "u and v are abstract reactants, not specific chemicals. The "
            "spot-as-protocell analogy is a visual one — Gray-Scott does "
            "not encode a real autocatalytic loop with kinetic constants "
            "from a known biochemistry. It demonstrates THAT autocatalysis "
            "+ diffusion can produce self-replicating spatial features."
        ),
        consumes="Seed v-field from Stage 0 (where condensation was densest).",
        produces="Spatial pattern of v-field maxima → seed reactant inventory for Stage 2 RAF.",
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
        apparatus=(
            "Conceptually a well-stirred reactor with a fixed set of food "
            "molecules continuously fed in, n_species reactant types, and "
            "n_reactions possible reactions each of which REQUIRES a "
            "catalyst (another species) to fire. We're not modelling the "
            "vessel — we're modelling the catalytic graph that determines "
            "whether the chemistry self-sustains."
        ),
        methods=(
            "Build a random reaction network: every reaction is assigned a "
            "random catalyst from the species inventory. Then find the RAF "
            "via the Hordijk-Steel layered closure (mandatory catalysis, "
            "F-generated reactants). On the spatial grid, each cell holds "
            "concentrations evolving under that network; cells couple via "
            "diffusion. The RAF members glow brighter as their loops fire."
        ),
        control=(
            "Null: catalysis_level = 0 (every reaction is uncatalysed). The "
            "Hordijk-Steel closure returns the empty set — no RAF exists. "
            "Watch the chemistry quietly decay to the food set with no "
            "amplification. Then ramp catalysis_level back up and observe "
            "the phase transition at the Kauffman connectivity threshold."
        ),
        expect=(
            "Watch for: bright hotspots emerging where RAF members "
            "amplify themselves. The catalysis_level_x100 stat shows the "
            "Kauffman connectivity (n_reactions / n_species); above ~1.0 "
            "RAFs appear, below ~0.5 they don't."
        ),
        caveats=(
            "The food set is arbitrary; the kinetic rates are uniform. "
            "Real prebiotic networks have wildly different rate constants "
            "and energy thresholds. This demonstrates topological RAF "
            "existence — not the rate at which a specific real chemistry "
            "ignites. The Hordijk-Steel closure IS the canonical method."
        ),
        consumes="Reactant inventory inherited from Stage 1 product field.",
        produces="Modal RAF product concentration → seeds Stage 3 amphiphile field.",
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
        apparatus=(
            "A thin aqueous layer with dissolved fatty acid (decanoic acid, "
            "C10) above its critical micelle concentration. In Hanczyc & "
            "Szostak's lab work, montmorillonite clay accelerates vesicle "
            "self-assembly; here we render the bilayer-formation step "
            "directly. CMC for decanoic acid is ≈ 85 mM (AMPHIPHILE_CMC_MM)."
        ),
        methods=(
            "Lipid concentration field evolves under Gray-Scott-like "
            "reaction-diffusion. Where the field exceeds the CMC threshold, "
            "we paint the membrane mask amber and count connected "
            "components as vesicles. v3.5 added a Helfrich bending term "
            "(κ_b * (∇²φ)²) so membrane curvature responds to bending "
            "modulus, not just to the threshold gate."
        ),
        control=(
            "Null: set cmc_threshold ABOVE the field's peak. The mask stays "
            "empty (vesicle_count = 0) no matter how long you run. Then "
            "drop the threshold below the peak and watch vesicles nucleate. "
            "This pins the claim that the CMC IS the membrane-formation "
            "gate — pinned in tests/test_vesicles.py for CI as well."
        ),
        expect=(
            "Watch for: dispersed lipid (viridis) coalescing into amber "
            "membrane patches once concentration crosses CMC. Connected "
            "components grow, merge, and form bounded compartments — the "
            "first thing in the pipeline that's spatially BOUNDED."
        ),
        caveats=(
            "The CMC gate is real; the Helfrich bending is real (κ_b ≈ "
            "10⁻¹⁹ J). But we don't model osmotic pressure, fatty-acid "
            "exchange between vesicles, or division mechanics. The "
            "compartment is bounded; the lifecycle isn't dynamic in the "
            "Szostak-lab sense — that's Stage 4's job."
        ),
        consumes="Modal product concentration from Stage 2 → seeds the amphiphile field.",
        produces="Vesicle centroids + counts → seed Stage 4 protocell positions.",
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
        apparatus=(
            "A population of bounded vesicles (from Stage 3) each carrying "
            "a genome — here a vector of n binary loci. Each vesicle has a "
            "growth rate determined by its genome's fitness; division and "
            "mutation are stochastic. Conceptually this is the simplest "
            "abstract model of Darwinian evolution: heritability + "
            "variation + differential survival → adaptation."
        ),
        methods=(
            "v3.5+ uses the real Eigen-Schuster replicator ODE "
            "dx_i/dt = x_i (k_i x_{i-1} − Φ) for the genome distribution "
            "(was a static fitness proxy in v3.4). Per engine step: "
            "evolve concentrations one Euler step, grow vesicles whose "
            "dominant genome's x_i exceeds threshold, divide on radius "
            "threshold, mutate on copy."
        ),
        control=(
            "Null: mutation_rate = 0. Watch the population converge on a "
            "single genome and stay there — no exploration. Or push "
            "mutation_rate above the Eigen error threshold (≈ 1/L) and "
            "watch the master sequence MELT (error catastrophe): the "
            "population becomes a uniform smear with no inheritance."
        ),
        expect=(
            "Watch for: discs growing greener (higher fitness) as selection "
            "favours fitter genomes. After a few hundred steps the "
            "population concentrates on a few master sequences. Try the "
            "error-catastrophe regime to see the entire population melt."
        ),
        caveats=(
            "Fitness function is a hypercycle-flavoured proxy, not a "
            "biochemically grounded function of the genome. Real "
            "protocell evolution has metabolism-genotype coupling, "
            "ribozyme catalysis, and energy budgeting we don't model. "
            "The Eigen ODE IS the canonical model; the fitness landscape "
            "is the toy part."
        ),
        consumes="Vesicle centroids inherited from Stage 3.",
        produces="Population of selected replicators — the closing chapter of the canonical pipeline.",
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
    apparatus=(
        "An alkaline hydrothermal chimney: serpentinisation of ocean crust "
        "vents warm, alkaline (pH ≈ 10), H₂-rich fluid into the mildly acidic "
        "(CO₂-rich, pH ≈ 5.5) Hadean ocean. Where the two meet across the thin "
        "FeS catalytic wall there is a natural ~3–4 pH-unit proton gradient — "
        "a built-in proton-motive force, the same kind every cell still uses "
        "to make ATP (Russell, Martin & Lane's chemiosmotic origin)."
    ),
    methods=(
        "The chimney interior is held alkaline and the ocean edges acidic as "
        "Dirichlet sources; a steady proton gradient relaxes between them. "
        "Synthesis is the Wood-Ljungdahl reaction 2 CO₂ + 4 H₂ → CH₃COOH + "
        "2 H₂O run as mass-action: rate ∝ PMF · [H₂] · [CO₂], capped by the "
        "2:1 H₂:CO₂ limiting reagent, so it ignites along the wall (where the "
        "gradient is steepest), not uniformly. The Nernst factor 59.16 mV/pH "
        "maps the proton field to a real pmf_mV ≈ 266 mV readout."
    ),
    control=(
        "Null: flatten the gradient (vent pH = ocean pH). The proton-motive "
        "force collapses, pmf_mV → 0, and synthesis stops entirely — no "
        "gradient, no free energy, no chemistry. Independently, removing "
        "either feedstock (H₂ or CO₂) halts the reaction even with the "
        "gradient intact, pinning that the vent supplies both the free energy "
        "AND the carbon-fixation chemistry."
    ),
    expect=(
        "Watch for: a blue alkaline chimney against an orange ocean, with a "
        "teal-green synthesis glow tracking the interface where the gradient "
        "is steepest — never in the uniform bulk. The interface_cells and "
        "pmf_mV stats quantify the active wall; both fall to zero when the "
        "gradient is flattened."
    ),
    caveats=(
        "The proton field, pH map, and PMF/ΔG readouts are real, but the "
        "actual acetyl-CoA / Wood-Ljungdahl carbon-fixation chemistry, real "
        "FeS/FeNi mineral catalysis, and fluid flow are all abstracted away. "
        "This shows THAT a geochemical gradient can be the free-energy source "
        "and set up the fixation chemistry — not a kinetic model of it."
    ),
    consumes="Condensed monomers from the primordial soup, dissolved in the vent fluid.",
    produces="Vent-synthesised organics → seed the reaction-diffusion concentration field.",
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
    apparatus=(
        "A montmorillonite clay surface bathed in a dilute monomer solution. "
        "Condensation polymerisation (joining monomers, releasing water) is "
        "uphill in bulk water, so the open ocean stays monomeric. Ferris "
        "showed clay concentrates monomers on its charged surface and "
        "templates RNA-nucleotide chains 30–50 units long; Cairns-Smith "
        "proposed clay crystals as the first 'genetic' material."
    ),
    methods=(
        "A static clay mask sits on the grid. Monomers diffuse and are fed; "
        "polymer forms at a rate that is high ON the clay and near-zero OFF "
        "it, and polymer slowly hydrolyses everywhere. Long polymer "
        "accumulates on the clay patches while the bulk stays monomeric — the "
        "chemistry is localised to the mineral surface. The "
        "polymer_on_clay_x100 vs polymer_in_bulk_x100 stats report the "
        "surface-vs-bulk contrast directly."
    ),
    control=(
        "Null: raise the bulk-water polymerisation rate to equal the clay "
        "rate. The surface advantage disappears, polymer_on_clay_x100 and "
        "polymer_in_bulk_x100 converge, and the localisation vanishes — "
        "polymer forms everywhere or nowhere, pinning that the mineral "
        "surface IS what makes long chains thermodynamically reachable."
    ),
    expect=(
        "Watch for: teal-green polymer building up only on the tan clay "
        "patches while the dark bulk stays monomeric. polymer_on_clay_x100 "
        "should climb well above polymer_in_bulk_x100; the gap is the whole "
        "point — it collapses in the equal-rate control."
    ),
    caveats=(
        "The clay is a binary mask with a rate contrast, not real geometry. "
        "The actual templating geometry of the clay interlayer, monomer "
        "activation chemistry, and sequence selectivity are all cut. This "
        "shows surface-localised polymerisation and the bulk-vs-surface "
        "contrast, not a faithful Ferris clay-catalysis mechanism."
    ),
    consumes="Reaction-diffusion product field, read as the dissolved monomer pool.",
    produces="Clay-bound polymers → seed the RAF reactant inventory for autocatalysis.",
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
    apparatus=(
        "A Frank-model asymmetric-autocatalysis system on a reaction-diffusion "
        "field. Life is homochiral (only L-amino acids, D-sugars), yet a "
        "racemic prebiotic soup holds equal enantiomers, so something broke "
        "and amplified the mirror symmetry. Frank's mechanism: each "
        "enantiomer catalyses its own formation while opposite hands "
        "annihilate. The Soai reaction (1995) is the lab realisation."
    ),
    methods=(
        "Three coupled reactions run on the grid: A + L → 2L and A + R → 2R "
        "(autocatalysis, rate k_a) plus L + R → inert (mutual antagonism, "
        "rate k_x = k_cross). Autocatalysis + antagonism makes the racemic "
        "state unstable to fluctuations; any tiny local excess is amplified, "
        "and diffusion lets neighbouring patches break to opposite hands, "
        "forming chiral domains that then compete across the field."
    ),
    control=(
        "Null: turn the antagonism rate k_x (k_cross) toward zero. With no "
        "mutual annihilation the racemic state becomes stable, fluctuations "
        "are not amplified, and no symmetry breaking occurs — the field stays "
        "dark (racemic) everywhere. This pins that antagonism, not "
        "autocatalysis alone, is what selects a single hand."
    ),
    expect=(
        "Watch for: a dark racemic field spontaneously breaking into teal "
        "(L-dominant) and magenta (R-dominant) domains that grow and compete, "
        "one hand eventually engulfing the other. Drive k_cross → 0 and the "
        "domains never form — the field stays uniformly dark."
    ),
    caveats=(
        "The enantiomers are abstract; we model no specific autocatalyst. The "
        "proposed sources of the initial bias — parity violation "
        "(Kondepudi & Nelson), circularly polarised light, mineral surfaces — "
        "are all cut; here the bias is just numerical fluctuation. This shows "
        "the symmetry-breaking dynamics, not their physical trigger."
    ),
    consumes="RAF reaction products, treated as the racemic monomer feed A.",
    produces="A single-handed (homochiral) monomer pool → the chiral feedstock for the RNA world.",
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
    apparatus=(
        "Gilbert's RNA world: RNA serves as both genotype (a copyable "
        "template) and catalyst (a ribozyme) before the DNA/protein division "
        "of labour. The quantitative law is Eigen's quasispecies theory on a "
        "single-peak landscape — a master sequence of length L replicating "
        "with superiority σ against mutants that replicate at rate 1."
    ),
    methods=(
        "A spatial Eigen model: each cell holds an RNA strand over a 4-letter "
        "alphabet (or is empty). Empty cells are colonised by a "
        "fitness-weighted occupied neighbour (selection), and the copy is "
        "made base-by-base with per-base error ε (mutation); occupied cells "
        "die at a fixed rate. Cells are coloured by Hamming distance to the "
        "master. The error_rate_x1000 and error_threshold_x1000 stats report "
        "ε against ε_c = ln(σ)/L live."
    ),
    control=(
        "Null: drive the per-base error rate ε past the Eigen threshold "
        "ε_c = ln(σ)/L (≈ ln(10)/16 ≈ 0.14 at defaults). The master sequence "
        "can no longer be maintained against copy errors and the population "
        "melts into random sequences — the error catastrophe. Below ε_c a "
        "stable mutant cloud (quasispecies) centres on the master."
    ),
    expect=(
        "Watch for: bright master-sequence colonies holding against a halo of "
        "darker mutants while error_rate_x1000 stays below "
        "error_threshold_x1000. Push ε past the threshold and the bright "
        "colonies dissolve into a uniform dark smear — the catastrophe, live."
    ),
    caveats=(
        "Real base-pairing/templated copying chemistry, ribozyme folding, and "
        "sequence-dependent fitness landscapes are all cut — the landscape is "
        "single-peak by construction. This captures selection on that "
        "landscape, per-base mutation, and the Eigen error threshold as an "
        "observable phase transition, not real RNA replication."
    ),
    consumes="The homochiral monomer pool from the chirality stage, as single-handed RNA bases.",
    produces="A maintained population of master RNA strands → the messages the genetic code reads.",
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
    apparatus=(
        "The coevolution account of the genetic code (Wong 1975; "
        "Vetsigian-Woese-Goldenfeld 2006): why is the codon→amino-acid "
        "mapping nearly universal across all life? Each cell carries both an "
        "RNA-like strand of codons AND its own private codon→amino-acid table, "
        "so message and code can vary and be selected together — the "
        "alternative to Crick's frozen accident or Woese's stereochemistry."
    ),
    methods=(
        "Each cell decodes its own strand through its own code to produce a "
        "peptide; fitness is how well that peptide matches a fixed target "
        "catalyst. Empty cells are colonised by fitness-weighted occupied "
        "neighbours, copying the strand (per-base mutation) and the code "
        "(rare codon→amino-acid swaps at rate code_mutation). Any code that "
        "makes a more useful peptide spreads, so the population converges on "
        "a single shared code purely through selection."
    ),
    control=(
        "Null: set code_mutation = 0 so the code can never change. The "
        "population is then frozen onto whatever private codes it started "
        "with — code_consensus_x100 cannot climb toward 100, and no shared "
        "universal code emerges. Convergence requires the code itself to be a "
        "mutable, selectable trait, which is the whole coevolution claim."
    ),
    expect=(
        "Watch for: the viridis fitness field brightening as cells decode "
        "their strands into the target peptide, and code_consensus_x100 "
        "climbing toward 100 as the surviving population agrees on one "
        "codon→amino-acid table — the emergence of a universal code on screen."
    ),
    caveats=(
        "Actual stereochemistry, real ribosomal translation, and the specific "
        "historical contingencies of the canonical code are all cut. This "
        "captures the coevolutionary dynamics of message and code and "
        "selection acting on the code itself — the mechanism behind code "
        "universality — not the real chemistry of any aminoacyl pairing."
    ),
    consumes="RNA strands from the RNA world, read as codon messages awaiting a code.",
    produces="Coded peptides under a shared genetic code → coded macromolecules for the coacervate stage.",
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
    apparatus=(
        "Comparative genomics for the Last Universal Common Ancestor. We "
        "cannot dig LUCA up, so we reconstruct its genome by taking the "
        "(threshold-relaxed) intersection of gene families across all "
        "lineages. Weiss et al. (2016) ran this over ~6.1 M prokaryotic genes "
        "and recovered a ~355-family core consistent with LUCA being a "
        "hydrothermal, hydrogen-using chemolithoautotroph."
    ),
    methods=(
        "Each cell carries a gene-presence bitset; some genes are essential "
        "(high benefit), some accessory (mild), some deleterious (cost), and "
        "every gene has a maintenance cost. Selection + mutation drive the "
        "spatial population. The headline luca_size stat counts genes present "
        "in ≥ core_prevalence (70%) of surviving lineages — exactly the "
        "prevalence threshold real reconstruction uses. It climbs from random "
        "genomes and locks at the essential-gene count."
    ),
    control=(
        "Null: lower core_prevalence toward 0 (count a gene as 'core' even at "
        "trivial frequency). luca_size inflates to include accessory and even "
        "deleterious genes — the distilled core stops tracking essential_target "
        "and ceases to be a meaningful ancestral genome. The prevalence "
        "threshold IS what makes the reconstruction a real intersection."
    ),
    expect=(
        "Watch for: the viridis fitness field stabilising as lineages that "
        "drop essential genes are selected out, while luca_size climbs and "
        "locks at roughly essential_target — that locked intersection is the "
        "simulated LUCA, the genome every surviving lineage inherited."
    ),
    caveats=(
        "Actual sequence evolution, the specific metabolic genes of real "
        "LUCA, horizontal gene transfer (covered by the genetic-code stage), "
        "and protein structure are all cut. This captures comparative-genomics "
        "distillation under a benefit-vs-cost economy and the prevalence "
        "threshold — not a phylogenetic reconstruction of the true ancestor."
    ),
    consumes="The selected protocell population, read as the surviving lineages to compare.",
    produces="The inferred ancestral core genome — the closing chapter of the extended pipeline.",
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
    apparatus=(
        "Oparin's 1924 coacervates — dense, membraneless droplets that form "
        "when macromolecules spontaneously separate from solution. A different "
        "answer to 'how did chemistry get a boundary?' than Stage 3's lipid "
        "vesicles: no membrane at all, just liquid-liquid phase separation. "
        "The same physics runs modern biomolecular condensates (Banani 2017), "
        "which revived coacervates as a serious origin-of-life model."
    ),
    methods=(
        "The Cahn-Hilliard equation for a conserved order parameter φ (local "
        "composition): μ = φ³ − φ − κ∇²φ (double-well chemistry + interface "
        "energy) with ∂φ/∂t = M∇²μ (total φ preserved). From a near-uniform, "
        "slightly off-critical mixture φ separates into a rich phase (gold "
        "droplets) and a dilute phase (dark), then coarsens by Ostwald "
        "ripening — small droplets feed larger ones, neighbours fuse — so the "
        "droplets count peaks and then declines."
    ),
    control=(
        "Null knobs: κ (kappa) sets the line tension — raise it for fewer, "
        "larger droplets — and the mean composition controls how much rich "
        "phase forms; push it far off-critical and almost no droplets "
        "nucleate at all. Either way the droplets stat tracks the change, "
        "pinning that conserved phase separation, not a hard threshold, gates "
        "compartment formation."
    ),
    expect=(
        "Watch for: a near-uniform field separating into gold coacervate-rich "
        "droplets against a dark dilute phase, then coarsening — the droplets "
        "stat rises to a peak and then falls as small droplets dissolve and "
        "neighbours fuse, exactly as real coacervates do."
    ),
    caveats=(
        "The specific macromolecules (polypeptide/polynucleotide complex "
        "coacervation), electrostatics, and selective partitioning of solutes "
        "are all cut — φ is an abstract composition, not a named polymer. "
        "This captures conserved liquid-liquid phase separation, droplet "
        "nucleation, and coarsening, not the chemistry of any real coacervate."
    ),
    consumes="Coded macromolecules from the genetic-code stage, as the phase-separating solute φ.",
    produces="Membraneless droplets → compartment candidates handed to the vesicle stage.",
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
)


@dataclass
class AbiogenesisExtendedPipelineRule(AbiogenesisPipelineRule):
    """Auto-promoting pipeline that walks every shipped origin-of-life process
    (10 stages, scientific order). Drop-in replacement for the canonical
    `AbiogenesisPipelineRule` — same protocol, just a longer narrative."""

    name: str = "abiogenesis-pipeline-extended"
    stage_classes: tuple = EXTENDED_STAGE_CLASSES
    stage_infos: tuple[StageInfo, ...] = EXTENDED_STAGE_INFO
    # Each chapter card sits on-screen for ~4.5 s; pair that with a longer
    # stage_duration so transitions don't feel rushed at the default FPS.
    stage_duration: int = 90
