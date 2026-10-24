"""Clinical-validation tooling: error types, agreement statistics, plain language, norms."""

import uuid

import pytest

from app.analysis.errors import classify_naming, sounds_similar
from app.exercises.norms import estimate_levels, syllables
from app.scripts import validate_scoring
from app.validation import metrics, plain_language


@pytest.mark.parametrize(
    ("response", "target", "outcome", "expected"),
    [
        ("dog", "dog", "correct", "correct"),
        ("", "dog", "skipped", "no_response"),
        ("um I don't know", "dog", "incorrect", "no_response"),
        ("cat", "dog", "incorrect", "semantic"),
        ("bone", "dog", "incorrect", "semantic"),
        ("log", "dog", "incorrect", "formal"),
        ("duck", "dog", "incorrect", "mixed"),
        ("spoon", "dog", "incorrect", "unrelated"),
        ("glarnet", "cup", "incorrect", "nonword_unrelated"),
        ("pensil", "pencil", "near_miss", "nonword_related"),
        ("you drink tea from it", "cup", "incorrect", "description"),
    ],
)
def test_pnt_error_types(response, target, outcome, expected):
    assert classify_naming(response, target, [target], outcome) == expected


def test_sound_similarity_uses_sounds_not_letters():
    assert sounds_similar("fone", "phone")
    assert sounds_similar("nife", "knife")
    assert not sounds_similar("spoon", "dog")


def test_benchmark_meets_its_targets():
    """Regression guard: the published numbers in docs/validation must not silently degrade."""
    for path in validate_scoring.SETS.values():
        r = validate_scoring.run(path)
        assert r["correctness"]["false_accept_rate"] <= 0.05
        assert r["correctness"]["false_reject_rate"] <= 0.10
        assert r["kappa"] >= 0.74


def test_agreement_statistics():
    a = ["x", "x", "y", "y"]
    assert metrics.percent_agreement(a, a) == 1.0
    assert metrics.cohen_kappa(a, a) == 1.0
    assert metrics.cohen_kappa(a, ["y", "y", "x", "x"]) == pytest.approx(-1.0)
    assert metrics.gwet_ac1(a, a) == 1.0
    rates = metrics.accept_rates([True, False, False], [True, True, False])
    assert rates["false_accept_rate"] == 0.5
    assert rates["false_reject_rate"] == 0.0
    assert metrics.spearman([1, 2, 3], [10, 20, 30]) == pytest.approx(1.0)
    assert metrics.spearman([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)


def test_content_validity_index():
    cvi = metrics.content_validity([[4, 4, 3], [4, 2, 1]])
    assert cvi["i_cvi"] == [1.0, pytest.approx(1 / 3)]
    assert cvi["s_cvi_ave"] == pytest.approx(2 / 3)
    assert cvi["s_cvi_ua"] == 0.5


def test_plain_language_checks():
    assert plain_language.check("What is this?", "prompt") == []
    assert "rare_word:prompt" in plain_language.check("Identify this utensil.", "prompt")
    assert plain_language.check("Name this stethoscope.", "prompt", {"stethoscope"}) == []
    assert plain_language.check("Look at the cup's handle.", "feedback") == []
    assert plain_language.check("The kettle's spout.", "feedback", {"kettle"}) == []
    assert "patronising:feedback" in plain_language.check("Good girl, sweetie!", "feedback")
    long = "This is a very long sentence that keeps going on and on for far too long."
    assert "long_sentence:feedback" in plain_language.check(long, "feedback")


def test_norm_levels_rank_common_short_words_easier():
    assert syllables("refrigerator") == 5
    assert syllables("cup") == 1
    levels = estimate_levels(["cup", "dog", "car", "refrigerator", "microscope", "telescope"])
    assert levels["cup"][1] < levels["refrigerator"][1]


def test_simulation_supports_the_personalization_claim():
    """The documented claim (docs/validation/personalization.md): ability-guided progression
    keeps more practice in the productive band than the step rule or fixed difficulty."""
    from app.scripts.simulate_learners import simulate

    stable = simulate(40, seed=3)["Stable ability, model correct"]
    assert stable["step+ability"]["in_band"] > stable["step-rule"]["in_band"]
    assert stable["step+ability"]["in_band"] > stable["fixed-middle"]["in_band"]


def test_panel_analysis_round_trip(tmp_path, monkeypatch):
    """Two raters who agree with the app give perfect agreement and no false accepts."""
    import csv

    from app.scripts import analyse_panel as ap

    monkeypatch.setattr(ap, "PACKETS", tmp_path / "packets")
    monkeypatch.setattr(ap, "PANEL", tmp_path / "panel")
    assert ap.make_scoring_packet() == ap.SCORING_PACKET_SIZE
    key = list(csv.DictReader((tmp_path / "packets" / "phase1-scoring-key.csv").open()))
    for rater in ("r1", "r2"):
        with (tmp_path / "panel" / "scoring" / f"{rater}.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["item_id", "correct", "error_type"])
            for k in key:
                w.writerow([k["item_id"], k["app_correct"], k["app_error_type"]])
    lines = ap.analyse_scoring()
    assert "| r1 vs r2 | 200 | 1.00 | 1.00 | — |" in lines
    assert "| App vs r1 | 200 | 1.00 | 1.00 | 0.0% |" in lines
    assert ap.analyse_content() == ["No content ratings returned yet (`panel/content/*.csv`)."]


def test_study_analysis_compares_conditions(tmp_path):
    import csv

    from app.scripts.study_data import FIELDS, analyse, nap, pseudonym

    assert nap([0.2, 0.3], [0.8, 0.9]) == 1.0
    assert nap([0.5], [0.5]) == 0.5
    pid = uuid.uuid4()
    assert pseudonym("s1", pid) != pseudonym("s2", pid) and str(pid) not in pseudonym("s1", pid)
    path = tmp_path / "study.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for session, (cond, outcome) in enumerate(
            [("step", "incorrect"), ("ability", "correct")] * 3, 1
        ):
            for pos in range(1, 6):
                w.writerow(
                    {
                        "participant": "P-x",
                        "study_day": 0,
                        "session": session,
                        "position": pos,
                        "condition": cond,
                        "exercise_type": "picture_naming",
                        "item": "cup",
                        "difficulty": 1,
                        "mode": "text",
                        "outcome": outcome,
                        "error_type": "",
                        "hints_used": 0,
                        "latency_ms": 900,
                    }
                )
    report = analyse(path)
    assert "| P-x | ability | 3 | 15 | 100% |" in report and "| 1.00 |" in report


def test_feedback_never_calls_a_different_word_close():
    import json

    from app.validation.generated_text import check_feedback

    raw = json.dumps({"feedback": "You are nearing the right word."})
    assert "contradicts_score:feedback" in check_feedback(raw, "incorrect")[0].reasons
    assert check_feedback(raw, "near_miss")[0].ok
