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
