from fastapi import APIRouter, Depends, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.goals import (
    GoalCreateRequest,
    GoalCreateResponse,
    GoalParseRequest,
    GoalParseResponse,
)
from app.services.goals import create_goal, parse_goal

router = APIRouter()


@router.post("/parse", response_model=GoalParseResponse, summary="AI 목표 생성")
async def parse_goal_route(
    payload: GoalParseRequest,
    _: User = Depends(get_current_user)
):
    return await parse_goal(payload)


@router.post("", response_model=GoalCreateResponse, status_code=status.HTTP_201_CREATED, summary="목표 저장")
async def create_goal_route(
    payload: GoalCreateRequest,
    user: User = Depends(get_current_user)
):
    return await create_goal(user, payload)
