# The science behind cellauto

cellauto is structured around a five-stage approximation of **abiogenesis** —
the chemistry-to-life transition. The original v1.0 README called it "natural
selection," but read carefully, the four rules sketch the prebiotic-chemistry
chapter of the origin-of-life story: random mixing, condensation, activated
intermediates, compartmentalization. v3.0 honors that intuition by
implementing each stage with real (or toy-but-real-concept) scientific
machinery and citing the canonical literature.

This document is the academic appendix: what each stage *means*, where the
math comes from, and what corners are cut.

---

## Stage 0 — Primordial soup

> "Each cell takes on a random color [from its surroundings]." — original Rule 1

Discrete molecular species mixing by random Brownian-style neighbor sampling.
Same-species cells in proximity condense; freshly-formed species are reactive
(`is_new`); a successful condensation yields a primitive protocell (`amoeba`)
that persists for a fixed lifetime, then dissolves.

The honest science here is the **primordial soup hypothesis** — first
articulated by Alexander Oparin (1924, *The Origin of Life*) and J. B. S.
Haldane (1929, *Rationalist Annual*). Both independently argued that early
Earth's oceans contained dissolved organic monomers (amino acids, simple
sugars, nucleobases) that mixed and reacted to produce more complex
molecules. Stanley Miller and Harold Urey's famous 1953 experiment
demonstrated that lightning-driven discharges in a reducing atmosphere
produce amino acids, validating the soup framework.

**What this implementation captures:** mass-action mixing, condensation of
like monomers, kinetic activation lifetime.
**What it doesn't:** real thermodynamics, real reaction kinetics, the
specific organic-chemistry pathways.

**Citations**
- Oparin, A. I. (1924). *Происхождение жизни* (The Origin of Life). Moscow.
- Haldane, J. B. S. (1929). The Origin of Life. *Rationalist Annual*, 148, 3–10.
- Miller, S. L. (1953). A production of amino acids under possible primitive
  Earth conditions. *Science*, 117(3046), 528–529. doi:10.1126/science.117.3046.528

---

## Stage 1 — Reaction-diffusion

A two-species reaction-diffusion PDE on a continuous concentration field.
The mathematics:

```
∂u/∂t  =  D_u ∇²u  -  u v²  +  F (1 - u)
∂v/∂t  =  D_v ∇²v  +  u v²  -  (F + k) v
```

Two reactants u and v diffuse with coefficients D_u, D_v. The non-linear
term u v² represents an autocatalytic reaction (one molecule of v catalyses
its own production from u). F is the feed rate of u; F+k is the kill rate
of v. Despite having only four parameters, this system produces a remarkable
parameter landscape — Pearson (1993) catalogued **five qualitatively
different regimes**:

| Regime | Behaviour | (F, k) example |
|---|---|---|
| Spots | Self-replicating spots, mitosis-like division | (0.035, 0.065) |
| Stripes | Long meandering stripes | (0.04, 0.06) |
| Mitosis | Cells split and migrate | (0.037, 0.065) |
| Waves | Travelling wavefronts | (0.014, 0.045) |
| Labyrinth | Maze-like patterns | (0.039, 0.058) |

Reaction-diffusion is the mechanism Alan Turing proposed in 1952 to explain
biological pattern formation (zebra stripes, leopard spots, fingerprint
ridges). The same math drives the BZ chemical oscillator, the Liesegang
ring phenomenon, and the spatial dynamics of many real catalytic systems.

We include it as Stage 1 because **self-replicating spots in Gray-Scott
visually resemble protocell division** and constitute the simplest dynamical
system the project ships that produces emergent self-organizing structure.

**Citations**
- Turing, A. M. (1952). The chemical basis of morphogenesis. *Phil. Trans.
  Royal Society B*, 237(641), 37–72. doi:10.1098/rstb.1952.0012
