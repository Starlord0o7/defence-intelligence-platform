from google import genai
from google.genai import types

from gemini_service import api_key

client = genai.Client(api_key=api_key)

EMBEDDING_MODEL = "gemini-embedding-001"


def generate_embedding(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    """Convert text into a numerical vector using Gemini."""

    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type
        ),
    )

    return response.embeddings[0].values

