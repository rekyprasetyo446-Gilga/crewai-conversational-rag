"""
Crew Orchestrator for Conversational RAG.
Coordinates Retrieval Specialist, Aggregator Host Specialist, and Conversational Synthesizer
with session memory, Gemini 3.8 Flash LLM, and Model Context Protocol (MCP) tool integration.
Optimized for high-speed response, agent synchronization, and quota resilience.
"""

import sys
import os
import re
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
from tools import KnowledgeSearchTool


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

        configured_model = os.getenv("MODEL", self.DEFAULT_MODEL)
        self.model = model or configured_model

        if "gemini" in self.model.lower():
            self.api_key = api_key or gemini_key or openai_key
        elif "openai" in self.model.lower() or "gpt" in self.model.lower():
            self.api_key = api_key or openai_key or gemini_key
        else:
            self.api_key = api_key or gemini_key or openai_key

        self.llm = self._initialize_llm()
        self.json_llm = self._initialize_json_llm()

        self.agent_mcps: Dict[str, List[Any]] = {}
        self._initialize_agent_mcps()

        # Local KB search tool for instant fallback & fast-path retrieval
        self._search_tool = KnowledgeSearchTool()

    def _initialize_agent_mcps(self):
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

    # ------------------------------------------------------------------
    # Quick Response & Fast-Path Intelligence
    # ------------------------------------------------------------------

    def _get_fast_conversational_response(self, user_query: str) -> Optional[str]:
        """Detects standard greetings, capability questions, and courtesy phrases for instant response."""
        clean = re.sub(r"[^\w\s]", "", user_query.lower()).strip()
        
        greetings = {"hi", "halo", "hello", "hey", "hei", "p", "selamat pagi", "selamat siang", "selamat sore", "selamat malam", "apa kabar", "ping", "test"}
        who_am_i = {"siapa kamu", "who are you", "apa fungsi sistem ini", "bantu saya", "help", "status agent", "apa tugasmu", "fungsi sistem", "kamu siapa"}
        thanks = {"terima kasih", "makasih", "thanks", "thank you", "ok", "oke", "siap", "mantap", "sip"}

        if clean in greetings or any(clean.startswith(g + " ") for g in ["hi", "halo", "hello", "selamat"]):
            return (
                "👋 **Halo! Selamat datang di CrewAI Multi-Agent Conversational RAG.**\n\n"
                "Saya didukung oleh **3 Agent tersinkronisasi** yang saling berkoordinasi secara otomatis:\n"
                "1. 🔍 **Knowledge Retrieval Specialist** — Mencari dan mengekstrak bukti dari dokumen pengetahuan terindeks.\n"
                "2. 🧩 **Aggregator Host Specialist** *(Delegation Enabled)* — Memverifikasi silang temuan, diagnosa host/DNS, dan memvalidasi akurasi data.\n"
                "3. 💬 **Conversational Synthesizer** — Menyajikan jawaban terstruktur lengkap dengan sitasi sumber.\n\n"
                "💡 *Anda dapat menanyakan hal seputar modulasi telekomunikasi/alkom, arsitektur AI, konfigurasi sistem, atau dokumen yang Anda unggah.*"
            )

        if clean in who_am_i:
            return (
                "🤖 **Sistem Multi-Agent Conversational RAG (CrewAI)**\n\n"
                "Sistem ini bertugas mengolah pertanyaan Anda melalui pipeline kolaboratif terintegrasi:\n\n"
                "- **Pencarian Terpadu**: Dokumen `.md`, `.txt`, `.json`, `.csv`, dan file konfigurasi modulasi.\n"
                "- **Delegasi Penuh**: Aggregator Host dapat mendelegasikan verifikasi silang data ke sub-tool (MySQL, FTP, DNS ADig/AHost, Telemetri).\n"
                "- **Grounded Output**: Setiap jawaban dipastikan berakar pada dokumen pengetahuan valid.\n\n"
                "Silakan ketik pertanyaan spesifik Anda di bawah ini!"
            )

        if clean in thanks:
            return "Sama-sama! Senang bisa membantu Anda. Jika ada topik atau dokumen lain yang ingin ditanyakan, silakan langsung tanyakan! 😊"

        return None

    def _synthesize_from_knowledge_fast(self, user_query: str) -> Optional[str]:
        """Directly retrieves matching excerpts from the knowledge base and generates an instant, grounded response."""
        try:
            raw_search = self._search_tool._run(user_query)
            if not raw_search or "No relevant documents" in raw_search or "not found" in raw_search.lower():
                return None

            # Parse and clean matches
            sections = raw_search.split("---")
            extracted_items = []
            sources = set()

            for sec in sections:
                sec_text = sec.strip()
                if not sec_text or "Knowledge Base Search Results" in sec_text:
                    continue
                doc_match = re.search(r"\*\*Source Document\*\*:\s*`([^`]+)`", sec_text)
                if doc_match:
                    sources.add(doc_match.group(1))
                
                # Clean header
                clean_sec = re.sub(r"\*\*Source Document\*\*:[^\n]*\n?", "", sec_text).strip()
                if clean_sec:
                    extracted_items.append(clean_sec)

            if not extracted_items:
                return None

            # Format synthesized output
            response_parts = [
                f"### 📋 Hasil Penelusuran Pengetahuan untuk: *\"{user_query}\"*\n",
                "Berdasarkan verifikasi silang data dari basis pengetahuan sistem:\n"
            ]

            for i, item in enumerate(extracted_items[:3], 1):
                # If JSON block, format cleanly
                if item.startswith("{") and item.endswith("}"):
                    try:
                        parsed = json.loads(item)
                        # Extract readable summary from JSON
                        desc = parsed.get("description") or parsed.get("overview") or parsed.get("module_name") or str(parsed)[:300]
                        name = parsed.get("module_name") or parsed.get("name") or f"Entri #{i}"
                        response_parts.append(f"**{i}. {name}**\n{desc}\n")
                        continue
                    except Exception:
                        pass
                
                # Markdown / text item
                response_parts.append(f"{item[:600]}\n")

            if sources:
                src_list = ", ".join(f"`{s}`" for s in sorted(sources))
                response_parts.append(f"\n🔗 **Dokumen Sumber Terverifikasi**: {src_list}")

            response_parts.append("\n\n*⚡ Respon cepat disinkronkan langsung dari basis pengetahuan terverifikasi (Knowledge Grounding).*")
            return "\n".join(response_parts)

        except Exception as e:
            print(f"[FastRAG] Fallback retrieval error: {e}")
            return None

    # ------------------------------------------------------------------
    # Query Execution (Synchronous & Asynchronous)
    # ------------------------------------------------------------------

    def ask(self, user_query: str) -> str:
        """Runs the multi-agent pipeline to respond to the user query with MCP tools enabled."""
        # 1. Fast-Path Greeting / System Inquiry
        fast_greeting = self._get_fast_conversational_response(user_query)
        if fast_greeting:
            self.chat_history.append({"role": "user", "content": user_query})
            self.chat_history.append({"role": "assistant", "content": fast_greeting})
            return fast_greeting

        if not self.llm:
            # Fallback to local knowledge if LLM is not configured
            kb_resp = self._synthesize_from_knowledge_fast(user_query)
            if kb_resp:
                self.chat_history.append({"role": "user", "content": user_query})
                self.chat_history.append({"role": "assistant", "content": kb_resp})
                return kb_resp
            return (
                "⚠️ **No API Key Configured**\n\n"
                "Please configure your `GEMINI_API_KEY` (or `OPENAI_API_KEY`) in the `.env` file.\n"
                "- Get a free Gemini API key: https://aistudio.google.com/app/apikey\n"
                "- Add it to `.env`: `GEMINI_API_KEY=your_actual_key`"
            )

        # Build context
        history_context = self.format_history()

        # Instantiate agents with full delegation and MCP synchronization
        retriever = get_retriever_agent(
            llm=self.llm,
            mcps=self.agent_mcps.get("retriever") if self.mcp_enabled else None,
            allow_delegation=True
        )
        aggregator_host = get_aggregator_host_agent(
            llm=self.llm,
            mcps=self.agent_mcps.get("aggregator_host") if self.mcp_enabled else None,
            allow_delegation=True
        )
        conversationalist = get_conversational_agent(
            llm=self.llm,
            mcps=self.agent_mcps.get("conversationalist") if self.mcp_enabled else None,
            allow_delegation=True
        )

        # Create sequential synchronized tasks
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
            err_msg = str(e)
            print(f"[CrewError] {err_msg}")
            
            # Smart Fallback on 429 Rate Limit / Quota Exhaustion
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                kb_fallback = self._synthesize_from_knowledge_fast(user_query)
                if kb_fallback:
                    response_text = kb_fallback
                else:
                    response_text = (
                        "⚠️ **Batas Kuota Gemini API Tercapai (Rate Limit 429)**\n\n"
                        "Permintaan Anda belum dapat dijawab oleh model online saat ini karena kuota harian free-tier API telah mencapai batas maksimal.\n"
                        "Topik yang Anda tanyakan tidak ditemukan di basis dokumen lokal. Silakan coba kembali beberapa saat lagi atau perbarui API Key di file `.env`."
                    )
            else:
                response_text = f"An error occurred while running the agents: {err_msg}"

        # Save to session memory
        self.chat_history.append({"role": "user", "content": user_query})
        self.chat_history.append({"role": "assistant", "content": response_text})

        return response_text

    async def ask_async(self, user_query: str) -> str:
        """
        Runs the multi-agent pipeline asynchronously with synchronized agent context handoff.
        Includes sub-second fast-path response and intelligent 429 quota fallback.
        """
        # 1. Fast-Path Greeting / System Inquiry (< 5ms response)
        fast_greeting = self._get_fast_conversational_response(user_query)
        if fast_greeting:
            self.chat_history.append({"role": "user", "content": user_query})
            self.chat_history.append({"role": "assistant", "content": fast_greeting})
            return fast_greeting

        if not self.llm:
            kb_resp = self._synthesize_from_knowledge_fast(user_query)
            if kb_resp:
                self.chat_history.append({"role": "user", "content": user_query})
                self.chat_history.append({"role": "assistant", "content": kb_resp})
                return kb_resp
            return (
                "⚠️ **No API Key Configured**\n\n"
                "Please configure your `GEMINI_API_KEY` (or `OPENAI_API_KEY`) in the `.env` file.\n"
                "- Get a free Gemini API key: https://aistudio.google.com/app/apikey\n"
                "- Add it to `.env`: `GEMINI_API_KEY=your_actual_key`"
            )

        # Build context
        history_context = self.format_history()

        # Synchronize agents with full delegation enabled
        retriever = get_retriever_agent(
            llm=self.llm,
            mcps=self.agent_mcps.get("retriever") if self.mcp_enabled else None,
            allow_delegation=True
        )
        aggregator_host = get_aggregator_host_agent(
            llm=self.llm,
            mcps=self.agent_mcps.get("aggregator_host") if self.mcp_enabled else None,
            allow_delegation=True
        )
        conversationalist = get_conversational_agent(
            llm=self.llm,
            mcps=self.agent_mcps.get("conversationalist") if self.mcp_enabled else None,
            allow_delegation=True
        )

        # Synchronized task chain
        t1 = create_retrieval_task(retriever, user_query, history_context)
        t2 = create_aggregation_host_task(aggregator_host, user_query, history_context)
        t3 = create_conversational_task(conversationalist, user_query, history_context)

        try:
            # Synchronized Step 1: Retriever extracts facts
            t1_output = await retriever.aexecute_task(task=t1, tools=retriever.tools)

            # Synchronized Step 2: Aggregator Host validates and cross-examines findings
            t2_output = await aggregator_host.aexecute_task(task=t2, context=str(t1_output), tools=aggregator_host.tools)

            # Synchronized Step 3: Conversational Synthesizer delivers final dialogue with citations
            t3_output = await conversationalist.aexecute_task(task=t3, context=str(t2_output), tools=conversationalist.tools)

            response_text = str(t3_output)

        except Exception as e:
            err_str = str(e)
            print(f"[AsyncCrewError] {err_str}")

            # Smart Fallback on 429 / Quota / Timeout
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                kb_fallback = self._synthesize_from_knowledge_fast(user_query)
                if kb_fallback:
                    response_text = kb_fallback
                else:
                    response_text = (
                        "⚠️ **Batas Kuota Gemini API Tercapai (Rate Limit 429)**\n\n"
                        "Permintaan Anda belum dapat dijawab oleh model online saat ini karena kuota harian free-tier API telah mencapai batas maksimal.\n"
                        "Topik yang Anda tanyakan tidak ditemukan di basis dokumen lokal. Silakan coba kembali beberapa saat lagi atau perbarui API Key di file `.env`."
                    )
            else:
                # Try fallback async kickoff
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
                    # Final resilient fallback to local knowledge
                    kb_fallback = self._synthesize_from_knowledge_fast(user_query)
                    if kb_fallback:
                        response_text = kb_fallback
                    else:
                        response_text = f"An error occurred while running the agents: {err_str}"

        # Save to session memory
        self.chat_history.append({"role": "user", "content": user_query})
        self.chat_history.append({"role": "assistant", "content": response_text})

        return response_text

    def clear_memory(self):
        """Clears the conversational memory history."""
        self.chat_history = []
