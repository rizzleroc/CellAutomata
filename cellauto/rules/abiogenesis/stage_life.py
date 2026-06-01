"""Stage XIII — LIFE: digital organisms with executing virtual-CPU genomes.

This is the v5.0 "life itself" stage. It picks up where Stage XII (LUCA
distillation) leaves off — LUCA is the *recipe* for life; Stage XIII is the
*lineage that lived*. The world is a 2-D grid of substrate and waste; each
cell may hold one :class:`~cellauto.rules.abiogenesis.life_vm.Organism`, whose
behaviour is a literal program run by the virtual CPU in ``life_vm``.

The metabolism loop (PRD §4 F2):

  * every executed instruction costs energy;
  * ``INGEST`` converts grid substrate into energy;
  * ``EXCRETE`` adds waste, which is mildly toxic to its neighbourhood;
  * energy = 0 ⇒ death (the body decays back into substrate over a few
    steps, so dead matter is broken down — PRD §8);
  * energy ≥ E_div ⇒ division into the least-occupied empty Moore neighbour,
    the daughter genome copied with per-instruction mutation ε.

Selection is implicit: genomes that ingest efficiently and divide before
they starve leave more descendants. Mutation at copy time supplies the
heritable variation, so distinct lineages diverge from the founder ancestor
within a few thousand steps (the F8 honest-emergence guard).

Rendering (PRD §4 F5, §5):

  * **viridis mode** (default, the v5.0.0 ship): organisms are filled discs
    coloured by energy on the substrate field (V7).
  * **SEM mode**: translucent hairline body walls — the V9 membrane sprite.
  * **internal anatomy** (V10, Phase 5.1): :meth:`render_plate` renders the
    population at high resolution with the Brachionus-style anatomy — a
    translucent body wall, a gut compartment with drifting ingested
    particles, the genome instruction strip (current instruction highlighted
    teal), a nucleus, and a cytoplasmic shimmer tied to execution rate.

References: see ``life_vm`` and ``docs/science.md`` (Ray 1991 Tierra; Ofria &
Wilke 2004 Avida; Eigen 1971 quasispecies; Channon 2003 open-ended evolution).
"""

from __future__ import annotations

import math
import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.renderer import cmap_viridis
from cellauto.rules.abiogenesis.life_vm import (
    ANCESTOR_GENOME,
    GENOME_CAP,
    Organism,
    VMConfig,
    error_threshold,
    execute_one,
    genome_distance,
    mutate_genome,
)

# Moore-neighbourhood unit directions, indexed by an organism's ``facing``
# (0..7). Clockwise from east.
_DIRS: tuple[tuple[int, int], ...] = (
    (1, 0),
    (1, 1),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (-1, -1),
    (0, -1),
    (1, -1),
)


@dataclass
class LifeState:
    """The full Stage XIII world: three coupled grids plus the live population.

    ``occupant[y, x]`` is the ``oid`` of the organism at that cell, or ``-1``
    when empty — an O(1) spatial index so movement, division-site search, and
    click-to-inspect don't scan the whole population.
    """

    substrate: np.ndarray  # H×W float32 in [0, 1] — food
    waste: np.ndarray  # H×W float32 in [0, 1] — toxic excretion
    occupant: np.ndarray  # H×W int32 — organism oid per cell, -1 = empty
    organisms: dict[int, Organism]
    corpses: list[list[int]]  # [x, y, steps_left] — bodies decaying to substrate
    next_oid: int


