from datetime import datetime

from pydantic import BaseModel


class GoalParseRequest(BaseModel):
    input: str


class GoalParseResponse(BaseModel):
    title: str
    startDate: str
    endDate: str
    aiMessage: str


class GoalCreateRequest(BaseModel):
    title: str
    startDate: str
    endDate: str


class GoalCreateResponse(BaseModel):
    id: str
    title: str
    startDate: str
    endDate: str
    createdAt: datetime


class GoalListItem(BaseModel):
    id: str
    title: str
    startDate: str
    endDate: str
    isActive: bool
    createdAt: datetime


class GoalListResponse(BaseModel):
    goals: list[GoalListItem]
