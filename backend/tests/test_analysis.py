import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis import analyze, score_to_priority
from data_store import Report, load_reports


def make_report(title="t", summary="s", category="c", priority="Low"):
    return {"id": 1, "title": title, "category": category,
            "location": "x", "source": "x", "summary": summary,
            "priority": priority}


def test_load_reports_returns_three_valid_reports():
    reports = load_reports()
    assert len(reports) == 3
    assert {r["priority"] for r in reports} == {"High", "Medium", "Low"}


def test_invalid_priority_is_rejected():
    with pytest.raises(ValidationError):
        Report(id=1, title="a", category="b", location="c",
               source="d", summary="e", priority="Urgent")


def test_missing_field_is_rejected():
    with pytest.raises(ValidationError):
        Report(id=1, title="a", category="b")


def test_risky_text_scores_high_and_lists_keywords():
    result = analyze(make_report(
        title="Troops reported near border",
        summary="Missile warning issued after an attack."))
    assert result["priority"] == "High"
    assert "troop" in result["matched_keywords"]
    assert result["risk_score"] <= 100


def test_calm_text_scores_low():
    result = analyze(make_report(summary="Routine and stable operations."))
    assert result["priority"] == "Low"
    assert result["risk_score"] == 0


def test_text_without_keywords_scores_zero():
    result = analyze(make_report(title="Library opens", summary="Books lent."))
    assert result["risk_score"] == 0
    assert result["matched_keywords"] == []


def test_thresholds():
    assert score_to_priority(60) == "High"
    assert score_to_priority(30) == "Medium"
    assert score_to_priority(29) == "Low"


def test_sample_reports_computed_vs_labelled():
    # Compares computed and labelled priority on the 3 synthetic samples.
    # This is a sanity check only, not an accuracy measurement.
    for report in load_reports():
        result = analyze(report)
        print(report["id"], result["risk_score"],
              result["priority"], result["labelled_priority"])
        assert result["priority"] in {"High", "Medium", "Low"}
