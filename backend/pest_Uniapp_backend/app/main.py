"""FastAPI应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.api.v1 import auth, users, detect, history


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print(f"[INFO] {settings.APP_NAME} 启动完成")
    yield
    print("[INFO] 应用关闭")


app = FastAPI(
    title=settings.APP_NAME,
    description="农作物害虫智能检测系统 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(detect.router, prefix="/api")
app.include_router(history.router, prefix="/api")

import os
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
