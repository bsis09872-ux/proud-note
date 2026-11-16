from shared.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)


class SpaceNotFound(
    NotFoundException, code="SPACE_NOT_FOUND", message="공간을 찾을 수 없어요 🧭"
): ...


class MembersOnlySpace(
    UnauthorizedException,
    code="MEMBERS_ONLY_SPACE",
    message="회원만 이용할 수 있는 공간이에요 🏡",
): ...


class CommentsDisabled(
    ForbiddenException,
    code="COMMENTS_DISABLED",
    message="이 공간에서는 댓글을 달 수 없어요 🤫",
): ...


class InvalidSpacePolicy(
    ValidationException,
    code="INVALID_SPACE_POLICY",
    message="공간 정책 값이 올바르지 않아요.",
): ...
