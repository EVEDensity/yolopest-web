"""小程序专用 Pydantic 模型"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── 认证 ──
class LoginRequest(BaseModel):
    email: str = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=8, max_length=128, description="密码")


class RegisterRequest(BaseModel):
    email: str = Field(..., description="邮箱地址")
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=8, max_length=128, description="密码")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=8, max_length=128, description="旧密码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")


# ── 用户 ──
class UserInfo(BaseModel):
    id: int
    email: str
    username: str
    avatar: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    username: Optional[str] = Field(None, max_length=50)
    avatar: Optional[str] = Field(None, max_length=512)


class UserStats(BaseModel):
    total: int = 0
    pests: int = 0
    images: int = 0
    videos: int = 0


# ── 检测 ──
class DetectionResult(BaseModel):
    name: str
    name_en: str = ""
    class_id: int = 0
    aliases: list[str] = Field(default_factory=list)
    confidence: float
    bbox: list[float] = Field(default_factory=list)


class DetectResponse(BaseModel):
    success: bool = True
    detections: list[DetectionResult] = Field(default_factory=list)
    total_count: int = 0
    time: str = ""
    result_image_url: str = ""
    record_id: int = 0


# ── 视频检测 ──
class VideoUploadResponse(BaseModel):
    success: bool = True
    task_id: str
    message: str = "视频已提交处理"


class VideoStatusResponse(BaseModel):
    task_id: str
    status: str  # pending / processing / completed / failed
    progress: int = 0
    error: Optional[str] = None


class VideoFrameDetection(BaseModel):
    frame_index: int
    timestamp_ms: int
    detections: list[DetectionResult] = Field(default_factory=list)
    annotated_frame: Optional[str] = None


class VideoResultResponse(BaseModel):
    status: str
    record_id: int = 0
    total_frames: int = 0
    processed_frames: int = 0
    pest_count: int = 0
    pest_types: list[dict] = Field(default_factory=list)
    frames: list[VideoFrameDetection] = Field(default_factory=list)
    video_length: float = 0
    fps: float = 0
    time_cost: float = 0


# ── 历史记录 ──
class HistoryItem(BaseModel):
    id: int
    type: str
    pest_name: str
    confidence: float
    time: str
    thumbnail: str
    is_favorite: bool = False
    created_at: datetime
    # 视频检测汇总字段（图片类型为 None）
    file_size: int = 0
    video_duration: float | None = None
    processed_frames: int | None = None
    pest_count: int | None = None
    pest_types_count: int | None = None

    class Config:
        from_attributes = True


class HistoryListResponse(BaseModel):
    items: list[HistoryItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    has_more: bool = False


class DetailResponse(BaseModel):
    id: int
    type: str
    pest_name: str
    confidence: float
    time: str
    image_path: str
    result_image_path: str
    result_json: str
    file_size: int
    is_favorite: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class FavoriteToggleResponse(BaseModel):
    id: int
    is_favorite: bool
