from typing import Any, ClassVar

from fastapi import status as http


class AppException(Exception):
    """모든 비즈니스 예외의 부모 (직접 생성 금지).

    하위 클래스는 클래스 키워드 인자로 상태·코드·기본 메시지를 선언한다.
        class NoteNotFound(NotFoundException, code="NOTE_NOT_FOUND", message="..."): ...
    raise 할 때는 메시지만 넘겨서 덮어쓸 수 있다.
        raise NoteNotFound("3번 노트가 없어요")
    """

    status_code: ClassVar[int]
    error_code: ClassVar[str]
    default_message: ClassVar[str]

    def __init_subclass__(
        cls,
        *,
        status: int | None = None,
        code: str | None = None,
        message: str | None = None,
        **kwargs: Any,
    ):
        super().__init_subclass__(**kwargs)
        if status is not None:
            cls.status_code = status
        if code is not None:
            cls.error_code = code
        if message is not None:
            cls.default_message = message
        # 부모에게도 없고 직접 선언도 안 했으면 import 시점에 바로 에러
        for attr in ("status_code", "error_code", "default_message"):
            if not hasattr(cls, attr):
                raise TypeError(f"{cls.__name__}: {attr} 이(가) 선언되지 않았습니다.")

    def __init__(self, message: str | None = None, *, errors: Any = None):
        if type(self) is AppException:
            raise TypeError("AppException은 직접 사용할 수 없습니다.")
        self.message = message or self.default_message
        self.errors = errors
        super().__init__(self.message)


# ---- 공통 예외 (도메인 예외는 이걸 상속해서 code·message만 바꾼다) ----
class BadRequestException(
    AppException,
    status=http.HTTP_400_BAD_REQUEST,
    code="BAD_REQUEST",
    message="잘못된 요청입니다.",
): ...


class UnauthorizedException(
    AppException,
    status=http.HTTP_401_UNAUTHORIZED,
    code="UNAUTHORIZED",
    message="인증이 필요합니다.",
): ...


class ForbiddenException(
    AppException,
    status=http.HTTP_403_FORBIDDEN,
    code="FORBIDDEN",
    message="권한이 없습니다.",
): ...


class NotFoundException(
    AppException,
    status=http.HTTP_404_NOT_FOUND,
    code="NOT_FOUND",
    message="리소스를 찾을 수 없습니다.",
): ...


class ConflictException(
    AppException,
    status=http.HTTP_409_CONFLICT,
    code="CONFLICT",
    message="이미 존재하는 리소스입니다.",
): ...


class ValidationException(
    AppException,
    status=http.HTTP_422_UNPROCESSABLE_CONTENT,
    code="VALIDATION_ERROR",
    message="입력값 검증에 실패했습니다.",
): ...
