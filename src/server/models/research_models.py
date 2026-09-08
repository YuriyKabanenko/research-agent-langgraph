import enum
import uuid

from pydantic import BaseModel, Field


class ResearchStatus(enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=100)


class ResearchAcceptedResponse(BaseModel):
    id: uuid.UUID
    status: ResearchStatus


class ResearchResponse(BaseModel):
    id: uuid.UUID
    topic: str
    status: ResearchStatus
    research: str | None = None
    error_message: str | None = None
