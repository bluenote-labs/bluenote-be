import json
import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional

from beanie import PydanticObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status

from app.models.goal import Goal
from app.models.pattern import Pattern
from app.models.record import Record
from app.models.user import User
from app.schemas.pattern import (
    HeatmapDay,
    HeatmapResponse,
    PatternFeedbackRequest,
    PatternFeedbackResponse,
    PatternItem,
    PatternListResponse,
)
from app.services.ai import AIGenerationError, generate_json

logger = logging.getLogger(__name__)

MIN_RECORDS_FOR_ANALYSIS = 5
RECORD_TEXT_LIMIT = 300

PATTERN_ANALYSIS_SYSTEM_PROMPT = (
    "너는 사용자의 하루 기록들을 분석해서 반복되는 행동 패턴을 찾아내는 도우미야. "
    "입력으로 사용자의 기록 목록(records)과 목표 목록(goals)이 JSON으로 주어져. 각 기록에는 고유 id가 있어. "
    "기록들에서 반복적으로 나타나는 행동/심리 패턴을 2~4개 찾아. "
    "목표(goals)를 참고하여 특정 목표와 관련된 행동 패턴도 찾아. "
    "각 패턴은 사용자에게 말하듯 자연스러운 한 문장(description)으로 표현하고, "
    "그 패턴의 근거가 된 기록들의 id를 evidenceRecordIds 배열에 담아. "
    "evidenceRecordIds에는 입력으로 주어진 id만 사용하고, 존재하지 않는 id는 절대 만들지 마. "
    "사용자가 입력한 언어를 그대로 유지해. "
    '반드시 다음 JSON 형식으로만 응답해: '
    '{"patterns": [{"description": string, "evidenceRecordIds": [string]}]}'
)

PATTERN_TRY_SYSTEM_PROMPT = (
    "너는 사용자의 행동 패턴을 극복할 수 있는 아주 작고 구체적인 시도를 제안하는 도우미야. "
    "부담 없이 바로 실행할 수 있는 2~4개의 짧은 행동을 제안해. "
    "각 제안은 '~하기' 형태의 간결한 명사구로 만들어. "
    "사용자가 입력한 언어를 그대로 유지해. "
    '반드시 다음 JSON 형식으로만 응답해: {"suggestedTries": [string]}'
)

ACTION_STATUS_MAP = {
    "confirm": "confirmed",
    "modify": "modified",
    "defer": "deferred",
}

WEEKDAY_NAMES = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]


def _resolve_range(period: str) -> tuple[str, str]:
    """period로부터 (start, end) 날짜 문자열을 계산한다."""
    today = datetime.now().date()

    if period == "1year":
        start = today - timedelta(days=364)
        return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

    if period.isdigit() and len(period) == 4:
        return f"{period}-01-01", f"{period}-12-31"

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="지원하지 않는 기간이에요."
    )


def _most_frequent_day(dates: list[datetime]) -> Optional[str]:
    if not dates:
        return None
    weekday, _ = Counter(d.weekday() for d in dates).most_common(1)[0]
    return WEEKDAY_NAMES[weekday]


def _most_active_month(dates: list[datetime]) -> Optional[str]:
    if not dates:
        return None
    month, _ = Counter(d.month for d in dates).most_common(1)[0]
    return f"{month}월"


async def get_heatmap(user: User, period: str) -> HeatmapResponse:
    start_str, end_str = _resolve_range(period)

    records = await Record.find(
        Record.user_id == user.id,
        {"date": {"$gte": start_str, "$lte": end_str}},
    ).sort(-Record.date).to_list()

    record_dates = [datetime.strptime(record.date, "%Y-%m-%d") for record in records]

    return HeatmapResponse(
        period=period,
        totalRecords=len(records),
        mostFrequentDay=_most_frequent_day(record_dates),
        mostActiveMonth=_most_active_month(record_dates),
        days=[HeatmapDay(date=record.date, recordId=str(record.id)) for record in records],
    )


def _to_pattern_item(pattern: Pattern) -> PatternItem:
    return PatternItem(
        id=str(pattern.id),
        description=pattern.description,
        evidenceRecordIds=[str(record_id) for record_id in pattern.evidence_record_ids],
        status=pattern.status,
        userModifiedDescription=pattern.user_modified_description,
    )


