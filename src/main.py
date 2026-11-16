from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from shared.core.config import settings
from shared.core.database import close_db, engine
from shared.core.exception_handlers import register_exception_handlers
from shared.core.logger import get_logger, setup_logging
from shared.core.middlewares import register_middlewares
from shared.core.schemas import APIResponse

setup_logging()
logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s 시작 (env=%s)", settings.app_name, settings.app_env)
    yield
    await close_db()
    logger.info("%s 종료", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description="오늘 내가 알게 된 것, 해낸 것을 자랑하고 서로 이모지로 칭찬하는 TIL 공간",
    version="0.1.0",
    lifespan=lifespan,
)

register_middlewares(app)
register_exception_handlers(app)


@app.get("/health", tags=["System"], summary="헬스체크 (DB 연결 포함)")
async def health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        logger.exception("DB 헬스체크 실패")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=APIResponse.fail(
                "DB_UNAVAILABLE", "데이터베이스에 연결할 수 없습니다."
            ).model_dump(mode="json"),
        )
    return APIResponse.ok({"status": "ok", "db": "ok"})
