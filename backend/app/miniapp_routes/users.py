"""小程序用户路由 — 个人信息、头像上传、统计数据、修改密码"""

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_sync_db
from app.models.user import User
from app.models.detection_record import DetectionRecord
from app.miniapp_routes.deps import get_current_user
from app.miniapp_routes.schemas import UserInfo, UserUpdateRequest, UserStats, ChangePasswordRequest
from app.utils.security import verify_password, hash_password

router = APIRouter(prefix="/users", tags=["小程序-用户"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static")
API_BASE_URL = "http://localhost:8000"


@router.get("/profile", response_model=UserInfo)
def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@router.put("/profile", response_model=UserInfo)
def update_profile(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """更新用户信息"""
    if request.username is not None:
        existing = db.query(User).filter(
            User.username == request.username,
            User.id != current_user.id,
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
    db: Session = Depends(get_sync_db),
):
    """获取用户检测统计信息"""
    user_id = current_user.id

    total = db.query(func.count(DetectionRecord.id)).filter(
        DetectionRecord.user_id == user_id
    ).scalar() or 0
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
    db: Session = Depends(get_sync_db),
):
    """上传用户头像"""
    avatar_dir = os.path.join(UPLOAD_DIR, "avatars")
    os.makedirs(avatar_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "avatar")[1] or ".jpg"
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(avatar_dir, filename)

    content = file.file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    avatar_url = f"{API_BASE_URL}/api/static/avatars/{filename}"

    current_user.avatar = avatar_url
    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)

    return {"url": avatar_url, "filename": filename}


@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """修改当前用户密码"""
    # 验证旧密码
    if not verify_password(request.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="旧密码错误")

    # 检查新旧密码不能相同
    if request.old_password == request.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")

    # 更新密码
    current_user.hashed_password = hash_password(request.new_password)
    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()

    return JSONResponse(content={"detail": "密码修改成功"}, status_code=200)
