from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.goals import GoalParseRequest, GoalParseResponse
from app.services.goals import parse_goal

router = APIRouter()


@router.post("/parse", response_model=GoalParseResponse, summary="AI 목표 생성")
async def parse_goal_route(
    payload: GoalParseRequest,
    _: User = Depends(get_current_user)
):
    return await parse_goal(payload)
