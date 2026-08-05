from typing import Optional
from pydantic import BaseModel


class KakaoLoginRequest(BaseModel):
    code: str


class UserInfo(BaseModel):
    id: str
    nickname: str
    profileImage: Optional[str] = None


class Token(BaseModel):
    accessToken: str
    user: UserInfo
    isNewUser: bool


class TokenRefreshResponse(BaseModel):
    accessToken: str