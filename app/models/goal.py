from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field


class Goal(Document):
    user_id: PydanticObjectId
    title: str
    start_date: str
    end_date: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "goals"
