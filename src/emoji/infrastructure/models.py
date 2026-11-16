import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from emoji.domain.emoji import CustomEmoji
from shared.core.models import Base, TimestampMixin, utcnow


class CustomEmojiModel(Base, TimestampMixin):
    __tablename__ = "custom_emojis"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    def to_entity(self) -> CustomEmoji:
        return CustomEmoji(
            id=self.id,
            name=self.name,
            image_path=self.image_path,
            created_by=self.created_by,
            created_at=self.created_at,
        )


class ReactionModel(Base):
    __tablename__ = "note_reactions"
    __table_args__ = (UniqueConstraint("note_id", "user_id", "emoji"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    emoji: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        nullable=False,
    )
