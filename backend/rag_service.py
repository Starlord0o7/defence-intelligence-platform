from vector_store import search_similar
from gemini_service import generate_answer


def ask_question(question: str) -> dict:
    """Retrieve relevant information and generate an answer."""

    results = search_similar(question, n_results=3)

    if not results:
        return {
            "answer": "No relevant documents were found.",
            "sources": []
        }

    context_parts = []
    sources = []

    for result in results:
        metadata = result["metadata"]

        context_parts.append(
            f"Source: {metadata['filename']}\n"
            f"Content: {result['text']}"
        )

        sources.append({
            "filename": metadata["filename"],
            "chunk_index": metadata["chunk_index"]
        })

    context = "\n\n".join(context_parts)

    answer = generate_answer(question, context)

    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }

