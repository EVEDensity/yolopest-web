"""数据库连接 — 与Web后端共享同一个 PostgreSQL 数据库"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

from app.config import settings


# 同步引擎（因为 psycopg2 是同步驱动）
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")
engine = create_engine(SYNC_DATABASE_URL, echo=settings.DEBUG, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Session:
    """获取数据库会话（同步）"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """创建尚未存在的表（users 表已由 Web 后端创建，此处只创建 detection_records 等）"""
    from app.models.user import User          # noqa: F401  确保模型被导入
    from app.models.detection import DetectionRecord  # noqa: F401

    # create_all 使用 IF NOT EXISTS，已有表（users）不会被修改
    Base.metadata.create_all(bind=engine)
