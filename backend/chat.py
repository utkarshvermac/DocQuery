import time

from fastapi import APIRouter, Depends, Response, status

from core.exceptions import DocumentNotFoundError, NoDocumentsError
from dependencies import Container, get_container
from schemas import ChatRequest, ChatResponse, SessionResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse, summary="Ask a question about your documents")
def chat(body: ChatRequest, c: Container = Depends(get_container)) -> ChatResponse:
    if not c.registry.list():
        raise NoDocumentsError("Upload at least one document before asking questions.")
    for doc_id in body.document_ids or []:
        if c.registry.get(doc_id) is None:
            raise DocumentNotFoundError(f"Document '{doc_id}' does not exist.")

    session_id = body.session_id or c.sessions.create()
    started = time.perf_counter()
    result = c.rag.ask(body.question, session_id, body.document_ids)
    return ChatResponse(
        session_id=session_id,
        answer=result.answer,
        sources=result.sources,
        latency_ms=int((time.perf_counter() - started) * 1000),
    )


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new conversation",
)
def create_session(c: Container = Depends(get_container)) -> SessionResponse:
    return SessionResponse(session_id=c.sessions.create())


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear a conversation's memory",
)
def delete_session(session_id: str, c: Container = Depends(get_container)) -> Response:
    c.sessions.delete(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