- Gray, P., & Scott, S. K. (1985). Sustained oscillations and other exotic
  patterns of behaviour in isothermal reactions. *J. Phys. Chem.*, 89(1), 22–32.
- Pearson, J. E. (1993). Complex patterns in a simple system. *Science*,
  261(5118), 189–192. doi:10.1126/science.261.5118.189

---

## Stage 2 — Autocatalytic sets (Kauffman RAFs)

Stuart Kauffman's 1986 insight: **above a connectivity threshold, random
reaction networks spontaneously contain closed catalytic cycles.** A small
random sample of plausibly-pre-biotic reactions, with each reaction catalysed
by some other species, will — with high probability — include a subset whose
products collectively catalyse each other in a closed loop.

Kauffman's argument was qualitative until Hordijk & Steel (2004) gave it
rigorous form: the **RAF algorithm** finds the maximal *Reflexively
Autocatalytic Food-generated set* of reactions in a network. RAF detection
is now the canonical way to formalize "Kauffman-style autocatalysis":

1. Start with the full reaction set.
2. Compute which species are producible from the food set ∪ current
   reaction products.
3. Prune reactions whose reactants OR catalyst are not producible.
4. Repeat until stable. What remains is the maximal RAF.

A non-empty RAF means: given the food, the network can sustain itself
indefinitely; every reaction can keep firing because its prerequisites are
always being regenerated by *other* reactions in the same set.

In this stage we generate a random reaction network, find its RAF, then
simulate the chemistry on a 2D grid with diffusion. The RAF reactions fire
whenever their reactants are colocated, producing visible autocatalytic
"ignition" — bright regions where the closed loop is amplifying.

**Citations**
- Kauffman, S. A. (1986). Autocatalytic sets of proteins. *J. Theor. Biol.*,
  119(1), 1–24. doi:10.1016/S0022-5193(86)80047-9
- Kauffman, S. A. (1993). *The Origins of Order: Self-Organization and
  Selection in Evolution*. Oxford University Press.
- Hordijk, W., & Steel, M. (2004). Detecting autocatalytic, self-sustaining
  sets in chemical reaction systems. *J. Theor. Biol.*, 227(4), 451–461.
  doi:10.1016/j.jtbi.2003.11.020
- Hordijk, W., Steel, M., & Kauffman, S. A. (2012). The structure of
  autocatalytic sets: evolvability, enablement, and emergence. *Acta
  Biotheoretica*, 60(4), 379–392.

---

## Stage 3 — Vesicle formation (lipid self-assembly)

Chemistry compartmentalizes. **Amphiphilic molecules** (lipids with a
hydrophilic head and hydrophobic tail) spontaneously self-assemble into
bilayer membranes above their critical micelle concentration (CMC). The
first stable membrane around a patch of self-sustaining chemistry is a
**protocell** — the moment the universe acquires bounded chemical
individuals capable of having their own internal state.

This stage runs a Gray-Scott-like reaction-diffusion for a lipid-precursor
species, then marks regions where lipid concentration exceeds the CMC as
membrane. Connected high-lipid regions become discrete vesicles tracked by
flood-fill connected-component labelling.

**What this captures:** threshold-based self-assembly, vesicle counting.
**What it cuts:** real lipid bilayer dynamics involve Helfrich curvature
elasticity, surface tension, and fluid mechanics (Lipowsky & Sackmann 1995).
Real vesicle growth/division has been studied experimentally by Hanczyc &
Szostak (2004). A faithful implementation would be a separate research project.

**Citations**
- Helfrich, W. (1973). Elastic properties of lipid bilayers: theory and
  possible experiments. *Z. Naturforsch. C*, 28(11), 693–703.
- Deamer, D. W. (2008). Origins of life: How leaky were primitive cells?
  *Nature*, 454(7200), 37–38. doi:10.1038/454037a
- Szostak, J. W., Bartel, D. P., & Luisi, P. L. (2001). Synthesizing life.
  *Nature*, 409(6818), 387–390.
