"""Stage XIII — unit tests for the digital-life virtual CPU (``life_vm``).

These exercise the VM in isolation against a tiny mock :class:`World`, so the
instruction semantics, energy accounting, and Eigen mutation/error-threshold
maths are pinned independently of the grid stage in ``stage_life``.
"""

from __future__ import annotations

import math
import random

from cellauto.rules.abiogenesis.life_vm import (
    ANCESTOR_GENOME,
    GENOME_CAP,
    N_OPCODES,
    N_REGISTERS,
    OP,
    OPCODES,
    Organism,
    VMConfig,
    error_threshold,
    execute_one,
    genome_distance,
    mutate_genome,
)


class MockWorld:
    """A minimal :class:`World` over plain python state.

    Records the calls the VM makes so the tests can assert against them, and
    exposes an ``rng`` attribute so ``RAND`` stays deterministic.
    """

    def __init__(self, *, substrate: int = 100, ingest: float = 1.0, move_ok: bool = True, seed: int = 0):
        self.substrate = substrate
        self._ingest = ingest
        self._move_ok = move_ok
        self.rng = random.Random(seed)
        self.excrete_calls = 0
        self.move_calls = 0
        self.division_requests: list[int] = []

    def sense_substrate(self, org: Organism) -> int:
        return self.substrate

    def ingest(self, org: Organism) -> float:
        return self._ingest

    def excrete(self, org: Organism) -> None:
        self.excrete_calls += 1

    def move(self, org: Organism) -> bool:
        self.move_calls += 1
        return self._move_ok

    def request_division(self, org: Organism) -> None:
        self.division_requests.append(org.oid)


def _org(genome: list[int], **kw) -> Organism:
    return Organism(
        oid=kw.pop("oid", 1),
        genome=list(genome),
        x=kw.pop("x", 0),
        y=kw.pop("y", 0),
        energy=kw.pop("energy", 100.0),
        **kw,
    )


def _run_one(org: Organism, world: MockWorld, cfg: VMConfig | None = None) -> None:
    execute_one(org, world, cfg or VMConfig())


# --------------------------------------------------------------------------- #
# 1. Instruction-set invariants                                               #
# --------------------------------------------------------------------------- #
def test_opcode_table_is_exactly_twenty():
    assert len(OPCODES) == 20
    assert N_OPCODES == 20
    assert N_REGISTERS == 4
    assert GENOME_CAP == 512
    # OP is a consistent reverse lookup of OPCODES.
    assert OP == {name: i for i, name in enumerate(OPCODES)}
    assert len(OP) == N_OPCODES


def test_canonical_opcode_order():
    expected = (
        "NOP", "INC", "DEC", "ADD", "SUB", "LOAD", "SWAP", "HEAD", "JUMP", "JZ",
        "CMP", "SENSE", "INGEST", "EXCRETE", "MOVE", "TURN", "DIVIDE", "COPY", "RAND", "LOOP",
    )  # fmt: skip
    assert OPCODES == expected


def test_ancestor_genome_entries_are_valid_opcodes():
    assert len(ANCESTOR_GENOME) > 0
    for op in ANCESTOR_GENOME:
        assert 0 <= op < N_OPCODES


# --------------------------------------------------------------------------- #
# 2. Energy accounting + register arithmetic                                  #
# --------------------------------------------------------------------------- #
def test_instruction_cost_charged_every_tick():
    cfg = VMConfig(instruction_cost=1.0)
    org = _org([OP["NOP"]], energy=10.0)
    world = MockWorld()
    _run_one(org, world, cfg)
    assert org.energy == 9.0
    assert org.last_op == OP["NOP"]
    assert org.age == 1


def test_empty_genome_just_charges_cost():
    org = _org([], energy=5.0)
    _run_one(org, MockWorld(), VMConfig(instruction_cost=2.0))
    assert org.energy == 3.0


