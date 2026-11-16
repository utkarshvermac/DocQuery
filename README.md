# DocQuery

**Ask questions about your documents and get answers with page-level citations.**
DocQuery is a full-stack Retrieval-Augmented Generation (RAG) application: upload PDF, DOCX or TXT files, and a language model answers strictly from their content, showing exactly which passages each claim came from.

| | |
|---|---|
| **Backend** | FastAPI, LangChain, ChromaDB, pypdf, python-docx |
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS |
| **Models** | OpenAI by default; Ollama (fully local) or Hugging Face embeddings via configuration |

---

## Architecture

```
                         ┌───────────────────────────────┐
                         │        Next.js Frontend        │
                         │  Sidebar (upload, scope)       │
                         │  Chat UI (markdown, citations) │
                         └───────────────┬───────────────┘
                                         │ REST / JSON  (/api/v1)
┌────────────────────────────────────────▼─────────────────────────────────────────┐
│                                  FastAPI Backend                                  │
│                                                                                   │
│   routes/documents ─► IngestionService          routes/chat ─► RAGService          │
│                        │                                        │                 │
│        validate ► parse (pypdf / python-docx / txt)             │                 │
│                        ▼                                        ▼                 │
│            Chunker (RecursiveCharacterTextSplitter)    1. Condense follow-up      │
│            size 1000 / overlap 200 + metadata             (uses session history)  │
│                        │                                2. Retrieve top-k         │
│                        ▼                                3. Generate with [n]     │
│               VectorStoreService  ◄─────────────────────   citations              │
│               (ChromaDB, cosine)                         4. Map [n] ► sources     │
│                        ▲                                        │                 │
│   DocumentRegistry (JSON)        SessionStore (TTL, bounded)    │                 │
└────────────────────────┼────────────────────────────────────────┼─────────────────┘
                         │                                        │
              Embedding provider                           Chat model provider
         (OpenAI | Ollama | Hugging Face)                   (OpenAI | Ollama)
```

**Request lifecycle for a question**

1. The frontend posts `{question, session_id, document_ids}` to `/chat`.
2. If the session has history, the question is rewritten as a standalone query (so "what about its cost?" works).
3. ChromaDB returns the top-k most similar chunks, filtered to the selected documents and a minimum similarity.
4. The LLM receives numbered excerpts and must cite them as `[1]`, `[2]`...
5. The API returns the answer plus a `sources` array (file, page or section, snippet, score). The UI turns each `[n]` into a clickable highlight that scrolls to its source card.

---

## Features

- **Multi-format ingestion**: PDF (per-page), DOCX (headings and tables), TXT (UTF-8 with fallback)
- **Smart chunking**: recursive splitting on paragraph, line, sentence then word boundaries, with overlap
- **Rich metadata**: file name, page number, DOCX section heading, chunk index
- **Cited answers**: inline `[n]` markers linked to the exact passage, document and page
- **Conversational memory**: follow-up questions resolved through query condensing; sessions expire and are bounded
- **Document scoping**: tick or untick documents to control what is searched
- **Duplicate detection** (SHA-256), size limits, file-signature checks, atomic registry writes
- **Robust errors**: typed domain exceptions, uniform JSON error envelope, rollback of partial indexing
- **Provider-agnostic**: swap OpenAI, Ollama or Hugging Face in `.env`, no code changes
- **Accessible UI**: keyboard navigation, focus states, ARIA live regions, reduced-motion support, mobile drawer layout

---

## Project structure

```
docquery/
├── README.md
├── backend/
│   ├── main.py                # App factory, middleware, error handlers, DI wiring
│   ├── config.py              # Typed settings from environment
│   ├── schemas.py             # Pydantic request / response models
│   ├── dependencies.py        # Service container for FastAPI
│   ├── requirements.txt
│   ├── .env.example
│   ├── core/                  # exceptions.py, logging_config.py
│   ├── routes/                # health.py, documents.py, chat.py
│   ├── services/
│   │   ├── parsing.py         # PDF / DOCX / TXT -> text units
│   │   ├── chunking.py        # Splitter + metadata
│   │   ├── llm_factory.py     # Chat model and embeddings per provider
│   │   ├── vectorstore.py     # ChromaDB wrapper
│   │   ├── registry.py        # Uploaded-document catalogue
│   │   ├── ingestion.py       # Upload pipeline orchestration
│   │   ├── sessions.py        # Conversation memory
│   │   └── rag_chain.py       # Condense -> retrieve -> generate -> cite
│   └── tests/test_core.py
└── frontend/
    ├── app/                   # layout.tsx, page.tsx, globals.css
    ├── components/            # Sidebar, UploadZone, DocumentList, ChatWindow,
    │                          # MessageBubble, CitationCard, ChatInput
    ├── hooks/                 # useDocuments.ts, useChat.ts
    ├── lib/                   # api.ts (client), types.ts, utils.ts
    └── package.json
```

---

## Setup

**Prerequisites:** Python 3.10+, Node.js 18.17+, and an OpenAI API key (or Ollama installed locally).

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # then edit .env and set OPENAI_API_KEY
uvicorn main:app --reload --port 8000
```

API docs (Swagger UI): <http://localhost:8000/docs>

### 2. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # points to http://localhost:8000/api/v1
npm run dev
```

