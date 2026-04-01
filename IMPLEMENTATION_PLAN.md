# RAG App — Implementation Plan

> Goal: Learn and understand every piece. We go slow, discuss each task before coding it.

---

## Phase 1: Infrastructure & Project Skeleton
*Get the boring setup right first. After this phase you can run all services locally.*

### Task 1.1 — Docker Compose (PostgreSQL + Qdrant + Redis)
- [ ] Write `docker-compose.yml` with 3 services
- [ ] PostgreSQL 16 on port 5432
- [ ] Qdrant on port 6333 (HTTP) + 6334 (gRPC)
- [ ] Redis on port 6379
- [ ] Verify: `docker-compose up -d` and hit Qdrant dashboard at localhost:6333/dashboard
- **Learn:** How docker-compose networks work, why each service needs its own port, what gRPC is and why Qdrant exposes it

### Task 1.2 — Backend Project Setup
- [ ] Create `backend/` folder structure (app/, models/, schemas/, routers/, services/, workers/, utils/)
- [ ] Create `requirements.txt` with all dependencies
- [ ] Create `backend/.env.example` with all required env vars
- [ ] Create `backend/app/config.py` — pydantic-settings to load env vars
- [ ] Create `backend/app/main.py` — bare FastAPI app with `/health` endpoint
- [ ] Verify: `uvicorn app.main:app --reload` returns `{"status": "ok"}` on GET /health
- **Learn:** How pydantic-settings works (BaseSettings, .env loading), why we centralize config instead of reading os.environ everywhere

### Task 1.3 — Database Setup (SQLAlchemy + Alembic)
- [ ] Create `backend/app/database.py` — async SQLAlchemy engine + session factory
- [ ] Install and init Alembic (`alembic init alembic`)
- [ ] Configure `alembic.ini` and `alembic/env.py` to use our async engine
- [ ] Verify: `alembic upgrade head` runs without errors (no tables yet, just connection test)
- **Learn:** What an async engine is (why not sync?), what a session factory does, how Alembic tracks migration versions in a table called `alembic_version`

---

## Phase 2: Auth System (JWT)
*Build auth before anything else — every other endpoint needs to know who's calling it.*

### Task 2.1 — User Model + Migration
- [ ] Create `backend/app/models/user.py` — User model (id, email, hashed_password, created_at)
- [ ] Generate Alembic migration: `alembic revision --autogenerate -m "create users table"`
- [ ] Run migration: `alembic upgrade head`
- [ ] Verify: Table exists in PostgreSQL
- **Learn:** How SQLAlchemy declarative models map to SQL tables, what autogenerate does (reads your models, diffs against DB, writes migration)

### Task 2.2 — Auth Schemas + Service
- [ ] Create `backend/app/schemas/auth.py` — RegisterRequest, LoginRequest, TokenResponse, UserResponse
- [ ] Create `backend/app/services/auth.py` — hash_password, verify_password (bcrypt), create_access_token, decode_token (PyJWT)
- [ ] Verify: Write a quick test — hash a password, verify it matches
- **Learn:** Why we hash (never store plaintext), how bcrypt adds salt automatically, what a JWT payload contains (sub, exp, iat), how signing works (HMAC-SHA256)

### Task 2.3 — Auth Routes + Dependency
- [ ] Create `backend/app/utils/deps.py` — `get_db` (yields async session), `get_current_user` (extracts JWT from Authorization header, decodes, fetches user)
- [ ] Create `backend/app/routers/auth.py` — `POST /auth/register`, `POST /auth/login`
- [ ] Wire router into `main.py`
- [ ] Verify: Register a user via Swagger UI, login, get token, decode it at jwt.io
- **Learn:** How FastAPI Depends() works (dependency injection), what Bearer token means, how the middleware chain works (request → dependency → route handler → response)

---

## Phase 3: Document Upload + Celery Pipeline
*The core of the RAG app — this is where PDFs become searchable knowledge.*

### Task 3.1 — Document Model + Migration
- [ ] Create `backend/app/models/document.py` — Document model (id, user_id FK, filename, status enum [uploading, processing, ready, failed], page_count, chunk_count, created_at)
- [ ] Generate + run Alembic migration
- [ ] Verify: Table exists, FK constraint works
- **Learn:** Why we track status (so frontend can poll), what FK constraints do at the DB level, why enum instead of string for status

