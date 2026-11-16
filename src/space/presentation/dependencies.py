from space.application.service import SpaceService
from space.domain.repository import SpaceRepository


def provide_space_repository() -> SpaceRepository:
    raise NotImplementedError("SpaceRepository 의존성이 주입되지 않았습니다.")


def provide_space_service() -> SpaceService:
    raise NotImplementedError("SpaceService 의존성이 주입되지 않았습니다.")
