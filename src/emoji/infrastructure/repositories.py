import uuid
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from emoji.domain.emoji import CustomEmoji, ReactionCount
from emoji.domain.repository import (
    CustomEmojiRepository,
    EmojiImageStorage,
    ReactionRepository,
)
from emoji.infrastructure.models import CustomEmojiModel, ReactionModel


class SqlAlchemyCustomEmojiRepository(CustomEmojiRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_all(self) -> list[CustomEmoji]:
        rows = await self.session.scalars(
            select(CustomEmojiModel).order_by(CustomEmojiModel.name)
        )
        return [m.to_entity() for m in rows]

    async def find_by_name(self, name: str) -> CustomEmoji | None:
        model = await self.session.scalar(
            select(CustomEmojiModel).where(CustomEmojiModel.name == name)
        )
        return model.to_entity() if model else None

    async def save(self, emoji: CustomEmoji) -> CustomEmoji:
        model = CustomEmojiModel(
            name=emoji.name, image_path=emoji.image_path, created_by=emoji.created_by
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()

    async def delete(self, emoji: CustomEmoji) -> None:
        await self.session.execute(
            delete(CustomEmojiModel).where(CustomEmojiModel.id == emoji.id)
        )


class SqlAlchemyReactionRepository(ReactionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, note_id: int, user_id: uuid.UUID, emoji: str) -> bool:
        # 동시에 두 번 눌러도 유니크 제약으로 1개만 들어간다
        stmt = (
            insert(ReactionModel)
            .values(note_id=note_id, user_id=user_id, emoji=emoji)
            .on_conflict_do_nothing(index_elements=["note_id", "user_id", "emoji"])
            .returning(ReactionModel.id)
        )
        return (await self.session.scalar(stmt)) is not None

    async def remove(self, note_id: int, user_id: uuid.UUID, emoji: str) -> bool:
        result = await self.session.execute(
            delete(ReactionModel).where(
                ReactionModel.note_id == note_id,
                ReactionModel.user_id == user_id,
                ReactionModel.emoji == emoji,
            )
        )
        return bool(result.rowcount)

    async def count_by_note(self, note_id: int) -> list[ReactionCount]:
        rows = await self.session.execute(
            select(
                ReactionModel.emoji,
                func.count(ReactionModel.id),
                func.min(ReactionModel.id),
            )
            .where(ReactionModel.note_id == note_id)
            .group_by(ReactionModel.emoji)
            .order_by(func.min(ReactionModel.id))  # 처음 달린 순서대로
        )
        return [ReactionCount(emoji=e, count=c) for e, c, _ in rows]

    async def mine(self, note_id: int, user_id: uuid.UUID) -> set[str]:
        rows = await self.session.scalars(
            select(ReactionModel.emoji).where(
                ReactionModel.note_id == note_id, ReactionModel.user_id == user_id
            )
        )
        return set(rows)

    async def delete_by_emoji(self, emoji: str) -> None:
        await self.session.execute(
            delete(ReactionModel).where(ReactionModel.emoji == emoji)
        )


class LocalEmojiImageStorage(EmojiImageStorage):
    """media/emojis/<uuid>.<ext> 에 저장, /media 로 서빙"""

    SUBDIR = "emojis"

    def __init__(self, media_dir: str, url_prefix: str = "/media"):
        self.root = Path(media_dir)
        self.url_prefix = url_prefix.rstrip("/")

    def save(self, data: bytes, ext: str) -> str:
        rel = f"{self.SUBDIR}/{uuid.uuid4().hex}.{ext}"
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return rel

    def delete(self, path: str) -> None:
        target = (self.root / path).resolve()
        if self.root.resolve() in target.parents:  # media 폴더 밖은 절대 안 지움
            target.unlink(missing_ok=True)

    def url_of(self, path: str) -> str:
        return f"{self.url_prefix}/{path}"
