import uuid
from abc import ABC, abstractmethod

from auth.domain.entities import IssuedToken, TokenPayload


class TokenProvider(ABC):
    @abstractmethod
    def issue(self, user_id: uuid.UUID) -> IssuedToken: ...

    @abstractmethod
    def decode(self, token: str) -> TokenPayload:
        """서명·만료 검증 실패 시 InvalidToken"""


class UserCredentialVerifier(ABC):
    @abstractmethod
    async def verify(self, email: str, password: str) -> uuid.UUID | None:
        """성공하면 user_id, 실패하면 None"""
