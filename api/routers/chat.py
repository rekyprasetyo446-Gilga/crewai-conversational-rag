"""
Chat Router: Endpoints for conversation execution, session management, and memory control.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from api.dependencies import get_crew_service
from api.services.crew_service import CrewService
from api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    ChatMessageItem,
    ClearMemoryResponse,
)

router = APIRouter(tags=["Chat & Conversation"])


@router.post(
    "/api/chat",
    response_model=ChatResponse,
    summary="Send a message to the CrewAI multi-agent RAG pipeline",
    description="Processes query with retriever, aggregator, and synthesizer agents, maintaining session memory.",
)
async def chat_endpoint(
    req: ChatRequest,
    crew_service: CrewService = Depends(get_crew_service),
) -> ChatResponse:
    clean_message = req.message.strip()
    if not clean_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty."
        )

    session_id = req.session_id or "default"
    reply, turns, model = await crew_service.ask_async(session_id, clean_message)

    return ChatResponse(
        reply=reply,
        turns=turns,
        model=model,
        session_id=session_id,
    )


@router.post(
    "/api/clear",
    response_model=ClearMemoryResponse,
    summary="Reset conversational memory",
    description="Wipes the short-term multi-turn history for a given session.",
)
async def clear_memory_endpoint(
    session_id: str = "default",
    crew_service: CrewService = Depends(get_crew_service),
) -> ClearMemoryResponse:
    crew_service.clear_session(session_id)
    return ClearMemoryResponse(
        status="Memory cleared",
        turns=0,
        session_id=session_id,
    )


@router.get(
    "/api/chat/history",
    response_model=ChatHistoryResponse,
    summary="Retrieve session message history",
    description="Returns the recorded conversational turns for a session.",
)
async def get_history_endpoint(
    session_id: str = "default",
    crew_service: CrewService = Depends(get_crew_service),
) -> ChatHistoryResponse:
    history = crew_service.get_history(session_id)
    items = [ChatMessageItem(role=turn["role"], content=turn["content"]) for turn in history]
    return ChatHistoryResponse(
        session_id=session_id,
        turns=len(items) // 2,
        history=items,
    )
