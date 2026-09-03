import uuid
from datetime import datetime, timezone
from typing import List, Optional
import enum
from sqlalchemy import ForeignKey, String, Uuid, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from research_assistant.state import ResearchMode

class Base(DeclarativeBase):
    """Base class every ORM model should inherit from once the schema is defined."""
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    agents: Mapped[List["Agent"]] = relationship(back_populates="user")
    tokens: Mapped[List["AuthToken"]] = relationship(back_populates="user")


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # SHA-256 hex digest of the plaintext token - the plaintext itself is never stored,
    # only returned once in the /register response. See implementation.md for why a
    # fast hash is fine here (the input is already a 256-bit random token, not a
    # human-chosen password).
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="tokens")


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="agents")
    config: Mapped[Optional["AgentConfig"]] = relationship(back_populates="agent", uselist=False)


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), primary_key=True)
    research_mode: Mapped[ResearchMode] = mapped_column(nullable=False)
    retry_max_count: Mapped[int] = mapped_column(nullable=False)
    critique_threshold: Mapped[int] = mapped_column(nullable=False)
    api_token: Mapped[str] = mapped_column(nullable=False)
    
    agent: Mapped["Agent"] = relationship(back_populates="config")
    