Open <http://localhost:3000>.

### 3. Running fully offline with Ollama (optional)

```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

In `backend/.env` set `LLM_PROVIDER=ollama` and `EMBEDDING_PROVIDER=ollama`.
> Embeddings are tied to the model that created them. If you change the embedding provider or model, delete `backend/data/` and re-upload your documents.

### 4. Tests

```bash
cd backend && pytest -q
```

---

## Environment variables (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai` or `ollama` |
| `EMBEDDING_PROVIDER` | `openai` | `openai`, `ollama` or `huggingface` |
| `OPENAI_API_KEY` | none | Required when using OpenAI |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Chat model name |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1000` / `200` | Characters per chunk / shared between neighbours |
| `RETRIEVAL_TOP_K` | `5` | Chunks passed to the LLM (1 to 20) |
| `MIN_RELEVANCE_SCORE` | `0.1` | Similarity floor (0 to 1); raise to be stricter |
| `MAX_UPLOAD_MB` | `25` | Per-file upload limit |
| `SESSION_TTL_MINUTES` | `120` | Idle time before a conversation is forgotten |
| `MAX_HISTORY_TURNS` | `6` | Question/answer pairs kept as context |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |

Frontend (`frontend/.env.local`): `NEXT_PUBLIC_API_URL`, default `http://localhost:8000/api/v1`.

---

## API reference

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Status, providers, document and chunk counts |
| `POST` | `/documents` | Upload one file (`multipart/form-data`, field `file`) |
| `GET` | `/documents` | List indexed documents |
| `DELETE` | `/documents/{id}` | Remove a document and its vectors |
| `POST` | `/chat` | Ask a question |
| `POST` | `/sessions` | Create a conversation |
| `DELETE` | `/sessions/{id}` | Clear a conversation's memory |

**Upload**

```bash
curl -F "file=@report.pdf" http://localhost:8000/api/v1/documents
```
```json
{ "id": "9f2c...", "filename": "report.pdf", "file_type": "pdf", "size_bytes": 482113,
  "page_count": 24, "chunk_count": 61, "sha256": "...", "uploaded_at": "2026-11-16T09:12:44Z" }
```

**Chat**

```bash
curl -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" \
  -d '{"question": "What were the main findings?", "session_id": null, "document_ids": null}'
```
```json
{
  "session_id": "b71e...",
  "answer": "The study found a 12% improvement in retention [1], driven mainly by onboarding changes [2].",
  "sources": [
    { "index": 1, "document_id": "9f2c...", "filename": "report.pdf", "page": 7, "section": null,
      "chunk_index": 18, "snippet": "Retention improved by 12% ...", "score": 0.612 }
  ],
  "latency_ms": 1840
}
```
Pass the returned `session_id` on later calls to ask follow-ups. `document_ids` limits retrieval to specific documents.

**Errors** use one envelope everywhere:

```json
{ "error": { "code": "file_too_large", "message": "File exceeds the 25 MB limit.", "details": {} } }
```

| HTTP | `code` | Meaning |
|---|---|---|
| 409 | `document_duplicate` | Identical file already uploaded |
| 409 | `no_documents` | Chat requested before any upload |
| 404 | `document_not_found` | Unknown document id |
| 413 | `file_too_large` | Over `MAX_UPLOAD_MB` |
| 415 | `unsupported_file_type` | Not PDF, DOCX or TXT (or empty) |
| 422 | `document_parse_failed` / `document_empty` / `validation_error` | Corrupt, scanned or invalid input |
| 502 | `llm_unavailable` | Model or embedding provider failed |

---

## Design decisions (for your evaluation)

- **Chunk size 1000 / overlap 200**: large enough to hold a full idea, small enough for precise retrieval; overlap prevents answers being cut at boundaries.
- **Cosine similarity**: Chroma is configured with `hnsw:space = cosine`, so `1 - distance` is an interpretable 0..1 score.
- **Query condensing**: follow-ups like "and the cost?" would retrieve poorly as-is; rewriting them with history fixes that.
- **Grounded prompting**: the model must refuse when excerpts lack the answer, must cite, and treats excerpt text as untrusted (basic prompt-injection resistance).
- **Layered services**: routes contain no business logic; services depend on abstractions (`Embeddings`, `BaseChatModel`), so providers and stores are swappable.
- **Sync endpoints**: parsing and embedding are blocking, so FastAPI runs them in worker threads and the event loop stays responsive.

## Limitations and future work

- Scanned PDFs need OCR (for example Tesseract) before upload.
- Sessions are in-memory; replace `SessionStore` with Redis for multi-process deployments.
- No authentication yet; add per-user collections and JWT before exposing publicly.
- Possible upgrades: streaming responses (SSE), hybrid BM25 + vector search, a re-ranker, evaluation with RAGAS.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Backend exits with "OPENAI_API_KEY is not set" | Add the key to `backend/.env`, or switch both providers to `ollama` |
| "Can't reach the DocQuery server" in the UI | Confirm uvicorn is running on port 8000 and `NEXT_PUBLIC_API_URL` is correct |
| Browser CORS error | Add your frontend origin to `CORS_ORIGINS` |
| "No readable text was found" | The PDF is scanned images; run OCR first |
| Odd results after changing embedding model | Delete `backend/data/` and re-upload |
