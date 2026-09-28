"""
Unit tests for Model Context Protocol (MCP) server integration and Gemini 3.8 Flash configuration.
"""

import os
import sys
from pathlib import Path
import pytest

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_manager import (
    load_mcp_config,
    build_mcp_server_config,
    get_agent_mcps,
    get_all_mcp_configs,
    get_mcp_summary,
    get_local_fastmcp_tools,
    MCPHostTelemetryTool,
    MCPProcessInspectorTool,
    MCPKnowledgeSearchTool,
    MCPDocumentReaderTool,
    MCPBlackboardWriteTool,
    MCPBlackboardReadTool,
)
from crewai.mcp import MCPServerStdio, MCPServerHTTP, MCPServerSSE
from agents import get_retriever_agent, get_aggregator_host_agent, get_conversational_agent
from crew import ConversationalRAGCrew
from mcp_server import (
    get_system_telemetry,
    inspect_host_process,
    search_mcp_knowledge,
    read_mcp_document,
    mcp_blackboard_write,
    mcp_blackboard_read,
    fetch_url_content,
)


def test_mcp_config_loading():
    """Verify that mcp_servers.json is parsed and contains expected servers."""
    cfg = load_mcp_config()
    assert cfg.get("enabled") is True
    assert "servers" in cfg
    assert "local_fastmcp" in cfg["servers"]

    server_data = cfg["servers"]["local_fastmcp"]
    assert server_data["transport"] == "stdio"
    assert "retriever" in server_data["agents"]
    assert "aggregator_host" in server_data["agents"]
    assert "conversationalist" in server_data["agents"]


def test_build_mcp_server_config():
    """Test instantiating Stdio, HTTP, and SSE configs."""
    # Stdio
    stdio_cfg = build_mcp_server_config("test_stdio", {
        "transport": "stdio",
        "command": "python",
        "args": ["mcp_server.py"]
    })
    assert isinstance(stdio_cfg, MCPServerStdio)
    assert stdio_cfg.command == sys.executable
    assert any("mcp_server.py" in str(a) for a in stdio_cfg.args)

    # HTTP
    http_cfg = build_mcp_server_config("test_http", {
        "transport": "http",
        "url": "https://example.com/mcp"
    })
    assert isinstance(http_cfg, MCPServerHTTP)
    assert http_cfg.url == "https://example.com/mcp"

    # SSE
    sse_cfg = build_mcp_server_config("test_sse", {
        "transport": "sse",
        "url": "https://example.com/mcp/sse"
    })
    assert isinstance(sse_cfg, MCPServerSSE)
    assert sse_cfg.url == "https://example.com/mcp/sse"


def test_get_agent_mcps():
    """Verify per-agent MCP configs are returned properly."""
    retriever_mcps = get_agent_mcps("retriever")
    assert len(retriever_mcps) >= 1
    assert isinstance(retriever_mcps[0], MCPServerStdio)

    aggregator_mcps = get_agent_mcps("aggregator_host")
    assert len(aggregator_mcps) >= 1

    synth_mcps = get_agent_mcps("conversationalist")
    assert len(synth_mcps) >= 1


def test_fastmcp_server_tools():
    """Test FastMCP server tool execution functions."""
    # Telemetry
    telemetry = get_system_telemetry()
    assert "MCP Host Telemetry" in telemetry
    assert "Python Runtime" in telemetry

    # Process Inspection
    proc_info = inspect_host_process("AggregatorHost.exe")
    assert "MCP Process Health" in proc_info

    # Blackboard Write & Read
    write_res = mcp_blackboard_write(
        key_name="test_key_mcp",
        value_data="MCP Verification 2026",
        session_id="test_session"
    )
    assert "Successfully saved" in write_res

    read_res = mcp_blackboard_read(
        key_name="test_key_mcp",
        session_id="test_session"
    )
    assert "MCP Verification 2026" in read_res

    # Document & Knowledge Search
    search_res = search_mcp_knowledge("support")
    assert "MCP Knowledge Search" in search_res or "No documentation found" in search_res

    # Invalid URL handling
    invalid_url = fetch_url_content("not-a-valid-url")
    assert "Invalid URL" in invalid_url


def test_crewai_basetool_mcp_adapters():
    """Test that FastMCP tools wrapped as CrewAI BaseTools execute correctly."""
    telemetry_tool = MCPHostTelemetryTool()
    output = telemetry_tool._run()
    assert "MCP Host Telemetry" in output

    blackboard_writer = MCPBlackboardWriteTool()
    w_out = blackboard_writer._run(key_name="base_tool_test", value_data="BaseToolOK", session_id="test_s")
    assert "Successfully saved" in w_out

    blackboard_reader = MCPBlackboardReadTool()
    r_out = blackboard_reader._run(key_name="base_tool_test", session_id="test_s")
    assert "BaseToolOK" in r_out

    all_tools = get_local_fastmcp_tools()
    assert len(all_tools) == 7


def test_agent_initialization_with_mcps():
    """Verify that multi-agent team instances carry MCP configurations and tools."""
    retriever = get_retriever_agent()
    assert retriever.role == "Knowledge Retrieval Specialist"
    assert retriever.mcps is not None
    assert len(retriever.mcps) >= 1
    tool_names = [t.name for t in retriever.tools]
    assert "MCP Knowledge Base Search" in tool_names

    aggregator = get_aggregator_host_agent()
    assert aggregator.role == "Aggregator Host Specialist"
    assert aggregator.mcps is not None
    agg_tool_names = [t.name for t in aggregator.tools]
    assert "MCP Host Telemetry Inspector" in agg_tool_names

    conversationalist = get_conversational_agent()
    assert conversationalist.role == "Conversational Synthesizer"
    assert conversationalist.mcps is not None
    conv_tool_names = [t.name for t in conversationalist.tools]
    assert "MCP URL Content Fetcher" in conv_tool_names


def test_crew_gemini_38_model_and_mcp_status():
    """Verify ConversationalRAGCrew defaults to Gemini 3.8 Flash and exposes MCP status."""
    crew = ConversationalRAGCrew(verbose=False)
    # Check default model configuration
    assert "gemini-3.8-flash" in crew.model

    # Check model normalization
    custom_crew = ConversationalRAGCrew(model="gemini-3.8-flash", verbose=False)
    assert custom_crew.model == "gemini/gemini-3.8-flash"

    # Check MCP status
    mcp_status = crew.get_mcp_status()
    assert mcp_status["enabled"] is True
    assert mcp_status["total_servers"] >= 1
    assert "agent_assignments" in mcp_status
    assert mcp_status["agent_assignments"]["retriever"] >= 1
    assert mcp_status["agent_assignments"]["aggregator_host"] >= 1
    assert mcp_status["agent_assignments"]["conversationalist"] >= 1
