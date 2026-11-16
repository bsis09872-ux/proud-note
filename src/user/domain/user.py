"""회원 도메인 규칙

1. 비밀번호는 8자 이상, 영문·숫자·특수문자를 모두 포함한다.
2. 이메일은 유효한 형식이고 중복될 수 없다 (로그인 ID).
3. 닉네임(name)은 2~20자. 친구 공간에서 작성자 이름으로 보인다.
4. 탈퇴는 소프트 삭제 (deleted_at 기록 + resign=True).
5. 탈퇴는 본인 또는 관리자만 가능하다.
"""

import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from shared.core.models import utcnow
from user.domain.exceptions import (
    InvalidOldPassword,
    InvalidUser,
    SamePassword,
    UserWithdrawn,
    WithdrawForbidden,
)
from user.domain.service import PasswordHasher

EMAIL_REGEX = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
PASSWORD_REGEX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z\d\s]).{8,64}$")

Role = Literal["USER", "ADMIN"]


@dataclass
class User:
    email: str
    name: str
    password_hash: str
    role: Role = "USER"
    resign: bool = False
    id: uuid.UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        self.email = self.email.strip().lower()
        self.name = self.name.strip()
        self._validate_email(self.email)
        self._validate_name(self.name)

    @classmethod
    def create(
        cls, email: str, name: str, raw_password: str, hasher: PasswordHasher
    ) -> "User":
        cls._validate_password(raw_password)
        return cls(email=email, name=name, password_hash=hasher.hash(raw_password))

    @property
    def is_admin(self) -> bool:
        return self.role == "ADMIN"

    def ensure_active(self) -> None:
        if self.resign:
            raise UserWithdrawn()

    def update_profile(self, name: str) -> None:
        self.ensure_active()
        self._validate_name(name.strip())
        self.name = name.strip()
        self.updated_at = utcnow()

    def change_password(
        self, old_password: str, new_password: str, hasher: PasswordHasher
    ) -> None:
        self.ensure_active()
        if not hasher.verify(old_password, self.password_hash):
            raise InvalidOldPassword()
        if old_password == new_password:
            raise SamePassword()
        self._validate_password(new_password)
        self.password_hash = hasher.hash(new_password)
        self.updated_at = utcnow()

    def withdraw(self, requester: "User") -> None:
        self.ensure_active()
        if not (requester.id == self.id or requester.is_admin):
            raise WithdrawForbidden()
        now = utcnow()
        self.resign = True
        self.deleted_at = now
        self.updated_at = now

    @staticmethod
    def _validate_email(email: str) -> None:
        if not EMAIL_REGEX.match(email):
            raise InvalidUser(errors={"email": ["올바른 이메일 형식을 입력해 주세요."]})

    @staticmethod
    def _validate_name(name: str) -> None:
        if not 2 <= len(name) <= 20:
            raise InvalidUser(errors={"name": ["닉네임은 2~20자여야 해요."]})

    @staticmethod
    def _validate_password(raw: str) -> None:
        if not PASSWORD_REGEX.match(raw):
            raise InvalidUser(
                errors={
                    "password": ["8~64자, 영문·숫자·특수문자를 모두 포함해 주세요."]
                }
            )
