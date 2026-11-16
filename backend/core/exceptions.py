"""Domain exceptions.

Every error raised deliberately by the application derives from
:class:`DocQueryError` and carries an HTTP status plus a stable machine-readable
``code`` so the frontend can react precisely. A single handler in ``main.py``
converts them into a uniform JSON envelope.
"""
from __future__ import annotations

from typing import Any


class DocQueryError(Exception):
    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class UnsupportedFileTypeError(DocQueryError):
    status_code, code = 415, "unsupported_file_type"


class FileTooLargeError(DocQueryError):
    status_code, code = 413, "file_too_large"


class DocumentParseError(DocQueryError):
    status_code, code = 422, "document_parse_failed"


class EmptyDocumentError(DocQueryError):
    status_code, code = 422, "document_empty"


class DuplicateDocumentError(DocQueryError):
    status_code, code = 409, "document_duplicate"


class DocumentNotFoundError(DocQueryError):
    status_code, code = 404, "document_not_found"


class NoDocumentsError(DocQueryError):
    status_code, code = 409, "no_documents"


class ConfigurationError(DocQueryError):
    status_code, code = 500, "configuration_error"


class LLMError(DocQueryError):
    status_code, code = 502, "llm_unavailable"
