"""检测记录模型 — 小程序端使用（与 Web端 detections 表分开存储）"""

from datetime import datetime, timezone

from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DetectionRecord(Base):
    __tablename__ = "detection_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    pest_name: Mapped[str] = mapped_column(String(100), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    image_path: Mapped[str] = mapped_column(String(512), default="")
    result_image_path: Mapped[str] = mapped_column(String(512), default="")
    result_json: Mapped[str] = mapped_column(Text, default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    # 视频检测汇总（避免每次列表查询都解析巨大的result_json）
    video_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    processed_frames: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pest_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pest_types_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
