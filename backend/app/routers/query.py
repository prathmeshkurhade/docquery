import time

from fastapi import APIRouter, Depends

from app.models.user import User
from app.schemas.query import Citation, QueryRequest, QueryResponse
from app.services.embedding import embed_query
from app.services.reranker import rerank_chunks
from app.services.vector_store import search_chunks
from app.services.llm import generate_answer
from app.utils.deps import get_current_user

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    user: User = Depends(get_current_user),
):
    """
    Ask a question about uploaded documents.

    Full RAG pipeline:
    1. Embed the question → vector
    2. Search Qdrant → top 20 similar chunks
    3. Re-rank with Cohere → top 5 most relevant
    4. Generate answer with Gemini → cited response

    Timing info is included so you can see where the latency is.
    """
    # Step 1: Embed the question
    t0 = time.time()
    query_vector = embed_query(request.question)

    # Step 2: Vector search (always scoped to current user)
    doc_filter = str(request.document_id) if request.document_id else None
    raw_results = search_chunks(query_vector, user_id=str(user.id), document_id=doc_filter, top_k=20)
    search_ms = round((time.time() - t0) * 1000)

    if not raw_results:
        return QueryResponse(
            answer="No relevant content found in the documents.",
            citations=[],
            timing={"search_ms": search_ms, "rerank_ms": 0, "generate_ms": 0},
        )

    # Step 3: Re-rank
    t1 = time.time()
    reranked = rerank_chunks(request.question, raw_results, top_n=5)
    rerank_ms = round((time.time() - t1) * 1000)

    # Step 4: Generate answer
    t2 = time.time()
    answer = generate_answer(request.question, reranked)
    generate_ms = round((time.time() - t2) * 1000)

    # Build citations — only include chunks with meaningful relevance
    # Scores below 0.15 are essentially noise
    citations = [
        Citation(
            text=chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
            page_number=chunk["page_number"],
            score=round(chunk["rerank_score"], 3),
        )
        for chunk in reranked
        if chunk["rerank_score"] > 0.15
    ]

    return QueryResponse(
        answer=answer,
        citations=citations,
        timing={
            "search_ms": search_ms,
            "rerank_ms": rerank_ms,
            "generate_ms": generate_ms,
        },
    )
