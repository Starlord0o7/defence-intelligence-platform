"""Improved keyword risk scoring for document chunks.

Builds on the rules in analysis.py (imported, not modified) and adds:
- more keywords (military, cyber, unrest, natural hazards)
- negation handling: "no casualties" does not add points
- a small, capped bonus for repeated keywords
- explainable output: matched, negated and calming keywords are listed

Still keyword rules chosen by the team, not a trained or validated model.
"""
import re

try:  # reuse the team's existing rules and thresholds
    from analysis import (CALMING_KEYWORDS, HIGH_THRESHOLD, MEDIUM_THRESHOLD,
                          RISK_KEYWORDS, score_to_priority)
except ImportError:  # run outside backend/ (e.g. unit tests of this package)
    RISK_KEYWORDS = {"attack": 30, "troop": 30, "missile": 30, "border": 20,
                     "flood": 20, "heavy": 20, "advisory": 10}
    CALMING_KEYWORDS = {"normal": -20, "routine": -20, "stable": -20}
    HIGH_THRESHOLD, MEDIUM_THRESHOLD = 60, 30

    def score_to_priority(score: int) -> str:
        if score >= HIGH_THRESHOLD:
            return "High"
        return "Medium" if score >= MEDIUM_THRESHOLD else "Low"

EXTRA_RISK_KEYWORDS = {
    "shelling": 30, "ambush": 30, "hostage": 30, "skirmish": 30,
    "intrusion": 30, "ransomware": 30, "cyberattack": 30,
    "earthquake": 20, "landslide": 20, "cyclone": 20, "drone": 20,
    "mobiliz": 20, "blockade": 20, "curfew": 20, "smuggl": 20, "clash": 20,
    "protest": 10, "suspicious": 10,
}

ALL_RISK_KEYWORDS = {**EXTRA_RISK_KEYWORDS, **RISK_KEYWORDS}  # team rules win

NEGATIONS = {"no", "not", "without", "nil", "zero", "none", "neither", "nor",
             "never", "absence"}
NEGATION_WINDOW = 3          # words before the keyword that are checked
REPEAT_BONUS = 5             # per extra occurrence of the same keyword
REPEAT_BONUS_CAP = 10        # max bonus per keyword


def _is_negated(text: str, start: int) -> bool:
    before = re.findall(r"[a-z']+", text[max(0, start - 60):start])
    return any(w in NEGATIONS for w in before[-NEGATION_WINDOW:])


def score_text(text: str) -> dict:
    """Score one piece of text (a chunk or a whole document)."""
    lowered = text.lower()
    total, matched, negated, calming = 0, [], [], []

    for word, points in ALL_RISK_KEYWORDS.items():
        live = 0
        for m in re.finditer(r"\b" + re.escape(word), lowered):
            if _is_negated(lowered, m.start()):
                if word not in negated:
                    negated.append(word)
            else:
                live += 1
        if live:
            matched.append(word)
            total += points + min(REPEAT_BONUS_CAP, REPEAT_BONUS * (live - 1))

    for word, points in CALMING_KEYWORDS.items():
        if re.search(r"\b" + re.escape(word), lowered):
            calming.append(word)
            total += points

    score = max(0, min(100, total))
    priority = score_to_priority(score)

    if matched or calming:
        reasoning = f"Score {score}/100 from keywords: {', '.join(matched + calming)}."
    else:
        reasoning = "No risk keywords matched, so the score is 0 (Low)."
    if negated:
        reasoning += f" Ignored because negated: {', '.join(negated)}."

    return {
        "risk_score": score,
        "priority": priority,
        "matched_keywords": matched + calming,
        "negated_keywords": negated,
        "reasoning": reasoning,
    }
