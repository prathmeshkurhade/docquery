from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="RAG App API",
    description="Upload PDFs, ask questions, get cited answers",
    version="0.1.0",
)

# Allow Next.js frontend (localhost:3000) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "database_url_configured": bool(settings.DATABASE_URL),
        "qdrant_url": settings.QDRANT_URL,
    }