@dataclass
class AbiogenesisStageLife:
    """Stage XIII — digital organisms (Tierra/Avida-derived virtual CPUs).

    All tunables are dataclass fields so they round-trip through snapshots via
    :meth:`to_config`. ``rng`` is supplied by the Engine for reproducibility.
    """

    name: str = "abiogenesis-life"
    renderer_kind: str = "field"

    # --- population / world ---
    initial_population: int = 120
    max_population: int = 1400
    substrate_max: float = 1.0
    substrate_regen: float = 0.05  # PRD §4 F2: r_S, linear toward S_max
    ingest_bite: float = 0.35  # max substrate fraction consumed per INGEST
    waste_excretion: float = 0.05
    waste_decay: float = 0.96  # waste relaxes back toward 0 each step
    waste_toxicity: float = 0.015  # per-step death prob ∝ local waste
    decay_steps: int = 10  # corpse → substrate over this many steps

    # --- virtual-CPU energetics (mirrors life_vm.VMConfig) ---
    mutation_rate: float = 0.02  # ε, per-instruction copy error
    instruction_cost: float = 1.0
    ingest_gain: float = 28.0
    move_cost: float = 2.0
    excrete_cost: float = 0.5
    e_div: float = 120.0
    initial_energy: float = 60.0

    # --- rendering ---
    sem_mode: bool = False  # translucent body walls (V9) vs filled discs (V7)
    show_anatomy: bool = True  # internal anatomy in render_plate (V10)
    colorblind_safe: bool = False

    rng: random.Random = field(default_factory=random.Random)

    _rgb_buf: np.ndarray | None = field(default=None, init=False, repr=False)
    _div_requests: set[int] = field(default_factory=set, init=False, repr=False)
    _founder_genome: list[int] = field(default_factory=lambda: list(ANCESTOR_GENOME), init=False, repr=False)

    # ------------------------------------------------------------------ #
    #  VM cost view                                                       #
    # ------------------------------------------------------------------ #
    def _vm_cfg(self) -> VMConfig:
        return VMConfig(
            instruction_cost=self.instruction_cost,
            ingest_gain=self.ingest_gain,
            move_cost=self.move_cost,
            excrete_cost=self.excrete_cost,
            e_div=self.e_div,
        )

    @property
    def error_threshold(self) -> float:
        """Eigen ε_c ≈ ln(σ)/L for the ancestor genome length — above this the
        master sequence melts (the error catastrophe). PRD §4 F1."""
        return error_threshold(len(self._founder_genome))

    # ------------------------------------------------------------------ #
    #  Initialisation (with optional upstream LUCA signal — G1 / PRD F4)  #
    # ------------------------------------------------------------------ #
    def init_state(
        self,
        width: int,
        height: int,
        *,
        seed_field: np.ndarray | None = None,
    ) -> LifeState:
        from cellauto.rules.abiogenesis.science import normalise_signal

        signal = normalise_signal(seed_field)
        # Substrate starts plentiful; if LUCA handed us a signal, the
        # best-adapted regions start a little richer (the lineage emerged
        # where the chemistry was good).
        if signal is not None and signal.shape == (height, width):
            base = 0.55 + 0.35 * signal
        else:
            base = np.full((height, width), 0.7, dtype=np.float32)
        substrate = np.clip(base, 0.0, self.substrate_max).astype(np.float32)
        waste = np.zeros((height, width), dtype=np.float32)
        occupant = np.full((height, width), -1, dtype=np.int32)

        organisms: dict[int, Organism] = {}
        next_oid = 0

        # Seed positions: the brightest LUCA cells (PRD §4 F4) if we have a
        # signal, else random empty cells.
        positions = self._seed_positions(width, height, signal)
        for px, py in positions:
            if occupant[py, px] != -1:
                continue
            org = Organism(
                oid=next_oid,
                genome=list(self._founder_genome),
                x=px,
                y=py,
                energy=self.initial_energy,
                facing=self.rng.randrange(8),
                lineage=next_oid,  # founders each start their own lineage
            )
            organisms[next_oid] = org
            occupant[py, px] = next_oid
            next_oid += 1

        return LifeState(
            substrate=substrate,
            waste=waste,
            occupant=occupant,
            organisms=organisms,
            corpses=[],
            next_oid=next_oid,
        )

    def _seed_positions(self, width: int, height: int, signal: np.ndarray | None) -> list[tuple[int, int]]:
        n = min(self.initial_population, width * height)
        if signal is not None and signal.shape == (height, width) and float(signal.max()) > 0:
            flat = signal.flatten()
            # Top-n brightest cells (LUCA pathway-graph hot-spots).
            top = np.argpartition(flat, -n)[-n:]
            return [(int(i % width), int(i // width)) for i in top]
        # Random scatter.
        cells = self.rng.sample(range(width * height), n)
        return [(c % width, c // width) for c in cells]

    # ------------------------------------------------------------------ #
    #  World protocol — what an executing organism does to the grid       #
    # ------------------------------------------------------------------ #
    # These are called from life_vm.execute_one via the World protocol. The
    # "current" state is bound on self during step() so the protocol methods
    # (which only receive the organism) can reach the grids.

    def sense_substrate(self, org: Organism) -> int:
        return int(self._state.substrate[org.y, org.x] * 255)

    def ingest(self, org: Organism) -> float:
        s = self._state.substrate
        avail = float(s[org.y, org.x])
        bite = min(self.ingest_bite, avail)
        s[org.y, org.x] = avail - bite
        return bite

    def excrete(self, org: Organism) -> None:
        w = self._state.waste
        w[org.y, org.x] = min(1.0, float(w[org.y, org.x]) + self.waste_excretion)

    def move(self, org: Organism) -> bool:
        dx, dy = _DIRS[org.facing % 8]
        nx, ny = org.x + dx, org.y + dy
        occ = self._state.occupant
        h, w = occ.shape
        if not (0 <= nx < w and 0 <= ny < h):
            return False
        if occ[ny, nx] != -1:
            return False
        occ[org.y, org.x] = -1
        occ[ny, nx] = org.oid
        org.x, org.y = nx, ny
        return True

    def request_division(self, org: Organism) -> None:
        self._div_requests.add(org.oid)

    # ------------------------------------------------------------------ #
    #  One simulation step (async, random organism order — PRD §8)        #
    # ------------------------------------------------------------------ #
    def step(self, state: LifeState) -> LifeState:
        self._state = state
        self._div_requests.clear()
        cfg = self._vm_cfg()

        # 1. Execute one instruction per organism, in random order.
        order = list(state.organisms.keys())
        self.rng.shuffle(order)
        e_cap = self.e_div * 5.0  # keep energy (and disc radius) bounded at the pop cap
        for oid in order:
            org = state.organisms.get(oid)
            if org is not None:
                execute_one(org, self, cfg)
                if org.energy > e_cap:
                    org.energy = e_cap

        # 2. Resolve divisions.
        for oid in list(self._div_requests):
            if len(state.organisms) >= self.max_population:
                break
            parent = state.organisms.get(oid)
            if parent is None or parent.energy < self.e_div:
                continue
            self._divide(state, parent)

        # 3. Deaths: starvation + waste toxicity.
        self._cull(state)

        # 4. Environment relaxation: substrate regen, waste decay, corpse decay.
        self._relax_environment(state)

        return state

    def _divide(self, state: LifeState, parent: Organism) -> None:
        site = self._division_site(state, parent)
        if site is None:
            return
        nx, ny = site
        daughter_genome = mutate_genome(parent.genome, self.mutation_rate, self.rng)
        if len(daughter_genome) > GENOME_CAP:
            daughter_genome = daughter_genome[:GENOME_CAP]
        oid = state.next_oid
        state.next_oid += 1
        parent.energy *= 0.5
        parent.n_divisions += 1
        daughter = Organism(
            oid=oid,
            genome=daughter_genome,
            x=nx,
            y=ny,
            energy=parent.energy,  # 50/50 split (parent already halved)
            facing=self.rng.randrange(8),
            parent=parent.oid,
            lineage=parent.lineage,
        )
        state.organisms[oid] = daughter
        state.occupant[ny, nx] = oid

    def _division_site(self, state: LifeState, parent: Organism) -> tuple[int, int] | None:
        """Least-occupied empty Moore neighbour (here: any empty neighbour,
        chosen to spread the population). Returns None if the parent is boxed in."""
        occ = state.occupant
        h, w = occ.shape
        empties: list[tuple[int, int]] = []
        for dx, dy in _DIRS:
            nx, ny = parent.x + dx, parent.y + dy
            if 0 <= nx < w and 0 <= ny < h and occ[ny, nx] == -1:
                empties.append((nx, ny))
        if not empties:
            return None
        return empties[self.rng.randrange(len(empties))]

    def _cull(self, state: LifeState) -> None:
        dead: list[int] = []
        for oid, org in state.organisms.items():
            if org.energy <= 0.0:
                dead.append(oid)
                continue
            # Waste toxicity: linear-in-waste death probability (PRD §4 F2).
            w = float(state.waste[org.y, org.x])
            if w > 0 and self.rng.random() < self.waste_toxicity * w:
                dead.append(oid)
        for oid in dead:
            org = state.organisms.pop(oid)
            state.occupant[org.y, org.x] = -1
            # The body decays back into substrate over decay_steps (PRD §8).
            state.corpses.append([org.x, org.y, self.decay_steps])

    def _relax_environment(self, state: LifeState) -> None:
        s = state.substrate
        # Linear regen toward S_max (vectorised, in place).
        s += self.substrate_regen * (self.substrate_max - s)
        np.clip(s, 0.0, self.substrate_max, out=s)
        # Waste relaxes toward zero.
        state.waste *= self.waste_decay
        # Corpses dribble their body mass back into the substrate.
        if state.corpses:
            give = self.substrate_max / max(1, self.decay_steps) * 0.5
            still: list[list[int]] = []
            for c in state.corpses:
                cx, cy, left = c
                s[cy, cx] = min(self.substrate_max, float(s[cy, cx]) + give)
                left -= 1
                if left > 0:
                    still.append([cx, cy, left])
            state.corpses = still

    # ------------------------------------------------------------------ #
    #  Downstream hand-off (PRD §4 F4) — population × per-organism fitness #
    # ------------------------------------------------------------------ #
    def extract_signal(self, state: LifeState) -> np.ndarray:
        """Where the healthy organisms are, weighted by energy. Suitable for
        seeding a hypothetical Stage XIV (multicellularity, v5.1)."""
        h, w = state.occupant.shape
        out = np.zeros((h, w), dtype=np.float32)
        if not state.organisms:
            return out
        emax = max((o.energy for o in state.organisms.values()), default=1.0)
        emax = max(emax, 1e-6)
        for org in state.organisms.values():
            out[org.y, org.x] = float(np.clip(org.energy / emax, 0.0, 1.0))
        return out

    # ------------------------------------------------------------------ #
    #  Lineage / inspector helpers (PRD §4 F5, V5/V6)                      #
    # ------------------------------------------------------------------ #
    def ancestry(self, state: LifeState, org: Organism, max_depth: int = 16) -> list[int]:
        """Chain of parent oids from ``org`` up toward its founder. Only links
        whose ancestor is still alive can be followed (dead parents are gone),
        so the chain is the *surviving* ancestry — still enough to show the
        learner where an organism came from."""
        chain: list[int] = [org.oid]
        cur = org
        for _ in range(max_depth):
            if cur.parent is None:
                break
            parent = state.organisms.get(cur.parent)
            if parent is None:
                break
            chain.append(parent.oid)
            cur = parent
        return chain

    def organism_at(self, state: LifeState, x: int, y: int) -> Organism | None:
        h, w = state.occupant.shape
        if not (0 <= x < w and 0 <= y < h):
            return None
        oid = int(state.occupant[y, x])
        return state.organisms.get(oid) if oid != -1 else None

    def lineage_count(self, state: LifeState) -> int:
        return len({o.lineage for o in state.organisms.values()})

    def founder_divergence(self, state: LifeState) -> float:
        """Mean genome distance from the founding ancestor — a scalar measure
        of how far the population has drifted (rises with successful evolution,
        explodes past the error catastrophe)."""
        if not state.organisms:
            return 0.0
        d = [genome_distance(o.genome, self._founder_genome) for o in state.organisms.values()]
        return float(np.mean(d))

    # ------------------------------------------------------------------ #
    #  Rendering — live grid path (V7 viridis discs / V9 SEM bodies)       #
    # ------------------------------------------------------------------ #
    def render_rgb(self, state: LifeState) -> np.ndarray:
        h, w = state.substrate.shape
        if self._rgb_buf is None or self._rgb_buf.shape[:2] != (h, w):
            self._rgb_buf = np.empty((h, w, 3), dtype=np.uint8)
        buf = self._rgb_buf
        # Background: substrate under viridis, darkened where waste pools.
        bg = cmap_viridis(state.substrate).astype(np.float32)
        bg *= (1.0 - 0.55 * np.clip(state.waste, 0, 1))[..., None]
        np.copyto(buf, np.clip(bg, 0, 255).astype(np.uint8))

        for org in state.organisms.values():
            self._paint_organism(buf, org)
        return buf

    def _energy_frac(self, org: Organism) -> float:
        return float(np.clip(org.energy / max(self.e_div, 1e-6), 0.0, 1.0))

    def _radius(self, org: Organism) -> int:
        # Bigger = more energy (PRD §4 F3). Bounded so the grid stays legible.
        return int(round(2 + 3 * self._energy_frac(org)))

    def _paint_organism(self, buf: np.ndarray, org: Organism) -> None:
        h, w = buf.shape[:2]
        r = self._radius(org)
        frac = self._energy_frac(org)
        # Energy → colour. Default viridis-teal→yellow; colorblind path stays
        # within a CVD-safe blue→yellow ramp.
        if self.colorblind_safe:
            col = (int(40 + 200 * frac), int(90 + 130 * frac), int(180 * (1 - frac) + 40 * frac))
        else:
            col = (int(40 + 150 * frac), int(120 + 110 * frac), int(120 + 60 * (1 - frac)))
        x0, x1 = max(0, org.x - r), min(w, org.x + r + 1)
        y0, y1 = max(0, org.y - r), min(h, org.y + r + 1)
        if x0 >= x1 or y0 >= y1:
            return
        yy, xx = np.ogrid[y0:y1, x0:x1]
        d2 = (xx - org.x) ** 2 + (yy - org.y) ** 2
        disc = d2 <= r * r
        ring = disc & (d2 >= (r - 1) ** 2)
        sub = buf[y0:y1, x0:x1]
        if self.sem_mode:
            # V9: translucent body wall — faint interior tint, hairline ring.
            tint = np.array((150, 130, 95), dtype=np.float32)  # warm sepia
            sub[disc] = (sub[disc].astype(np.float32) * 0.55 + tint * 0.45).astype(np.uint8)
            sub[ring] = (225, 205, 165)
        else:
            # V7: filled energy disc, white membrane ring.
            sub[disc] = col
            sub[ring] = (235, 235, 235)
        buf[y0:y1, x0:x1] = sub

    # ------------------------------------------------------------------ #
    #  Rendering — SEM "live feed" microscopy plate (V9/V10, Phase 5.1)    #
    # ------------------------------------------------------------------ #
    def render_sem(
        self,
        state: LifeState,
        width: int = 600,
        height: int = 600,
        max_org: int = 22,
        seed: int = 0,
        phase: float = 0.0,
    ) -> np.ndarray:
        """The Brachionus-style "LIVE SEM FEED · 400×" microscopy plate — the
        headline Phase 5.1 visual. Renders a modest sample of organisms LARGE
        (cell size is decoupled from grid density, matching the 400× reference)
        on a granular sepia substrate, each as a translucent depth-shaded body
        with cilia, a dense granular gut, a nucleus, and the genome instruction
        bead-arc (the currently-executing opcode glows teal). One dividing cell
        carries the single teal division bridge. Every element maps to real
        organism state — no decorative motion.

        Returns an ``(height, width, 3)`` uint8 array, ready for the canvas or
        a saved preview. Built with Pillow for clean alpha compositing.
        """

        gh, gw = state.substrate.shape
        npr = np.random.RandomState(seed & 0x7FFFFFFF)
        bg = self._sem_substrate(width, height, state.substrate, npr).convert("RGBA")

        orgs = sorted(state.organisms.values(), key=lambda o: -o.energy)[:max_org]
        orgs = sorted(orgs, key=lambda o: o.y)  # back-to-front for depth
        margin, base_r = 0.10, min(width, height) * 0.085
        div_oid = (
            max(state.organisms.values(), key=lambda o: (o.n_divisions, o.energy)).oid
            if state.organisms
            else None
        )
        for o in orgs:
            cx = (margin + (1 - 2 * margin) * (o.x / max(1, gw - 1))) * width
            cy = (margin + (1 - 2 * margin) * (o.y / max(1, gh - 1))) * height
            ef = min(o.energy / max(self.e_div, 1e-6), 1.6)
            r = base_r * (0.78 + 0.5 * ef)
            self._sem_organism(bg, cx, cy, r, o, phase, dividing=(o.oid == div_oid and ef > 0.5))

        out = self._sem_overlay(bg.convert("RGB"))
        return np.asarray(out, dtype=np.uint8)

    def render_plate(self, state: LifeState, scale: int = 12, max_organisms: int = 60) -> np.ndarray:
        """High-resolution SEM plate sized to ``grid × scale`` — the saved
        ``docs/generated/stage13_life.png`` companion. Delegates to
        :meth:`render_sem`."""
        h, w = state.substrate.shape
        return self.render_sem(state, width=w * scale, height=h * scale, max_org=max_organisms)

    def _sem_substrate(self, width: int, height: int, substrate: np.ndarray, npr: np.random.RandomState):
        """Particulate SEM field: multi-octave value noise, sepia-graded and
        shaded by the substrate concentration so food-rich regions read brighter."""
        from PIL import Image, ImageFilter

        base = np.zeros((height, width), np.float32)
        for octave, cell in enumerate((6, 14, 32, 70)):
            gh, gw = height // cell + 2, width // cell + 2
            grid = (npr.random_sample((gh, gw)) * 255).astype(np.uint8)
            up = np.asarray(Image.fromarray(grid).resize((width, height), Image.BILINEAR), np.float32) / 255
            base += up * (0.55**octave)
        base /= max(float(base.max()), 1e-6)
        base = 0.82 * base + 0.18 * npr.random_sample((height, width)).astype(np.float32)
        sub_u8 = (np.clip(substrate, 0, 1) * 255).astype(np.uint8)
        sub_up = np.asarray(Image.fromarray(sub_u8).resize((width, height), Image.BILINEAR), np.float32) / 255
        val = base * (0.45 + 0.55 * sub_up)
        img = np.empty((height, width, 3), np.float32)
        img[..., 0] = 30 + 150 * val
        img[..., 1] = 24 + 120 * val
        img[..., 2] = 16 + 78 * val
        arr = np.clip(img, 0, 255).astype(np.uint8)
        return Image.fromarray(arr, "RGB").filter(ImageFilter.GaussianBlur(0.5))

    def _organic_outline(
        self, org: Organism, ox: float, oy: float, rx: float, ry: float, phase: float, n: int = 60
    ) -> list[tuple[float, float]]:
        """A unique, irregular amoeboid outline per organism — never an ellipse.

        The radius is modulated by a handful of sine harmonics whose amplitudes
        and phases are *stable per organism* (seeded by its ``oid``) so each
        cell keeps its own body shape, while a ``phase``-driven term makes the
        membrane slowly wobble and the whole body creep its orientation — the
        cell reads as ALIVE rather than a frozen stamp. The genome biases a
        low-frequency lobe so the form reflects the program it carries.
        """
        orng = random.Random((org.oid * 2654435761) & 0xFFFFFFFF)
        harm = []
        for k in (2, 3, 5, 7):
            amp = orng.uniform(0.06, 0.22) / (1 + (k - 2) * 0.35)
            hph = orng.uniform(0, 2 * math.pi)
            spd = orng.uniform(0.4, 1.1) * (1 if orng.random() < 0.5 else -1)
            harm.append((k, amp, hph, spd))
        g = org.genome
        lobe = 0.12 * ((g[0] % 5) / 5.0) if g else 0.0
        ang = (org.facing / 8.0) * 2 * math.pi + phase * 0.012  # slow creep of orientation
        ca, sa = math.cos(ang), math.sin(ang)
        pts: list[tuple[float, float]] = []
        for i in range(n):
            th = 2 * math.pi * i / n
            rr = 1.0 + lobe * math.sin(2 * th + phase * 0.05)
            for k, amp, hph, spd in harm:
                rr += amp * math.sin(k * th + hph + phase * 0.13 * spd)
            bx, by = math.cos(th) * rx * rr, math.sin(th) * ry * rr
            pts.append((ox + bx * ca - by * sa, oy + bx * sa + by * ca))
        return pts

    def _sem_organism(
        self, base, cx: float, cy: float, r: float, org: Organism, phase: float, dividing: bool
    ) -> None:
        """One translucent, depth-shaded organism with an organic (non-uniform)
        body, beating cilia, and a drifting gut — drawn on its own RGBA layer
        then alpha-composited onto the substrate."""
        from PIL import Image, ImageDraw, ImageFilter

        pad = int(r * 2.4) + 8
        L = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
        ox, oy = float(pad), float(pad)
        rx, ry = r, r * 0.74
        pts = self._organic_outline(org, ox, oy, rx, ry, phase)
        closed = pts + [pts[0]]

        # Soft drop shadow — the organic silhouette, offset and blurred.
        sh = Image.new("RGBA", L.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).polygon([(px + r * 0.16, py + r * 0.26) for px, py in pts], fill=(0, 0, 0, 120))
        L = Image.alpha_composite(L, sh.filter(ImageFilter.GaussianBlur(r * 0.22)))

        # Beating cilia/flagella along the membrane — length pulses with phase.
        d = ImageDraw.Draw(L)
        for i in range(0, len(pts), 2):
            px, py = pts[i]
            ux, uy = px - ox, py - oy
            ln = math.hypot(ux, uy) or 1.0
            ux, uy = ux / ln, uy / ln
            beat = 0.14 + 0.13 * math.sin(i * 0.5 + phase * 0.45 + org.oid)
            hl = r * beat
            d.line(
                [px, py, px + ux * hl, py + uy * hl], fill=(182, 162, 122, 95), width=max(1, int(r * 0.05))
            )

        # Soft translucent halo (SEM out-of-focus glow).
        halo = Image.new("RGBA", L.size, (0, 0, 0, 0))
        ImageDraw.Draw(halo).polygon(
            [(ox + (px - ox) * 1.12, oy + (py - oy) * 1.12) for px, py in pts], fill=(150, 134, 100, 60)
        )
        L = Image.alpha_composite(L, halo.filter(ImageFilter.GaussianBlur(r * 0.18)))

        # Translucent body: organic polygon mask × radial depth gradient, with a
        # faint cytoplasmic shimmer tied to phase + identity.
        mask = Image.new("L", L.size, 0)
        ImageDraw.Draw(mask).polygon(pts, fill=255)
        yy, xx = np.mgrid[0 : L.size[1], 0 : L.size[0]].astype(np.float32)
        dist = np.sqrt(((xx - ox) / (rx * 1.18)) ** 2 + ((yy - oy) / (ry * 1.18)) ** 2)
        radial = np.clip(1.0 - dist, 0.0, 1.0)
        m = np.asarray(mask, np.float32) / 255.0
        shim = 1.0 + 0.06 * math.sin(phase * 0.3 + org.oid)
        body_arr = np.zeros((L.size[1], L.size[0], 4), np.uint8)
        body_arr[..., 0] = min(255, int(150 * shim))
        body_arr[..., 1] = min(255, int(132 * shim))
        body_arr[..., 2] = min(255, int(96 * shim))
        body_arr[..., 3] = np.clip(m * (0.30 + 0.70 * radial) * 182, 0, 188).astype(np.uint8)
        L = Image.alpha_composite(L, Image.fromarray(body_arr, "RGBA"))
        d = ImageDraw.Draw(L)

        # Bright organic rim highlight (the SEM wall) + offset nucleus.
        d.line(closed, fill=(225, 208, 168, 225), width=max(1, int(r * 0.07)), joint="curve")
        nx, ny = ox - rx * 0.30, oy - ry * 0.26
        d.ellipse([nx - r * 0.22, ny - r * 0.22, nx + r * 0.22, ny + r * 0.22], fill=(120, 104, 78, 150))

        # Dense granular gut that slowly churns (drift tied to phase).
        grng = random.Random((org.oid * 40503) & 0xFFFFFFFF)
        gx, gy = ox + rx * 0.08, oy + ry * 0.12
        n_gran = 46 + (org.regs[0] % 18)
        for k in range(n_gran):
            a0 = grng.uniform(0, 2 * math.pi)
            rad_f = grng.random() ** 0.5
            a = a0 + phase * 0.02 * (0.5 + (k % 3))
            px = gx + math.cos(a) * rx * 0.60 * rad_f
            py = gy + math.sin(a) * ry * 0.60 * rad_f
            gr = r * (0.05 + 0.07 * grng.random())
            shade = 40 + int(35 * grng.random())
            d.ellipse([px - gr, py - gr, px + gr, py + gr], fill=(shade + 16, shade, shade - 8, 220))

        # Genome instruction bead-arc hugging the lower membrane; current = teal.
        if org.genome:
            n_show = min(16, len(org.genome))
            ip0 = org.ip % len(org.genome)
            for i in range(n_show):
                idx = int((0.10 + 0.80 * i / max(1, n_show - 1)) * (len(pts) // 2)) % len(pts)
                px, py = pts[idx]
                bx, by = ox + (px - ox) * 0.82, oy + (py - oy) * 0.82
                dot = max(2, int(r * 0.075))
                if i == 0:
                    col = (80, 235, 210, 255)
                else:
                    base_c = 235 if org.genome[(ip0 + i) % len(org.genome)] / 19 > 0.5 else 205
                    col = (base_c, base_c - 18, base_c - 70, 245)
                d.ellipse([bx - dot, by - dot, bx + dot, by + dot], fill=col, outline=(40, 30, 20, 160))

        if dividing:
            glow = Image.new("RGBA", L.size, (0, 0, 0, 0))
            gd2 = ImageDraw.Draw(glow)
            gd2.ellipse(
                [ox + rx * 0.55, oy - ry * 0.78, ox + rx * 1.95, oy + ry * 0.78], fill=(40, 225, 205, 70)
            )
            gd2.line(
                [ox + rx * 0.7, oy, ox + rx * 1.25, oy],
                fill=(120, 245, 225, 230),
                width=max(2, int(r * 0.12)),
            )
            L = Image.alpha_composite(L, glow.filter(ImageFilter.GaussianBlur(r * 0.16)))

        base.alpha_composite(L, (int(cx - pad), int(cy - pad)))

    def _sem_overlay(self, img, scale_um: int = 50):
        """Instrument chrome: frame, crosshair, the 400× SEM badge, and the
        50 µm scale bar — the museum-microscopy furniture from the reference."""
        from PIL import ImageDraw

        width, height = img.size
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([6, 6, width - 7, height - 7], outline=(150, 132, 96, 180), width=2)
        cx, cy = width // 2, height // 2
        d.line([cx - 26, cy, cx + 26, cy], fill=(200, 185, 150, 120), width=1)
        d.line([cx, cy - 26, cx, cy + 26], fill=(200, 185, 150, 120), width=1)
        bw, bh = 250, 26
        d.rectangle(
            [width - bw - 16, 16, width - 16, 16 + bh], fill=(20, 15, 10, 170), outline=(150, 132, 96, 180)
        )
        d.text((width - bw - 6, 22), "LIVE SEM FEED  ·  STAGE XIII  ·  400×", fill=(220, 205, 165, 255))
        sb = 150
        sx, sy = cx - sb // 2, height - 34
        d.line([sx, sy, sx + sb, sy], fill=(225, 208, 168, 230), width=2)
        d.line([sx, sy - 5, sx, sy + 5], fill=(225, 208, 168, 230), width=2)
        d.line([sx + sb, sy - 5, sx + sb, sy + 5], fill=(225, 208, 168, 230), width=2)
        d.text((cx - 22, sy - 20), f"{scale_um} um", fill=(220, 205, 165, 255))
        return img

    # discrete fallback (kept for the protocol; field path is the real one).
    def render_cell(self, state: LifeState, x: int, y: int) -> tuple[str, str]:
        org = self.organism_at(state, x, y)
        if org is not None:
            frac = self._energy_frac(org)
            g = int(120 + 100 * frac)
            return f"#{g:02x}{max(0, g - 40):02x}40", "oval"
        v = float(state.substrate[y, x])
        gray = int(np.clip(v * 255, 0, 255))
        return f"#{gray:02x}{gray:02x}{gray:02x}", "rect"

    # ------------------------------------------------------------------ #
    #  Stats                                                              #
    # ------------------------------------------------------------------ #
    def population(self, state: LifeState) -> Mapping[str, int]:
        orgs = list(state.organisms.values())
        n = len(orgs)
        avg_e = float(np.mean([o.energy for o in orgs])) if orgs else 0.0
        avg_len = float(np.mean([o.genome_len() for o in orgs])) if orgs else 0.0
        return {
            "organisms": n,
            "lineages": self.lineage_count(state),
            "avg_energy": int(round(avg_e)),
            "avg_genome_len": int(round(avg_len)),
            "founder_divergence_x100": int(round(self.founder_divergence(state) * 100)),
            "mutation_rate_x1000": int(round(self.mutation_rate * 1000)),
            "error_threshold_x1000": int(round(self.error_threshold * 1000)),
            "substrate_x1000": int(round(float(state.substrate.mean()) * 1000)),
        }

    # ------------------------------------------------------------------ #
    #  Serialisation (round-trips through Engine snapshots)               #
    # ------------------------------------------------------------------ #
    def serialize_state(self, state: LifeState) -> dict:
        return {
            "substrate": np.round(state.substrate, 4).tolist(),
            "waste": np.round(state.waste, 4).tolist(),
            "next_oid": state.next_oid,
            "corpses": [list(c) for c in state.corpses],
            "organisms": [self._serialize_org(o) for o in state.organisms.values()],
        }

    @staticmethod
    def _serialize_org(o: Organism) -> dict:
        return {
            "oid": o.oid,
            "genome": list(o.genome),
            "x": o.x,
            "y": o.y,
            "energy": round(o.energy, 4),
            "ip": o.ip,
            "regs": list(o.regs),
            "head": o.head,
            "flag": o.flag,
            "facing": o.facing,
            "copy_head": o.copy_head,
            "age": o.age,
            "parent": o.parent,
            "lineage": o.lineage,
            "n_divisions": o.n_divisions,
            "last_op": o.last_op,
        }

    def deserialize_state(self, data: dict) -> LifeState:
        substrate = np.array(data["substrate"], dtype=np.float32)
        waste = np.array(data["waste"], dtype=np.float32)
        h, w = substrate.shape
        occupant = np.full((h, w), -1, dtype=np.int32)
        organisms: dict[int, Organism] = {}
        for d in data["organisms"]:
            org = Organism(
                oid=d["oid"],
                genome=list(d["genome"]),
                x=d["x"],
                y=d["y"],
                energy=float(d["energy"]),
                ip=d["ip"],
                regs=list(d["regs"]),
                head=d["head"],
                flag=d["flag"],
                facing=d["facing"],
                copy_head=d["copy_head"],
                age=d["age"],
                parent=d["parent"],
                lineage=d["lineage"],
                n_divisions=d["n_divisions"],
                last_op=d["last_op"],
            )
            organisms[org.oid] = org
            occupant[org.y, org.x] = org.oid
        return LifeState(
            substrate=substrate,
            waste=waste,
            occupant=occupant,
            organisms=organisms,
            corpses=[list(c) for c in data.get("corpses", [])],
            next_oid=data["next_oid"],
        )

    def to_config(self) -> dict:
        return {
            "initial_population": self.initial_population,
            "max_population": self.max_population,
            "substrate_max": self.substrate_max,
            "substrate_regen": self.substrate_regen,
            "ingest_bite": self.ingest_bite,
            "waste_excretion": self.waste_excretion,
            "waste_decay": self.waste_decay,
            "waste_toxicity": self.waste_toxicity,
            "decay_steps": self.decay_steps,
            "mutation_rate": self.mutation_rate,
            "instruction_cost": self.instruction_cost,
            "ingest_gain": self.ingest_gain,
            "move_cost": self.move_cost,
            "excrete_cost": self.excrete_cost,
            "e_div": self.e_div,
            "initial_energy": self.initial_energy,
            "sem_mode": self.sem_mode,
            "show_anatomy": self.show_anatomy,
            "colorblind_safe": self.colorblind_safe,
        }
