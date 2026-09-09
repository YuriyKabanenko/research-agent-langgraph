import uuid

from pydantic import BaseModel
from research_assistant.state import ModelFamily, ResearchMode
from research_assistant.llm.model import DEFAULT_MODEL_FAMILY, DEFAULT_MODEL_NAME

class AgentConfig(BaseModel):
    research_mode: ResearchMode = ResearchMode.quick
    token: str
    retry_max_count: int = 3
    critique_threshold: int = 6
    model_family: ModelFamily = DEFAULT_MODEL_FAMILY
    model_name: str = DEFAULT_MODEL_NAME


class AgentCreateRequest(BaseModel):
    name: str


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    user_id: uuid.UUID
    has_config: bool


class AgentConfigCreateRequest(BaseModel):
    research_mode: ResearchMode = ResearchMode.quick
    retry_max_count: int = 3
    critique_threshold: int = 6
    api_token: str
    model_family: ModelFamily = DEFAULT_MODEL_FAMILY
    model_name: str = DEFAULT_MODEL_NAME


class AgentConfigResponse(BaseModel):
    agent_id: uuid.UUID
    research_mode: ResearchMode
    retry_max_count: int
    critique_threshold: int
    model_family: ModelFamily
    model_name: str
