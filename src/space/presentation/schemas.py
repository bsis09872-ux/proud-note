from pydantic import BaseModel, ConfigDict


class SpaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    emoji: str
    description: str
    public_read: bool
    guest_write: bool
    anonymous: bool
    daily_limit: int | None
    max_notes: int | None
    allow_comments: bool
    page_size: int
