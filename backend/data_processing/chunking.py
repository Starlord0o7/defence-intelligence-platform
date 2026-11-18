"""Paragraph and sentence aware chunking."""
import re

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


def split_sentences(paragraph: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_END.split(paragraph) if s.strip()]


def chunk_text(
    text: str,
    max_chars: int = 1000,
    overlap_chars: int = 150,
) -> list[str]:
    """Split cleaned text into chunks of at most `max_chars` characters
    (a single sentence longer than the limit is hard-split).

    Chunks end on sentence boundaries. The tail of each chunk (whole
    sentences, up to `overlap_chars`) is repeated at the start of the next
    one so context is not lost at the boundary.
    """
    if max_chars <= 0 or overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("Invalid chunk size or overlap.")

    sentences = []
    for paragraph in text.split("\n\n"):
        sentences.extend(split_sentences(paragraph))

    units = []
    for sentence in sentences:
        while len(sentence) > max_chars:  # very long unbroken text
            cut = sentence.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            units.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if sentence:
            units.append(sentence)

    chunks = []
    current: list[str] = []
    length = 0

    for unit in units:
        added = len(unit) + (1 if current else 0)
        if current and length + added > max_chars:
            chunks.append(" ".join(current))
            current = _overlap_tail(current, overlap_chars, len(unit), max_chars)
            length = len(" ".join(current))
            added = len(unit) + (1 if current else 0)
        current.append(unit)
        length += added

    if current:
        last = " ".join(current)
        # Avoid emitting a chunk that only repeats the previous overlap.
        if not chunks or last not in chunks[-1]:
            chunks.append(last)

    return chunks


def _overlap_tail(sentences, overlap_chars, next_len, max_chars):
    tail, size = [], 0
    for sentence in reversed(sentences):
        if size + len(sentence) > overlap_chars:
            break
        tail.insert(0, sentence)
        size += len(sentence) + 1
    # Never let the overlap push the next sentence over the limit.
    while tail and size + next_len + 1 > max_chars:
        size -= len(tail.pop(0)) + 1
    return tail
