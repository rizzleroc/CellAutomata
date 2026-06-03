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

**Real data:** the 16 molecular "species" are not abstract — they are the 16
most abundant products Miller actually recovered in 1953, and the initial soup
is sampled weighted by his reported yields (formic acid ≈ 49%, glycine ≈ 13%,
glycolic acid ≈ 12%, alanine ≈ 7%, with everything else in the tail). So the
starting grid reflects the measured composition of a spark-discharge soup
rather than a uniform rainbow — a real soup is dominated by a few simple
molecules. (See `MILLER_UREY_SPECIES` in `natural_selection.py`.)

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
| Mitosis | Cells split and migrate | (0.0367, 0.0649) |
| Waves | Travelling wavefronts | (0.014, 0.045) |
| Labyrinth | Maze-like patterns | (0.039, 0.058) |

**Numerics.** We integrate with forward Euler on a unit grid (dx = 1, dt = 1)
and a 5-point Laplacian — the standard non-dimensional "xmorphia"
parameterization with `Du = 0.16, Dv = 0.08`. These are *rescaled* values, not
Pearson's original `Du = 2×10⁻⁵, Dv = 10⁻⁵` on the unit square; space and time
are non-dimensionalized, so the patterns are faithful while the raw constants
differ. The explicit-diffusion stability bound for a 2D 5-point stencil is
`D·dt/dx² ≤ 1/4`; here the largest term is `0.16 ≤ 0.25`, so the scheme is
stable with margin. (The integrator clips `u, v` to `[0, 1]`, which keeps a
demo well-behaved but would also mask a true instability if you pushed `dt`
past the bound.)

The `Du : Dv = 2 : 1` ratio is a *modelling* choice, not a measured chemical
ratio: Turing patterns require the inhibitor to diffuse faster than the
activator, and a ratio around 2 reliably lands in the pattern-forming regime.
Real small-molecule aqueous diffusion coefficients are all of order
`10⁻⁹ m²/s` (glycine `D ≈ 1.06×10⁻⁹ m²/s`; most metabolites cluster in
`0.5–1×10⁻⁹`), differing by far less than 2× — so the qualitative requirement
"inhibitor diffuses faster" is the physically meaningful part, while the exact
factor is tuned for the demonstration.

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

**Real data:** the membrane is identified with a named fatty acid whose
*measured* critical micelle concentration anchors the threshold (`decanoic
acid (C10)` ≈ 85 mM, `octanoic (C8)` ≈ 250 mM, `oleic (C18:1)` ≈ 0.1 mM; see
`AMPHIPHILE_CMC_MM`). C8–C10 monocarboxylic acids are the prebiotic sweet
spot — the species Deamer extracted from the Murchison meteorite that form
vesicles under early-Earth conditions. The simulation field is normalized so
1.0 corresponds to the chosen amphiphile's CMC.

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

## RNA world — spatial quasispecies and the error catastrophe

Selectable directly as the `abiogenesis-rna-world` rule (not yet woven into the
auto-promoting pipeline). Walter Gilbert's 1986 **RNA world** hypothesis is the
dominant modern picture of early life: RNA served as both genotype (a copyable
template) and catalyst (a ribozyme) before the DNA/protein division of labour.
The quantitative law that governs any such self-replicator is Eigen's
**quasispecies** theory.

For a single-peak fitness landscape — a "master" sequence of length *L* that
replicates with superiority σ, every mutant replicating at rate 1 — the master
is maintained only while the per-base copy-error rate stays below the
**error threshold**:

```
ε_c  =  ln(σ) / L
```

Below ε_c the population is a quasispecies: a mutant cloud centred on the
master. Above ε_c the master is lost and the population melts into random
sequences — the **error catastrophe**. This stage is a spatial Eigen model:
each cell holds an RNA strand over a 4-letter alphabet (or is empty); empty
cells are colonised by a *fitness-weighted* occupied neighbour (selection), and
the copy is made base-by-base with per-base error ε (mutation); occupied cells
die at a fixed rate. Cells are coloured by Hamming distance to the master
(bright = master, dark = far mutant). Dragging the error-rate slider past
ε_c ≈ ln(10)/16 ≈ 0.14 reproduces the catastrophe live.

