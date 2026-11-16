"""Upload -> validate -> parse -> chunk -> embed -> register pipeline."""
from __future__ import annotations

import hashlib
import logging
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

from config import Settings
from core.exceptions import (
    DocumentNotFoundError,
    DuplicateDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from schemas import DocumentInfo
from services.chunking import Chunker
from services.parsing import parse_document
from services.registry import DocumentRegistry
from services.vectorstore import VectorStoreService

logger = logging.getLogger(__name__)
_READ_BLOCK = 1024 * 1024


class IngestionService:
    def __init__(
        self,
        settings: Settings,
        vectorstore: VectorStoreService,
        registry: DocumentRegistry,
    ) -> None:
        self._settings = settings
        self._vectorstore = vectorstore
        self._registry = registry
        self._chunker = Chunker(settings.chunk_size, settings.chunk_overlap)

    def ingest(self, filename: str, fileobj: BinaryIO) -> DocumentInfo:
        safe_name = Path(filename or "").name  # strips any path traversal
        ext = Path(safe_name).suffix.lower()
        if ext not in self._settings.allowed_extensions:
            allowed = ", ".join(self._settings.allowed_extensions)
            raise UnsupportedFileTypeError(f"'{ext or 'unknown'}' files are not supported. Use {allowed}.")

        with tempfile.TemporaryDirectory(prefix="docquery_") as tmp:
            path = Path(tmp) / f"upload{ext}"
            size, digest = self._spool(fileobj, path)

            if (dup := self._registry.find_by_hash(digest)) is not None:
                raise DuplicateDocumentError(
                    f"'{dup.filename}' has already been uploaded.",
                    details={"document_id": dup.id},
                )

            parsed = parse_document(path)
            doc_id = uuid.uuid4().hex
            chunks = self._chunker.split(parsed, doc_id=doc_id, filename=safe_name)
            self._vectorstore.add_chunks(chunks, doc_id)

            info = DocumentInfo(
                id=doc_id,
                filename=safe_name,
                file_type=ext.lstrip("."),
                size_bytes=size,
                page_count=parsed.page_count,
                chunk_count=len(chunks),
                sha256=digest,
                uploaded_at=datetime.now(timezone.utc),
            )
            self._registry.add(info)
            logger.info("Ingested %s (%d chunks)", safe_name, len(chunks))
            return info

    def delete(self, doc_id: str) -> None:
        if self._registry.get(doc_id) is None:
            raise DocumentNotFoundError("Document not found.")
        self._vectorstore.delete_document(doc_id)
        self._registry.remove(doc_id)

    def _spool(self, fileobj: BinaryIO, dest: Path) -> tuple[int, str]:
        """Stream to disk while enforcing the size limit and hashing."""
        sha, size = hashlib.sha256(), 0
        with dest.open("wb") as out:
            while block := fileobj.read(_READ_BLOCK):
                size += len(block)
                if size > self._settings.max_upload_bytes:
                    raise FileTooLargeError(
                        f"File exceeds the {self._settings.max_upload_mb} MB limit."
                    )
                sha.update(block)
                out.write(block)
        if size == 0:
            raise UnsupportedFileTypeError("The uploaded file is empty.")
        return size, sha.hexdigest()
