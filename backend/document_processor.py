from pathlib import Path
import pymupdf


def extract_text(file_path: str) -> str:
    """Extract text from PDF or TXT files."""

    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".pdf":
        text_parts = []

        with pymupdf.open(path) as document:
            for page in document:
                text_parts.append(page.get_text())

        text = "\n".join(text_parts)

    elif extension == ".txt":
        text = path.read_text(encoding="utf-8")

    else:
        raise ValueError("Only PDF and TXT files are supported.")

    text = text.strip()

    if not text:
        raise ValueError("No readable text found in the document.")

    return text


def split_into_chunks(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200
) -> list[str]:
    """Split text into overlapping chunks."""

    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Invalid chunk size or overlap.")

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks

