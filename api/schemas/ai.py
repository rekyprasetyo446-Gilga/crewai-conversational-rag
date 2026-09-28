"""
Pydantic schemas for the AI Module endpoints.
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# GET /api/ai/info
# ---------------------------------------------------------------------------

class AgentInfo(BaseModel):
    name: str = Field(..., description="Agent display name")
    role: str = Field(..., description="Agent functional role")
    description: str = Field(..., description="What this agent does")
    tools: List[str] = Field(default_factory=list, description="Tools available to this agent")
    allow_delegation: Optional[bool] = Field(default=None, description="Whether agent delegation is enabled")


class ToolInfo(BaseModel):
    name: str = Field(..., description="Tool display name")
    description: str = Field(..., description="What the tool does")


class AIInfoResponse(BaseModel):
    system_name: str = Field(..., description="Name of the AI system")
    version: str = Field(..., description="System version")
    active_model: str = Field(..., description="Currently configured LLM model")
    model_configured: bool = Field(..., description="Whether the LLM API key is set")
    pipeline: str = Field(..., description="Pipeline process type (e.g. sequential)")
    agents: List[AgentInfo] = Field(default_factory=list, description="Registered agents in the pipeline")
    tools: List[ToolInfo] = Field(default_factory=list, description="Available CrewAI tools")


# ---------------------------------------------------------------------------
# POST /api/ai/query  (JSON-mode structured RAG)
# ---------------------------------------------------------------------------

class AIQueryRequest(BaseModel):
    message: str = Field(..., description="The user question or query")
    session_id: str = Field(default="default", description="Session identifier for memory continuity")
    use_json_mode: bool = Field(
        default=True,
        description="If True, uses json_llm for structured JSON output; if False, falls back to plain text pipeline"
    )


class SourceItem(BaseModel):
    document: str = Field(..., description="Source document filename")
    relevant_excerpts: List[str] = Field(default_factory=list, description="Relevant text excerpts from this document")
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevance score 0-1")


class AIQueryResponse(BaseModel):
    query: str = Field(..., description="The original user query")
    session_id: str = Field(..., description="Session identifier")
    model: str = Field(..., description="Model used to generate the response")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score 0-1")
    sources: List[SourceItem] = Field(default_factory=list, description="Source documents with excerpts")
    aggregated_facts: List[str] = Field(default_factory=list, description="Key facts extracted from knowledge base")
    conflicts: List[str] = Field(default_factory=list, description="Any conflicting information found")
    host_diagnostics: Optional[str] = Field(default=None, description="Host diagnostics if queried")
    summary: str = Field(default="", description="Concise factual summary answer")
    raw_output: Optional[str] = Field(default=None, description="Raw agent output if JSON parsing failed")


# ---------------------------------------------------------------------------
# GET /api/ai/knowledge/index
# ---------------------------------------------------------------------------

class DocumentIndexItem(BaseModel):
    filename: str = Field(..., description="Knowledge file name")
    category: str = Field(..., description="Document category")
    topics: List[str] = Field(default_factory=list, description="List of topics covered")
    summary: str = Field(..., description="Brief document summary")
    format: str = Field(..., description="File format (md, json, txt, etc.)")
    estimated_size_kb: float = Field(default=0.0, description="Estimated file size in KB")


class KnowledgeIndexResponse(BaseModel):
    index_version: str = Field(..., description="Index schema version")
    total_documents: int = Field(..., description="Total number of indexed documents")
    categories: List[str] = Field(default_factory=list, description="Available document categories")
    documents: List[DocumentIndexItem] = Field(default_factory=list, description="Index entries for all documents")
    topic_to_documents: Dict[str, List[str]] = Field(
        default_factory=dict, description="Mapping of topics to relevant document filenames"
    )


# ---------------------------------------------------------------------------
# POST /api/ai/knowledge/search  (direct lightweight search)
# ---------------------------------------------------------------------------

class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., description="Search query keywords or phrase")
    json_only: bool = Field(
        default=False,
        description="If True, searches only structured JSON knowledge files"
    )


class SearchExcerpt(BaseModel):
    document: str = Field(..., description="Source document filename")
    section_index: int = Field(..., description="Section/chunk index within the document")
    score: int = Field(..., description="Relevance score (higher = more relevant)")
    text: str = Field(..., description="Matching text excerpt")


class KnowledgeSearchResponse(BaseModel):
    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Number of matching excerpts returned")
    excerpts: List[SearchExcerpt] = Field(default_factory=list, description="Ranked matching excerpts")
    raw_output: str = Field(default="", description="Raw formatted output from the search tool")
