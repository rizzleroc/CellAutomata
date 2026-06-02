"""Day-in-the-Life narrative script — content and stage-resolution invariants.

These tests guard the *content* layer of the story channel: that the twelve
day-beats are well-formed (stage indices in order, moods and times from the
canonical vocabularies, lines short and first-person-sized, sky colours valid),
and that ``NarrativeScript.beat_for`` is total — it never raises and clamps both
the canonical 5-stage pipeline and arbitrary out-of-range indices onto the
extended 12-beat arc.
"""

from __future__ import annotations

from cellauto.character import MOODS
from cellauto.narrative import (
    DAY_IN_THE_LIFE,
    SKY_COLORS,
    TIMES_OF_DAY,
    DayBeat,
    NarrativeScript,
)


def test_day_has_twelve_beats_in_stage_order():
    assert len(DAY_IN_THE_LIFE) == 12
    for index, beat in enumerate(DAY_IN_THE_LIFE):
        assert beat.stage == index


def test_every_mood_is_known():
    for beat in DAY_IN_THE_LIFE:
        assert beat.mood in MOODS


def test_every_time_of_day_is_known():
    for beat in DAY_IN_THE_LIFE:
        assert beat.time_of_day in TIMES_OF_DAY


def test_lines_are_non_empty_and_short():
    for beat in DAY_IN_THE_LIFE:
        assert beat.line.strip()
        assert len(beat.line) <= 160


def test_titles_and_clocks_are_non_empty():
    for beat in DAY_IN_THE_LIFE:
        assert beat.title.strip()
        assert beat.clock.strip()


def test_sky_is_valid_rgb_triple():
    for beat in DAY_IN_THE_LIFE:
        assert isinstance(beat.sky, tuple)
        assert len(beat.sky) == 3
        for channel in beat.sky:
            assert isinstance(channel, int)
            assert 0 <= channel <= 255


def test_sky_matches_time_of_day_palette():
    for beat in DAY_IN_THE_LIFE:
        assert beat.sky == SKY_COLORS[beat.time_of_day]


def test_arc_starts_curious_and_ends_reborn():
    assert DAY_IN_THE_LIFE[0].mood == "curious"
    assert DAY_IN_THE_LIFE[-1].mood == "reborn"
    assert DAY_IN_THE_LIFE[-1].time_of_day == "dawn"


def test_beat_for_never_raises_and_returns_daybeat():
    script = NarrativeScript()
    for stage in range(-3, 20):
        beat = script.beat_for(stage)
        assert isinstance(beat, DayBeat)


def test_canonical_pipeline_maps_onto_extended_arc():
    script = NarrativeScript()
    assert script.beat_for(0, pipeline_len=5).stage == 0
    assert script.beat_for(1, pipeline_len=5).stage == 2
    assert script.beat_for(2, pipeline_len=5).stage == 4
    assert script.beat_for(3, pipeline_len=5).stage == 9
    assert script.beat_for(4, pipeline_len=5).stage == 10


def test_canonical_pipeline_clamps_out_of_range():
    script = NarrativeScript()
    # Canonical index clamps to [0, 4] before the mapping.
    assert script.beat_for(-2, pipeline_len=5).stage == 0
    assert script.beat_for(99, pipeline_len=5).stage == 10


def test_extended_pipeline_is_direct_index():
    script = NarrativeScript()
    for stage in range(12):
        assert script.beat_for(stage).stage == stage


def test_extended_pipeline_clamps_out_of_range():
    script = NarrativeScript()
    assert script.beat_for(99).stage == 11
    assert script.beat_for(-5).stage == 0


def test_empty_beats_returns_safe_fallback():
    script = NarrativeScript(beats=[])
    beat = script.beat_for(3)
    assert isinstance(beat, DayBeat)
    assert beat.mood in MOODS
    assert beat.time_of_day in TIMES_OF_DAY
    assert beat.line.strip()


def test_default_pipeline_len_is_extended():
    script = NarrativeScript()
    # The default pipeline_len (12) must treat the index as an extended beat,
    # not route it through the canonical mapping.
    assert script.beat_for(1).stage == 1
