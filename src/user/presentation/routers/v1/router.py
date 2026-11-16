import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from shared.core.schemas import APIResponse
from user.application.dto import (
    ChangePasswordCommand,
    SignUpCommand,
    UpdateProfileCommand,
)
from user.application.service import UserService
from user.domain.user import User
from user.presentation.dependencies import (
    get_current_user,
    provide_user_service,
    require_admin,
)
from user.presentation.schemas import UserResponse

router = APIRouter(prefix="/v1/users", tags=["User"])

Service = Annotated[UserService, Depends(provide_user_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
    response_model=APIResponse[UserResponse],
)
async def sign_up(command: SignUpCommand, service: Service):
    user = await service.sign_up(command)
    return APIResponse.ok(UserResponse.model_validate(user), "가입을 환영해요! 🌱")


@router.get("/me", summary="내 정보", response_model=APIResponse[UserResponse])
async def get_me(user: CurrentUser):
    return APIResponse.ok(UserResponse.model_validate(user))


@router.patch("/me", summary="닉네임 수정", response_model=APIResponse[UserResponse])
async def update_me(command: UpdateProfileCommand, service: Service, user: CurrentUser):
    updated = await service.update_profile(user.id, command)
    return APIResponse.ok(UserResponse.model_validate(updated), "닉네임을 바꿨어요.")


# 튜터 코드는 PATCH /users/{user_id}/password 로 인증 없이 남의 비밀번호를 바꿀 수 있었음 -> /me 로 수정
@router.patch("/me/password", summary="비밀번호 변경", response_model=APIResponse[None])
async def change_password(
    command: ChangePasswordCommand, service: Service, user: CurrentUser
):
    await service.change_password(user.id, command)
    return APIResponse.ok(message="비밀번호를 바꿨어요.")


@router.delete("/me", summary="회원 탈퇴", response_model=APIResponse[None])
async def withdraw_me(service: Service, user: CurrentUser):
    await service.withdraw(user.id, user)
    return APIResponse.ok(message="탈퇴했어요. 그동안 고마웠어요 🌷")


@router.delete(
    "/{user_id}", summary="회원 탈퇴 처리 (관리자)", response_model=APIResponse[None]
)
async def withdraw_user(
    user_id: uuid.UUID, service: Service, admin: Annotated[User, Depends(require_admin)]
):
    await service.withdraw(user_id, admin)
    return APIResponse.ok(message="탈퇴 처리했어요.")
