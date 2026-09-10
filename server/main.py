from dotenv import load_dotenv

load_dotenv()

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import BackgroundTasks, Body, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from research_assistant.graph import agent as compiled_agent
from server.auth import generate_token, hash_string
from server.db.base import Agent, AgentConfig as AgentConfigOrm, AuthToken, User, Research
from server.db.session import async_session_factory, engine, get_db_session
from server.dependencies import get_agent_service, get_current_user, get_db_service
from server.models.agent_models import *
from server.models.auth_models import *
from server.models.research_models import *
from server.services.agent_service import AgentService
from server.services.db_service import DBService
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Compiled once here and shared via app.state - AgentService instances are
    # built fresh per request but all reuse this same graph.
    app.state.agent = compiled_agent
    yield
    # Release the pooled DB connections on shutdown.
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.warning("Integrity error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=409, content={"detail": "Conflict with existing data"})


@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError):
    logger.error("Database unavailable on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Unhandled database error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def read_root():
    return {"status": "ok"}


@app.post("/register", status_code=201)
async def register(
    body: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RegisterResponse:
    user = User(name=body.name, password_hash=hash_string(body.password))
    session.add(user)
    await session.flush()  # assigns user.id without ending the transaction

    token = generate_token()
    session.add(AuthToken(token_hash=hash_string(token), user_id=user.id))
    await session.commit()

    return RegisterResponse(user_id=user.id, name=user.name, token=token)

@app.post("/login", status_code=200)
async def login(
    body: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    token_service: Annotated[DBService[AuthToken], Depends(get_db_service(AuthToken))]
) -> LoginResponse:
    user = await session.execute(
        select(User).where(User.password_hash == hash_string(body.password), User.name == body.name)
    )
    user = user.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    new_token = generate_token()
    await token_service.create(token_hash=hash_string(new_token), user_id=user.id)
    
    return LoginResponse(token=new_token)


@app.get("/agents")
async def list_agents(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[AgentResponse]:
    result = await session.execute(
        select(Agent).options(selectinload(Agent.config)).where(Agent.user_id == user.id)
    )
    agents = result.scalars().all()
    return [
        AgentResponse(id=a.id, name=a.name, user_id=a.user_id, has_config=a.config is not None)
        for a in agents
    ]


@app.post("/agents", status_code=201)
async def create_agent(
    body: AgentCreateRequest,
    agent_service: Annotated[DBService[Agent], Depends(get_db_service(Agent))],
    user: Annotated[User, Depends(get_current_user)],
) -> AgentResponse:
    record = await agent_service.create(name=body.name, user_id=user.id)
    return AgentResponse(id=record.id, name=record.name, user_id=record.user_id, has_config=False)


@app.patch("/agents/{agent_id}")
async def update_agent(
    agent_id: uuid.UUID,
    body: AgentUpdateRequest,
    agent_service: Annotated[DBService[Agent], Depends(get_db_service(Agent))],
    config_service: Annotated[DBService[AgentConfigOrm], Depends(get_db_service(AgentConfigOrm))],
    user: Annotated[User, Depends(get_current_user)],
) -> AgentResponse:
    agent_record = await agent_service.get(agent_id)
    if agent_record is None or agent_record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Agent not found")

    updated = await agent_service.update(agent_id, name=body.name)
    config_record = await config_service.get(agent_id)
    return AgentResponse(
        id=updated.id, name=updated.name, user_id=updated.user_id, has_config=config_record is not None
    )


@app.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    agent_record = await session.get(Agent, agent_id)
    if agent_record is None or agent_record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Research rows FK to agents with no cascade - block deletion rather than
    # orphaning past research history.
    existing_research = await session.execute(
        select(Research.id).where(Research.agent_id == agent_id).limit(1)
    )
    if existing_research.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409, detail="Agent has research history and cannot be deleted"
        )

    config_record = await session.get(AgentConfigOrm, agent_id)
    if config_record is not None:
        await session.delete(config_record)

    await session.delete(agent_record)
    await session.commit()


@app.post("/agents/{agent_id}/config", status_code=201)
async def create_agent_config(
    agent_id: uuid.UUID,
    body: AgentConfigCreateRequest,
    agent_service: Annotated[DBService[Agent], Depends(get_db_service(Agent))],
    config_service: Annotated[DBService[AgentConfigOrm], Depends(get_db_service(AgentConfigOrm))],
    user: Annotated[User, Depends(get_current_user)],
) -> AgentConfigResponse:
    agent_record = await agent_service.get(agent_id)
    if agent_record is None or agent_record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Agent not found")

    record = await config_service.create(
        agent_id=agent_id,
        research_mode=body.research_mode,
        retry_max_count=body.retry_max_count,
        critique_threshold=body.critique_threshold,
        api_token=body.api_token,
        model_family=body.model_family,
        model_name=body.model_name,
    )
    return AgentConfigResponse(
        agent_id=record.agent_id,
        research_mode=record.research_mode,
        retry_max_count=record.retry_max_count,
        critique_threshold=record.critique_threshold,
        model_family=record.model_family,
        model_name=record.model_name,
    )


@app.get("/agents/{agent_id}/config")
async def get_agent_config(
    agent_id: uuid.UUID,
    agent_service: Annotated[DBService[Agent], Depends(get_db_service(Agent))],
    config_service: Annotated[DBService[AgentConfigOrm], Depends(get_db_service(AgentConfigOrm))],
    user: Annotated[User, Depends(get_current_user)],
) -> AgentConfigResponse:
    agent_record = await agent_service.get(agent_id)
    if agent_record is None or agent_record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Agent not found")

    record = await config_service.get(agent_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Agent has no config")

    return AgentConfigResponse(
        agent_id=record.agent_id,
        research_mode=record.research_mode,
        retry_max_count=record.retry_max_count,
        critique_threshold=record.critique_threshold,
        model_family=record.model_family,
        model_name=record.model_name,
    )


@app.patch("/agents/{agent_id}/config")
async def update_agent_config(
    agent_id: uuid.UUID,
    body: AgentConfigUpdateRequest,
    agent_service: Annotated[DBService[Agent], Depends(get_db_service(Agent))],
    config_service: Annotated[DBService[AgentConfigOrm], Depends(get_db_service(AgentConfigOrm))],
    user: Annotated[User, Depends(get_current_user)],
) -> AgentConfigResponse:
    agent_record = await agent_service.get(agent_id)
    if agent_record is None or agent_record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Agent not found")

    existing = await config_service.get(agent_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Agent has no config")

    values = {
        "research_mode": body.research_mode,
        "retry_max_count": body.retry_max_count,
        "critique_threshold": body.critique_threshold,
    }
    if body.api_token:
        values["api_token"] = body.api_token

    record = await config_service.update(agent_id, **values)
    return AgentConfigResponse(
        agent_id=record.agent_id,
        research_mode=record.research_mode,
        retry_max_count=record.retry_max_count,
        critique_threshold=record.critique_threshold,
        model_family=record.model_family,
        model_name=record.model_name,
    )


async def _run_research(research_id: uuid.UUID, topic: str, agent_service: AgentService) -> None:
    # Runs after the response has been sent, on its own DB session - the
    # request's session gets torn down independently and this can easily
    # outlive it.
    async with async_session_factory() as session:
        research_service = DBService(session, Research)
        await research_service.update(research_id, status=ResearchStatus.running)

        try:
            result = await agent_service.invoke(topic)
        except ValueError as e:
            await research_service.update(
                research_id, status=ResearchStatus.failed, error_message=str(e)
            )
            return
        except Exception:
            logger.exception("Research %s failed unexpectedly", research_id)
            await research_service.update(
                research_id, status=ResearchStatus.failed, error_message="Internal error"
            )
            return
    
        
        await research_service.update(
            research_id,
            status=ResearchStatus.completed,
            resarch=result["content"],
            # Preserves first-seen order while dropping repeats from retries.
            tools_used=list(dict.fromkeys(result["tools_used"])),
            research_rate=result["research_rate"],
        )


@app.post("/research", status_code=202)
async def research(
    body: ResearchRequest,
    background_tasks: BackgroundTasks,
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
    research_service: Annotated[DBService[Research], Depends(get_db_service(Research))],
    user: Annotated[User, Depends(get_current_user)],
) -> ResearchAcceptedResponse:
    record = await research_service.create(
        topic=body.topic,
        status=ResearchStatus.pending,
        user_id=user.id,
        agent_id=body.agent_id,
    )
    background_tasks.add_task(_run_research, record.id, body.topic, agent_service)

    return ResearchAcceptedResponse(id=record.id, status=record.status)


@app.get("/research")
async def list_research(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[ResearchResponse]:
    result = await session.execute(
        select(Research)
        .options(selectinload(Research.agent))
        .where(Research.user_id == user.id)
        .order_by(Research.created_at.desc())
    )
    records = result.scalars().all()
    return [
        ResearchResponse(
            id=r.id,
            topic=r.topic,
            status=r.status,
            research=r.resarch,
            tools_used=r.tools_used,
            research_rate=r.research_rate,
            error_message=r.error_message,
            created_at=r.created_at,
            agent_name=r.agent.name,
        )
        for r in records
    ]


@app.get("/research/{research_id}")
async def get_research(
    research_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> ResearchResponse:
    result = await session.execute(
        select(Research).options(selectinload(Research.agent)).where(Research.id == research_id)
    )
    record = result.scalar_one_or_none()
    if record is None or record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Research not found")

    return ResearchResponse(
        id=record.id,
        topic=record.topic,
        status=record.status,
        research=record.resarch,
        tools_used=record.tools_used,
        research_rate=record.research_rate,
        error_message=record.error_message,
        created_at=record.created_at,
        agent_name=record.agent.name,
    )


@app.delete("/research/{research_id}", status_code=204)
async def delete_research(
    research_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    record = await session.get(Research, research_id)
    if record is None or record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Research not found")

    await session.delete(record)
    await session.commit()
