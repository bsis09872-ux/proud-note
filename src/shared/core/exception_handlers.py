from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from shared.core.exceptions import AppException
from shared.core.logger import get_logger
from shared.core.schemas import APIResponse

logger = get_logger(__name__)


def _json(status_code: int, body: APIResponse) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


def register_exception_handlers(app: FastAPI) -> None:
    # 1) 우리가 던진 비즈니스 예외
    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        logger.warning(
            "[%s] %s %s - %s",
            exc.error_code,
            request.method,
            request.url.path,
            exc.message,
        )
        return _json(
            exc.status_code, APIResponse.fail(exc.error_code, exc.message, exc.errors)
        )

    # 2) Pydantic 요청 검증 실패 -> {"필드": ["메시지", ...]}
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        errors: dict[str, list[str]] = {}
        for err in exc.errors():
            field = ".".join(
                str(loc) for loc in err["loc"] if loc not in ("body", "query", "path")
            )
            errors.setdefault(field or "non_field_errors", []).append(err["msg"])
        return _json(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            APIResponse.fail(
                "REQUEST_VALIDATION_ERROR", "요청 입력값이 올바르지 않습니다.", errors
            ),
        )

    # 3) 없는 URL(404), 허용 안 된 메서드(405) 등 프레임워크 예외도 같은 형식으로
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        return _json(
            exc.status_code,
            APIResponse.fail(f"HTTP_{exc.status_code}", str(exc.detail)),
        )

    # 4) 예상 못한 서버 오류 -> 내부 정보는 숨기고 로그로만
    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        logger.exception("Unhandled error: %s %s", request.method, request.url.path)
        return _json(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            APIResponse.fail("INTERNAL_SERVER_ERROR", "서버 내부 오류가 발생했습니다."),
        )
