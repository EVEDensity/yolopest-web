from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import get_settings
from app.api.router import router  # 使用新的路由聚合
from app.routers import history  # 保留原有路由
from app.api import video  # 添加这一行导入视频模块
from app.api import statistics  # 导入统计路由

# 小程序专用路由
from app.miniapp_routes.auth import router as miniapp_auth_router
from app.miniapp_routes.users import router as miniapp_users_router
from app.miniapp_routes.detect import router as miniapp_detect_router
from app.miniapp_routes.history import router as miniapp_history_router

import uvicorn
import logging
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ultralytics'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

settings = get_settings()
app = FastAPI(debug=settings.debug)

# 解决跨域问题
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许小程序及其他所有来源
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
    expose_headers=["Content-Disposition"],
)

# 确保静态文件目录存在
os.makedirs(os.path.join("app", "static"), exist_ok=True)
os.makedirs(os.path.join("app", "static", "videos"), exist_ok=True)
os.makedirs(os.path.join("app", "static", "images"), exist_ok=True)
os.makedirs(os.path.join("app", "static", "results"), exist_ok=True)
os.makedirs(os.path.join("app", "static", "avatars"), exist_ok=True)

# 挂载静态文件服务
app.mount("/api/static", StaticFiles(directory=os.path.join("app", "static")), name="static")

# ── Web 端路由 ──
app.include_router(router, prefix="/api")
app.include_router(history.router, prefix="/api")  # 保留原有路由

# 添加视频处理路由
app.include_router(video.router, prefix="/api/video", tags=["video"])

# 添加统计路由
app.include_router(statistics.router, prefix="/api", tags=["Statistics"])

# ── 小程序专用路由（与 Web 端共享 users 表，使用 /api/miniapp 避免冲突） ──
app.include_router(miniapp_auth_router, prefix="/api/miniapp")
app.include_router(miniapp_users_router, prefix="/api/miniapp")
app.include_router(miniapp_detect_router, prefix="/api/miniapp")
app.include_router(miniapp_history_router, prefix="/api/miniapp")

@app.get("/")
async def health_check():
    return {"status": "backend is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)