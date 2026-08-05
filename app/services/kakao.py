import httpx
from app.core.config import settings
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_URL = "https://kapi.kakao.com/v2/user/me"


async def get_kakao_token(code: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            KAKAO_TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "authorization_code",
                "client_id": settings.KAKAO_REST_API_KEY,
                "client_secret": settings.KAKAO_CLIENT_SECRET,
                "redirect_uri": settings.REDIRECT_URI,
                "code": code
            }
        )
        if response.status_code != 200:
            logger.error(f"카카오 토큰 발급 실패: status={response.status_code}, body={response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="카카오 인가 코드가 유효하지 않아요."
            )
        return response.json()["access_token"]
    

async def get_kakao_user(kakao_access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            KAKAO_USER_URL,
            headers={"Authorization": f"Bearer {kakao_access_token}"}
        )
        if response.status_code != 200:
            logger.error(f"카카오 사용자 정보 조회 실패 : status={response}, body={response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="카카오 서버에서 사용자 정보를 가져오지 못했어요."
            )
        return response.json()