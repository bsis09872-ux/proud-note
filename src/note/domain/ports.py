from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """비회원 글 비밀번호 해싱"""

    @abstractmethod
    def hash(self, raw: str) -> str: ...

    @abstractmethod
    def verify(self, raw: str, hashed: str) -> bool: ...
