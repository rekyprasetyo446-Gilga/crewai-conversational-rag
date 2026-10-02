"""
UI Router: Serves the web dashboard user interface and Service Worker.
"""

from pathlib import Path
from fastapi import APIRouter, Depends, Response
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


@router.api_route("/sw.js", methods=["GET", "HEAD"], summary="Serve Cross-Browser Service Worker")
async def service_worker_endpoint(settings: Settings = Depends(get_settings)):
    """
    Serves the high-performance Service Worker script.
    Compatible across Chrome, Edge, and Firefox with root scope privileges.
    """
    sw_path = settings.templates_dir / "sw.js"
    if sw_path.exists():
        content = sw_path.read_text(encoding="utf-8")
        return Response(
            content=content,
            media_type="application/javascript",
            headers={
                "Service-Worker-Allowed": "/",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    return Response(content="// Service Worker not found", media_type="application/javascript", status_code=404)
