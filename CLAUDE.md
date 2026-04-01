# RAG Application

## What This Is
A Retrieval-Augmented Generation (RAG) application where users upload PDFs, ask questions in natural language, and get accurate answers with citations pointing back to the exact source. Built for **learning** — understanding every architectural decision, not just shipping code.

## Tech Stack
- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** Next.js 14 (TypeScript, Tailwind CSS)
- **Task Queue:** Celery + Redis (async PDF processing)
- **Metadata DB:** PostgreSQL (local Docker — user data, documents, auth)
- **Vector DB:** Qdrant (local Docker — embeddings + semantic search)
- **Embeddings:** OpenAI `text-embedding-3-small` (1536 dimensions)
- **Re-Ranker:** Cohere Rerank API (cross-encoder for relevance scoring)
- **LLM:** OpenAI GPT-4o (answer generation with citations)
- **Auth:** JWT-based (self-built)
- **File Storage:** Local filesystem (dev)

## Architecture Overview
```
User → Next.js Frontend → FastAPI API
                              │
                    ┌─────────┼──────────────┐
                    │         │              │
                PostgreSQL   Redis         Local FS
                (metadata)   (broker)      (PDFs)
                    │         │
                    │    Celery Worker
                    │    (PDF processing pipeline)
                    │         │
                    │    ┌────┴─────────────────────┐
                    │    │ 1. Extract text (PyMuPDF) │
                    │    │ 2. Chunk (overlapping)    │
                    │    │ 3. Embed (OpenAI)         │
                    │    │ 4. Store → Qdrant         │
                    │    └──────────────────────────-┘
                    │
              Query Flow:
              Question → Embed → Qdrant Search (top 20)
                      → Cohere Re-rank (top 3-5)
                      → GPT-4o (generate answer + citations)
```

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
│   ├── Dockerfile
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
├── docker-compose.yml           # PostgreSQL, Qdrant, Redis
├── CLAUDE.md                    # This file
└── IMPLEMENTATION_PLAN.md       # Detailed build plan with tasks
```

## Key Architectural Decisions
1. **Qdrant over pgvector** — Purpose-built vector DB; teaches vector DB concepts (collections, points, payloads, HNSW), has a dashboard UI at localhost:6333, skills transfer to Pinecone/Weaviate/Milvus
2. **PostgreSQL separate from vectors** — Clean separation: PG handles relational data (users, documents, metadata), Qdrant handles vectors. Each does what it's best at
3. **Celery + Redis over in-process** — PDF processing is CPU-heavy; without a queue, concurrent uploads block the API. Celery runs workers as separate processes
4. **Cohere Re-rank after vector search** — Vector search (bi-encoder) encodes query and chunks independently. Re-ranker (cross-encoder) sees them together, catches semantic nuance cosine similarity misses
5. **Separate services layer** — Routers stay thin (HTTP concerns only), services contain business logic, makes testing easier
6. **Everything local via Docker** — No cloud dependencies during dev. docker-compose runs PG, Qdrant, Redis

## Commands
```bash
# Infrastructure (PostgreSQL, Qdrant, Redis)
docker-compose up -d

# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Celery worker
cd backend && celery -A app.workers.celery_app worker --loglevel=info

# Frontend
cd frontend && npm install && npm run dev

# Database migrations
cd backend && alembic upgrade head

# Qdrant dashboard
# Open http://localhost:6333/dashboard in browser
```

## Environment Variables
See `backend/.env.example` and `frontend/.env.example` for required keys:
- `OPENAI_API_KEY` — embeddings + LLM
- `COHERE_API_KEY` — re-ranking
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `QDRANT_URL` — Qdrant connection string (default: http://localhost:6333)
- `JWT_SECRET` — token signing key
