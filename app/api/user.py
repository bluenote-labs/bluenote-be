from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import UserDetailResponse
from app.services.user import get_user_info

router = APIRouter()


@router.get("/me", response_model=UserDetailResponse)
async def get_my_info(user: User = Depends(get_current_user)):
    return await get_user_info(user)
