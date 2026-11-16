import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TokenPayload:
    user_id: uuid.UUID
    jti: str
    exp: datetime


@dataclass(frozen=True)
class IssuedToken:
    access_token: str
    jti: str
    expires_at: datetime
    expires_in: int  # 초
    token_type: str = "bearer"
