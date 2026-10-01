"""
MCP Manager for CrewAI Conversational RAG.
Handles discovery, configuration parsing, and instantiation of Model Context Protocol (MCP) servers
for CrewAI multi-agent teams.
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from crewai.mcp import (
    MCPServerConfig,
    MCPServerStdio,
    MCPServerHTTP,
    MCPServerSSE,
)
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "mcp_servers.json"


def load_mcp_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Loads MCP server configurations from JSON file."""
    path = config_path or CONFIG_PATH
    if not path.exists():
        return {"enabled": True, "servers": {}}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data
    except Exception as e:
        print(f"[Warning] Failed to parse MCP configuration file '{path}': {e}")
        return {"enabled": False, "servers": {}}


def build_mcp_server_config(server_id: str, cfg: Dict[str, Any]) -> Optional[MCPServerConfig]:
    """Instantiates the appropriate MCPServerConfig from a dictionary definition."""
    transport = cfg.get("transport", "stdio").lower()

    if transport == "stdio":
        cmd = cfg.get("command", "python")
        # Ensure 'python' resolves to current sys.executable in virtualenv
        if cmd.lower() in ["python", "python3"]:
            cmd = sys.executable

        raw_args = cfg.get("args", [])
        args = []
        for arg in raw_args:
            # Resolve script path if relative to project root
            target = PROJECT_ROOT / arg
            if target.exists():
                args.append(str(target))
            else:
                args.append(str(arg))

        env = cfg.get("env", None)
        return MCPServerStdio(
            command=cmd,
            args=args,
            env=env
        )

    elif transport == "http":
        url = cfg.get("url")
        if not url:
            return None
        headers = cfg.get("headers", None)
        if headers and isinstance(headers, dict):
            headers = {k: os.path.expandvars(str(v)) for k, v in headers.items()}
        streamable = cfg.get("streamable", True)
        return MCPServerHTTP(
            url=url,
            headers=headers,
            streamable=streamable
        )

    elif transport == "sse":
        url = cfg.get("url")
        if not url:
            return None
        headers = cfg.get("headers", None)
        if headers and isinstance(headers, dict):
            headers = {k: os.path.expandvars(str(v)) for k, v in headers.items()}
        return MCPServerSSE(
            url=url,
            headers=headers
        )

    return None


def get_agent_mcps(agent_role: str, config_path: Optional[Path] = None) -> List[MCPServerConfig]:
    """
    Returns the list of MCPServerConfig instances configured for a given agent role.
    Roles: 'retriever', 'aggregator_host', 'conversationalist', or 'all'.
    """
    cfg = load_mcp_config(config_path)
    if not cfg.get("enabled", True):
        return []

    assigned_configs: List[MCPServerConfig] = []
    normalized_role = agent_role.lower().strip()

    for server_id, server_data in cfg.get("servers", {}).items():
        agents_list = [a.lower().strip() for a in server_data.get("agents", ["all"])]
        if "all" in agents_list or normalized_role in agents_list:
            server_config = build_mcp_server_config(server_id, server_data)
            if server_config:
                assigned_configs.append(server_config)

    return assigned_configs


def get_all_mcp_configs(config_path: Optional[Path] = None) -> Dict[str, MCPServerConfig]:
    """Returns a dictionary of all active MCPServerConfig instances keyed by server ID."""
    cfg = load_mcp_config(config_path)
    if not cfg.get("enabled", True):
        return {}

    configs = {}
    for server_id, server_data in cfg.get("servers", {}).items():
        sc = build_mcp_server_config(server_id, server_data)
        if sc:
            configs[server_id] = sc
    return configs


