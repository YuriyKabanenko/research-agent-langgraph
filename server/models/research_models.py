import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class ResearchStatus(enum.Enum):
    pending = "pending"
    running = "running"
    awaiting_review = "awaiting_review"
    completed = "completed"
    failed = "failed"


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=5)
    agent_id: uuid.UUID
    # Opt-in: a complex topic then fans out into one full research loop per subtopic.
    allow_topic_split: bool = False


class ReviewRequest(BaseModel):
    approved: bool
    feedback: str | None = None

    @model_validator(mode="after")
    def _feedback_required_to_send_back(self) -> "ReviewRequest":
        if self.feedback is not None:
            self.feedback = self.feedback.strip() or None
        if not self.approved and self.feedback is None:
            raise ValueError("feedback is required when approved is false")
        return self


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
