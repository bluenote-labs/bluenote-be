from fastapi import APIRouter, Response, Request, Depends
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import KakaoLoginRequest, Token, TokenRefreshResponse
from app.schemas.base import MessageResponse
from app.services.auth import kakao_login, logout, refresh_token

router = APIRouter()

@router.post("/kakao", response_model=Token)
async def kakao_login_route(request: KakaoLoginRequest, response: Response):
    return await kakao_login(request.code, response)


@router.post("/logout", response_model=MessageResponse)
async def logout_route(
    request: Request,
    response: Response,
    _: User = Depends(get_current_user)
):
    return await logout(response, request)


@router.post("/token/refresh", response_model=TokenRefreshResponse)
async def refresh_token_route(
    request: Request,
    response: Response
):
    return await refresh_token(request, response)