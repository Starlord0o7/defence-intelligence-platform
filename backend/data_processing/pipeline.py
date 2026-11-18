"""End-to-end processing: file -> cleaned, chunked, labelled records."""
from pathlib import Path

from .categorizer import categorize
from .chunking import chunk_text
from .cleaning import clean_text, remove_repeated_lines
from .extraction import extract_pages
from .metadata import extract_document_date
from .risk import score_text


def process_document(
    file_path: str,
    filename: str | None = None,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> dict:
    """Process a PDF or TXT file.

    Returns:
        {
          "filename": str,
          "date": "YYYY-MM-DD" or "",
          "category": str,                # document level
          "risk": {...},                  # document level (highest chunk)
          "page_count": int,
          "chunks": [
            {"text", "filename", "page", "chunk_index", "date",
             "category", "risk_score", "priority", "matched_keywords"}
          ]
        }
    Page numbers are kept per chunk: chunks never span two pages.
    """
    name = filename or Path(file_path).name

    pages = extract_pages(file_path)
    # Date is read from the raw first page: cleaning joins header lines,
    # which would hide the 'Date:' label.
    doc_date = extract_document_date(pages[0]["text"])
    pages = remove_repeated_lines(pages)
    pages = [{**p, "text": clean_text(p["text"])} for p in pages]
    pages = [p for p in pages if p["text"]]

    if not pages:
        raise ValueError("No readable text left after cleaning.")

    full_text = "\n\n".join(p["text"] for p in pages)

    chunks = []
    for page in pages:
        for text in chunk_text(page["text"], chunk_size, overlap):
            risk = score_text(text)
            chunks.append({
                "text": text,
                "filename": name,
                "page": page["page"],
                "chunk_index": len(chunks),
                "date": doc_date,
                "category": categorize(text)["category"],
                "risk_score": risk["risk_score"],
                "priority": risk["priority"],
                "matched_keywords": risk["matched_keywords"],
            })

    top = max(chunks, key=lambda c: c["risk_score"])
    doc_risk = score_text(full_text)
    doc_risk["risk_score"] = top["risk_score"]
    doc_risk["priority"] = top["priority"]
    doc_risk["reasoning"] = (
        f"Highest chunk score {top['risk_score']}/100 "
        f"(page {top['page']}, chunk {top['chunk_index']})."
    )

    return {
        "filename": name,
        "date": doc_date,
        "category": categorize(full_text)["category"],
        "risk": doc_risk,
        "page_count": len(pages),
        "chunks": chunks,
    }


def to_vector_store_records(result: dict, document_id: str) -> dict:
    """Convert process_document() output to ChromaDB-ready lists.

    ids use the same '<document_id>_chunk_<n>' scheme as vector_store.py.
    Metadata is flat and never None (ChromaDB rejects None), and keeps the
    existing keys (document_id, filename, chunk_index) so rag_service.py
    keeps working. Embeddings are NOT created here; that stays in
    embedding_service.py.
    """
    ids, documents, metadatas = [], [], []
    for c in result["chunks"]:
        ids.append(f"{document_id}_chunk_{c['chunk_index']}")
        documents.append(c["text"])
        metadatas.append({
            "document_id": document_id,
            "filename": c["filename"],
            "chunk_index": c["chunk_index"],
            "page": c["page"],
            "date": c["date"] or "",
            "category": c["category"],
            "risk_score": c["risk_score"],
            "priority": c["priority"],
        })
    return {"ids": ids, "documents": documents, "metadatas": metadatas}
