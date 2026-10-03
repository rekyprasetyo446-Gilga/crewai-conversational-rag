"""
Application configuration for FastAPI CrewAI RAG server.
"""

import os
from pathlib import Path
from typing import List, Set
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseModel):
    app_name: str = "CrewAI Conversational RAG API"
    app_version: str = "1.0.0"
    app_description: str = (
        "Modular FastAPI backend for multi-agent conversational RAG "
        "powered by CrewAI, document retrieval, and persistent session memory."
    )
    knowledge_dir: Path = Field(default_factory=lambda: Path(os.getenv("KNOWLEDGE_DIR", BASE_DIR / "knowledge")))
    templates_dir: Path = Field(default_factory=lambda: Path(BASE_DIR / "templates"))
    allowed_extensions: Set[str] = Field(
        default_factory=lambda: {".md", ".txt", ".json", ".pdf", ".csv"}
    )
    max_upload_size_bytes: int = 20 * 1024 * 1024  # 20 MB
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    host: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    adsense_api_key: str = Field(default_factory=lambda: os.getenv("ADSENSE_API_KEY", "your-super-secret-key-to-block-spies"))

settings = Settings()
