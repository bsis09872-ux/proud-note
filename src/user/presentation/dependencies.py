"""플레이스홀더. 실제 구현은 wiring/user.py 에서 dependency_overrides 로 연결한다.

bearer_scheme 을 파라미터로 선언해 두는 이유:
OpenAPI 문서는 override 전 원본 함수 기준으로 만들어진다. 여기서 선언하지 않으면
Swagger 가 이 API 에 인증이 필요하다는 걸 몰라서, Authorize 를 눌러도 토큰을 보내지 않는다.
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials

from auth.presentation.dependencies import bearer_scheme
from user.application.service import UserService
from user.domain.repository import UserRepository
from user.domain.user import User

Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def provide_user_repository() -> UserRepository:
    raise NotImplementedError("UserRepository 의존성이 주입되지 않았습니다.")


def provide_user_service() -> UserService:
    raise NotImplementedError("UserService 의존성이 주입되지 않았습니다.")


async def get_optional_user(credentials: Credentials) -> User | None:
    """토큰 없으면 None, 잘못된 토큰이면 401"""
    raise NotImplementedError("get_optional_user 의존성이 주입되지 않았습니다.")


async def get_current_user(credentials: Credentials) -> User:
    """로그인 필수"""
    raise NotImplementedError("get_current_user 의존성이 주입되지 않았습니다.")


async def require_admin(credentials: Credentials) -> User:
    """관리자 필수"""
    raise NotImplementedError("require_admin 의존성이 주입되지 않았습니다.")
