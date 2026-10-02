"""
AIService: Handles AI module features â€” structured JSON RAG queries,
knowledge index retrieval, direct search, and system metadata.
"""

import json
import sys
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from fastapi import HTTPException

from api.config import settings


# ---------------------------------------------------------------------------
# Static agent / tool metadata (mirrors agents.py and tools.py declarations)
# ---------------------------------------------------------------------------

_AGENT_METADATA = [
    {
        "name": "Knowledge Retrieval Specialist",
        "role": "Retriever",
        "description": (
            "Searches and retrieves accurate facts and excerpts from knowledge base documents. "
            "Strictly grounded in indexed documentation with integrated AHost DNS verification."
        ),
        "tools": ["Knowledge Base Search", "List Knowledge Documents", "Read Complete Document", "AHost Lookup Tool"],
        "allow_delegation": True,
    },
    {
        "name": "Aggregator Host Specialist",
        "role": "Aggregator",
        "description": (
            "Aggregates, cross-examines, and synthesizes knowledge excerpts. "
            "Resolves conflicts, deduplicates findings, inspects local host diagnostics (AggregatorHost.exe), "
            "and performs deep asynchronous DNS diagnostics via adig.exe and ahost.exe."
        ),
        "tools": [
            "Knowledge Base Search",
            "Read Complete Document",
            "Aggregator Host Status Inspector",
            "ADig DNS Query Tool",
            "AHost Lookup Tool",
            "MySQL Query Tool",
            "MySQL Shared Blackboard Tool",
            "XAMPP FileZilla FTP Storage Tool",
            "XAMPP Mercury Mail Tool",
        ],
        "allow_delegation": True,
    },
    {
        "name": "Conversational Synthesizer",
        "role": "Synthesizer",
        "description": (
            "Synthesizes retrieved and aggregated knowledge into warm, natural, "
            "and well-cited conversational responses for the user."
        ),
        "tools": ["XAMPP Mercury Mail Tool"],
        "allow_delegation": True,
    },
]

_TOOL_METADATA = [
    {
        "name": "Knowledge Base Search",
        "description": "Keyword and relevance-based search across all knowledge base documents.",
    },
    {
        "name": "List Knowledge Documents",
        "description": "Lists all indexed documents in the knowledge directory with file sizes.",
    },
    {
        "name": "Read Complete Document",
        "description": "Reads the full content of a specific knowledge base document by name.",
    },
    {
        "name": "Aggregator Host Status Inspector",
        "description": (
            "Inspects local host system telemetry, CPU architecture, "
            "and Windows AggregatorHost.exe process health."
        ),
    },
    {
        "name": "JSON Knowledge Search",
        "description": (
            "Searches exclusively through structured JSON knowledge files, "
            "returning parsed key-value data relevant to the query."
        ),
    },
    {
        "name": "ADig DNS Query Tool",
        "description": (
            "Performs low-level asynchronous DNS interrogation (A, AAAA, MX, TXT, NS, SOA, PTR, CNAME) "
            "using adig.exe (c-ares engine)."
        ),
    },
    {
        "name": "AHost Lookup Tool",
        "description": (
            "Performs fast asynchronous hostname and dual-stack IP address resolution (IPv4 & IPv6) "
            "using ahost.exe (c-ares engine)."
        ),
    },
    {
        "name": "MySQL Query Tool",
        "description": "Executes read-only SQL queries against the XAMPP MySQL database 'crewai_memory'.",
    },
    {
        "name": "MySQL Shared Blackboard Tool",
        "description": "Reads and writes shared agent facts to the XAMPP MySQL shared_blackboard table.",
    },
    {
        "name": "XAMPP FileZilla FTP Storage Tool",
        "description": "Uploads, lists, and downloads files in centralized FTP storage on FileZilla.",
    },
    {
        "name": "XAMPP Mercury Mail Tool",
        "description": "Dispatches SMTP alert notifications and checks POP3 incoming mail via Mercury.",
    },
]


