from datetime import datetime
from app.schemas.auth import UserInfo


class UserDetailResponse(UserInfo):
    createdAt: datetime
