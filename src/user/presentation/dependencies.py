"""플레이스홀더. 실제 구현은 wiring/user.py 에서 dependency_overrides 로 연결한다."""

from user.application.service import UserService
from user.domain.repository import UserRepository
from user.domain.user import User


def provide_user_repository() -> UserRepository:
    raise NotImplementedError("UserRepository 의존성이 주입되지 않았습니다.")


def provide_user_service() -> UserService:
    raise NotImplementedError("UserService 의존성이 주입되지 않았습니다.")


async def get_optional_user() -> User | None:
    """토큰 없으면 None, 잘못된 토큰이면 401"""
    raise NotImplementedError("get_optional_user 의존성이 주입되지 않았습니다.")


async def get_current_user() -> User:
    """로그인 필수"""
    raise NotImplementedError("get_current_user 의존성이 주입되지 않았습니다.")


async def require_admin() -> User:
    """관리자 필수"""
    raise NotImplementedError("require_admin 의존성이 주입되지 않았습니다.")
