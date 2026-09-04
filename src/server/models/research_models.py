import uuid

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=100)

class ResearchResponse(BaseModel):
    topic: str
    research: str