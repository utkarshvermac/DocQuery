"""Document parsing: PDF, DOCX and TXT -> normalised text units.

Each parser returns :class:`ParsedPage` objects that keep the best available
location info (page number for PDFs, nearest heading for DOCX) so citations
can point users to the right place later on.
"""
from __future__ import annotations

import logging
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from core.exceptions import (
    DocQueryError,
    DocumentParseError,
    EmptyDocumentError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedPage:
    text: str
    page: int | None = None      # 1-based page number (PDF)
    section: str | None = None   # nearest heading (DOCX)


@dataclass(frozen=True)
class ParsedDocument:
    pages: list[ParsedPage]
    page_count: int | None       # None for formats without pages


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
_HYPHEN_BREAK = re.compile(r"(?<=[a-z])-\n(?=[a-z])")
_MULTI_NEWLINE = re.compile(r"\n{3,}")
_MULTI_SPACE = re.compile(r"[ \t\u00a0]{2,}")


def _normalise(text: str) -> str:
    """Clean extraction artefacts without destroying paragraph structure."""
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    text = _HYPHEN_BREAK.sub("", text)
    text = _MULTI_SPACE.sub(" ", text)
    text = _MULTI_NEWLINE.sub("\n\n", text)
    return text.strip()


def _verify_signature(path: Path, ext: str) -> None:
    """Reject files whose content does not match their extension."""
    with path.open("rb") as fh:
        head = fh.read(8192)
    if ext == ".pdf" and b"%PDF" not in head[:1024]:
        raise DocumentParseError("This file is not a valid PDF.")
    if ext == ".docx" and not zipfile.is_zipfile(path):
        raise DocumentParseError("This file is not a valid DOCX document.")
    if ext == ".txt" and b"\x00" in head:
        raise DocumentParseError("This file looks binary, not plain text.")


# --------------------------------------------------------------------------- #
# Format-specific parsers
# --------------------------------------------------------------------------- #
def _parse_pdf(path: Path) -> ParsedDocument:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    if reader.is_encrypted and not reader.decrypt(""):
        raise DocumentParseError("This PDF is password-protected.")

    pages: list[ParsedPage] = []
    for number, page in enumerate(reader.pages, start=1):
        text = _normalise(page.extract_text() or "")
        if text:
            pages.append(ParsedPage(text=text, page=number))
    return ParsedDocument(pages=pages, page_count=len(reader.pages))


def _parse_docx(path: Path) -> ParsedDocument:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    document = Document(str(path))
    sections: list[ParsedPage] = []
    heading: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        text = _normalise("\n".join(buffer))
        if text:
            sections.append(ParsedPage(text=text, section=heading))
        buffer.clear()

    for block in document.iter_inner_content():
        if isinstance(block, Paragraph):
            style = (block.style.name if block.style is not None else "") or ""
            if style.startswith(("Heading", "Title")) and block.text.strip():
                flush()
                heading = block.text.strip()[:120]
            if block.text.strip():
                buffer.append(block.text)
        elif isinstance(block, Table):
            for row in block.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    buffer.append(" | ".join(cells))
    flush()
    return ParsedDocument(pages=sections, page_count=None)


def _parse_txt(path: Path) -> ParsedDocument:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")  # never fails; best-effort fallback
    text = _normalise(text)
    return ParsedDocument(pages=[ParsedPage(text=text)] if text else [], page_count=None)


_PARSERS = {".pdf": _parse_pdf, ".docx": _parse_docx, ".txt": _parse_txt}


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def parse_document(path: Path) -> ParsedDocument:
    """Parse ``path`` and return its text. Raises ``DocQueryError`` subclasses."""
    ext = path.suffix.lower()
    parser = _PARSERS.get(ext)
    if parser is None:
        raise UnsupportedFileTypeError(f"Unsupported file type '{ext}'.")

    _verify_signature(path, ext)
    try:
        parsed = parser(path)
    except DocQueryError:
        raise
    except Exception as exc:  # third-party parsers raise many exception types
        logger.exception("Failed to parse %s", path.name)
        raise DocumentParseError(
            "The file could not be read. It may be corrupted."
        ) from exc

    if not parsed.pages:
        raise EmptyDocumentError(
            "No readable text was found. Scanned documents need OCR first."
        )
    return parsed
