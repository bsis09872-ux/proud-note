from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status

from note.application.dto import (
    CommentCreateCommand,
    CommentUpdateCommand,
    NoteCreateCommand,
    NoteListQuery,
    NoteUpdateCommand,
)
from note.application.guide import writing_guide
from note.application.service import CommentService, NoteService
from note.presentation.dependencies import (
    get_client_ip_hash,
    provide_comment_service,
    provide_note_service,
)
from note.presentation.schemas import CommentResponse, NoteResponse
from shared.core.schemas import APIResponse, PageResponse
from user.domain.user import User
from user.presentation.dependencies import get_current_user, get_optional_user

router = APIRouter(prefix="/v1", tags=["Note"])

Notes = Annotated[NoteService, Depends(provide_note_service)]
Comments = Annotated[CommentService, Depends(provide_comment_service)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
CurrentUser = Annotated[User, Depends(get_current_user)]
GuestPassword = Annotated[
    str | None, Header(alias="X-Guest-Password", description="비회원 글 수정·삭제 시")
]


# ---------- 가이드 ----------
@router.get(
    "/notes/writing-guide", summary="글쓰기 가이드", response_model=APIResponse[dict]
)
async def get_writing_guide(
    space_id: str | None = Query(default=None, examples=["plaza"]),
):
    return APIResponse.ok(writing_guide(space_id))


# ---------- 노트 ----------
@router.get(
    "/spaces/{space_id}/notes",
    summary="노트 목록 (최신순, 태그·키워드 검색)",
    response_model=APIResponse[PageResponse[NoteResponse]],
)
async def list_notes(
    space_id: str,
    query: Annotated[NoteListQuery, Query()],
    service: Notes,
    user: OptionalUser,
):
    space, page = await service.list_notes(space_id, query, user)
    items = [NoteResponse.of(n, space, user) for n in page.items]
    return APIResponse.ok(PageResponse.of(items, page.total, page.page, page.size))


@router.post(
    "/spaces/{space_id}/notes",
    status_code=status.HTTP_201_CREATED,
    summary="노트 작성 (광장은 비회원도 가능)",
    response_model=APIResponse[NoteResponse],
)
async def write_note(
    space_id: str,
    command: NoteCreateCommand,
    service: Notes,
    user: OptionalUser,
    ip_hash: Annotated[str, Depends(get_client_ip_hash)],
):
    view = await service.write(space_id, command, user, ip_hash)
    return APIResponse.ok(NoteResponse.from_view(view, user), "오늘의 자랑 완료! 🎉")


@router.get(
    "/notes/{note_id}", summary="노트 상세", response_model=APIResponse[NoteResponse]
)
async def get_note(note_id: int, service: Notes, user: OptionalUser):
    return APIResponse.ok(
        NoteResponse.from_view(await service.get_readable(note_id, user), user)
    )


@router.patch(
    "/notes/{note_id}", summary="노트 수정", response_model=APIResponse[NoteResponse]
)
async def edit_note(
    note_id: int,
    command: NoteUpdateCommand,
    service: Notes,
    user: OptionalUser,
    guest_password: GuestPassword = None,
):
    view = await service.edit(note_id, command, user, guest_password)
    return APIResponse.ok(NoteResponse.from_view(view, user), "수정했어요 ✏️")


@router.delete(
    "/notes/{note_id}", summary="노트 삭제", response_model=APIResponse[None]
)
async def delete_note(
    note_id: int,
    service: Notes,
    user: OptionalUser,
    guest_password: GuestPassword = None,
):
    await service.delete(note_id, user, guest_password)
    return APIResponse.ok(message="삭제했어요 🧹")


# ---------- 칭찬 댓글 ----------
@router.get(
    "/notes/{note_id}/comments",
    summary="댓글 목록",
    response_model=APIResponse[list[CommentResponse]],
)
async def list_comments(note_id: int, service: Comments, user: OptionalUser):
    comments = await service.list_comments(note_id, user)
    return APIResponse.ok([CommentResponse.of(c, user) for c in comments])


@router.post(
    "/notes/{note_id}/comments",
    status_code=status.HTTP_201_CREATED,
    summary="칭찬 댓글 작성 (회원)",
    response_model=APIResponse[CommentResponse],
)
async def write_comment(
    note_id: int, command: CommentCreateCommand, service: Comments, user: CurrentUser
):
    comment = await service.write(note_id, command, user)
    return APIResponse.ok(CommentResponse.of(comment, user), "칭찬을 남겼어요 💌")


@router.patch(
    "/comments/{comment_id}",
    summary="댓글 수정",
    response_model=APIResponse[CommentResponse],
)
async def edit_comment(
    comment_id: int, command: CommentUpdateCommand, service: Comments, user: CurrentUser
):
    comment = await service.edit(comment_id, command, user)
    return APIResponse.ok(CommentResponse.of(comment, user))


@router.delete(
    "/comments/{comment_id}", summary="댓글 삭제", response_model=APIResponse[None]
)
async def delete_comment(comment_id: int, service: Comments, user: CurrentUser):
    await service.delete(comment_id, user)
    return APIResponse.ok(message="삭제했어요 🧹")
