import uuid
from abc import ABC, abstractmethod

from emoji.domain.emoji import CustomEmoji, ReactionCount


class CustomEmojiRepository(ABC):
    @abstractmethod
    async def find_all(self) -> list[CustomEmoji]: ...

    @abstractmethod
    async def find_by_name(self, name: str) -> CustomEmoji | None: ...

    @abstractmethod
    async def save(self, emoji: CustomEmoji) -> CustomEmoji: ...

    @abstractmethod
    async def delete(self, emoji: CustomEmoji) -> None: ...


class ReactionRepository(ABC):
    @abstractmethod
    async def add(self, note_id: int, user_id: uuid.UUID, emoji: str) -> bool:
        """추가했으면 True, 이미 있으면 False"""

    @abstractmethod
    async def remove(self, note_id: int, user_id: uuid.UUID, emoji: str) -> bool: ...

    @abstractmethod
    async def count_by_note(self, note_id: int) -> list[ReactionCount]: ...

    @abstractmethod
    async def mine(self, note_id: int, user_id: uuid.UUID) -> set[str]: ...

    @abstractmethod
    async def delete_by_emoji(self, emoji: str) -> None: ...


class EmojiImageStorage(ABC):
    @abstractmethod
    def save(self, data: bytes, ext: str) -> str:
        """저장 후 media 기준 상대경로 반환"""

    @abstractmethod
    def delete(self, path: str) -> None: ...

    @abstractmethod
    def url_of(self, path: str) -> str: ...
