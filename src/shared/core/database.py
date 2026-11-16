import uuid
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shared.core.config import settings


def connect_args() -> dict[str, Any]:
    """asyncpg 연결 옵션 (Alembic 도 같은 옵션을 쓴다)"""
    args: dict[str, Any] = {}
    if settings.db_ssl:
        args["ssl"] = "require"
    if settings.db_use_pooler:
        # PgBouncer/Supavisor transaction 모드는 커넥션을 돌려 쓰기 때문에
        # prepared statement 를 캐시하면 "prepared statement already exists" 에러가 난다
        args["statement_cache_size"] = 0
        args["prepared_statement_cache_size"] = 0
        args["prepared_statement_name_func"] = lambda: f"__asyncpg_{uuid.uuid4()}__"
    return args


engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,  # 끊어진 커넥션 자동 감지
    pool_recycle=1800,  # 30분마다 커넥션 재생성
    echo=settings.sql_echo,
    connect_args=connect_args(),
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """요청 하나 = 트랜잭션 하나. 정상 종료 시 commit, 예외 시 rollback."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_db() -> None:
    await engine.dispose()