def test_inc_dec_wrap_and_head_select():
    org = _org([OP["INC"]], energy=100.0)
    org.regs = [10, 0, 0, 0]
    _run_one(org, MockWorld())
    assert org.regs[0] == 11

    # DEC at 0 wraps to 255 via &0xFF.
    org = _org([OP["DEC"]], energy=100.0)
    org.regs = [0, 0, 0, 0]
    _run_one(org, MockWorld())
    assert org.regs[0] == 255

    # INC at 255 wraps to 0.
    org = _org([OP["INC"]], energy=100.0)
    org.regs = [255, 0, 0, 0]
    _run_one(org, MockWorld())
    assert org.regs[0] == 0

    # HEAD advances which register is acted on.
    org = _org([OP["HEAD"], OP["INC"]], energy=100.0)
    org.regs = [0, 0, 0, 0]
    _run_one(org, MockWorld())  # HEAD -> head == 1
    assert org.head == 1
    _run_one(org, MockWorld())  # INC -> regs[1]
    assert org.regs[1] == 1
    assert org.regs[0] == 0


def test_add_sub_use_regs_1_and_2():
    org = _org([OP["ADD"]], energy=100.0)
    org.regs = [0, 200, 100, 0]
    _run_one(org, MockWorld())
    assert org.regs[0] == (300 & 0xFF)  # 44

    org = _org([OP["SUB"]], energy=100.0)
    org.regs = [0, 5, 10, 0]
    _run_one(org, MockWorld())
    assert org.regs[0] == ((5 - 10) & 0xFF)  # 251


def test_swap_exchanges_reg0_and_head():
    org = _org([OP["SWAP"]], energy=100.0)
    org.regs = [1, 2, 3, 4]
    org.head = 2
    _run_one(org, MockWorld())
    assert org.regs[0] == 3
    assert org.regs[2] == 1


def test_cmp_sets_sign_flag():
    # reg0 > reg1 -> +1
    org = _org([OP["CMP"]], energy=100.0)
    org.regs = [10, 5, 0, 0]
    _run_one(org, MockWorld())
    assert org.flag == 1
    # reg0 < reg1 -> -1
    org = _org([OP["CMP"]], energy=100.0)
    org.regs = [5, 10, 0, 0]
    _run_one(org, MockWorld())
    assert org.flag == -1
    # equal -> 0
    org = _org([OP["CMP"]], energy=100.0)
    org.regs = [7, 7, 0, 0]
    _run_one(org, MockWorld())
    assert org.flag == 0


# --------------------------------------------------------------------------- #
# 3. World-coupled opcodes                                                    #
# --------------------------------------------------------------------------- #
def test_ingest_adds_energy_by_gain():
    cfg = VMConfig(instruction_cost=1.0, ingest_gain=28.0)
    org = _org([OP["INGEST"]], energy=100.0)
    world = MockWorld(ingest=0.5)
    _run_one(org, world, cfg)
    # +0.5 * 28 income, -1 instruction cost.
    assert org.energy == 100.0 + 0.5 * 28.0 - 1.0


def test_sense_writes_substrate_into_head_register():
    org = _org([OP["SENSE"]], energy=100.0)
    org.head = 2
    world = MockWorld(substrate=137)
    _run_one(org, world)
    assert org.regs[2] == 137
    # Masked to a byte.
    org = _org([OP["SENSE"]], energy=100.0)
    world = MockWorld(substrate=300)
    _run_one(org, world)
    assert org.regs[0] == 300 & 0xFF


def test_excrete_charges_cost_and_calls_world():
    cfg = VMConfig(instruction_cost=1.0, excrete_cost=0.5)
    org = _org([OP["EXCRETE"]], energy=100.0)
    world = MockWorld()
    _run_one(org, world, cfg)
    assert world.excrete_calls == 1
    assert org.energy == 100.0 - 1.0 - 0.5


def test_move_charges_only_on_success():
    cfg = VMConfig(instruction_cost=1.0, move_cost=2.0)
    # success: charged instruction + move cost
    org = _org([OP["MOVE"]], energy=100.0)
    world = MockWorld(move_ok=True)
    _run_one(org, world, cfg)
    assert world.move_calls == 1
    assert org.energy == 100.0 - 1.0 - 2.0

    # failure: only the base instruction cost
    org = _org([OP["MOVE"]], energy=100.0)
    world = MockWorld(move_ok=False)
    _run_one(org, world, cfg)
    assert world.move_calls == 1
    assert org.energy == 100.0 - 1.0


