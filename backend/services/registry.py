"""Tiny JSON-file registry of uploaded documents (thread-safe, atomic writes)."""
from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from pathlib import Path

from schemas import DocumentInfo

logger = logging.getLogger(__name__)


class DocumentRegistry:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.RLock()
        self._docs: dict[str, DocumentInfo] = {}
        path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            self._docs = {d["id"]: DocumentInfo(**d) for d in raw}
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.exception("Registry file is corrupted; starting empty")

    def _persist(self) -> None:
        payload = [d.model_dump(mode="json") for d in self._docs.values()]
        fd, tmp = tempfile.mkstemp(dir=self._path.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        os.replace(tmp, self._path)  # atomic on POSIX and Windows

    def add(self, doc: DocumentInfo) -> None:
        with self._lock:
            self._docs[doc.id] = doc
            self._persist()

    def remove(self, doc_id: str) -> DocumentInfo | None:
        with self._lock:
            doc = self._docs.pop(doc_id, None)
            if doc:
                self._persist()
            return doc

    def get(self, doc_id: str) -> DocumentInfo | None:
        with self._lock:
            return self._docs.get(doc_id)

    def find_by_hash(self, sha256: str) -> DocumentInfo | None:
        with self._lock:
            return next((d for d in self._docs.values() if d.sha256 == sha256), None)

    def list(self) -> list[DocumentInfo]:
        with self._lock:
            return sorted(self._docs.values(), key=lambda d: d.uploaded_at, reverse=True)
