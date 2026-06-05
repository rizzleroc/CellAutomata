"""The 10-part explainer SERIES script — data only. Grounded in the actual code
(rules, defaults, presets, citations) and verified to render via render_rgb.
Consumed by tools/series.py."""

# helpers to keep scenes terse
def T(title, sub, vo): return dict(kind="title", title=title, sub=sub, vo=vo)
def E(rule, cap, vo, cfg=None, mode="central", warm=80, grid=180, crisp=False):
    return dict(kind="engine", rule=rule, cfg=cfg or {}, mode=mode, warm=warm, grid=grid, crisp=crisp, cap=cap, vo=vo)
def GS(cap, vo, cfg, warm=300):
    return dict(kind="engine", rule="abiogenesis-stage1-grayscott", cfg=cfg, mode="scatter", warm=warm, grid=200, cap=cap, vo=vo)
def C(cmd, knobs, cap, vo): return dict(kind="command", cmd=cmd, knobs=knobs, cap=cap, vo=vo)
def REL(cap, vo, pal="gold", cfg=None, **kw): return dict(kind="relit", pal=pal, cfg=cfg or dict(F=0.026, k=0.055), cap=cap, vo=vo, **kw)
def MAN(cap, vo, **kw): return dict(kind="mandala", cap=cap, vo=vo, **kw)
def GRID(cap, vo): return dict(kind="grid", cap=cap, vo=vo)

