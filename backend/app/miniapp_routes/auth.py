"""小程序认证路由 — JSON格式登录/注册/登出，与Web端共享 users 表"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_sync_db
from app.models.user import User
from app.utils.security import verify_password, hash_password, create_access_token
from app.miniapp_routes.deps import get_current_user
from app.miniapp_routes.schemas import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["小程序-认证"])


@router.post("/login", response_model=TokenResponse)
def miniapp_login(request: LoginRequest, db: Session = Depends(get_sync_db)):
    """小程序登录 - 邮箱+密码，返回JWT令牌"""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="邮箱未注册")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用，请联系管理员")
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="密码错误")

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.post("/register", response_model=TokenResponse)
def miniapp_register(request: RegisterRequest, db: Session = Depends(get_sync_db)):
    """小程序注册 - 邮箱+用户名+密码，注册成功自动登录返回JWT"""
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=400, detail="该邮箱已注册")
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(status_code=400, detail="该用户名已被使用")

    user = User(
        email=request.email,
        username=request.username,
        hashed_password=hash_password(request.password),
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.post("/logout")
def miniapp_logout(current_user: User = Depends(get_current_user)):
    """登出（JWT无状态，此处用于确认登出；客户端需清除本地token）"""
    return JSONResponse(
        content={"detail": "已退出登录", "user_id": current_user.id},
        status_code=200,
    )
