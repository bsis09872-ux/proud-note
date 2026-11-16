from shared.core.exceptions import UnauthorizedException


class InvalidCredentials(
    UnauthorizedException,
    code="INVALID_CREDENTIALS",
    message="이메일 또는 비밀번호가 올바르지 않아요.",
): ...


class InvalidToken(
    UnauthorizedException,
    code="INVALID_TOKEN",
    message="유효하지 않거나 만료된 토큰이에요.",
): ...


class TokenRevoked(
    UnauthorizedException, code="TOKEN_REVOKED", message="로그아웃된 토큰이에요."
): ...
