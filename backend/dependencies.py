"""Application container + FastAPI dependency accessors."""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from config import Settings
from services.ingestion import IngestionService
from services.rag_chain import RAGService
from services.registry import DocumentRegistry
from services.sessions import SessionStore
from services.vectorstore import VectorStoreService


@dataclass
class Container:
    settings: Settings
    vectorstore: VectorStoreService
    registry: DocumentRegistry
    ingestion: IngestionService
    sessions: SessionStore
    rag: RAGService


def get_container(request: Request) -> Container:
    return request.app.state.container
