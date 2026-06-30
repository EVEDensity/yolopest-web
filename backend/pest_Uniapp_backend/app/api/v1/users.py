"""用户相关API路由 - 与Web端共享 users 表"""

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.detection import DetectionRecord
from app.models.user import User
from app.schemas.user import UserInfo, UserUpdateRequest, UserStats

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/profile", response_model=UserInfo)
def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@router.put("/profile", response_model=UserInfo)
def update_profile(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新用户信息"""
    if request.username is not None:
        # 检查用户名是否已被其他用户占用
        existing = db.query(User).filter(
            User.username == request.username,
            User.id != current_user.id  # 排除自己
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="该用户名已被使用")
        current_user.username = request.username

    if request.avatar is not None:
        current_user.avatar = request.avatar

    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/stats", response_model=UserStats)
def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户检测统计信息"""
    user_id = current_user.id

    total = db.query(func.count(DetectionRecord.id)).filter(DetectionRecord.user_id == user_id).scalar() or 0
    images = db.query(func.count(DetectionRecord.id)).filter(
        DetectionRecord.user_id == user_id, DetectionRecord.type == "image"
    ).scalar() or 0
    videos = db.query(func.count(DetectionRecord.id)).filter(
        DetectionRecord.user_id == user_id, DetectionRecord.type == "video"
    ).scalar() or 0
    pests = db.query(func.count(func.distinct(DetectionRecord.pest_name))).filter(
        DetectionRecord.user_id == user_id, DetectionRecord.pest_name != ""
    ).scalar() or 0

    return UserStats(total=total, pests=pests, images=images, videos=videos)


@router.post("/upload_avatar")
def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传用户头像"""
    avatar_dir = os.path.join(settings.UPLOAD_DIR, "avatars")
    os.makedirs(avatar_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "avatar")[1] or ".jpg"
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(avatar_dir, filename)

    content = file.file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # 构建 HTTP URL
    avatar_url = f"{settings.API_BASE_URL}/uploads/avatars/{filename}"

    # 更新用户头像
    current_user.avatar = avatar_url
    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)

    return {"url": avatar_url, "filename": filename}
