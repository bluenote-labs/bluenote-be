from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TryCreateRequest(BaseModel):
    patternId: str
    action: str
    startDate: str
    endDate: str


class TryCreateResponse(BaseModel):
    id: str
    patternId: str
    action: str
    startDate: str
    endDate: str
    createdAt: datetime


class TryResultSummaryOut(BaseModel):
    totalRecords: int
    actionTakenCount: int
    notableQuote: str
    quoteCount: int


class TryCurrentItem(BaseModel):
    id: str
    patternId: str
    action: str
    startDate: str
    endDate: str


class TryPastItem(BaseModel):
    id: str
    action: str
    startDate: str
    endDate: str
    resultSummary: Optional[TryResultSummaryOut] = None


class TryListResponse(BaseModel):
    current: Optional[TryCurrentItem] = None
    past: list[TryPastItem]
