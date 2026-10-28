"""Rule-based report analysis with explainable output.

The score comes from keyword rules chosen by the team. It is NOT a trained
or validated AI model. Every result lists the keywords that caused the score
so a person can check the reasoning.
"""
import re

# Keyword -> points. Word-start matching, so "troop" also matches "troops".
RISK_KEYWORDS = {
    "attack": 30,
    "troop": 30,
    "missile": 30,
    "explosion": 30,
    "infiltrat": 30,
    "casualt": 30,
    "breach": 30,
    "border": 20,
    "severe": 20,
    "disrupt": 20,
    "emergency": 20,
    "flood": 20,
    "evacuat": 20,
    "outage": 20,
    "heavy": 20,
    "advisory": 10,
    "warning": 10,
    "delay": 10,
    "rainfall": 10,
}

# Words that suggest nothing unusual is happening reduce the score.
CALMING_KEYWORDS = {
    "normal": -20,
    "routine": -20,
    "stable": -20,
}

HIGH_THRESHOLD = 60
MEDIUM_THRESHOLD = 30

METHOD = "Keyword-based rule scoring (demonstration)"
LIMITATIONS = (
    "Keyword rules chosen by the team and tested only on synthetic data. "
    "Not a trained or validated AI model, not a real intelligence assessment."
)


def _find_matches(text: str, keywords: dict) -> list[tuple[str, int]]:
    matches = []
    for word, points in keywords.items():
        if re.search(r"\b" + re.escape(word), text):
            matches.append((word, points))
    return matches


def score_to_priority(score: int) -> str:
    if score >= HIGH_THRESHOLD:
        return "High"
    if score >= MEDIUM_THRESHOLD:
        return "Medium"
    return "Low"


def analyze(report: dict) -> dict:
    """Score one report and explain the result."""
    text = " ".join(
        [report["title"], report["category"], report["summary"]]
    ).lower()

    risk_matches = _find_matches(text, RISK_KEYWORDS)
    calming_matches = _find_matches(text, CALMING_KEYWORDS)

    raw_score = sum(p for _, p in risk_matches) + sum(p for _, p in calming_matches)
    score = max(0, min(100, raw_score))
    priority = score_to_priority(score)

    matched = [w for w, _ in risk_matches] + [w for w, _ in calming_matches]
    if matched:
        reasoning = (
            f"Score {score}/100 from keywords: {', '.join(matched)}. "
            f"Thresholds: High >= {HIGH_THRESHOLD}, Medium >= {MEDIUM_THRESHOLD}."
        )
    else:
        reasoning = "No risk keywords matched, so the score is 0 (Low)."

    return {
        "report_id": report["id"],
        "title": report["title"],
        "priority": priority,
        "labelled_priority": report["priority"],
        "risk_score": score,
        "matched_keywords": matched,
        "reasoning": reasoning,
        "method": METHOD,
        "limitations": LIMITATIONS,
    }
