"""이모지 도메인 규칙

1. 반응 이모지는 두 종류: 유니코드 이모지(🎉) 또는 커스텀 이모지(:party_parrot:).
2. 커스텀 이모지 이름: 영문 소문자/숫자/_ 2~32자 (슬랙처럼 :이름: 으로 사용).
3. 이미지: PNG·GIF·JPG·WEBP, 256KB 이하 (확장자 말고 파일 시그니처로 판별).
4. 커스텀 이모지 삭제는 등록한 회원 또는 관리자만. 삭제하면 그 이모지 반응도 함께 사라진다.
5. 반응은 회원만, 노트당 같은 이모지는 1번 (다른 이모지는 여러 개 가능).
"""

import re
import uuid
from dataclasses import dataclass
from datetime import datetime

from emoji.domain.exceptions import InvalidEmoji, InvalidEmojiImage, NotEmojiOwner

NAME_RE = re.compile(r"^[a-z0-9_]{2,32}$")
CUSTOM_RE = re.compile(r"^:([a-z0-9_]{2,32}):$")
MAX_IMAGE_BYTES = 256 * 1024
MAX_UNICODE_LEN = 16


def detect_image_type(data: bytes) -> str:
    """파일 시그니처(매직 넘버)로 확장자 판별"""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    raise InvalidEmojiImage()


def validate_image(data: bytes) -> str:
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise InvalidEmojiImage()
    return detect_image_type(data)


def validate_name(name: str) -> str:
    name = (name or "").strip().strip(":").lower()
    if not NAME_RE.match(name):
        raise InvalidEmoji(
            errors={"name": ["영문 소문자·숫자·_ 2~32자로 지어 주세요."]}
        )
    return name


def custom_name_of(emoji: str) -> str | None:
    """':party:' -> 'party', 유니코드면 None"""
    m = CUSTOM_RE.match(emoji)
    return m.group(1) if m else None


def normalize_reaction(raw: str) -> str:
    emoji = (raw or "").strip()
    if custom_name_of(emoji):
        return emoji
    # 유니코드 이모지: 짧고, ASCII(일반 글자) 가 아니어야 한다
    if not emoji or len(emoji) > MAX_UNICODE_LEN or any(ch.isascii() for ch in emoji):
        raise InvalidEmoji(
            errors={"emoji": ["🎉 같은 이모지나 :이름: 형식의 커스텀 이모지만 돼요."]}
        )
    return emoji


@dataclass
class CustomEmoji:
    name: str
    image_path: str
    created_by: uuid.UUID | None
    id: int | None = None
    created_at: datetime | None = None

    @property
    def code(self) -> str:
        return f":{self.name}:"

    def ensure_deletable(self, requester_id: uuid.UUID, is_admin: bool) -> None:
        if not (is_admin or self.created_by == requester_id):
            raise NotEmojiOwner()


@dataclass(frozen=True)
class ReactionCount:
    emoji: str
    count: int
