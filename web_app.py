"""
FastAPI Server Launcher for CrewAI Conversational RAG.
Serves the browser dashboard and modular REST API.
"""

import sys
from pathlib import Path

# Ensure project root is in Python module search path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import uvicorn
from api import app, create_app
from api.config import settings

# Export app at module level for ASGI servers (e.g. uvicorn web_app:app)
__all__ = ["app", "create_app"]

if __name__ == "__main__":
    host = settings.host
    port = settings.port

    print(f"Starting {settings.app_name} v{settings.app_version}...")
    print(f"Web Dashboard:   http://{host}:{port}/")
    print(f"API Docs:        http://{host}:{port}/docs")
    print(f"ReDoc Docs:      http://{host}:{port}/redoc")
    if host != "127.0.0.1":
        print(f"Local Loopback:  http://127.0.0.1:{port}/")

    uvicorn.run("web_app:app", host=host, port=port, reload=True)
