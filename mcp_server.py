"""
Built-in FastMCP Server for CrewAI Conversational RAG.
Exposes specialized tools over the Model Context Protocol (MCP) using stdio transport.
Can be queried by Knowledge Retrieval Specialist, Aggregator Host Specialist,
and Conversational Synthesizer.
"""

import sys
import os
import json
import platform
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("CrewAI-Conversational-RAG-MCP")

KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", "./knowledge")
BLACKBOARD_FILE = Path("./.blackboard_cache.json")


# ==========================================
# Tool 1: System Telemetry
# ==========================================
@mcp.tool()
def get_system_telemetry() -> str:
    """Inspects host system telemetry, OS specs, architecture, CPU count, and Python runtime."""
    cpu_count = os.cpu_count() or 1
    system_info = {
        "os": f"{platform.system()} {platform.release()} (Version: {platform.version()})",
        "architecture": platform.machine(),
        "processor": platform.processor() or "Standard x86/x64",
        "hostname": platform.node(),
        "cpu_threads": cpu_count,
        "python_runtime": platform.python_version(),
    }
    return (
        "### [MCP Host Telemetry]\n"
        f"- **OS**: {system_info['os']}\n"
        f"- **Architecture**: {system_info['architecture']}\n"
        f"- **Host / Node**: {system_info['hostname']}\n"
        f"- **CPU Threads**: {system_info['cpu_threads']}\n"
        f"- **Python Runtime**: {system_info['python_runtime']}\n"
    )


# ==========================================
# Tool 2: Host Process Inspector
# ==========================================
@mcp.tool()
def inspect_host_process(process_name: str = "AggregatorHost.exe") -> str:
    """Queries running processes to verify health and resource status of specific host processes like AggregatorHost.exe."""
    clean_proc = process_name.strip()
    if not clean_proc:
        clean_proc = "AggregatorHost.exe"

    if platform.system() == "Windows":
        try:
            cmd = ["tasklist", "/FI", f"IMAGENAME eq {clean_proc}", "/FO", "LIST"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, stdin=subprocess.DEVNULL)
            output = result.stdout.strip()
            if clean_proc.lower() in output.lower():
                return f"### [MCP Process Health: {clean_proc}]\nStatus: ACTIVE / RUNNING\n```\n{output}\n```"
            else:
                return f"### [MCP Process Health: {clean_proc}]\nStatus: NOT RUNNING\nProcess '{clean_proc}' is not currently active in Windows tasklist."
        except Exception as e:
            return f"Error querying Windows tasklist for '{clean_proc}': {str(e)}"
    else:
        return f"Process inspection for '{clean_proc}' is optimized for Windows host environments."


# ==========================================
# Tool 3: Knowledge Base Search via MCP
# ==========================================
@mcp.tool()
def search_mcp_knowledge(query: str, max_results: int = 3) -> str:
    """Searches documents inside the local knowledge base directory and returns relevant excerpts matching the query."""
    base_path = Path(KNOWLEDGE_DIR)
    if not base_path.exists():
        return f"Knowledge directory '{KNOWLEDGE_DIR}' not found."

    query_terms = [q.lower().strip() for q in query.split() if len(q.strip()) > 2]
    if not query_terms:
        query_terms = [query.lower().strip()]

    supported_extensions = ["*.md", "*.txt", "*.json", "*.rst", "*.csv"]
    all_files: List[Path] = []
    for ext in supported_extensions:
        all_files.extend(base_path.glob(f"**/{ext}"))

    if not all_files:
        return f"No documentation found in knowledge base '{KNOWLEDGE_DIR}'."

    matches = []
    for file_path in all_files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        for idx, p in enumerate(paragraphs):
            p_lower = p.lower()
            score = sum(1 for term in query_terms if term in p_lower)
            if score > 0 or query.lower() in p_lower:
                matches.append({
                    "file": file_path.name,
                    "section": idx + 1,
                    "score": score + (5 if query.lower() in p_lower else 0),
                    "text": p[:450]
                })

    if not matches:
        file_list = ", ".join(f.name for f in all_files[:10])
        return f"No direct matches found for '{query}' via MCP. Indexed documents: {file_list}."

    matches.sort(key=lambda x: x["score"], reverse=True)
    top = matches[:max_results]

    results = [f"### [MCP Knowledge Search: '{query}']\n"]
    for m in top:
        results.append(f"**Source**: `{m['file']}` (Section {m['section']})\n{m['text']}\n")
    return "\n---\n".join(results)


