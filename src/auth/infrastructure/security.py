import uuid
from datetime import UTC, datetime, timedelta

import jwt

from auth.domain.entities import IssuedToken, TokenPayload
from auth.domain.exceptions import InvalidToken
from auth.domain.service import TokenProvider
from shared.core.config import settings


class JwtTokenProvider(TokenProvider):
    # 튜터 코드는 os.getenv + 하드코딩 기본 키 -> 설정(.env)에서만 읽도록 수정 (키 없으면 기동 실패)
    def __init__(
        self,
        secret_key: str = settings.jwt_secret_key,
        algorithm: str = settings.jwt_algorithm,
        expire_minutes: int = settings.access_token_expire_minutes,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes

    def issue(self, user_id: uuid.UUID) -> IssuedToken:
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=self.expire_minutes)
        jti = str(uuid.uuid4())
        token = jwt.encode(
            {"sub": str(user_id), "jti": jti, "iat": now, "exp": expires_at},
            self.secret_key,
            algorithm=self.algorithm,
        )
        return IssuedToken(
            access_token=token,
            jti=jti,
            expires_at=expires_at,
            expires_in=self.expire_minutes * 60,
        )

    def decode(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"require": ["sub", "jti", "exp"]},
            )
            return TokenPayload(
                user_id=uuid.UUID(payload["sub"]),
                jti=payload["jti"],
                exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
            )
        except (jwt.PyJWTError, KeyError, ValueError) as err:
            raise InvalidToken() from err
