from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from auth.application.service import AuthService
from auth.presentation.dependencies import bearer_scheme, provide_auth_service
from shared.core.database import get_db
from shared.core.exceptions import UnauthorizedException
from user.application.service import UserService
from user.domain.exceptions import AdminRequired, UserWithdrawn
from user.domain.repository import UserRepository
from user.domain.service import PasswordHasher
from user.domain.user import User
from user.infrastructure.repositories import SqlAlchemyUserRepository
from user.infrastructure.security import BcryptPasswordHasher
from user.presentation.dependencies import (
    get_current_user,
    get_optional_user,
    provide_user_repository,
    provide_user_service,
    require_admin,
)

password_hasher: PasswordHasher = BcryptPasswordHasher()


def create_user_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def create_user_service(
    repository: Annotated[UserRepository, Depends(create_user_repository)],
) -> UserService:
    return UserService(repository=repository, hasher=password_hasher)


async def resolve_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    # provide_auth_service 도 override 되므로 wiring.auth 를 직접 import 할 필요 없음 (순환 import 방지)
    auth_service: Annotated[AuthService, Depends(provide_auth_service)],
    user_repo: Annotated[UserRepository, Depends(create_user_repository)],
) -> User | None:
    """토큰 없으면 None, 위조/만료/로그아웃 토큰이면 401"""
    if credentials is None:
        return None
    payload = await auth_service.authenticate(credentials.credentials)
    user = await user_repo.find_by_id(payload.user_id)
    if user is None:
        raise UnauthorizedException("존재하지 않는 회원이에요.")
    if user.resign:
        raise UserWithdrawn()
    return user


async def resolve_current_user(
    user: Annotated[User | None, Depends(resolve_optional_user)],
) -> User:
    if user is None:
        raise UnauthorizedException("로그인이 필요해요 🔐")
    return user


async def resolve_require_admin(
    user: Annotated[User, Depends(resolve_current_user)],
) -> User:
    if not user.is_admin:
        raise AdminRequired()
    return user


def wire_user_dependencies(app: FastAPI) -> None:
    app.dependency_overrides.update(
        {
            provide_user_repository: create_user_repository,
            provide_user_service: create_user_service,
            get_optional_user: resolve_optional_user,
            get_current_user: resolve_current_user,
            require_admin: resolve_require_admin,
        }
    )
