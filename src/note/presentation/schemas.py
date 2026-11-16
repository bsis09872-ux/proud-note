from datetime import date, datetime

from pydantic import BaseModel

from note.application.service import NoteView
from note.domain.note import Comment, Note, Requester
from space.domain.space import Space


class NoteResponse(BaseModel):
    id: int
    space_id: str
    author_name: str
    is_guest: bool
    is_mine: bool
    learned: str | None
    achieved: str | None
    proud_of_me: str | None
    tags: list[str]
    posted_on: date
    created_at: datetime
    updated_at: datetime | None

    @classmethod
    def of(
        cls, note: Note, space: Space, requester: Requester | None
    ) -> "NoteResponse":
        return cls(
            id=note.id,
            space_id=note.space_id,
            author_name=note.display_name(space.anonymous),
            is_guest=note.author.is_guest,
            is_mine=note.is_owned_by(requester),
            learned=note.learned,
            achieved=note.achieved,
            proud_of_me=note.proud_of_me,
            tags=note.tags,
            posted_on=note.posted_on,
            created_at=note.created_at,
            updated_at=note.updated_at,
        )

    @classmethod
    def from_view(cls, view: NoteView, requester: Requester | None) -> "NoteResponse":
        return cls.of(view.note, view.space, requester)


class CommentResponse(BaseModel):
    id: int
    note_id: int
    author_name: str
    is_mine: bool
    content: str
    created_at: datetime
    updated_at: datetime | None

    @classmethod
    def of(cls, comment: Comment, requester: Requester | None) -> "CommentResponse":
        return cls(
            id=comment.id,
            note_id=comment.note_id,
            author_name=comment.author_name,
            is_mine=requester is not None and comment.user_id == requester.id,
            content=comment.content,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )
