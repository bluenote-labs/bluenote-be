import logging
import uuid

from azure.storage.blob import ContentSettings
from azure.storage.blob.aio import BlobServiceClient
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


async def upload_image(file: UploadFile) -> str:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="지원하지 않는 파일 형식이에요. (jpg, png, webp만 가능)"
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일 크기가 5MB를 초과했어요."
        )

    extension = ALLOWED_CONTENT_TYPES[file.content_type]
    blob_name = f"{uuid.uuid4()}.{extension}"

    try:
        async with BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STR
        ) as blob_service_client:
            blob_client = blob_service_client.get_blob_client(
                container=settings.AZURE_STORAGE_CONTAINER_NAME,
                blob=blob_name,
            )
            await blob_client.upload_blob(
                content,
                content_settings=ContentSettings(content_type=file.content_type),
            )
            return blob_client.url
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Azure Blob Storage 업로드 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="파일 업로드에 실패했어요."
        )
