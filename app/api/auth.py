from fastapi import APIRouter, Response
from app.schemas.auth import KakaoLoginRequest, Token
from app.services.auth import kakao_login

router = APIRouter()

@router.post("/kakao", response_model=Token)
async def kakao_login_route(request: KakaoLoginRequest, response: Response):
    return await kakao_login(request.code, response)
