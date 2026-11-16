"""ChromaDB-backed vector store (persistent, local)."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from config import Settings
from core.exceptions import LLMError

logger = logging.getLogger(__name__)
_BATCH = 64  # embedding API calls are batched to stay within provider limits


@dataclass(frozen=True)
class RetrievedChunk:
    document: Document
    score: float  # cosine similarity, 0..1 (higher is better)


class VectorStoreService:
    def __init__(self, settings: Settings, embeddings: Embeddings) -> None:
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        self._store = Chroma(
            collection_name=settings.chroma_collection,
            embedding_function=embeddings,
            persist_directory=str(settings.chroma_dir),
            # Cosine space makes ``1 - distance`` a meaningful similarity.
            collection_metadata={"hnsw:space": "cosine"},
        )

    # -- write ------------------------------------------------------------- #
    def add_chunks(self, chunks: list[Document], doc_id: str) -> None:
        ids = [f"{doc_id}:{c.metadata['chunk_index']}" for c in chunks]
        try:
            for start in range(0, len(chunks), _BATCH):
                self._store.add_documents(
                    chunks[start : start + _BATCH], ids=ids[start : start + _BATCH]
                )
        except Exception as exc:
            logger.exception("Embedding / indexing failed for %s", doc_id)
            self.delete_document(doc_id)  # roll back partial writes
            raise LLMError(
                "Could not create embeddings. Check the embedding provider settings."
            ) from exc

    def delete_document(self, doc_id: str) -> None:
        existing = self._store.get(where={"doc_id": doc_id}, include=[])
        if existing["ids"]:
            self._store.delete(ids=existing["ids"])

    # -- read -------------------------------------------------------------- #
    def search(
        self,
        query: str,
        *,
        k: int,
        document_ids: list[str] | None = None,
        min_score: float = 0.0,
    ) -> list[RetrievedChunk]:
        where = None
        if document_ids:
            where = (
                {"doc_id": document_ids[0]}
                if len(document_ids) == 1
                else {"doc_id": {"$in": document_ids}}
            )
        try:
            results = self._store.similarity_search_with_score(query, k=k, filter=where)
        except Exception as exc:
            logger.exception("Vector search failed")
            raise LLMError("Search failed. Check the embedding provider settings.") from exc

        hits = [RetrievedChunk(doc, 1.0 - float(dist)) for doc, dist in results]
        return [h for h in hits if h.score >= min_score]

    def count(self) -> int:
        return self._store._collection.count()  # noqa: SLF001 - no public API
