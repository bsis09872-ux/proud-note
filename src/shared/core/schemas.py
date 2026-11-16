from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class APIResponse[T](BaseModel):
    """성공/실패 모두 같은 모양으로 응답한다."""

    success: bool
    code: str = Field(description="성공 시 OK, 실패 시 에러 코드")
    message: str | None = None
    data: T | None = None
    errors: Any = Field(default=None, description="실패 시 상세 (필드별 오류 등)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def ok(
        cls, data: T | None = None, message: str = "요청이 성공했습니다."
    ) -> "APIResponse[T]":
        return cls(success=True, code="OK", message=message, data=data)

    @classmethod
    def fail(cls, code: str, message: str, errors: Any = None) -> "APIResponse[None]":
        return cls(success=False, code=code, message=message, errors=errors)


class PageResponse[T](BaseModel):
    """목록 페이징 공통 응답"""

    items: list[T]
    total: int
    page: int
    size: int
    total_pages: int

    @classmethod
    def of(cls, items: list[T], total: int, page: int, size: int) -> "PageResponse[T]":
        total_pages = (total + size - 1) // size if size else 0
        return cls(
            items=items, total=total, page=page, size=size, total_pages=total_pages
        )
