from datetime import datetime
from typing import List, Optional

from beanie import Document, PydanticObjectId
from pydantic import Field


class Pattern(Document):
    user_id: PydanticObjectId
    description: str
    evidence_record_ids: List[PydanticObjectId] = []
    status: str = "unconfirmed"  # unconfirmed | confirmed | modified | deferred
    user_modified_description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "patterns"
