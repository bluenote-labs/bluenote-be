from datetime import datetime
from app.models.user import User
from app.schemas.user import UserDetailResponse, UserUpdateRequest


async def get_user_info(user: User) -> UserDetailResponse:
    return UserDetailResponse(
        id=str(user.id),
        nickname=user.nickname,
        profileImage=user.profile_image,
        createdAt=user.created_at,
    )


async def update_user_info(user: User, payload: UserUpdateRequest) -> UserDetailResponse:
    if payload.nickname is not None:
        user.nickname = payload.nickname
    if payload.profileImage is not None:
        user.profile_image = payload.profileImage
    if payload.backgroundImage is not None:
        user.background_image = payload.backgroundImage
    user.updated_at = datetime.now()
    await user.save()

    return UserDetailResponse(
        id=str(user.id),
        nickname=user.nickname,
        profileImage=user.profile_image,
        createdAt=user.created_at,
    )
