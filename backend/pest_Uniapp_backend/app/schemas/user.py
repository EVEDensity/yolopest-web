"""用户相关的Pydantic模型 — 与Web后端共享 users 表"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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
