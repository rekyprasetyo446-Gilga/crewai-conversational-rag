"""
Agent definitions for the Conversational RAG Crew.
"""

from typing import Optional, Any
from crewai import Agent
from tools import (
    KnowledgeSearchTool,
    ListKnowledgeDocumentsTool,
    KnowledgeReadDocumentTool,
    AggregatorHostStatusTool,
    MySQLQueryTool,
    MySQLBlackboardTool,
    FTPStorageTool,
    EmailNotificationTool,
)

def get_retriever_agent(llm: Optional[Any] = None) -> Agent:
    """Creates the Knowledge Retrieval Specialist Agent."""
    return Agent(
        role="Knowledge Retrieval Specialist",
        goal="Query the knowledge base to retrieve accurate, verified facts and excerpts to answer user inquiries.",
        backstory=(
            "You are a dedicated information retrieval expert. You navigate documentation, "
            "technical manuals, company policies, and FAQs with precision. You ensure that "
            "all information is strictly grounded in the knowledge documents, noting exact sources."
        ),
        tools=[
            KnowledgeSearchTool(),
            ListKnowledgeDocumentsTool(),
            KnowledgeReadDocumentTool()
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

def get_aggregator_host_agent(llm: Optional[Any] = None) -> Agent:
    """Creates the Aggregator Host Specialist Agent."""
    return Agent(
        role="Aggregator Host Specialist",
        goal=(
            "Aggregate, cross-examine, and synthesize knowledge excerpts from retrieval, MySQL shared memory/database, "
            "FileZilla FTP shared storage, and local host diagnostics, resolving conflicts and compiling consolidated briefings."
        ),
        backstory=(
            "You are the central Aggregator Host Coordinator in this multi-agent collective. "
            "You scrutinize raw findings collected by the retrieval partner, eliminate redundancy, "
            "reconcile contradictory information, and verify source anchors. Additionally, you "
            "inspect local host system telemetry, query/write the shared XAMPP MySQL blackboard, "
            "manage shared artifact storage on the XAMPP FileZilla FTP server, and dispatch email alerts via Mercury Mail."
        ),
        tools=[
            KnowledgeSearchTool(),
            KnowledgeReadDocumentTool(),
            AggregatorHostStatusTool(),
            MySQLQueryTool(),
            MySQLBlackboardTool(),
            FTPStorageTool(),
            EmailNotificationTool(),
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

def get_conversational_agent(llm: Optional[Any] = None) -> Agent:
    """Creates the Conversational Synthesizer & Memory Coordinator Agent."""
    return Agent(
        role="Conversational Synthesizer",
        goal="Synthesize retrieved knowledge into warm, helpful, and natural conversational responses, maintaining chat flow and citing sources.",
        backstory=(
            "You are an empathetic, articulate AI companion and advisor. You take raw facts "
            "and findings provided by your retrieval partner and weave them into a smooth, "
            "engaging dialogue. You speak directly to the user, acknowledge previous conversation "
            "context, clearly cite source documents, and can dispatch executive email briefings via Mercury Mail when requested."
        ),
        tools=[
            EmailNotificationTool(),
        ],
        llm=llm,
        verbose=True,
        allow_delegation=True
    )

