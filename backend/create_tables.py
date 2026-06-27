import asyncio
import logging
from sqlalchemy import text

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 正确导入模型
from app.models.base import Base
from app.models.user import User  # 显式导入User模型
from app.models.history import History  # 显式导入History模型
from app.models.detection import Detection  # 显式导入Detection模型
from app.core.database import engine, DATABASE_URL


async def create_tables():
    """按当前配置创建所有数据库表。"""
    logger.info(f"正在连接到数据库: {DATABASE_URL}")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

            logger.info("所有数据库表已成功创建！")

            result = await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
                )
            )
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"数据库中的表: {tables}")

    except Exception as e:
        logger.error(f"创建表时出错: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(create_tables())
