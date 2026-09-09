import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ResearchStatus(enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=5)
    agent_id: uuid.UUID


class ResearchAcceptedResponse(BaseModel):
    id: uuid.UUID
    status: ResearchStatus


class ResearchResponse(BaseModel):
    id: uuid.UUID
    topic: str
    status: ResearchStatus
    research: str | None = None
    tools_used: list[str] | None = None
    research_rate: int | None = None
    error_message: str | None = None
    created_at: datetime
    agent_name: str
