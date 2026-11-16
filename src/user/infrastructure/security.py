import bcrypt

from user.domain.service import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    def hash(self, raw_password: str) -> str:
        return bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    def verify(self, raw_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(raw_password.encode(), hashed_password.encode())
        except ValueError:  # 해시 형식이 깨진 경우
            return False
