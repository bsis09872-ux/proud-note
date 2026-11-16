from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.database import get_db
from space.application.service import SpaceService
from space.domain.repository import SpaceRepository
from space.infrastructure.repositories import SqlAlchemySpaceRepository
from space.presentation.dependencies import (
    provide_space_repository,
    provide_space_service,
)


def create_space_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SpaceRepository:
    return SqlAlchemySpaceRepository(session)


def create_space_service(
    repository: Annotated[SpaceRepository, Depends(create_space_repository)],
) -> SpaceService:
    return SpaceService(repository)


def wire_space_dependencies(app: FastAPI) -> None:
    app.dependency_overrides.update(
        {
            provide_space_repository: create_space_repository,
            provide_space_service: create_space_service,
        }
    )
