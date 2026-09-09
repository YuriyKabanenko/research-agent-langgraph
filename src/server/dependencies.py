from typing import Annotated, Callable

from fastapi import Depends, Header, HTTPException, Request
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth import hash_string
from server.db.base import Agent, AgentConfig as AgentConfigOrm, AuthToken, User
from server.db.session import get_db_session
from server.models.agent_models import AgentConfig
from server.models.research_models import ResearchRequest
from server.services.agent_service import AgentService
from server.services.db_service import DBService, ModelType


def get_agent(request: Request) -> CompiledStateGraph:
    # Built once in main.py's lifespan and stashed on app.state - this just hands
    # out the shared instance instead of rebuilding the compiled graph per request.
    return request.app.state.agent


def get_db_service(model: type[ModelType]) -> Callable[..., DBService[ModelType]]:
    # Dependency factory: use as `Depends(get_db_service(SomeModel))` once real
    # models exist, to get a DBService[SomeModel] bound to the request's session.
    def _get_db_service(
        session: Annotated[AsyncSession, Depends(get_db_session)],
    ) -> DBService[ModelType]:
        return DBService(session, model)

    return _get_db_service


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401,
            detail="Missing or malformed Authorization header, expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await session.execute(
        select(User).join(AuthToken).where(AuthToken.token_hash == hash_string(token))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_agent_service(
    body: ResearchRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    agent: Annotated[CompiledStateGraph, Depends(get_agent)],
) -> AgentService:
    # Research must run against a caller-owned, persisted Agent - agent_id is
    # never trusted to belong to the caller without this check.
    agent_row = await session.get(Agent, body.agent_id)
    if agent_row is None or agent_row.user_id != user.id:
        raise HTTPException(status_code=404, detail="Agent not found")

    config_row = await session.get(AgentConfigOrm, body.agent_id)
    if config_row is None:
        raise HTTPException(status_code=422, detail="Agent has no config")

    config = AgentConfig(
        research_mode=config_row.research_mode,
        token=config_row.api_token,
        retry_max_count=config_row.retry_max_count,
        critique_threshold=config_row.critique_threshold,
        model_family=config_row.model_family,
        model_name=config_row.model_name,
    )
    return AgentService(agent=agent, config=config)
