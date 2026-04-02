import logging
import time

from google import genai

from app.config import settings

logger = logging.getLogger(__name__)

# Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 3072

# Rate limit: 100 requests/minute on free tier
# We add delays between batches and retry on 429
BATCH_SIZE = 50  # smaller batches = less likely to hit limit
DELAY_BETWEEN_BATCHES = 2  # seconds between batches
MAX_RETRIES = 5


def _embed_batch_with_retry(batch: list[str]) -> list:
    """Embed a single batch with automatic retry on rate limit."""
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
            )
            return response.embeddings
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_time = (attempt + 1) * 15  # 15s, 30s, 45s, 60s, 75s
                logger.warning(f"Rate limited, waiting {wait_time}s (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries exceeded for embedding batch")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Convert a list of text strings into embedding vectors using Gemini.
    Handles rate limiting with automatic retry and delays between batches.
    """
    all_embeddings = []

    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        logger.info(f"Embedding batch {batch_num}/{total_batches}: {len(batch)} texts")

        embeddings = _embed_batch_with_retry(batch)
        all_embeddings.extend(embeddings)

        # Delay between batches to avoid hitting rate limit
        if i + BATCH_SIZE < len(texts):
            time.sleep(DELAY_BETWEEN_BATCHES)

    return [emb.values for emb in all_embeddings]


def embed_query(query: str) -> list[float]:
    """Embed a single query string. Used during search."""
    embeddings = _embed_batch_with_retry([query])
    return embeddings[0].values
