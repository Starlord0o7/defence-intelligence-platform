"""Text cleaning that keeps paragraph structure for the chunker."""
import re
import unicodedata
from collections import Counter

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_PAGE_NUMBER_LINE = re.compile(
    r"^\s*(page\s+)?\d+(\s*(of|/)\s*\d+)?\s*$", re.IGNORECASE
)
_LIGATURES = {"\ufb01": "fi", "\ufb02": "fl", "\ufb00": "ff",
              "\ufb03": "ffi", "\ufb04": "ffl"}


def remove_repeated_lines(pages: list[dict], min_pages: int = 3) -> list[dict]:
    """Drop headers/footers: short lines that repeat on at least half the
    pages. Only applied to documents with `min_pages` or more pages, so a
    legitimate repeated line in a short document is never removed."""
    if len(pages) < min_pages:
        return pages

    counts = Counter()
    for page in pages:
        lines = {_norm_line(l) for l in page["text"].splitlines()}
        counts.update(l for l in lines if l and len(l) <= 80)

    threshold = max(2, len(pages) // 2)
    repeated = {line for line, n in counts.items() if n >= threshold}

    cleaned = []
    for page in pages:
        kept = [l for l in page["text"].splitlines()
                if _norm_line(l) not in repeated]
        cleaned.append({**page, "text": "\n".join(kept)})
    return cleaned


def _norm_line(line: str) -> str:
    # Digits are masked so "Report - Page 3" and "Report - Page 4" match.
    return re.sub(r"\d+", "#", line.strip().lower())


def clean_text(text: str) -> str:
    """Normalise one page of text.

    - fixes ligatures and control characters
    - re-joins words split by a hyphen at a line end
    - joins single line breaks inside a paragraph
    - keeps blank-line paragraph breaks
    - removes bare page-number lines and collapses extra whitespace
    """
    text = unicodedata.normalize("NFC", text)
    for bad, good in _LIGATURES.items():
        text = text.replace(bad, good)
    text = _CONTROL.sub(" ", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")

    lines = [l for l in text.split("\n") if not _PAGE_NUMBER_LINE.match(l)]
    text = "\n".join(lines)

    # "trans-\nport" -> "transport" (only lower-case continuation)
    text = re.sub(r"(\w)-\n(?=[a-z])", r"\1", text)

    paragraphs = re.split(r"\n\s*\n", text)
    cleaned = []
    for para in paragraphs:
        para = re.sub(r"\s*\n\s*", " ", para)
        para = re.sub(r"[ \t]{2,}", " ", para).strip()
        if para:
            cleaned.append(para)

    return "\n\n".join(cleaned)
