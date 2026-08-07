from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class RecordGenerateRequest(BaseModel):
    input: str


class RecordCreateRequest(BaseModel):
    title: str
    content: dict
    imageUrl: Optional[str] = None
    goalIds: List[str] = []


class RecordCreateResponse(BaseModel):
    id: str
    date: str
    title: str
    createdAt: datetime
