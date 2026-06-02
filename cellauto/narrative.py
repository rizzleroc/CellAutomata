"""Day-in-the-Life narrative script (v4.1) — the anthropomorphized story channel.

This module is the *content* layer of cellauto's second animation channel: a
clearly-labelled, first-person "day in the life of the cell" narration that
rides on top of the grounded SEM micrograph. It is **storytelling, not
instrument truth** — the SEM channel (``renderer_sem``) remains the literal
depth-shaded view of the simulation; this channel narrates that view as a
character's day.

The twelve origin-of-life stages of the extended pipeline are mapped onto the
arc of a single day — dawn → morning → noon → afternoon → dusk → night →
rebirth-at-dawn — so a viewer experiences abiogenesis as "a day in the life"
of one protagonist: the cell, telling its own story in the first person.

Interface contract (locked — implementers fill the bodies, do not change
signatures):

    DayBeat              — frozen dataclass, one narrative beat per stage
    TIMES_OF_DAY         — ordered tuple of the six day phases
    DAY_IN_THE_LIFE      — list[DayBeat], one per EXTENDED pipeline stage (12)
    NarrativeScript      — resolves a (stage, pipeline_len) → DayBeat

Both the canonical 5-stage pipeline and the extended 12-stage pipeline must
resolve to a sensible beat (canonical stages map onto the extended arc).
"""

from __future__ import annotations

from dataclasses import dataclass

# Ordered day phases. Index 0 is the first light, index 5 is deep night; the
# final stage loops back to a new dawn (rebirth) — see DAY_IN_THE_LIFE.
TIMES_OF_DAY: tuple[str, ...] = (
    "dawn",
    "morning",
    "noon",
    "afternoon",
    "dusk",
    "night",
)

# Time-of-day accent colours (RGB) used by the channel's light grade so each
# beat reads as a distinct moment in a day. Implementers may tune these.
SKY_COLORS: dict[str, tuple[int, int, int]] = {
    "dawn": (0xE8, 0xB0, 0x7A),
    "morning": (0xF2, 0xD9, 0xA6),
    "noon": (0xFB, 0xF3, 0xDE),
    "afternoon": (0xE6, 0xC0, 0x86),
    "dusk": (0xC8, 0x7A, 0x6E),
    "night": (0x3A, 0x4A, 0x6E),
}


@dataclass(frozen=True)
class DayBeat:
    """One narrative beat — the cell's voice for a single pipeline stage.

    Fields:
      stage        extended-pipeline stage index this beat narrates (0-based).
      time_of_day  one of TIMES_OF_DAY.
      clock        display clock label, e.g. "06:00".
      title        short anthropomorphized chapter title, e.g. "First Stirrings".
      line         1-2 sentence FIRST-PERSON narration ("the cell" speaking).
      mood         a CharacterMood key (see cellauto.character.MOODS):
                   curious | calm | excited | struggling | triumphant |
                   weary | reborn.
      sky          time-of-day accent RGB (defaults from SKY_COLORS[time_of_day]).
    """

    stage: int
    time_of_day: str
    clock: str
    title: str
    line: str
    mood: str
    sky: tuple[int, int, int]


