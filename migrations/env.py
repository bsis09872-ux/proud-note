import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# 모든 모델을 import 해야 autogenerate 가 테이블을 인식한다
import auth.infrastructure.models  # noqa: F401
import emoji.infrastructure.models  # noqa: F401
import note.infrastructure.models  # noqa: F401
import space.infrastructure.models  # noqa: F401
import user.infrastructure.models  # noqa: F401
from shared.core.config import settings
from shared.core.database import connect_args
from shared.core.models import Base

config = context.config
# % 는 configparser 에서 특수문자라 이스케이프 (비밀번호에 % 가 있을 수 있음)
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=target_metadata, compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(
        settings.database_url, poolclass=pool.NullPool, connect_args=connect_args()
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
