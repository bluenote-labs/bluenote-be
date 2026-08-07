from datetime import datetime
from typing import List, Optional

from beanie import Document, PydanticObjectId
from pydantic import Field


class Record(Document):
    user_id: PydanticObjectId
    date: str
    title: str
    content: dict
    image_url: Optional[str] = None
    goal_ids: List[PydanticObjectId] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "records"
