# ---- build: 의존성만 먼저 설치 (코드 바뀌어도 이 레이어는 캐시) ----
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ---- runtime: 가볍게, root 아닌 사용자로 실행 ----
FROM python:3.13-slim
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY alembic.ini ./
COPY migrations ./migrations
COPY scripts ./scripts
COPY src ./src
RUN mkdir -p /app/media && chown -R app:app /app/media
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 시작할 때 마이그레이션 적용 후 서버 실행
# --proxy-headers: Nginx/ALB 뒤에서 실제 클라이언트 IP 사용 (광장 비회원 하루 1개 제한에 필요)
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --app-dir src --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
