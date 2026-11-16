from dataclasses import dataclass

from note.application.dto import (
    CommentCreateCommand,
    CommentUpdateCommand,
    NoteCreateCommand,
    NoteListQuery,
    NoteUpdateCommand,
)
from note.domain.exceptions import CommentNotFound, DailyLimitExceeded, NoteNotFound
from note.domain.note import Author, Comment, Note, Requester
from note.domain.ports import PasswordHasher
from note.domain.repository import CommentRepository, NoteRepository
from shared.core.logger import get_logger
from shared.core.schemas import PageResponse
from space.application.service import SpaceService
from space.domain.space import Space

logger = get_logger(__name__)


@dataclass
class NoteView:
    """응답 조립용: 노트 + 그 노트가 속한 공간"""

    note: Note
    space: Space


class NoteService:
    def __init__(
        self,
        note_repo: NoteRepository,
        space_service: SpaceService,
        hasher: PasswordHasher,
    ):
        self.note_repo = note_repo
        self.space_service = space_service
        self.hasher = hasher

    async def write(
        self,
        space_id: str,
        command: NoteCreateCommand,
        requester: Requester | None,
        client_ip_hash: str,
    ) -> NoteView:
        space = await self.space_service.get_space(space_id)
        space.ensure_writable(is_member=requester is not None)
        author = Author.member(requester) if requester else Author.guest(client_ip_hash)

        note = Note.write(
            space_id=space.id,
            author=author,
            contents=command.contents(),
            tags=command.tags,
            guest_password=command.guest_password,
            hasher=self.hasher,
        )

        if space.daily_limit or space.max_notes:
            # 같은 공간 동시 작성을 줄 세워서 "하루 1개"·"최대 N개" 경쟁 조건을 막는다
            await self.note_repo.lock_space(space.id)

        if space.daily_limit:
            written = await self.note_repo.count_by_author_on(
                space.id, author.key, note.posted_on
            )
            if written >= space.daily_limit:
                raise DailyLimitExceeded(
                    f"{space.emoji} {space.name}엔 하루 {space.daily_limit}번만 올릴 수 있어요 🌙"
                )

        saved = await self.note_repo.save(note)

        if space.max_notes:
            trimmed = await self.note_repo.trim_space(space.id, keep=space.max_notes)
            if trimmed:
                logger.info("[%s] 오래된 노트 %d개 정리", space.id, trimmed)

        return NoteView(saved, space)

    async def list_notes(
        self, space_id: str, query: NoteListQuery, requester: Requester | None
    ) -> tuple[Space, PageResponse[Note]]:
        space = await self.space_service.get_space(space_id)
        space.ensure_readable(is_member=requester is not None)
        size = query.size or space.page_size
        items = await self.note_repo.find_page(
            space.id,
            offset=(query.page - 1) * size,
            limit=size,
            tag=query.tag,
            keyword=query.keyword,
        )
        total = await self.note_repo.count(
            space.id, tag=query.tag, keyword=query.keyword
        )
        return space, PageResponse.of(items, total, query.page, size)

    async def get_readable(self, note_id: int, requester: Requester | None) -> NoteView:
        note = await self.note_repo.find_by_id(note_id)
        if note is None:
            raise NoteNotFound()
        space = await self.space_service.get_space(note.space_id)
        space.ensure_readable(is_member=requester is not None)
        return NoteView(note, space)

    async def edit(
        self,
        note_id: int,
        command: NoteUpdateCommand,
        requester: Requester | None,
        guest_password: str | None,
    ) -> NoteView:
        view = await self.get_readable(note_id, requester)
        view.note.ensure_editable(requester, guest_password, self.hasher)
        view.note.edit(command.changes())
        return NoteView(await self.note_repo.save(view.note), view.space)

    async def delete(
        self, note_id: int, requester: Requester | None, guest_password: str | None
    ) -> None:
        view = await self.get_readable(note_id, requester)
        view.note.ensure_editable(requester, guest_password, self.hasher)
        view.note.soft_delete()
        await self.note_repo.save(view.note)


class CommentService:
    def __init__(self, comment_repo: CommentRepository, note_service: NoteService):
        self.comment_repo = comment_repo
        self.note_service = note_service

    async def list_comments(
        self, note_id: int, requester: Requester | None
    ) -> list[Comment]:
        view = await self.note_service.get_readable(note_id, requester)
        if not view.space.allow_comments:
            return []
        return await self.comment_repo.find_by_note(note_id)

    async def write(
        self, note_id: int, command: CommentCreateCommand, requester: Requester
    ) -> Comment:
        view = await self.note_service.get_readable(note_id, requester)
        view.space.ensure_commentable()
        comment = Comment.write(note_id, requester, command.content)
        return await self.comment_repo.save(comment)

    async def edit(
        self, comment_id: int, command: CommentUpdateCommand, requester: Requester
    ) -> Comment:
        comment = await self._get(comment_id)
        comment.ensure_editable(requester)
        comment.edit(command.content)
        return await self.comment_repo.save(comment)

    async def delete(self, comment_id: int, requester: Requester) -> None:
        comment = await self._get(comment_id)
        comment.ensure_editable(requester)
        comment.soft_delete()
        await self.comment_repo.save(comment)

    async def _get(self, comment_id: int) -> Comment:
        comment = await self.comment_repo.find_by_id(comment_id)
        if comment is None:
            raise CommentNotFound()
        return comment
