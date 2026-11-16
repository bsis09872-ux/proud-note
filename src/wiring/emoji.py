from typing import Annotated

from fastapi import Depends, FastAPI
from shared.core.config import settings
from shared.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from emoji.application.service import EmojiService
from emoji.infrastructure.cache import TTLCache
from emoji.infrastructure.repositories import (
    LocalEmojiImageStorage,
    SqlAlchemyCustomEmojiRepository,
    SqlAlchemyReactionRepository,
)
from emoji.presentation.dependencies import provide_emoji_service
from note.application.service import NoteService
from wiring.note import create_note_service

# 앱 전체에서 하나씩 (싱글턴)
image_storage = LocalEmojiImageStorage(settings.media_dir)
emoji_cache = TTLCache(ttl_seconds=300)  # 이모지 목록: 거의 안 바뀜
reaction_cache = TTLCache(ttl_seconds=30, max_items=2048)  # 반응 집계: 자주 바뀜


def create_emoji_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    note_service: Annotated[NoteService, Depends(create_note_service)],
) -> EmojiService:
    return EmojiService(
        emoji_repo=SqlAlchemyCustomEmojiRepository(session),
        reaction_repo=SqlAlchemyReactionRepository(session),
        storage=image_storage,
        note_service=note_service,
        emoji_cache=emoji_cache,
        reaction_cache=reaction_cache,
    )


def wire_emoji_dependencies(app: FastAPI) -> None:
    app.dependency_overrides.update({provide_emoji_service: create_emoji_service})
