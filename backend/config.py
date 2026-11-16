"""Centralised, validated application configuration.

All tunables come from environment variables (or a local ``.env`` file) so the
same code runs unchanged in development, CI and production (12-factor style).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Application -------------------------------------------------------
    app_name: str = "DocQuery API"
    app_version: str = "1.0.0"
    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"  # comma-separated

    # --- Providers ---------------------------------------------------------
    llm_provider: Literal["openai", "ollama"] = "openai"
    embedding_provider: Literal["openai", "ollama", "huggingface"] = "openai"

    openai_api_key: SecretStr | None = None
    openai_base_url: str | None = None
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.1"
    ollama_embedding_model: str = "nomic-embed-text"

    hf_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    llm_temperature: float = 0.1
    llm_timeout_seconds: int = 60

    # --- RAG tuning --------------------------------------------------------
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_top_k: int = 5
    min_relevance_score: float = 0.1  # cosine similarity floor, 0..1

    # --- Limits ------------------------------------------------------------
    max_upload_mb: int = 25
    allowed_extensions: tuple[str, ...] = (".pdf", ".txt", ".docx")
    session_ttl_minutes: int = 120
    max_sessions: int = 1000
    max_history_turns: int = 6

    # --- Storage -----------------------------------------------------------
    data_dir: Path = BASE_DIR / "data"
    chroma_collection: str = "docquery"

    # ----------------------------------------------------------------------
    @model_validator(mode="after")
    def _check_consistency(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        if not 1 <= self.retrieval_top_k <= 20:
            raise ValueError("RETRIEVAL_TOP_K must be between 1 and 20")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def registry_path(self) -> Path:
        return self.data_dir / "documents.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
