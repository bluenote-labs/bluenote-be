from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HeatmapDay(BaseModel):
    date: str
    recordId: str


class HeatmapResponse(BaseModel):
    period: str
    totalRecords: int
    mostFrequentDay: Optional[str] = None
    mostActiveMonth: Optional[str] = None
    days: list[HeatmapDay]


class PatternItem(BaseModel):
    id: str
    description: str
    evidenceRecordIds: list[str]
    status: str
    userModifiedDescription: Optional[str] = None


class PatternListResponse(BaseModel):
    patterns: list[PatternItem]


class PatternFeedbackRequest(BaseModel):
    action: str
    modifiedDescription: Optional[str] = None


class PatternFeedbackResponse(BaseModel):
    id: str
    status: str
    description: str
    suggestedTries: list[str]


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
