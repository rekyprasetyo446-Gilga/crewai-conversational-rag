"""
CrewService: Manages multi-turn ConversationalRAGCrew instances per session.
"""

from typing import Dict, List, Tuple
from crew import ConversationalRAGCrew


class CrewService:
    """Manages session-isolated ConversationalRAGCrew instances."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.sessions: Dict[str, ConversationalRAGCrew] = {}

    def get_crew(self, session_id: str = "default") -> ConversationalRAGCrew:
        """Retrieves or instantiates a ConversationalRAGCrew for the given session_id."""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationalRAGCrew(verbose=self.verbose)
        return self.sessions[session_id]

    async def ask_async(self, session_id: str, message: str) -> Tuple[str, int, str]:
        """
        Executes query on the session's crew asynchronously.
        Returns (reply, turns_count, model_name).
        """
        crew = self.get_crew(session_id)
        reply = await crew.ask_async(message)
        turns = len(crew.chat_history) // 2
        return reply, turns, crew.model

    def clear_session(self, session_id: str = "default") -> int:
        """Resets memory history for the specified session."""
        if session_id in self.sessions:
            self.sessions[session_id].clear_memory()
        return 0

    def get_history(self, session_id: str = "default") -> List[Dict[str, str]]:
        """Returns the conversation history for a given session."""
        crew = self.get_crew(session_id)
        return list(crew.chat_history)

    def session_count(self) -> int:
        """Returns total active session instances."""
        return len(self.sessions)

    def is_configured(self) -> bool:
        """Checks if default crew LLM credentials are validly configured."""
        crew = self.get_crew("default")
        return crew.llm is not None

    def get_active_model(self) -> str:
        """Returns the active model name."""
        crew = self.get_crew("default")
        return crew.model