# --------------------------------------------------------------------------- #
# 4. DIVIDE threshold                                                          #
# --------------------------------------------------------------------------- #
def test_divide_requires_energy_AND_a_complete_self_copy():
    # Self-encoded replication: DIVIDE fires only when BOTH (a) energy is at or
    # above the threshold after the instruction charge, AND (b) the daughter
    # tape COPY has been building is at least a full genome long. Energy alone
    # is not enough — a genome that never copies itself leaves no offspring.
    cfg = VMConfig(instruction_cost=1.0, e_div=120.0)
    n = 1  # single-instruction genome [DIVIDE]; a full self-copy is length 1.

    # (a) Energy high but daughter buffer EMPTY → no request (no self-copy).
    org = _org([OP["DIVIDE"]], energy=500.0)
    assert len(org.daughter) < n
    world = MockWorld()
    _run_one(org, world, cfg)
    assert world.division_requests == [], "DIVIDE fired without a self-copy"

    # (b) Energy high AND a full-length daughter tape → request fires.
    org = _org([OP["DIVIDE"]], energy=500.0, oid=7)
    org.daughter = [OP["NOP"]]  # a complete (length-n) self-copy is ready
    world = MockWorld()
    _run_one(org, world, cfg)
    assert world.division_requests == [7]

    # (c) Full self-copy but energy below threshold (121-1 == 120 ok; 120-1 < 120 no).
    org = _org([OP["DIVIDE"]], energy=120.0)
    org.daughter = [OP["NOP"]]
    world = MockWorld()
    _run_one(org, world, cfg)
    assert world.division_requests == [], "DIVIDE fired below the energy threshold"

    org = _org([OP["DIVIDE"]], energy=121.0)
    org.daughter = [OP["NOP"]]
    world = MockWorld()
    _run_one(org, world, cfg)
    assert world.division_requests == [org.oid]


# --------------------------------------------------------------------------- #
# 4b. COPY — the self-replication loop (Avida h-copy idiom)                    #
# --------------------------------------------------------------------------- #
def test_copy_builds_the_daughter_tape_from_own_genome():
    # With ε = 0, executing COPY n times copies the genome verbatim into the
    # daughter buffer; further COPYs are no-ops once the tape is full.
    cfg = VMConfig(copy_mutation=0.0)
    world = MockWorld()
    # A single-instruction genome: COPY caps the daughter tape at length 1.
    copy_org = _org([OP["COPY"]], energy=100.0)
    for _ in range(3):
        _run_one(copy_org, world, cfg)
    assert copy_org.daughter == [OP["COPY"]]

    # A length-3 genome: 3 COPYs build the full 3-instruction tape.
    org3 = _org([OP["COPY"], OP["INGEST"], OP["DIVIDE"]], energy=100.0)
    # Manually step COPY at ip 0 three times by resetting ip to 0 each time.
    for _ in range(3):
        org3.ip = 0
        _run_one(org3, world, cfg)
    assert org3.daughter == [OP["COPY"], OP["INGEST"], OP["DIVIDE"]]
    # A 4th COPY is a no-op — the tape is already a full self-copy.
    org3.ip = 0
    _run_one(org3, world, cfg)
    assert len(org3.daughter) == 3


def test_copy_applies_epsilon_mutation_at_copy_time():
    # ε = 1.0 → every copied instruction is resampled, so the daughter tape
    # diverges from the genome (Eigen's per-digit copy error, applied during
    # the act of copying — not as a free post-hoc engine mutation).
    cfg = VMConfig(copy_mutation=1.0)
    # A pure-COPY genome: every tick copies one instruction (the source is
    # always COPY), so with ε=1 the daughter tape should end up almost entirely
    # *not* COPY — proof the error is applied at copy time.
    org = _org([OP["COPY"]] * 60, energy=10_000.0)
    world = MockWorld(seed=1)
    for _ in range(60):
        _run_one(org, world, cfg)
    assert len(org.daughter) == 60
    # Most positions should have been mutated away from the source COPY opcode.
    mutated = sum(1 for v in org.daughter if v != OP["COPY"])
    assert mutated > 45, f"ε=1 should randomize most copied instructions, got {mutated}/60"


