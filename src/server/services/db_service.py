from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class DBService(Generic[ModelType]):
    """Generic async CRUD over a single SQLAlchemy model.

    Schema-agnostic on purpose - once real models exist, use it as
    `DBService(session, SomeModel)`.
    """

    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self.session = session
        self.model = model

    async def create(self, **values: Any) -> ModelType:
        obj = self.model(**values)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get(self, id_: Any) -> ModelType | None:
        return await self.session.get(self.model, id_)

    async def list(self, limit: int = 100, offset: int = 0) -> Sequence[ModelType]:
        result = await self.session.execute(select(self.model).limit(limit).offset(offset))
        return result.scalars().all()

    async def update(self, id_: Any, **values: Any) -> ModelType | None:
        obj = await self.get(id_)
        if obj is None:
            return None
        for key, value in values.items():
            setattr(obj, key, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id_: Any) -> bool:
        obj = await self.get(id_)
        if obj is None:
            return False
        await self.session.delete(obj)
        await self.session.commit()
        return True
