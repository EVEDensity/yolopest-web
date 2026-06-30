from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import load_only
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.core.users import current_active_user
from app.models.user import User
from app.models.history import History
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Statistics"])


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user),
    startTime: Optional[float] = Query(None, description="起始时间（毫秒时间戳）"),
    endTime: Optional[float] = Query(None, description="结束时间（毫秒时间戳）"),
):
    try:
        query = (
            select(History)
            .where(
                History.user_id == current_user.id,
                History.type == "image",
            )
            .options(load_only(History.result, History.timestamp))
        )

        if startTime is not None:
            start_dt = datetime.fromtimestamp(startTime / 1000)
            query = query.where(History.timestamp >= start_dt)
        if endTime is not None:
            end_dt = datetime.fromtimestamp(endTime / 1000)
            query = query.where(History.timestamp <= end_dt)

        result = await db.execute(query)
        records = result.scalars().all()

        pest_map: dict[str, int] = {}
        confidence_list: list[float] = []
        trend_map: dict[str, int] = {}

        for record in records:
            if not record.result or "predictions" not in record.result:
                continue
            predictions = record.result["predictions"]
            if not predictions:
                continue

            for pred in predictions:
                pest_name = pred.get("class", pred.get("pest", "未知"))
                confidence = pred.get("confidence", 0)
                pest_map[pest_name] = pest_map.get(pest_name, 0) + 1
                confidence_list.append(confidence)

            day_str = record.timestamp.strftime("%Y-%m-%d") if record.timestamp else ""
            if day_str:
                trend_map[day_str] = trend_map.get(day_str, 0) + len(predictions)

        pest_distribution = [
            {"name": name, "value": count}
            for name, count in sorted(pest_map.items(), key=lambda x: -x[1])
        ]

        trend_data = [
            {"date": date, "count": count}
            for date, count in sorted(trend_map.items())
        ]

        total = len(confidence_list)
        avg_conf = (sum(confidence_list) / total) if total > 0 else 0

        return {
            "pestDistribution": pest_distribution,
            "confidenceData": confidence_list,
            "trendData": trend_data,
            "totalDetections": total,
            "uniquePestTypes": len(pest_map),
            "averageConfidence": round(avg_conf, 4),
        }

    except Exception as e:
        logger.error(f"获取统计数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")
