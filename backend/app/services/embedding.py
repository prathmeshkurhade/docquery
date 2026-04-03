import logging
import time

import requests

from app.config import settings

logger = logging.getLogger(__name__)

# HuggingFace Space URL — your self-hosted embedding model
EMBEDDING_URL = settings.EMBEDDING_URL
EMBEDDING_DIMENSIONS = 1024  # bge-large-en-v1.5 outputs 1024 dimensions

BATCH_SIZE = 50
MAX_RETRIES = 5


def _embed_batch_with_retry(texts: list[str]) -> list[list[float]]:
    """Call the HuggingFace Space embedding API with retry."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                f"{EMBEDDING_URL}/embed",
                json={"texts": texts},
                timeout=120,  # model can be slow on first call (cold start)
            )
            response.raise_for_status()
            return response.json()["embeddings"]
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = (attempt + 1) * 10
                logger.warning(f"Embedding request failed, retrying in {wait_time}s (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                time.sleep(wait_time)
            else:
                raise Exception(f"Embedding service failed after {MAX_RETRIES} attempts: {e}")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Convert a list of text strings into embedding vectors.
    Calls your self-hosted bge-large-en-v1.5 model on HuggingFace Spaces.
    No rate limits — it's your own server.
    """
    all_embeddings = []
    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        logger.info(f"Embedding batch {batch_num}/{total_batches}: {len(batch)} texts")

        embeddings = _embed_batch_with_retry(batch)
        all_embeddings.extend(embeddings)

    return all_embeddings


def embed_query(query: str) -> list[float]:
    """Embed a single query string. Used during search."""
    embeddings = _embed_batch_with_retry([query])
    return embeddings[0]
