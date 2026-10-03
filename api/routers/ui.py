"""
UI Router: Serves the web dashboard user interface and Service Worker.
"""

from pathlib import Path
from fastapi import APIRouter, Depends, Response
from fastapi.responses import FileResponse
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


@router.api_route("/manifest.json", methods=["GET", "HEAD"], summary="Serve Web App Manifest")
async def manifest_endpoint(settings: Settings = Depends(get_settings)):
    """Serves the W3C Web App Manifest for Chrome, Edge, and Firefox PWA auto-run."""
    manifest_path = settings.templates_dir / "manifest.json"
    if manifest_path.exists():
        return Response(
            content=manifest_path.read_text(encoding="utf-8"),
            media_type="application/manifest+json",
            headers={
                "Cache-Control": "public, max-age=3600",
            },
        )
    return Response(content="{}", media_type="application/manifest+json", status_code=404)


@router.api_route("/favicon.ico", methods=["GET", "HEAD"], summary="Serve Favicon")
async def favicon_endpoint(settings: Settings = Depends(get_settings)):
    ico_path = settings.templates_dir / "icons" / "favicon.ico"
    if ico_path.exists():
        return FileResponse(ico_path, media_type="image/x-icon", headers={"Cache-Control": "public, max-age=86400"})
    return Response(status_code=404)


@router.api_route("/icons/{filename}", methods=["GET", "HEAD"], summary="Serve Icon Assets")
async def icons_endpoint(filename: str, settings: Settings = Depends(get_settings)):
    icons_dir = (settings.templates_dir / "icons").resolve()
    icon_path = (icons_dir / filename).resolve()
    if not str(icon_path).startswith(str(icons_dir)):
        return Response(status_code=403)
    if icon_path.exists() and icon_path.is_file():
        media_types = {
            ".png": "image/png",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".webp": "image/webp",
        }
        media_type = media_types.get(icon_path.suffix.lower(), "application/octet-stream")
        return FileResponse(
            icon_path,
            media_type=media_type,
            headers={"Cache-Control": "public, max-age=86400"},
        )
    return Response(status_code=404)

@router.api_route("/style.css", methods=["GET", "HEAD"], summary="Serve CSS")
async def style_endpoint(settings: Settings = Depends(get_settings)):
    css_path = settings.templates_dir / "style.css"
    if css_path.exists():
        return Response(content=css_path.read_text(encoding="utf-8"), media_type="text/css")
    return Response(status_code=404)

@router.api_route("/app.js", methods=["GET", "HEAD"], summary="Serve JS")
async def app_endpoint(settings: Settings = Depends(get_settings)):
    js_path = settings.templates_dir / "app.js"
    if js_path.exists():
        return Response(content=js_path.read_text(encoding="utf-8"), media_type="application/javascript")
    return Response(status_code=404)

@router.api_route("/ads.txt", methods=["GET", "HEAD"], summary="Serve ads.txt for Google AdSense")
async def ads_txt_endpoint(settings: Settings = Depends(get_settings)):
    ads_path = settings.templates_dir / "ads.txt"
    if ads_path.exists():
        return Response(content=ads_path.read_text(encoding="utf-8"), media_type="text/plain")
    return Response(status_code=404)

@router.api_route("/assets/{filename}", methods=["GET", "HEAD"], summary="Serve Assets")
async def assets_endpoint(filename: str, settings: Settings = Depends(get_settings)):
    assets_dir = (settings.templates_dir / "assets").resolve()
    asset_path = (assets_dir / filename).resolve()
    if not str(asset_path).startswith(str(assets_dir)):
        return Response(status_code=403)
    if asset_path.exists() and asset_path.is_file():
        return FileResponse(asset_path, headers={"Cache-Control": "public, max-age=86400"})
    return Response(status_code=404)