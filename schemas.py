"""Pydantic request / response models - the public API contract."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_type: str
    size_bytes: int
    page_count: int | None = None
    chunk_count: int
    sha256: str
    uploaded_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]
    total: int


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, max_length=64)
    document_ids: list[str] | None = Field(
        default=None, description="Restrict retrieval to these documents. Omit for all."
    )

    @field_validator("question")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question must not be blank")
        return v


class SourceCitation(BaseModel):
    index: int = Field(..., description="Number used in the answer text, e.g. [1]")
    document_id: str
    filename: str
    page: int | None = None
    section: str | None = None
    chunk_index: int
    snippet: str
    score: float = Field(..., description="Cosine similarity, 0..1")


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceCitation]
    latency_ms: int


class SessionResponse(BaseModel):
    session_id: str


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_provider: str
    embedding_provider: str
    documents: int
    chunks: int


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = {}


class ErrorResponse(BaseModel):
    error: ErrorBody
