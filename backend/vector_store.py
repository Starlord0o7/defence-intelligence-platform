
from pathlib import Path

import chromadb
import chromadb.config

from embedding_service import generate_embedding


# Local vector database
DB_PATH = Path(__file__).parent / "chroma_db_local"

# Initial cosine-distance threshold.
# Lower distance means greater similarity.
SIMILARITY_DISTANCE_THRESHOLD = 0.65

_client = None
_collection = None


def _get_collection():
    global _client, _collection

    if _collection is None:
        _client = chromadb.PersistentClient(
            path=str(DB_PATH),
            settings=chromadb.config.Settings(
                anonymized_telemetry=False
            )
        )

        _collection = _client.get_or_create_collection(
            name="intelligence_documents",
            embedding_function=None,
            metadata={"hnsw:space": "cosine"}
        )

    return _collection


def add_chunks(
    document_id: str,
    filename: str,
    chunks: list[str]
) -> int:
    """Generate embeddings and store document chunks."""

    if not chunks:
        raise ValueError("No chunks provided.")

    ids = []
    embeddings = []
    metadatas = []
    valid_chunks = []

    for index, chunk in enumerate(chunks):
        if not chunk.strip():
            continue

        ids.append(f"{document_id}_chunk_{index}")

        embeddings.append(
            generate_embedding(chunk, "RETRIEVAL_DOCUMENT")
        )

        metadatas.append({
            "document_id": document_id,
            "filename": filename,
            "chunk_index": index
        })

        valid_chunks.append(chunk)

    if not valid_chunks:
        raise ValueError("No valid text chunks found.")

    _get_collection().upsert(
        ids=ids,
        embeddings=embeddings,
        documents=valid_chunks,
        metadatas=metadatas
    )

    return len(valid_chunks)


def add_processed_chunks(
    document_id: str,
    records: dict
) -> int:
    """Store processed chunks with their metadata."""

    if not records or not records.get("ids"):
        raise ValueError("No valid text chunks found.")

    embeddings = []

    for text in records["documents"]:
        embeddings.append(
            generate_embedding(text, "RETRIEVAL_DOCUMENT")
        )

    _get_collection().upsert(
        ids=records["ids"],
        embeddings=embeddings,
        documents=records["documents"],
        metadatas=records["metadatas"]
    )

    return len(records["ids"])


def search_similar(
    query: str,
    n_results: int = 3
) -> list[dict]:
    """Retrieve relevant chunks using cosine distance filtering."""

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    collection = _get_collection()
    total_documents = collection.count()

    if total_documents == 0:
        return []

    query_embedding = generate_embedding(
        query,
        "RETRIEVAL_QUERY"
    )

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, total_documents),
        include=["documents", "metadatas", "distances"]
    )

    matches = []

    for index in range(len(results["ids"][0])):
        distance = results["distances"][0][index]

        # Exclude results that are too distant from the query.
        if distance > SIMILARITY_DISTANCE_THRESHOLD:
            continue

        matches.append({
            "text": results["documents"][0][index],
            "metadata": results["metadatas"][0][index],
            "distance": distance
        })

    return matches


def list_documents() -> list[dict]:
    """List uploaded documents and their chunk counts."""

    results = _get_collection().get(
        include=["metadatas"]
    )

    documents = {}

    for metadata in results["metadatas"]:
        document_id = metadata["document_id"]
        filename = metadata["filename"]

        if document_id not in documents:
            documents[document_id] = {
                "document_id": document_id,
                "filename": filename,
                "chunks_stored": 0
            }

        documents[document_id]["chunks_stored"] += 1

    return list(documents.values())
