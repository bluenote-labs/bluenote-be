import logging
from beanie import PydanticObjectId
from fastapi import Request, Response, HTTPException, status
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.models.user import User
from app.schemas.auth import Token, TokenRefreshResponse, UserInfo
from app.schemas.base import MessageResponse
from app.services.kakao import get_kakao_token, get_kakao_user
from app.core.config import settings


logger = logging.getLogger(__name__)

async def kakao_login(code: str, response: Response) -> dict:
    kakao_access_token = await get_kakao_token(code)
    kakao_user = await get_kakao_user(kakao_access_token)

    kakao_id = str(kakao_user["id"])
    kakao_account = kakao_user.get("kakao_account", {})
    profile = kakao_account.get("profile", {})
    nickname = profile.get("nickname", "")

    existing_user = await User.find_one(User.provider_id == kakao_id)
    is_returning_user = existing_user is not None

    # 신규 유저는 user_id를 먼저 확정한 뒤 토큰을 발급해야
    # access_token의 sub 값이 실제 저장된 user_id와 일치함
    if not existing_user:
        new_user = User(provider_id=kakao_id, nickname=nickname, provider="kakao")
        await new_user.insert()
        user_id = new_user.id
        target_user = new_user
        logger.info(f"신규 유저 가입: kakao_id={kakao_id}")
    else:
        user_id = existing_user.id
        target_user = existing_user

    user_id = str(target_user.id)

    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id })

    await target_user.set({User.refresh_token: refresh_token})

    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        secure=not settings.IS_LOCAL,
        samesite="lax" if settings.IS_LOCAL else "none",
        max_age=7 * 24 * 60 * 60,  # 7일
        path="/"
    )

    return Token(
        accessToken=access_token,
        user=UserInfo(
            id=user_id,
            nickname=nickname,
            profileImage=target_user.profile_image
        ),
        isNewUser=not is_returning_user,
    )


async def logout(response: Response, request: Request) -> MessageResponse:
    refresh_token = request.cookies.get("refreshToken")

    if refresh_token:
        await User.find_one(User.refresh_token == refresh_token).update(
            {"$set": {User.refresh_token: None}}
        )

    response.delete_cookie(
        key="refreshToken",
        httponly=True,
        secure=not settings.IS_LOCAL,
        samesite="lax" if settings.IS_LOCAL else "none",
        path="/"
    )
    return MessageResponse(message="로그아웃 되었어요.")


async def refresh_token(request: Request, response: Response) -> TokenRefreshResponse:
    refresh_token = request.cookies.get("refreshToken")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰이에요."
        )

    try:
        payload = verify_token(refresh_token)
        user_id = payload.get("sub")

    except Exception as e:
        logger.error(f"refreshToken 검증 실패: {e}") 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰이에요."
        )

    user = await User.get(PydanticObjectId(user_id))
    
    if not user or user.refresh_token != refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰이에요."
        )

    new_access_token = create_access_token({"sub": user_id})
    new_refresh_token = create_refresh_token({"sub": user_id})

    await user.update({"$set": {"refresh_token": new_refresh_token}})

    response.set_cookie(
        key="refreshToken",
        value=new_refresh_token,
        httponly=True,
        secure=not settings.IS_LOCAL,
        samesite="lax" if settings.IS_LOCAL else "none",
        path="/"
    )

    return TokenRefreshResponse(accessToken=new_access_token)