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
    web_search_enabled: bool = False
    tavily_token: str | None = None


class AgentCreateRequest(BaseModel):
    name: str


class AgentUpdateRequest(BaseModel):
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
    web_search_enabled: bool = False
    # Required when web_search_enabled (checked in the endpoint, so the 422 carries a
    # readable message), ignored otherwise.
    tavily_api_token: str | None = None


class AgentConfigUpdateRequest(BaseModel):
    research_mode: ResearchMode = ResearchMode.quick
    retry_max_count: int = 3
    critique_threshold: int = 6
    # Omitted/blank keeps the existing token - unlike create, editing shouldn't force
    # re-entering a secret the user already stored.
    api_token: str | None = None
    web_search_enabled: bool = False
    # Same keep-if-blank rule as api_token, but only while web search stays enabled:
    # enabling it with no key stored yet requires one, and disabling it clears the key.
    tavily_api_token: str | None = None


class AgentConfigResponse(BaseModel):
    agent_id: uuid.UUID
    research_mode: ResearchMode
    retry_max_count: int
    critique_threshold: int
    model_family: ModelFamily
    model_name: str
    # tavily_api_token is never returned - while this is true, a key is stored.
    web_search_enabled: bool