class AIService:
    """Provides AI module features: info, structured RAG query, knowledge index, and direct search."""

    def __init__(self, knowledge_dir: Path = settings.knowledge_dir):
        self.knowledge_dir = knowledge_dir
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # GET /api/ai/info
    # ------------------------------------------------------------------

    def get_ai_info(self, active_model: str, model_configured: bool) -> Dict[str, Any]:
        """Returns static AI system metadata merged with live model configuration."""
        return {
            "system_name": settings.app_name,
            "version": settings.app_version,
            "active_model": active_model,
            "model_configured": model_configured,
            "pipeline": "sequential",
            "agents": _AGENT_METADATA,
            "tools": _TOOL_METADATA,
        }

    # ------------------------------------------------------------------
    # POST /api/ai/query  (JSON-mode structured RAG)
    # ------------------------------------------------------------------

    async def structured_query(
        self,
        session_id: str,
        message: str,
        crew_service,  # CrewService injected to avoid circular imports
        use_json_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Runs the multi-agent RAG pipeline and attempts to return structured JSON output.
        Falls back to raw text if JSON mode fails or produces unparseable output.
        """
        # Ensure project root is in sys.path so crew/tasks imports work
        project_root = Path(__file__).resolve().parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        crew = crew_service.get_crew(session_id)
        model = crew.model

        if use_json_mode and crew.json_llm:
            result = await self._run_json_pipeline(crew, message)
        else:
            # Fall back to standard async pipeline
            reply = await crew.ask_async(message)
            result = self._wrap_plain_text(message, reply)

        result["session_id"] = session_id
        result["model"] = model
        return result

    async def _run_json_pipeline(self, crew, message: str) -> Dict[str, Any]:
        """Runs the full 3-agent pipeline using json_llm for structured aggregation output."""
        try:
            from crewai import Crew, Process
            from agents import get_retriever_agent, get_aggregator_host_agent, get_conversational_agent
            from tasks import (
                create_retrieval_task,
                create_json_aggregation_task,
                create_conversational_task,
            )

            history_context = crew.format_history()

            retriever = get_retriever_agent(llm=crew.llm, allow_delegation=True)
            aggregator = get_aggregator_host_agent(llm=crew.json_llm, allow_delegation=True)
            synthesizer = get_conversational_agent(llm=crew.llm, allow_delegation=True)

            t1 = create_retrieval_task(retriever, message, history_context)
            t2 = create_json_aggregation_task(aggregator, message, history_context)
            t3 = create_conversational_task(synthesizer, message, history_context)

            crew_run = Crew(
                agents=[retriever, aggregator, synthesizer],
                tasks=[t1, t2, t3],
                process=Process.sequential,
                verbose=crew.verbose,
            )

            result = crew_run.kickoff()
            raw_output = str(result)

            # Save to session memory
            crew.chat_history.append({"role": "user", "content": message})
            crew.chat_history.append({"role": "assistant", "content": raw_output})

            # Try to parse JSON from the aggregation task output
            parsed = self._extract_json_from_output(raw_output)
            if parsed:
                return parsed
            else:
                return self._wrap_plain_text(message, raw_output)

        except Exception as e:
            return {
                "query": message,
                "confidence": 0.0,
                "sources": [],
                "aggregated_facts": [],
                "conflicts": [],
                "host_diagnostics": None,
                "summary": f"An error occurred during structured query: {str(e)}",
                "raw_output": str(e),
            }

    def _extract_json_from_output(self, raw: str) -> Optional[Dict[str, Any]]:
        """Attempts to extract a JSON object from raw agent output."""
        # Try direct JSON parse first
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            pass

        # Try to extract first JSON block from markdown output
        import re
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find a raw JSON object anywhere in output
        match = re.search(r"\{[^{}]*\"query\"[^{}]*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _wrap_plain_text(self, query: str, raw_output: str) -> Dict[str, Any]:
        """Wraps a plain text response in the structured schema format."""
        return {
            "query": query,
            "confidence": 0.5,
            "sources": [],
            "aggregated_facts": [],
            "conflicts": [],
            "host_diagnostics": None,
            "summary": raw_output,
            "raw_output": raw_output,
        }

    # ------------------------------------------------------------------
    # GET /api/ai/knowledge/index
    # ------------------------------------------------------------------

    def get_knowledge_index(self) -> Dict[str, Any]:
        """Reads and returns the parsed knowledge_index.json file."""
        index_path = self.knowledge_dir / "knowledge_index.json"
        if not index_path.exists():
            raise HTTPException(
                status_code=404,
                detail="knowledge_index.json not found in knowledge directory."
            )
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse knowledge_index.json: {str(e)}"
            )

        # Inject live document count
        docs = data.get("documents", [])
        data["total_documents"] = len(docs)
        return data

    # ------------------------------------------------------------------
    # POST /api/ai/knowledge/search  (direct lightweight search)
    # ------------------------------------------------------------------

    def direct_search(self, query: str, json_only: bool = False) -> Dict[str, Any]:
        """
        Runs direct knowledge search without spinning up any agents.
        Uses KnowledgeSearchTool or JsonKnowledgeSearchTool depending on json_only flag.
        """
        try:
            if json_only:
                from tools import JsonKnowledgeSearchTool
                tool = JsonKnowledgeSearchTool()
            else:
                from tools import KnowledgeSearchTool
                tool = KnowledgeSearchTool()

            raw_output = tool._run(query=query)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Knowledge search failed: {str(e)}"
            )

        # Parse excerpts from raw output for structured response
        excerpts = self._parse_search_excerpts(raw_output, query)
        return {
            "query": query,
            "total_results": len(excerpts),
            "excerpts": excerpts,
            "raw_output": raw_output,
        }

    def _parse_search_excerpts(self, raw: str, query: str) -> List[Dict[str, Any]]:
        """Parses the raw string output from KnowledgeSearchTool into structured excerpt items."""
        import re
        excerpts = []
        blocks = raw.split("---")
        for i, block in enumerate(blocks):
            if not block.strip() or "Search Results" in block:
                continue
            doc_match = re.search(r"\*\*Source Document\*\*:\s*`([^`]+)`\s*\(Section (\d+)\)", block)
            text = re.sub(r"\*\*Source Document\*\*:[^\n]*\n?", "", block).strip()
            if text:
                excerpts.append({
                    "document": doc_match.group(1) if doc_match else "unknown",
                    "section_index": int(doc_match.group(2)) if doc_match else i,
                    "score": max(1, len([w for w in query.lower().split() if w in text.lower()])),
                    "text": text[:500],
                })
        return excerpts


