
from sentence_transformers import SentenceTransformer

# Local embedding model — no API key required.
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_model = None


def _get_model():
    """Load the embedding model only when first needed."""
    global _model

    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")

    return _model


def generate_embedding(
    text: str,
    task_type: str = "RETRIEVAL_DOCUMENT"
) -> list[float]:
    """Convert text into a local numerical embedding."""

    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    model = _get_model()

    embedding = model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()
