from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, documents, query

app = FastAPI(
    title="RAG App API",
    description="Upload PDFs, ask questions, get cited answers",
    version="0.1.0",
)

# Allow frontend to call this API (local + production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://65.0.185.51",
        "http://docuchatop.duckdns.org",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(query.router)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "database_url_configured": bool(settings.DATABASE_URL),
        "qdrant_url": settings.QDRANT_URL,
    }