def test_divide_needs_the_copy_loop_to_run_first():
    # End-to-end at the VM level: a [COPY, DIVIDE] genome must run COPY enough
    # times to fill the 2-instruction tape before DIVIDE will request. Energy
    # is kept huge so the ONLY gate under test is the self-copy.
    cfg = VMConfig(copy_mutation=0.0, e_div=10.0)
    org = _org([OP["COPY"], OP["DIVIDE"]], energy=10_000.0)
    world = MockWorld()
    _run_one(org, world, cfg)  # ip0: COPY  → daughter=[COPY]
    _run_one(org, world, cfg)  # ip1: DIVIDE → tape len 1 < 2 → NO request
    assert world.division_requests == []
    _run_one(org, world, cfg)  # ip0: COPY  → daughter=[COPY, DIVIDE] (full)
    _run_one(org, world, cfg)  # ip1: DIVIDE → tape full → request
    assert world.division_requests == [org.oid]


# --------------------------------------------------------------------------- #
# 7. LOAD immediate                                                            #
# --------------------------------------------------------------------------- #
def test_load_consumes_next_byte_as_immediate():
    # LOAD then literal 42; head=1 so it lands in regs[1].
    org = _org([OP["LOAD"], 42], energy=100.0)
    org.head = 1
    _run_one(org, MockWorld())
    assert org.regs[1] == 42
    # ip advanced past both the opcode and its immediate (wraps mod 2 -> 0).
    assert org.ip == 0


def test_load_immediate_masked_to_byte():
    org = _org([OP["LOAD"], 300], energy=100.0)
    _run_one(org, MockWorld())
    assert org.regs[0] == 300 & 0xFF


# --------------------------------------------------------------------------- #
# 5. Mutation + Eigen error threshold                                          #
# --------------------------------------------------------------------------- #
def test_mutate_epsilon_zero_is_identical_copy():
    rng = random.Random(1)
    genome = list(ANCESTOR_GENOME)
    out = mutate_genome(genome, 0.0, rng)
    assert out == genome
    assert out is not genome  # a copy, not the same object


def test_mutate_epsilon_one_randomizes_every_position():
    rng = random.Random(2)
    # Use a long uniform genome so the random replacement is very unlikely to
    # coincide with the original at many positions.
    genome = [0] * 200
    out = mutate_genome(genome, 1.0, rng)
    assert len(out) == len(genome)
    # All entries are valid opcodes.
    assert all(0 <= v < N_OPCODES for v in out)
    # With epsilon=1 every position is resampled; expected matches ~ L/20.
    d = genome_distance(out, genome)
    assert d > len(genome) * 0.8  # ~190 expected, comfortably above 160


def test_error_threshold_formula_and_default():
    L = 13
    # Exact formula with sigma = e: ln(e)/L = 1/L.
    assert error_threshold(L) == math.log(math.e) / L
    assert abs(error_threshold(L) - 1.0 / L) < 1e-12
    # Explicit sigma argument.
    sigma = 8.0
    assert error_threshold(L, selective_superiority=sigma) == math.log(sigma) / L


# --------------------------------------------------------------------------- #
# 6. Genome distance                                                           #
# --------------------------------------------------------------------------- #
def test_genome_distance_cases():
    assert genome_distance([1, 2, 3], [1, 2, 3]) == 0
    assert genome_distance([1, 2, 3], [1, 9, 3]) == 1
    # length difference is counted in addition to mismatches over overlap
    assert genome_distance([1, 2, 3], [1, 2, 3, 4, 5]) == 2
    assert genome_distance([1, 2, 3, 9], [1, 0, 3]) == 1 + 1  # one mismatch + one length diff
