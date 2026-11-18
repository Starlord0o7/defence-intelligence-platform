"""Date extraction from document text."""
import re
from datetime import date

_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}
_MONTH_RE = "|".join(list(_MONTHS) + [m[:3] for m in _MONTHS])

_PATTERNS = [
    # 15 October 2026 / 15th Oct, 2026
    (re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_RE})\.?,?\s+(\d{{4}})\b", re.I), "dmy_text"),
    # October 15, 2026
    (re.compile(rf"\b({_MONTH_RE})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})\b", re.I), "mdy_text"),
    # 2026-10-15
    (re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"), "iso"),
    # 15/10/2026 or 15-10-2026 (day first, as is usual in India)
    (re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b"), "dmy_num"),
]


def _month(name: str) -> int:
    name = name.lower()
    return _MONTHS.get(name) or next(v for k, v in _MONTHS.items() if k.startswith(name[:3]))


def _build(kind: str, g: tuple):
    try:
        if kind == "dmy_text":
            return date(int(g[2]), _month(g[1]), int(g[0]))
        if kind == "mdy_text":
            return date(int(g[2]), _month(g[0]), int(g[1]))
        if kind == "iso":
            return date(int(g[0]), int(g[1]), int(g[2]))
        return date(int(g[2]), int(g[1]), int(g[0]))
    except ValueError:  # e.g. 31/02/2026
        return None


def find_dates(text: str) -> list[tuple[int, date]]:
    """All valid dates in `text` as (position, date), in reading order."""
    found = []
    for pattern, kind in _PATTERNS:
        for match in pattern.finditer(text):
            parsed = _build(kind, match.groups())
            if parsed:
                found.append((match.start(), parsed))
    return sorted(found)


def extract_document_date(text: str) -> str:
    """Best guess at the document date as 'YYYY-MM-DD', or '' if none.

    A date on a line labelled 'Date' / 'Dated' / 'Published' wins. Otherwise
    the first date in the first 1500 characters is used. Dates deep in the
    body are ignored because they usually refer to events, not the document.
    """
    labelled = re.search(
        r"^\s*(?:date|dated|published|issued)\s*[:\-]\s*(.+)$",
        text, re.I | re.M,
    )
    if labelled:
        dates = find_dates(labelled.group(1))
        if dates:
            return dates[0][1].isoformat()

    dates = find_dates(text[:1500])
    return dates[0][1].isoformat() if dates else ""
