"""Smart chunking with overlap and rich metadata."""
from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from services.parsing import ParsedDocument


class Chunker:
    """Splits parsed pages into overlapping chunks.

    ``RecursiveCharacterTextSplitter`` tries paragraph breaks first, then
    lines, sentences and words, so chunks end on natural boundaries. The
    overlap keeps context that straddles a boundary retrievable from both sides.
    """

    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""],
            add_start_index=True,
        )

    def split(self, parsed: ParsedDocument, *, doc_id: str, filename: str) -> list[Document]:
        chunks: list[Document] = []
        for page in parsed.pages:
            # ChromaDB rejects ``None`` metadata values, so only set known keys.
            base: dict = {"doc_id": doc_id, "source": filename}
            if page.page is not None:
                base["page"] = page.page
            if page.section:
                base["section"] = page.section
            chunks.extend(self._splitter.create_documents([page.text], metadatas=[base]))

        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = index
        return chunks
