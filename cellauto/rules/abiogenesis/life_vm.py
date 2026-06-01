"""LIFE — the virtual CPU that *is* each digital organism (Stage XIII).

This is the v5.0 "digital life" engine. After Stage XII distils LUCA — the
*recipe* for life — Stage XIII populates the post-LUCA world with discrete
organisms whose behaviour is not a probability table but an **executing
program**. Every organism carries a genome: a tape of opcodes for a tiny
virtual CPU. The CPU steps instruction-by-instruction, and each instruction
is the organism *doing something* — ingesting substrate, excreting waste,
moving, comparing, copying, dividing. The genome IS the phenotype.

The design is deliberately Tierra/Avida-derived (see ``docs/science.md``):

  * **Tierra** (Ray 1991) gave us self-replicating assembly-language
    programs competing for CPU time in a shared soup, with parasites that
    hijack a neighbour's copy loop. We borrow the instruction-tape genome
    and the copy-loop idiom (``COPY`` / ``DIVIDE``); the shared-memory
    parasite variant is deferred to V12 (Phase 5.4).
  * **Avida** (Ofria & Wilke 2004) gave us grid-cellular organisms, each
    with its *own private* memory and a metabolism that rewards work with
    energy. We adopt the private-memory model (it sidesteps the whole
    ecological-complexity question for v5.0) and the energy economy: every
    executed instruction costs energy; ``INGEST`` replenishes it from the
    environment.

The module is intentionally free of any rendering, grid, or Tk concerns so
it can be unit-tested in isolation against a mock world. The Stage XIII rule
in ``stage_life.py`` supplies the concrete :class:`World`.

References:
    Ray, T. S. (1991). An approach to the synthesis of life. Artificial
        Life II, Santa Fe Institute Studies, 371-408.
    Adami, C., & Brown, C. T. (1994). Evolutionary learning in the 2D
        artificial life system 'Avida'. Artificial Life IV, 377-381.
    Ofria, C., & Wilke, C. O. (2004). Avida: a software platform for
        research in computational evolutionary biology. Artificial Life,
        10(2), 191-229.
    Eigen, M. (1971). Selforganization of matter and the evolution of
        biological macromolecules. Naturwissenschaften, 58(10), 465-523.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Protocol

# ---------------------------------------------------------------------------
# Instruction set — 20 opcodes (PRD §4 F1: "~20 opcodes, Tierra-derived").
# ---------------------------------------------------------------------------
#
# The opcodes are referenced everywhere by their integer value (the genome is
# a list of these ints). ``OPCODES`` is the canonical name table; ``OP`` is a
# reverse lookup so code can read ``OP["INGEST"]`` instead of a magic number.
# Keeping the count at exactly 20 is a deliberate PRD decision (§8): small
# enough to reason about, large enough for emergent behaviour.

OPCODES: tuple[str, ...] = (
    "NOP",  # 0  — no-op; also a template marker (Tierra nop-pattern idiom)
    "INC",  # 1  — reg[head] += 1
    "DEC",  # 2  — reg[head] -= 1
    "ADD",  # 3  — reg[0] = reg[1] + reg[2]
    "SUB",  # 4  — reg[0] = reg[1] - reg[2]
    "LOAD",  # 5  — reg[head] = next genome byte (immediate literal)
    "SWAP",  # 6  — swap reg[0] and reg[head]
    "HEAD",  # 7  — advance the register head (selects which reg INC/DEC hit)
    "JUMP",  # 8  — ip += (reg[head] mod genome length), wrapping
    "JZ",  # 9  — if flag == 0: same jump as JUMP
    "CMP",  # 10 — flag = sign(reg[0] - reg[1])  ∈ {-1, 0, +1}
    "SENSE",  # 11 — reg[head] = local substrate level (0..255)
    "INGEST",  # 12 — consume substrate at this cell → energy  (metabolism in)
    "EXCRETE",  # 13 — release waste into this cell             (metabolism out)
    "MOVE",  # 14 — step to the faced neighbour if empty (costs extra energy)
    "TURN",  # 15 — facing = (facing + 1 + reg[head]) mod 8
    "DIVIDE",  # 16 — reproduce if energy ≥ E_div (genome copied with ε mutation)
    "COPY",  # 17 — advance the self-read copy head (replication progress)
    "RAND",  # 18 — reg[head] = rng byte 0..255
    "LOOP",  # 19 — reset ip to 0 (soft restart of the program)
)

OP: dict[str, int] = {name: i for i, name in enumerate(OPCODES)}
N_OPCODES: int = len(OPCODES)
assert N_OPCODES == 20, "PRD §4 F1 pins the instruction set at 20 opcodes"

N_REGISTERS: int = 4
GENOME_CAP: int = 512  # PRD §4 F1: private memory ≤ 512 instructions


# ---------------------------------------------------------------------------
# The canonical viable ancestor (Tierra's "ancestor 0080" analogue).
# ---------------------------------------------------------------------------
#
# A hand-written genome that actually *lives*: it senses its surroundings,
# eats whenever there is substrate, periodically excretes, occasionally
# turns and moves to find fresh food, and divides once it is energy-rich.
# Every founding organism starts from this tape; mutation explores the
# neighbourhood around it. Keeping the ancestor viable is what lets the
# default population sustain itself for ≥ 10k steps (PRD §7 acceptance #2).
ANCESTOR_GENOME: tuple[int, ...] = (
    OP["SENSE"],  # read how much food is under me
    OP["INGEST"],  # eat it → energy
    OP["INGEST"],  # eat again (cheap; gated by remaining substrate)
    OP["CMP"],  # compare registers (sets the flag)
    OP["NOP"],
    OP["EXCRETE"],  # dump some waste
    OP["INGEST"],
    OP["DIVIDE"],  # split when rich enough
    OP["TURN"],  # reorient
    OP["MOVE"],  # wander toward fresh substrate
    OP["INGEST"],
    OP["DIVIDE"],
    OP["LOOP"],  # start the program over
)


class World(Protocol):
    """Everything an executing organism can do to its environment.

    The Stage XIII rule implements this; ``life_vm`` only depends on the
    protocol so the VM can be exercised against a mock world in tests.
    All coordinates are taken from the organism itself.
    """

    def sense_substrate(self, org: Organism) -> int: ...

    def ingest(self, org: Organism) -> float:
        """Consume substrate at the organism's cell; return energy gained."""
        ...

    def excrete(self, org: Organism) -> None:
        """Release waste into the organism's cell."""
        ...

    def move(self, org: Organism) -> bool:
        """Attempt to step into the faced neighbour; return True on success."""
        ...

    def request_division(self, org: Organism) -> None:
        """Flag that this organism wants to divide this step."""
        ...


