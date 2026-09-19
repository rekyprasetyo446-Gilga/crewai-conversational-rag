"""
System health and status schemas.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Overall system health status")
    version: str = Field(..., description="API version")
    model_configured: bool = Field(..., description="True if LLM API key and model are properly configured")
    active_sessions: int = Field(..., description="Number of active conversational sessions")
    total_documents: int = Field(..., description="Number of indexed documents in knowledge base")


class StatusResponse(BaseModel):
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    model: str = Field(..., description="Active language model")
    knowledge_dir: str = Field(..., description="Absolute path to knowledge base directory")
    active_sessions: int = Field(..., description="Active session count")
