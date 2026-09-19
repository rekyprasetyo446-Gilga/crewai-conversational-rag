"""
CrewAI Conversational RAG FastAPI Module.
Provides the main application factory and app instance.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.routers import chat_router, documents_router, system_router, ui_router, ai_router


def create_app() -> FastAPI:
    """Application factory for the modular FastAPI server."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS for decoupled frontend or local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register modular routers
    app.include_router(ui_router)
    app.include_router(chat_router)
    app.include_router(documents_router)
    app.include_router(system_router)
    app.include_router(ai_router)

    return app


app = create_app()

__all__ = ["create_app", "app"]
