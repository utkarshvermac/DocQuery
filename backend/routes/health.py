from fastapi import APIRouter, Depends

from dependencies import Container, get_container
from schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Service health and stats")
def health(c: Container = Depends(get_container)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=c.settings.app_version,
        llm_provider=c.settings.llm_provider,
        embedding_provider=c.settings.embedding_provider,
        documents=len(c.registry.list()),
        chunks=c.vectorstore.count(),
    )
