from abc import ABC, abstractmethod

from space.domain.space import Space


class SpaceRepository(ABC):
    @abstractmethod
    async def find_by_id(self, space_id: str) -> Space | None: ...

    @abstractmethod
    async def find_all(self) -> list[Space]: ...

    @abstractmethod
    async def save(self, space: Space) -> Space: ...
