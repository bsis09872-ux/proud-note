from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from auth.presentation.routers.v1.router import router as auth_router
from emoji.presentation.routers.v1.router import router as emoji_router
from note.presentation.routers.v1.router import router as note_router
from shared.core.config import settings
from shared.core.database import close_db, engine
from shared.core.exception_handlers import register_exception_handlers
from shared.core.logger import get_logger, setup_logging
from shared.core.middlewares import register_middlewares
from shared.core.schemas import APIResponse
from space.presentation.routers.v1.router import router as space_router
from user.presentation.routers.v1.router import router as user_router
from wiring import wire_dependencies

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
wire_dependencies(app)

for router in (user_router, auth_router, space_router, note_router, emoji_router):
    app.include_router(router)

# 커스텀 이모지 이미지 서빙 (/media/emojis/xxx.png)
Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")


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
