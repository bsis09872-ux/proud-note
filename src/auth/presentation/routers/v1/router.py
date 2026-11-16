from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials

from auth.application.dto import LoginCommand
from auth.application.service import AuthService
from auth.domain.exceptions import InvalidToken
from auth.presentation.dependencies import bearer_scheme, provide_auth_service
from auth.presentation.schemas import TokenResponse
from shared.core.schemas import APIResponse

router = APIRouter(prefix="/v1/auth", tags=["Auth"])

Service = Annotated[AuthService, Depends(provide_auth_service)]


@router.post(
    "/login", summary="로그인 (JWT 발급)", response_model=APIResponse[TokenResponse]
)
async def login(command: LoginCommand, service: Service):
    token = await service.login(command)
    return APIResponse.ok(
        TokenResponse(access_token=token.access_token, expires_in=token.expires_in),
        "어서 와요! 오늘도 자랑할 거리 있나요? ✨",
    )


@router.post(
    "/logout", summary="로그아웃 (토큰 무효화)", response_model=APIResponse[None]
)
async def logout(
    service: Service,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
):
    if credentials is None:
        raise InvalidToken("Authorization 헤더가 필요해요.")
    await service.logout(credentials.credentials)
    return APIResponse.ok(message="로그아웃했어요. 내일 또 만나요 👋")
