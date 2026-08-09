import logging
from datetime import datetime

from beanie import PydanticObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status

from app.models.goal import Goal
from app.models.user import User
from app.schemas.base import SuccessResponse
from app.utils.datetime import today_str
from app.schemas.goals import (
    GoalCreateRequest,
    GoalCreateResponse,
    GoalListItem,
    GoalListResponse,
    GoalParseRequest,
    GoalParseResponse,
    GoalUpdateRequest,
    GoalUpdateResponse,
)
from app.services.ai import AIGenerationError, generate_json

logger = logging.getLogger(__name__)

GOAL_PARSE_SYSTEM_PROMPT = (
    "너는 사용자의 목표 입력 문장을 분석해서 목표명과 기간을 추출하는 도우미야. "
    "오늘 날짜는 {today}야. '오늘', '내일', '2주간', '한 달' 같은 상대적인 표현은 오늘 날짜를 기준으로 계산해. "
    "title은 목표를 나타내는 간결한 명사구로 만들어. "
    "startDate와 endDate는 'YYYY-MM-DD' 형식으로만 응답해. "
    "aiMessage는 사용자에게 등록 여부를 묻는 짧은 질문형 한 문장으로 만들어. "
    "날짜는 '8월 4일'처럼 간결하게 표현하고 연도는 생략해. 시작일과 종료일의 월이 같으면 종료일의 월도 생략해서 '8월 4일부터 17일까지'처럼 써. "
    "예시: '8월 4일부터 17일까지 매일 정처기 공부로 등록할까요?' "
    "사용자가 입력한 언어를 그대로 유지해. "
    '반드시 다음 JSON 형식으로만 응답해: '
    '{{"title": string, "startDate": string, "endDate": string, "aiMessage": string}}'
)


async def parse_goal(payload: GoalParseRequest) -> GoalParseResponse:
    today = today_str()
    system_prompt = GOAL_PARSE_SYSTEM_PROMPT.format(today=today)

    try:
        result = await generate_json(system_prompt, payload.input)
        return GoalParseResponse(
            title=result["title"],
            startDate=result["startDate"],
            endDate=result["endDate"],
            aiMessage=result["aiMessage"],
        )
    except (AIGenerationError, KeyError, TypeError) as e:
        logger.error(f"목표 분석 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="목표 분석에 실패했어요. 다시 시도해주세요."
        )


def _validate_date_range(start_date: str, end_date: str) -> None:
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="종료일은 시작일보다 빠를 수 없어요."
        )


async def create_goal(user: User, payload: GoalCreateRequest) -> GoalCreateResponse:
    _validate_date_range(payload.startDate, payload.endDate)

    goal = Goal(
        user_id=user.id,
        title=payload.title,
        start_date=payload.startDate,
        end_date=payload.endDate,
    )
    await goal.insert()

    return GoalCreateResponse(
        id=str(goal.id),
        title=goal.title,
        startDate=goal.start_date,
        endDate=goal.end_date,
        createdAt=goal.created_at,
    )


async def _get_owned_goal(user: User, goal_id: str) -> Goal:
    try:
        goal_oid = PydanticObjectId(goal_id)
    except (InvalidId, ValueError):
        goal = None
    else:
        goal = await Goal.find_one(Goal.id == goal_oid, Goal.user_id == user.id)

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="목표를 찾을 수 없어요."
        )
    return goal


async def list_goals(user: User) -> GoalListResponse:
    today = today_str()
    goals = await Goal.find(Goal.user_id == user.id).sort(-Goal.created_at).to_list()

    return GoalListResponse(
        goals=[
            GoalListItem(
                id=str(goal.id),
                title=goal.title,
                startDate=goal.start_date,
                endDate=goal.end_date,
                isActive=goal.start_date <= today <= goal.end_date,
                createdAt=goal.created_at,
            )
            for goal in goals
        ]
    )


async def update_goal(user: User, goal_id: str, payload: GoalUpdateRequest) -> GoalUpdateResponse:
    goal = await _get_owned_goal(user, goal_id)

    updates = payload.model_dump(exclude_unset=True)
    if "title" in updates:
        goal.title = updates["title"]
    if "startDate" in updates:
        goal.start_date = updates["startDate"]
    if "endDate" in updates:
        goal.end_date = updates["endDate"]

    _validate_date_range(goal.start_date, goal.end_date)

    goal.updated_at = datetime.now()
    await goal.save()

    return GoalUpdateResponse(
        id=str(goal.id),
        title=goal.title,
        startDate=goal.start_date,
        endDate=goal.end_date,
        updatedAt=goal.updated_at,
    )


async def delete_goal(user: User, goal_id: str) -> SuccessResponse:
    goal = await _get_owned_goal(user, goal_id)
    await goal.delete()
    return SuccessResponse(success=True)
