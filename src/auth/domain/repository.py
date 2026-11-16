from abc import ABC, abstractmethod
from datetime import datetime


class TokenBlacklistRepository(ABC):
    @abstractmethod
    async def add(self, jti: str, expired_at: datetime) -> None: ...

    @abstractmethod
    async def is_blacklisted(self, jti: str) -> bool: ...

    @abstractmethod
    async def cleanup_expired(self, now: datetime) -> int:
        """만료된 항목 정리 (어차피 토큰 자체가 만료라 보관할 필요 없음)"""
