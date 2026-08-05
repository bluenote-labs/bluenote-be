from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import UserDetailResponse, UserUpdateRequest
from app.services.user import get_user_info, update_user_info

router = APIRouter()


@router.get("/me", response_model=UserDetailResponse, summary="내 정보 조회")
async def get_my_info(user: User = Depends(get_current_user)):
    return await get_user_info(user)


@router.put("/me", response_model=UserDetailResponse, summary="내 정보 수정")
async def update_my_info(payload: UserUpdateRequest, user: User = Depends(get_current_user)):
    return await update_user_info(user, payload)