**What this captures:** selection on a single-peak landscape, per-base
mutation, and the Eigen error threshold as an observable phase transition.
**What it cuts:** real base-pairing/templated copying chemistry, ribozyme
folding, and sequence-dependent fitness landscapes.

**Citations**
- Gilbert, W. (1986). The RNA World. *Nature*, 319, 618.
- Eigen, M. (1971). Selforganization of matter… *Naturwissenschaften*, 58(10),
  465–523.
- Spiegelman, S. (1971). An approach to the experimental analysis of
  precellular evolution. *Q. Rev. Biophys.*, 4(2–3), 213–253.
- Joyce, G. F. (2002). The antiquity of RNA-based evolution. *Nature*,
  418(6894), 214–221.

---

## Origin of the genetic code — coevolution of message and code

Selectable as the `abiogenesis-genetic-code` rule. The deepest unsolved
problem at the chemistry-to-biology boundary is the origin of the **genetic
code** itself: why is the codon→amino-acid mapping (nearly) universal across
all life, and how did it arise? Three classic answers:

- **Stereochemical** (Woese 1965): codons and their amino acids are physically
  matched — the code reflects molecular complementarity.
- **Coevolution** (Wong 1975; Vetsigian, Woese & Goldenfeld 2006): the code
  and the messages it interprets coevolve, and innovation-sharing among
  proto-organisms drives the population to converge on a single shared code.
- **Frozen accident** (Crick 1968): whatever code happened first locked in.

This stage models the **coevolution** account. Each cell on the grid carries
both an RNA-like strand of codons *and* its own private codon→amino-acid
table. Each cell decodes its own strand through its own code to produce a
peptide; fitness is how well that peptide matches a fixed target catalyst.
Empty cells are colonised by fitness-weighted occupied neighbours, copying
both the strand (with per-base mutation) and the code (with rare swaps). Any
code that happens to make a more useful peptide spreads. The
`code_consensus` population stat tracks how much the surviving population
agrees on the code: convergence toward 1.0 is the emergence of a universal
genetic code.

**What this captures:** the coevolutionary dynamics of message and code, and
selection acting on the code itself — the mechanism behind the universality
of the genetic code (Vetsigian-Woese-Goldenfeld 2006).
**What it cuts:** actual stereochemistry, actual translation by ribosomes,
and the specific historical contingencies that shaped the canonical code.

**Citations**
- Crick, F. H. C. (1968). The origin of the genetic code. *J. Mol. Biol.*,
  38(3), 367–379.
- Woese, C. R. (1965). On the evolution of the genetic code. *PNAS*, 54,
  1546–1552.
- Wong, J. T.-F. (1975). A co-evolution theory of the genetic code. *PNAS*,
  72(5), 1909–1912.
- Vetsigian, K., Woese, C., & Goldenfeld, N. (2006). Collective evolution and
  the genetic code. *PNAS*, 103(28), 10696–10701.
- Koonin, E. V. (2017). Frozen accident pushing 50… *Life*, 7(2), 22.

---

## Homochirality — spontaneous mirror-symmetry breaking

Selectable as the `abiogenesis-homochirality` rule. Life is **homochiral**: it
uses only L-amino acids and D-sugars, never their mirror images. A racemic
prebiotic soup has equal amounts of each enantiomer, so something broke the
mirror symmetry and amplified one hand to exclusivity. F. C. Frank's 1953 model
shows the mechanism: **autocatalysis** (each enantiomer catalyses its own
formation) plus **mutual antagonism** (opposite hands annihilate) makes the
racemic state unstable — any tiny fluctuation is amplified until one hand wins.

```
A + L → 2L      (autocatalysis,    rate k_a)
A + R → 2R      (autocatalysis,    rate k_a)
L + R → inert   (mutual antagonism, rate k_x)
```

On the 2D reaction-diffusion field, local patches spontaneously break to
opposite handedness, forming **chiral domains** (teal = L-dominant, magenta =
R-dominant) that then compete. Turning the antagonism rate k_x toward zero
restores a stable racemic state — no symmetry breaking. The **Soai reaction**
(1995) is the laboratory realisation of asymmetric autocatalysis amplifying a
tiny enantiomeric excess to near-homochirality.

**What this captures:** autocatalysis + mutual antagonism, spontaneous
symmetry breaking, and spatial chiral-domain formation/competition.
**What it cuts:** the actual chemistry of a specific autocatalyst, and the
proposed sources of the initial bias (Kondepudi & Nelson 1985 on parity
violation; circularly polarised light; mineral surfaces).

