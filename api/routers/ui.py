"""
UI Router: Serves the web dashboard user interface.
"""

from pathlib import Path
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from api.config import Settings
from api.dependencies import get_settings

router = APIRouter(tags=["Web UI"])


@router.get("/", response_class=HTMLResponse, summary="Serve Web UI Dashboard")
async def index_endpoint(settings: Settings = Depends(get_settings)):
    """Serves the modern dark-mode browser chat interface."""
    html_path = settings.templates_dir / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"), status_code=200)
    return HTMLResponse(content="<h1>CrewAI Web UI template not found.</h1>", status_code=404)
