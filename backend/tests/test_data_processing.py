import sys
from pathlib import Path

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_processing import process_document, to_vector_store_records
from data_processing.categorizer import categorize
from data_processing.chunking import chunk_text
from data_processing.cleaning import clean_text, remove_repeated_lines
from data_processing.extraction import extract_pages
from data_processing.metadata import extract_document_date
from data_processing.risk import score_text

SAMPLE = Path(__file__).resolve().parents[1] / "sample_documents" / "test_report.txt"


def make_pdf(path, pages):
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        page.insert_textbox(pymupdf.Rect(50, 50, 550, 780), text, fontsize=11)
    doc.save(str(path))
    doc.close()


# extraction
def test_txt_is_single_page(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("Hello world.", encoding="utf-8")
    assert extract_pages(str(f)) == [{"page": 1, "text": "Hello world."}]


def test_pdf_keeps_real_page_numbers(tmp_path):
    f = tmp_path / "a.pdf"
    make_pdf(f, ["First page text.", "Second page text.", "Third page text."])
    assert [p["page"] for p in extract_pages(str(f))] == [1, 2, 3]


def test_blank_pdf_page_is_skipped_but_numbers_stay(tmp_path):
    f = tmp_path / "a.pdf"
    make_pdf(f, ["Page one text.", "", "Page three text."])
    assert [p["page"] for p in extract_pages(str(f))] == [1, 3]


def test_unsupported_and_empty_files(tmp_path):
    bad = tmp_path / "a.docx"
    bad.write_text("x")
    with pytest.raises(ValueError):
        extract_pages(str(bad))
    empty = tmp_path / "e.txt"
    empty.write_text("   \n ")
    with pytest.raises(ValueError):
        extract_pages(str(empty))


# cleaning
def test_clean_fixes_hyphen_breaks_and_joins_lines():
    out = clean_text("Road trans-\nport was  closed\nin the north.\n\nNew para.")
    assert out == "Road transport was closed in the north.\n\nNew para."


def test_clean_removes_page_number_lines():
    assert clean_text("Text here.\n12\nPage 3 of 9\nMore.") == "Text here. More."


def test_repeated_header_removed_only_for_long_docs():
    pages = [{"page": i, "text": f"CONFIDENTIAL HEADER\nBody {i}.\nPage {i}"}
             for i in range(1, 5)]
    out = remove_repeated_lines(pages)
    assert all("CONFIDENTIAL" not in p["text"] for p in out)
    short = pages[:2]
    assert remove_repeated_lines(short) == short


# chunking
def test_chunks_respect_limit_and_end_on_sentences():
    text = " ".join(f"Sentence number {i} is here." for i in range(80))
    chunks = chunk_text(text, max_chars=300, overlap_chars=60)
    assert len(chunks) > 1
    assert all(len(c) <= 300 for c in chunks)
    assert all(c.endswith(".") for c in chunks)


def test_chunks_overlap_and_cover_everything():
    sentences = [f"Fact {i} stated clearly." for i in range(60)]
    chunks = chunk_text(" ".join(sentences), max_chars=200, overlap_chars=50)
    joined = " ".join(chunks)
    assert all(s in joined for s in sentences)
    assert any(chunks[0].split(". ")[-1][:6] in c for c in chunks[1:2])


def test_long_unbroken_text_is_hard_split():
    chunks = chunk_text("word " * 500, max_chars=100, overlap_chars=10)
    assert all(len(c) <= 100 for c in chunks)


def test_invalid_chunk_settings():
    with pytest.raises(ValueError):
        chunk_text("abc", max_chars=10, overlap_chars=10)


# metadata
@pytest.mark.parametrize("text,expected", [
    ("Date: 15 October 2026\nBody", "2026-10-15"),
    ("Published: October 5, 2026", "2026-10-05"),
    ("Issued 2026-03-09 by office", "2026-03-09"),
    ("Dated: 15/10/2026", "2026-10-15"),
    ("No date here at all.", ""),
    ("Date: 31/02/2026", ""),
])
def test_date_extraction(text, expected):
    assert extract_document_date(text) == expected


def test_labelled_date_beats_earlier_date():
    text = "Event on 1 January 2020 was reviewed.\nDate: 15 October 2026"
    assert extract_document_date(text) == "2026-10-15"


# categorisation
def test_categories():
    assert categorize("Heavy rainfall and a cyclone hit the coast")["category"] == "Weather"
    assert categorize("Troops and missile launchers deployed")["category"] == "Military Activity"
    assert categorize("Ransomware and phishing campaign")["category"] == "Cyber"
    assert categorize("Nothing relevant here")["category"] == "General"


# risk
def test_negation_is_ignored():
    r = score_text("There were no casualties and no attack on the border post.")
    assert "casualt" not in r["matched_keywords"]
    assert "attack" not in r["matched_keywords"]
    assert "casualt" in r["negated_keywords"]


def test_repeat_bonus_is_capped():
    one = score_text("An explosion occurred.")["risk_score"]
    many = score_text("explosion " * 10)["risk_score"]
    assert many == one + 10


def test_calming_words_reduce_score_and_clamp_at_zero():
    assert score_text("Everything is normal and stable.")["risk_score"] == 0


def test_score_in_range():
    r = score_text("attack missile troop explosion breach infiltrat casualt")
    assert r["risk_score"] == 100 and r["priority"] == "High"


# pipeline
def test_sample_txt_end_to_end():
    r = process_document(str(SAMPLE))
    assert r["filename"] == "test_report.txt"
    assert r["date"] == "2026-10-15"
    c = r["chunks"][0]
    assert {"text", "filename", "page", "chunk_index", "date"} <= set(c)
    assert c["page"] == 1


def test_multi_page_pdf_chunks_keep_page_numbers(tmp_path):
    f = tmp_path / "r.pdf"
    make_pdf(f, ["Date: 15 October 2026. Troops moved near the border.",
                 "Routine patrol. Situation normal.",
                 "Flood warning issued for the valley."])
    r = process_document(str(f))
    assert r["date"] == "2026-10-15"
    assert sorted({c["page"] for c in r["chunks"]}) == [1, 2, 3]
    assert [c["chunk_index"] for c in r["chunks"]] == list(range(len(r["chunks"])))
    assert r["chunks"][0]["priority"] in {"Medium", "High"}


def test_vector_store_records_are_flat_and_aligned():
    r = process_document(str(SAMPLE))
    rec = to_vector_store_records(r, "doc1")
    assert len(rec["ids"]) == len(rec["documents"]) == len(rec["metadatas"])
    assert rec["ids"][0] == "doc1_chunk_0"
    for m in rec["metadatas"]:
        assert all(v is not None and isinstance(v, (str, int, float, bool))
                   for v in m.values())
        assert {"document_id", "filename", "chunk_index", "page"} <= set(m)


def test_demo_intel_briefing_pdf_end_to_end():
    demo_pdf = Path(__file__).resolve().parents[1] / "sample_documents" / "demo_intel_briefing.pdf"
    r = process_document(str(demo_pdf))
    assert r["filename"] == "demo_intel_briefing.pdf"
    assert r["date"] == "2026-10-15"
    assert r["page_count"] == 3
    assert r["risk"]["priority"] == "High"
    assert "troop" in r["risk"]["matched_keywords"]
    assert "casualt" in r["risk"]["negated_keywords"]
    assert len(r["chunks"]) == 3
    assert [c["page"] for c in r["chunks"]] == [1, 2, 3]
