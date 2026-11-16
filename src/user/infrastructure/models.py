import uuid

from sqlalchemy import Boolean, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from shared.core.models import Base, SoftDeleteMixin, TimestampMixin
from user.domain.user import User


class UserModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="USER")
    resign: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def to_entity(self) -> User:
        return User(
            id=self.id,
            email=self.email,
            name=self.name,
            password_hash=self.password_hash,
            role=self.role,
            resign=self.resign,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
        )

    def apply(self, user: User) -> None:
        self.email = user.email
        self.name = user.name
        self.password_hash = user.password_hash
        self.role = user.role
        self.resign = user.resign
        self.deleted_at = user.deleted_at