# ==========================================
# Tool 4: Read Complete Document via MCP
# ==========================================
@mcp.tool()
def read_mcp_document(document_name: str) -> str:
    """Reads the full content of a specified document by name from the knowledge base directory."""
    base_path = Path(KNOWLEDGE_DIR)
    target = base_path / document_name
    if not target.exists():
        matches = list(base_path.glob(f"**/{document_name}*"))
        if matches:
            target = matches[0]
        else:
            return f"Document '{document_name}' not found in knowledge directory '{KNOWLEDGE_DIR}'."

    try:
        content = target.read_text(encoding="utf-8", errors="ignore")
        return f"### [MCP Document: {target.name}]\n\n{content}"
    except Exception as e:
        return f"Error reading document '{document_name}': {str(e)}"


# ==========================================
# Tool 5 & 6: Shared Multi-Agent Blackboard via MCP
# ==========================================
def _load_blackboard() -> Dict[str, Any]:
    if BLACKBOARD_FILE.exists():
        try:
            return json.loads(BLACKBOARD_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_blackboard(data: Dict[str, Any]) -> None:
    try:
        BLACKBOARD_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass

@mcp.tool()
def mcp_blackboard_write(key_name: str, value_data: str, session_id: str = "global") -> str:
    """Writes an intermediate fact, verified finding, or hypothesis to the shared multi-agent blackboard."""
    if not key_name or not value_data:
        return "Error: key_name and value_data must be provided."

    data = _load_blackboard()
    session_store = data.setdefault(session_id, {})
    session_store[key_name] = {
        "value": value_data,
        "author": "MCP Agent Collective"
    }
    _save_blackboard(data)
    return f"Successfully saved '{key_name}' to MCP shared blackboard for session '{session_id}'."

@mcp.tool()
def mcp_blackboard_read(key_name: str, session_id: str = "global") -> str:
    """Reads a previously stored fact or observation from the shared multi-agent blackboard."""
    data = _load_blackboard()
    session_store = data.get(session_id, {})
    if key_name in session_store:
        entry = session_store[key_name]
        return f"### [MCP Blackboard: {key_name}]\n- **Value**: {entry['value']}\n- **Author**: {entry['author']}"
    return f"No blackboard entry found for key '{key_name}' in session '{session_id}'."


# ==========================================
# Tool 7: Web Content Fetcher via MCP
# ==========================================
@mcp.tool()
def fetch_url_content(url: str) -> str:
    """Fetches text content from a public web URL or API endpoint for knowledge enrichment."""
    import urllib.request
    import urllib.parse
    import re

    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return f"Invalid URL format: '{url}'. Must start with http:// or https://."

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CrewAI-MCP-Agent/1.0 (Python/Windows)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            # Clean HTML tags if present
            clean_text = re.sub(r"<[^>]+>", " ", content)
            clean_text = re.sub(r"\s+", " ", clean_text).strip()
            return f"### [MCP Fetched Content from {url}]\n\n{clean_text[:2000]}"
    except Exception as e:
        return f"Failed to fetch content from '{url}' via MCP: {str(e)}"


# ==========================================
# Tool 8: Asynchronous DNS Interrogation via adig.exe
# ==========================================
@mcp.tool()
def query_dns_adig(domain: str, record_type: str = "A", server: str = "", extra_flags: str = "") -> str:
    """Interrogates DNS servers for specific record types (A, AAAA, MX, TXT, NS, SOA, PTR, CNAME) using adig.exe."""
    try:
        from tools import AdigDnsQueryTool
        tool = AdigDnsQueryTool()
        return tool._run(domain=domain, record_type=record_type, server=server, extra_flags=extra_flags)
    except Exception as e:
        return f"MCP adig query error: {str(e)}"


# ==========================================
# Tool 9: Asynchronous Hostname Resolution via ahost.exe
# ==========================================
@mcp.tool()
def resolve_host_ahost(host: str, lookup_type: str = "u", server: str = "", domain: str = "", debug: bool = False) -> str:
    """Resolves hostnames to dual-stack IPv4/IPv6 addresses or tests DNS reachability using ahost.exe."""
    try:
        from tools import AhostLookupTool
        tool = AhostLookupTool()
        return tool._run(host=host, lookup_type=lookup_type, server=server, domain=domain, debug=debug)
    except Exception as e:
        return f"MCP ahost lookup error: {str(e)}"


if __name__ == "__main__":
    # Runs FastMCP over standard input/output transport
    mcp.run(transport="stdio")

