"""迁移脚本：为已有的 users 表添加 avatar 和 updated_at 列（Uniapp 独占字段）"""

from app.config import settings
from app.database import engine
from sqlalchemy import text


def migrate():
    with engine.connect() as conn:
        # 检查列是否已存在，避免重复添加
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'avatar'
        """))
        if result.fetchone() is None:
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar VARCHAR(512)"))
            print("[OK] 已添加 avatar 列")
        else:
            print("[SKIP] avatar 列已存在")

        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'updated_at'
        """))
        if result.fetchone() is None:
            conn.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMPTZ"))
            print("[OK] 已添加 updated_at 列")
        else:
            print("[SKIP] updated_at 列已存在")

        conn.commit()
        print("[DONE] 迁移完成")


if __name__ == "__main__":
    migrate()
