from dotenv import load_dotenv

load_dotenv()

import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Body, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from research_assistant.graph import agent as compiled_agent
from server.auth import generate_token, hash_string
from server.db.base import AuthToken, User, Research
from server.db.session import engine, get_db_session
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
    

@app.post("/research")
async def research(
    topic: ResearchRequest,
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
    research_service: Annotated[DBService[Research], Depends(get_db_service(Research))],
    user: Annotated[User, Depends(get_current_user)],
) -> ResearchResponse:
    try:
        topic, response = await agent_service.invoke(topic)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        await research_service.create(topic=topic, resarch=response, user_id=user.id)
    except SQLAlchemyError:
        logger.exception("Failed to persist research result for user %s", user.id)
        await research_service.session.rollback()

    return ResearchResponse(topic=topic, research=response)