# AGENT(task #2): populate one DayBeat per EXTENDED pipeline stage (12 entries,
# stage indices 0..11 in the extended order:
#   0 soup, 1 vent, 2 reaction-diffusion, 3 minerals, 4 RAF, 5 chirality,
#   6 RNA world, 7 genetic code, 8 coacervate, 9 vesicles, 10 selection,
#   11 LUCA).
# Map them across the day arc (roughly two stages per phase, ending at night /
# looping to a new dawn for LUCA = "rebirth"). Keep each `line` first-person,
# warm, scientifically-faithful-but-anthropomorphized, <= ~160 chars. Pull the
# science from docs/science.md and the StageInfo entries in
# cellauto/rules/abiogenesis/pipeline.py so the story never contradicts the sim.
DAY_IN_THE_LIFE: list[DayBeat] = [
    DayBeat(
        stage=0,
        time_of_day="dawn",
        clock="05:30",
        title="First Stirrings",
        line=(
            "I wake as a haze of loose molecules, glycine and formic acid "
            "drifting in a warm ocean. I am not yet anyone — just the soup."
        ),
        mood="curious",
        sky=(210, 150, 165),
    ),
    DayBeat(
        stage=1,
        time_of_day="dawn",
        clock="06:30",
        title="Warm Hands in the Dark",
        line=(
            "I press against a vent's alkaline wall, where acid meets base. "
            "The proton gradient is the first warmth I ever feel — free energy."
        ),
        mood="calm",
        sky=(228, 162, 150),
    ),
    DayBeat(
        stage=2,
        time_of_day="morning",
        clock="08:30",
        title="I Learn to Ripple",
        line=(
            "Morning light, and I begin to pattern. Feed and kill races "
            "across me as spots and stripes — my first self-made shape."
        ),
        mood="excited",
        sky=(190, 215, 205),
    ),
    DayBeat(
        stage=3,
        time_of_day="morning",
        clock="10:00",
        title="A Workbench of Clay",
        line=(
            "I settle on a clay surface that holds my monomers close, and "
            "let me string them into my first real chains against the water."
        ),
        mood="curious",
        sky=(216, 228, 196),
    ),
    DayBeat(
        stage=4,
        time_of_day="noon",
        clock="12:00",
        title="The Loop That Feeds Itself",
        line=(
            "At noon my reactions close into a ring — each one makes the "
            "next. I am autocatalytic now: a fire that keeps itself lit."
        ),
        mood="excited",
        sky=(250, 248, 238),
    ),
    DayBeat(
        stage=5,
        time_of_day="noon",
        clock="13:00",
        title="Choosing a Hand",
        line=(
            "Mirror-twins fought inside me until one hand won. I am "
            "homochiral now — left-handed, certain, no longer symmetric."
        ),
        mood="triumphant",
        sky=(252, 242, 212),
    ),
    DayBeat(
        stage=6,
        time_of_day="afternoon",
        clock="14:30",
        title="My First Memory",
        line=(
            "I copy an RNA strand base by base. Errors creep in, but below "
            "the threshold I hold the master sequence — I can remember myself."
        ),
        mood="struggling",
        sky=(238, 196, 128),
    ),
    DayBeat(
        stage=7,
        time_of_day="afternoon",
        clock="16:00",
        title="Learning a Shared Word",
        line=(
            "My codons and my code grow up together until neighbors and I "
            "agree what each triplet means. We are writing one language."
        ),
        mood="triumphant",
        sky=(236, 176, 108),
    ),
    DayBeat(
        stage=8,
        time_of_day="dusk",
        clock="18:30",
        title="Gathering Myself In",
        line=(
            "At dusk my crowded molecules condense into droplets — no skin "
            "yet, just dense and dilute. I have an inside for the first time."
        ),
        mood="calm",
        sky=(230, 140, 96),
    ),
    DayBeat(
        stage=9,
        time_of_day="dusk",
        clock="20:00",
        title="A Skin of My Own",
        line=(
            "Fatty acids gather past their threshold and wrap me in a "
            "bilayer. I am bounded now — a protocell with a within and a without."
        ),
        mood="weary",
        sky=(200, 108, 104),
    ),
    DayBeat(
        stage=10,
        time_of_day="night",
        clock="22:30",
        title="Surviving the Night",
        line=(
            "In the dark I grow, divide, and pass my mix to a daughter with "
            "small mutations. The fit endure: this is selection, and I am it."
        ),
        mood="triumphant",
        sky=(44, 64, 104),
    ),
    DayBeat(
        stage=11,
        time_of_day="dawn",
        clock="05:00",
        title="The Ancestor at Dawn",
        line=(
            "A new dawn distills me down to the core every lineage will "
            "inherit. I am LUCA — the last common ancestor, born again."
        ),
        mood="reborn",
        sky=(224, 168, 178),
    ),
]


# Canonical 5-stage pipeline (soup, reaction-diffusion, RAF, vesicles,
# selection) mapped onto the extended 12-beat day arc.
_CANONICAL_TO_EXTENDED: tuple[int, ...] = (0, 2, 4, 9, 10)


class NarrativeScript:
    """Resolves a live pipeline stage to its day-in-the-life beat.

    Construct once; ``beat_for`` is called every frame by the channel, so it
    must be cheap (no allocation in the hot path beyond a dict lookup).
    """

    def __init__(self, beats: list[DayBeat] | None = None) -> None:
        self._beats = beats if beats is not None else DAY_IN_THE_LIFE

    def all_beats(self) -> list[DayBeat]:
        return list(self._beats)

    def beat_for(self, stage: int, *, pipeline_len: int = 12) -> DayBeat:
        """Return the DayBeat for ``stage`` of a pipeline of length
        ``pipeline_len``.

        AGENT(task #2): map the canonical 5-stage pipeline onto the 12-beat
        extended arc (so canonical Stage 2 'vesicles' lands on the vesicle
        beat, etc.), and clamp out-of-range indices. Must never raise —
        return a sensible fallback beat for unknown stages.
        """
        beats = self._beats
        if not beats:
            return DayBeat(
                stage=0,
                time_of_day="dawn",
                clock="05:30",
                title="First Stirrings",
                line="I wake as a haze of loose molecules in a warm ocean.",
                mood="curious",
                sky=SKY_COLORS["dawn"],
            )

        last = len(beats) - 1

        if pipeline_len <= 5:
            # Canonical 5-stage pipeline: soup, reaction-diffusion, RAF,
            # vesicles, selection → extended-beat indices.
            canonical = 0 if stage < 0 else 4 if stage > 4 else stage
            extended_index = _CANONICAL_TO_EXTENDED[canonical]
        else:
            extended_index = stage

        # Clamp the resolved index into the valid beat range.
        if extended_index < 0:
            extended_index = 0
        elif extended_index > last:
            extended_index = last

        return beats[extended_index]
