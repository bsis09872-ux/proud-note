from pydantic import BaseModel, Field


class SpaceUpdateCommand(BaseModel):
    """관리자 공간 정책 수정 (보낸 필드만 변경)"""

    name: str | None = Field(default=None, min_length=1, max_length=50)
    emoji: str | None = Field(default=None, max_length=16)
    description: str | None = Field(default=None, max_length=200)
    public_read: bool | None = None
    guest_write: bool | None = None
    anonymous: bool | None = None
    daily_limit: int | None = Field(default=None, ge=1, description="null = 무제한")
    max_notes: int | None = Field(default=None, ge=1, description="null = 무제한")
    allow_comments: bool | None = None
    page_size: int | None = Field(default=None, ge=1, le=100)

    def changes(self) -> dict:
        data = self.model_dump(exclude_unset=True)
        # daily_limit / max_notes 는 null 로 "무제한" 지정 가능, 나머지 null 은 무시
        nullable = {"daily_limit", "max_notes"}
        return {k: v for k, v in data.items() if v is not None or k in nullable}
