"""
System Router: Health checks, telemetry, and system configuration endpoints.
"""

from fastapi import APIRouter, Depends
from api.config import Settings
from api.dependencies import get_settings, get_crew_service, get_document_service
from api.services.crew_service import CrewService
from api.services.document_service import DocumentService
from api.schemas.system import HealthResponse, StatusResponse

router = APIRouter(tags=["System & Health"])


@router.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns the health status, active session count, and knowledge base document count.",
)
async def health_endpoint(
    settings: Settings = Depends(get_settings),
    crew_service: CrewService = Depends(get_crew_service),
    doc_service: DocumentService = Depends(get_document_service),
) -> HealthResponse:
    docs = doc_service.list_documents()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        model_configured=crew_service.is_configured(),
        active_sessions=crew_service.session_count(),
        total_documents=len(docs),
    )


@router.get(
    "/api/status",
    response_model=StatusResponse,
    summary="System and Model Configuration Status",
    description="Returns metadata about the active LLM, knowledge directory, and server state.",
)
async def status_endpoint(
    settings: Settings = Depends(get_settings),
    crew_service: CrewService = Depends(get_crew_service),
) -> StatusResponse:
    return StatusResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        model=crew_service.get_active_model(),
        knowledge_dir=str(settings.knowledge_dir.resolve()),
        active_sessions=crew_service.session_count(),
    )
