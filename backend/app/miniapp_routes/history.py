"""小程序历史记录路由 — 查询、收藏、详情、删除"""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.database import get_sync_db
from app.models.user import User
from app.models.detection_record import DetectionRecord
from app.miniapp_routes.deps import get_current_user
from app.miniapp_routes.schemas import (
    HistoryItem,
    HistoryListResponse,
    DetailResponse,
    FavoriteToggleResponse,
)

router = APIRouter(prefix="/history", tags=["小程序-历史记录"])


def _get_time_filter_start(time_filter: str) -> datetime | None:
    now = datetime.now(timezone.utc)
    if time_filter == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_filter == "week":
        return now - timedelta(days=7)
    elif time_filter == "month":
        return now - timedelta(days=30)
    return None


@router.get("", response_model=HistoryListResponse)
def get_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: str = Query(default=""),
    time_filter: str = Query(default="all"),
    favorites: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """获取用户检测历史记录，支持分页/搜索/时间/收藏筛选"""
    user_id = current_user.id

    query = db.query(DetectionRecord).filter(DetectionRecord.user_id == user_id)
    count_query = db.query(func.count(DetectionRecord.id)).filter(
        DetectionRecord.user_id == user_id
    )

    if favorites:
        query = query.filter(DetectionRecord.is_favorite == True)
        count_query = count_query.filter(DetectionRecord.is_favorite == True)

    start_time = _get_time_filter_start(time_filter)
    if start_time:
        query = query.filter(DetectionRecord.created_at >= start_time)
        count_query = count_query.filter(DetectionRecord.created_at >= start_time)

    if keyword:
        query = query.filter(DetectionRecord.pest_name.ilike(f"%{keyword}%"))
        count_query = count_query.filter(DetectionRecord.pest_name.ilike(f"%{keyword}%"))

    total = count_query.scalar() or 0
    offset = (page - 1) * page_size
    records = (
        query.order_by(desc(DetectionRecord.created_at))
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = []
    for r in records:
        items.append(
            HistoryItem(
                id=r.id,
                type=r.type,
                pest_name=r.pest_name or "未知",
                confidence=round(r.confidence, 1),
                time=r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                thumbnail=r.result_image_path or r.image_path or "",
                is_favorite=r.is_favorite or False,
                created_at=r.created_at,
                file_size=r.file_size or 0,
                video_duration=getattr(r, "video_duration", None),
                processed_frames=getattr(r, "processed_frames", None),
                pest_count=getattr(r, "pest_count", None),
                pest_types_count=getattr(r, "pest_types_count", None),
            )
        )

    return HistoryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total,
    )


@router.get("/{record_id}", response_model=DetailResponse)
def get_detail(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """获取单条检测记录的详细结果"""
    record = (
        db.query(DetectionRecord)
        .filter(
            DetectionRecord.id == record_id,
            DetectionRecord.user_id == current_user.id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    return DetailResponse(
        id=record.id,
        type=record.type,
        pest_name=record.pest_name or "未知",
        confidence=round(record.confidence, 1),
        time=record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        image_path=record.image_path or "",
        result_image_path=record.result_image_path or "",
        result_json=record.result_json or "[]",
        file_size=record.file_size or 0,
        is_favorite=record.is_favorite or False,
        created_at=record.created_at,
    )


@router.post("/{record_id}/favorite", response_model=FavoriteToggleResponse)
def toggle_favorite(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """切换收藏状态"""
    record = (
        db.query(DetectionRecord)
        .filter(
            DetectionRecord.id == record_id,
            DetectionRecord.user_id == current_user.id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    record.is_favorite = not record.is_favorite
    db.commit()

    return FavoriteToggleResponse(id=record.id, is_favorite=record.is_favorite)


@router.delete("/{record_id}")
def delete_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """删除单条检测记录"""
    record = (
        db.query(DetectionRecord)
        .filter(
            DetectionRecord.id == record_id,
            DetectionRecord.user_id == current_user.id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    # 删除关联的本地文件
    import os
    for path_attr in ["image_path", "result_image_path"]:
        file_url = getattr(record, path_attr, "")
        if not file_url:
            continue
        # 兼容旧格式（相对路径 /api/static/...）和新格式（完整URL http://.../api/static/...）
        if "/api/static/" in file_url:
            rel_path = file_url.split("/api/static/", 1)[1]
            # 静态文件在 backend/app/static/ 下（与 main.py StaticFiles 挂载一致）
            abs_path = os.path.join(
                os.path.dirname(__file__), "..", "static", rel_path
            )
            try:
                if os.path.exists(abs_path):
                    os.unlink(abs_path)
            except Exception:
                pass

    db.delete(record)
    db.commit()

    return JSONResponse(content={"detail": "已删除"}, status_code=200)


@router.delete("")
def clear_all_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """清空当前用户所有检测记录"""
    deleted = (
        db.query(DetectionRecord)
        .filter(DetectionRecord.user_id == current_user.id)
        .delete()
    )
    db.commit()

    return JSONResponse(
        content={"detail": f"已清空 {deleted} 条记录"}, status_code=200
    )
