---
title: Embedding API
emoji: 🔢
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---

# Embedding API

FastAPI service running `BAAI/bge-large-en-v1.5` for text embeddings.

## Endpoints

- `POST /embed` — embed a list of texts
- `GET /health` — health check
