import uuid

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class RegisterResponse(BaseModel):
    user_id: uuid.UUID
    name: str
    token: str
