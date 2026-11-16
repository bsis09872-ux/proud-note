from abc import ABC, abstractmethod
from datetime import date

from note.domain.note import Comment, Note


class NoteRepository(ABC):
    @abstractmethod
    async def find_by_id(self, note_id: int) -> Note | None:
        """삭제되지 않은 노트 단건"""

    @abstractmethod
    async def find_page(
        self,
        space_id: str,
        *,
        offset: int,
        limit: int,
        tag: str | None,
        keyword: str | None,
    ) -> list[Note]:
        """최신순 목록"""

    @abstractmethod
    async def count(
        self, space_id: str, *, tag: str | None, keyword: str | None
    ) -> int: ...

    @abstractmethod
    async def count_by_author_on(
        self, space_id: str, author_key: str, posted_on: date
    ) -> int:
        """하루 작성 수 (삭제한 글 포함 -> 지우고 다시 쓰기 방지)"""

    @abstractmethod
    async def lock_space(self, space_id: str) -> None:
        """같은 공간 동시 작성 직렬화 (트랜잭션 끝나면 자동 해제)"""

    @abstractmethod
    async def trim_space(self, space_id: str, keep: int) -> int:
        """최신 keep 개만 남기고 하드 삭제, 삭제 수 반환"""

    @abstractmethod
    async def save(self, note: Note) -> Note: ...


class CommentRepository(ABC):
    @abstractmethod
    async def find_by_id(self, comment_id: int) -> Comment | None: ...

    @abstractmethod
    async def find_by_note(self, note_id: int) -> list[Comment]: ...

    @abstractmethod
    async def save(self, comment: Comment) -> Comment: ...
