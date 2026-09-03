from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Body, Depends, FastAPI, HTTPException

from research_assistant.graph import agent as compiled_agent
from server.auth import generate_token, hash_token
from server.db.base import AuthToken, User
from server.db.session import engine, get_db_session
from server.dependencies import get_agent_service, get_current_user
from server.models.auth_models import RegisterRequest, RegisterResponse
from server.services.agent_service import AgentService
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Compiled once here and shared via app.state - AgentService instances are
    # built fresh per request but all reuse this same graph.
    app.state.agent = compiled_agent
    yield
    # Release the pooled DB connections on shutdown.
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def read_root():
    return {"status": "ok"}


@app.post("/register", status_code=201)
async def register(
    body: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RegisterResponse:
    user = User(name=body.name)
    session.add(user)
    await session.flush()  # assigns user.id without ending the transaction

    token = generate_token()
    session.add(AuthToken(token_hash=hash_token(token), user_id=user.id))
    await session.commit()

    return RegisterResponse(user_id=user.id, name=user.name, token=token)


@app.post("/research")
async def research(
    topic: Annotated[str, Body()],
    service: Annotated[AgentService, Depends(get_agent_service)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        return await service.invoke(topic)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
