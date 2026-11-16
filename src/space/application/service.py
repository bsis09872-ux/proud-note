from space.application.dto import SpaceUpdateCommand
from space.domain.exceptions import SpaceNotFound
from space.domain.repository import SpaceRepository
from space.domain.space import Space


class SpaceService:
    def __init__(self, repository: SpaceRepository):
        self.repository = repository

    async def list_spaces(self) -> list[Space]:
        return await self.repository.find_all()

    async def get_space(self, space_id: str) -> Space:
        space = await self.repository.find_by_id(space_id)
        if space is None:
            raise SpaceNotFound()
        return space

    async def update_space(self, space_id: str, command: SpaceUpdateCommand) -> Space:
        space = await self.get_space(space_id)
        space.update_policy(command.changes())
        return await self.repository.save(space)
