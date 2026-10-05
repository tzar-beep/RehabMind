from types import SimpleNamespace

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.analysis.scoring import score_naming
from app.performance.models import PerformanceProfile
from app.performance.progression import apply_outcome

CUP = ("cup", ["cup", "mug", "coffee cup"])


@pytest.mark.parametrize(
    ("answer", "outcome", "match"),
    [
        ("cup", "correct", "exact"),
        ("  Cup! ", "correct", "exact"),
        ("a cup", "correct", "exact"),
        ("mug", "correct", "accepted_variant"),
        ("cups", "correct", "plural"),
        ("it's a coffee cup", "correct", "in_phrase"),
        ("that's not a cup", "incorrect", "none"),
        ("cupp", "near_miss", "similar"),
        ("glass", "incorrect", "none"),
        ("", "skipped", "skipped"),
        ("I don't know", "skipped", "skipped"),
        (None, "skipped", "skipped"),
    ],
)
def test_naming_scoring(answer, outcome, match):
    result = score_naming(answer, *CUP)
    assert (result.outcome, result.match_type) == (outcome, match)


def test_near_miss_on_longer_words():
    assert score_naming("umbrela", "umbrella", ["umbrella"]).outcome == "near_miss"


def _cs(lo, hi, adv=3, back=2):
    return SimpleNamespace(
        min_difficulty=lo,
        max_difficulty=hi,
        advance_after_correct=adv,
        step_back_after_incorrect=back,
    )


def _profile(level):
    return PerformanceProfile(
        target_difficulty=level,
        consecutive_correct=0,
        consecutive_incorrect=0,
        total_attempts=0,
        total_correct=0,
        recent_outcomes=[],
    )


def test_advances_after_streak_and_caps_at_max():
    p, cs = _profile(2), _cs(1, 3)
    for _ in range(3):
        apply_outcome(p, "correct", cs)
    assert p.target_difficulty == 3
    for _ in range(9):
        apply_outcome(p, "correct", cs)
    assert p.target_difficulty == 3


def test_steps_back_and_floors_at_min():
    p, cs = _profile(2), _cs(2, 4)
    for _ in range(6):
        apply_outcome(p, "incorrect", cs)
    assert p.target_difficulty == 2


def test_near_miss_resets_streaks():
    p, cs = _profile(1), _cs(1, 5)
    apply_outcome(p, "correct", cs)
    apply_outcome(p, "correct", cs)
    apply_outcome(p, "near_miss", cs)
    apply_outcome(p, "correct", cs)
    assert p.target_difficulty == 1


@given(
    bounds=st.tuples(st.integers(1, 5), st.integers(1, 5)).map(sorted),
    start=st.integers(1, 5),
    outcomes=st.lists(st.sampled_from(["correct", "near_miss", "incorrect", "skipped"])),
    adv=st.integers(1, 10),
    back=st.integers(1, 10),
)
def test_progression_never_leaves_clinician_range(bounds, start, outcomes, adv, back):
    cs = _cs(bounds[0], bounds[1], adv, back)
    p = _profile(start)
    for o in outcomes:
        apply_outcome(p, o, cs)
        assert cs.min_difficulty <= p.target_difficulty <= cs.max_difficulty
