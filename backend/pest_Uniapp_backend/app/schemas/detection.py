"""检测相关的Pydantic模型"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DetectionResult(BaseModel):
    name: str
    confidence: float
    bbox: list[float] = Field(default_factory=list)


class DetectResponse(BaseModel):
    success: bool = True
    detections: list[DetectionResult] = Field(default_factory=list)
    total_count: int = 0
    time: str = ""
    result_image_url: str = ""
    record_id: int = 0


class HistoryItem(BaseModel):
    id: int
    type: str
    pest_name: str
    confidence: float
    time: str
    thumbnail: str
    is_favorite: bool = False
    created_at: datetime

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