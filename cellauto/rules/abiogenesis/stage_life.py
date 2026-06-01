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

  * **viridis mode** (the v5.0.0 ship): :meth:`render_rgb` draws filled discs
    coloured by energy on the substrate field (V7) — fast, grid-resolution.
  * **SEM mode** (V9/V10, Phase 5.1): :meth:`render_sem` (and :meth:`render_plate`)
    delegate to :mod:`life_sem`, a 3D scanning-electron-microscope render —
    each organism is a normal-mapped lit body (organic dome + organelle relief
    + edge-brightening + wet specular) on a granular sepia substrate, with
    depth-of-field, a filmic grade, and one teal dividing cell. This is the
    Brachionus-style headline visual and the live desktop canvas for Stage XIII.

References: see ``life_vm`` and ``docs/science.md`` (Ray 1991 Tierra; Ofria &
Wilke 2004 Avida; Eigen 1971 quasispecies; Channon 2003 open-ended evolution).
"""

from __future__ import annotations

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
        max_org: int = 24,
        seed: int = 0,
        phase: float = 0.0,
    ) -> np.ndarray:
        """The "LIVE SEM FEED · 400×" plate for Stage XIII. Prefers the
        photoreal SPRITE compositor (:mod:`life_sprites`), which blits a
        committed atlas of path-traced translucent cells (baked offline by
        ``tools/bake_life_sprites.py``) — genuine subsurface scattering at zero
        runtime render cost. If the baked atlas is absent it falls back to the
        procedural 3D renderer (:mod:`life_sem`): normal-mapped lit bodies with
        SEM edge-brightening, AO and a filmic grade. Either way one dividing
        cell is the single teal accent and ``phase`` (the engine step) animates
        the feed. Returns an ``(height, width, 3)`` uint8 array."""
        from cellauto.rules.abiogenesis import life_sem

        try:
            from cellauto.rules.abiogenesis import life_sprites

            return life_sprites.render(
                state, self, width=width, height=height, max_org=max_org, seed=seed, phase=phase
            )
        except (FileNotFoundError, OSError, KeyError, ValueError):
            return life_sem.render(
                state, self, width=width, height=height, max_org=max_org, seed=seed, phase=phase
            )

    def render_plate(self, state: LifeState, scale: int = 12, max_organisms: int = 60) -> np.ndarray:
        """High-resolution SEM plate sized to ``grid × scale`` — the saved
        ``docs/generated/stage13_life.png`` companion. Delegates to
        :meth:`render_sem`."""
        h, w = state.substrate.shape
        return self.render_sem(state, width=w * scale, height=h * scale, max_org=max_organisms)

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