**Citations**
- Frank, F. C. (1953). On spontaneous asymmetric synthesis. *Biochim. Biophys.
  Acta*, 11, 459–463.
- Soai, K., et al. (1995). Asymmetric autocatalysis and amplification of
  enantiomeric excess. *Nature*, 378, 767–768.
- Blackmond, D. G. (2004). Asymmetric autocatalysis and its implications for
  the origin of homochirality. *PNAS*, 101(16), 5732–5736.
- Kondepudi, D. K., & Nelson, G. W. (1985). Weak neutral currents and the
  origin of biomolecular chirality. *Nature*, 314, 438–441.

---

## Alkaline hydrothermal vents — a proton gradient does the work

Selectable as the `abiogenesis-hydrothermal-vent` rule. This is the
**metabolism-first** alternative to the lightning-powered soup. Serpentinisation
of ocean crust produces warm, alkaline (pH ~9–11), H₂-rich vent fluid; the early
ocean was mildly acidic (CO₂-rich, pH ~5–7). Where the two meet across the thin
catalytic (FeS) walls of a vent chimney there is a natural **proton gradient** of
~3–4 pH units — a built-in proton-motive force, the very same kind of gradient
every living cell still uses to make ATP (chemiosmosis).

Lane & Martin (2012) argue that this geochemical gradient, *not* a hand-set feed
rate, is the free-energy source for the first carbon fixation. The stage models
exactly that: the chimney interior is held alkaline and the ocean edges acidic
(Dirichlet sources), a steady gradient forms between them, and organic matter is
synthesised in proportion to the **steepness** of the local gradient — so
synthesis ignites along the chimney wall (the interface), not uniformly. Flatten
the gradient (vent pH = ocean pH) and synthesis stops entirely: no gradient, no
free energy, no chemistry. Blue = alkaline, orange = acidic, teal-green glow =
organic synthesis.

**What this captures:** a fixed geochemical proton gradient as the energy
source, and interface-localised synthesis driven by the proton-motive force.
The stage exposes **real thermodynamic readouts**: the abstract proton field
maps to actual pH (alkaline ≈ 10, ocean ≈ 5.5 by default — the early-Earth
ocean estimate of Krissansen-Totton et al. 2018); at 25 °C the Nernst factor
2.303 RT/F ≈ 59.16 mV per pH unit gives the proton-motive force directly
(PMF ≈ 266 mV at default ΔpH = 4.5), and Faraday's constant converts that to
the available free energy (ΔG ≈ −26 kJ/mol per proton). Those numbers sit
comfortably above ATP synthase's ~150 mV threshold and in the range
Lane & Martin argue can drive abiotic carbon fixation.

**The chemistry the gradient drives is the Wood-Ljungdahl pathway.** The
stage tracks dissolved H₂ (replenished inside the alkaline chimney by
serpentinisation) and dissolved CO₂ (globally fed from the CO₂-rich Hadean
ocean), and the synthesis term is a proper mass-action reaction with the
real net stoichiometry

```
2 CO₂ + 4 H₂ → CH₃COOH + 2 H₂O      (ΔG° ≈ −95 kJ/mol)
```

Rate ∝ PMF · [H₂] · [CO₂], capped by the 2 : 1 H₂ : CO₂ requirement (the
limiting reagent is enforced). Take either feedstock away and the reaction
stops *even though the proton gradient is still there* — exactly the
Russell-Martin-Sojo argument that the alkaline-vent geochemistry sets up
not just a free-energy source but the actual carbon-fixation chemistry that
became central metabolism.
**What it cuts:** the actual carbon-fixation chemistry (acetyl-CoA / Wood-
Ljungdahl pathway), real FeS/FeNi mineral catalysis, and fluid flow.

**Citations**
- Russell, M. J., & Hall, A. J. (1997). The emergence of life from iron
  monosulphide bubbles… *J. Geol. Soc.*, 154(3), 377–402.
- Martin, W., & Russell, M. J. (2007). On the origin of biochemistry at an
  alkaline hydrothermal vent. *Phil. Trans. R. Soc. B*, 362, 1887–1925.
- Lane, N., & Martin, W. F. (2012). The origin of membrane bioenergetics.
  *Cell*, 151(7), 1406–1416.