### Task 3.2 — File Upload Endpoint
- [ ] Create `backend/app/schemas/document.py` — DocumentResponse, DocumentListResponse
- [ ] Create `backend/app/routers/documents.py` — `POST /documents/upload` (accepts PDF file, saves to local filesystem, creates DB row with status=uploading)
- [ ] Also add `GET /documents/` (list user's documents) and `GET /documents/{id}` (single doc with status)
- [ ] Wire router into `main.py`
- [ ] Verify: Upload a PDF via Swagger UI, see it saved to disk, see DB row
- **Learn:** How FastAPI handles file uploads (UploadFile, SpooledTemporaryFile), why we save first then process (don't block the upload response), what multipart/form-data is

### Task 3.3 — Celery App + Redis Connection
- [ ] Create `backend/app/workers/celery_app.py` — Celery app instance, configure broker (Redis), result backend (Redis)
- [ ] Create a dummy task that just sleeps 5 seconds and logs "done"
- [ ] Run worker: `celery -A app.workers.celery_app worker --loglevel=info`
- [ ] Trigger dummy task from FastAPI endpoint
- [ ] Verify: Task appears in worker logs, completes after 5s
- **Learn:** What a broker is (Redis stores the task message), what a result backend is (where task results go), how `delay()` vs `apply_async()` work, what happens if the worker is down (tasks queue up in Redis)

### Task 3.4 — PDF Text Extraction
- [ ] Create `backend/app/utils/pdf_extractor.py` — Extract text from PDF using PyMuPDF (fitz)
- [ ] Handle: multi-page extraction, page number tracking, basic cleaning (remove excessive whitespace)
- [ ] Verify: Extract text from a sample PDF, print per-page results
- **Learn:** Why PyMuPDF over PyPDF2 (faster, better table handling), what the extraction actually returns (raw text with layout info), why text extraction from PDFs is a hard problem (PDFs store rendering instructions, not structured text)

### Task 3.5 — Text Chunking
- [ ] Create `backend/app/utils/chunker.py` — Chunk text with overlap using langchain's RecursiveCharacterTextSplitter
- [ ] Configure: chunk_size=512 tokens, chunk_overlap=50 tokens
- [ ] Each chunk stores: text, page_number, chunk_index, document_id
- [ ] Verify: Chunk a multi-page document, inspect chunks at boundaries (overlap should repeat text)
- **Learn:** Why we chunk (embeddings have token limits, smaller chunks = more precise retrieval), why overlap (if a sentence is split at the boundary, overlap ensures both chunks have the full context), why recursive splitting (tries paragraph → sentence → word breaks, not arbitrary cuts)

### Task 3.6 — Embedding Service
- [ ] Create `backend/app/services/embedding.py` — Call OpenAI embeddings API, batch chunks (max 2048 per batch)
- [ ] Returns list of (chunk_text, vector) pairs
- [ ] Handle rate limiting with exponential backoff
- [ ] Verify: Embed a few chunks, check vector dimensions = 1536
- **Learn:** What an embedding actually is (a 1536-dimensional point in space where similar meanings are nearby), why `text-embedding-3-small` (good balance of cost/quality), what batching does (1 API call for 100 chunks instead of 100 calls)

### Task 3.7 — Qdrant Storage
- [ ] Create `backend/app/services/vector_store.py` — Create collection (if not exists), upsert points, search
- [ ] Collection config: vector size=1536, distance=Cosine
- [ ] Each point payload: document_id, chunk_index, page_number, text
- [ ] Verify: Upsert some vectors, search from Qdrant dashboard, see results
- **Learn:** What a collection is (like a table but for vectors), what HNSW index is (the data structure that makes approximate nearest neighbor search fast — O(log n) instead of O(n)), what payload is (metadata attached to each vector), why cosine distance (measures angle between vectors, not magnitude)

### Task 3.8 — Full PDF Pipeline (Wire It All Together)
- [ ] Create `backend/app/workers/pdf_pipeline.py` — Celery task that chains: extract → chunk → embed → store in Qdrant → update document status to "ready"
- [ ] Update upload endpoint to trigger this task after file save
- [ ] Handle errors: if any step fails, set document status to "failed" with error message
- [ ] Verify: Upload a PDF, watch worker logs, see chunks appear in Qdrant dashboard, document status goes uploading → processing → ready
- **Learn:** How Celery task error handling works (try/except + status update), why we update status at each step (frontend polling), what happens if worker crashes mid-task (task stays in Redis, gets redelivered)

---

## Phase 4: Query System (Search + Re-rank + Generate)
*Where the magic happens — user asks a question, gets an intelligent answer.*

### Task 4.1 — Vector Search
- [ ] Add search method to `vector_store.py` — Takes query vector, returns top 20 results with scores
- [ ] Create `backend/app/schemas/query.py` — QueryRequest (question, optional document_id filter), QueryResponse (answer, citations)
- [ ] Verify: Embed a question, search Qdrant, see ranked chunks
- **Learn:** How cosine similarity scoring works (1.0 = identical, 0.0 = unrelated), why we fetch 20 and not just 3 (re-ranker will narrow down — casting a wide net first means we don't miss relevant chunks that had low vector similarity)

### Task 4.2 — Cohere Re-Ranking
- [ ] Create `backend/app/services/reranker.py` — Takes query + 20 chunks, calls Cohere Rerank, returns top 3-5
- [ ] Verify: Compare vector search ranking vs re-ranked ranking for same query (they WILL differ — that's the point)
- **Learn:** Why re-ranking exists (bi-encoder vs cross-encoder trade-off), how Cohere scores (0.0 to 1.0 relevance), why this is a separate API call and not part of the vector DB, when re-ranking matters most (ambiguous queries, long documents)

### Task 4.3 — LLM Answer Generation
- [ ] Create `backend/app/services/llm.py` — Takes question + top chunks, calls GPT-4o with a system prompt, returns answer with citations
- [ ] System prompt template: instructs the model to answer ONLY from provided chunks, cite with [page X], say "I don't know" if chunks don't contain the answer
- [ ] Verify: Ask a question about an uploaded PDF, get a cited answer
- **Learn:** What the system prompt does (constrains the LLM to only use provided context — without it, GPT would hallucinate from training data), why we say "I don't know" (RAG without this instruction is dangerous — it'll make up answers), how temperature affects output (0.0 = deterministic, 0.7 = creative)

### Task 4.4 — Query Endpoint (Wire It All Together)
- [ ] Create `backend/app/routers/query.py` — `POST /query/` (authenticated, takes question + optional doc filter)
- [ ] Full flow: embed question → Qdrant search → Cohere re-rank → GPT-4o generate → return response
- [ ] Include timing info in response (search_ms, rerank_ms, generate_ms) for learning
- [ ] Verify: End-to-end test through Swagger UI
- **Learn:** How the full pipeline fits together, where the latency is (generation is slowest), what the response shape looks like

---

## Phase 5: Frontend
*Make it usable. Simple UI — upload page + chat page.*

### Task 5.1 — Next.js Project Setup
- [ ] Create Next.js 14 project with TypeScript + Tailwind CSS
- [ ] Set up API client (axios or fetch wrapper) pointing to localhost:8000
- [ ] Create basic layout (sidebar + main content area)
- [ ] Verify: `npm run dev` shows a blank page with layout

### Task 5.2 — Auth Pages
- [ ] Login page + Register page
- [ ] Store JWT token in localStorage (or httpOnly cookie)
- [ ] Auth context/provider — wrap app, redirect to login if not authenticated
- [ ] Verify: Register → Login → see dashboard

### Task 5.3 — Document Upload Page
- [ ] File upload component (drag-and-drop or file picker, PDF only)
- [ ] Document list showing all uploaded docs with status badges (processing, ready, failed)
- [ ] Poll status every 2 seconds while document is processing
- [ ] Verify: Upload PDF, see status go from processing → ready

### Task 5.4 — Chat / Query Page
- [ ] Chat interface — message input + conversation history
- [ ] Select which document(s) to query against
- [ ] Display answers with formatted citations (clickable page references)
- [ ] Show timing breakdown (search, re-rank, generate)
- [ ] Verify: Ask questions, get cited answers, see the full flow working

---

## Phase 6: Polish & Learn More
*Optional improvements once core is working.*

### Task 6.1 — Streaming Responses
- [ ] Switch GPT-4o call to streaming
- [ ] Use Server-Sent Events (SSE) to stream tokens to frontend
- [ ] Verify: See answer appear word-by-word like ChatGPT
- **Learn:** What SSE is, how streaming differs from polling, why it feels faster (first token appears in ~200ms instead of waiting 3-5s for full response)

### Task 6.2 — Chat History
- [ ] Store conversation history in PostgreSQL
- [ ] Send previous messages as context to GPT-4o (conversation memory)
- [ ] Verify: Follow-up questions work ("What about page 5?" after a previous question)

### Task 6.3 — Multi-Document Query
- [ ] Allow querying across all documents (no filter)
- [ ] Qdrant payload filtering to scope search to specific docs
- [ ] Verify: Upload 3 PDFs, ask a question that spans them

### Task 6.4 — Error Handling & Edge Cases
- [ ] Handle: empty PDFs, scanned PDFs (no text), massive PDFs (>100 pages)
- [ ] Rate limiting on API endpoints
- [ ] Proper error responses with meaningful messages

---

## Dependency Install Order
```
Phase 1: docker, docker-compose
Phase 1: pip install fastapi uvicorn pydantic-settings python-dotenv
Phase 1: pip install sqlalchemy[asyncio] asyncpg alembic
Phase 2: pip install passlib[bcrypt] python-jose[cryptography]
Phase 3: pip install celery[redis] PyMuPDF langchain-text-splitters openai qdrant-client
Phase 4: pip install cohere
Phase 5: npx create-next-app@14 frontend --typescript --tailwind --app
```

---

## How We'll Work
1. I explain what we're about to build and **why**
2. You ask questions until it clicks
3. We write the code together
4. We test it and see it working
5. Move to the next task

**Current status: Ready to start Task 1.1**
