"""检测相关API路由（图片+视频+YOLO推理）"""

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.detection import DetectionRecord
from app.models.user import User
from app.services.yolo_service import yolo_service
from app.schemas.detection import DetectResponse

router = APIRouter(prefix="/detect", tags=["检测"])


def _ensure_upload_dir(sub_dir: str = "") -> str:
    base = os.path.join(settings.UPLOAD_DIR, sub_dir)
    os.makedirs(base, exist_ok=True)
    return base


def _save_upload_file(file: UploadFile, sub_dir: str = "") -> str:
    ext = os.path.splitext(file.filename or "file")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    save_dir = _ensure_upload_dir(sub_dir)
    save_path = os.path.join(save_dir, filename)
    content = file.file.read()
    with open(save_path, "wb") as f:
        f.write(content)
    return save_path


@router.post("/image", response_model=DetectResponse)
def detect_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传图片进行害虫检测"""
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图片文件")

    image_path = _save_upload_file(file, sub_dir="images")
    file_size = os.path.getsize(image_path)

    detections = yolo_service.predict_image(image_path)
    result_image_path = yolo_service.save_result_image(image_path, _ensure_upload_dir("results"))

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    pest_name = detections[0]["name"] if detections else ""
    confidence = detections[0]["confidence"] if detections else 0.0

    record = DetectionRecord(
        user_id=current_user.id,
        type="image",
        pest_name=pest_name,
        confidence=confidence,
        image_path=image_path,
        result_image_path=result_image_path or "",
        result_json=str(detections),
        file_size=file_size,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return DetectResponse(
        success=True,
        detections=detections,
        total_count=len(detections),
        time=now_str,
        result_image_url=result_image_path or "",
        record_id=record.id,
    )


@router.post("/video")
def detect_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传视频进行害虫检测"""
    allowed_types = ["video/mp4", "video/webm", "video/quicktime"]
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="仅支持 MP4/WebM/MOV 格式")

    video_path = _save_upload_file(file, sub_dir="videos")
    file_size = os.path.getsize(video_path)

    result = yolo_service.predict_video(video_path)
    pest_types = result.get("pest_types", [])
    pest_names = [pt["name"] for pt in pest_types]
    pest_name = "、".join(pest_names) if pest_names else ""

    record = DetectionRecord(
        user_id=current_user.id,
        type="video",
        pest_name=pest_name,
        confidence=0.0,
        image_path=video_path,
        result_json=str(result),
        file_size=file_size,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "success": True,
        "total_frames": result["total_frames"],
        "pest_count": result["pest_count"],
        "pest_types": result["pest_types"],
        "record_id": record.id,
    }
