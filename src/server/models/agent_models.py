from pydantic import BaseModel
from research_assistant.state import ResearchMode

class AgentConfig(BaseModel):
    research_mode: ResearchMode = ResearchMode.quick
    token: str
    retry_max_count: int = 3
    critique_threshold: int = 6
    