from fastapi import APIRouter, Depends, File, Response, UploadFile, status

from dependencies import Container, get_container
from schemas import DocumentInfo, DocumentListResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "",
    response_model=DocumentInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index a PDF, TXT or DOCX file",
)
def upload_document(
    file: UploadFile = File(...), c: Container = Depends(get_container)
) -> DocumentInfo:
    # Sync endpoint => FastAPI runs it in a worker thread, so slow parsing and
    # embedding calls never block the event loop.
    return c.ingestion.ingest(file.filename or "", file.file)


@router.get("", response_model=DocumentListResponse, summary="List indexed documents")
def list_documents(c: Container = Depends(get_container)) -> DocumentListResponse:
    docs = c.registry.list()
    return DocumentListResponse(documents=docs, total=len(docs))


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document and its vectors",
)
def delete_document(document_id: str, c: Container = Depends(get_container)) -> Response:
    c.ingestion.delete(document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
