from typing import Annotated

from fastapi import Depends, FastAPI
from shared.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from note.application.service import CommentService, NoteService
from note.domain.ports import PasswordHasher
from note.infrastructure.repositories import (
    SqlAlchemyCommentRepository,
    SqlAlchemyNoteRepository,
)
from note.infrastructure.security import BcryptPasswordHasher
from note.presentation.dependencies import provide_comment_service, provide_note_service
from space.application.service import SpaceService
from wiring.space import create_space_service

guest_password_hasher: PasswordHasher = BcryptPasswordHasher()


def create_note_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    space_service: Annotated[SpaceService, Depends(create_space_service)],
) -> NoteService:
    return NoteService(
        note_repo=SqlAlchemyNoteRepository(session),
        space_service=space_service,
        hasher=guest_password_hasher,
    )


def create_comment_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    note_service: Annotated[NoteService, Depends(create_note_service)],
) -> CommentService:
    return CommentService(SqlAlchemyCommentRepository(session), note_service)


def wire_note_dependencies(app: FastAPI) -> None:
    app.dependency_overrides.update(
        {
            provide_note_service: create_note_service,
            provide_comment_service: create_comment_service,
        }
    )
