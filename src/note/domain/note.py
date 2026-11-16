"""노트(오늘의 자랑) 도메인 규칙

1. learned(알게 된 것) / achieved(해낸 것) / proud_of_me(오늘의 나) 중 하나 이상 필수, 각 1000자 이하.
2. 태그는 최대 5개, 1~20자 (한글/영문/숫자/_/-), 소문자·중복 제거.
3. 회원 글은 작성자 또는 관리자만 수정/삭제. 비회원 글은 작성 시 비밀번호로 검증.
4. author_key 로 "누가 썼는지" 식별 (회원 u:<id>, 비회원 g:<IP 해시>) -> 하루 작성 제한에 사용.
5. 날짜(posted_on) 는 한국 시간 기준.
6. 삭제는 소프트 삭제. 단, 공간 최대 보관 개수 초과분은 하드 삭제.
"""

import re
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from note.domain.exceptions import (
    GuestPasswordMismatch,
    GuestPasswordRequired,
    InvalidNote,
    NotOwner,
)
from note.domain.ports import PasswordHasher
from shared.core.models import utcnow

KST = ZoneInfo("Asia/Seoul")
CONTENT_FIELDS = ("learned", "achieved", "proud_of_me")
CONTENT_MAX = 1000
MAX_TAGS = 5
TAG_RE = re.compile(r"^[0-9a-z가-힣_-]{1,20}$")
ANONYMOUS_NAME = "익명의 프라우더 🫧"


def today_kst() -> date:
    return datetime.now(KST).date()


class Requester(Protocol):
    """노트 도메인이 알아야 하는 '요청자' 정보 (user 도메인 User 가 그대로 만족)"""

    id: uuid.UUID
    name: str
    role: str


def is_admin(requester: Requester | None) -> bool:
    return requester is not None and requester.role == "ADMIN"


@dataclass(frozen=True)
class Author:
    key: str
    user_id: uuid.UUID | None = None
    nickname: str | None = None

    @classmethod
    def member(cls, user: Requester) -> "Author":
        return cls(key=f"u:{user.id}", user_id=user.id, nickname=user.name)

    @classmethod
    def guest(cls, ip_hash: str) -> "Author":
        return cls(key=f"g:{ip_hash}")

    @property
    def is_guest(self) -> bool:
        return self.user_id is None


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _clean_tags(tags: list[str] | None) -> list[str]:
    result: list[str] = []
    for raw in tags or []:
        tag = raw.strip().lstrip("#").lower()
        if tag and tag not in result:
            result.append(tag)
    return result


@dataclass
class Note:
    space_id: str
    author: Author
    learned: str | None = None
    achieved: str | None = None
    proud_of_me: str | None = None
    tags: list[str] = field(default_factory=list)
    guest_password_hash: str | None = None
    posted_on: date = field(default_factory=today_kst)
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        self.learned = _clean_text(self.learned)
        self.achieved = _clean_text(self.achieved)
        self.proud_of_me = _clean_text(self.proud_of_me)
        self.tags = _clean_tags(self.tags)
        self._validate()

    @classmethod
    def write(
        cls,
        *,
        space_id: str,
        author: Author,
        contents: dict[str, Any],
        tags: list[str] | None,
        guest_password: str | None,
        hasher: PasswordHasher,
    ) -> "Note":
        password_hash = None
        if author.is_guest:
            if not guest_password or not 4 <= len(guest_password) <= 20:
                raise GuestPasswordRequired()
            password_hash = hasher.hash(guest_password)
        return cls(
            space_id=space_id,
            author=author,
            tags=tags or [],
            guest_password_hash=password_hash,
            **{k: contents.get(k) for k in CONTENT_FIELDS},
        )

    # ---- 권한 ----
    def is_owned_by(self, requester: Requester | None) -> bool:
        return requester is not None and self.author.user_id == requester.id

    def ensure_editable(
        self,
        requester: Requester | None,
        guest_password: str | None,
        hasher: PasswordHasher,
    ) -> None:
        if is_admin(requester):
            return
        if self.author.is_guest:
            if not guest_password:
                raise GuestPasswordRequired(
                    "X-Guest-Password 헤더로 비밀번호를 보내 주세요 🔑"
                )
            if not self.guest_password_hash or not hasher.verify(
                guest_password, self.guest_password_hash
            ):
                raise GuestPasswordMismatch()
            return
        if not self.is_owned_by(requester):
            raise NotOwner()

    # ---- 변경 ----
    def edit(self, changes: dict[str, Any]) -> None:
        for key in CONTENT_FIELDS:
            if key in changes:
                setattr(self, key, _clean_text(changes[key]))
        if "tags" in changes:
            self.tags = _clean_tags(changes["tags"])
        self._validate()
        self.updated_at = utcnow()

    def soft_delete(self) -> None:
        self.deleted_at = utcnow()

    def display_name(self, anonymous: bool) -> str:
        if anonymous:
            return ANONYMOUS_NAME
        return self.author.nickname or "탈퇴한 프라우더"

    def _validate(self) -> None:
        errors: dict[str, list[str]] = {}
        if not any(getattr(self, k) for k in CONTENT_FIELDS):
            errors["non_field_errors"] = [
                "알게 된 것 · 해낸 것 · 오늘의 나 중 하나는 꼭 적어 주세요 🌱"
            ]
        for key in CONTENT_FIELDS:
            value = getattr(self, key)
            if value and len(value) > CONTENT_MAX:
                errors[key] = [f"{CONTENT_MAX}자 이하로 적어 주세요."]
        if len(self.tags) > MAX_TAGS:
            errors["tags"] = [f"태그는 최대 {MAX_TAGS}개예요."]
        bad = [t for t in self.tags if not TAG_RE.match(t)]
        if bad:
            errors.setdefault("tags", []).append(
                f"태그는 1~20자 한글/영문/숫자/_/- 만 가능해요: {', '.join(bad)}"
            )
        if errors:
            raise InvalidNote(errors=errors)


@dataclass
class Comment:
    note_id: int
    user_id: uuid.UUID | None
    author_name: str
    content: str
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        self.content = self._validate(self.content)

    @classmethod
    def write(cls, note_id: int, requester: Requester, content: str) -> "Comment":
        return cls(
            note_id=note_id,
            user_id=requester.id,
            author_name=requester.name,
            content=content,
        )

    def ensure_editable(self, requester: Requester) -> None:
        if not (is_admin(requester) or self.user_id == requester.id):
            raise NotOwner("내가 쓴 댓글만 고칠 수 있어요 🙅")

    def edit(self, content: str) -> None:
        self.content = self._validate(content)
        self.updated_at = utcnow()

    def soft_delete(self) -> None:
        self.deleted_at = utcnow()

    @staticmethod
    def _validate(content: str) -> str:
        content = (content or "").strip()
        if not 1 <= len(content) <= 500:
            raise InvalidNote(errors={"content": ["댓글은 1~500자로 적어 주세요."]})
        return content
