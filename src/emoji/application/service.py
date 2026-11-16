from dataclasses import dataclass

from emoji.domain.emoji import (
    CustomEmoji,
    ReactionCount,
    custom_name_of,
    normalize_reaction,
    validate_image,
    validate_name,
)
from emoji.domain.exceptions import (
    EmojiNameTaken,
    EmojiNotFound,
    ReactionAlreadyExists,
    ReactionNotFound,
)
from emoji.domain.repository import (
    CustomEmojiRepository,
    EmojiImageStorage,
    ReactionRepository,
)
from emoji.infrastructure.cache import TTLCache
from note.application.service import NoteService
from note.domain.note import Requester, is_admin

EMOJI_LIST_KEY = "emojis"


def _summary_key(note_id: int) -> str:
    return f"reactions:{note_id}"


@dataclass
class ReactionSummaryItem:
    emoji: str
    count: int
    reacted_by_me: bool
    image_url: str | None  # 커스텀 이모지면 이미지 주소


class EmojiService:
    def __init__(
        self,
        emoji_repo: CustomEmojiRepository,
        reaction_repo: ReactionRepository,
        storage: EmojiImageStorage,
        note_service: NoteService,
        emoji_cache: TTLCache,
        reaction_cache: TTLCache,
    ):
        self.emoji_repo = emoji_repo
        self.reaction_repo = reaction_repo
        self.storage = storage
        self.note_service = note_service
        self.emoji_cache = emoji_cache
        self.reaction_cache = reaction_cache

    # ---------- 커스텀 이모지 ----------
    async def list_emojis(self) -> list[CustomEmoji]:
        cached = self.emoji_cache.get(EMOJI_LIST_KEY)
        if cached is not None:
            return cached
        emojis = await self.emoji_repo.find_all()
        self.emoji_cache.set(EMOJI_LIST_KEY, emojis)
        return emojis

    async def register(
        self, name: str, data: bytes, requester: Requester
    ) -> CustomEmoji:
        name = validate_name(name)
        ext = validate_image(data)
        if await self.emoji_repo.find_by_name(name):
            raise EmojiNameTaken()
        path = self.storage.save(data, ext)
        try:
            saved = await self.emoji_repo.save(
                CustomEmoji(name=name, image_path=path, created_by=requester.id)
            )
        except Exception:
            self.storage.delete(path)  # DB 실패하면 파일도 정리
            raise
        self.emoji_cache.delete(EMOJI_LIST_KEY)
        return saved

    async def remove(self, name: str, requester: Requester) -> None:
        emoji = await self.emoji_repo.find_by_name(validate_name(name))
        if emoji is None:
            raise EmojiNotFound()
        emoji.ensure_deletable(requester.id, is_admin(requester))
        await self.reaction_repo.delete_by_emoji(emoji.code)
        await self.emoji_repo.delete(emoji)
        self.storage.delete(emoji.image_path)
        self.emoji_cache.delete(EMOJI_LIST_KEY)
        self.reaction_cache.clear()  # 여러 노트에 걸쳐 있으니 통째로 비운다

    def image_url(self, emoji: CustomEmoji) -> str:
        return self.storage.url_of(emoji.image_path)

    # ---------- 반응 ----------
    async def react(self, note_id: int, raw_emoji: str, requester: Requester) -> None:
        await self.note_service.get_readable(note_id, requester)
        emoji = normalize_reaction(raw_emoji)
        name = custom_name_of(emoji)
        if name and not await self._custom_exists(name):
            raise EmojiNotFound(f"{emoji} 이모지는 아직 없어요. 먼저 등록해 주세요 🎨")
        if not await self.reaction_repo.add(note_id, requester.id, emoji):
            raise ReactionAlreadyExists()
        self.reaction_cache.delete(_summary_key(note_id))

    async def unreact(self, note_id: int, raw_emoji: str, requester: Requester) -> None:
        await self.note_service.get_readable(note_id, requester)
        emoji = normalize_reaction(raw_emoji)
        if not await self.reaction_repo.remove(note_id, requester.id, emoji):
            raise ReactionNotFound()
        self.reaction_cache.delete(_summary_key(note_id))

    async def summary(
        self, note_id: int, requester: Requester | None
    ) -> list[ReactionSummaryItem]:
        await self.note_service.get_readable(note_id, requester)

        key = _summary_key(note_id)
        counts: list[ReactionCount] | None = self.reaction_cache.get(key)
        if counts is None:
            counts = await self.reaction_repo.count_by_note(note_id)
            self.reaction_cache.set(key, counts)

        # "내가 눌렀는지" 는 사람마다 달라서 캐시하지 않는다
        mine = (
            await self.reaction_repo.mine(note_id, requester.id) if requester else set()
        )
        images = {e.code: self.image_url(e) for e in await self.list_emojis()}
        return [
            ReactionSummaryItem(
                emoji=c.emoji,
                count=c.count,
                reacted_by_me=c.emoji in mine,
                image_url=images.get(c.emoji),
            )
            for c in counts
        ]

    async def _custom_exists(self, name: str) -> bool:
        return any(e.name == name for e in await self.list_emojis())
