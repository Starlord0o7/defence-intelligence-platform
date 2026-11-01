from pathlib import Path

import chromadb

from embedding_service import generate_embedding


# Store the database inside the backend folder
DB_PATH = Path(__file__).parent / "chroma_db"

client = chromadb.PersistentClient(path=str(DB_PATH))

collection = client.get_or_create_collection(
    name="intelligence_documents",
    metadata={"hnsw:space": "cosine"}
)


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

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=valid_chunks,
        metadatas=metadatas
    )

    return len(valid_chunks)


def search_similar(query: str, n_results: int = 3) -> list[dict]:
    """Find document chunks relevant to a question."""

    if not query.strip():
        raise ValueError("Search query cannot be empty.")

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
        matches.append({
            "text": results["documents"][0][index],
            "metadata": results["metadatas"][0][index],
            "distance": results["distances"][0][index]
        })

    return matches

