"""认证相关API路由 - 与Web端同步：邮箱+用户名注册，邮箱+密码登录"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录 - 邮箱+密码，返回JWT令牌"""
    service = AuthService(db)
    try:
        user = service.login(request.email, request.password)
        token = service.generate_token(user)
        return TokenResponse(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册 - 邮箱+用户名+密码，注册成功自动登录返回JWT令牌"""
    service = AuthService(db)
    try:
        user = service.register(request.email, request.username, request.password)
        token = service.generate_token(user)
        return TokenResponse(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
