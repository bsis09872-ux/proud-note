import hashlib
import hmac

import bcrypt

from note.domain.ports import PasswordHasher
from shared.core.config import settings


class BcryptPasswordHasher(PasswordHasher):
    def hash(self, raw: str) -> str:
        return bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()

    def verify(self, raw: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(raw.encode(), hashed.encode())
        except ValueError:
            return False


def hash_client_ip(ip: str) -> str:
    """IP 원문은 저장하지 않는다. 서버 비밀키로 HMAC -> 같은 IP 는 같은 값."""
    return hmac.new(
        settings.jwt_secret_key.encode(), ip.encode(), hashlib.sha256
    ).hexdigest()[:40]
