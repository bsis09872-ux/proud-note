from shared.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)


class NoteNotFound(
    NotFoundException, code="NOTE_NOT_FOUND", message="노트를 찾을 수 없어요 🥲"
): ...


class CommentNotFound(
    NotFoundException, code="COMMENT_NOT_FOUND", message="댓글을 찾을 수 없어요 🥲"
): ...


class InvalidNote(
    ValidationException, code="INVALID_NOTE", message="노트 내용을 확인해 주세요 ✍️"
): ...


class DailyLimitExceeded(
    ConflictException,
    code="DAILY_LIMIT_EXCEEDED",
    message="광장엔 하루 한 번만 올릴 수 있어요 🌙",
): ...


class GuestPasswordRequired(
    BadRequestException,
    code="GUEST_PASSWORD_REQUIRED",
    message="비회원은 비밀번호(4~20자)가 필요해요 🔑",
): ...


class NotOwner(
    ForbiddenException, code="NOT_OWNER", message="내가 쓴 글만 고칠 수 있어요 🙅"
): ...


class GuestPasswordMismatch(
    ForbiddenException,
    code="GUEST_PASSWORD_MISMATCH",
    message="비밀번호가 맞지 않아요 🔒",
): ...
