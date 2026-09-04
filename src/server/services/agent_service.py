from langgraph.graph.state import CompiledStateGraph

from server.models.agent_models import AgentConfig
from research_assistant.state import ResearchStep


class AgentService:
    def __init__(self, agent: CompiledStateGraph, config: AgentConfig):
        self.agent = agent
        self.config = config

    async def invoke(self, topic: str) -> ResearchStep:
        initial_state = {
            "topic": topic,
            "research_mode": self.config.research_mode,
            "research_plan": "",
            "messages": [],
            "research_steps": [],
            "critical_analysis": "",
            "retry_max_count": self.config.retry_max_count,
            "critique_threshold": self.config.critique_threshold,
            "error_message": "",
            "final_response": "",
        }

        result = await self.agent.ainvoke(initial_state)

        self.state = result
        
        if result.get("error_message"):
            raise ValueError(result["error_message"])

        return result["topic"], result["final_response"]
