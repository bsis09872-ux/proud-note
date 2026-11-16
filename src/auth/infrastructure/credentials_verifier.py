import uuid

import bcrypt

from auth.domain.service import UserCredentialVerifier
from user.domain.repository import UserRepository
from user.domain.service import PasswordHasher

# 없는 이메일이어도 bcrypt 를 한 번 돌려서 응답 시간으로 가입 여부를 알 수 없게 한다
_DUMMY_HASH = bcrypt.hashpw(b"proud-note-dummy", bcrypt.gensalt()).decode()


class UserCredentialVerifierImpl(UserCredentialVerifier):
    def __init__(self, user_repo: UserRepository, password_hasher: PasswordHasher):
        self._user_repo = user_repo
        self._hasher = password_hasher

    async def verify(self, email: str, password: str) -> uuid.UUID | None:
        user = await self._user_repo.find_by_email(email)
        if user is None:
            self._hasher.verify(password, _DUMMY_HASH)
            return None
        if not self._hasher.verify(password, user.password_hash):
            return None
        # 튜터 코드는 탈퇴 회원도 로그인 가능했음 -> 차단
        if user.resign:
            return None
        return user.id
