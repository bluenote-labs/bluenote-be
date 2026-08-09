from fastapi import APIRouter, Depends, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.base import SuccessResponse
from app.schemas.goals import (
    GoalCreateRequest,
    GoalCreateResponse,
    GoalListResponse,
    GoalParseRequest,
    GoalParseResponse,
    GoalUpdateRequest,
    GoalUpdateResponse,
)
from app.services.goals import create_goal, delete_goal, list_goals, parse_goal, update_goal

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


@router.get("", response_model=GoalListResponse, summary="목표 목록 조회")
async def list_goals_route(
    user: User = Depends(get_current_user)
):
    return await list_goals(user)


@router.put("/{goal_id}", response_model=GoalUpdateResponse, summary="목표 수정")
async def update_goal_route(
    goal_id: str,
    payload: GoalUpdateRequest,
    user: User = Depends(get_current_user)
):
    return await update_goal(user, goal_id, payload)


@router.delete("/{goal_id}", response_model=SuccessResponse, summary="목표 삭제")
async def delete_goal_route(
    goal_id: str,
    user: User = Depends(get_current_user)
):
    return await delete_goal(user, goal_id)
