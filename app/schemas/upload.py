from pydantic import BaseModel


class UploadResponse(BaseModel):
    imageUrl: str
