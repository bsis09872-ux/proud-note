"""통합 테스트: 진짜 PostgreSQL(테스트 전용 DB)에 Alembic 마이그레이션을 적용하고 API 를 호출한다.

TEST_DATABASE_URL 기본값: postgresql+asyncpg://proud:proud@localhost:5433/proud_note_test
(docker compose up -d 로 띄운 DB 에 proud_note_test DB 를 자동 생성)
"""

import os
import tempfile
from collections.abc import Callable, Iterator

import asyncpg
import pytest

TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://proud:proud@localhost:5433/proud_note_test",
)
# 앱 import 전에 설정을 바꿔야 한다 (settings 는 import 시점에 읽힘)
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["MEDIA_DIR"] = tempfile.mkdtemp(prefix="proud-note-media-")
os.environ.setdefault("LOG_LEVEL", "WARNING")

import anyio
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from shared.core.database import engine

PASSWORD = "Proud1234!"
TABLES = "users, token_blacklist, notes, note_comments, note_reactions, custom_emojis"


async def _ensure_database() -> None:
    plain = TEST_DB_URL.replace("+asyncpg", "")
    base, db_name = plain.rsplit("/", 1)
    conn = await asyncpg.connect(f"{base}/postgres")
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname=$1", db_name
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await conn.close()


async def _drop_all() -> None:
    plain = TEST_DB_URL.replace("+asyncpg", "")
    conn = await asyncpg.connect(plain)
    try:
        await conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    finally:
        await conn.close()


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    anyio.run(_ensure_database)
    anyio.run(_drop_all)
    command.upgrade(Config("alembic.ini"), "head")  # 마이그레이션 자체도 함께 검증

    from main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_db(client: TestClient) -> Iterator[None]:
    """테스트마다 데이터 초기화 (공간은 시드값으로 되돌림), 캐시도 비움"""

    async def reset() -> None:
        async with engine.begin() as conn:
            await conn.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))
            await conn.execute(
                text(
                    "UPDATE spaces SET page_size=20, daily_limit=1, max_notes=50 WHERE id='plaza'"
                )
            )

    client.portal.call(reset)
    from wiring.emoji import emoji_cache, reaction_cache

    emoji_cache.clear()
    reaction_cache.clear()
    yield


def run_sql(client: TestClient, sql: str, **params) -> None:
    async def _run() -> None:
        async with engine.begin() as conn:
            await conn.execute(text(sql), params)

    client.portal.call(_run)


@pytest.fixture
def signup(client: TestClient) -> Callable[..., dict]:
    """회원가입 + 로그인 -> Authorization 헤더 반환"""

    def _signup(email: str, name: str = "프라우더", admin: bool = False) -> dict:
        r = client.post(
            "/v1/users", json={"email": email, "name": name, "password": PASSWORD}
        )
        assert r.status_code == 201, r.text
        if admin:
            run_sql(client, "UPDATE users SET role='ADMIN' WHERE email=:e", e=email)
        r = client.post("/v1/auth/login", json={"email": email, "password": PASSWORD})
        return {"Authorization": f"Bearer {r.json()['data']['access_token']}"}

    return _signup
