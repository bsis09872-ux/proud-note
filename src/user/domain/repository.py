import uuid
from abc import ABC, abstractmethod

from user.domain.user import User


class UserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, user_id: uuid.UUID) -> User | None: ...

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def save(self, user: User) -> User:
        """id 없으면 INSERT, 있으면 UPDATE"""