def get_mcp_summary(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Generates a comprehensive diagnostic report of registered MCP servers and status."""
    cfg = load_mcp_config(config_path)
    enabled = cfg.get("enabled", True)
    servers = cfg.get("servers", {})

    summary: Dict[str, Any] = {
        "enabled": enabled,
        "total_servers": len(servers),
        "servers": []
    }

    for s_id, s_data in servers.items():
        summary["servers"].append({
            "id": s_id,
            "name": s_data.get("name", s_id),
            "transport": s_data.get("transport", "stdio"),
            "agents": s_data.get("agents", []),
            "tools_overview": s_data.get("tools_overview", []),
        })

    return summary


# ==========================================
# Native CrewAI BaseTool Wrappers for Local FastMCP Tools
# ==========================================
# Exposes direct BaseTool adapters for local FastMCP functions, allowing direct
# tool execution or fallback in environments without subprocess spawning.

class FastMCPQueryInput(BaseModel):
    query: str = Field(..., description="Query topic or keywords to search across the MCP knowledge base.")

class FastMCPDocInput(BaseModel):
    document_name: str = Field(..., description="Exact name of the document to inspect over MCP.")

class FastMCPBlackboardWriteInput(BaseModel):
    key_name: str = Field(..., description="Key identifier for shared observation.")
    value_data: str = Field(..., description="Fact or finding to store on blackboard.")
    session_id: str = Field(default="global", description="Session identifier.")

class FastMCPBlackboardReadInput(BaseModel):
    key_name: str = Field(..., description="Key identifier to read from shared blackboard.")
    session_id: str = Field(default="global", description="Session identifier.")

class FastMCPURLInput(BaseModel):
    url: str = Field(..., description="Public web URL to fetch and extract content from.")

class FastMCPProcessInput(BaseModel):
    process_name: str = Field(default="AggregatorHost.exe", description="Process name to inspect.")


class MCPHostTelemetryTool(BaseTool):
    name: str = "MCP Host Telemetry Inspector"
    description: str = "Inspects host platform telemetry, CPU specifications, OS architecture, and runtime via FastMCP."

    def _run(self) -> str:
        from mcp_server import get_system_telemetry
        return get_system_telemetry()


class MCPProcessInspectorTool(BaseTool):
    name: str = "MCP Process Health Inspector"
    description: str = "Queries Windows tasklist and system processes to verify AggregatorHost.exe health via FastMCP."
    args_schema: type[BaseModel] = FastMCPProcessInput

    def _run(self, process_name: str = "AggregatorHost.exe") -> str:
        from mcp_server import inspect_host_process
        return inspect_host_process(process_name=process_name)


class MCPKnowledgeSearchTool(BaseTool):
    name: str = "MCP Knowledge Base Search"
    description: str = "Performs keyword and semantic document retrieval across the knowledge base via FastMCP."
    args_schema: type[BaseModel] = FastMCPQueryInput

    def _run(self, query: str) -> str:
        from mcp_server import search_mcp_knowledge
        return search_mcp_knowledge(query=query)


class MCPDocumentReaderTool(BaseTool):
    name: str = "MCP Document Reader"
    description: str = "Reads complete document content by name from the knowledge base directory via FastMCP."
    args_schema: type[BaseModel] = FastMCPDocInput

    def _run(self, document_name: str) -> str:
        from mcp_server import read_mcp_document
        return read_mcp_document(document_name=document_name)


class MCPBlackboardWriteTool(BaseTool):
    name: str = "MCP Shared Blackboard Writer"
    description: str = "Stores shared findings and verified facts into the multi-agent shared blackboard via FastMCP."
    args_schema: type[BaseModel] = FastMCPBlackboardWriteInput

    def _run(self, key_name: str, value_data: str, session_id: str = "global") -> str:
        from mcp_server import mcp_blackboard_write
        return mcp_blackboard_write(key_name=key_name, value_data=value_data, session_id=session_id)


class MCPBlackboardReadTool(BaseTool):
    name: str = "MCP Shared Blackboard Reader"
    description: str = "Retrieves previously stored observations and intermediate facts from the shared blackboard via FastMCP."
    args_schema: type[BaseModel] = FastMCPBlackboardReadInput

    def _run(self, key_name: str, session_id: str = "global") -> str:
        from mcp_server import mcp_blackboard_read
        return mcp_blackboard_read(key_name=key_name, session_id=session_id)


class MCPURLFetcherTool(BaseTool):
    name: str = "MCP URL Content Fetcher"
    description: str = "Fetches and cleans public web URL or API content for knowledge enrichment via FastMCP."
    args_schema: type[BaseModel] = FastMCPURLInput

    def _run(self, url: str) -> str:
        from mcp_server import fetch_url_content
        return fetch_url_content(url=url)


class MCPAdigInput(BaseModel):
    domain: str = Field(..., description="Domain name or host to query via adig.")
    record_type: str = Field(default="A", description="DNS record type: A, AAAA, MX, TXT, NS, SOA, CNAME, PTR, ANY.")
    server: str = Field(default="", description="Optional custom DNS server IP address.")
    extra_flags: str = Field(default="", description="Optional extra flags.")


class MCPAdigQueryTool(BaseTool):
    name: str = "MCP ADig DNS Query Tool"
    description: str = "Performs asynchronous DNS interrogation and record inspection via FastMCP (adig.exe / c-ares engine)."
    args_schema: type[BaseModel] = MCPAdigInput

    def _run(self, domain: str, record_type: str = "A", server: str = "", extra_flags: str = "") -> str:
        from mcp_server import query_dns_adig
        return query_dns_adig(domain=domain, record_type=record_type, server=server, extra_flags=extra_flags)


class MCPAhostInput(BaseModel):
    host: str = Field(..., description="Hostname or IP address to resolve via ahost.")
    lookup_type: str = Field(default="u", description="Lookup type: 'u' (both IPv4/IPv6), 'a' (IPv4), or 'aaaa' (IPv6).")
    server: str = Field(default="", description="Optional custom DNS server IP.")
    domain: str = Field(default="", description="Optional search domain to append.")
    debug: bool = Field(default=False, description="Whether to include debug output.")


class MCPAhostLookupTool(BaseTool):
    name: str = "MCP AHost Lookup Tool"
    description: str = "Performs fast asynchronous hostname and dual-stack IP resolution via FastMCP (ahost.exe / c-ares engine)."
    args_schema: type[BaseModel] = MCPAhostInput

    def _run(self, host: str, lookup_type: str = "u", server: str = "", domain: str = "", debug: bool = False) -> str:
        from mcp_server import resolve_host_ahost
        return resolve_host_ahost(host=host, lookup_type=lookup_type, server=server, domain=domain, debug=debug)


def get_local_fastmcp_tools() -> List[BaseTool]:
    """Returns a list of all local FastMCP tools adapted as CrewAI BaseTools."""
    return [
        MCPHostTelemetryTool(),
        MCPProcessInspectorTool(),
        MCPKnowledgeSearchTool(),
        MCPDocumentReaderTool(),
        MCPBlackboardWriteTool(),
        MCPBlackboardReadTool(),
        MCPURLFetcherTool(),
        MCPAdigQueryTool(),
        MCPAhostLookupTool(),
    ]

