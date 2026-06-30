"""应用配置 - 从.env文件读取环境变量"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Yolo-Pest API"
    DEBUG: bool = False

    # 数据库配置 — 与Web后端共享同一个数据库
    DATABASE_URL: str = "postgresql+psycopg2://yolopest:yolopest@localhost:5432/yolopest"

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "your_secret_key_here_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    MODEL_PATH: str = "../model_weights/best.pt"
    IMG_SIZE: int = 640
    CONF_THRESH: float = 0.5

    DEEPSEEK_API_KEY: Optional[str] = None

    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024
    API_BASE_URL: str = "http://localhost:8001"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # 忽略 .env 中 Web 前端定义的 VITE_* / POSTGRES_* 变量
    }


settings = Settings()
