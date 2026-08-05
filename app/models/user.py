from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime

class User(Document):
    provider: str
    provider_id: str
    nickname: str
    profile_image: Optional[str] = None
    background_image: Optional[str] = None
    refresh_token: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "users"