@dataclass
class Organism:
    """One digital organism: a genome plus the live state of its virtual CPU.

    ``oid`` is a stable per-run identity; ``parent`` is the ``oid`` of the
    organism that budded this one (``None`` for founders), which is all the
    ancestry tracking (PRD §4 F5, V5) needs to reconstruct a lineage chain.
    ``lineage`` is the founder's ``oid`` — every descendant of the same
    founder shares it, so counting distinct ``lineage`` values counts
    surviving lineages (the F8 honest-emergence guard).
    """

    oid: int
    genome: list[int]
    x: int
    y: int
    energy: float
    # --- virtual-CPU registers / heads ---
    ip: int = 0  # instruction pointer
    regs: list[int] = field(default_factory=lambda: [0] * N_REGISTERS)
    head: int = 0  # selects which register INC/DEC/etc. act on
    flag: int = 0  # comparison flag ∈ {-1, 0, +1}
    facing: int = 0  # 0..7, a Moore-neighbourhood direction
    copy_head: int = 0  # self-read progress (replication idiom)
    # --- bookkeeping ---
    age: int = 0
    parent: int | None = None
    lineage: int = 0
    n_divisions: int = 0
    last_op: int = 0  # opcode executed on the most recent tick

    def genome_len(self) -> int:
        return len(self.genome)

    def current_instruction(self) -> int:
        """Opcode currently under the instruction pointer (the one the
        inspector highlights teal). Safe against an empty genome."""
        if not self.genome:
            return OP["NOP"]
        return self.genome[self.ip % len(self.genome)]


def random_genome(rng: random.Random, length: int = len(ANCESTOR_GENOME)) -> list[int]:
    """A uniformly random tape — used for diversity seeding / fuzz tests, not
    for the default founders (those use :data:`ANCESTOR_GENOME`)."""
    length = max(1, min(length, GENOME_CAP))
    return [rng.randrange(N_OPCODES) for _ in range(length)]


def mutate_genome(genome: list[int], epsilon: float, rng: random.Random) -> list[int]:
    """Copy ``genome`` with per-instruction substitution probability ``epsilon``.

    This is Eigen's per-digit error model: each position is copied correctly
    with probability ``1 - epsilon`` and otherwise replaced by a random
    opcode. Eigen's error threshold (the "error catastrophe") sits at
    ``epsilon_c = ln(sigma) / L`` for selective superiority ``sigma`` and
    genome length ``L``; above it the master sequence can no longer be
    maintained against copying noise and the lineage melts. See
    :func:`error_threshold`.
    """
    out: list[int] = []
    for op in genome:
        if rng.random() < epsilon:
            out.append(rng.randrange(N_OPCODES))
        else:
            out.append(op)
    return out


def error_threshold(genome_len: int, selective_superiority: float = math.e) -> float:
    """Eigen's quasispecies error threshold ε_c = ln(σ) / L.

    With the default σ = e this reduces to the textbook ε_c ≈ 1 / L. Below
    ε_c the master sequence is maintained; above it the population melts into
    a random ensemble. Exposed so the rule and its tests can pin the
    catastrophe (PRD §4 F1, §7 acceptance #4)."""
    L = max(1, int(genome_len))
    return math.log(selective_superiority) / L


