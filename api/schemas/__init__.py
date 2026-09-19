"""
Pydantic schemas for request and response validation.
"""

from .chat import ChatRequest, ChatResponse, ChatHistoryResponse, ClearMemoryResponse
from .document import (
    DocumentItem,
    DocumentListResponse,
    DocumentUploadResponse,
    DocumentDeleteResponse,
    DocumentContentResponse,
)
from .system import HealthResponse, StatusResponse
from .ai import (
    AIInfoResponse,
    AgentInfo,
    ToolInfo,
    AIQueryRequest,
    AIQueryResponse,
    SourceItem,
    KnowledgeIndexResponse,
    DocumentIndexItem,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    SearchExcerpt,
)

__all__ = [
    "ChatRequest",
    "ChatResponse",
    "ChatHistoryResponse",
    "ClearMemoryResponse",
    "DocumentItem",
    "DocumentListResponse",
    "DocumentUploadResponse",
    "DocumentDeleteResponse",
    "DocumentContentResponse",
    "HealthResponse",
    "StatusResponse",
    # AI Module
    "AIInfoResponse",
    "AgentInfo",
    "ToolInfo",
    "AIQueryRequest",
    "AIQueryResponse",
    "SourceItem",
    "KnowledgeIndexResponse",
    "DocumentIndexItem",
    "KnowledgeSearchRequest",
    "KnowledgeSearchResponse",
    "SearchExcerpt",
]
