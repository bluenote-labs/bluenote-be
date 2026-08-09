import json
import logging
from typing import Optional

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.models.record import Record
from app.models.try_ import Try, TryResultSummary
from app.models.user import User
from app.schemas.tries import (
    TryCreateRequest,
    TryCreateResponse,
    TryCurrentItem,
    TryListResponse,
    TryPastItem,
    TryResultSummaryOut,
)
from app.services.ai import AIGenerationError, generate_json
from app.services.pattern import RECORD_TEXT_LIMIT, get_owned_pattern
from app.utils.datetime import today_str

logger = logging.getLogger(__name__)

TRY_RESULT_SYSTEM_PROMPT = (
    "너는 사용자가 진행한 시도(action)의 결과를 그 기간 동안의 기록들로 분석하는 도우미야. "
    "각 기록을 보고 사용자가 실제로 그 행동을 했다고 볼 수 있는 기록 수를 세어 actionTakenCount에 담아. "
    "기록들 중 사용자의 변화나 생각을 가장 잘 보여주는 인상적인 표현을 하나 골라 notableQuote에 담고, "
    "비슷한 표현이나 정서가 기록들에서 몇 번 등장했는지 quoteCount에 담아. "
    "사용자가 입력한 언어를 그대로 유지해. "
    '반드시 다음 JSON 형식으로만 응답해: '
    '{"actionTakenCount": number, "notableQuote": string, "quoteCount": number}'
)


async def create_try(user: User, payload: TryCreateRequest) -> TryCreateResponse:
    await get_owned_pattern(user, payload.patternId)

    ongoing = await Try.find_one(
        Try.user_id == user.id,
        {"end_date": {"$gte": today_str()}},
    )
    if ongoing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 진행 중인 시도가 있어요."
        )

    try_doc = Try(
        user_id=user.id,
        pattern_id=PydanticObjectId(payload.patternId),
        action=payload.action,
        start_date=payload.startDate,
        end_date=payload.endDate,
    )
    await try_doc.insert()

    return TryCreateResponse(
        id=str(try_doc.id),
        patternId=str(try_doc.pattern_id),
        action=try_doc.action,
        startDate=try_doc.start_date,
        endDate=try_doc.end_date,
        createdAt=try_doc.created_at,
    )


async def _generate_result_summary(user: User, try_doc: Try) -> Optional[TryResultSummary]:
    records = await Record.find(
        Record.user_id == user.id,
        {"date": {"$gte": try_doc.start_date, "$lte": try_doc.end_date}},
    ).to_list()

    if not records:
        return TryResultSummary(
            total_records=0, action_taken_count=0, notable_quote="", quote_count=0
        )

    ai_input = json.dumps(
        {
            "action": try_doc.action,
            "records": [
                {"date": record.date, "text": record.plain_text[:RECORD_TEXT_LIMIT]}
                for record in records
            ],
        },
        ensure_ascii=False,
    )

    try:
        result = await generate_json(TRY_RESULT_SYSTEM_PROMPT, ai_input)
        return TryResultSummary(
            total_records=len(records),
            action_taken_count=result["actionTakenCount"],
            notable_quote=result["notableQuote"],
            quote_count=result["quoteCount"],
        )
    except (AIGenerationError, KeyError, TypeError) as e:
        logger.error(f"시도 결과 요약 생성 실패 (try_id={try_doc.id}): {e}")
        return None


async def get_tries(user: User) -> TryListResponse:
    tries = await Try.find(Try.user_id == user.id).sort(-Try.created_at).to_list()
    today = today_str()

    current = next((t for t in tries if t.end_date >= today), None)
    past = [t for t in tries if t.end_date < today]

    for try_doc in past:
        if try_doc.result_summary is None:
            summary = await _generate_result_summary(user, try_doc)
            if summary:
                try_doc.result_summary = summary
                await try_doc.save()

    return TryListResponse(
        current=(
            TryCurrentItem(
                id=str(current.id),
                patternId=str(current.pattern_id),
                action=current.action,
                startDate=current.start_date,
                endDate=current.end_date,
            )
            if current
            else None
        ),
        past=[
            TryPastItem(
                id=str(try_doc.id),
                action=try_doc.action,
                startDate=try_doc.start_date,
                endDate=try_doc.end_date,
                resultSummary=(
                    TryResultSummaryOut(
                        totalRecords=try_doc.result_summary.total_records,
                        actionTakenCount=try_doc.result_summary.action_taken_count,
                        notableQuote=try_doc.result_summary.notable_quote,
                        quoteCount=try_doc.result_summary.quote_count,
                    )
                    if try_doc.result_summary
                    else None
                ),
            )
            for try_doc in past
        ],
    )
