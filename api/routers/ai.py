"""
AI Router: Endpoints for AI system metadata, structured JSON RAG queries,
knowledge index retrieval, and lightweight direct knowledge search.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from api.dependencies import get_ai_service, get_crew_service
from api.services.ai_service import AIService
from api.services.crew_service import CrewService
from api.schemas.ai import (
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

router = APIRouter(prefix="/api/ai", tags=["AI Module"])


@router.get(
    "/info",
    response_model=AIInfoResponse,
    summary="AI system metadata",
    description=(
        "Returns the active LLM model, pipeline architecture, "
        "full list of registered agents, and available tools."
    ),
)
async def ai_info_endpoint(
    ai_service: AIService = Depends(get_ai_service),
    crew_service: CrewService = Depends(get_crew_service),
) -> AIInfoResponse:
    info = ai_service.get_ai_info(
        active_model=crew_service.get_active_model(),
        model_configured=crew_service.is_configured(),
    )
    return AIInfoResponse(
        system_name=info["system_name"],
        version=info["version"],
        active_model=info["active_model"],
        model_configured=info["model_configured"],
        pipeline=info["pipeline"],
        agents=[AgentInfo(**a) for a in info["agents"]],
        tools=[ToolInfo(**t) for t in info["tools"]],
    )


@router.post(
    "/query",
    response_model=AIQueryResponse,
    summary="Structured JSON RAG query",
    description=(
        "Runs the full multi-agent RAG pipeline (Retriever → Aggregator → Synthesizer) "
        "and returns a structured JSON response with sources, facts, confidence, and a summary. "
        "Set `use_json_mode=true` to use the json_llm for structured aggregation output."
    ),
)
async def ai_query_endpoint(
    req: AIQueryRequest,
    ai_service: AIService = Depends(get_ai_service),
    crew_service: CrewService = Depends(get_crew_service),
) -> AIQueryResponse:
    clean_message = req.message.strip()
    if not clean_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    result = await ai_service.structured_query(
        session_id=req.session_id,
        message=clean_message,
        crew_service=crew_service,
        use_json_mode=req.use_json_mode,
    )

    sources = [
        SourceItem(
            document=s.get("document", ""),
            relevant_excerpts=s.get("relevant_excerpts", []),
            relevance_score=float(s.get("relevance_score", 0.0)),
        )
        for s in result.get("sources", [])
    ]

    return AIQueryResponse(
        query=result.get("query", clean_message),
        session_id=result.get("session_id", req.session_id),
        model=result.get("model", "unknown"),
        confidence=float(result.get("confidence", 0.0)),
        sources=sources,
        aggregated_facts=result.get("aggregated_facts", []),
        conflicts=result.get("conflicts", []),
        host_diagnostics=result.get("host_diagnostics"),
        summary=result.get("summary", ""),
        raw_output=result.get("raw_output"),
    )


@router.get(
    "/knowledge/index",
    response_model=KnowledgeIndexResponse,
    summary="Structured knowledge index",
    description=(
        "Returns the parsed knowledge_index.json — a structured map of all knowledge base documents, "
        "their categories, topics, and summaries."
    ),
)
async def knowledge_index_endpoint(
    ai_service: AIService = Depends(get_ai_service),
) -> KnowledgeIndexResponse:
    data = ai_service.get_knowledge_index()
    docs = [
        DocumentIndexItem(
            filename=d.get("filename", ""),
            category=d.get("category", ""),
            topics=d.get("topics", []),
            summary=d.get("summary", ""),
            format=d.get("format", ""),
            estimated_size_kb=float(d.get("estimated_size_kb", 0.0)),
        )
        for d in data.get("documents", [])
    ]
    return KnowledgeIndexResponse(
        index_version=data.get("index_version", "1.0"),
        total_documents=data.get("total_documents", len(docs)),
        categories=data.get("categories", []),
        documents=docs,
        topic_to_documents=data.get("topic_to_documents", {}),
    )


@router.post(
    "/knowledge/search",
    response_model=KnowledgeSearchResponse,
    summary="Direct lightweight knowledge search",
    description=(
        "Runs KnowledgeSearchTool (or JsonKnowledgeSearchTool if json_only=true) directly "
        "without spinning up any agents. Fast, lightweight, and ideal for autocomplete or previews."
    ),
)
async def knowledge_search_endpoint(
    req: KnowledgeSearchRequest,
    ai_service: AIService = Depends(get_ai_service),
) -> KnowledgeSearchResponse:
    clean_query = req.query.strip()
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty.",
        )

    result = ai_service.direct_search(query=clean_query, json_only=req.json_only)
    excerpts = [
        SearchExcerpt(
            document=e.get("document", ""),
            section_index=e.get("section_index", 0),
            score=e.get("score", 0),
            text=e.get("text", ""),
        )
        for e in result.get("excerpts", [])
    ]
    return KnowledgeSearchResponse(
        query=result.get("query", clean_query),
        total_results=result.get("total_results", len(excerpts)),
        excerpts=excerpts,
        raw_output=result.get("raw_output", ""),
    )
