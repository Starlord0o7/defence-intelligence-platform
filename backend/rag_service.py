
from vector_store import search_similar
from gemini_service import generate_answer


def ask_question(question: str) -> dict:
    """Retrieve relevant information and generate an answer."""

    results = search_similar(question, n_results=3)

    if not results:
        return {
            "question": question,
            "answer": "No relevant documents were found.",
            "sources": []
        }

    context_parts = []
    sources = []
    seen_chunks = set()

    for result in results:
        metadata = result["metadata"]

        filename = metadata["filename"]
        chunk_index = metadata["chunk_index"]

        # Skip duplicate document chunks.
        chunk_id = (filename, chunk_index)

        if chunk_id in seen_chunks:
            continue

        seen_chunks.add(chunk_id)

        page_num = metadata.get("page", 1)

        context_parts.append(
            f"Source: {filename} (Page {page_num})\n"
            f"Content: {result['text']}"
        )

        sources.append({
            "filename": filename,
            "chunk_index": chunk_index,
            "page": page_num,
            "category": metadata.get("category", "General"),
            "date": metadata.get("date", "")
        })

    context = "\n\n".join(context_parts)
    answer = generate_answer(question, context)

    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }
