import zlib
from datetime import date

from sqlalchemy import Select, delete, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from note.domain.note import Comment, Note
from note.domain.repository import CommentRepository, NoteRepository
from note.infrastructure.models import CommentModel, NoteModel


def _escape_like(keyword: str) -> str:
    return keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class SqlAlchemyNoteRepository(NoteRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, note_id: int) -> Note | None:
        model = await self.session.scalar(
            select(NoteModel).where(
                NoteModel.id == note_id, NoteModel.deleted_at.is_(None)
            )
        )
        return model.to_entity() if model else None

    def _filtered(
        self, stmt: Select, space_id: str, tag: str | None, keyword: str | None
    ) -> Select:
        stmt = stmt.where(
            NoteModel.space_id == space_id, NoteModel.deleted_at.is_(None)
        )
        if tag:
            # @> 연산자 -> GIN 인덱스 사용
            stmt = stmt.where(
                NoteModel.tags.contains([tag.strip().lstrip("#").lower()])
            )
        if keyword:
            pattern = f"%{_escape_like(keyword.strip())}%"
            stmt = stmt.where(
                or_(
                    NoteModel.learned.ilike(pattern, escape="\\"),
                    NoteModel.achieved.ilike(pattern, escape="\\"),
                    NoteModel.proud_of_me.ilike(pattern, escape="\\"),
                )
            )
        return stmt

    async def find_page(
        self,
        space_id: str,
        *,
        offset: int,
        limit: int,
        tag: str | None,
        keyword: str | None,
    ) -> list[Note]:
        stmt = self._filtered(select(NoteModel), space_id, tag, keyword)
        stmt = stmt.order_by(NoteModel.created_at.desc(), NoteModel.id.desc())
        rows = await self.session.scalars(stmt.offset(offset).limit(limit))
        return [m.to_entity() for m in rows]

    async def count(
        self, space_id: str, *, tag: str | None, keyword: str | None
    ) -> int:
        stmt = self._filtered(select(func.count(NoteModel.id)), space_id, tag, keyword)
        return await self.session.scalar(stmt) or 0

    async def count_by_author_on(
        self, space_id: str, author_key: str, posted_on: date
    ) -> int:
        stmt = select(func.count(NoteModel.id)).where(
            NoteModel.space_id == space_id,
            NoteModel.author_key == author_key,
            NoteModel.posted_on == posted_on,
        )
        return await self.session.scalar(stmt) or 0

    async def lock_space(self, space_id: str) -> None:
        lock_key = zlib.crc32(f"notes:{space_id}".encode())
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(:k)"), {"k": lock_key}
        )

    async def trim_space(self, space_id: str, keep: int) -> int:
        keep_ids = (
            select(NoteModel.id)
            .where(NoteModel.space_id == space_id, NoteModel.deleted_at.is_(None))
            .order_by(NoteModel.created_at.desc(), NoteModel.id.desc())
            .limit(keep)
        )
        result = await self.session.execute(
            delete(NoteModel).where(
                NoteModel.space_id == space_id,
                NoteModel.deleted_at.is_(None),
                NoteModel.id.not_in(keep_ids.scalar_subquery()),
            )
        )
        return result.rowcount or 0

    async def save(self, note: Note) -> Note:
        if note.id is None:
            model = NoteModel()
            self.session.add(model)
        else:
            model = await self.session.get(NoteModel, note.id)
            if model is None:
                raise ValueError(f"note {note.id} not found")
        model.apply(note)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()


class SqlAlchemyCommentRepository(CommentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, comment_id: int) -> Comment | None:
        model = await self.session.scalar(
            select(CommentModel).where(
                CommentModel.id == comment_id, CommentModel.deleted_at.is_(None)
            )
        )
        return model.to_entity() if model else None

    async def find_by_note(self, note_id: int) -> list[Comment]:
        rows = await self.session.scalars(
            select(CommentModel)
            .where(CommentModel.note_id == note_id, CommentModel.deleted_at.is_(None))
            .order_by(CommentModel.created_at, CommentModel.id)
        )
        return [m.to_entity() for m in rows]

    async def save(self, comment: Comment) -> Comment:
        if comment.id is None:
            model = CommentModel()
            self.session.add(model)
        else:
            model = await self.session.get(CommentModel, comment.id)
            if model is None:
                raise ValueError(f"comment {comment.id} not found")
        model.apply(comment)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()
