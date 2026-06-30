"""小程序检测路由 — 图片/视频上传 + YOLO推理"""

import json
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_sync_db
from app.models.user import User
from app.models.detection_record import DetectionRecord
from app.services.yolo_service import yolo_service, video_task_manager
from app.miniapp_routes.deps import get_current_user
from app.miniapp_routes.schemas import (
    DetectResponse,
    VideoUploadResponse,
    VideoStatusResponse,
    VideoResultResponse,
)

router = APIRouter(prefix="/detect", tags=["小程序-检测"])

# 上传目录
# 静态文件目录：与 main.py 中 StaticFiles 挂载路径一致（backend/app/static/）
_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
# 小程序端需要完整URL（浏览器可自动拼接相对路径，但小程序<image>不行）
# 通过环境变量 API_BASE_URL 配置：
#   - 默认本地开发: http://localhost:8000 （小程序可直接加载图片）
#   - Docker部署: 设为空字符串 → 生成相对路径 /api/static/... （nginx反代）
#   - 生产环境: 设为 https://your-domain.com
_base = os.getenv("API_BASE_URL", "http://localhost:8000").strip().rstrip("/")
if _base:
    _API_STATIC = _base + "/api/static"
else:
    _API_STATIC = "/api/static"  # 相对路径，浏览器自动拼接当前域名


def _ensure_dir(sub_dir: str = "") -> str:
    path = os.path.join(_BASE_DIR, sub_dir)
    os.makedirs(path, exist_ok=True)
    return path


def _save_file(file: UploadFile, sub_dir: str = "") -> tuple[str, str]:
    """保存上传文件，返回 (本地绝对路径, URL相对路径)"""
    ext = os.path.splitext(file.filename or "file")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    save_dir = _ensure_dir(sub_dir)
    save_path = os.path.join(save_dir, filename)
    content = file.file.read()
    with open(save_path, "wb") as f:
        f.write(content)
    url_path = f"{_API_STATIC}/{sub_dir}/{filename}"
    return save_path, url_path


@router.post("/image", response_model=DetectResponse)
def detect_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """上传图片进行害虫检测"""
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图片文件")

    image_path, image_url = _save_file(file, sub_dir="images")
    file_size = os.path.getsize(image_path)

    # 一次模型调用同时获取检测结果 + 保存标注图
    detections, result_filename = yolo_service.predict_image(
        image_path, output_dir=_ensure_dir("results")
    )
    result_image_url = f"{_API_STATIC}/results/{result_filename}" if result_filename else ""

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    pest_name = detections[0]["name"] if detections else ""
    confidence = detections[0]["confidence"] if detections else 0.0

    record = DetectionRecord(
        user_id=current_user.id,
        type="image",
        pest_name=pest_name,
        confidence=confidence,
        image_path=image_url,           # 存URL，前端可直接加载
        result_image_path=result_image_url,
        result_json=json.dumps(detections),
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
        result_image_url=result_image_url,
        record_id=record.id,
    )


# ── 视频异步检测（与Web端 task模式对齐） ──

@router.post("/video", response_model=VideoUploadResponse)
def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """上传视频并提交异步检测任务"""
    allowed = ["video/mp4", "video/webm", "video/quicktime"]
    if file.content_type and file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="仅支持 MP4/WebM/MOV 格式")

    video_path, video_url = _save_file(file, sub_dir="videos")
    file_size = os.path.getsize(video_path)

    # 创建异步检测任务
    results_dir = _ensure_dir("results")
    task_id = video_task_manager.create_task(video_path, results_dir)

    # 预创建检测记录（状态为处理中）
    record = DetectionRecord(
        user_id=current_user.id,
        type="video",
        pest_name="检测中...",
        confidence=0.0,
        image_path=video_url,
        result_json=f'{{"task_id": "{task_id}"}}',
        file_size=file_size,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return VideoUploadResponse(
        success=True,
        task_id=task_id,
        message="视频已提交处理，请轮询状态获取结果",
    )


@router.get("/video/status/{task_id}", response_model=VideoStatusResponse)
def get_video_status(task_id: str):
    """查询视频处理任务状态"""
    status = video_task_manager.get_status(task_id)
    if status is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return VideoStatusResponse(**status)


@router.get("/video/result/{task_id}", response_model=VideoResultResponse)
def get_video_result(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """获取视频处理完整结果，完成后自动更新检测记录"""
    status = video_task_manager.get_status(task_id)
    if status is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    if status["status"] in ("pending", "processing"):
        raise HTTPException(status_code=202, detail=f"任务处理中 ({status['progress']}%)")

    if status["status"] == "failed":
        # 更新记录为失败
        _update_record_by_task_id(db, task_id, pest_name="检测失败", result_json=f'{{"error": "{status.get("error", "")}"}}')
        raise HTTPException(status_code=500, detail=status.get("error", "视频处理失败"))

    result = video_task_manager.get_result(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="结果不存在")

    # 更新检测记录
    pest_types = result.get("pest_types", [])
    pest_names = [pt["name"] for pt in pest_types]
    pest_name = "、".join(pest_names) if pest_names else "未检出"
    confidence = 0.0
    if result.get("frames"):
        all_confs = []
        for f in result["frames"]:
            for d in f.get("detections", []):
                all_confs.append(d.get("confidence", 0))
        confidence = round(sum(all_confs) / len(all_confs), 1) if all_confs else 0.0

    record_id = _update_record_by_task_id(
        db, task_id,
        pest_name=pest_name,
        confidence=confidence,
        result_json=json.dumps(result),
        video_duration=result.get("video_length", 0),
        processed_frames=result.get("processed_frames", 0),
        pest_count=result.get("pest_count", 0),
        pest_types_count=len(pest_types),
    )

    return VideoResultResponse(
        status="completed",
        record_id=record_id or 0,
        total_frames=result.get("total_frames", 0),
        processed_frames=result.get("processed_frames", 0),
        pest_count=result.get("pest_count", 0),
        pest_types=pest_types,
        frames=result.get("frames", []),
        video_length=result.get("video_length", 0),
        fps=result.get("fps", 0),
        time_cost=result.get("time_cost", 0),
    )


def _update_record_by_task_id(db: Session, task_id: str, **kwargs) -> int | None:
    """根据 task_id 更新检测记录（含视频汇总字段），返回记录ID"""
    # 注意：result_json 现已用 json.dumps 存储，task_id 搜索仍兼容新旧格式
    record = db.query(DetectionRecord).filter(
        DetectionRecord.result_json.like(f'%"{task_id}"%')
    ).first()
    if record:
        for k, v in kwargs.items():
            if hasattr(DetectionRecord, k):
                setattr(record, k, v)
        db.commit()
        return record.id
    return None
