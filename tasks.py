"""
Task definitions for the Conversational RAG Crew.
"""

from crewai import Task, Agent

def create_retrieval_task(agent: Agent, user_query: str, chat_history: str = "") -> Task:
    """Creates the task for searching and extracting knowledge from the knowledge base."""
    return Task(
        description=(
            f"Analyze the user's inquiry: '{user_query}'\n"
            f"Recent conversation context:\n{chat_history if chat_history else 'No prior messages.'}\n\n"
            "Search the knowledge base using your retrieval tools to find all relevant facts, "
            "data points, instructions, or policies that address the user's message. "
            "List specific document names and quote or summarize relevant sections."
        ),
        expected_output=(
            "A clear, structured brief containing the retrieved evidence, key facts, "
            "and the specific source document names (e.g., 'company_handbook.md', 'product_manual.md'). "
            "If no information is found, explicitly note that no relevant data was found in the knowledge base."
        ),
        agent=agent
    )

def create_aggregation_host_task(agent: Agent, user_query: str, chat_history: str = "") -> Task:
    """Creates the task for aggregating, verifying, and cross-examining retrieved knowledge and host diagnostics."""
    return Task(
        description=(
            f"The user query is: '{user_query}'\n"
            f"Recent conversation context:\n{chat_history if chat_history else 'No prior messages.'}\n\n"
            "Review the findings from the Knowledge Retrieval Specialist and perform deep aggregation:\n"
            "1. Cross-reference facts across documents, deduplicating repetitive points and reconciling any discrepancies.\n"
            "2. If the user's query relates to host system status, environment specs, Windows AggregatorHost process health, "
            "or DNS/network diagnostics, use the Aggregator Host Status Inspector, ADig DNS Query Tool (adig.exe), or AHost Lookup Tool (ahost.exe) "
            "to collect live host and network diagnostics.\n"
            "3. Compile an authoritative, structured aggregation brief with verified document sources, eliminating any ungrounded assertions."
        ),
        expected_output=(
            "A comprehensive, structured aggregation dossier containing:\n"
            "- Consolidated factual findings with verified document sources (e.g., 'company_handbook.md', 'product_manual.md').\n"
            "- Resolution of any ambiguous or conflicting statements.\n"
            "- Relevant host system diagnostics, AggregatorHost telemetry, or c-ares DNS/network diagnostic results if queried.\n"
            "- A synthesized factual foundation ready for the Conversational Synthesizer."
        ),
        agent=agent
    )

def create_conversational_task(agent: Agent, user_query: str, chat_history: str = "") -> Task:
    """Creates the task for synthesizing the conversational answer for the user."""
    return Task(
        description=(
            f"The user asked: '{user_query}'\n"
            f"Recent conversation context:\n{chat_history if chat_history else 'No prior messages.'}\n\n"
            "Review the aggregated facts, validated evidence, and source dossier compiled by the Aggregator Host Specialist. "
            "Craft a warm, conversational, well-formatted response directly answering the user. "
            "Guidelines:\n"
            "- Speak naturally and directly to the user.\n"
            "- Ground all factual statements in the aggregated sources.\n"
            "- Include friendly citations (e.g., *Source: company_handbook.md* or *Source: Aggregator Host Diagnostics*).\n"
            "- If the knowledge base lacked relevant information, answer graciously, state that "
            "it is outside the current indexed documentation, and suggest what topics are available."
        ),
        expected_output=(
            "The final, complete conversational response ready to be delivered to the user, "
            "formatted with markdown highlights, bullet points if helpful, and citations."
        ),
        agent=agent
    )


def create_json_aggregation_task(agent: Agent, user_query: str, chat_history: str = "") -> Task:
    """Creates an aggregation task that produces structured JSON output using Gemini JSON mode."""
    return Task(
        description=(
            f"The user query is: '{user_query}'\n"
            f"Recent conversation context:\n{chat_history if chat_history else 'No prior messages.'}\n\n"
            "Review all findings from the Knowledge Retrieval Specialist and produce a comprehensive "
            "aggregation in **strict JSON format**.\n\n"
            "Your JSON output MUST follow this exact schema:\n"
            "{\n"
            '  "query": "<the original user query>",\n'
            '  "confidence": <float 0.0-1.0>,\n'
            '  "sources": [\n'
            "    {\n"
            '      "document": "<filename>",\n'
            '      "relevant_excerpts": ["<excerpt1>", "<excerpt2>"],\n'
            '      "relevance_score": <float 0.0-1.0>\n'
            "    }\n"
            "  ],\n"
            '  "aggregated_facts": ["<fact1>", "<fact2>"],\n'
            '  "conflicts": ["<conflict description if any>"],\n'
            '  "host_diagnostics": null,\n'
            '  "summary": "<concise factual summary>"\n'
            "}\n\n"
            "If host diagnostics are requested, populate the host_diagnostics field with relevant data."
        ),
        expected_output=(
            "A valid JSON object conforming to the schema above, containing aggregated facts, "
            "source documents with relevance scores, any conflicts found, and a concise summary."
        ),
        agent=agent,
        output_json=True
    )

