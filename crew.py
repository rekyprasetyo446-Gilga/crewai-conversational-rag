"""
Crew Orchestrator for Conversational RAG.
Coordinates Retrieval Specialist, Aggregator Host Specialist, and Conversational Synthesizer
with session memory, Gemini 3.8 Flash LLM, and Model Context Protocol (MCP) tool integration.
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

from crewai import Crew, Process, LLM
from crewai.mcp import MCPServerConfig
from agents import get_retriever_agent, get_aggregator_host_agent, get_conversational_agent
from tasks import create_retrieval_task, create_aggregation_host_task, create_conversational_task
from mcp_manager import get_agent_mcps, get_mcp_summary


class ConversationalRAGCrew:
    """Multi-agent Conversational RAG orchestrator with memory management and MCP tool support."""

    DEFAULT_MODEL = "gemini/gemini-3.8-flash"

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        verbose: bool = True,
        mcp_enabled: bool = True,
        mcp_config_path: Optional[Union[str, Path]] = None,
    ):
        self.verbose = verbose
        self.chat_history: List[Dict[str, str]] = []
        self.mcp_enabled = mcp_enabled
        self.mcp_config_path = Path(mcp_config_path) if mcp_config_path else None
        
        # Determine model and API credentials
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        env_model = os.getenv("MODEL", self.DEFAULT_MODEL)
        chosen_model = model or env_model

        # Normalize Gemini model string format (e.g. gemini-3.8-flash -> gemini/gemini-3.8-flash)
        if chosen_model.startswith("gemini-") and not chosen_model.startswith("gemini/"):
            chosen_model = f"gemini/{chosen_model}"

        if api_key:
            self.api_key = api_key
            self.model = chosen_model
        elif gemini_key and gemini_key != "your_gemini_api_key_here":
            self.api_key = gemini_key
            self.model = chosen_model
            if not self.model.startswith("gemini/"):
                self.model = f"gemini/{self.model}"
        elif openai_key:
            self.api_key = openai_key
            self.model = model or os.getenv("MODEL", "gpt-4o-mini")
        else:
            self.api_key = None
            self.model = chosen_model

        self.llm = self._initialize_llm()
        self.json_llm = self._initialize_json_llm()

        # Resolve MCP configurations for multiple agents
        self._init_mcp_configs()

    def _init_mcp_configs(self):
        """Initializes per-agent MCP server configurations."""
        if self.mcp_enabled:
            self.agent_mcps = {
                "retriever": get_agent_mcps("retriever", self.mcp_config_path),
                "aggregator_host": get_agent_mcps("aggregator_host", self.mcp_config_path),
                "conversationalist": get_agent_mcps("conversationalist", self.mcp_config_path),
            }
        else:
            self.agent_mcps = {
                "retriever": [],
                "aggregator_host": [],
                "conversationalist": [],
            }

    def get_mcp_status(self) -> Dict[str, Any]:
        """Returns diagnostic report of registered MCP servers and per-agent mappings."""
        summary = get_mcp_summary(self.mcp_config_path)
        summary["agent_assignments"] = {
            role: len(configs) for role, configs in self.agent_mcps.items()
        }
        return summary

    def _initialize_llm(self) -> Optional[LLM]:
        """Initializes the CrewAI LLM instance."""
        if not self.api_key:
            return None
        try:
            return LLM(model=self.model, api_key=self.api_key)
        except Exception as e:
            print(f"[Warning] Failed to initialize CrewAI LLM: {e}")
            return None

    def _initialize_json_llm(self) -> Optional[LLM]:
        """Initializes a CrewAI LLM instance configured for JSON structured output."""
        if not self.api_key:
            return None
        try:
            return LLM(
                model=self.model,
                api_key=self.api_key,
                response_format={"type": "json_object"},
            )
        except Exception:
            try:
                return LLM(
                    model=self.model,
                    api_key=self.api_key,
                )
            except Exception as e:
                print(f"[Warning] Failed to initialize JSON LLM: {e}")
                return None

    def format_history(self, max_turns: int = 5) -> str:
        """Formats the last N conversational turns for context injection."""
        if not self.chat_history:
            return "No previous conversation history."
        
        recent = self.chat_history[-max_turns:]
        lines = []
        for turn in recent:
            role = "User" if turn["role"] == "user" else "Assistant"
            lines.append(f"{role}: {turn['content']}")
        return "\n".join(lines)

    def ask(self, user_query: str) -> str:
        """Runs the multi-agent pipeline to respond to the user query with MCP tools enabled."""
        if not self.llm:
            return (
                "⚠️ **No API Key Configured**\n\n"
                "Please configure your `GEMINI_API_KEY` (or `OPENAI_API_KEY`) in the `.env` file.\n"
                "- Get a free Gemini API key: https://aistudio.google.com/app/apikey\n"
                "- Add it to `.env`: `GEMINI_API_KEY=your_actual_key`"
            )

        # Build context
        history_context = self.format_history()

        # Instantiate agents with MCP configurations
        retriever = get_retriever_agent(
            llm=self.llm,
            mcps=self.agent_mcps.get("retriever") if self.mcp_enabled else None,
            allow_delegation=True
        )
        aggregator_host = get_aggregator_host_agent(
            llm=self.llm,
            mcps=self.agent_mcps.get("aggregator_host") if self.mcp_enabled else None
        )
        conversationalist = get_conversational_agent(
            llm=self.llm,
            mcps=self.agent_mcps.get("conversationalist") if self.mcp_enabled else None
        )

        # Create sequential tasks
        t1 = create_retrieval_task(retriever, user_query, history_context)
        t2 = create_aggregation_host_task(aggregator_host, user_query, history_context)
        t3 = create_conversational_task(conversationalist, user_query, history_context)

        # Assemble Crew
        crew = Crew(
            agents=[retriever, aggregator_host, conversationalist],
            tasks=[t1, t2, t3],
            process=Process.sequential,
            verbose=self.verbose
        )

        try:
            result = crew.kickoff()
            response_text = str(result)
        except Exception as e:
            response_text = f"An error occurred while running the agents: {str(e)}"

        # Save to session memory
        self.chat_history.append({"role": "user", "content": user_query})
        self.chat_history.append({"role": "assistant", "content": response_text})

        return response_text

    async def ask_async(self, user_query: str) -> str:
        """
        Runs the multi-agent pipeline asynchronously awaiting agent task executions.
        Leverages `await agent.aexecute_task(...)` for non-blocking task execution.
        """
        if not self.llm:
            return (
                "⚠️ **No API Key Configured**\n\n"
                "Please configure your `GEMINI_API_KEY` (or `OPENAI_API_KEY`) in the `.env` file.\n"
                "- Get a free Gemini API key: https://aistudio.google.com/app/apikey\n"
                "- Add it to `.env`: `GEMINI_API_KEY=your_actual_key`"
            )

        # Build context
        history_context = self.format_history()

        # Instantiate agents with MCP configurations
        retriever = get_retriever_agent(
            llm=self.llm,
            mcps=self.agent_mcps.get("retriever") if self.mcp_enabled else None,
            allow_delegation=True
        )
        aggregator_host = get_aggregator_host_agent(
            llm=self.llm,
            mcps=self.agent_mcps.get("aggregator_host") if self.mcp_enabled else None
        )
        conversationalist = get_conversational_agent(
            llm=self.llm,
            mcps=self.agent_mcps.get("conversationalist") if self.mcp_enabled else None
        )

        # Create sequential tasks
        t1 = create_retrieval_task(retriever, user_query, history_context)
        t2 = create_aggregation_host_task(aggregator_host, user_query, history_context)
        t3 = create_conversational_task(conversationalist, user_query, history_context)

        try:
            # Step 1: Asynchronously await retriever executing retrieval task
            t1_output = await retriever.aexecute_task(task=t1, tools=retriever.tools)

            # Step 2: Asynchronously await aggregator host executing aggregation task with retrieval context
            t2_output = await aggregator_host.aexecute_task(task=t2, context=str(t1_output), tools=aggregator_host.tools)

            # Step 3: Asynchronously await conversationalist executing synthesis task with aggregated context
            t3_output = await conversationalist.aexecute_task(task=t3, context=str(t2_output), tools=conversationalist.tools)

            response_text = str(t3_output)
        except Exception as e:
            # Fallback to crew async kickoff if individual agent execution encountered an issue
            try:
                crew = Crew(
                    agents=[retriever, aggregator_host, conversationalist],
                    tasks=[t1, t2, t3],
                    process=Process.sequential,
                    verbose=self.verbose
                )
                result = await crew.kickoff_async()
                response_text = str(result)
            except Exception as fallback_e:
                response_text = f"An error occurred while running the agents: {str(e)} (Fallback: {str(fallback_e)})"

        # Save to session memory
        self.chat_history.append({"role": "user", "content": user_query})
        self.chat_history.append({"role": "assistant", "content": response_text})

        return response_text

    def clear_memory(self):
        """Clears the conversational memory history."""
        self.chat_history = []
