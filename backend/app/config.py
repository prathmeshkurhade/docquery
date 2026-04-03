from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Reads from .env file automatically.
    Every field here maps to an env variable (case-insensitive).
    e.g. DATABASE_URL in .env → settings.DATABASE_URL in Python
    """

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ragapp:ragapp123@localhost:5433/ragapp"

    # Vector DB
    QDRANT_URL: str = "http://localhost:6333"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Embedding service (HuggingFace Space)
    EMBEDDING_URL: str = "https://prathmeshkurhade-embedding-api.hf.space"

    # Gemini (LLM only now)
    GEMINI_API_KEY: str = ""

    # Cohere (re-ranking, optional)
    COHERE_API_KEY: str = ""

    # Auth
    JWT_SECRET: str = "change-this-to-a-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours

    model_config = SettingsConfigDict(
        env_file=".env",        # loads from .env file in current directory
        env_file_encoding="utf-8",
        extra="ignore",         # ignore unknown env vars, don't crash
    )


# Single instance — import this everywhere
settings = Settings()
