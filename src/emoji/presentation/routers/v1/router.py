from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from emoji.application.service import EmojiService
from emoji.domain.emoji import MAX_IMAGE_BYTES
from emoji.domain.exceptions import InvalidEmojiImage
from emoji.presentation.dependencies import provide_emoji_service
from emoji.presentation.schemas import (
    CustomEmojiResponse,
    ReactionCommand,
    ReactionSummaryResponse,
)
from shared.core.schemas import APIResponse
from user.domain.user import User
from user.presentation.dependencies import get_current_user, get_optional_user

router = APIRouter(prefix="/v1", tags=["Emoji"])

Service = Annotated[EmojiService, Depends(provide_emoji_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def _emoji_response(service: EmojiService, e) -> CustomEmojiResponse:
    return CustomEmojiResponse(
        name=e.name,
        code=e.code,
        image_url=service.image_url(e),
        created_at=e.created_at,
    )


# ---------- 커스텀 이모지 ----------
@router.get(
    "/emojis",
    summary="커스텀 이모지 목록",
    response_model=APIResponse[list[CustomEmojiResponse]],
)
async def list_emojis(service: Service):
    return APIResponse.ok(
        [_emoji_response(service, e) for e in await service.list_emojis()]
    )


@router.post(
    "/emojis",
    status_code=status.HTTP_201_CREATED,
    summary="커스텀 이모지 등록 (회원, multipart)",
    response_model=APIResponse[CustomEmojiResponse],
)
async def register_emoji(
    service: Service,
    user: CurrentUser,
    name: Annotated[
        str, Form(description="영문 소문자·숫자·_ 2~32자", examples=["party_parrot"])
    ],
    image: Annotated[UploadFile, File(description="PNG·GIF·JPG·WEBP, 256KB 이하")],
):
    data = await image.read(MAX_IMAGE_BYTES + 1)  # 한도+1 만 읽어서 큰 파일 차단
    if len(data) > MAX_IMAGE_BYTES:
        raise InvalidEmojiImage()
    emoji = await service.register(name, data, user)
    return APIResponse.ok(
        _emoji_response(service, emoji), f"{emoji.code} 등록 완료! 🎨"
    )


@router.delete(
    "/emojis/{name}", summary="커스텀 이모지 삭제", response_model=APIResponse[None]
)
async def delete_emoji(name: str, service: Service, user: CurrentUser):
    await service.remove(name, user)
    return APIResponse.ok(message="이모지를 지웠어요 🧹")


# ---------- 반응 ----------
@router.get(
    "/notes/{note_id}/reactions",
    summary="노트 반응 집계",
    response_model=APIResponse[list[ReactionSummaryResponse]],
)
async def reaction_summary(note_id: int, service: Service, user: OptionalUser):
    items = await service.summary(note_id, user)
    return APIResponse.ok([ReactionSummaryResponse(**asdict(i)) for i in items])


@router.post(
    "/notes/{note_id}/reactions",
    status_code=status.HTTP_201_CREATED,
    summary="반응 추가 (회원)",
    response_model=APIResponse[None],
)
async def react(
    note_id: int, command: ReactionCommand, service: Service, user: CurrentUser
):
    await service.react(note_id, command.emoji, user)
    return APIResponse.ok(message="반응을 남겼어요 💛")


@router.delete(
    "/notes/{note_id}/reactions",
    summary="반응 취소 (회원)",
    response_model=APIResponse[None],
)
async def unreact(
    note_id: int,
    service: Service,
    user: CurrentUser,
    emoji: Annotated[str, Query(min_length=1, max_length=40, examples=["🎉"])],
):
    await service.unreact(note_id, emoji, user)
    return APIResponse.ok(message="반응을 취소했어요")
