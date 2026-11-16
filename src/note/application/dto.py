"""Pydantic CQRS: 쓰기 = Command, 읽기 = Query"""

from pydantic import BaseModel, Field


class NoteCreateCommand(BaseModel):
    learned: str | None = Field(
        default=None, max_length=1000, description="📚 오늘 알게 된 것"
    )
    achieved: str | None = Field(
        default=None, max_length=1000, description="🏆 오늘 해낸 것"
    )
    proud_of_me: str | None = Field(
        default=None, max_length=1000, description="🌷 오늘의 나"
    )
    tags: list[str] = Field(default_factory=list, max_length=5)
    guest_password: str | None = Field(
        default=None, min_length=4, max_length=20, description="비회원만 (수정·삭제용)"
    )

    def contents(self) -> dict:
        return {
            "learned": self.learned,
            "achieved": self.achieved,
            "proud_of_me": self.proud_of_me,
        }


class NoteUpdateCommand(BaseModel):
    """보낸 필드만 수정 (null 을 보내면 그 칸을 비움)"""

    learned: str | None = Field(default=None, max_length=1000)
    achieved: str | None = Field(default=None, max_length=1000)
    proud_of_me: str | None = Field(default=None, max_length=1000)
    tags: list[str] | None = Field(default=None, max_length=5)

    def changes(self) -> dict:
        data = self.model_dump(exclude_unset=True)
        if data.get("tags") is None:
            data.pop("tags", None)
        return data


class NoteListQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int | None = Field(
        default=None, ge=1, le=100, description="비우면 공간 기본값"
    )
    tag: str | None = Field(default=None, max_length=20)
    keyword: str | None = Field(default=None, min_length=1, max_length=50)


class CommentCreateCommand(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class CommentUpdateCommand(BaseModel):
    content: str = Field(min_length=1, max_length=500)
