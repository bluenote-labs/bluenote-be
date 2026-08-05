from fastapi import APIRouter, Depends, File, UploadFile

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.upload import UploadResponse
from app.services.upload import upload_image

router = APIRouter()


@router.post("", response_model=UploadResponse)
async def upload_image_route(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user)
):
    image_url = await upload_image(file)
    return UploadResponse(imageUrl=image_url)
