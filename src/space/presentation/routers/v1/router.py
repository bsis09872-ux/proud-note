from typing import Annotated

from fastapi import APIRouter, Depends

from shared.core.schemas import APIResponse
from space.application.dto import SpaceUpdateCommand
from space.application.service import SpaceService
from space.presentation.dependencies import provide_space_service
from space.presentation.schemas import SpaceResponse
from user.domain.user import User
from user.presentation.dependencies import require_admin

router = APIRouter(prefix="/v1/spaces", tags=["Space"])

Service = Annotated[SpaceService, Depends(provide_space_service)]


@router.get("", summary="공간 목록", response_model=APIResponse[list[SpaceResponse]])
async def list_spaces(service: Service):
    spaces = await service.list_spaces()
    return APIResponse.ok([SpaceResponse.model_validate(s) for s in spaces])


@router.get(
    "/{space_id}", summary="공간 정책 조회", response_model=APIResponse[SpaceResponse]
)
async def get_space(space_id: str, service: Service):
    return APIResponse.ok(
        SpaceResponse.model_validate(await service.get_space(space_id))
    )


@router.patch(
    "/{space_id}",
    summary="공간 정책 수정 (관리자)",
    response_model=APIResponse[SpaceResponse],
)
async def update_space(
    space_id: str,
    command: SpaceUpdateCommand,
    service: Service,
    _: Annotated[User, Depends(require_admin)],
):
    space = await service.update_space(space_id, command)
    return APIResponse.ok(SpaceResponse.model_validate(space), "공간 정책을 바꿨어요.")
