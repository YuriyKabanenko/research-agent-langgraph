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
from server.db.base import AuthToken, User, Research
from server.db.session import async_session_factory, engine, get_db_session
from server.dependencies import get_agent_service, get_current_user, get_db_service
from server.models.auth_models import *
from server.models.research_models import *
from server.services.agent_service import AgentService
from server.services.db_service import DBService
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
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

@app.get("/login", status_code=200)
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
    

async def _run_research(research_id: uuid.UUID, topic: str, agent_service: AgentService) -> None:
    # Runs after the response has been sent, on its own DB session - the
    # request's session gets torn down independently and this can easily
    # outlive it.
    async with async_session_factory() as session:
        research_service = DBService(session, Research)
        await research_service.update(research_id, status=ResearchStatus.running)

        try:
            _, result = await agent_service.invoke(topic)
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
            research_id, status=ResearchStatus.completed, resarch=result
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
        topic=body.topic, status=ResearchStatus.pending, user_id=user.id
    )
    background_tasks.add_task(_run_research, record.id, body.topic, agent_service)

    return ResearchAcceptedResponse(id=record.id, status=record.status)


@app.get("/research/{research_id}")
async def get_research(
    research_id: uuid.UUID,
    research_service: Annotated[DBService[Research], Depends(get_db_service(Research))],
    user: Annotated[User, Depends(get_current_user)],
) -> ResearchResponse:
    record = await research_service.get(research_id)
    if record is None or record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Research not found")

    return ResearchResponse(
        id=record.id,
        topic=record.topic,
        status=record.status,
        research=record.resarch,
        error_message=record.error_message,
    )
