from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    # ── 基础配置 ──
    debug: bool = False
    model_path: str = "./model_weights/best.pt"
    img_size: int = 640
    conf_thresh: float = 0.5

    # ── 数据库组件（.env 设置了 DATABASE_URL 则优先使用）──
    POSTGRES_USER: str = "yolopest"
    POSTGRES_PASSWORD: str = "yolopest"
    POSTGRES_DB: str = "yolopest"
    DATABASE_URL: str = ""

    # ── Redis ──
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ──
    SECRET_KEY: str = "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION"
    algorithm: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @model_validator(mode="after")
    def build_database_url(self):
        """如果 .env 未设置完整 DATABASE_URL，则从组件自动拼接"""
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@localhost:5434/{self.POSTGRES_DB}"
            )
        return self

    # ── 向后兼容的小写别名 ──
    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def secret_key(self) -> str:
        return self.SECRET_KEY

    @property
    def access_token_expire_minutes(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def redis_url(self) -> str:
        return self.REDIS_URL


@lru_cache()
def get_settings():
    return Settings()
