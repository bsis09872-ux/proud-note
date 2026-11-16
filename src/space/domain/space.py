"""공간(Space) = 게시판 설정.

| 정책          | friends | plaza            |
|---------------|---------|------------------|
| 비회원 열람   | X       | O                |
| 비회원 작성   | X       | O (비밀번호 필수) |
| 익명 표시     | X       | O                |
| 1인 하루 작성 | 무제한  | 1개              |
| 최대 보관     | 무제한  | 50개 (오래된 순 삭제) |
| 댓글          | O       | X                |
반응(이모지)은 공간과 상관없이 회원만 가능하다.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from shared.core.models import utcnow
from space.domain.exceptions import (
    CommentsDisabled,
    InvalidSpacePolicy,
    MembersOnlySpace,
)

FRIENDS = "friends"
PLAZA = "plaza"

# PATCH 로 바꿀 수 있는 필드
UPDATABLE_FIELDS = frozenset(
    {
        "name",
        "emoji",
        "description",
        "public_read",
        "guest_write",
        "anonymous",
        "daily_limit",
        "max_notes",
        "allow_comments",
        "page_size",
    }
)


@dataclass
class Space:
    id: str
    name: str
    emoji: str
    description: str
    public_read: bool = False
    guest_write: bool = False
    anonymous: bool = False
    daily_limit: int | None = None  # None = 무제한
    max_notes: int | None = None  # None = 무제한
    allow_comments: bool = True
    page_size: int = 20
    created_at: datetime | None = None
    updated_at: datetime | None = field(default=None)

    def __post_init__(self) -> None:
        self._validate()

    # ---- 정책 검사 ----
    def ensure_readable(self, is_member: bool) -> None:
        if not (self.public_read or is_member):
            raise MembersOnlySpace()

    def ensure_writable(self, is_member: bool) -> None:
        if not (self.guest_write or is_member):
            raise MembersOnlySpace("회원만 글을 쓸 수 있는 공간이에요 🏡")

    def ensure_commentable(self) -> None:
        if not self.allow_comments:
            raise CommentsDisabled()

    # ---- 변경 ----
    def update_policy(self, changes: dict[str, Any]) -> None:
        unknown = set(changes) - UPDATABLE_FIELDS
        if unknown:
            raise InvalidSpacePolicy(
                errors={k: ["변경할 수 없는 항목입니다."] for k in unknown}
            )
        for key, value in changes.items():
            setattr(self, key, value)
        self._validate()
        self.updated_at = utcnow()

    def _validate(self) -> None:
        errors: dict[str, list[str]] = {}
        if not self.name or not self.name.strip():
            errors["name"] = ["이름은 비워둘 수 없어요."]
        if not 1 <= self.page_size <= 100:
            errors["page_size"] = ["1~100 사이여야 해요."]
        if self.daily_limit is not None and self.daily_limit < 1:
            errors["daily_limit"] = ["1 이상이거나 비워둬야(무제한) 해요."]
        if self.max_notes is not None and self.max_notes < 1:
            errors["max_notes"] = ["1 이상이거나 비워둬야(무제한) 해요."]
        if self.guest_write and not self.public_read:
            errors["guest_write"] = [
                "비회원 작성을 허용하려면 비회원 열람도 허용해야 해요."
            ]
        if errors:
            raise InvalidSpacePolicy(errors=errors)


# 기본 공간 (Alembic 시드에서 사용)
DEFAULT_SPACES: list[dict[str, Any]] = [
    {
        "id": FRIENDS,
        "name": "친구 공간",
        "emoji": "🏡",
        "description": "친구들끼리 닉네임으로 오늘의 반짝임을 나누는 곳",
        "public_read": False,
        "guest_write": False,
        "anonymous": False,
        "daily_limit": None,
        "max_notes": None,
        "allow_comments": True,
        "page_size": 20,
    },
    {
        "id": PLAZA,
        "name": "광장",
        "emoji": "🌏",
        "description": "누구나 익명으로 하루 한 번 자랑하는 곳 (최신 50개만 머물러요)",
        "public_read": True,
        "guest_write": True,
        "anonymous": True,
        "daily_limit": 1,
        "max_notes": 50,
        "allow_comments": False,
        "page_size": 20,
    },
]
