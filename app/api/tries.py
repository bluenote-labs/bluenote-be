from fastapi import APIRouter, Depends, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.base import SuccessResponse
from app.schemas.tries import TryCreateRequest, TryCreateResponse, TryListResponse
from app.services.tries import create_try, delete_try, get_tries

router = APIRouter()


@router.post("/tries", response_model=TryCreateResponse, status_code=status.HTTP_201_CREATED, summary="실험(시도) 생성")
async def create_try_route(
    payload: TryCreateRequest,
    user: User = Depends(get_current_user)
):
    return await create_try(user, payload)


@router.get("/tries", response_model=TryListResponse, summary="실험(시도) 목록 조회")
async def get_tries_route(
    user: User = Depends(get_current_user)
):
    return await get_tries(user)


@router.delete("/tries/{try_id}", response_model=SuccessResponse, summary="실험(시도) 삭제")
async def delete_try_route(
    try_id: str,
    user: User = Depends(get_current_user)
):
    return await delete_try(user, try_id)
