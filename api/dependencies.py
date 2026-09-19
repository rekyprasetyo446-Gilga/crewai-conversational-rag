"""
FastAPI dependency injection providers.
"""

from functools import lru_cache
from api.config import Settings, settings
from api.services.crew_service import CrewService
from api.services.document_service import DocumentService
from api.services.ai_service import AIService


@lru_cache()
def get_settings() -> Settings:
    """Provides application settings instance."""
    return settings


# Singleton instances for services across request lifecycle
_crew_service = CrewService(verbose=True)
_document_service = DocumentService(knowledge_dir=settings.knowledge_dir)
_ai_service = AIService(knowledge_dir=settings.knowledge_dir)


def get_crew_service() -> CrewService:
    """Dependency provider for CrewService."""
    return _crew_service


def get_document_service() -> DocumentService:
    """Dependency provider for DocumentService."""
    return _document_service


def get_ai_service() -> AIService:
    """Dependency provider for AIService."""
    return _ai_service
