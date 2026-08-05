from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.schemas.auth import UserInfo


class UserDetailResponse(UserInfo):
    createdAt: datetime


class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    profileImage: Optional[str] = None
    backgroundImage: Optional[str] = None
