import uuid
from dataclasses import dataclass
from typing import Any

from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from server.models.agent_models import AgentConfig
from research_assistant.state import ResearchStep
from research_assistant.llm import model as llm_model
from research_assistant.llm import tools as llm_tools


# The graph paused in human_review and is waiting for the user to approve or send back
# this draft.
@dataclass
class Paused:
    candidate: ResearchStep


# The graph ran to the end.
@dataclass
class Completed:
    final: ResearchStep


ResearchOutcome = Paused | Completed


class AgentService:
    def __init__(self, agent: CompiledStateGraph, config: AgentConfig):
        self.agent = agent
        self.config = config

    async def start(self, research_id: uuid.UUID, topic: str) -> ResearchOutcome:
        initial_state = {
            "topic": topic,
            "research_mode": self.config.research_mode,
            "model_family": self.config.model_family,
            "model_name": self.config.model_name,
            "research_plan": "",
            "messages": [],
            "research_steps": [],
            "critical_analysis": "",
            "retry_max_count": self.config.retry_max_count,
            "critique_threshold": self.config.critique_threshold,
            # Both conditions, so a config that somehow has the flag but no key never
            # gets offered a search tool that can only fail.
            "web_search_enabled": self.config.web_search_enabled and bool(self.config.tavily_token),
            "human_feedback": "",
            "error_message": "",
            "final_response": "",
        }
        return await self._run(research_id, initial_state)

    # decision is {"approved": bool, "feedback": str | None} - what human_review's
    # interrupt() returns once the graph is resumed.
    async def resume(self, research_id: uuid.UUID, decision: dict[str, Any]) -> ResearchOutcome:
        return await self._run(research_id, Command(resume=decision))

    async def _run(self, research_id: uuid.UUID, graph_input: Any) -> ResearchOutcome:
        # One checkpoint thread per Research row - resume finds the paused run by it.
        config = {"configurable": {"thread_id": str(research_id)}}

        # The agent's BYOK token travels via contextvar, not graph state - state gets
        # captured by LangSmith tracing and now also persisted by the checkpointer, and
        # a raw API key has no business ending up in either. Which also means a resumed
        # run has to set it again here: it isn't in the checkpoint.
        api_key_token = llm_model.set_api_key(self.config.token)
        # Always set, even to None: that's what stops search_in_web from falling back to
        # the server's own TAVILY_API_KEY env var (see llm/tools.py).
        tavily_key_token = llm_tools.set_tavily_api_key(self.config.tavily_token)
        try:
            result = await self.agent.ainvoke(graph_input, config)
        finally:
            llm_tools.reset_tavily_api_key(tavily_key_token)
            llm_model.reset_api_key(api_key_token)

        if result.get("error_message"):
            raise ValueError(result["error_message"])

        if "__interrupt__" in result:
            return Paused(candidate=result["__interrupt__"][0].value["candidate"])

        return Completed(final=result["final_response"])
