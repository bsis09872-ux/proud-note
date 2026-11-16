import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from user.domain.repository import UserRepository
from user.domain.user import User
from user.infrastructure.models import UserModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        model = await self.session.get(UserModel, user_id)
        return model.to_entity() if model else None

    async def find_by_email(self, email: str) -> User | None:
        model = await self.session.scalar(
            select(UserModel).where(UserModel.email == email.strip().lower())
        )
        return model.to_entity() if model else None

    async def save(self, user: User) -> User:
        if user.id is None:
            model = UserModel()
            self.session.add(model)
        else:
            model = await self.session.get(UserModel, user.id)
            if model is None:
                raise ValueError(f"user {user.id} not found")
        model.apply(user)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()
