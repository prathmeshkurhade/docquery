import logging

import cohere

from app.config import settings

logger = logging.getLogger(__name__)

# Cohere client
co = cohere.Client(api_key=settings.COHERE_API_KEY)


def rerank_chunks(query: str, chunks: list[dict], top_n: int = 5) -> list[dict]:
    """
    Re-rank chunks using Cohere's cross-encoder.

    Input:
    - query: the user's question
    - chunks: list of dicts from vector search (each has "text", "page_number", "score", etc.)
    - top_n: how many to keep after re-ranking

    What happens:
    1. Vector search gave us 20 chunks ranked by cosine similarity (rough ranking)
    2. Cohere's cross-encoder reads EACH chunk alongside the query (sees them together)
    3. It scores each pair: "how relevant is this chunk to this specific question?"
    4. We return the top 5 by relevance score

    Why this matters:
    - Vector search might rank "safety regulations overview" above "helmets are required"
      for the query "what safety gear is needed?"
    - Cross-encoder understands the question-chunk relationship and fixes this
    """
    if not chunks:
        return []

    # Extract just the text for Cohere
    documents = [chunk["text"] for chunk in chunks]

    response = co.rerank(
        query=query,
        documents=documents,
        top_n=top_n,
        model="rerank-v3.5",
    )

    # Build reranked results — keep all original metadata
    reranked = []
    for result in response.results:
        chunk = chunks[result.index].copy()
        chunk["rerank_score"] = result.relevance_score  # 0.0 to 1.0
        reranked.append(chunk)

    logger.info(
        f"Re-ranked {len(chunks)} chunks → top {len(reranked)} "
        f"(scores: {[round(r['rerank_score'], 3) for r in reranked]})"
    )

    return reranked
