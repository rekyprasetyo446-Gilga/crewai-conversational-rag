"""
Chat request and response schemas.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's query or message", min_length=1)
    session_id: Optional[str] = Field(
        default="default",
        description="Session identifier for multi-user/multi-tab conversation isolation"
    )


class ChatResponse(BaseModel):
    reply: str = Field(..., description="Synthesized grounded answer from the CrewAI multi-agent team")
    turns: int = Field(..., description="Current conversation turn count for this session")
    model: str = Field(..., description="Active LLM model used for synthesis")
    session_id: str = Field(default="default", description="Session identifier")


class ChatMessageItem(BaseModel):
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message text content")


class ChatHistoryResponse(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    turns: int = Field(..., description="Number of completed conversational turns")
    history: List[ChatMessageItem] = Field(default_factory=list, description="Ordered conversation history turns")


class ClearMemoryResponse(BaseModel):
    status: str = Field(default="Memory cleared", description="Operation status")
    turns: int = Field(default=0, description="Turn count after reset")
    session_id: str = Field(default="default", description="Session identifier cleared")
