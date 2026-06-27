from fastapi_users import schemas

class UserRead(schemas.BaseUser[int]):
    username: str
    role: str | None = "user"

class UserCreate(schemas.BaseUserCreate):
    username: str
    role: str | None = "user"

class UserUpdate(schemas.BaseUserUpdate):
    username: str | None = None
    role: str | None = None