PARTS = [
    # ---- PART 1 ----
    dict(slug="overview", title="What is CellAutomata?", scenes=[
        T("What is CellAutomata?", "Simple rules → life-like worlds. The science, the art, and the sandbox.",
          "What if life-like complexity needed nothing but a few simple rules?"),
        GS("An open-source sandbox", "CellAutomata is an open-source sandbox where dead-simple rules grow life-like worlds.", dict(preset="mitosis")),
        E("conway", "From Life to the origin of life", "From Conway's Game of Life, to the chemistry of the origin of life itself.", crisp=True, warm=60, grid=130),
        GRID("Search thousands of sims", "It can even search thousands of simulations at once for the most alive-looking ones."),
        C(["cellauto export --rule abiogenesis-stage1-grayscott \\",
           "   --rule-config preset=mitosis --grid 200 \\",
           "   --steps 120 --fps 12 --out mitosis.gif"],
          [("--rule", "which world to run"), ("--rule-config", "tune any knob (preset, F, k, ...)"),
           ("--seed", "reproduce it exactly"), ("--steps / --fps / --canvas", "length & resolution")],
          "One command, fully reproducible",
          "Everything runs from one command: pick a rule, tune its knobs, set a seed, and it's reproducible forever."),
        REL("A 10-part guide", "Over ten parts, we'll explain exactly how each world works — and how to make it your own.", pal="amethyst"),
    ]),
    # ---- PART 2 ----
    dict(slug="grayscott", title="Gray-Scott Reaction-Diffusion", scenes=[
        T("Gray-Scott Reaction-Diffusion", "Two chemicals, four numbers, endless patterns.",
          "The heart of CellAutomata is reaction-diffusion."),
        GS("Feed U, kill V", "Two chemicals react and spread: one feeds the reaction, the other kills it.", dict(preset="spots")),
        GS("F and k control everything", "Tune two numbers — the feed rate F and the kill rate k — and spots grow, then divide like cells.", dict(preset="mitosis")),
        GS("spots · stripes · mazes · waves", "Nudge them again and you get mazes, stripes, or travelling waves.", dict(preset="labyrinth")),
        REL("Turing patterns, 1952", "It's the same Turing mechanism that paints a leopard's spots and a zebra's stripes.", pal="gold", cfg=dict(F=0.026, k=0.055)),
        C(["cellauto export --rule abiogenesis-stage1-grayscott \\",
           "   --rule-config F=0.0367 --rule-config k=0.0649 \\",
           "   --rule-config Du=0.16 --rule-config Dv=0.08 --out gs.gif"],
          [("preset", "spots / stripes / mitosis / waves / labyrinth"), ("F   (0.01–0.10)", "feed rate of U"),
           ("k   (0.04–0.075)", "kill rate of V"), ("Du / Dv  (0.16 / 0.08)", "diffusion — keep ~2:1"),
           ("substeps_per_frame (10)", "PDE stability")],
          "Tune F, k, Du, Dv",
          "Five presets get you started, or set F, k, and the diffusion rates by hand and explore the whole map."),
    ]),
    # ---- PART 3 ----
    dict(slug="conway", title="Conway's Game of Life", scenes=[
        T("Conway's Game of Life", "Four rules, infinite behaviour.", "The most famous cellular automaton of all."),
        E("conway", "Born on 3, survive on 2 or 3", "One rule decides life and death: a cell is born with three live neighbours, and survives with two or three.", crisp=True, warm=2, grid=120),
        E("conway", "Gliders, oscillators, guns", "From that, gliders crawl, blinkers blink, and whole machines self-assemble.", crisp=True, warm=40, grid=120),
        E("conway", "It's Turing-complete", "A random scribble can stay alive for thousands of generations before it settles — and the game can compute anything.", crisp=True, warm=120, grid=140),
        C(["cellauto export --rule conway --grid 120 \\",
           "   --rule-config initial_density=0.35 \\",
           "   --rule-config wrap=true --steps 200 --out life.gif"],
          [("initial_density (0.35)", "fraction starting alive"), ("wrap (true)", "toroidal edges — gliders re-enter"),
           ("--seed", "pick which random soup"), ("--grid", "world size")],
          "density · wrap · seed",
          "Set the starting density, wrap the edges into a torus, and pick a seed to choose your universe."),
    ]),
    # ---- PART 4 ----
    dict(slug="wolfram", title="Wolfram's Elementary Automata", scenes=[
        T("Wolfram's Elementary Automata", "One line of cells, 256 universes.", "Now the simplest computers imaginable."),
        E("wolfram1d", "1D rule, 2D history", "A single row of cells updates from its neighbours, and its history scrolls down the screen.", cfg=dict(rule_number=30), crisp=True, warm=0, grid=130),
        E("wolfram1d", "Rule 90 — a fractal", "Each of the 256 rules is just a number. Rule 90 draws a perfect fractal.", cfg=dict(rule_number=90), crisp=True, warm=0, grid=130),
        E("wolfram1d", "Rule 30 — pure chaos", "Rule 30 makes pure chaos — random enough to generate random numbers.", cfg=dict(rule_number=30), crisp=True, warm=0, grid=130),
        E("wolfram1d", "Rule 110 — Turing-complete", "And Rule 110 is Turing-complete: this one line of cells can compute anything.", cfg=dict(rule_number=110), crisp=True, warm=0, grid=130),
        C(["cellauto export --rule wolfram1d \\",
           "   --rule-config rule_number=110 \\",
           "   --grid 100 --steps 100 --out rule110.gif"],
          [("rule_number (0–255)", "which of the 256 rules"), ("30 / 90 / 110", "chaos / fractal / universal"),
           ("--grid", "row width"), ("--steps", "generations of history")],
          "rule_number 0–255",
          "Change one number from zero to two-fifty-five, and a completely different universe unfolds."),
    ]),
    # ---- PART 5 ----
    dict(slug="pipeline", title="The Abiogenesis Pipeline", scenes=[
        T("The Abiogenesis Pipeline", "Chemistry to life, in scientific stages.", "Now the project's beating heart: the origin of life."),
        E("abiogenesis-pipeline-extended", "Soup → LUCA", "A pipeline walks from dead chemistry all the way to the last universal common ancestor.", warm=20, grid=160),
        E("abiogenesis-stage0-soup", "Stage 0 — primordial soup", "It begins as a primordial soup — sixteen molecules, weighted by Miller's 1953 spark-discharge yields.", warm=40, grid=150),
        E("abiogenesis-hydrothermal-vent", "Each stage seeds the next", "Each stage hands its result to the next, seeding new chemistry where the last one lit up.", warm=60, grid=150),
        GS("12 stages of real science", "Reaction-diffusion, autocatalysis, membranes, selection — twelve scientific stages in all.", dict(preset="mitosis")),
        C(["cellauto gui --rule abiogenesis-pipeline-extended \\",
           "   --grid 100 --seed 999",
           "cellauto simulate --stage 4 --steps 200 --save run.json"],
          [("--stage / starting_stage", "jump straight to any stage"), ("stage_duration (90)", "steps per stage"),
           ("auto_promote (true)", "advance automatically"), ("--load run.json", "resume a saved run")],
          "Jump to any stage",
          "Watch the whole journey, or jump straight to any stage with a single flag."),
    ]),
    # ---- PART 6 ----
    dict(slug="early-chemistry", title="Soup, Vents & Mineral Catalysis", scenes=[
        T("Soup, Vents & Mineral Catalysis", "Where the first chemistry happens.", "Where does the first chemistry actually come from?"),
        E("abiogenesis-stage0-soup", "Miller–Urey, 1953", "In the soup, lightning-made molecules diffuse, combine, and form the very first compartments.", warm=50, grid=150),
        E("abiogenesis-hydrothermal-vent", "Lane–Martin vents", "At an alkaline vent, acidic ocean meets alkaline fluid — a built-in proton gradient that powers carbon fixation.", warm=70, grid=150),
        E("abiogenesis-mineral-catalysis", "Clay catalysis — Ferris", "On clay surfaces, monomers concentrate and snap into polymers that never form in open water.", warm=60, grid=150),
        C(["cellauto export --rule abiogenesis-hydrothermal-vent \\",
           "   --rule-config vent_alkalinity=0.05 \\",
           "   --rule-config ocean_acidity=0.95 --out vent.gif"],
          [("vent_alkalinity / ocean_acidity", "the pH gradient (~4.5 units)"), ("k_synth (6.0)", "Wood–Ljungdahl rate"),
           ("clay_patches (9)", "number of clay sites"), ("amoeba_lifespan (25)", "soup compartment lifetime")],
          "Tune the gradient & catalysts",
          "Turn the pH gradient up or down, add clay patches, and watch the chemistry respond."),
    ]),
    # ---- PART 7 ----
    dict(slug="self-replication", title="Self-Replication", scenes=[
        T("Self-Replication", "Autocatalytic sets and the RNA world.", "How does chemistry start copying itself?"),
        E("abiogenesis-stage2-raf", "Reflexively autocatalytic sets", "Kauffman's idea: a random web of reactions can close on itself, each one catalysing another.", warm=40, grid=150),
        E("abiogenesis-stage2-raf", "Crossing the threshold", "Above a connectivity threshold the network ignites — lifeless chemistry bootstraps into self-sustaining.", warm=90, grid=150),
        E("abiogenesis-rna-world", "RNA quasispecies — Eigen", "In the RNA world, strands copy themselves with errors — and Eigen found a hard limit.", cfg=dict(error_rate=0.02), warm=60, grid=130),
        E("abiogenesis-rna-world", "The error catastrophe", "Copy too sloppily — past the error threshold — and the master sequence melts into noise.", cfg=dict(error_rate=0.22), warm=70, grid=130),
        C(["cellauto export --rule abiogenesis-rna-world \\",
           "   --rule-config error_rate=0.20 \\",
           "   --rule-config superiority=10 --out catastrophe.gif"],
          [("error_rate (0.02)", "copy error per base"), ("superiority (10)", "master's advantage σ"),
           ("seq_length (16)", "genome length L"), ("threshold ≈ ln(σ)/L", "raise error_rate past it!")],
          "error_rate vs the threshold",
          "Push the error rate past l-n sigma over L, and watch order collapse in real time."),
    ]),
    # ---- PART 8 ----
    dict(slug="compartments", title="Compartments & Selection", scenes=[
        T("Compartments & Selection", "Vesicles, coacervates, hypercycles.", "Now chemistry needs a body — a compartment."),
        E("abiogenesis-stage3-vesicles", "Vesicles — fatty-acid membranes", "Fatty acids self-assemble into membranes once they cross their critical concentration.", warm=80, grid=150),
        E("abiogenesis-coacervate", "Coacervates — phase separation", "Or chemistry can simply demix into oily droplets — the membraneless compartments Oparin imagined.", warm=90, grid=150),
        E("abiogenesis-stage4-selection", "Protocell selection", "Wrap a self-copying cycle in a membrane and you get protocells that grow, divide, and compete.", warm=90, grid=150),
        E("abiogenesis-stage4-selection", "Eigen–Schuster hypercycle", "It's a hypercycle — a closed loop of catalysts, only as strong as its weakest member.", warm=140, grid=150),
        C(["cellauto export --rule abiogenesis-stage4-selection \\",
           "   --rule-config mutation_rate=0.30 \\",
           "   --rule-config n_species=4 --out melt.gif"],
          [("mutation_rate (0.02)", "per-gene mutation"), ("n_species (4)", "genome length"),
           ("error_threshold = 1/n", "exceed it → catastrophe"), ("amphiphile / cmc_threshold", "fatty acid & vesicles"),
           ("kappa_bend (0.025)", "membrane stiffness")],
          "Tune mutation & membranes",
          "Raise mutation past one-over-n, and the protocells lose their identity entirely."),
    ]),
    # ---- PART 9 ----
    dict(slug="information-luca", title="Information & LUCA", scenes=[
        T("Information & LUCA", "Handedness, the code, and the common ancestor.", "Finally — information, and the ancestor of us all."),
        E("abiogenesis-homochirality", "Homochirality — Frank, 1953", "Life is one-handed. From a fifty-fifty mix, autocatalysis and antagonism let one mirror-image win.", warm=80, grid=150),
        E("abiogenesis-genetic-code", "The genetic code evolves", "Each cell carries a private codon-to-amino-acid code; selection makes them converge on one shared code.", warm=90, grid=150),
        E("abiogenesis-luca", "LUCA by comparative genomics", "At the end, we intersect every surviving genome to distil their common ancestor.", warm=110, grid=150),
        E("abiogenesis-luca", "Weiss et al., 2016", "The core genes that no lineage can lose — that intersection IS the simulated LUCA.", warm=170, grid=150),
        C(["cellauto export --rule abiogenesis-homochirality --out chiral.gif",
           "cellauto export --rule abiogenesis-luca \\",
           "   --rule-config n_genes=16 --out luca.gif"],
          [("k_auto / k_cross", "autocatalysis vs antagonism"), ("n_genes (16)", "gene-presence bits"),
           ("per_gene_mutation (0.01)", "gene loss / gain"), ("watch luca_size", "converges to the core genome")],
          "Tune chirality & genes",
          "Tune handedness, or gene mutation, and watch the common core emerge."),
    ]),
    # ---- PART 10 ----
    dict(slug="sandbox-to-art", title="From Sandbox to Art", scenes=[
        T("From Sandbox to Art", "Search, palettes, kaleidoscope, relighting.", "So how did the simulations become art?"),
        GRID("16-way discovery search", "A sixteen-way search runs thousands of simulations and scores them for complexity and life."),
        MAN("Kaleidoscope folding", "Fold a field into n-fold symmetry, and reaction-diffusion becomes a mandala.", pal="nebula", n1=12, n2=6, octs=1),
        REL("3D normal-map relighting", "Treat it as a heightfield, light it, and flat math becomes molten gold.", pal="gold", cfg=dict(F=0.018, k=0.05)),
        REL("Deterministic · 4K", "Every frame stays deterministic — a seed and a few parameters rebuild it in 4K.", pal="ice", cfg=dict(F=0.0545, k=0.062), bump=4.2, shin=44, ks=1.2),
        C(["cellauto export --rule abiogenesis-stage1-grayscott \\",
           "   --rule-config preset=mitosis --seed 5650 \\",
           "   --grid 256 --steps 300 --canvas 1080 --out art.gif"],
          [("--seed", "owns the exact result"), ("--canvas (px)", "render resolution"),
           ("--rule-config", "every knob from parts 2–9"), ("tools/", "kaleidoscope · relight · discovery")],
          "Open source — make your own",
          "It's all open source: clone it, tune any knob, and make worlds that are yours. That's CellAutomata."),
    ]),
]
