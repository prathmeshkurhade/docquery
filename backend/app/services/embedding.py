import logging

from google import genai

from app.config import settings

logger = logging.getLogger(__name__)

# Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Model: text-embedding-004
# - 768 dimensions (smaller than OpenAI's 1536, but still good)
# - Free tier: 1500 requests/day
# - Good quality embeddings for semantic search
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 3072


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Convert a list of text strings into embedding vectors using Gemini.

    Input:  ["chunk 1 text", "chunk 2 text", ...]
    Output: [[0.023, -0.041, ...], [0.019, -0.038, ...], ...]

    Batching: Gemini accepts up to 100 texts per request.
    """
    all_embeddings = []
    batch_size = 100

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        logger.info(f"Embedding batch {i // batch_size + 1}: {len(batch)} texts")

        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch,
        )

        all_embeddings.extend(response.embeddings)

    # Extract the vector values from each embedding object
    return [emb.values for emb in all_embeddings]


def embed_query(query: str) -> list[float]:
    """
    Embed a single query string. Used during search.
    """
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=query,
    )
    return response.embeddings[0].values
