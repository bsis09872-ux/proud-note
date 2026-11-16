from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수(.env) -> 타입이 검증된 설정 객체.
    필수값이 없거나 형식이 틀리면 서버가 아예 뜨지 않는다(fail fast).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 앱
    app_name: str = "Proud Note API"
    app_env: Literal["local", "dev", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # DB
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20
    sql_echo: bool = False

    # JWT (HS512는 64바이트 이상 키 권장 -> 짧으면 기동 실패)
    jwt_secret_key: str = Field(min_length=64)
    jwt_algorithm: str = "HS512"
    access_token_expire_minutes: int = 60

    # CORS (JSON 배열 형식: ["http://localhost:3000"])
    cors_origins: list[str] = ["http://localhost:3000"]

    # 업로드 파일 저장 위치 (커스텀 이모지)
    media_dir: str = "media"

    @property
    def is_local(self) -> bool:
        return self.app_env == "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
