from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from auth.domain.repository import TokenBlacklistRepository
from auth.infrastructure.models import TokenBlacklistModel


class SqlAlchemyTokenBlacklistRepository(TokenBlacklistRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, jti: str, expired_at: datetime) -> None:
        # 같은 토큰으로 로그아웃 두 번 해도 에러 안 나게
        await self.session.execute(
            insert(TokenBlacklistModel)
            .values(jti=jti, expired_at=expired_at)
            .on_conflict_do_nothing(index_elements=["jti"])
        )

    async def is_blacklisted(self, jti: str) -> bool:
        found = await self.session.scalar(
            select(TokenBlacklistModel.jti).where(TokenBlacklistModel.jti == jti)
        )
        return found is not None

    async def cleanup_expired(self, now: datetime) -> int:
        result = await self.session.execute(
            delete(TokenBlacklistModel).where(TokenBlacklistModel.expired_at <= now)
        )
        return result.rowcount or 0
