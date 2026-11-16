import uuid

from user.application.dto import (
    ChangePasswordCommand,
    SignUpCommand,
    UpdateProfileCommand,
)
from user.domain.exceptions import EmailAlreadyExists, UserNotFound
from user.domain.repository import UserRepository
from user.domain.service import PasswordHasher
from user.domain.user import User


class UserService:
    def __init__(self, repository: UserRepository, hasher: PasswordHasher):
        self.repository = repository
        self.hasher = hasher

    async def sign_up(self, command: SignUpCommand) -> User:
        # 튜터 코드는 모든 예외를 ConflictException 으로 바꿔서 검증 에러가 409 로 나가던 버그 수정
        if await self.repository.find_by_email(command.email):
            raise EmailAlreadyExists()
        user = User.create(
            email=command.email,
            name=command.name,
            raw_password=command.password,
            hasher=self.hasher,
        )
        return await self.repository.save(user)

    async def get(self, user_id: uuid.UUID) -> User:
        user = await self.repository.find_by_id(user_id)
        if user is None:
            raise UserNotFound()
        return user

    async def update_profile(
        self, user_id: uuid.UUID, command: UpdateProfileCommand
    ) -> User:
        user = await self.get(user_id)
        user.update_profile(command.name)
        return await self.repository.save(user)

    async def change_password(
        self, user_id: uuid.UUID, command: ChangePasswordCommand
    ) -> None:
        user = await self.get(user_id)
        user.change_password(command.old_password, command.new_password, self.hasher)
        await self.repository.save(user)

    async def withdraw(self, user_id: uuid.UUID, requester: User) -> None:
        user = await self.get(user_id)
        user.withdraw(requester)
        await self.repository.save(user)
