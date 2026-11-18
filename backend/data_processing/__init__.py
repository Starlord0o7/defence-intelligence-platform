"""Data handling and analysis module (extraction, cleaning, chunking,
metadata, event categorisation, keyword risk scoring).

Standalone: it does not import or modify main.py, vector_store.py or any
other RAG file. Entry point: process_document().
"""
from .pipeline import process_document, to_vector_store_records

__all__ = ["process_document", "to_vector_store_records"]
