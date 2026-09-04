from typing import Annotated, Callable

from fastapi import Depends, Header, HTTPException, Request
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth import hash_string
from server.db.base import AuthToken, User
from server.db.session import get_db_session
from server.models.agent_models import AgentConfig
from server.services.agent_service import AgentService
from server.services.db_service import DBService, ModelType


def get_agent(request: Request) -> CompiledStateGraph:
    # Built once in main.py's lifespan and stashed on app.state - this just hands
    # out the shared instance instead of rebuilding the compiled graph per request.
    return request.app.state.agent


def get_agent_service(
    config: AgentConfig,
    agent: Annotated[CompiledStateGraph, Depends(get_agent)],
) -> AgentService:
    return AgentService(agent=agent, config=config)


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
