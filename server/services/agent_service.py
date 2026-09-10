from langgraph.graph.state import CompiledStateGraph

from server.models.agent_models import AgentConfig
from research_assistant.state import ResearchStep
from research_assistant.llm import model as llm_model


class AgentService:
    def __init__(self, agent: CompiledStateGraph, config: AgentConfig):
        self.agent = agent
        self.config = config

    async def invoke(self, topic: str) -> ResearchStep:
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
            "error_message": "",
            "final_response": "",
        }

        # The agent's BYOK token travels via contextvar, not initial_state - state
        # gets captured by LangSmith tracing, and a raw API key has no business
        # ending up there.
        api_key_token = llm_model.set_api_key(self.config.token)
        try:
            result = await self.agent.ainvoke(initial_state)
        finally:
            llm_model.reset_api_key(api_key_token)

        self.state = result

        if result.get("error_message"):
            raise ValueError(result["error_message"])

        return result["final_response"]
