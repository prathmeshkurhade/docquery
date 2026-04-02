import uuid

from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    document_id: uuid.UUID | None = None  # optional: filter to specific doc


class Citation(BaseModel):
    text: str
    page_number: int
    score: float  # rerank relevance score


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    timing: dict  # search_ms, rerank_ms, generate_ms — for learning
