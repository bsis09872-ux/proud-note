import uuid
from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, Index, String, Text, Uuid, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from note.domain.note import Author, Comment, Note
from shared.core.models import Base, SoftDeleteMixin, TimestampMixin


class NoteModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "notes"
    __table_args__ = (
        Index("ix_notes_space_id_created_at", "space_id", "created_at"),
        Index(
            "ix_notes_space_id_author_key_posted_on",
            "space_id",
            "author_key",
            "posted_on",
        ),
        Index("ix_notes_tags", "tags", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    space_id: Mapped[str] = mapped_column(
        String(30), ForeignKey("spaces.id"), nullable=False
    )

    learned: Mapped[str | None] = mapped_column(Text)
    achieved: Mapped[str | None] = mapped_column(Text)
    proud_of_me: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(20)), nullable=False, default=list, server_default=text("'{}'")
    )

    author_key: Mapped[str] = mapped_column(String(80), nullable=False)
    author_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    author_name: Mapped[str | None] = mapped_column(String(50))
    guest_password_hash: Mapped[str | None] = mapped_column(String(72))
    posted_on: Mapped[date] = mapped_column(Date, nullable=False)

    def to_entity(self) -> Note:
        return Note(
            id=self.id,
            space_id=self.space_id,
            author=Author(
                key=self.author_key,
                user_id=self.author_user_id,
                nickname=self.author_name,
            ),
            learned=self.learned,
            achieved=self.achieved,
            proud_of_me=self.proud_of_me,
            tags=list(self.tags or []),
            guest_password_hash=self.guest_password_hash,
            posted_on=self.posted_on,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
        )

    def apply(self, note: Note) -> None:
        self.space_id = note.space_id
        self.learned = note.learned
        self.achieved = note.achieved
        self.proud_of_me = note.proud_of_me
        self.tags = list(note.tags)
        self.author_key = note.author.key
        self.author_user_id = note.author.user_id
        self.author_name = note.author.nickname
        self.guest_password_hash = note.guest_password_hash
        self.posted_on = note.posted_on
        self.deleted_at = note.deleted_at


class CommentModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "note_comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    author_name: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    def to_entity(self) -> Comment:
        return Comment(
            id=self.id,
            note_id=self.note_id,
            user_id=self.user_id,
            author_name=self.author_name,
            content=self.content,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
        )

    def apply(self, comment: Comment) -> None:
        self.note_id = comment.note_id
        self.user_id = comment.user_id
        self.author_name = comment.author_name
        self.content = comment.content
        self.deleted_at = comment.deleted_at
