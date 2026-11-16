from shared.core.models import Base, TimestampMixin
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from space.domain.space import Space


class SpaceModel(Base, TimestampMixin):
    __tablename__ = "spaces"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    emoji: Mapped[str] = mapped_column(String(16), nullable=False, default="")
    description: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    public_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    guest_write: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    daily_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_notes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    allow_comments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    page_size: Mapped[int] = mapped_column(Integer, nullable=False, default=20)

    POLICY_FIELDS = (
        "name",
        "emoji",
        "description",
        "public_read",
        "guest_write",
        "anonymous",
        "daily_limit",
        "max_notes",
        "allow_comments",
        "page_size",
    )

    def to_entity(self) -> Space:
        return Space(
            id=self.id,
            **{f: getattr(self, f) for f in self.POLICY_FIELDS},
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def apply(self, space: Space) -> None:
        for f in self.POLICY_FIELDS:
            setattr(self, f, getattr(space, f))