def genome_distance(a: list[int], b: list[int]) -> int:
    """Hamming-style distance between two genomes (mismatch count over the
    shorter length, plus the length difference). Used for lineage-diversity
    metrics and the founder-divergence tests."""
    n = min(len(a), len(b))
    mism = sum(1 for i in range(n) if a[i] != b[i])
    return mism + abs(len(a) - len(b))


@dataclass
class VMConfig:
    """Tunable costs for one tick of the virtual CPU. Defaults follow PRD §4:
    every instruction costs 1 unit of energy; INGEST replenishes it."""

    instruction_cost: float = 1.0  # PRD §4 F1: every instruction costs 1 unit
    ingest_gain: float = 28.0  # energy per fully-consumed unit of substrate
    move_cost: float = 2.0  # MOVE costs extra on top of instruction_cost
    excrete_cost: float = 0.5
    e_div: float = 120.0  # energy threshold for DIVIDE (PRD §4 F2)


def execute_one(org: Organism, world: World, cfg: VMConfig) -> None:
    """Run exactly **one** instruction of ``org``'s genome against ``world``.

    Async, one-instruction-per-organism-per-step execution (PRD §8: "async
    with random organism order") keeps the model testable and avoids the
    grid-rhythm artefacts of fully-synchronous update. The function mutates
    ``org`` in place and drives the environment through ``world``; it never
    raises on a degenerate genome.

    Energy accounting: the base ``instruction_cost`` is charged for every
    tick; opcodes that touch the world (MOVE, EXCRETE) add their own surcharge,
    and INGEST is the only source of energy income.
    """
    org.age += 1
    if not org.genome:
        org.energy -= cfg.instruction_cost
        return

    n = len(org.genome)
    op = org.genome[org.ip % n]
    org.last_op = op
    # Advance the instruction pointer first; JUMP/LOOP overwrite it below.
    org.ip = (org.ip + 1) % n

    # Base metabolic cost of being alive and executing.
    org.energy -= cfg.instruction_cost

    if op == OP["NOP"]:
        pass
    elif op == OP["INC"]:
        org.regs[org.head] = (org.regs[org.head] + 1) & 0xFF
    elif op == OP["DEC"]:
        org.regs[org.head] = (org.regs[org.head] - 1) & 0xFF
    elif op == OP["ADD"]:
        org.regs[0] = (org.regs[1] + org.regs[2]) & 0xFF
    elif op == OP["SUB"]:
        org.regs[0] = (org.regs[1] - org.regs[2]) & 0xFF
    elif op == OP["LOAD"]:
        # Immediate literal: read (and consume) the next genome byte.
        literal = org.genome[org.ip % n]
        org.regs[org.head] = literal & 0xFF
        org.ip = (org.ip + 1) % n
    elif op == OP["SWAP"]:
        org.regs[0], org.regs[org.head] = org.regs[org.head], org.regs[0]
    elif op == OP["HEAD"]:
        org.head = (org.head + 1) % N_REGISTERS
    elif op == OP["JUMP"]:
        org.ip = org.regs[org.head] % n
    elif op == OP["JZ"]:
        if org.flag == 0:
            org.ip = org.regs[org.head] % n
    elif op == OP["CMP"]:
        diff = org.regs[0] - org.regs[1]
        org.flag = (diff > 0) - (diff < 0)
    elif op == OP["SENSE"]:
        org.regs[org.head] = world.sense_substrate(org) & 0xFF
    elif op == OP["INGEST"]:
        org.energy += world.ingest(org) * cfg.ingest_gain
    elif op == OP["EXCRETE"]:
        world.excrete(org)
        org.energy -= cfg.excrete_cost
    elif op == OP["MOVE"]:
        if world.move(org):
            org.energy -= cfg.move_cost
    elif op == OP["TURN"]:
        org.facing = (org.facing + 1 + org.regs[org.head]) % 8
    elif op == OP["DIVIDE"]:
        if org.energy >= cfg.e_div:
            world.request_division(org)
    elif op == OP["COPY"]:
        org.copy_head = (org.copy_head + 1) % n
    elif op == OP["RAND"]:
        # rng access goes through the world's organism so determinism is owned
        # by the stage; fall back to the standard module rng only if absent.
        org.regs[org.head] = _world_rng(world).randrange(256)
    elif op == OP["LOOP"]:
        org.ip = 0


def _world_rng(world: World) -> random.Random:
    """Best-effort access to the world's RNG so RAND stays reproducible.
    Falls back to a module-level Random if the world doesn't expose one."""
    rng = getattr(world, "rng", None)
    if isinstance(rng, random.Random):
        return rng
    return _FALLBACK_RNG


_FALLBACK_RNG = random.Random(0)
