from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

app = FastAPI(title="Embedding API")

# Load model on startup — downloads once, cached after
model = SentenceTransformer("BAAI/bge-large-en-v1.5")

DIMENSIONS = 1024


class EmbedRequest(BaseModel):
    texts: list[str]


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]
    dimensions: int


@app.post("/embed", response_model=EmbedResponse)
def embed(request: EmbedRequest):
    """Embed a list of texts. Returns list of 1024-dim vectors."""
    # bge models recommend prepending "Represent this sentence: " for better results
    # but for retrieval, raw text works fine
    embeddings = model.encode(request.texts, normalize_embeddings=True)
    return EmbedResponse(
        embeddings=embeddings.tolist(),
        dimensions=DIMENSIONS,
    )


@app.get("/health")
def health():
    return {"status": "ok", "model": "BAAI/bge-large-en-v1.5", "dimensions": DIMENSIONS}