- Hanczyc, M. M., & Szostak, J. W. (2004). Replicating vesicles as models
  of primitive cell growth and division. *Curr. Opin. Chem. Biol.*, 8(6),
  660–664. doi:10.1016/j.cbpa.2004.10.002
- Lipowsky, R., & Sackmann, E. (1995). *Structure and Dynamics of
  Membranes*. North-Holland.

---

## Stage 4 — Protocell selection (hypercycle dynamics)

Once chemistry is compartmentalized, **selection becomes possible.**
Protocells with efficient internal chemistry grow; those without dissolve.
Growing protocells eventually divide, and the daughter inherits the
parent's internal state with stochastic mutation. **This is the moment
Darwinian dynamics appear** — not as an imposed law, but as a consequence
of bounded chemical individuality with heritable variation and differential
survival.

The canonical theoretical framework is Manfred Eigen and Peter Schuster's
**hypercycle** (1977): a closed loop of replicators where each member
catalyses the formation of the next. Hypercycles are evolutionarily stable
in a way isolated self-replicators are not — they sidestep Eigen's "error
catastrophe" by distributing information across multiple replicating
species.

This stage's implementation is deliberately a TOY. Each protocell carries
a vector "genome" representing its internal species mix; its fitness is the
Shannon entropy × total concentration; size grows with fitness; division at
a radius threshold creates a mutated daughter; old/small protocells die.
Real protocell evolution involves internal RAF dynamics and stochastic
mutation rates that determine the error threshold (see Adamala & Szostak's
2013 experimental work).

We include this stage to make explicit where the project's *original* claim
of "natural selection" actually lives: not in the soup, but in the
chemistry-bearing membranes that arise after compartmentalization. Once
there, the four-pillar Darwinian requirements — variation, inheritance,
selection, replication — are all present.

**Citations**
- Eigen, M. (1971). Selforganization of matter and the evolution of
  biological macromolecules. *Naturwissenschaften*, 58(10), 465–523.
- Eigen, M., & Schuster, P. (1977). The hypercycle: a principle of natural
  self-organization. Part A: emergence of the hypercycle.
  *Naturwissenschaften*, 64(11), 541–565. doi:10.1007/BF00450633
- Eigen, M., & Schuster, P. (1978). The hypercycle. Part B: the abstract
  hypercycle. *Naturwissenschaften*, 65(1), 7–41.
- Adamala, K., & Szostak, J. W. (2013). Nonenzymatic template-directed RNA
  synthesis inside model protocells. *Science*, 342(6162), 1098–1100.
- Szostak, J. W. (2017). The narrow road to the deep past: in search of the
  chemistry of the origin of life. *Angew. Chem.*, 56(37), 11037–11043.

---

## How to read the pipeline

The `abiogenesis-pipeline` rule runs the five stages in sequence with
auto-transition thresholds, so a single run walks the entire chemistry-to-
life narrative end to end. The transitions are heuristic — chosen so the
demo holds together visually, not to match any specific origin-of-life
timescale. The real Earth took ~500 million years to walk this trajectory.

You can also run any stage in isolation with `cellauto gui --rule
abiogenesis-stageN-...` or skip ahead via the GUI's **Promote stage** button.

## Honest limitations

This is a sandbox for thinking about abiogenesis, not a quantitative model.

- **Toy time/length scales.** Steps are not seconds; cells are not nm or μm.
- **No real thermodynamics.** Free energies, entropy of mixing, Gibbs
  energies of reaction are not modelled.
- **No real reaction kinetics.** Rates are mass-action with phenomenological
  constants, not Arrhenius / transition-state theory.
- **Toy membrane physics.** Stage 3 uses threshold detection rather than
  fluid simulation of lipid bilayers.
- **Toy fitness function.** Stage 4 uses Shannon entropy × concentration as
  a placeholder; real protocell fitness depends on internal RAF dynamics.

For each, the reference list above points at the rigorous treatment.
