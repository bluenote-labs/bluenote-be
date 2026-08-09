from datetime import datetime
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


class TryResultSummary(BaseModel):
    total_records: int
    action_taken_count: int
    notable_quote: str
    quote_count: int


class Try(Document):
    user_id: PydanticObjectId
    pattern_id: PydanticObjectId
    action: str
    start_date: str
    end_date: str
    result_summary: Optional[TryResultSummary] = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "tries"
