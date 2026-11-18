"""Page-aware text extraction for PDF and TXT files."""
from pathlib import Path

import pymupdf

SUPPORTED_EXTENSIONS = {".pdf", ".txt"}


def extract_pages(file_path: str) -> list[dict]:
    """Return [{"page": 1, "text": "..."}, ...] (page numbers start at 1).

    PDF: one entry per page, so page numbers are real.
    TXT: one entry per form-feed separated section; a normal file is page 1.
    Pages with no readable text are skipped (e.g. scanned images).
    """
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Only PDF and TXT files are supported.")

    pages = []

    if extension == ".pdf":
        with pymupdf.open(path) as document:
            for number, page in enumerate(document, start=1):
                pages.append({"page": number, "text": page.get_text()})
    else:
        raw = _read_text_file(path)
        for number, section in enumerate(raw.split("\f"), start=1):
            pages.append({"page": number, "text": section})

    pages = [p for p in pages if p["text"].strip()]

    if not pages:
        raise ValueError(
            "No readable text found in the document. "
            "Scanned PDFs need OCR, which is not supported yet."
        )

    return pages


def _read_text_file(path: Path) -> str:
    """Read a TXT file, tolerating a BOM and non-UTF-8 encodings."""
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")
