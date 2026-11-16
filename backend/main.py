"""DocQuery API entry point.

Run:  uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from core.exceptions import DocQueryError
from core.logging_config import configure_logging
from dependencies import Container
from routes import chat, documents, health
from services.ingestion import IngestionService
from services.llm_factory import build_chat_model, build_embeddings
from services.rag_chain import RAGService
from services.registry import DocumentRegistry
from services.sessions import SessionStore
from services.vectorstore import VectorStoreService

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("docquery")


def _build_container() -> Container:
    """Wire up all services once at startup (simple dependency injection)."""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    vectorstore = VectorStoreService(settings, build_embeddings(settings))
    registry = DocumentRegistry(settings.registry_path)
    sessions = SessionStore(
        settings.session_ttl_minutes, settings.max_sessions, settings.max_history_turns
    )
    return Container(
        settings=settings,
        vectorstore=vectorstore,
        registry=registry,
        ingestion=IngestionService(settings, vectorstore, registry),
        sessions=sessions,
        rag=RAGService(build_chat_model(settings), vectorstore, sessions, settings),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = _build_container()
    logger.info(
        "DocQuery ready | llm=%s embeddings=%s", settings.llm_provider, settings.embedding_provider
    )
    yield


def _error(status: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": details or {}}},
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Retrieval-Augmented Generation API for document question answering.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_log(request: Request, call_next):
        request_id, started = uuid.uuid4().hex[:8], time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "%s %s -> %s (%d ms) [%s]",
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter() - started) * 1000,
            request_id,
        )
        return response

    @app.exception_handler(DocQueryError)
    async def domain_error(_: Request, exc: DocQueryError):
        return _error(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(p) for p in first.get("loc", [])[1:]) or "request"
        return _error(422, "validation_error", f"Invalid {field}: {first.get('msg', 'bad input')}")

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception):
        logger.exception("Unhandled error")
        return _error(500, "internal_error", "Something went wrong on the server.")

    api_prefix = "/api/v1"
    app.include_router(health.router, prefix=api_prefix)
    app.include_router(documents.router, prefix=api_prefix)
    app.include_router(chat.router, prefix=api_prefix)
    return app


app = create_app()
