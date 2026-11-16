import logging
from contextvars import ContextVar

from shared.core.config import settings

# 요청마다 다른 값을 가지는 "요청 ID" (미들웨어에서 세팅)
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class RequestIdFilter(logging.Filter):
    """모든 로그 레코드에 현재 요청 ID를 붙인다."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level)

    # 너무 시끄러운 라이브러리 로그는 한 단계 올린다
    for noisy in ("asyncio", "httpx", "httpx2"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
