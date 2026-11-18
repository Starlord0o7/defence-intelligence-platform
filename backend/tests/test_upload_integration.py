
"""
Integration tests for the /documents/upload endpoint.

These tests use local document processing and mocked ChromaDB storage.
No Gemini API key or paid service is required.
"""

import asyncio
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi import UploadFile
from starlette.datastructures import Headers

import pytest
import main as _main


SAMPLE_DOC = (
    Path(__file__).resolve().parents[1]
    / "sample_documents"
    / "test_report.txt"
)

DEMO_PDF = (
    Path(__file__).resolve().parents[1]
    / "sample_documents"
    / "demo_intel_briefing.pdf"
)


def _make_upload_file(path: Path, content_type: str):
    """Build an UploadFile from a real sample file."""

    data = path.read_bytes()

    return UploadFile(
        filename=path.name,
        file=io.BytesIO(data),
        headers=Headers({"content-type": content_type}),
    )


# Shared mock ChromaDB collection.
_mock_col = MagicMock()
_mock_col.upsert.return_value = None
_mock_col.count.return_value = 0
_mock_col.query.return_value = {
    "ids": [[]],
    "documents": [[]],
    "metadatas": [[]],
    "distances": [[]],
}
_mock_col.get.return_value = {
    "ids": [],
    "metadatas": [],
}


def test_upload_txt_returns_threat_assessment():
    """Check TXT upload and threat assessment metadata."""

    upload = _make_upload_file(SAMPLE_DOC, "text/plain")

    with (
        patch("vector_store._get_collection", return_value=_mock_col),
        patch("vector_store.generate_embedding", return_value=[0.1] * 384),
    ):
        data = asyncio.run(_main.upload_document(file=upload))

    assert data["filename"] == "test_report.txt"
    assert data["date"] == "2026-10-15"
    assert data["page_count"] == 1
    assert "threat_assessment" in data
    assert data["threat_assessment"]["priority"] in {
        "High", "Medium", "Low"
    }
    assert data["chunks_stored"] > 0


def test_upload_demo_pdf_returns_enriched_metadata():
    """Check PDF upload, page count, and threat metadata."""

    upload = _make_upload_file(DEMO_PDF, "application/pdf")

    with (
        patch("vector_store._get_collection", return_value=_mock_col),
        patch("vector_store.generate_embedding", return_value=[0.1] * 384),
    ):
        data = asyncio.run(_main.upload_document(file=upload))

    assert data["filename"] == "demo_intel_briefing.pdf"
    assert data["date"] == "2026-10-15"
    assert data["page_count"] == 3
    assert data["threat_assessment"]["priority"] == "High"
    assert "casualt" in data["threat_assessment"]["negated_keywords"]
    assert data["chunks_stored"] == 3
