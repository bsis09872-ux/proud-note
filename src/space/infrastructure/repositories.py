from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from space.domain.repository import SpaceRepository
from space.domain.space import Space
from space.infrastructure.models import SpaceModel


class SqlAlchemySpaceRepository(SpaceRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, space_id: str) -> Space | None:
        model = await self.session.get(SpaceModel, space_id)
        return model.to_entity() if model else None

    async def find_all(self) -> list[Space]:
        rows = await self.session.scalars(
            select(SpaceModel).order_by(SpaceModel.created_at)
        )
        return [m.to_entity() for m in rows]

    async def save(self, space: Space) -> Space:
        model = await self.session.get(SpaceModel, space.id)
        if model is None:
            model = SpaceModel(id=space.id)
            self.session.add(model)
        model.apply(space)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()
