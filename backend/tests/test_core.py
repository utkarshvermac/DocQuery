"""Fast unit tests that need no API keys or network."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from core.exceptions import EmptyDocumentError, UnsupportedFileTypeError
from services.chunking import Chunker
from services.parsing import ParsedDocument, ParsedPage, parse_document
from services.rag_chain import RAGService
from services.sessions import SessionStore


def test_chunker_keeps_metadata_and_overlap():
    text = " ".join(f"Sentence number {i}." for i in range(200))
    parsed = ParsedDocument([ParsedPage(text, page=3)], page_count=3)
    chunks = Chunker(200, 50).split(parsed, doc_id="d1", filename="a.pdf")
    assert len(chunks) > 3
    assert all(c.metadata["page"] == 3 and c.metadata["source"] == "a.pdf" for c in chunks)
    assert [c.metadata["chunk_index"] for c in chunks] == list(range(len(chunks)))
    assert all(len(c.page_content) <= 200 for c in chunks)


def test_txt_parsing_and_empty_rejection(tmp_path):
    ok = tmp_path / "n.txt"
    ok.write_text("Hello world", encoding="utf-8")
    assert parse_document(ok).pages[0].text == "Hello world"
    blank = tmp_path / "b.txt"
    blank.write_text("   \n  ", encoding="utf-8")
    with pytest.raises(EmptyDocumentError):
        parse_document(blank)


def test_unsupported_extension(tmp_path):
    f = tmp_path / "x.png"
    f.write_bytes(b"abc")
    with pytest.raises(UnsupportedFileTypeError):
        parse_document(f)


def test_session_history_is_bounded():
    store = SessionStore(ttl_minutes=5, max_sessions=10, max_turns=2)
    sid = store.create()
    for i in range(5):
        store.append_turn(sid, f"q{i}", f"a{i}")
    history = store.get_history(sid)
    assert len(history) == 4 and history[0].content == "q3"


def test_citation_selection_prefers_cited_sources():
    from schemas import SourceCitation

    mk = lambda i: SourceCitation(index=i, document_id="d", filename="f", chunk_index=i, snippet="s", score=0.5)
    cites = [mk(1), mk(2), mk(3)]
    assert [c.index for c in RAGService._select_cited("Yes [2].", cites)] == [2]
    assert len(RAGService._select_cited("No markers", cites)) == 3
