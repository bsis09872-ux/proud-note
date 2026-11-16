from datetime import datetime

from pydantic import BaseModel, Field


class CustomEmojiResponse(BaseModel):
    name: str
    code: str = Field(description="반응할 때 쓰는 값, 예: :party:")
    image_url: str
    created_at: datetime


class ReactionCommand(BaseModel):
    emoji: str = Field(min_length=1, max_length=40, examples=["🎉", ":party:"])


class ReactionSummaryResponse(BaseModel):
    emoji: str
    count: int
    reacted_by_me: bool
    image_url: str | None
