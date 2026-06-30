"""认证业务逻辑 - 与Web端同步：邮箱+用户名注册，邮箱+密码登录"""

from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.security import hash_password, verify_password, create_access_token


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, email: str, username: str, password: str) -> User:
        """注册新用户 - 邮箱+用户名+密码"""
        # 检查邮箱是否已注册
        existing_email = self.db.query(User).filter(User.email == email).first()
        if existing_email:
            raise ValueError("该邮箱已注册")

        # 检查用户名是否已被使用
        existing_username = self.db.query(User).filter(User.username == username).first()
        if existing_username:
            raise ValueError("该用户名已被使用")

        user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, email: str, password: str) -> User:
        """用户登录 - 邮箱+密码"""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("邮箱未注册")
        if not verify_password(password, user.hashed_password):
            raise ValueError("密码错误")
        if not user.is_active:
            raise ValueError("账号已被禁用")
        return user

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def generate_token(user: User) -> str:
        return create_access_token(data={"sub": str(user.id)})
