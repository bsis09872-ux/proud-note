from shared.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)


class UserNotFound(
    NotFoundException, code="USER_NOT_FOUND", message="회원을 찾을 수 없어요."
): ...


class EmailAlreadyExists(
    ConflictException,
    code="EMAIL_ALREADY_EXISTS",
    message="이미 사용 중인 이메일이에요.",
): ...


class InvalidUser(
    ValidationException, code="INVALID_USER", message="회원 정보를 확인해 주세요."
): ...


class UserWithdrawn(
    ForbiddenException, code="USER_WITHDRAWN", message="탈퇴한 회원은 이용할 수 없어요."
): ...


class InvalidOldPassword(
    BadRequestException,
    code="INVALID_OLD_PASSWORD",
    message="기존 비밀번호가 일치하지 않아요.",
): ...


class SamePassword(
    BadRequestException,
    code="SAME_PASSWORD",
    message="새 비밀번호는 이전과 달라야 해요.",
): ...


class WithdrawForbidden(
    ForbiddenException,
    code="WITHDRAW_PERMISSION_DENIED",
    message="탈퇴는 본인 또는 관리자만 할 수 있어요.",
): ...


class AdminRequired(
    ForbiddenException, code="ADMIN_REQUIRED", message="관리자 권한이 필요해요."
): ...
