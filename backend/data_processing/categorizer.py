"""Rule-based event categorisation.

Categories 'Weather', 'Public Safety' and 'Infrastructure' match the labels
already used in data/reports.json. Like analysis.py this is keyword rules,
not a trained model, and every result lists the keywords that decided it.
"""
import re

CATEGORY_KEYWORDS = {
    "Weather": ["rain", "rainfall", "storm", "cyclone", "fog", "snowfall",
                "heatwave", "waterlogg", "weather", "monsoon", "wind"],
    "Natural Disaster": ["flood", "earthquake", "landslide", "avalanche",
                         "tsunami", "wildfire", "cloudburst", "drought"],
    "Public Safety": ["advisory", "evacuat", "rescue", "emergency",
                      "casualt", "injur", "residents", "relief", "shelter"],
    "Infrastructure": ["road", "bridge", "power", "outage", "grid", "rail",
                       "pipeline", "telecom", "airport", "port", "dam",
                       "infrastructure", "transport"],
    "Border Security": ["border", "infiltrat", "smuggl", "crossing",
                        "patrol", "fence", "intrusion", "ceasefire"],
    "Military Activity": ["troop", "missile", "artillery", "shelling",
                          "deploy", "mobiliz", "armoured", "drone",
                          "exercise", "garrison", "military"],
    "Cyber": ["cyber", "malware", "ransomware", "phishing", "hack",
              "breach", "ddos", "network intrusion"],
    "Civil Unrest": ["protest", "riot", "curfew", "unrest", "clash",
                     "demonstrat", "strike", "blockade"],
}

DEFAULT_CATEGORY = "General"


def categorize(text: str) -> dict:
    """Return {"category", "scores", "matched_keywords"}.

    Each distinct keyword counts once per category (word-start matching, so
    'troop' matches 'troops'). The highest score wins; ties go to the
    category listed first above. No match gives 'General'.
    """
    lowered = text.lower()
    scores, matched = {}, {}

    for category, words in CATEGORY_KEYWORDS.items():
        hits = [w for w in words if re.search(r"\b" + re.escape(w), lowered)]
        if hits:
            scores[category] = len(hits)
            matched[category] = hits

    if not scores:
        return {"category": DEFAULT_CATEGORY, "scores": {}, "matched_keywords": []}

    best = max(scores, key=lambda c: (scores[c], -list(CATEGORY_KEYWORDS).index(c)))
    return {"category": best, "scores": scores, "matched_keywords": matched[best]}
