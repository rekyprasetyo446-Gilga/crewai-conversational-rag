"""
Agent definitions for the Conversational RAG Crew.
Integrated with Model Context Protocol (MCP) server support for Gemini 3.8 Flash.
"""

from typing import Optional, Any, List, Union
from crewai import Agent
from crewai.mcp import MCPServerConfig
from tools import (
    AdSenseTransactionResolverTool,
    KnowledgeSearchTool,
    ListKnowledgeDocumentsTool,
    KnowledgeReadDocumentTool,
    AggregatorHostStatusTool,
    MySQLQueryTool,
    MySQLBlackboardTool,
    FTPStorageTool,
    EmailNotificationTool,
    AdigDnsQueryTool,
    AhostLookupTool,
)
from mcp_manager import (
    get_agent_mcps,
    MCPHostTelemetryTool,
    MCPProcessInspectorTool,
    MCPKnowledgeSearchTool,
    MCPDocumentReaderTool,
    MCPBlackboardWriteTool,
    MCPBlackboardReadTool,
    MCPURLFetcherTool,
    MCPAdigQueryTool,
    MCPAhostLookupTool,
)


def get_retriever_agent(
    llm: Optional[Any] = None,
    mcps: Optional[List[Union[str, MCPServerConfig]]] = None,
    include_direct_mcp_tools: bool = True,
    allow_delegation: bool = True
) -> Agent:
    """Creates the Knowledge Retrieval Specialist Agent with MCP connectivity."""
    agent_mcps = mcps if mcps is not None else get_agent_mcps("retriever")

    tools = [
        KnowledgeSearchTool(),
        ListKnowledgeDocumentsTool(),
        KnowledgeReadDocumentTool(),
        AhostLookupTool(),
    ]
    if include_direct_mcp_tools:
        tools.extend([
            MCPKnowledgeSearchTool(),
            MCPDocumentReaderTool(),
            MCPAhostLookupTool(),
        ])

    return Agent(
        role="Knowledge Retrieval Specialist",
        goal="Query the knowledge base, verify host reachability via ahost, and query MCP endpoints to retrieve accurate, verified facts and excerpts to answer user inquiries.",
        backstory=(
            "You are a dedicated information retrieval expert. You navigate documentation, "
            "technical manuals, company policies, FAQs, and perform hostname lookups with precision using native retrieval and "
            "Model Context Protocol (MCP) tools. You ensure that all information is strictly grounded in the knowledge documents, noting exact sources."
        ),
        tools=tools,
        mcps=agent_mcps if agent_mcps else None,
        llm=llm,
        verbose=True,
        allow_delegation=allow_delegation
    )


def get_aggregator_host_agent(
    llm: Optional[Any] = None,
    mcps: Optional[List[Union[str, MCPServerConfig]]] = None,
    include_direct_mcp_tools: bool = True,
    allow_delegation: bool = True
) -> Agent:
    """Creates the Aggregator Host Specialist Agent with MCP telemetry, DNS diagnostics, and shared memory tools."""
    agent_mcps = mcps if mcps is not None else get_agent_mcps("aggregator_host")

    tools = [
        KnowledgeSearchTool(),
        KnowledgeReadDocumentTool(),
        AggregatorHostStatusTool(),
        AdigDnsQueryTool(),
        AhostLookupTool(),
        MySQLQueryTool(),
        MySQLBlackboardTool(),
        FTPStorageTool(),
        EmailNotificationTool(),
    ]
    if include_direct_mcp_tools:
        tools.extend([
            MCPHostTelemetryTool(),
            MCPProcessInspectorTool(),
            MCPBlackboardWriteTool(),
            MCPBlackboardReadTool(),
            MCPAdigQueryTool(),
            MCPAhostLookupTool(),
        ])

    return Agent(
        role="Aggregator Host Specialist",
        goal=(
            "Aggregate, cross-examine, and synthesize knowledge excerpts from retrieval, MySQL shared memory/database, "
            "FileZilla FTP shared storage, and local host diagnostics via Model Context Protocol (MCP), resolving conflicts and compiling consolidated briefings."
        ),
        backstory=(
            "You are the central Aggregator Host Coordinator in this multi-agent collective. "
            "You scrutinize raw findings collected by the retrieval partner, eliminate redundancy, "
            "reconcile contradictory information, and verify source anchors. Additionally, you "
            "inspect local host system telemetry and processes via MCP, query/write the shared MySQL and MCP blackboard, "
            "manage shared artifact storage on the XAMPP FileZilla FTP server, and dispatch email alerts via Mercury Mail."
        ),
        tools=tools,
        mcps=agent_mcps if agent_mcps else None,
        llm=llm,
        verbose=True,
        allow_delegation=allow_delegation
    )


def get_conversational_agent(
    llm: Optional[Any] = None,
    mcps: Optional[List[Union[str, MCPServerConfig]]] = None,
    include_direct_mcp_tools: bool = True,
    allow_delegation: bool = True
) -> Agent:
    """Creates the Conversational Synthesizer & Memory Coordinator Agent with MCP tools."""
    agent_mcps = mcps if mcps is not None else get_agent_mcps("conversationalist")

    tools = [
        EmailNotificationTool(),
    ]
    if include_direct_mcp_tools:
        tools.extend([
            MCPURLFetcherTool(),
        ])

    return Agent(
        role="Conversational Synthesizer",
        goal="Synthesize retrieved knowledge into warm, helpful, and natural conversational responses, maintaining chat flow, citing sources, and utilizing MCP web fetch tools when needed.",
        backstory=(
            "You are an empathetic, articulate AI companion and advisor. You take raw facts "
            "and findings provided by your retrieval and aggregator partners and weave them into a smooth, "
            "engaging dialogue. You speak directly to the user, acknowledge previous conversation "
            "context, clearly cite source documents, and can dispatch executive email briefings or query external MCP endpoints when requested."
        ),
        tools=tools,
        mcps=agent_mcps if agent_mcps else None,
        llm=llm,
        verbose=True,
        allow_delegation=allow_delegation
    )