async def get_patterns(user: User) -> PatternListResponse:
    patterns = await Pattern.find(Pattern.user_id == user.id).sort(-Pattern.created_at).to_list()
    return PatternListResponse(patterns=[_to_pattern_item(p) for p in patterns])


async def analyze_patterns(user: User) -> PatternListResponse:
    records = await Record.find(Record.user_id == user.id).sort(-Record.date).to_list()
    if len(records) < MIN_RECORDS_FOR_ANALYSIS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="패턴을 분석하려면 기록이 5개 이상 필요해요."
        )

    goals = await Goal.find(Goal.user_id == user.id).to_list()

    ai_input = json.dumps(
        {
            "records": [
                {
                    "id": str(record.id),
                    "date": record.date,
                    "title": record.title,
                    "text": record.plain_text[:RECORD_TEXT_LIMIT],
                }
                for record in records
            ],
            "goals": [
                {"title": goal.title, "startDate": goal.start_date, "endDate": goal.end_date}
                for goal in goals
            ],
        },
        ensure_ascii=False,
    )

    valid_ids = {str(record.id) for record in records}
    try:
        result = await generate_json(PATTERN_ANALYSIS_SYSTEM_PROMPT, ai_input)
        new_patterns = [
            Pattern(
                user_id=user.id,
                description=raw["description"],
                evidence_record_ids=[
                    PydanticObjectId(rid)
                    for rid in raw.get("evidenceRecordIds", [])
                    if rid in valid_ids
                ],
            )
            for raw in result["patterns"]
        ]
    except (AIGenerationError, KeyError, TypeError) as e:
        logger.error(f"패턴 분석 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="패턴 분석에 실패했어요. 다시 시도해주세요."
        )

    # AI 호출 성공 후에만 기존 패턴을 교체한다 (실패 시 기존 패턴 보존)
    # TODO: tries API 도입 시 진행 중인 시도(end_date >= 오늘)도 함께 삭제해야 한다.
    # 완료된 시도(result_summary 보유)는 히스토리로 보존하고, pattern_id가 끊기는
    # 진행 중인 시도만 정리한다.
    await Pattern.find(Pattern.user_id == user.id).delete()
    for pattern in new_patterns:
        await pattern.insert()

    return PatternListResponse(patterns=[_to_pattern_item(p) for p in new_patterns])


async def _get_owned_pattern(user: User, pattern_id: str) -> Pattern:
    try:
        pattern_oid = PydanticObjectId(pattern_id)
    except (InvalidId, ValueError):
        pattern = None
    else:
        pattern = await Pattern.find_one(Pattern.id == pattern_oid, Pattern.user_id == user.id)

    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="패턴을 찾을 수 없어요."
        )
    return pattern


async def _generate_suggested_tries(description: str) -> list[str]:
    try:
        result = await generate_json(PATTERN_TRY_SYSTEM_PROMPT, description)
        return result["suggestedTries"]
    except (AIGenerationError, KeyError, TypeError) as e:
        logger.error(f"추천 시도 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="추천 시도 생성에 실패했어요. 다시 시도해주세요."
        )


async def submit_pattern_feedback(
    user: User, pattern_id: str, payload: PatternFeedbackRequest
) -> PatternFeedbackResponse:
    pattern = await _get_owned_pattern(user, pattern_id)

    if payload.action not in ACTION_STATUS_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 action이에요."
        )
    if payload.action == "modify" and not payload.modifiedDescription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 패턴 설명을 입력해주세요."
        )

    pattern.status = ACTION_STATUS_MAP[payload.action]
    if payload.action == "modify":
        pattern.user_modified_description = payload.modifiedDescription
    pattern.updated_at = datetime.now()
    await pattern.save()

    effective_description = pattern.user_modified_description or pattern.description

    suggested_tries: list[str] = []
    if payload.action in ("confirm", "modify"):
        suggested_tries = await _generate_suggested_tries(effective_description)

    return PatternFeedbackResponse(
        id=str(pattern.id),
        status=pattern.status,
        description=effective_description,
        suggestedTries=suggested_tries,
    )
