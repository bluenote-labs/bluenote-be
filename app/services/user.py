from app.models.user import User
from app.schemas.user import UserDetailResponse


async def get_user_info(user: User) -> UserDetailResponse:
    return UserDetailResponse(
        id=str(user.id),
        nickname=user.nickname,
        profileImage=user.profile_image,
        createdAt=user.created_at,
    )
