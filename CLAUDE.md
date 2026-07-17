# RAG Application

## What This Is
A Retrieval-Augmented Generation (RAG) application where users upload PDFs, ask questions in natural language, and get accurate answers with citations pointing back to the exact source. Built for **learning** — understanding every architectural decision, not just shipping code.

## Tech Stack
- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** Next.js 14 (TypeScript, Tailwind CSS)
- **Task Queue:** Celery + Redis (async PDF processing) — broker hosted on Upstash
- **Metadata DB:** PostgreSQL — hosted on Supabase (via Supavisor session pooler)
- **Vector DB:** Qdrant — hosted on Qdrant Cloud (embeddings + semantic search)
- **Embeddings:** Self-hosted `bge-large-en-v1.5` on a HuggingFace Space (1024 dimensions)
- **Re-Ranker:** Cohere Rerank API (cross-encoder for relevance scoring)
- **LLM:** Google Gemini 2.5 Flash (answer generation with citations)
- **Auth:** JWT-based (self-built)
- **File Storage:** Local filesystem (dev)

## Architecture Overview
```
User → Next.js Frontend → FastAPI API
                              │
                    ┌─────────┼──────────────┐
                    │         │              │
              Supabase     Upstash        Local FS
             (Postgres)    (Redis)         (PDFs)
                    │         │
                    │    Celery Worker
                    │    (PDF processing pipeline)
                    │         │
                    │    ┌────┴──────────────────────────┐
                    │    │ 1. Extract text (PyMuPDF)      │
                    │    │ 2. Chunk (overlapping)         │
                    │    │ 3. Embed (bge-large on HF)     │
                    │    │ 4. Store → Qdrant Cloud        │
                    │    └───────────────────────────────-┘
                    │
              Query Flow:
              Question → Embed (bge-large) → Qdrant Cloud Search (top 20)
                      → Cohere Re-rank (top 3-5)
                      → Gemini 2.5 Flash (generate answer + citations)
```

Everything except local file storage is now a hosted free-tier service — nothing runs
locally besides `uvicorn`, the Celery worker, and `npm run dev`. Docker was removed
entirely (see git history) after repeated local Windows/Docker Desktop issues.

## Project Structure
```
ragapp/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── database.py          # SQLAlchemy async engine setup
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   └── document.py
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   │   ├── auth.py
│   │   │   ├── document.py
│   │   │   └── query.py
│   │   ├── routers/             # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── documents.py
│   │   │   └── query.py
│   │   ├── services/            # Business logic layer
│   │   │   ├── auth.py
│   │   │   ├── document.py
│   │   │   ├── embedding.py
│   │   │   ├── reranker.py
│   │   │   └── llm.py
│   │   ├── workers/             # Celery tasks
│   │   │   ├── celery_app.py
│   │   │   └── pdf_pipeline.py
│   │   └── utils/               # Shared helpers
│   │       ├── pdf_extractor.py
│   │       ├── chunker.py
│   │       └── deps.py          # FastAPI dependencies (get_db, get_current_user)
│   ├── alembic/                 # Database migrations
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js app router pages
│   │   ├── components/          # React components
│   │   ├── lib/                 # API client, auth helpers
│   │   └── types/               # TypeScript types
│   ├── package.json
│   ├── tailwind.config.ts
│   └── .env.example
├── CLAUDE.md                    # This file
└── IMPLEMENTATION_PLAN.md       # Detailed build plan with tasks
```

## Key Architectural Decisions
1. **Qdrant over pgvector** — Purpose-built vector DB; teaches vector DB concepts (collections, points, payloads, HNSW), skills transfer to Pinecone/Weaviate/Milvus
2. **PostgreSQL separate from vectors** — Clean separation: PG handles relational data (users, documents, metadata), Qdrant handles vectors. Each does what it's best at
3. **Celery + Redis over in-process** — PDF processing is CPU-heavy; without a queue, concurrent uploads block the API. Celery runs workers as separate processes
4. **Cohere Re-rank after vector search** — Vector search (bi-encoder) encodes query and chunks independently. Re-ranker (cross-encoder) sees them together, catches semantic nuance cosine similarity misses
5. **Separate services layer** — Routers stay thin (HTTP concerns only), services contain business logic, makes testing easier
6. **Everything hosted on free tiers, nothing local** — Supabase (Postgres), Upstash (Redis), Qdrant Cloud (vectors). Originally ran via Docker Compose locally; switched to hosted services after repeated Docker Desktop/Windows issues made local dev unreliable

## Commands
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Celery worker (must use --pool=solo on Windows — prefork/billiard is broken there)
cd backend && celery -A app.workers.celery_app worker --loglevel=info --pool=solo

# Frontend
cd frontend && npm install && npm run dev

# Database migrations
cd backend && alembic upgrade head
```

## Environment Variables
See `backend/.env.example` for required keys:
- `DATABASE_URL` — Supabase Postgres connection string (use the session pooler host, not `db.*.supabase.co` directly — that hostname is IPv6-only and fails to resolve on most networks)
- `REDIS_URL` — Upstash Redis connection string (`rediss://...`, TLS required)
- `QDRANT_URL` / `QDRANT_API_KEY` — Qdrant Cloud cluster URL + API key
- `EMBEDDING_URL` — HuggingFace Space URL for the self-hosted bge-large embedding model
- `GEMINI_API_KEY` — LLM answer generation
- `COHERE_API_KEY` — re-ranking
- `JWT_SECRET` — token signing key
