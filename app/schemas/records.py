from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


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


class GoalSummary(BaseModel):
    id: str
    title: str


class RecordListItem(BaseModel):
    id: str
    date: str
    title: str
    imageUrl: Optional[str] = None
    goals: List[GoalSummary] = []
    createdAt: datetime


class RecordListResponse(BaseModel):
    records: List[RecordListItem]
    total: int
    page: int
    totalPages: int
    hasNext: bool


class RecordListQuery(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    month: Optional[str] = Field(None, description="월별 필터 (YYYY-MM, 달력뷰용)")
    goal_id: Optional[str] = Field(None, description="목표별 필터")
    keyword: Optional[str] = Field(None, description="제목/본문 검색")
    has_image: Optional[bool] = Field(None, description="사진 있는 기록만 (사진 모아보기용)")
