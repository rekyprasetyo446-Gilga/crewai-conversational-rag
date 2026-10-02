"""
Modular API routers.
"""

from .chat import router as chat_router
from .documents import router as documents_router
from .system import router as system_router
from .ui import router as ui_router
from .ai import router as ai_router
from .adsense import router as adsense_router

__all__ = ["chat_router", "documents_router", "system_router", "ui_router", "ai_router", "adsense_router"]
