"""用户模型 — 与Web后端共享 users 表（fastapi-users 生成的表结构）"""

from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """
    映射到 Web后端 fastapi-users 创建的 users 表。
    字段与 backend/app/models/user.py 完全一致，确保两个后端共享同一张表。
    """
    __tablename__ = "users"

    # === fastapi-users SQLAlchemyBaseUserTable[int] 提供的字段 ===
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # === 自定义字段（Web后端 User 模型中也定义了这些） ===
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)

    # === 扩展字段（仅 Uniapp 使用，已通过迁移脚本加入表中） ===
    avatar: Mapped[str | None] = mapped_column(String(512), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
