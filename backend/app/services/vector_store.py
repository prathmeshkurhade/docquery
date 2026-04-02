import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.config import settings
from app.services.embedding import EMBEDDING_DIMENSIONS

logger = logging.getLogger(__name__)

# Qdrant client — connects to localhost:6333
client = QdrantClient(url=settings.QDRANT_URL)

# Collection name — like a "table" in Qdrant
COLLECTION_NAME = "document_chunks"


def ensure_collection():
    """
    Create the collection if it doesn't exist.

    Collection config:
    - vector size = 1536 (matches OpenAI embedding dimensions)
    - distance = Cosine (measures angle between vectors, not magnitude)
      Cosine similarity: 1.0 = identical meaning, 0.0 = completely unrelated

    This is idempotent — safe to call multiple times.
    """
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)

    if not exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSIONS,
                distance=Distance.COSINE,
            ),
        )
        logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")


def store_chunks(
    document_id: str,
    chunks: list[dict],
    embeddings: list[list[float]],
):
    """
    Store chunk embeddings in Qdrant.

    Each "point" in Qdrant has:
    - id: unique UUID
    - vector: the 1536-dim embedding
    - payload: metadata (document_id, text, page_number, chunk_index)

    Payload is searchable — we can filter by document_id later
    to only search within a specific document.
    """
    ensure_collection()

    points = []
    for chunk, embedding in zip(chunks, embeddings):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "document_id": document_id,
                "text": chunk["text"],
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
            },
        )
        points.append(point)

    # Upsert in batches of 100 (Qdrant handles large batches fine,
    # but batching is good practice)
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch,
        )

    logger.info(f"Stored {len(points)} chunks in Qdrant for document {document_id}")


def search_chunks(
    query_embedding: list[float],
    document_id: str | None = None,
    top_k: int = 20,
) -> list[dict]:
    """
    Search for similar chunks using a query embedding.

    Returns top_k most similar chunks, optionally filtered to a specific document.

    Each result contains:
    - text: the chunk text
    - page_number: which page it came from
    - score: cosine similarity (0.0 to 1.0)
    - document_id: which document it belongs to
    """
    ensure_collection()

    # Optional filter: only search within a specific document
    search_filter = None
    if document_id:
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=search_filter,
        limit=top_k,
    )

    return [
        {
            "text": point.payload["text"],
            "page_number": point.payload["page_number"],
            "chunk_index": point.payload["chunk_index"],
            "document_id": point.payload["document_id"],
            "score": point.score,
        }
        for point in results.points
    ]


def delete_document_chunks(document_id: str):
    """Delete all chunks for a document from Qdrant."""
    ensure_collection()

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        ),
    )

    logger.info(f"Deleted chunks from Qdrant for document {document_id}")