- Sojo, V., et al. (2016). The origin of life in alkaline hydrothermal vents.
  *Astrobiology*, 16(2), 181–197.

---

## Coacervates — membraneless compartments by phase separation

Selectable as the `abiogenesis-coacervate` rule. This is the *original*
protocell idea — Alexander Oparin's 1924 **coacervates**: dense, membraneless
droplets that form when macromolecules spontaneously separate from solution.
It's a different answer to "how did chemistry get a boundary?" than Stage 3's
lipid vesicles: no membrane at all, just liquid-liquid phase separation. The
same physics underlies modern **biomolecular condensates** (membraneless
organelles), which has revived coacervates as a serious origin-of-life model.

The dynamics are the **Cahn-Hilliard equation** — phase separation with a
*conserved* order parameter φ (local composition):

```
μ      =  φ³ − φ − κ ∇²φ      (double-well chemistry + interface energy)
∂φ/∂t  =  M ∇²μ               (conserved: total φ is preserved)
```

From a near-uniform, slightly off-critical mixture, φ separates into a
coacervate-rich phase (gold droplets) and a dilute phase (dark), then
**coarsens**: small droplets dissolve to feed larger ones (Ostwald ripening)
and neighbours fuse, so the droplet count peaks and then declines — exactly as
real coacervates do. κ sets the line tension (bigger → fewer, larger droplets)
and the mean composition controls how much rich phase forms.

**What this captures:** conserved liquid-liquid phase separation, droplet
nucleation, and coarsening.
**What it cuts:** the specific macromolecules (polypeptide/polynucleotide
complex coacervation), electrostatics, and selective partitioning of solutes.

**Citations**
- Oparin, A. I. (1924). *The Origin of Life*. (Coacervate hypothesis.)
- Bungenberg de Jong, H. G. (1932). Coacervation. *(original coacervate work)*
- Cahn, J. W., & Hilliard, J. E. (1958). Free energy of a nonuniform system.
  *J. Chem. Phys.*, 28(2), 258–267.
- Banani, S. F., et al. (2017). Biomolecular condensates. *Nat. Rev. Mol. Cell
  Biol.*, 18, 285–298.

---

## Mineral-surface catalysis — the first polymers form on clay

Selectable as the `abiogenesis-mineral-catalysis` rule. **Condensation
polymerisation** (joining monomers into chains, releasing water) is uphill in
bulk water, so dilute monomers don't spontaneously form long polymers in the
open ocean. Mineral surfaces fix this. James Ferris showed **montmorillonite
clay** catalyses RNA-nucleotide polymerisation into 30–50-unit chains by
concentrating monomers on its charged surface and templating bond formation;
A. G. Cairns-Smith proposed clay crystals as the first "genetic" material.

The stage models surface catalysis directly: a static **clay mask** sits on the
grid; monomers diffuse and are fed; polymer forms at a rate that is high *on*
the clay and near-zero *off* it; polymer slowly hydrolyses everywhere. Long
polymer accumulates on the clay patches (teal-green) while the bulk (dark) stays
monomeric — the chemistry is localised to the mineral surface. Raise the
bulk-water rate to equal the clay rate and the localisation vanishes.

**What this captures:** surface-localised polymerisation, the bulk-water vs
mineral-surface contrast, and slow hydrolysis.
**What it cuts:** the real templating geometry of the clay interlayer, monomer
activation chemistry, and sequence selectivity.

**Citations**
- Ferris, J. P., Hill, A. R., Liu, R., & Orgel, L. E. (1996). Synthesis of long
  prebiotic oligomers on mineral surfaces. *Nature*, 381, 59–61.
- Cairns-Smith, A. G. (1982). *Genetic Takeover and the Mineral Origins of
  Life*. Cambridge University Press.
- Hanczyc, M. M., Fujikawa, S. M., & Szostak, J. W. (2003). Experimental models
  of primitive cellular compartments. *Science*, 302, 618–622.
- Hazen, R. M., & Sverjensky, D. A. (2010). Mineral surfaces… and the origins of
  life. *CSH Perspect. Biol.*, 2, a002162.

---

## LUCA distillation — the last universal common ancestor

Selectable as the `abiogenesis-luca` rule. Every organism alive today
descends from a single inferred ancestor, the **Last Universal Common
Ancestor (LUCA)**. We cannot dig it up; we reconstruct its genome by
**comparative genomics** — taking the (threshold-relaxed) intersection of
gene families across all sequenced lineages. Weiss et al. (2016) ran this
analysis over ~6.1 million prokaryotic protein-coding genes and recovered a
core gene set (~355 protein families) consistent with LUCA being a
hydrothermal, hydrogen-using chemolithoautotroph.

This stage models that distillation. Each cell carries a gene-presence
bitset; some genes are essential (high fitness), some accessory (mild), some
deleterious (cost), and every gene has a maintenance cost. Selection +
mutation drive the population; the headline `luca_size` stat is the number
of genes present in ≥ 70% of surviving lineages — exactly the kind of
prevalence threshold real LUCA reconstruction uses. From random initial
genomes, `luca_size` climbs and locks at roughly the essential-gene count
(12 by default). That intersection IS the simulated LUCA, the genome every
lineage inherited.

**What this captures:** comparative-genomics distillation of a core ancestral
genome under selection, the trade-off between gene benefit and genome-size
cost, and the gene-prevalence threshold real reconstruction relies on.
**What it cuts:** actual sequence evolution, the specific metabolic genes of
real LUCA, horizontal gene transfer (the `abiogenesis-genetic-code` stage
covers that part), and protein structure.

**Citations**
- Koonin, E. V. (2003). Comparative genomics, minimal gene-sets and the last
  universal common ancestor. *Nat. Rev. Microbiol.*, 1, 127–136.
- Theobald, D. L. (2010). A formal test of the theory of universal common
  ancestry. *Nature*, 465, 219–222.
- Weiss, M. C., et al. (2016). The physiology and habitat of the last
  universal common ancestor. *Nat. Microbiol.*, 1, 16116.
- Mirkin, B. G., et al. (2003). Parsimonious evolutionary scenarios for
  genome evolution. *BMC Evol. Biol.*, 3, 2.

---

## How to read the pipeline

The `abiogenesis-pipeline` rule runs the five stages in sequence with
auto-transition thresholds, so a single run walks the entire chemistry-to-
life narrative end to end. The transitions are heuristic — chosen so the
demo holds together visually, not to match any specific origin-of-life
timescale. The real Earth took ~500 million years to walk this trajectory.

You can also run any stage in isolation with `cellauto gui --rule
abiogenesis-stageN-...` or skip ahead via the GUI's **Promote stage** button.

## SEM mode is a rendering choice, not new physics

v4.0 ships a depth-shaded "scanning-electron-microscope" rendering path
(`cellauto/renderer_sem.py`) alongside the v3.6 viridis renderer. **The
simulation maths, constants, dynamics, RNG handling, and snapshot format
are unchanged from v3.6.** Toggling `View ▸ SEM mode` does not introduce
new physics, new species, new reactions, or new free parameters. The same
seed under SEM mode and under viridis produces the same step count, the
same population stats, and the same internal state.

What SEM mode *does* is reinterpret the existing per-stage
`render_rgb(state)` output as a height field, then apply Lambertian +
ambient + specular shading, a value-noise micro-texture, a sepia or mono
LUT, and a LANCZOS upscale, before overlaying the LIVE SEM FEED badge,
crosshair, and scale bar. Every SEM pixel still traces back to a real
engine value: the height-from-luminance step is deterministic and
invertible up to the LUT.

The depth shading is therefore **interpretive, not measurement**. The
scale bar is a visual reference for the grid extent, not a calibrated
micron readout. The "LIVE SEM FEED" badge is a framing device borrowed
from instrument UIs; it does not imply that the simulation is being run
against electron-microscope data. Readers familiar with real SEM
micrographs should treat the v4.0 rendering as a stylised presentation
of the v3.6 dynamics, not as a replacement instrument output.

This framing is deliberate. The v3.x line earned scientific credibility
through coupled dynamics (G1), the real Eigen-Schuster ODE (G2), Helfrich
bending (G3), the Miyazawa-Jernigan landscape (G4), and the pathway-graph
LUCA distillation (G5). The v4.0 line is about scientific *representation*
on top of that engine — making the chemistry-to-life story read as a
microscope view rather than a heat-map. The two are independent. If you
want the raw scientific signal without the shading, `View ▸ SEM mode`
turns it off and the v3.6 viridis path renders the same state.

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
